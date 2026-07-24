"""In-memory persistence adapters for local agent and API tests."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from app.models.session import CartItem, Session, SessionCreate, SessionEvent, SessionStatus
from app.services.protocols import IDBAdapter, ISessionStore


class InMemoryDBAdapter(IDBAdapter, ISessionStore):
    """Small IDBAdapter implementation used in local mock mode."""

    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}
        self.events: list[SessionEvent] = []
        self.next_cart_id = 1
        self._next_event_id = 1

    async def create_session(
        self,
        session: SessionCreate | Session,
        host_token_hash: str | None = None,
        guest_token: str | None = None,
        cart_items: Sequence[CartItem] | None = None,
    ) -> Session:
        if isinstance(session, Session):
            created = session
        else:
            if host_token_hash is None or guest_token is None:
                raise ValueError("host_token_hash and guest_token are required")
            created = Session(
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

        created.cart_items = self._assign_cart(created.session_id, cart_items or created.cart_items)
        self.sessions[created.session_id] = created
        return created

    async def get_session(self, session_id: str) -> Session | None:
        return self.sessions.get(session_id)

    async def get_latest_session_for_host(self, host_phone: str) -> Session | None:
        candidates = [s for s in self.sessions.values() if s.host_phone == host_phone]
        if not candidates:
            return None
        return max(candidates, key=lambda s: (s.created_at, s.session_id))

    async def list_sessions_for_host(self, host_phone: str, *, limit: int = 10) -> list[Session]:
        candidates = [s for s in self.sessions.values() if s.host_phone == host_phone]
        candidates.sort(key=lambda s: (s.created_at, s.session_id), reverse=True)
        return candidates[:limit]

    async def delete_sessions_for_host(self, host_phone: str) -> int:
        to_delete = [
            session_id
            for session_id, session in self.sessions.items()
            if session.host_phone == host_phone
        ]
        for session_id in to_delete:
            del self.sessions[session_id]
        self.events = [e for e in self.events if e.session_id not in to_delete]
        return len(to_delete)

    async def delete_sessions_older_than(self, cutoff: datetime) -> int:
        to_delete = [
            session_id
            for session_id, session in self.sessions.items()
            if session.created_at < cutoff
        ]
        for session_id in to_delete:
            del self.sessions[session_id]
        self.events = [e for e in self.events if e.session_id not in to_delete]
        return len(to_delete)

    async def update_cart_items(self, session_id: str, items: Sequence[CartItem]) -> list[CartItem]:
        session = self.sessions[session_id]
        session.cart_items = self._assign_cart(session_id, items)
        return session.cart_items

    async def update_session_status(self, session_id: str, status: SessionStatus | str) -> None:
        if session := self.sessions.get(session_id):
            session.status = status  # type: ignore[assignment]

    async def insert_session_event(self, event: SessionEvent) -> SessionEvent | None:
        from datetime import UTC, datetime

        # Mirror the unique (message_id, event_type) index: reject duplicates
        # so webhook retries cannot double-record ledger events.
        if event.message_id is not None and await self.get_session_event(
            event.message_id, str(event.event_type)
        ):
            return None
        stored = event.model_copy(
            update={"id": self._next_event_id, "created_at": datetime.now(UTC)}
        )
        self._next_event_id += 1
        self.events.append(stored)
        return stored

    async def get_session_event(self, message_id: str, event_type: str) -> SessionEvent | None:
        for event in self.events:
            if event.message_id == message_id and str(event.event_type) == str(event_type):
                return event
        return None

    async def get_session_events(self, session_id: str) -> list[SessionEvent]:
        return [e for e in self.events if e.session_id == session_id]

    def _assign_cart(self, session_id: str, items: Sequence[CartItem]) -> list[CartItem]:
        assigned: list[CartItem] = []
        for item in items:
            assigned_item = item.model_copy(
                update={
                    "id": item.id or self.next_cart_id,
                    "session_id": session_id,
                }
            )
            if item.id is None:
                self.next_cart_id += 1
            assigned.append(assigned_item)
        return assigned
