"""Protocol interfaces for EasyOrder services.

Every module must have a Protocol interface so production clients
can be swapped for mocks in tests (AGENTS.md rule #23).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from app.services.whatsapp_sender import SessionHandoff

from app.models.session import (
    CartItem,
    Session,
    SessionCreate,
    SessionEvent,
    SessionInitResult,
    SessionStatus,
)
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

    async def initialize_tagged_message(self, message: IncomingMessage) -> SessionInitResult:
        """Process a tagged message and return session plus private host token material."""
        ...


class IWhatsAppSender(Protocol):
    """Interface for outbound WhatsApp communication."""

    async def send_group_message(self, group_id: str, text: str) -> None:
        """Send a message to the WhatsApp group."""
        ...

    async def send_private_message(self, recipient_id: str, text: str) -> None:
        """Send a private message to one WhatsApp user."""
        ...

    async def send_session_handoff(self, recipient_id: str, handoff: SessionHandoff) -> None:
        """Send the session handoff using the richest capability the provider supports."""
        ...


class IShortLinkService(Protocol):
    """Interface for short-link aliases of tokenized session URLs."""

    async def create(self, target_path: str) -> str:
        """Return an opaque short code for a relative target path."""
        ...

    async def resolve(self, code: str) -> str | None:
        """Return the target path for a code, or None when unknown."""
        ...

    async def create_short_url(self, base_url: str, target_path: str) -> str:
        """Return the absolute short URL for a relative target path."""
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


class ISwiggyMcpClient(Protocol):
    """Protocol for Swiggy MCP clients."""

    async def search_restaurants(self, lat: float, lng: float, query: str) -> list[dict[str, Any]]:
        """Search Swiggy Food restaurants or dishes."""
        ...

    async def get_restaurants(self, lat: float, lng: float) -> list[dict[str, Any]]:
        """Browse nearby Swiggy Food restaurants without a search query."""
        ...

    async def get_restaurant(self, restaurant_id: str) -> dict[str, Any]:
        """Return details for one restaurant."""
        ...

    async def get_restaurant_menu(self, restaurant_id: str) -> list[dict[str, Any]]:
        """Return a normalized restaurant menu."""
        ...

    async def search_instamart(self, lat: float, lng: float, query: str) -> list[dict[str, Any]]:
        """Search Swiggy Instamart items."""
        ...

    async def exchange_oauth_code(self, oauth_code: str) -> str:
        """Exchange a Swiggy OAuth code for an authorization header."""
        ...

    async def create_cart(
        self,
        auth_header: str,
        vertical: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create a Swiggy checkout cart for one vertical."""
        ...

    async def get_substitute_items(self, item_id: str) -> list[dict[str, Any]]:
        """Return substitute candidates for an unavailable item."""
        ...

    async def place_order(
        self,
        auth_header: str,
        vertical: str,
        restaurant_id: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Place a finalized order and return its order record."""
        ...

    async def get_order_history(self, auth_header: str) -> list[dict[str, Any]]:
        """Return past orders for the authenticated Swiggy customer, newest first."""
        ...

    async def get_current_order(self, auth_header: str, order_id: str) -> dict[str, Any]:
        """Return the live status of one order."""
        ...

    async def get_delivery_update(self, order_id: str) -> dict[str, Any]:
        """Return the delivery/rider tracking state for one order."""
        ...


class IDBAdapter(Protocol):
    """Protocol for production session and cart persistence."""

    async def create_session(
        self,
        session: SessionCreate,
        host_token_hash: str,
        guest_token: str,
        cart_items: Sequence[CartItem] | None = None,
    ) -> Session:
        """Create a session and its initial cart atomically."""
        ...

    async def get_session(self, session_id: str) -> Session | None:
        """Retrieve a session and its cart by ID."""
        ...

    async def get_latest_session_for_host(self, host_phone: str) -> Session | None:
        """Retrieve the most recent session created by a host wa_id."""
        ...

    async def list_sessions_for_host(self, host_phone: str, *, limit: int = 10) -> list[Session]:
        """Retrieve the most recent sessions created by a host wa_id, newest first."""
        ...

    async def delete_sessions_for_host(self, host_phone: str) -> int:
        """Permanently delete every session (and cascading cart/timeline data)
        created by a host wa_id. Returns the number of sessions deleted.

        Backs the DPDP/data-erasure request flow: EasyOrder stores phone
        numbers and order history, so users need a way to have it removed.
        """
        ...

    async def delete_sessions_older_than(self, cutoff: datetime) -> int:
        """Permanently delete every session older than ``cutoff``. Returns
        the number of sessions deleted. Backs the data-retention script."""
        ...

    async def update_cart_items(self, session_id: str, items: Sequence[CartItem]) -> list[CartItem]:
        """Replace a session cart with validated items."""
        ...

    async def update_session_status(self, session_id: str, status: SessionStatus | str) -> None:
        """Update session lifecycle status."""
        ...

    async def insert_session_event(self, event: SessionEvent) -> SessionEvent | None:
        """Persist one session timeline event.

        Returns None when an event with the same (message_id, event_type)
        was already recorded, mirroring ON CONFLICT DO NOTHING semantics.
        """
        ...

    async def get_session_event(self, message_id: str, event_type: str) -> SessionEvent | None:
        """Return the recorded event for a processed message, or None."""
        ...

    async def get_session_events(self, session_id: str) -> list[SessionEvent]:
        """Return all timeline events for a session, oldest-first."""
        ...
