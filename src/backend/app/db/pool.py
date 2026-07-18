"""Shared asyncpg connection pool for Postgres persistence.

The session adapter, short-link service, and auth store all take a connection
factory with the contract "await factory() -> connection; await
connection.close() when done". Historically that factory opened a brand-new
asyncpg connection per query (TCP + auth handshake every time), which does not
survive production load. This module provides one bounded, shared pool per
database URL; the factory hands out pooled connections whose ``close()``
releases back to the pool instead of tearing down the socket, so the existing
call sites keep working unchanged.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


class _PooledConnection:
    """Adapts a pooled asyncpg connection to the per-operation contract.

    Delegates all query methods (``fetch``/``fetchrow``/``execute``/
    ``transaction``/...) to the underlying connection, but ``close()`` releases
    it back to the pool rather than closing the socket.
    """

    def __init__(self, pool: Any, connection: Any) -> None:
        self._pool = pool
        self._connection = connection

    def __getattr__(self, name: str) -> Any:
        # Only reached for attributes not defined on the proxy itself.
        return getattr(self._connection, name)

    async def close(self) -> None:
        await self._pool.release(self._connection)


PoolFactory = Callable[..., Awaitable[Any]]


class AsyncpgConnectionPool:
    """Lazily-initialized, shared asyncpg pool for one database URL.

    The pool is created on first use (inside the running event loop), so it can
    be constructed synchronously at app startup. A single instance is shared by
    every Postgres-backed store so the process holds a bounded set of
    connections instead of opening one per query.
    """

    def __init__(
        self,
        database_url: str,
        *,
        min_size: int = 1,
        max_size: int = 10,
        create_pool: PoolFactory | None = None,
    ) -> None:
        self._database_url = database_url
        self._min_size = min_size
        self._max_size = max_size
        self._create_pool = create_pool
        self._pool: Any | None = None
        self._lock = asyncio.Lock()

    def _resolve_create_pool(self) -> PoolFactory:
        if self._create_pool is not None:
            return self._create_pool
        try:
            import asyncpg
        except ImportError as error:  # pragma: no cover - environment guard
            raise RuntimeError("asyncpg is required for PostgreSQL persistence") from error
        return asyncpg.create_pool

    async def _ensure_pool(self) -> Any:
        if self._pool is None:
            async with self._lock:
                if self._pool is None:
                    self._pool = await self._resolve_create_pool()(
                        self._database_url,
                        min_size=self._min_size,
                        max_size=self._max_size,
                    )
        return self._pool

    async def acquire(self) -> _PooledConnection:
        pool = await self._ensure_pool()
        connection = await pool.acquire()
        return _PooledConnection(pool, connection)

    def connection_factory(self) -> Callable[[], Awaitable[_PooledConnection]]:
        """Return a per-operation factory backed by this shared pool."""

        async def factory() -> _PooledConnection:
            return await self.acquire()

        return factory

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
