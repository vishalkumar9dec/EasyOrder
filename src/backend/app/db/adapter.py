"""Async PostgreSQL adapter for EasyOrder sessions and carts."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.models.order import Order, OrderCreate, OrderLineItem, OrderStatus
from app.models.session import (
    CartItem,
    EventType,
    Session,
    SessionCreate,
    SessionEvent,
    SessionStatus,
)
from app.models.spend import (
    SPENT_ORDER_STATUSES,
    SPENT_SESSION_STATUSES,
    SpendBucket,
    SpendSummary,
)


class DatabaseAdapterError(RuntimeError):
    """Base error raised by the database adapter."""


class SessionNotFoundError(DatabaseAdapterError):
    """Raised when a requested session does not exist."""


ConnectionFactory = Callable[[], Awaitable[Any]]


def _as_decimal(value: Any) -> Decimal:
    """Normalize an aggregate result to Decimal.

    ``COALESCE(SUM(...), 0)`` comes back as Decimal from asyncpg, but the zero
    branch can arrive as an int, and a driver in mock mode may hand back a
    float — quantize once here rather than at every call site.
    """
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _deleted_row_count(execute_result: str) -> int:
    """Parse asyncpg's ``execute()`` status tag, e.g. ``"DELETE 3"`` -> ``3``."""
    try:
        return int(execute_result.rsplit(" ", 1)[-1])
    except (ValueError, AttributeError):
        return 0


def asyncpg_connection_factory(database_url: str) -> ConnectionFactory:
    """Per-operation asyncpg connection factory shared by Postgres-backed services."""

    async def get_connection() -> Any:
        try:
            import asyncpg
        except ImportError as error:  # pragma: no cover - environment guard
            raise DatabaseAdapterError(
                "asyncpg is required for PostgreSQL persistence"
            ) from error

        return await asyncpg.connect(database_url)

    return get_connection


