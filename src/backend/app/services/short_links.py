"""Short-link aliases for tokenized session URLs.

WhatsApp handoff copy must never display raw tokenized session URLs
(task 10.2). Instead, an opaque short code maps server-side to the
tokenized session path; the redirect endpoint resolves it on click.
Codes carry no token material, so leaking a message body never leaks
a token directly — the code is only useful while the mapping exists.
"""

from __future__ import annotations

import secrets
from typing import Any


async def _close_connection(connection: Any) -> None:
    close = getattr(connection, "close", None)
    if close is not None:
        result = close()
        if hasattr(result, "__await__"):
            await result

SHORT_LINK_PATH_PREFIX = "/api/r"


def _validate_target_path(target_path: str) -> None:
    if not target_path.startswith("/"):
        raise ValueError("Short-link targets must be relative paths")


def _new_code(code_bytes: int) -> str:
    return secrets.token_urlsafe(code_bytes)


class InMemoryShortLinkService:
    """Process-local short-link store for memory persistence mode.

    Mappings live exactly as long as in-memory sessions (both reset on
    backend restart), so a stale code can never outlive its session.
    """

    def __init__(self, *, code_bytes: int = 6) -> None:
        self._code_bytes = code_bytes
        self._paths_by_code: dict[str, str] = {}
        self._codes_by_path: dict[str, str] = {}

    async def create(self, target_path: str) -> str:
        """Return a short code for a relative target path, reusing existing codes."""
        _validate_target_path(target_path)
        if existing := self._codes_by_path.get(target_path):
            return existing
        code = _new_code(self._code_bytes)
        while code in self._paths_by_code:
            code = _new_code(self._code_bytes)
        self._paths_by_code[code] = target_path
        self._codes_by_path[target_path] = code
        return code

    async def resolve(self, code: str) -> str | None:
        """Return the target path for a code, or None when unknown."""
        return self._paths_by_code.get(code)

    async def create_short_url(self, base_url: str, target_path: str) -> str:
        """Return the absolute short URL for a relative target path."""
        code = await self.create(target_path)
        return f"{base_url.rstrip('/')}{SHORT_LINK_PATH_PREFIX}/{code}"


class PostgresShortLinkService:
    """Durable short-link store for postgres persistence mode.

    Uses the same async connection factory contract as
    ``AsyncPostgresDBAdapter`` so both share one configuration path.
    """

    def __init__(self, connection_factory: Any, *, code_bytes: int = 6) -> None:
        self._connection_factory = connection_factory
        self._code_bytes = code_bytes

    async def create(self, target_path: str) -> str:
        _validate_target_path(target_path)
        connection = await self._connection_factory()
        try:
            # Insert-or-reuse without a race: ON CONFLICT on target_path
            # keeps one code per target even under concurrent webhooks.
            code = _new_code(self._code_bytes)
            row = await connection.fetchrow(
                """
                INSERT INTO short_links (code, target_path)
                VALUES ($1, $2)
                ON CONFLICT (target_path) DO NOTHING
                RETURNING code
                """,
                code,
                target_path,
            )
            if row is not None:
                return row["code"]
            existing = await connection.fetchrow(
                "SELECT code FROM short_links WHERE target_path = $1",
                target_path,
            )
            if existing is None:
                raise RuntimeError("short link insert conflicted but target not found")
            return existing["code"]
        finally:
            await _close_connection(connection)

    async def resolve(self, code: str) -> str | None:
        connection = await self._connection_factory()
        try:
            row = await connection.fetchrow(
                "SELECT target_path FROM short_links WHERE code = $1",
                code,
            )
            return row["target_path"] if row is not None else None
        finally:
            await _close_connection(connection)

    async def create_short_url(self, base_url: str, target_path: str) -> str:
        code = await self.create(target_path)
        return f"{base_url.rstrip('/')}{SHORT_LINK_PATH_PREFIX}/{code}"


def create_short_link_service(
    settings: Any,
    connection_factory: Any | None = None,
) -> InMemoryShortLinkService | PostgresShortLinkService:
    """Select short-link persistence to match the session store.

    When ``connection_factory`` is provided (the shared pool), it is used
    instead of a per-operation connection factory.
    """
    if settings.persistence_mode == "postgres":
        if connection_factory is None:
            from app.db.adapter import asyncpg_connection_factory

            connection_factory = asyncpg_connection_factory(settings.database_url)
        return PostgresShortLinkService(connection_factory)
    return InMemoryShortLinkService()
