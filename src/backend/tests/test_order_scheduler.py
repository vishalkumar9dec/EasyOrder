import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.order import OrderCreate, OrderLineItem, OrderStatus
from app.services.memory_db import InMemoryDBAdapter
from app.services.mock_swiggy import MockSwiggyMcpClient, MockSwiggyScenario
from app.services.order_scheduler import OrderScheduler
from app.services.whatsapp_sender import MockWhatsAppSender


def run(coro):
    return asyncio.run(coro)


def scheduled_order(
    db,
    *,
    restaurant_id="rest-moti-mahal",
    restaurant_name="MotiMahal",
    item_id="food-mm-paneer-tikka",
    item_name="Paneer Tikka",
    price="260.00",
    due_in_seconds=-1,
    wa_id="919988776655",
):
    return run(
        db.create_order(
            OrderCreate(
                wa_id=wa_id,
                restaurant_id=restaurant_id,
                restaurant_name=restaurant_name,
                items=[OrderLineItem(item_id=item_id, name=item_name, price=price)],
                total=price,
                status=OrderStatus.SCHEDULED,
                target_placement_at=datetime.now(UTC) + timedelta(seconds=due_in_seconds),
            )
        )
    )


def test_tick_places_due_orders_and_notifies() -> None:
    db = InMemoryDBAdapter()
    sender = MockWhatsAppSender()
    scheduler = OrderScheduler(db=db, swiggy_client=MockSwiggyMcpClient(), whatsapp_sender=sender)
    order = scheduled_order(db, due_in_seconds=-5)

    placed_count = run(scheduler.tick())

    updated = run(db.get_order(order.order_id))
    assert placed_count == 1
    assert updated.status == OrderStatus.PLACED
    assert updated.swiggy_order_id is not None
    assert any("Placed!" in message.text for message in sender.sent_messages)


def test_tick_leaves_not_yet_due_orders_untouched() -> None:
    db = InMemoryDBAdapter()
    sender = MockWhatsAppSender()
    scheduler = OrderScheduler(db=db, swiggy_client=MockSwiggyMcpClient(), whatsapp_sender=sender)
    order = scheduled_order(db, due_in_seconds=3600)

    placed_count = run(scheduler.tick())

    updated = run(db.get_order(order.order_id))
    assert placed_count == 0
    assert updated.status == OrderStatus.SCHEDULED


def test_one_orders_failure_does_not_block_the_rest_of_the_batch() -> None:
    db = InMemoryDBAdapter()
    sender = MockWhatsAppSender()

    class PartiallyFailingSwiggyClient(MockSwiggyMcpClient):
        async def place_order(self, auth_header, vertical, restaurant_id, items):
            if restaurant_id == "rest-fails":
                raise RuntimeError("simulated Swiggy outage")
            return await super().place_order(auth_header, vertical, restaurant_id, items)

    scheduler = OrderScheduler(
        db=db, swiggy_client=PartiallyFailingSwiggyClient(), whatsapp_sender=sender
    )
    good_order_1 = scheduled_order(db, restaurant_id="rest-moti-mahal", due_in_seconds=-5)
    # rest-fails has no MOCK_MENUS entry, so get_restaurant_menu falls back to
    # its synthetic single "-combo" item — match that so the pre-placement
    # reverify step passes and place_order's simulated failure actually runs.
    failing_order = scheduled_order(
        db,
        restaurant_id="rest-fails",
        restaurant_name="Fails Kitchen",
        item_id="rest-fails-combo",
        item_name="Family meal combo",
        price="720.00",
        due_in_seconds=-4,
    )
    good_order_2 = scheduled_order(
        db,
        restaurant_id="rest-biryani-by-kilo",
        restaurant_name="BiryaniByKilo",
        item_id="food-bbk-egg-biryani",
        item_name="Egg Biryani",
        price="300.00",
        due_in_seconds=-3,
    )

    placed_count = run(scheduler.tick())

    assert placed_count == 3
    assert run(db.get_order(good_order_1.order_id)).status == OrderStatus.PLACED
    assert run(db.get_order(good_order_2.order_id)).status == OrderStatus.PLACED
    failed = run(db.get_order(failing_order.order_id))
    assert failed.status == OrderStatus.FAILED
    assert failed.failure_reason is not None


def test_tick_resets_to_pending_confirmation_when_price_changed_instead_of_placing() -> None:
    db = InMemoryDBAdapter()
    sender = MockWhatsAppSender()
    swiggy = MockSwiggyMcpClient(MockSwiggyScenario(price_change_item_id="food-mm-chicken-65"))
    scheduler = OrderScheduler(db=db, swiggy_client=swiggy, whatsapp_sender=sender)
    order = scheduled_order(
        db,
        item_id="food-mm-chicken-65",
        item_name="Chicken 65",
        price="320.00",
        due_in_seconds=-5,
    )

    run(scheduler.tick())

    updated = run(db.get_order(order.order_id))
    assert updated.status == OrderStatus.PENDING_CONFIRMATION
    assert updated.total == Decimal("345.00")
    assert updated.swiggy_order_id is None
    assert any("now costs" in message.text for message in sender.sent_messages)


def test_tick_cancels_when_item_no_longer_on_menu() -> None:
    db = InMemoryDBAdapter()
    sender = MockWhatsAppSender()
    swiggy = MockSwiggyMcpClient(MockSwiggyScenario(unavailable_item_id="food-mm-chicken-65"))
    scheduler = OrderScheduler(db=db, swiggy_client=swiggy, whatsapp_sender=sender)
    order = scheduled_order(
        db,
        item_id="food-mm-chicken-65",
        item_name="Chicken 65",
        price="320.00",
        due_in_seconds=-5,
    )

    run(scheduler.tick())

    updated = run(db.get_order(order.order_id))
    assert updated.status == OrderStatus.CANCELLED
    assert any("no longer available" in message.text for message in sender.sent_messages)


def test_run_forever_stops_cleanly_on_cancel() -> None:
    async def main() -> None:
        db = InMemoryDBAdapter()
        scheduler = OrderScheduler(
            db=db,
            swiggy_client=MockSwiggyMcpClient(),
            whatsapp_sender=MockWhatsAppSender(),
            poll_interval_seconds=0.01,
        )
        task = asyncio.create_task(scheduler.run_forever())
        await asyncio.sleep(0.03)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    run(main())
