import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.db.adapter import AsyncPostgresDBAdapter, SessionNotFoundError
from app.models.order import OrderCreate, OrderLineItem, OrderStatus
from app.models.session import (
    CartItem,
    DietaryTag,
    SessionCreate,
    SessionEvent,
    SessionStatus,
    Vertical,
)


class FakeTransaction:
    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection

    async def __aenter__(self) -> None:
        self.connection.transaction_depth += 1

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        self.connection.transaction_depth -= 1


class FakeConnection:
    def __init__(self) -> None:
        self.sessions: dict[str, dict] = {}
        self.cart_items: list[dict] = []
        self.session_events: list[dict] = []
        self.orders: dict[str, dict] = {}
        self.transaction_depth = 0
        self.next_cart_id = 1

    def transaction(self) -> FakeTransaction:
        return FakeTransaction(self)

    async def fetchrow(self, sql: str, *args):
        if "INSERT INTO sessions" in sql:
            row = {
                "session_id": args[0],
                "whatsapp_group_id": args[1],
                "host_phone": args[2],
                "host_token_hash": args[3],
                "guest_token": args[4],
                "budget_limit": args[5],
                "head_count": args[6],
                "dietary_preference": args[7],
                "status": args[8],
                "budget_warning": args[9],
                "degraded_verticals": args[10],
                "warnings": args[11],
                "created_at": datetime.now(UTC),
            }
            self.sessions[row["session_id"]] = row
            return row

        if "SELECT * FROM sessions" in sql:
            return self.sessions.get(args[0])

        if "INSERT INTO session_events" in sql:
            already_recorded = args[4] is not None and any(
                event["message_id"] == args[4] and event["event_type"] == args[1]
                for event in self.session_events
            )
            if already_recorded:
                return None
            row = {
                "id": len(self.session_events) + 1,
                "session_id": args[0],
                "event_type": args[1],
                "message_text": args[2],
                "intent_label": args[3],
                "message_id": args[4],
                "sender_wa_id": args[5],
                "mode": args[6],
                "request_id": args[7],
                "created_at": datetime.now(UTC),
            }
            self.session_events.append(row)
            return row

        if "FROM session_events" in sql:
            return next(
                (
                    event
                    for event in self.session_events
                    if event["message_id"] == args[0] and event["event_type"] == args[1]
                ),
                None,
            )

        if "INSERT INTO orders" in sql:
            row = {
                "order_id": args[0],
                "wa_id": args[1],
                "restaurant_id": args[2],
                "restaurant_name": args[3],
                "items": args[4],
                "total": args[5],
                "budget_limit": args[6],
                "delivery_deadline": args[7],
                "target_placement_at": args[8],
                "status": args[9],
                "source_message_id": args[10],
                "swiggy_order_id": None,
                "failure_reason": None,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
            self.orders[row["order_id"]] = row
            return row

        if "SELECT * FROM orders WHERE order_id" in sql:
            return self.orders.get(args[0])

        if "SELECT * FROM orders WHERE source_message_id" in sql:
            return next(
                (o for o in self.orders.values() if o["source_message_id"] == args[0]), None
            )

        if "PENDING_CONFIRMATION" in sql and "SELECT" in sql:
            return next(
                (
                    o
                    for o in self.orders.values()
                    if o["wa_id"] == args[0] and o["status"] == "PENDING_CONFIRMATION"
                ),
                None,
            )

        if "FROM sessions s" in sql and "COUNT(*)" in sql:
            statuses = args[1]
            matches = [
                s
                for s in self.sessions.values()
                if s["host_phone"] == args[0] and s["status"] in statuses
            ]
            total = sum(
                item["price"] * item["quantity"]
                for item in self.cart_items
                if item["session_id"] in {s["session_id"] for s in matches}
            )
            return {"count": len(matches), "total": total or 0}

        if "FROM orders" in sql and "COUNT(*)" in sql:
            statuses = args[1]
            matches = [
                o for o in self.orders.values() if o["wa_id"] == args[0] and o["status"] in statuses
            ]
            return {"count": len(matches), "total": sum(o["total"] for o in matches) or 0}

        raise AssertionError(f"Unexpected fetchrow SQL: {sql}")

    async def fetch(self, sql: str, *args):
        if "FROM cart_items" in sql:
            session_id = args[0]
            return [item for item in self.cart_items if item["session_id"] == session_id]

        if "FROM orders" in sql and "WHERE wa_id" in sql:
            matches = [o for o in self.orders.values() if o["wa_id"] == args[0]]
            matches.sort(key=lambda o: o["created_at"], reverse=True)
            return matches[: args[1]]

        if "FROM orders" in sql and "status = 'SCHEDULED'" in sql:
            as_of = args[0]
            matches = [
                o
                for o in self.orders.values()
                if o["status"] == "SCHEDULED"
                and o["target_placement_at"] is not None
                and o["target_placement_at"] <= as_of
            ]
            matches.sort(key=lambda o: o["target_placement_at"])
            return matches[: args[1]]

        raise AssertionError(f"Unexpected fetch SQL: {sql}")

    async def fetchval(self, sql: str, *args):
        if "SELECT EXISTS" in sql:
            return args[0] in self.sessions
        raise AssertionError(f"Unexpected fetchval SQL: {sql}")

    async def execute(self, sql: str, *args):
        if "DELETE FROM cart_items" in sql:
            session_id = args[0]
            self.cart_items = [item for item in self.cart_items if item["session_id"] != session_id]
            return "DELETE"

        if "INSERT INTO cart_items" in sql:
            row = {
                "id": self.next_cart_id,
                "session_id": args[0],
                "item_id": args[1],
                "name": args[2],
                "quantity": args[3],
                "price": args[4],
                "added_by": args[5],
                "dietary_tag": args[6],
                "vertical": args[7],
                "restaurant_id": args[8],
                "restaurant_name": args[9],
                "brand_name": args[10],
                "source_label": args[11],
                "created_at": datetime.now(UTC),
            }
            self.next_cart_id += 1
            self.cart_items.append(row)
            return "INSERT 0 1"

        if "UPDATE sessions SET status" in sql:
            session_id = args[0]
            if session_id not in self.sessions:
                return "UPDATE 0"
            self.sessions[session_id]["status"] = args[1]
            return "UPDATE 1"

        if "DELETE FROM sessions WHERE host_phone" in sql:
            host_phone = args[0]
            to_delete = [
                sid for sid, row in self.sessions.items() if row["host_phone"] == host_phone
            ]
            return self._delete_sessions(to_delete)

        if "DELETE FROM sessions WHERE created_at" in sql:
            cutoff = args[0]
            to_delete = [
                sid for sid, row in self.sessions.items() if row["created_at"] < cutoff
            ]
            return self._delete_sessions(to_delete)

        if "UPDATE orders SET status = $2" in sql:
            order_id = args[0]
            if order_id not in self.orders:
                return "UPDATE 0"
            self.orders[order_id]["status"] = args[1]
            return "UPDATE 1"

        if "SET status = 'SCHEDULED'" in sql:
            order_id = args[0]
            self.orders[order_id]["status"] = "SCHEDULED"
            self.orders[order_id]["target_placement_at"] = args[1]
            return "UPDATE 1"

        if "SET status = 'PLACED'" in sql:
            order_id = args[0]
            self.orders[order_id]["status"] = "PLACED"
            self.orders[order_id]["swiggy_order_id"] = args[1]
            return "UPDATE 1"

        if "SET status = 'FAILED'" in sql:
            order_id = args[0]
            self.orders[order_id]["status"] = "FAILED"
            self.orders[order_id]["failure_reason"] = args[1]
            return "UPDATE 1"

        if "SET status = 'PENDING_CONFIRMATION'" in sql:
            order_id = args[0]
            self.orders[order_id]["status"] = "PENDING_CONFIRMATION"
            self.orders[order_id]["items"] = args[1]
            self.orders[order_id]["total"] = args[2]
            return "UPDATE 1"

        raise AssertionError(f"Unexpected execute SQL: {sql}")

    def _delete_sessions(self, session_ids: list[str]) -> str:
        for session_id in session_ids:
            del self.sessions[session_id]
        self.cart_items = [
            item for item in self.cart_items if item["session_id"] not in session_ids
        ]
        self.session_events = [
            event for event in self.session_events if event["session_id"] not in session_ids
        ]
        return f"DELETE {len(session_ids)}"


def run(coro):
    return asyncio.run(coro)


def test_adapter_creates_session_with_initial_cart_in_transaction() -> None:
    connection = FakeConnection()
    adapter = AsyncPostgresDBAdapter(lambda: asyncio.sleep(0, result=connection))

    created = run(
        adapter.create_session(
            SessionCreate(
                whatsapp_group_id="group_ipl_fans_1",
                host_phone="919988776655",
                dietary_preference=DietaryTag.VEG,
            ),
            host_token_hash="abc123",
            guest_token="guest_public",
            cart_items=[
                CartItem(
                    item_id="food-paneer-roll",
                    name="Paneer tikka rolls",
                    quantity=4,
                    price=Decimal("180.00"),
                    added_by="919988776655",
                    dietary_tag=DietaryTag.VEG,
                    vertical=Vertical.FOOD,
                    restaurant_id="rest-roll-house",
                    restaurant_name="Roll House",
                )
            ],
        )
    )

    assert created.session_id.startswith("session_")
    assert created.host_token_hash == "abc123"
    assert created.guest_token == "guest_public"
    assert created.dietary_preference == DietaryTag.VEG
    assert created.cart_items[0].name == "Paneer tikka rolls"
    assert connection.transaction_depth == 0


def test_adapter_get_session_returns_session_with_cart_items() -> None:
    connection = FakeConnection()
    adapter = AsyncPostgresDBAdapter(lambda: asyncio.sleep(0, result=connection))
    created = run(
        adapter.create_session(
            SessionCreate(whatsapp_group_id="group", host_phone="host"),
            host_token_hash="hash",
            guest_token="guest",
        )
    )

    run(
        adapter.update_cart_items(
            created.session_id,
            [
                CartItem(
                    item_id="im-cola",
                    name="Cola 2L bottle",
                    price=Decimal("110.00"),
                    added_by="guest",
                    dietary_tag=DietaryTag.VEG,
                    vertical=Vertical.INSTAMART,
                    brand_name="Thums Up",
                    source_label="Instamart Mock Store",
                )
            ],
        )
    )

    loaded = run(adapter.get_session(created.session_id))

    assert loaded is not None
    assert loaded.session_id == created.session_id
    assert loaded.cart_items[0].item_id == "im-cola"
    assert loaded.cart_items[0].brand_name == "Thums Up"
    assert loaded.cart_items[0].source_label == "Instamart Mock Store"


def test_adapter_raises_for_missing_session_cart_or_status_updates() -> None:
    connection = FakeConnection()
    adapter = AsyncPostgresDBAdapter(lambda: asyncio.sleep(0, result=connection))

    with pytest.raises(SessionNotFoundError):
        run(adapter.update_cart_items("missing", []))

    with pytest.raises(SessionNotFoundError):
        run(adapter.update_session_status("missing", SessionStatus.ACTIVE))


def test_adapter_records_session_event_exactly_once() -> None:
    connection = FakeConnection()
    adapter = AsyncPostgresDBAdapter(lambda: asyncio.sleep(0, result=connection))
    event = SessionEvent(
        message_id="wamid.dedupe",
        event_type="whatsapp_tagged_message",
        session_id="session_abc123",
    )

    first = run(adapter.insert_session_event(event))
    second = run(adapter.insert_session_event(event))

    assert first is not None
    assert first.message_id == "wamid.dedupe"
    assert second is None
    assert len(connection.session_events) == 1


def test_adapter_gets_session_event_by_message_id_and_type() -> None:
    connection = FakeConnection()
    adapter = AsyncPostgresDBAdapter(lambda: asyncio.sleep(0, result=connection))
    run(
        adapter.insert_session_event(
            SessionEvent(
                message_id="wamid.lookup",
                event_type="whatsapp_tagged_message",
                session_id="session_abc123",
            )
        )
    )

    found = run(adapter.get_session_event("wamid.lookup", "whatsapp_tagged_message"))
    missing = run(adapter.get_session_event("wamid.other", "whatsapp_tagged_message"))
    wrong_type = run(adapter.get_session_event("wamid.lookup", "other_event"))

    assert found is not None
    assert found.session_id == "session_abc123"
    assert missing is None
    assert wrong_type is None


def test_adapter_deletes_sessions_for_host() -> None:
    connection = FakeConnection()
    adapter = AsyncPostgresDBAdapter(lambda: asyncio.sleep(0, result=connection))
    run(
        adapter.create_session(
            SessionCreate(whatsapp_group_id="group_1", host_phone="919988776655"),
            host_token_hash="h1",
            guest_token="g1",
        )
    )
    run(
        adapter.create_session(
            SessionCreate(whatsapp_group_id="group_2", host_phone="919988776655"),
            host_token_hash="h2",
            guest_token="g2",
        )
    )
    run(
        adapter.create_session(
            SessionCreate(whatsapp_group_id="group_3", host_phone="911111111111"),
            host_token_hash="h3",
            guest_token="g3",
        )
    )

    deleted = run(adapter.delete_sessions_for_host("919988776655"))

    assert deleted == 2
    assert len(connection.sessions) == 1
    assert next(iter(connection.sessions.values()))["host_phone"] == "911111111111"


def test_adapter_deletes_sessions_older_than_cutoff() -> None:
    connection = FakeConnection()
    adapter = AsyncPostgresDBAdapter(lambda: asyncio.sleep(0, result=connection))
    run(
        adapter.create_session(
            SessionCreate(whatsapp_group_id="group_1", host_phone="919988776655"),
            host_token_hash="h1",
            guest_token="g1",
        )
    )
    old_session_id = next(iter(connection.sessions))
    connection.sessions[old_session_id]["created_at"] = datetime(2020, 1, 1, tzinfo=UTC)
    run(
        adapter.create_session(
            SessionCreate(whatsapp_group_id="group_2", host_phone="911111111111"),
            host_token_hash="h2",
            guest_token="g2",
        )
    )

    deleted = run(adapter.delete_sessions_older_than(datetime(2025, 1, 1, tzinfo=UTC)))

    assert deleted == 1
    assert len(connection.sessions) == 1


def _order_create(**overrides) -> OrderCreate:
    defaults = dict(
        wa_id="919988776655",
        restaurant_id="rest-moti-mahal",
        restaurant_name="MotiMahal",
        items=[OrderLineItem(item_id="food-mm-paneer-tikka", name="Paneer Tikka", price="260.00")],
        total="260.00",
    )
    defaults.update(overrides)
    return OrderCreate(**defaults)


def test_adapter_creates_and_reads_back_an_order() -> None:
    connection = FakeConnection()
    adapter = AsyncPostgresDBAdapter(lambda: asyncio.sleep(0, result=connection))

    created = run(
        adapter.create_order(_order_create(budget_limit="800.00", source_message_id="wamid.1"))
    )
    fetched = run(adapter.get_order(created.order_id))
    by_message = run(adapter.get_order_by_source_message_id("wamid.1"))

    assert fetched.order_id == created.order_id
    assert fetched.items[0].name == "Paneer Tikka"
    assert fetched.budget_limit == Decimal("800.00")
    assert by_message.order_id == created.order_id
    assert run(adapter.get_order_by_source_message_id("wamid.missing")) is None


def test_adapter_pending_confirmation_lookup() -> None:
    connection = FakeConnection()
    adapter = AsyncPostgresDBAdapter(lambda: asyncio.sleep(0, result=connection))
    run(adapter.create_order(_order_create(status=OrderStatus.PENDING_CONFIRMATION)))
    run(adapter.create_order(_order_create(wa_id="911111111111", status=OrderStatus.PLACED)))

    pending = run(adapter.get_pending_confirmation_order("919988776655"))
    none_pending = run(adapter.get_pending_confirmation_order("911111111111"))

    assert pending is not None
    assert none_pending is None


def test_adapter_order_status_transitions() -> None:
    connection = FakeConnection()
    adapter = AsyncPostgresDBAdapter(lambda: asyncio.sleep(0, result=connection))
    created = run(adapter.create_order(_order_create(status=OrderStatus.PENDING_CONFIRMATION)))

    target = datetime.now(UTC) + timedelta(hours=1)
    run(adapter.set_order_scheduled(created.order_id, target_placement_at=target))
    assert run(adapter.get_order(created.order_id)).status == "SCHEDULED"

    run(adapter.set_order_placed(created.order_id, swiggy_order_id="order-42"))
    placed = run(adapter.get_order(created.order_id))
    assert placed.status == "PLACED"
    assert placed.swiggy_order_id == "order-42"

    run(adapter.set_order_failed(created.order_id, failure_reason="boom"))
    failed = run(adapter.get_order(created.order_id))
    assert failed.status == "FAILED"
    assert failed.failure_reason == "boom"

    run(adapter.update_order_status(created.order_id, OrderStatus.CANCELLED))
    assert run(adapter.get_order(created.order_id)).status == "CANCELLED"


def test_adapter_set_order_price_changed_resets_to_pending_confirmation() -> None:
    connection = FakeConnection()
    adapter = AsyncPostgresDBAdapter(lambda: asyncio.sleep(0, result=connection))
    created = run(adapter.create_order(_order_create(status=OrderStatus.SCHEDULED)))

    new_items = [OrderLineItem(item_id="food-mm-chicken-65", name="Chicken 65", price="345.00")]
    run(adapter.set_order_price_changed(created.order_id, items=new_items, total=Decimal("345.00")))

    updated = run(adapter.get_order(created.order_id))
    assert updated.status == "PENDING_CONFIRMATION"
    assert updated.total == Decimal("345.00")
    assert updated.items[0].name == "Chicken 65"


def test_adapter_list_orders_for_host_and_due_scheduled_orders() -> None:
    connection = FakeConnection()
    adapter = AsyncPostgresDBAdapter(lambda: asyncio.sleep(0, result=connection))
    run(adapter.create_order(_order_create(wa_id="919988776655")))
    run(adapter.create_order(_order_create(wa_id="919988776655")))
    run(adapter.create_order(_order_create(wa_id="911111111111")))

    now = datetime.now(UTC)
    due = run(
        adapter.create_order(
            _order_create(
                wa_id="919900000000",
                status=OrderStatus.SCHEDULED,
                target_placement_at=now - timedelta(minutes=1),
            )
        )
    )
    run(
        adapter.create_order(
            _order_create(
                wa_id="919900000000",
                status=OrderStatus.SCHEDULED,
                target_placement_at=now + timedelta(hours=1),
            )
        )
    )

    listed = run(adapter.list_orders_for_host("919988776655"))
    due_orders = run(adapter.get_due_scheduled_orders(as_of=now))

    assert len(listed) == 2
    assert all(order.wa_id == "919988776655" for order in listed)
    assert [order.order_id for order in due_orders] == [due.order_id]


def test_adapter_spend_summary_counts_only_committed_records() -> None:
    connection = FakeConnection()
    adapter = AsyncPostgresDBAdapter(lambda: asyncio.sleep(0, result=connection))
    wa_id = "919988776655"

    run(adapter.create_order(_order_create(wa_id=wa_id, total="300.00")))
    run(
        adapter.create_order(
            _order_create(wa_id=wa_id, total="250.50", status=OrderStatus.DELIVERED)
        )
    )
    run(
        adapter.create_order(
            _order_create(wa_id=wa_id, total="900.00", status=OrderStatus.SCHEDULED)
        )
    )
    run(
        adapter.create_order(
            _order_create(wa_id=wa_id, total="500.00", status=OrderStatus.CANCELLED)
        )
    )
    run(adapter.create_order(_order_create(wa_id="911111111111", total="999.00")))

    ordered = run(
        adapter.create_session(
            SessionCreate(whatsapp_group_id="group_1", host_phone=wa_id),
            host_token_hash="hash",
            guest_token="guest_1",
            cart_items=[
                CartItem(
                    item_id="food-biryani",
                    name="Chicken Biryani",
                    quantity=2,
                    price=Decimal("339.00"),
                    added_by=wa_id,
                    vertical=Vertical.FOOD,
                    restaurant_id="rest-1",
                    restaurant_name="Paradise",
                )
            ],
        )
    )
    run(adapter.update_session_status(ordered.session_id, SessionStatus.ORDERED))
    # Still being planned — intent, not spend.
    run(
        adapter.create_session(
            SessionCreate(whatsapp_group_id="group_2", host_phone=wa_id),
            host_token_hash="hash",
            guest_token="guest_2",
            cart_items=[
                CartItem(
                    item_id="food-roti",
                    name="Tandoori Roti",
                    quantity=3,
                    price=Decimal("49.00"),
                    added_by=wa_id,
                    vertical=Vertical.FOOD,
                    restaurant_id="rest-1",
                    restaurant_name="Paradise",
                )
            ],
        )
    )

    summary = run(adapter.get_spend_summary(wa_id))

    assert summary.restaurant_orders.count == 2
    assert summary.restaurant_orders.total == Decimal("550.50")
    assert summary.group_orders.count == 1
    assert summary.group_orders.total == Decimal("678.00")
    assert summary.total == Decimal("1228.50")
    assert summary.order_count == 3
