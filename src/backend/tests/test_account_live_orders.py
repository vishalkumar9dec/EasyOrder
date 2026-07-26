"""GET /api/me/orders/live — Scheduled/Ongoing/Historical bucketing."""

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services.web_auth import normalize_phone
from tests.test_account_api import login
from tests.test_whatsapp_webhook import business_chat_settings, whatsapp_payload


def test_my_live_orders_requires_login() -> None:
    client = TestClient(app)

    assert client.get("/api/me/orders/live").status_code == 401


def test_my_live_orders_buckets_scheduled_ongoing_and_is_isolated_per_user() -> None:
    client = TestClient(app)
    phone = "+91 99880 00030"
    wa_id = normalize_phone(phone)

    app.dependency_overrides[get_settings] = business_chat_settings
    try:
        immediate = client.post(
            "/api/whatsapp/webhook",
            json=whatsapp_payload(
                "Order paneer tikka from MotiMahal restaurant",
                message_id="wamid.live.immediate",
                phone_number_id="business-42",
                sender_wa_id=wa_id,
            ),
        )
        assert immediate.json()["intents"][0]["intent"] == "targeted_order"

        scheduled = client.post(
            "/api/whatsapp/webhook",
            json=whatsapp_payload(
                "Order Egg Biryani for me from BiryaniByKilo and it should reach by 8PM",
                message_id="wamid.live.scheduled",
                phone_number_id="business-42",
                sender_wa_id=wa_id,
            ),
        )
        assert scheduled.json()["intents"][0]["intent"] == "targeted_order"
    finally:
        app.dependency_overrides.pop(get_settings, None)

    login(client, phone)
    body = client.get("/api/me/orders/live").json()

    assert body["wa_id"] == wa_id
    assert len(body["ongoing"]) == 1
    assert body["ongoing"][0]["restaurant_name"] == "MotiMahal"
    assert body["ongoing"][0]["status"] == "PLACED"
    assert len(body["scheduled"]) == 1
    assert body["scheduled"][0]["restaurant_name"] == "BiryaniByKilo"
    assert body["scheduled"][0]["status"] == "SCHEDULED"
    assert body["scheduled"][0]["target_placement_at"] is not None
    assert body["historical"] == []

    # A different logged-in user sees none of this history.
    other = TestClient(app)
    login(other, "+91 99880 00031")
    other_body = other.get("/api/me/orders/live").json()
    assert other_body["scheduled"] == []
    assert other_body["ongoing"] == []
    assert other_body["historical"] == []
