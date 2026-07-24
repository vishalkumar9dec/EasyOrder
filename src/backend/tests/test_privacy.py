import asyncio

from app.models.session import SessionCreate
from app.services.memory_db import InMemoryDBAdapter
from app.services.privacy import (
    DELETION_CONFIRMED_REPLY_TEMPLATE,
    DELETION_NOTHING_TO_DELETE_REPLY,
    answer_data_deletion_request,
)

WARNING_REPLY = "this deletes everything, confirm to proceed"


def run(coro):
    return asyncio.run(coro)


def test_unconfirmed_request_returns_warning_without_deleting() -> None:
    db = InMemoryDBAdapter()
    run(
        db.create_session(
            SessionCreate(whatsapp_group_id="group_1", host_phone="919988776655"),
            host_token_hash="hash",
            guest_token="guest",
        )
    )

    reply = run(
        answer_data_deletion_request(
            db, wa_id="919988776655", confirmed=False, warning_reply=WARNING_REPLY
        )
    )

    assert reply == WARNING_REPLY
    assert len(db.sessions) == 1


def test_confirmed_request_deletes_and_reports_count() -> None:
    db = InMemoryDBAdapter()
    run(
        db.create_session(
            SessionCreate(whatsapp_group_id="group_1", host_phone="919988776655"),
            host_token_hash="hash",
            guest_token="guest",
        )
    )
    run(
        db.create_session(
            SessionCreate(whatsapp_group_id="group_2", host_phone="919988776655"),
            host_token_hash="hash2",
            guest_token="guest2",
        )
    )

    reply = run(
        answer_data_deletion_request(
            db, wa_id="919988776655", confirmed=True, warning_reply=WARNING_REPLY
        )
    )

    assert reply == DELETION_CONFIRMED_REPLY_TEMPLATE.format(count=2)
    assert len(db.sessions) == 0


def test_confirmed_request_with_no_data_reports_nothing_to_delete() -> None:
    db = InMemoryDBAdapter()

    reply = run(
        answer_data_deletion_request(
            db, wa_id="919900000000", confirmed=True, warning_reply=WARNING_REPLY
        )
    )

    assert reply == DELETION_NOTHING_TO_DELETE_REPLY
