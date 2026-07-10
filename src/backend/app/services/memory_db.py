"""In-memory persistence adapters for local agent and API tests."""

from __future__ import annotations

from collections.abc import Sequence

from app.models.session import CartItem, Session, SessionCreate, SessionEvent, SessionStatus
from app.services.protocols import IDBAdapter, ISessionStore


class InMemoryDBAdapter(IDBAdapter, ISessionStore):
    """Small IDBAdapter implementation used in local mock mode."""

    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}
        self.session_events: dict[tuple[str, str], SessionEvent] = {}
        self.next_cart_id = 1

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

    async def update_cart_items(self, session_id: str, items: Sequence[CartItem]) -> list[CartItem]:
        session = self.sessions[session_id]
        session.cart_items = self._assign_cart(session_id, items)
        return session.cart_items

    async def update_session_status(self, session_id: str, status: SessionStatus | str) -> None:
        if session := self.sessions.get(session_id):
            session.status = status  # type: ignore[assignment]

    async def get_session_event(self, message_id: str, event_type: str) -> SessionEvent | None:
        return self.session_events.get((message_id, event_type))

    async def insert_session_event(self, event: SessionEvent) -> SessionEvent | None:
        key = (event.message_id, event.event_type)
        if key in self.session_events:
            return None
        stored = event.model_copy(update={"id": len(self.session_events) + 1})
        self.session_events[key] = stored
        return stored

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
