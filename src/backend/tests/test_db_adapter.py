import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.db.adapter import AsyncPostgresDBAdapter, SessionNotFoundError
from app.models.session import CartItem, DietaryTag, SessionCreate, SessionStatus, Vertical


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

        raise AssertionError(f"Unexpected fetchrow SQL: {sql}")

    async def fetch(self, sql: str, *args):
        if "FROM cart_items" in sql:
            session_id = args[0]
            return [item for item in self.cart_items if item["session_id"] == session_id]
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

        raise AssertionError(f"Unexpected execute SQL: {sql}")


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
                )
            ],
        )
    )

    loaded = run(adapter.get_session(created.session_id))

    assert loaded is not None
    assert loaded.session_id == created.session_id
    assert loaded.cart_items[0].item_id == "im-cola"


def test_adapter_raises_for_missing_session_cart_or_status_updates() -> None:
    connection = FakeConnection()
    adapter = AsyncPostgresDBAdapter(lambda: asyncio.sleep(0, result=connection))

    with pytest.raises(SessionNotFoundError):
        run(adapter.update_cart_items("missing", []))

    with pytest.raises(SessionNotFoundError):
        run(adapter.update_session_status("missing", SessionStatus.ACTIVE))
