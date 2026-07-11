"""Task 10.7: persistence mode selection and Postgres-backed short links."""

import asyncio

from app.api.whatsapp import create_db_adapter_for_settings
from app.config import Settings
from app.db.adapter import AsyncPostgresDBAdapter
from app.services.memory_db import InMemoryDBAdapter
from app.services.short_links import (
    InMemoryShortLinkService,
    PostgresShortLinkService,
    create_short_link_service,
)


class FakeShortLinkConnection:
    """Mimics asyncpg rows for the short_links table."""

    def __init__(self) -> None:
        self.rows: dict[str, str] = {}
        self.closed = False

    async def fetchrow(self, sql: str, *args):
        if "INSERT INTO short_links" in sql:
            code, target_path = args
            if target_path in self.rows.values():
                return None
            self.rows[code] = target_path
            return {"code": code}
        if "SELECT code FROM short_links" in sql:
            for code, target in self.rows.items():
                if target == args[0]:
                    return {"code": code}
            return None
        if "SELECT target_path FROM short_links" in sql:
            target = self.rows.get(args[0])
            return {"target_path": target} if target is not None else None
        raise AssertionError(f"Unexpected SQL: {sql}")

    async def close(self) -> None:
        self.closed = True


def test_memory_mode_selects_in_memory_stores() -> None:
    settings = Settings(app_env="test", persistence_mode="memory")

    assert isinstance(create_db_adapter_for_settings(settings), InMemoryDBAdapter)
    assert isinstance(create_short_link_service(settings), InMemoryShortLinkService)


def test_postgres_mode_selects_durable_stores() -> None:
    settings = Settings(app_env="test", persistence_mode="postgres")

    assert isinstance(create_db_adapter_for_settings(settings), AsyncPostgresDBAdapter)
    assert isinstance(create_short_link_service(settings), PostgresShortLinkService)


def test_postgres_short_links_reuse_code_per_target() -> None:
    connection = FakeShortLinkConnection()

    async def factory():
        return connection

    service = PostgresShortLinkService(factory)

    first = asyncio.run(service.create("/session/s1?token=guest_a"))
    repeat = asyncio.run(service.create("/session/s1?token=guest_a"))
    other = asyncio.run(service.create("/session/s2?token=guest_b"))

    assert first == repeat
    assert first != other
    assert asyncio.run(service.resolve(first)) == "/session/s1?token=guest_a"
    assert asyncio.run(service.resolve("missing")) is None
    assert connection.closed


def test_postgres_short_links_reject_absolute_targets() -> None:
    async def factory():  # pragma: no cover - must not be reached
        raise AssertionError("connection should not be opened for invalid targets")

    service = PostgresShortLinkService(factory)

    try:
        asyncio.run(service.create("https://evil.example/x"))
    except ValueError:
        pass
    else:
        raise AssertionError("absolute target was accepted")
