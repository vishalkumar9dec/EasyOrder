import hashlib
import hmac

from fastapi.testclient import TestClient

from app.api.whatsapp import verify_signature
from app.config import Settings
from app.main import app
from app.services.mock_agent import MockAgentService


def whatsapp_payload(message_text: str = "@EasyOrder get biryani for 4") -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "business-account-1",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": "group_ipl_fans_1",
                            },
                            "contacts": [{"wa_id": "919988776655"}],
                            "messages": [
                                {
                                    "from": "919988776655",
                                    "id": "wamid.test",
                                    "timestamp": "1782489000",
                                    "type": "text",
                                    "text": {"body": message_text},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def test_webhook_verification_returns_exact_challenge_text() -> None:
    response = TestClient(app).get(
        "/api/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "local-verify-token",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 200
    assert response.text == "challenge-123"


def test_webhook_verification_rejects_wrong_token() -> None:
    response = TestClient(app).get(
        "/api/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 401


def test_signature_helper_accepts_valid_signature() -> None:
    raw_body = b'{"hello":"world"}'
    secret = "test-secret"
    signature = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    verify_signature(
        raw_body,
        f"sha256={signature}",
        Settings(app_env="test", whatsapp_app_secret=secret),
    )


def test_signature_helper_rejects_invalid_signature() -> None:
    raw_body = b'{"hello":"world"}'

    try:
        verify_signature(
            raw_body,
            "sha256=bad",
            Settings(app_env="test", whatsapp_app_secret="test-secret"),
        )
    except Exception as error:
        assert getattr(error, "status_code") == 401
    else:
        raise AssertionError("invalid signature was accepted")


def test_untagged_message_is_ignored_without_agent_call() -> None:
    client = TestClient(app)
    agent_service = app.state.agent_service
    assert isinstance(agent_service, MockAgentService)
    calls_before = len(agent_service.handled_messages)

    response = client.post("/api/whatsapp/webhook", json=whatsapp_payload("hello everyone"))

    assert response.status_code == 200
    assert response.json() == {
        "status": "ignored",
        "reason": "no_easyorder_mention",
        "messages_seen": 1,
    }
    assert len(agent_service.handled_messages) == calls_before


def test_tagged_message_creates_mock_session() -> None:
    response = TestClient(app).post(
        "/api/whatsapp/webhook",
        json=whatsapp_payload("@EasyOrder get biryani for 4 under 2000"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "created"
    assert body["sessions"][0]["session_id"].startswith("session_")
    assert body["sessions"][0]["guest_link"].startswith("/session/session_")
    assert body["sessions"][0]["status"] == "ACTIVE"


def test_invalid_payload_returns_structured_error() -> None:
    response = TestClient(app).post("/api/whatsapp/webhook", json={"not": "a webhook"})

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid WhatsApp webhook payload"
