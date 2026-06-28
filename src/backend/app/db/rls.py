"""Helpers for PostgreSQL RLS request header claims."""

from __future__ import annotations

import json


def build_rls_headers(
    *,
    host_token: str | None = None,
    guest_token: str | None = None,
) -> dict[str, str]:
    """Build the token headers consumed by database RLS policies."""

    headers: dict[str, str] = {}
    if host_token:
        headers["x-host-token"] = host_token
    if guest_token:
        headers["x-guest-token"] = guest_token
    return headers


def encode_rls_headers(headers: dict[str, str]) -> str:
    """Encode RLS headers for PostgreSQL ``request.headers`` settings."""

    return json.dumps(headers, separators=(",", ":"), sort_keys=True)


async def set_rls_headers(connection, headers: dict[str, str]) -> None:
    """Set local request headers for one transaction-scoped RLS operation."""

    await connection.execute(
        "SELECT set_config('request.headers', $1, true)",
        encode_rls_headers(headers),
    )
