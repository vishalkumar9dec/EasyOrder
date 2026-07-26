"""Resolves a pending budget-confirmation order with the user's next reply.

Real multi-turn confirmation: the bot asks a question when placing an order
would exceed the stated budget, and a SEPARATE, later WhatsApp message (not
a same-message "...confirm" suffix like the deletion/share patterns)
resolves it. State lives entirely on the Order row (status=PENDING_CONFIRMATION).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from app.models.order import Order, OrderStatus
from app.services.protocols import IDBAdapter, ISwiggyMcpClient
from app.services.targeted_order import (
    PLACEHOLDER_AUTH_HEADER,
    handle_reverification_mismatch,
    reverify_order_before_placement,
)

_ORDER_CONFIRM_YES = re.compile(r"\b(yes|confirm|go ahead|haan|place it|proceed)\b", re.IGNORECASE)
_ORDER_CONFIRM_NO = re.compile(r"\b(no|cancel|stop|nahi)\b", re.IGNORECASE)


async def resolve_pending_order_confirmation(
    db: IDBAdapter,
    swiggy_client: ISwiggyMcpClient,
    order: Order,
    reply_text: str,
) -> str:
    """Resolve one pending order against the user's confirmation reply."""
    normalized = reply_text.strip().lower()
    is_yes = _ORDER_CONFIRM_YES.search(normalized) is not None
    is_no = _ORDER_CONFIRM_NO.search(normalized) is not None

    if is_yes and not is_no:
        if order.delivery_deadline is not None:
            return await _schedule(db, swiggy_client, order)
        return await _place(db, swiggy_client, order)

    if is_no:
        await db.update_order_status(order.order_id, OrderStatus.CANCELLED)
        return "Cancelled — nothing was ordered."

    return (
        f"Still waiting on your confirmation for the {order.restaurant_name} order "
        f"(INR {order.total}) — reply YES to place it or NO to cancel."
    )


async def _schedule(db: IDBAdapter, swiggy_client: ISwiggyMcpClient, order: Order) -> str:
    restaurant = await swiggy_client.get_restaurant(order.restaurant_id)
    now = datetime.now(UTC)
    target_placement_at = order.delivery_deadline - timedelta(
        minutes=int(restaurant.get("eta_minutes") or 0)
    )
    if target_placement_at <= now:
        target_placement_at = now
    await db.set_order_scheduled(order.order_id, target_placement_at=target_placement_at)
    deadline_label = order.delivery_deadline.strftime("%I:%M %p UTC").lstrip("0")
    return f"Scheduled — I'll place your {order.restaurant_name} order so it reaches by {deadline_label}."


async def _place(db: IDBAdapter, swiggy_client: ISwiggyMcpClient, order: Order) -> str:
    # The menu can have changed in the gap between the original quote and
    # this "yes" reply — re-check before committing, exactly as checkout
    # re-validates via create_cart before the real order goes through.
    reverification = await reverify_order_before_placement(swiggy_client, order)
    if not reverification.unchanged:
        return await handle_reverification_mismatch(db, order, reverification)

    try:
        result = await swiggy_client.place_order(
            auth_header=PLACEHOLDER_AUTH_HEADER,
            vertical="food",
            restaurant_id=order.restaurant_id,
            items=[item.model_dump(mode="json") for item in order.items],
        )
    except Exception as error:
        await db.set_order_failed(order.order_id, failure_reason=str(error))
        return "Sorry, placing that order failed. Please try again."

    await db.set_order_placed(order.order_id, swiggy_order_id=str(result["order_id"]))
    return f"Placed! {order.restaurant_name} order — total INR {order.total}."
