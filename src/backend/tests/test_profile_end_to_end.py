"""A user's own order history changing what a later bare prompt produces.

The full path: three real orders through the webhook, then one vague message,
and the session that comes back carries the budget the user actually spends —
with the reply saying so.
"""

from decimal import Decimal

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.models.session import SessionStatus
from app.services.web_auth import normalize_phone
from tests.test_whatsapp_webhook import business_chat_settings, whatsapp_payload

PHONE = "+91 99880 00061"


def latest_private_messages(wa_id: str) -> list[str]:
    sender = app.state.whatsapp_sender
    return [m.text for m in sender.sent_messages if m.recipient_id == wa_id]


def test_history_teaches_the_next_order_and_the_reply_says_so() -> None:
    client = TestClient(app)
    wa_id = normalize_phone(PHONE)
    db = app.state.db_adapter

    app.dependency_overrides[get_settings] = business_chat_settings
    try:
        # Three real single-restaurant orders, each placed immediately.
        for index in range(3):
            placed = client.post(
                "/api/whatsapp/webhook",
                json=whatsapp_payload(
                    "Order paneer tikka and chicken 65 from MotiMahal restaurant",
                    message_id=f"wamid.profile.seed.{index}",
                    phone_number_id="business-42",
                    sender_wa_id=wa_id,
                ),
            )
            assert placed.json()["intents"][0]["intent"] == "targeted_order"

        # Now a prompt that names no budget at all.
        created = client.post(
            "/api/whatsapp/webhook",
            json=whatsapp_payload(
                "get biryani",
                message_id="wamid.profile.bare",
                phone_number_id="business-42",
                sender_wa_id=wa_id,
            ),
        )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert created.status_code == 200
    session_id = created.json()["sessions"][0]["session_id"]
    session = _await(db.get_session(session_id))

    # The stock fallback is 3000. This session carries what the user spends.
    assert session.budget_limit != Decimal("3000")
    assert session.budget_limit > 0

    note = next((t for t in latest_private_messages(wa_id) if "You didn't say" in t), None)
    assert note is not None, "applied defaults must be disclosed to the host"
    assert "override" in note.lower()


def test_a_stated_budget_survives_the_whole_pipeline() -> None:
    client = TestClient(app)
    wa_id = normalize_phone("+91 99880 00062")
    db = app.state.db_adapter

    app.dependency_overrides[get_settings] = business_chat_settings
    try:
        for index in range(3):
            client.post(
                "/api/whatsapp/webhook",
                json=whatsapp_payload(
                    "Order paneer tikka and chicken 65 from MotiMahal restaurant",
                    message_id=f"wamid.profile.explicit.seed.{index}",
                    phone_number_id="business-42",
                    sender_wa_id=wa_id,
                ),
            )
        created = client.post(
            "/api/whatsapp/webhook",
            json=whatsapp_payload(
                "get biryani for 4 under 2500",
                message_id="wamid.profile.explicit",
                phone_number_id="business-42",
                sender_wa_id=wa_id,
            ),
        )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    session = _await(db.get_session(created.json()["sessions"][0]["session_id"]))

    assert session.budget_limit == Decimal("2500.00")
    assert session.status in (SessionStatus.ACTIVE, SessionStatus.DEGRADED)


def _await(coro):
    import asyncio

    return asyncio.run(coro)
