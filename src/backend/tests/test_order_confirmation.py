import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from decimal import Decimal

from app.models.order import OrderCreate, OrderLineItem, OrderStatus
from app.services.memory_db import InMemoryDBAdapter
from app.services.mock_swiggy import MockSwiggyMcpClient, MockSwiggyScenario
from app.services.order_confirmation import resolve_pending_order_confirmation


def run(coro):
    return asyncio.run(coro)


def make_pending_order(db: InMemoryDBAdapter, *, delivery_deadline=None):
    return run(
        db.create_order(
            OrderCreate(
                wa_id="919988776655",
                restaurant_id="rest-moti-mahal",
                restaurant_name="MotiMahal",
                items=[
                    OrderLineItem(item_id="food-mm-paneer-tikka", name="Paneer Tikka", price="260.00")
                ],
                total="260.00",
                budget_limit="200.00",
                delivery_deadline=delivery_deadline,
                status=OrderStatus.PENDING_CONFIRMATION,
                source_message_id="wamid.confirm.1",
            )
        )
    )


def test_yes_reply_places_order_immediately_when_no_deadline() -> None:
    db = InMemoryDBAdapter()
    swiggy = MockSwiggyMcpClient()
    order = make_pending_order(db)

    reply = run(resolve_pending_order_confirmation(db, swiggy, order, "yes"))

    updated = run(db.get_order(order.order_id))
    assert "Placed!" in reply
    assert updated.status == OrderStatus.PLACED
    assert updated.swiggy_order_id is not None


def test_yes_reply_schedules_instead_of_placing_when_deadline_present() -> None:
    db = InMemoryDBAdapter()
    swiggy = MockSwiggyMcpClient()
    deadline = datetime.now(UTC) + timedelta(hours=2)
    order = make_pending_order(db, delivery_deadline=deadline)

    reply = run(resolve_pending_order_confirmation(db, swiggy, order, "yes"))

    updated = run(db.get_order(order.order_id))
    assert "Scheduled" in reply
    assert updated.status == OrderStatus.SCHEDULED
    assert updated.swiggy_order_id is None
    assert updated.target_placement_at == deadline - timedelta(minutes=40)


def test_no_reply_cancels_order() -> None:
    db = InMemoryDBAdapter()
    swiggy = MockSwiggyMcpClient()
    order = make_pending_order(db)

    reply = run(resolve_pending_order_confirmation(db, swiggy, order, "no"))

    updated = run(db.get_order(order.order_id))
    assert "Cancelled" in reply
    assert updated.status == OrderStatus.CANCELLED


def test_ambiguous_reply_re_asks_and_leaves_status_unchanged() -> None:
    db = InMemoryDBAdapter()
    swiggy = MockSwiggyMcpClient()
    order = make_pending_order(db)

    reply = run(resolve_pending_order_confirmation(db, swiggy, order, "maybe later"))

    updated = run(db.get_order(order.order_id))
    assert "Still waiting" in reply
    assert updated.status == OrderStatus.PENDING_CONFIRMATION


def test_yes_reply_with_changed_price_resets_to_pending_confirmation_instead_of_placing() -> None:
    db = InMemoryDBAdapter()
    swiggy = MockSwiggyMcpClient(MockSwiggyScenario(price_change_item_id="food-mm-paneer-tikka"))
    order = make_pending_order(db)

    reply = run(resolve_pending_order_confirmation(db, swiggy, order, "yes"))

    updated = run(db.get_order(order.order_id))
    assert "now costs" in reply
    assert "INR 285.00" in reply
    assert updated.status == OrderStatus.PENDING_CONFIRMATION
    assert updated.total == Decimal("285.00")
    assert updated.swiggy_order_id is None


def test_yes_reply_with_item_gone_from_menu_cancels_instead_of_placing() -> None:
    db = InMemoryDBAdapter()
    swiggy = MockSwiggyMcpClient(MockSwiggyScenario(unavailable_item_id="food-mm-paneer-tikka"))
    order = make_pending_order(db)

    reply = run(resolve_pending_order_confirmation(db, swiggy, order, "yes"))

    updated = run(db.get_order(order.order_id))
    assert "no longer available" in reply
    assert updated.status == OrderStatus.CANCELLED
    assert updated.swiggy_order_id is None


def test_place_order_failure_on_yes_marks_failed_and_apologizes() -> None:
    db = InMemoryDBAdapter()

    class FailingSwiggyClient(MockSwiggyMcpClient):
        async def place_order(self, auth_header, vertical, restaurant_id, items):
            raise RuntimeError("simulated Swiggy failure")

    order = make_pending_order(db)

    reply = run(resolve_pending_order_confirmation(db, FailingSwiggyClient(), order, "yes"))

    updated = run(db.get_order(order.order_id))
    assert "failed" in reply.lower()
    assert updated.status == OrderStatus.FAILED
    assert updated.failure_reason is not None
