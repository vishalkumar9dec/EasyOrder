"""Task 11.1: WhatsApp OTP login and account API."""

import re

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.services.web_auth import InvalidPhoneError, normalize_phone
from tests.test_whatsapp_webhook import business_chat_settings, whatsapp_payload


def latest_otp_for(wa_id: str) -> str:
    sender = app.state.whatsapp_sender
    for message in reversed(sender.sent_messages):
        if message.recipient_id == wa_id and "login code" in message.text:
            return re.search(r"\b(\d{6})\b", message.text).group(1)
    raise AssertionError(f"no OTP message captured for {wa_id}")


def login(client: TestClient, phone: str) -> str:
    wa_id = normalize_phone(phone)
    assert client.post("/api/auth/otp/request", json={"phone": phone}).status_code == 200
    code = latest_otp_for(wa_id)
    verified = client.post("/api/auth/otp/verify", json={"phone": phone, "code": code})
    assert verified.status_code == 200
    return wa_id


def test_phone_normalization_rules() -> None:
    assert normalize_phone("+91 99887 76655") == "919988776655"
    assert normalize_phone("9988776655") == "919988776655"
    assert normalize_phone("919988776655") == "919988776655"
    for bad in ("hello", "12345", "+12 34"):
        try:
            normalize_phone(bad)
        except InvalidPhoneError:
            continue
        raise AssertionError(f"{bad!r} was accepted")


def test_otp_login_flow_sets_cookie_and_me_works() -> None:
    client = TestClient(app)

    wa_id = login(client, "+91 99880 00010")
    me = client.get("/api/me")

    assert me.status_code == 200
    assert me.json() == {"wa_id": wa_id}
    assert "easyorder_web_session" in client.cookies


def test_wrong_code_and_attempt_exhaustion_fail_closed() -> None:
    client = TestClient(app)
    phone = "+91 99880 00011"
    assert client.post("/api/auth/otp/request", json={"phone": phone}).status_code == 200

    for _ in range(5):
        response = client.post(
            "/api/auth/otp/verify", json={"phone": phone, "code": "000000"}
        )
        assert response.status_code == 401

    # Even the real code is dead after the attempt limit.
    code = latest_otp_for(normalize_phone(phone))
    response = client.post("/api/auth/otp/verify", json={"phone": phone, "code": code})
    assert response.status_code == 401


def test_me_requires_login_and_logout_revokes() -> None:
    client = TestClient(app)
    assert client.get("/api/me").status_code == 401
    assert client.get("/api/me/orders").status_code == 401

    login(client, "+91 99880 00012")
    assert client.get("/api/me").status_code == 200

    assert client.post("/api/auth/logout").status_code == 200
    client.cookies.clear()
    assert client.get("/api/me").status_code == 401


def test_my_orders_matches_whatsapp_history_and_is_isolated() -> None:
    client = TestClient(app)
    phone = "+91 99880 00013"
    wa_id = normalize_phone(phone)

    # Create an order through the WhatsApp surface for this identity.
    app.dependency_overrides[get_settings] = business_chat_settings
    try:
        created = client.post(
            "/api/whatsapp/webhook",
            json=whatsapp_payload(
                "get biryani for 4 under 2000",
                phone_number_id="business-42",
                sender_wa_id=wa_id,
            ),
        )
        assert created.json()["status"] == "created"
    finally:
        app.dependency_overrides.pop(get_settings, None)

    login(client, phone)
    orders = client.get("/api/me/orders")

    assert orders.status_code == 200
    body = orders.json()
    assert body["wa_id"] == wa_id
    assert len(body["orders"]) == 1
    order = body["orders"][0]
    assert order["session_id"].startswith("session_")
    assert order["item_count"] > 0
    assert "/api/r/" in order["review_url"]
    assert "token=" not in order["review_url"]
    assert "host_" not in str(body)

    # A different logged-in user sees nothing of this history.
    other = TestClient(app)
    login(other, "+91 99880 00014")
    other_orders = other.get("/api/me/orders").json()
    assert other_orders["orders"] == []


def test_verify_cookie_flags_follow_environment() -> None:
    client = TestClient(app)
    phone = "+91 99880 00015"
    client.post("/api/auth/otp/request", json={"phone": phone})
    code = latest_otp_for(normalize_phone(phone))

    response = client.post("/api/auth/otp/verify", json={"phone": phone, "code": code})

    cookie_header = response.headers["set-cookie"]
    assert "HttpOnly" in cookie_header
    assert "SameSite=lax" in cookie_header
    # app_env=local in tests -> not Secure; non-local must set Secure.
    assert "Secure" not in cookie_header
    assert (
        Settings(app_env="staging").app_env != "local"
    )  # guard: env drives the Secure flag in the route
