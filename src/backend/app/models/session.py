"""Session domain models.

These are the internal representations used by the backend.
They are independent of the database layer (Supabase/PostgreSQL).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SessionStatus(StrEnum):
    """Lifecycle states of an EasyOrder session."""

    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    CHECKOUT_READY = "CHECKOUT_READY"
    ORDERED = "ORDERED"


class Session(BaseModel):
    """Core session domain model."""

    session_id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:12]}")
    whatsapp_group_id: str | None = None
    host_phone: str = ""
    host_token_hash: str = ""
    guest_token: str = Field(default_factory=lambda: f"guest_{uuid.uuid4().hex[:12]}")
    budget_limit: float = 3000.0
    head_count: int = 4
    status: SessionStatus = SessionStatus.INITIALIZING
    budget_warning: bool = False
    degraded_verticals: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def generate_host_token() -> str:
    """Generate a raw host token (sent via WhatsApp DM)."""
    return f"host_{uuid.uuid4().hex}"


def hash_host_token(raw_token: str) -> str:
    """SHA-256 hash a raw host token for storage."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
