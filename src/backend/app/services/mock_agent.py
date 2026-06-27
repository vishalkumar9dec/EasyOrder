"""Mock service implementations for local webhook development."""

from __future__ import annotations

from app.models.session import Session, generate_host_token, hash_host_token
from app.models.whatsapp import IncomingMessage
from app.services.protocols import IAgentService, ISessionStore


class InMemorySessionStore(ISessionStore):
    """Small in-memory store used until PostgreSQL session persistence lands."""

    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}

    async def create_session(self, session: Session) -> Session:
        self.sessions[session.session_id] = session
        return session

    async def get_session(self, session_id: str) -> Session | None:
        return self.sessions.get(session_id)

    async def update_session_status(self, session_id: str, status: str) -> None:
        if session := self.sessions.get(session_id):
            session.status = status  # type: ignore[assignment]


class MockAgentService(IAgentService):
    """Creates a deterministic session without invoking LLMs or Swiggy."""

    def __init__(self, store: ISessionStore) -> None:
        self.store = store
        self.handled_messages: list[IncomingMessage] = []

    async def handle_tagged_message(self, message: IncomingMessage) -> Session:
        self.handled_messages.append(message)
        raw_host_token = generate_host_token()
        session = Session(
            whatsapp_group_id=message.phone_number_id,
            host_phone=message.sender_id,
            host_token_hash=hash_host_token(raw_host_token),
        )
        return await self.store.create_session(session)
