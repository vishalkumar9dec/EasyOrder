"""Async PostgreSQL adapter for EasyOrder sessions and carts."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Sequence
from decimal import Decimal
from typing import Any

from app.models.session import (
    CartItem,
    EventType,
    Session,
    SessionCreate,
    SessionEvent,
    SessionStatus,
)


class DatabaseAdapterError(RuntimeError):
    """Base error raised by the database adapter."""


class SessionNotFoundError(DatabaseAdapterError):
    """Raised when a requested session does not exist."""


ConnectionFactory = Callable[[], Awaitable[Any]]


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

        async def get_connection() -> Any:
            try:
                import asyncpg
            except ImportError as error:  # pragma: no cover - environment guard
                raise DatabaseAdapterError(
                    "asyncpg is required for PostgreSQL persistence"
                ) from error

            return await asyncpg.connect(database_url)

        return cls(get_connection)

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
