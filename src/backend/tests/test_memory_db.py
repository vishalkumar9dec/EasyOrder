import asyncio
from datetime import UTC, datetime

from app.models.session import SessionCreate, SessionEvent
from app.services.memory_db import InMemoryDBAdapter


def run(coro):
    return asyncio.run(coro)


def _create(adapter: InMemoryDBAdapter, *, host_phone: str) -> str:
    session = run(
        adapter.create_session(
            SessionCreate(whatsapp_group_id="group_1", host_phone=host_phone),
            host_token_hash="hash",
            guest_token="guest",
        )
    )
    return session.session_id


def test_delete_sessions_for_host_removes_only_that_hosts_sessions_and_events() -> None:
    adapter = InMemoryDBAdapter()
    target_session_id = _create(adapter, host_phone="919988776655")
    other_session_id = _create(adapter, host_phone="911111111111")
    run(
        adapter.insert_session_event(
            SessionEvent(session_id=target_session_id, event_type="whatsapp_tagged_message")
        )
    )
    run(
        adapter.insert_session_event(
            SessionEvent(session_id=other_session_id, event_type="whatsapp_tagged_message")
        )
    )

    deleted = run(adapter.delete_sessions_for_host("919988776655"))

    assert deleted == 1
    assert run(adapter.get_session(target_session_id)) is None
    assert run(adapter.get_session(other_session_id)) is not None
    assert all(event.session_id != target_session_id for event in adapter.events)
    assert any(event.session_id == other_session_id for event in adapter.events)


def test_delete_sessions_for_host_with_no_sessions_returns_zero() -> None:
    adapter = InMemoryDBAdapter()

    assert run(adapter.delete_sessions_for_host("919900000000")) == 0


def test_delete_sessions_older_than_cutoff() -> None:
    adapter = InMemoryDBAdapter()
    old_session_id = _create(adapter, host_phone="919988776655")
    adapter.sessions[old_session_id].created_at = datetime(2020, 1, 1, tzinfo=UTC)
    recent_session_id = _create(adapter, host_phone="911111111111")

    deleted = run(adapter.delete_sessions_older_than(datetime(2025, 1, 1, tzinfo=UTC)))

    assert deleted == 1
    assert run(adapter.get_session(old_session_id)) is None
    assert run(adapter.get_session(recent_session_id)) is not None
