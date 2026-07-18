"""WhatsApp OTP login and web sessions for the PWA (task 11.1, ADR 0006).

The user proves control of a phone number by echoing a one-time code sent
to it over WhatsApp. Verifying issues an opaque web session token bound to
the ``wa_id`` — web identity equals WhatsApp identity by construction.

Codes and session tokens are stored hashed. Postgres persistence keeps web
sessions valid across backend restarts, matching session-link durability.
"""

from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

OTP_TTL = timedelta(minutes=5)
OTP_MAX_ATTEMPTS = 5
WEB_SESSION_TTL = timedelta(days=30)
WEB_SESSION_COOKIE = "easyorder_web_session"

_PHONE_RE = re.compile(r"^\+?\d{8,15}$")


class InvalidPhoneError(ValueError):
    """Raised when a login phone number cannot be normalized to a wa_id."""


def normalize_phone(phone: str) -> str:
    """Normalize a user-entered phone number to wa_id digits.

    Accepts optional +, spaces, and dashes; assumes India (91) when a bare
    10-digit local number is given, matching the WhatsApp-first audience.
    """
    compact = re.sub(r"[\s\-()]", "", phone or "")
    if not _PHONE_RE.match(compact):
        raise InvalidPhoneError("Enter the phone number with country code, digits only")
    digits = compact.lstrip("+")
    if len(digits) == 10:
        digits = f"91{digits}"
    return digits


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class _OtpRecord:
    code_hash: str
    expires_at: datetime
    attempts: int = 0


class InMemoryAuthStore:
    """Process-local auth store for memory persistence mode."""

    def __init__(self) -> None:
        self._otps: dict[str, _OtpRecord] = {}
        self._web_sessions: dict[str, tuple[str, datetime]] = {}

    async def put_otp(self, wa_id: str, code_hash: str, expires_at: datetime) -> None:
        self._otps[wa_id] = _OtpRecord(code_hash=code_hash, expires_at=expires_at)

    async def take_otp_attempt(self, wa_id: str) -> _OtpRecord | None:
        record = self._otps.get(wa_id)
        if record is None:
            return None
        record.attempts += 1
        if record.attempts > OTP_MAX_ATTEMPTS or record.expires_at < _now():
            del self._otps[wa_id]
            return None
        return record

    async def clear_otp(self, wa_id: str) -> None:
        self._otps.pop(wa_id, None)

    async def put_web_session(self, token_hash: str, wa_id: str, expires_at: datetime) -> None:
        self._web_sessions[token_hash] = (wa_id, expires_at)

    async def get_web_session_wa_id(self, token_hash: str) -> str | None:
        entry = self._web_sessions.get(token_hash)
        if entry is None:
            return None
        wa_id, expires_at = entry
        if expires_at < _now():
            del self._web_sessions[token_hash]
            return None
        return wa_id

    async def delete_web_session(self, token_hash: str) -> None:
        self._web_sessions.pop(token_hash, None)


class PostgresAuthStore:
    """Durable auth store for postgres persistence mode."""

    def __init__(self, connection_factory: Any) -> None:
        self._connection_factory = connection_factory

    async def _run(self, operation):
        connection = await self._connection_factory()
        try:
            return await operation(connection)
        finally:
            close = getattr(connection, "close", None)
            if close is not None:
                result = close()
                if hasattr(result, "__await__"):
                    await result

    async def put_otp(self, wa_id: str, code_hash: str, expires_at: datetime) -> None:
        async def op(connection):
            await connection.execute(
                """
                INSERT INTO login_otps (wa_id, code_hash, expires_at, attempts)
                VALUES ($1, $2, $3, 0)
                ON CONFLICT (wa_id) DO UPDATE
                    SET code_hash = EXCLUDED.code_hash,
                        expires_at = EXCLUDED.expires_at,
                        attempts = 0
                """,
                wa_id,
                code_hash,
                expires_at,
            )

        await self._run(op)

    async def take_otp_attempt(self, wa_id: str) -> _OtpRecord | None:
        async def op(connection):
            row = await connection.fetchrow(
                """
                UPDATE login_otps SET attempts = attempts + 1
                WHERE wa_id = $1
                RETURNING code_hash, expires_at, attempts
                """,
                wa_id,
            )
            if row is None:
                return None
            record = _OtpRecord(
                code_hash=row["code_hash"],
                expires_at=row["expires_at"],
                attempts=row["attempts"],
            )
            if record.attempts > OTP_MAX_ATTEMPTS or record.expires_at < _now():
                await connection.execute("DELETE FROM login_otps WHERE wa_id = $1", wa_id)
                return None
            return record

        return await self._run(op)

    async def clear_otp(self, wa_id: str) -> None:
        async def op(connection):
            await connection.execute("DELETE FROM login_otps WHERE wa_id = $1", wa_id)

        await self._run(op)

    async def put_web_session(self, token_hash: str, wa_id: str, expires_at: datetime) -> None:
        async def op(connection):
            await connection.execute(
                """
                INSERT INTO web_sessions (token_hash, wa_id, expires_at)
                VALUES ($1, $2, $3)
                """,
                token_hash,
                wa_id,
                expires_at,
            )

        await self._run(op)

    async def get_web_session_wa_id(self, token_hash: str) -> str | None:
        async def op(connection):
            row = await connection.fetchrow(
                "SELECT wa_id, expires_at FROM web_sessions WHERE token_hash = $1",
                token_hash,
            )
            if row is None:
                return None
            if row["expires_at"] < _now():
                await connection.execute(
                    "DELETE FROM web_sessions WHERE token_hash = $1", token_hash
                )
                return None
            return row["wa_id"]

        return await self._run(op)

    async def delete_web_session(self, token_hash: str) -> None:
        async def op(connection):
            await connection.execute("DELETE FROM web_sessions WHERE token_hash = $1", token_hash)

        await self._run(op)


def create_auth_store(
    settings: Any,
    connection_factory: Any | None = None,
) -> InMemoryAuthStore | PostgresAuthStore:
    """Select auth persistence to match the session store.

    When ``connection_factory`` is provided (the shared pool), it is used
    instead of a per-operation connection factory.
    """
    if settings.persistence_mode == "postgres":
        if connection_factory is None:
            from app.db.adapter import asyncpg_connection_factory

            connection_factory = asyncpg_connection_factory(settings.database_url)
        return PostgresAuthStore(connection_factory)
    return InMemoryAuthStore()


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def otp_message(code: str) -> str:
    return (
        f"Your EasyOrder login code is {code}. It expires in 5 minutes. "
        "Never share this code."
    )


async def start_login(store: Any, wa_id: str) -> str:
    """Create and store a fresh OTP; returns the plaintext code for sending."""
    code = generate_otp_code()
    await store.put_otp(wa_id, _hash(code), _now() + OTP_TTL)
    return code


async def verify_login(store: Any, wa_id: str, code: str) -> str | None:
    """Verify an OTP; on success issue and return the plaintext session token."""
    record = await store.take_otp_attempt(wa_id)
    if record is None:
        return None
    if not secrets.compare_digest(record.code_hash, _hash(code.strip())):
        return None
    await store.clear_otp(wa_id)
    token = f"websess_{secrets.token_urlsafe(32)}"
    await store.put_web_session(_hash(token), wa_id, _now() + WEB_SESSION_TTL)
    return token


async def resolve_web_session(store: Any, token: str | None) -> str | None:
    """Return the wa_id for a session cookie value, or None."""
    if not token:
        return None
    return await store.get_web_session_wa_id(_hash(token))


async def revoke_web_session(store: Any, token: str | None) -> None:
    if token:
        await store.delete_web_session(_hash(token))
