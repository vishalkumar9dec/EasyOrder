"""Protocol interfaces for EasyOrder services.

Every module must have a Protocol interface so production clients
can be swapped for mocks in tests (AGENTS.md rule #23).
"""

from __future__ import annotations

from typing import Protocol

from app.models.session import Session
from app.models.whatsapp import IncomingMessage


class IAgentService(Protocol):
    """Interface for the LangGraph agent orchestrator.

    The webhook handler calls ``handle_tagged_message`` when a message
    contains the ``@EasyOrder`` tag. The agent is responsible for:
    1. Parsing intent (budget, headcount, dietary prefs)
    2. Querying Swiggy MCP
    3. Building a recommended cart
    4. Persisting the session with results
    """

    async def handle_tagged_message(self, message: IncomingMessage) -> Session:
        """Process a tagged @EasyOrder message and return the initialized session."""
        ...


class ISessionStore(Protocol):
    """Interface for session persistence.

    In production this talks to PostgreSQL via Supabase.
    In mock mode it uses an in-memory dict.
    """

    async def create_session(self, session: Session) -> Session:
        """Persist a new session and return it."""
        ...

    async def get_session(self, session_id: str) -> Session | None:
        """Retrieve a session by ID, or None if not found."""
        ...

    async def update_session_status(self, session_id: str, status: str) -> None:
        """Update a session's status field."""
        ...
