"""Targeted single-restaurant order flow: "order X and Y from <restaurant>".

A deliberately simpler, separate pipeline from EasyOrderAgentService's
LangGraph — no multi-guest session, no worker fan-out across verticals, just
one restaurant, named dishes, and (optionally) a budget gate or delivery
deadline.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from app.models.order import Order, OrderCreate, OrderLineItem, OrderStatus
from app.models.whatsapp import IncomingMessage
from app.services import menu_matching
from app.services.agent import (
    AgentRejectedPromptError,
    InputGuardrails,
    TargetedOrderIntent,
    TargetedOrderIntentParser,
)
from app.services.protocols import IDBAdapter, ISwiggyMcpClient

# No real Swiggy OAuth exists for this autonomous (no host-browser) flow yet,
# mirroring the existing placeholder-auth precedent used for pre-checkout
# validation in api/session.py ("Bearer mock-precheckout-validation").
PLACEHOLDER_AUTH_HEADER = "Bearer mock-order-placement"

CLARIFY_RESTAURANT_REPLY = (
    "Which restaurant should I order from? For example: "
    "order paneer tikka from MotiMahal."
)


class TargetedOrderService:
    """Handles targeted single-restaurant order prompts."""

    def __init__(
        self,
        db: IDBAdapter,
        swiggy_client: ISwiggyMcpClient,
        parser: TargetedOrderIntentParser,
        guardrails: InputGuardrails | None = None,
    ) -> None:
        self.db = db
        self.swiggy_client = swiggy_client
        self.parser = parser
        self.guardrails = guardrails or InputGuardrails()

    async def handle_targeted_order_message(self, message: IncomingMessage) -> str:
        existing = await self.db.get_order_by_source_message_id(message.message_id)
        if existing is not None:
            return self._reply_for_status(existing)

        try:
            sanitized = self.guardrails.sanitize(message.message_text)
        except AgentRejectedPromptError:
            return "Sorry, I couldn't process that message."

        intent = await self.parser.parse(sanitized)
        if intent is None or not intent.restaurant_name:
            return CLARIFY_RESTAURANT_REPLY

        restaurant = await self.swiggy_client.find_restaurant_by_name(intent.restaurant_name)
        if restaurant is None:
            return f"I couldn't find a restaurant named '{intent.restaurant_name}'."

        if not intent.dish_names:
            return f"What would you like to order from {restaurant['name']}?"

        menu = await self.swiggy_client.get_restaurant_menu(restaurant["restaurant_id"])
        matched_items = menu_matching.match_menu_items(menu, intent.dish_names)
        missing = self._missing_dish_names(menu, intent.dish_names)
        if missing:
            return (
                f"Couldn't find {', '.join(missing)} on {restaurant['name']}'s menu. "
                "Please try again with the exact dish names."
            )

        total = sum((Decimal(str(item["price"])) for item in matched_items), Decimal("0.00"))
        dish_label = ", ".join(item["name"] for item in matched_items)

        now = datetime.now(UTC)
        deadline, deadline_note = self._resolve_deadline(intent.delivery_deadline_minutes, now)
        target_placement_at = None
        placement_note = ""
        if deadline is not None:
            target_placement_at = deadline - timedelta(minutes=int(restaurant["eta_minutes"]))
            if target_placement_at <= now:
                target_placement_at = now
                placement_note = " It's cut close, so I'll place it right away."

        order_base = {
            "wa_id": message.sender_id,
            "restaurant_id": restaurant["restaurant_id"],
            "restaurant_name": restaurant["name"],
            "items": [
                OrderLineItem(item_id=item["item_id"], name=item["name"], price=item["price"])
                for item in matched_items
            ],
            "total": total,
            "budget_limit": intent.budget_limit,
            "delivery_deadline": deadline,
            "source_message_id": message.message_id,
        }

        if intent.budget_limit is not None and total > intent.budget_limit:
            order = await self.db.create_order(
                OrderCreate(**order_base, status=OrderStatus.PENDING_CONFIRMATION)
            )
            schedule_note = (
                " Since it's also timed, replying YES will schedule it instead of "
                "placing it right away." if deadline is not None else ""
            )
            return (
                f"{dish_label} from {order.restaurant_name} comes to INR {total}, which "
                f"exceeds your INR {intent.budget_limit} budget.{schedule_note} "
                "Reply YES to place it anyway, or NO to cancel."
            )

        if target_placement_at is not None:
            order = await self.db.create_order(
                OrderCreate(
                    **order_base,
                    status=OrderStatus.SCHEDULED,
                    target_placement_at=target_placement_at,
                )
            )
            return (
                f"Got it — {dish_label} from {order.restaurant_name} (INR {total}) is "
                f"scheduled so it reaches by {deadline_note}.{placement_note}"
            )

        result = await self.swiggy_client.place_order(
            auth_header=PLACEHOLDER_AUTH_HEADER,
            vertical="food",
            restaurant_id=restaurant["restaurant_id"],
            items=[item.model_dump(mode="json") for item in order_base["items"]],
        )
        order = await self.db.create_order(
            OrderCreate(**order_base, status=OrderStatus.PLACED)
        )
        await self.db.set_order_placed(order.order_id, swiggy_order_id=str(result["order_id"]))
        return f"Placed! {dish_label} from {order.restaurant_name} — total INR {total}."

    @staticmethod
    def _missing_dish_names(menu: list[dict[str, Any]], dish_names: list[str]) -> list[str]:
        missing = []
        for dish_name in dish_names:
            if not menu_matching.match_menu_items(menu, [dish_name]):
                missing.append(dish_name)
        return missing

    @staticmethod
    def _resolve_deadline(
        deadline_minutes: int | None,
        now: datetime,
    ) -> tuple[datetime | None, str]:
        if deadline_minutes is None:
            return None, ""
        candidate = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            minutes=deadline_minutes
        )
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate, candidate.strftime("%I:%M %p UTC").lstrip("0")

    @staticmethod
    def _reply_for_status(order: Order) -> str:
        if order.status == OrderStatus.PENDING_CONFIRMATION:
            return (
                f"Still waiting on your confirmation for the {order.restaurant_name} "
                "order — reply YES or NO."
            )
        if order.status == OrderStatus.SCHEDULED:
            return f"Already scheduled: {order.restaurant_name} order."
        if order.status == OrderStatus.PLACED:
            return f"Already placed: {order.restaurant_name} order."
        return f"That order was already processed (status: {order.status})."


@dataclass(frozen=True)
class ReverificationResult:
    """Result of re-checking an order's items/price against the live menu
    immediately before actually placing it — the menu can change in the gap
    between when the order was first quoted and when it's finally placed
    (a "yes" reply, or a scheduler tick, can both happen much later)."""

    unchanged: bool
    items: list[OrderLineItem]
    total: Decimal
    missing_dish_names: list[str]


async def reverify_order_before_placement(
    swiggy_client: ISwiggyMcpClient,
    order: Order,
) -> ReverificationResult:
    """Re-fetch the restaurant's current menu and compare against the order's
    snapshotted items/total. Mirrors the group-session checkout flow's
    create_cart PRICE_CHANGED/ITEM_UNAVAILABLE check, applied to place_order."""
    menu = await swiggy_client.get_restaurant_menu(order.restaurant_id)
    menu_by_id = {str(item["item_id"]): item for item in menu}

    fresh_items: list[OrderLineItem] = []
    missing_dish_names: list[str] = []
    for line in order.items:
        current = menu_by_id.get(line.item_id)
        if current is None:
            missing_dish_names.append(line.name)
            continue
        fresh_items.append(
            OrderLineItem(
                item_id=line.item_id,
                name=str(current["name"]),
                price=current["price"],
                quantity=line.quantity,
            )
        )

    total = sum((item.price * item.quantity for item in fresh_items), Decimal("0.00"))
    unchanged = (
        not missing_dish_names
        and len(fresh_items) == len(order.items)
        and total == order.total
    )
    return ReverificationResult(
        unchanged=unchanged,
        items=fresh_items,
        total=total,
        missing_dish_names=missing_dish_names,
    )


async def handle_reverification_mismatch(
    db: IDBAdapter,
    order: Order,
    reverification: ReverificationResult,
) -> str:
    """Persist the mismatch and return the WhatsApp reply text explaining it.

    An item that disappeared from the menu cancels the order outright (there
    is nothing to re-confirm). A price change resets the order to
    PENDING_CONFIRMATION at the new price and asks again, reusing the same
    multi-turn confirmation mechanism the budget gate already uses.
    """
    if reverification.missing_dish_names:
        await db.update_order_status(order.order_id, OrderStatus.CANCELLED)
        return (
            f"Sorry, {', '.join(reverification.missing_dish_names)} from "
            f"{order.restaurant_name} is no longer available. Order cancelled — "
            "please try again."
        )

    await db.set_order_price_changed(
        order.order_id,
        items=reverification.items,
        total=reverification.total,
    )
    dish_label = ", ".join(item.name for item in reverification.items)
    return (
        f"Heads up — {dish_label} from {order.restaurant_name} now costs "
        f"INR {reverification.total} (was INR {order.total}). Reply YES to "
        "place it at the new price, or NO to cancel."
    )