class AsyncPostgresDBAdapter:
    """PostgreSQL implementation of the session persistence boundary.

    The adapter expects an async connection factory. Production uses ``asyncpg``
    connections; tests can inject a lightweight fake.
    """

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    @classmethod
    def from_database_url(cls, database_url: str) -> AsyncPostgresDBAdapter:
        """Build an adapter backed by per-operation ``asyncpg`` connections."""
        return cls(asyncpg_connection_factory(database_url))

    async def create_session(
        self,
        session: SessionCreate,
        host_token_hash: str,
        guest_token: str,
        cart_items: Sequence[CartItem] | None = None,
    ) -> Session:
        """Create a session and initial cart in one transaction."""

        connection = await self._connection_factory()
        session_model = Session(
            whatsapp_group_id=session.whatsapp_group_id,
            host_phone=session.host_phone,
            host_token_hash=host_token_hash,
            guest_token=guest_token,
            budget_limit=session.budget_limit,
            head_count=session.head_count,
            dietary_preference=session.dietary_preference,
            status=session.status,
            budget_warning=session.budget_warning,
            degraded_verticals=session.degraded_verticals,
            warnings=session.warnings,
        )

        try:
            async with connection.transaction():
                row = await connection.fetchrow(
                    """
                    INSERT INTO sessions (
                        session_id,
                        whatsapp_group_id,
                        host_phone,
                        host_token_hash,
                        guest_token,
                        budget_limit,
                        head_count,
                        dietary_preference,
                        status,
                        budget_warning,
                        degraded_verticals,
                        warnings
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb)
                    RETURNING *
                    """,
                    session_model.session_id,
                    session_model.whatsapp_group_id,
                    session_model.host_phone,
                    session_model.host_token_hash,
                    session_model.guest_token,
                    session_model.budget_limit,
                    session_model.head_count,
                    session_model.dietary_preference,
                    session_model.status,
                    session_model.budget_warning,
                    list(session_model.degraded_verticals),
                    json.dumps([warning.model_dump() for warning in session_model.warnings]),
                )
                persisted_session = self._session_from_row(row)
                if cart_items:
                    await self._replace_cart_items(
                        connection,
                        persisted_session.session_id,
                        cart_items,
                    )
                    persisted_session.cart_items = await self._fetch_cart_items(
                        connection,
                        persisted_session.session_id,
                    )
                return persisted_session
        except DatabaseAdapterError:
            raise
        except Exception as error:  # pragma: no cover - mapped in tests via fakes
            raise DatabaseAdapterError("Failed to create session") from error
        finally:
            await self._close_connection(connection)

    async def get_session(self, session_id: str) -> Session | None:
        """Read a session with its cart items."""

        connection = await self._connection_factory()
        try:
            row = await connection.fetchrow(
                "SELECT * FROM sessions WHERE session_id = $1",
                session_id,
            )
            if row is None:
                return None

            session = self._session_from_row(row)
            session.cart_items = await self._fetch_cart_items(connection, session_id)
            return session
        finally:
            await self._close_connection(connection)

    async def get_latest_session_for_host(self, host_phone: str) -> Session | None:
        """Read the most recent session created by a host wa_id, with cart items."""

        connection = await self._connection_factory()
        try:
            row = await connection.fetchrow(
                """
                SELECT * FROM sessions
                WHERE host_phone = $1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                host_phone,
            )
            if row is None:
                return None

            session = self._session_from_row(row)
            session.cart_items = await self._fetch_cart_items(connection, session.session_id)
            return session
        finally:
            await self._close_connection(connection)

    async def list_sessions_for_host(self, host_phone: str, *, limit: int = 10) -> list[Session]:
        """Read the most recent sessions created by a host wa_id, newest first."""

        connection = await self._connection_factory()
        try:
            rows = await connection.fetch(
                """
                SELECT * FROM sessions
                WHERE host_phone = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                host_phone,
                limit,
            )
            sessions = []
            for row in rows:
                session = self._session_from_row(row)
                session.cart_items = await self._fetch_cart_items(connection, session.session_id)
                sessions.append(session)
            return sessions
        finally:
            await self._close_connection(connection)

    async def delete_sessions_for_host(self, host_phone: str) -> int:
        """Delete every session for a host wa_id; cart_items/session_events cascade."""

        connection = await self._connection_factory()
        try:
            result = await connection.execute(
                "DELETE FROM sessions WHERE host_phone = $1",
                host_phone,
            )
            return _deleted_row_count(result)
        finally:
            await self._close_connection(connection)

    async def delete_sessions_older_than(self, cutoff: datetime) -> int:
        """Delete every session older than ``cutoff``; cascades to cart/timeline data."""

        connection = await self._connection_factory()
        try:
            result = await connection.execute(
                "DELETE FROM sessions WHERE created_at < $1",
                cutoff,
            )
            return _deleted_row_count(result)
        finally:
            await self._close_connection(connection)

    async def update_cart_items(self, session_id: str, items: Sequence[CartItem]) -> list[CartItem]:
        """Atomically replace the persisted cart for a session."""

        connection = await self._connection_factory()
        try:
            exists = await connection.fetchval(
                "SELECT EXISTS (SELECT 1 FROM sessions WHERE session_id = $1)",
                session_id,
            )
            if not exists:
                raise SessionNotFoundError(f"Session {session_id} was not found")

            async with connection.transaction():
                await self._replace_cart_items(connection, session_id, items)
                return await self._fetch_cart_items(connection, session_id)
        finally:
            await self._close_connection(connection)

    async def update_session_status(self, session_id: str, status: SessionStatus | str) -> None:
        """Update session lifecycle status."""

        connection = await self._connection_factory()
        try:
            result = await connection.execute(
                "UPDATE sessions SET status = $2 WHERE session_id = $1",
                session_id,
                str(status),
            )
            if result == "UPDATE 0":
                raise SessionNotFoundError(f"Session {session_id} was not found")
        finally:
            await self._close_connection(connection)

    async def insert_session_event(self, event: SessionEvent) -> SessionEvent | None:
        """Persist one session timeline event and return it with id and created_at.

        Returns None when the (message_id, event_type) pair was already
        recorded, so webhook retries cannot double-record ledger events.
        """

        connection = await self._connection_factory()
        try:
            row = await connection.fetchrow(
                """
                INSERT INTO session_events (
                    session_id, event_type, message_text, intent_label,
                    message_id, sender_wa_id, mode, request_id
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (message_id, event_type) DO NOTHING
                RETURNING *
                """,
                event.session_id,
                str(event.event_type),
                event.message_text,
                event.intent_label,
                event.message_id,
                event.sender_wa_id,
                event.mode,
                event.request_id,
            )
            return self._session_event_from_row(row) if row is not None else None
        finally:
            await self._close_connection(connection)

    async def get_session_event(self, message_id: str, event_type: str) -> SessionEvent | None:
        """Return the recorded event for a processed message, or None."""

        connection = await self._connection_factory()
        try:
            row = await connection.fetchrow(
                """
                SELECT * FROM session_events
                WHERE message_id = $1 AND event_type = $2
                """,
                message_id,
                str(event_type),
            )
            return self._session_event_from_row(row) if row is not None else None
        finally:
            await self._close_connection(connection)

    async def get_session_events(self, session_id: str) -> list[SessionEvent]:
        """Fetch all timeline events for a session, ordered oldest-first."""

        connection = await self._connection_factory()
        try:
            rows = await connection.fetch(
                """
                SELECT * FROM session_events
                WHERE session_id = $1
                ORDER BY created_at
                """,
                session_id,
            )
            return [self._session_event_from_row(row) for row in rows]
        finally:
            await self._close_connection(connection)

    async def create_order(self, order: OrderCreate) -> Order:
        """Persist a new targeted order."""

        connection = await self._connection_factory()
        order_model = Order(**order.model_dump())
        try:
            row = await connection.fetchrow(
                """
                INSERT INTO orders (
                    order_id, wa_id, restaurant_id, restaurant_name, items, total,
                    budget_limit, delivery_deadline, target_placement_at, status,
                    source_message_id
                )
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10, $11)
                RETURNING *
                """,
                order_model.order_id,
                order_model.wa_id,
                order_model.restaurant_id,
                order_model.restaurant_name,
                json.dumps([item.model_dump(mode="json") for item in order_model.items]),
                order_model.total,
                order_model.budget_limit,
                order_model.delivery_deadline,
                order_model.target_placement_at,
                order_model.status,
                order_model.source_message_id,
            )
            return self._order_from_row(row)
        except DatabaseAdapterError:
            raise
        except Exception as error:  # pragma: no cover - mapped in tests via fakes
            raise DatabaseAdapterError("Failed to create order") from error
        finally:
            await self._close_connection(connection)

    async def get_order(self, order_id: str) -> Order | None:
        connection = await self._connection_factory()
        try:
            row = await connection.fetchrow("SELECT * FROM orders WHERE order_id = $1", order_id)
            return self._order_from_row(row) if row is not None else None
        finally:
            await self._close_connection(connection)

    async def get_order_by_source_message_id(self, message_id: str) -> Order | None:
        connection = await self._connection_factory()
        try:
            row = await connection.fetchrow(
                "SELECT * FROM orders WHERE source_message_id = $1", message_id
            )
            return self._order_from_row(row) if row is not None else None
        finally:
            await self._close_connection(connection)

    async def get_pending_confirmation_order(self, wa_id: str) -> Order | None:
        connection = await self._connection_factory()
        try:
            row = await connection.fetchrow(
                "SELECT * FROM orders WHERE wa_id = $1 AND status = 'PENDING_CONFIRMATION'",
                wa_id,
            )
            return self._order_from_row(row) if row is not None else None
        finally:
            await self._close_connection(connection)

    async def list_orders_for_host(self, wa_id: str, *, limit: int = 30) -> list[Order]:
        connection = await self._connection_factory()
        try:
            rows = await connection.fetch(
                """
                SELECT * FROM orders
                WHERE wa_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                wa_id,
                limit,
            )
            return [self._order_from_row(row) for row in rows]
        finally:
            await self._close_connection(connection)

    async def get_spend_summary(self, wa_id: str) -> SpendSummary:
        """Aggregate committed spend in SQL, over every record — not just a page of them."""

        connection = await self._connection_factory()
        try:
            group_row = await connection.fetchrow(
                """
                SELECT
                    COUNT(*) AS count,
                    COALESCE(SUM(cart.total), 0) AS total
                FROM sessions s
                LEFT JOIN LATERAL (
                    SELECT SUM(ci.price * ci.quantity) AS total
                    FROM cart_items ci
                    WHERE ci.session_id = s.session_id
                ) cart ON TRUE
                WHERE s.host_phone = $1 AND s.status = ANY($2::text[])
                """,
                wa_id,
                [str(status) for status in SPENT_SESSION_STATUSES],
            )
            order_row = await connection.fetchrow(
                """
                SELECT
                    COUNT(*) AS count,
                    COALESCE(SUM(total), 0) AS total
                FROM orders
                WHERE wa_id = $1 AND status = ANY($2::text[])
                """,
                wa_id,
                [str(status) for status in SPENT_ORDER_STATUSES],
            )
            return SpendSummary(
                group_orders=SpendBucket(
                    total=_as_decimal(group_row["total"]),
                    count=group_row["count"],
                ),
                restaurant_orders=SpendBucket(
                    total=_as_decimal(order_row["total"]),
                    count=order_row["count"],
                ),
            )
        finally:
            await self._close_connection(connection)

    async def get_due_scheduled_orders(
        self,
        *,
        as_of: datetime,
        limit: int = 20,
    ) -> list[Order]:
        connection = await self._connection_factory()
        try:
            rows = await connection.fetch(
                """
                SELECT * FROM orders
                WHERE status = 'SCHEDULED' AND target_placement_at <= $1
                ORDER BY target_placement_at
                LIMIT $2
                """,
                as_of,
                limit,
            )
            return [self._order_from_row(row) for row in rows]
        finally:
            await self._close_connection(connection)

    async def update_order_status(self, order_id: str, status: OrderStatus | str) -> None:
        connection = await self._connection_factory()
        try:
            await connection.execute(
                "UPDATE orders SET status = $2, updated_at = NOW() WHERE order_id = $1",
                order_id,
                str(status),
            )
        finally:
            await self._close_connection(connection)

    async def set_order_scheduled(self, order_id: str, *, target_placement_at: datetime) -> None:
        connection = await self._connection_factory()
        try:
            await connection.execute(
                """
                UPDATE orders
                SET status = 'SCHEDULED', target_placement_at = $2, updated_at = NOW()
                WHERE order_id = $1
                """,
                order_id,
                target_placement_at,
            )
        finally:
            await self._close_connection(connection)

    async def set_order_placed(self, order_id: str, *, swiggy_order_id: str) -> None:
        connection = await self._connection_factory()
        try:
            await connection.execute(
                """
                UPDATE orders
                SET status = 'PLACED', swiggy_order_id = $2, updated_at = NOW()
                WHERE order_id = $1
                """,
                order_id,
                swiggy_order_id,
            )
        finally:
            await self._close_connection(connection)

    async def set_order_failed(self, order_id: str, *, failure_reason: str) -> None:
        connection = await self._connection_factory()
        try:
            await connection.execute(
                """
                UPDATE orders
                SET status = 'FAILED', failure_reason = $2, updated_at = NOW()
                WHERE order_id = $1
                """,
                order_id,
                failure_reason,
            )
        finally:
            await self._close_connection(connection)

    async def set_order_price_changed(
        self,
        order_id: str,
        *,
        items: Sequence[OrderLineItem],
        total: Decimal,
    ) -> None:
        connection = await self._connection_factory()
        try:
            await connection.execute(
                """
                UPDATE orders
                SET status = 'PENDING_CONFIRMATION', items = $2::jsonb, total = $3,
                    updated_at = NOW()
                WHERE order_id = $1
                """,
                order_id,
                json.dumps([item.model_dump(mode="json") for item in items]),
                total,
            )
        finally:
            await self._close_connection(connection)

    @staticmethod
    def _order_from_row(row: Any) -> Order:
        data = dict(row)
        data["total"] = Decimal(str(data["total"]))
        if data.get("budget_limit") is not None:
            data["budget_limit"] = Decimal(str(data["budget_limit"]))
        items = data.get("items") or []
        if isinstance(items, str):
            items = json.loads(items)
        data["items"] = [OrderLineItem(**item) for item in items]
        return Order(**data)

    async def _replace_cart_items(
        self,
        connection: Any,
        session_id: str,
        items: Sequence[CartItem],
    ) -> None:
        await connection.execute("DELETE FROM cart_items WHERE session_id = $1", session_id)
        for item in items:
            await connection.execute(
                """
                INSERT INTO cart_items (
                    session_id,
                    item_id,
                    name,
                    quantity,
                    price,
                    added_by,
                    dietary_tag,
                    vertical,
                    restaurant_id,
                    restaurant_name,
                    brand_name,
                    source_label
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                session_id,
                item.item_id,
                item.name,
                item.quantity,
                item.price,
                item.added_by,
                item.dietary_tag,
                item.vertical,
                item.restaurant_id,
                item.restaurant_name,
                item.brand_name,
                item.source_label,
            )

    async def _fetch_cart_items(self, connection: Any, session_id: str) -> list[CartItem]:
        rows = await connection.fetch(
            """
            SELECT *
            FROM cart_items
            WHERE session_id = $1
            ORDER BY id
            """,
            session_id,
        )
        return [self._cart_item_from_row(row) for row in rows]

    @staticmethod
    def _session_from_row(row: Any) -> Session:
        data = dict(row)
        data["budget_limit"] = Decimal(str(data["budget_limit"]))
        data["degraded_verticals"] = list(data.get("degraded_verticals") or [])
        warnings = data.get("warnings") or []
        if isinstance(warnings, str):
            warnings = json.loads(warnings)
        data["warnings"] = list(warnings)
        return Session(**data)

    @staticmethod
    def _cart_item_from_row(row: Any) -> CartItem:
        data = dict(row)
        data["price"] = Decimal(str(data["price"]))
        return CartItem(**data)

    @staticmethod
    def _session_event_from_row(row: Any) -> SessionEvent:
        data = dict(row)
        return SessionEvent(
            id=data["id"],
            session_id=data["session_id"],
            event_type=EventType(data["event_type"]),
            message_text=data.get("message_text"),
            intent_label=data.get("intent_label"),
            message_id=data.get("message_id"),
            sender_wa_id=data.get("sender_wa_id"),
            mode=data.get("mode"),
            request_id=data.get("request_id"),
            created_at=data.get("created_at"),
        )

    @staticmethod
    async def _close_connection(connection: Any) -> None:
        close = getattr(connection, "close", None)
        if close is not None:
            result = close()
            if hasattr(result, "__await__"):
                await result
