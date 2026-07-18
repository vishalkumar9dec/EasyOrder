"""Opt-in integration tests against a real local Postgres (make db-up && make db-migrate).

Skipped automatically when the database is unreachable so CI and
credential-free checkouts stay green.
"""

import asyncio
import uuid

import pytest

from app.db.adapter import AsyncPostgresDBAdapter, asyncpg_connection_factory
from app.db.pool import AsyncpgConnectionPool
from app.models.session import EventType, SessionCreate, SessionEvent
from app.services.short_links import PostgresShortLinkService

DATABASE_URL = "postgresql://easyorder:easyorder@localhost:5432/easyorder"


def _database_available() -> bool:
    async def probe() -> bool:
        try:
            connection = await asyncio.wait_for(
                asyncpg_connection_factory(DATABASE_URL)(), timeout=1.5
            )
        except Exception:
            return False
        try:
            await connection.fetchrow("SELECT 1 AS ok")
            # Schema must be migrated, not just reachable.
            await connection.fetchrow("SELECT 1 FROM session_events LIMIT 1")
            await connection.fetchrow("SELECT 1 FROM short_links LIMIT 1")
            return True
        except Exception:
            return False
        finally:
            await connection.close()

    return asyncio.run(probe())


pytestmark = pytest.mark.skipif(
    not _database_available(),
    reason="local Postgres not reachable/migrated; run `make db-up && make db-migrate`",
)


def test_session_events_and_short_links_survive_new_connections() -> None:
    adapter = AsyncPostgresDBAdapter.from_database_url(DATABASE_URL)
    short_links = PostgresShortLinkService(asyncpg_connection_factory(DATABASE_URL))
    marker = uuid.uuid4().hex[:10]

    async def run() -> None:
        session = await adapter.create_session(
            SessionCreate(whatsapp_group_id=f"itest-{marker}", host_phone="919988776655"),
            host_token_hash="0" * 64,
            guest_token=f"guest_itest_{marker}",
        )

        inserted = await adapter.insert_session_event(
            SessionEvent(
                session_id=session.session_id,
                event_type=EventType.WHATSAPP_INBOUND,
                message_text="itest inbound",
                message_id=f"wamid.itest-{marker}",
            )
        )
        duplicate = await adapter.insert_session_event(
            SessionEvent(
                session_id=session.session_id,
                event_type=EventType.WHATSAPP_INBOUND,
                message_id=f"wamid.itest-{marker}",
            )
        )

        code = await short_links.create(f"/session/{session.session_id}?token=guest_{marker}")
        reused = await short_links.create(f"/session/{session.session_id}?token=guest_{marker}")

        # Fresh adapter instances = fresh connections, proving durability
        # beyond any in-process state.
        reread_adapter = AsyncPostgresDBAdapter.from_database_url(DATABASE_URL)
        reread_links = PostgresShortLinkService(asyncpg_connection_factory(DATABASE_URL))
        events = await reread_adapter.get_session_events(session.session_id)
        resolved = await reread_links.resolve(code)

        assert inserted is not None
        assert duplicate is None, "unique (message_id, event_type) must dedupe"
        assert code == reused
        assert [e.event_type for e in events] == ["whatsapp_inbound"]
        assert events[0].message_text == "itest inbound"
        assert resolved == f"/session/{session.session_id}?token=guest_{marker}"

    asyncio.run(run())


def test_pooled_connections_serve_session_reads_and_writes() -> None:
    """The shared asyncpg pool backs the adapter + short links end to end."""
    pool = AsyncpgConnectionPool(DATABASE_URL, min_size=1, max_size=4)
    factory = pool.connection_factory()
    adapter = AsyncPostgresDBAdapter(factory)
    short_links = PostgresShortLinkService(factory)
    marker = uuid.uuid4().hex[:10]

    async def run() -> None:
        try:
            session = await adapter.create_session(
                SessionCreate(whatsapp_group_id=f"pool-{marker}", host_phone="919988776655"),
                host_token_hash="0" * 64,
                guest_token=f"guest_pool_{marker}",
            )
            # Multiple ops reuse the pool rather than opening a socket each time.
            reread = await adapter.get_session(session.session_id)
            code = await short_links.create(f"/session/{session.session_id}?token=g_{marker}")
            resolved = await short_links.resolve(code)

            assert reread is not None
            assert reread.session_id == session.session_id
            assert resolved == f"/session/{session.session_id}?token=g_{marker}"
        finally:
            await pool.close()

    asyncio.run(run())
