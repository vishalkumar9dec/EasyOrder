"""Background poller that places SCHEDULED orders once their target time arrives.

No job-queue infra (Celery/Redis/etc.) exists in this codebase — this is a
plain in-process asyncio loop, consistent with the rest of the app's
simplicity level. One order's failure is isolated so it never blocks the
rest of the due batch or crashes the loop.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from app.models.order import Order
from app.services.protocols import IDBAdapter, ISwiggyMcpClient, IWhatsAppSender
from app.services.targeted_order import (
    PLACEHOLDER_AUTH_HEADER,
    handle_reverification_mismatch,
    reverify_order_before_placement,
)
from app.services.whatsapp_sender import WhatsAppSendError

logger = logging.getLogger("easyorder.api")

DEFAULT_POLL_INTERVAL_SECONDS = 30.0


class OrderScheduler:
    """Polls for due SCHEDULED orders and places them automatically."""

    def __init__(
        self,
        db: IDBAdapter,
        swiggy_client: ISwiggyMcpClient,
        whatsapp_sender: IWhatsAppSender,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    ) -> None:
        self.db = db
        self.swiggy_client = swiggy_client
        self.whatsapp_sender = whatsapp_sender
        self.poll_interval_seconds = poll_interval_seconds

    async def run_forever(self) -> None:
        while True:
            try:
                await self.tick()
            except Exception:
                logger.exception("order_scheduler_tick_failed")
            await asyncio.sleep(self.poll_interval_seconds)

    async def tick(self) -> int:
        """Place every currently-due SCHEDULED order. Returns how many were due."""
        due = await self.db.get_due_scheduled_orders(as_of=datetime.now(UTC))
        for order in due:
            await self._place_one(order)
        return len(due)

    async def _place_one(self, order: Order) -> None:
        # The target placement time can be well in the future relative to
        # when the order was quoted — re-check the menu right before
        # actually committing, same as the confirmation-reply path does.
        try:
            reverification = await reverify_order_before_placement(self.swiggy_client, order)
        except Exception:
            logger.exception("order_scheduler_reverify_failed order_id=%s", order.order_id)
            await self.db.set_order_failed(order.order_id, failure_reason="Menu re-check failed")
            await self._notify(
                order,
                f"Sorry, your scheduled {order.restaurant_name} order couldn't be placed.",
            )
            return

        if not reverification.unchanged:
            text = await handle_reverification_mismatch(self.db, order, reverification)
            await self._notify(order, text)
            return

        try:
            result = await self.swiggy_client.place_order(
                auth_header=PLACEHOLDER_AUTH_HEADER,
                vertical="food",
                restaurant_id=order.restaurant_id,
                items=[item.model_dump(mode="json") for item in order.items],
            )
        except Exception as error:
            logger.exception("order_scheduler_place_failed order_id=%s", order.order_id)
            await self.db.set_order_failed(order.order_id, failure_reason=str(error))
            await self._notify(
                order,
                f"Sorry, your scheduled {order.restaurant_name} order couldn't be placed.",
            )
            return

        await self.db.set_order_placed(order.order_id, swiggy_order_id=str(result["order_id"]))
        await self._notify(
            order,
            f"Placed! Your scheduled {order.restaurant_name} order — total INR {order.total}.",
        )

    async def _notify(self, order: Order, text: str) -> None:
        try:
            await self.whatsapp_sender.send_private_message(order.wa_id, text)
        except WhatsAppSendError:
            logger.warning(
                "order_scheduler_notification_failed",
                extra={"order_id": order.order_id},
                exc_info=True,
            )
        except Exception:
            logger.warning(
                "order_scheduler_notification_failed",
                extra={"order_id": order.order_id},
                exc_info=True,
            )
