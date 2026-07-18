import asyncio

import pytest

from app.db.pool import AsyncpgConnectionPool, _PooledConnection


class FakePoolConnection:
    def __init__(self) -> None:
        self.queries: list[str] = []

    async def fetchrow(self, sql: str, *args):
        self.queries.append(sql)
        return {"ok": 1}


class FakePool:
    def __init__(self) -> None:
        self.connection = FakePoolConnection()
        self.acquired = 0
        self.released = 0
        self.closed = False

    async def acquire(self):
        self.acquired += 1
        return self.connection

    async def release(self, connection) -> None:
        assert connection is self.connection
        self.released += 1

    async def close(self) -> None:
        self.closed = True


def test_pooled_connection_delegates_and_releases_on_close() -> None:
    async def run() -> None:
        pool = FakePool()
        conn = _PooledConnection(pool, pool.connection)

        row = await conn.fetchrow("SELECT 1")
        assert row == {"ok": 1}
        assert pool.connection.queries == ["SELECT 1"]

        # close() must release back to the pool, not tear down the socket.
        await conn.close()
        assert pool.released == 1

    asyncio.run(run())


def test_pool_creates_once_and_reuses() -> None:
    async def run() -> None:
        created: list[dict] = []
        fake_pool = FakePool()

        async def fake_create_pool(url, **kwargs):
            created.append({"url": url, **kwargs})
            return fake_pool

        pool = AsyncpgConnectionPool(
            "postgresql://x", min_size=2, max_size=7, create_pool=fake_create_pool
        )
        factory = pool.connection_factory()

        c1 = await factory()
        c2 = await factory()
        await c1.close()
        await c2.close()

        # Pool built exactly once with the configured sizing; both acquires
        # come from the same pool.
        assert len(created) == 1
        assert created[0] == {"url": "postgresql://x", "min_size": 2, "max_size": 7}
        assert fake_pool.acquired == 2
        assert fake_pool.released == 2

        await pool.close()
        assert fake_pool.closed is True

    asyncio.run(run())


def test_pool_close_without_use_is_noop() -> None:
    async def run() -> None:
        pool = AsyncpgConnectionPool("postgresql://x", create_pool=_unused_create_pool)
        await pool.close()  # never initialized -> no error

    asyncio.run(run())


async def _unused_create_pool(*args, **kwargs):  # pragma: no cover - must not run
    raise AssertionError("pool should not be created")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__]))
