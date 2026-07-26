import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.order import OrderCreate, OrderLineItem, OrderStatus
from app.models.session import SessionCreate, SessionEvent
from app.services.memory_db import InMemoryDBAdapter


def run(coro):
    return asyncio.run(coro)


def _create(adapter: InMemoryDBAdapter, *, host_phone: str) -> str:
    session = run(
        adapter.create_session(
            SessionCreate(whatsapp_group_id="group_1", host_phone=host_phone),
            host_token_hash="hash",
            guest_token="guest",
        )
    )
    return session.session_id


def test_delete_sessions_for_host_removes_only_that_hosts_sessions_and_events() -> None:
    adapter = InMemoryDBAdapter()
    target_session_id = _create(adapter, host_phone="919988776655")
    other_session_id = _create(adapter, host_phone="911111111111")
    run(
        adapter.insert_session_event(
            SessionEvent(session_id=target_session_id, event_type="whatsapp_tagged_message")
        )
    )
    run(
        adapter.insert_session_event(
            SessionEvent(session_id=other_session_id, event_type="whatsapp_tagged_message")
        )
    )

    deleted = run(adapter.delete_sessions_for_host("919988776655"))

    assert deleted == 1
    assert run(adapter.get_session(target_session_id)) is None
    assert run(adapter.get_session(other_session_id)) is not None
    assert all(event.session_id != target_session_id for event in adapter.events)
    assert any(event.session_id == other_session_id for event in adapter.events)


def test_delete_sessions_for_host_with_no_sessions_returns_zero() -> None:
    adapter = InMemoryDBAdapter()

    assert run(adapter.delete_sessions_for_host("919900000000")) == 0


def test_delete_sessions_older_than_cutoff() -> None:
    adapter = InMemoryDBAdapter()
    old_session_id = _create(adapter, host_phone="919988776655")
    adapter.sessions[old_session_id].created_at = datetime(2020, 1, 1, tzinfo=UTC)
    recent_session_id = _create(adapter, host_phone="911111111111")

    deleted = run(adapter.delete_sessions_older_than(datetime(2025, 1, 1, tzinfo=UTC)))

    assert deleted == 1
    assert run(adapter.get_session(old_session_id)) is None
    assert run(adapter.get_session(recent_session_id)) is not None


def _create_order(adapter: InMemoryDBAdapter, **overrides) -> str:
    defaults = dict(
        wa_id="919988776655",
        restaurant_id="rest-moti-mahal",
        restaurant_name="MotiMahal",
        items=[OrderLineItem(item_id="food-mm-paneer-tikka", name="Paneer Tikka", price="260.00")],
        total="260.00",
        status=OrderStatus.PLACED,
    )
    defaults.update(overrides)
    order = run(adapter.create_order(OrderCreate(**defaults)))
    return order.order_id


def test_order_crud_round_trip() -> None:
    adapter = InMemoryDBAdapter()
    order_id = _create_order(adapter, source_message_id="wamid.order.1")

    fetched = run(adapter.get_order(order_id))
    by_message = run(adapter.get_order_by_source_message_id("wamid.order.1"))

    assert fetched.order_id == order_id
    assert by_message.order_id == order_id
    assert run(adapter.get_order_by_source_message_id("wamid.unknown")) is None


def test_pending_confirmation_lookup_is_scoped_to_wa_id_and_status() -> None:
    adapter = InMemoryDBAdapter()
    _create_order(adapter, wa_id="919988776655", status=OrderStatus.PENDING_CONFIRMATION)
    _create_order(adapter, wa_id="919900000000", status=OrderStatus.PLACED)

    pending = run(adapter.get_pending_confirmation_order("919988776655"))
    none_pending = run(adapter.get_pending_confirmation_order("919900000000"))

    assert pending is not None
    assert pending.wa_id == "919988776655"
    assert none_pending is None


def test_get_due_scheduled_orders_filters_by_status_and_target_time() -> None:
    adapter = InMemoryDBAdapter()
    now = datetime.now(UTC)
    due_id = _create_order(
        adapter,
        status=OrderStatus.SCHEDULED,
        target_placement_at=now - timedelta(minutes=1),
    )
    _create_order(
        adapter,
        status=OrderStatus.SCHEDULED,
        target_placement_at=now + timedelta(hours=1),
    )
    _create_order(adapter, status=OrderStatus.PLACED)

    due = run(adapter.get_due_scheduled_orders(as_of=now))

    assert [order.order_id for order in due] == [due_id]


def test_order_status_transition_helpers() -> None:
    adapter = InMemoryDBAdapter()
    order_id = _create_order(adapter, status=OrderStatus.PENDING_CONFIRMATION)

    run(adapter.set_order_scheduled(order_id, target_placement_at=datetime.now(UTC)))
    assert run(adapter.get_order(order_id)).status == OrderStatus.SCHEDULED

    run(adapter.set_order_placed(order_id, swiggy_order_id="order-99"))
    placed = run(adapter.get_order(order_id))
    assert placed.status == OrderStatus.PLACED
    assert placed.swiggy_order_id == "order-99"

    run(adapter.set_order_failed(order_id, failure_reason="boom"))
    failed = run(adapter.get_order(order_id))
    assert failed.status == OrderStatus.FAILED
    assert failed.failure_reason == "boom"

    run(adapter.update_order_status(order_id, OrderStatus.CANCELLED))
    assert run(adapter.get_order(order_id)).status == OrderStatus.CANCELLED


def test_set_order_price_changed_resets_to_pending_confirmation_with_new_items_and_total() -> None:
    adapter = InMemoryDBAdapter()
    order_id = _create_order(adapter, status=OrderStatus.SCHEDULED)

    new_items = [OrderLineItem(item_id="food-mm-chicken-65", name="Chicken 65", price="345.00")]
    run(adapter.set_order_price_changed(order_id, items=new_items, total=Decimal("345.00")))

    updated = run(adapter.get_order(order_id))
    assert updated.status == OrderStatus.PENDING_CONFIRMATION
    assert updated.total == Decimal("345.00")
    assert updated.items[0].name == "Chicken 65"


def test_list_orders_for_host_is_newest_first_and_scoped_to_wa_id() -> None:
    adapter = InMemoryDBAdapter()
    _create_order(adapter, wa_id="919988776655")
    _create_order(adapter, wa_id="919988776655")
    _create_order(adapter, wa_id="919900000000")

    orders = run(adapter.list_orders_for_host("919988776655"))

    assert len(orders) == 2
    assert all(order.wa_id == "919988776655" for order in orders)
