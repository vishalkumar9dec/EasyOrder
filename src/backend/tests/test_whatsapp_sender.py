import asyncio
import json
import urllib.error
from io import BytesIO

import pytest

from app.services.whatsapp_sender import (
    MetaCloudWhatsAppSender,
    SessionHandoff,
    WhatsAppSendError,
    build_cta_handoff_payloads,
    build_template_handoff_payload,
    create_whatsapp_sender,
)


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


def test_meta_sender_posts_sandbox_text_payload(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    sender = MetaCloudWhatsAppSender(
        access_token="test-token",
        phone_number_id="phone-123",
        api_version="v20.0",
    )

    sender._send_text_message("919988776655", "hello")

    assert captured["url"] == "https://graph.facebook.com/v20.0/phone-123/messages"
    assert captured["headers"]["Authorization"] == "Bearer test-token"
    assert captured["payload"] == {
        "messaging_product": "whatsapp",
        "to": "919988776655",
        "type": "text",
        "text": {"preview_url": False, "body": "hello"},
    }


def test_meta_sender_maps_graph_errors(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url,
            400,
            "bad request",
            hdrs=None,
            fp=BytesIO(b'{"error":{"message":"Bad recipient","code":131030}}'),
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    sender = MetaCloudWhatsAppSender(access_token="test-token", phone_number_id="phone-123")

    with pytest.raises(WhatsAppSendError) as error:
        sender._send_text_message("919988776655", "hello")

    assert "Bad recipient" in str(error.value)


def test_whatsapp_sender_factory_selects_meta_mode() -> None:
    sender = create_whatsapp_sender(
        provider_mode="meta",
        access_token="test-token",
        phone_number_id="phone-123",
        api_version="v20.0",
    )

    assert isinstance(sender, MetaCloudWhatsAppSender)


def make_handoff() -> SessionHandoff:
    return SessionHandoff(
        session_id="session_abc123",
        host_short_url="https://easyorder.example/api/r/h0stC0de",
        guest_short_url="https://easyorder.example/api/r/gu3stC0d",
    )


def test_cta_handoff_payloads_give_each_link_its_own_button() -> None:
    host_payload, guest_payload = build_cta_handoff_payloads("919988776655", make_handoff())

    for payload in (host_payload, guest_payload):
        assert payload["type"] == "interactive"
        assert payload["interactive"]["type"] == "cta_url"
        assert "token=" not in str(payload)
        assert "host_" not in str(payload)
        assert "guest_" not in str(payload)

    host_action = host_payload["interactive"]["action"]
    assert host_action["parameters"]["display_text"] == "Review order"
    assert host_action["parameters"]["url"] == "https://easyorder.example/api/r/h0stC0de"

    guest_action = guest_payload["interactive"]["action"]
    assert guest_action["parameters"]["display_text"] == "Share with group"
    assert guest_action["parameters"]["url"] == "https://easyorder.example/api/r/gu3stC0d"
    # Button-only message: no URL in the visible copy.
    guest_body = guest_payload["interactive"]["body"]["text"]
    assert "http" not in guest_body


def test_template_handoff_payload_maps_documented_variables() -> None:
    payload = build_template_handoff_payload(
        "919988776655",
        make_handoff(),
        template_name="easyorder_session_handoff",
        template_language="en",
    )

    assert payload["type"] == "template"
    template = payload["template"]
    assert template["name"] == "easyorder_session_handoff"
    assert template["language"] == {"code": "en"}
    body, host_button, guest_button = template["components"]
    assert body["parameters"][0]["text"] == "https://easyorder.example/api/r/gu3stC0d"
    assert host_button["sub_type"] == "url"
    assert host_button["index"] == "0"
    assert host_button["parameters"][0]["text"] == "https://easyorder.example/api/r/h0stC0de"
    assert guest_button["sub_type"] == "url"
    assert guest_button["index"] == "1"
    assert guest_button["parameters"][0]["text"] == "https://easyorder.example/api/r/gu3stC0d"
    assert "token=" not in str(payload)


def test_handoff_fallback_text_is_concise_short_link_copy() -> None:
    handoff = make_handoff()

    assert "https://easyorder.example/api/r/h0stC0de" in handoff.fallback_text
    assert "https://easyorder.example/api/r/gu3stC0d" in handoff.fallback_text
    assert "token=" not in handoff.fallback_text
    assert len(handoff.fallback_text) < 300


def test_meta_sender_sends_two_cta_messages_by_default(monkeypatch) -> None:
    captured = []

    def fake_urlopen(request, timeout):
        captured.append(json.loads(request.data.decode("utf-8")))
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    sender = MetaCloudWhatsAppSender(access_token="test-token", phone_number_id="phone-123")

    asyncio.run(sender.send_session_handoff("919988776655", make_handoff()))

    assert [p["type"] for p in captured] == ["interactive", "interactive"]
    assert all(p["to"] == "919988776655" for p in captured)
    display_texts = [p["interactive"]["action"]["parameters"]["display_text"] for p in captured]
    assert display_texts == ["Review order", "Share with group"]


def test_meta_sender_uses_template_when_configured(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    sender = MetaCloudWhatsAppSender(
        access_token="test-token",
        phone_number_id="phone-123",
        handoff_template_name="easyorder_session_handoff",
        handoff_template_language="en",
    )

    asyncio.run(sender.send_session_handoff("919988776655", make_handoff()))

    assert captured["payload"]["type"] == "template"
    assert captured["payload"]["template"]["name"] == "easyorder_session_handoff"


def test_meta_sender_falls_back_to_text_when_rich_payload_rejected(monkeypatch) -> None:
    sent_payloads = []

    def fake_urlopen(request, timeout):
        payload = json.loads(request.data.decode("utf-8"))
        sent_payloads.append(payload)
        if payload["type"] == "interactive":
            raise urllib.error.HTTPError(
                request.full_url,
                400,
                "bad request",
                hdrs=None,
                fp=BytesIO(b'{"error":{"message":"interactive not supported"}}'),
            )
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    sender = MetaCloudWhatsAppSender(access_token="test-token", phone_number_id="phone-123")
    handoff = make_handoff()

    asyncio.run(sender.send_session_handoff("919988776655", handoff))

    assert [p["type"] for p in sent_payloads] == ["interactive", "text"]
    assert sent_payloads[1]["text"]["body"] == handoff.fallback_text


def test_mock_sender_captures_handoff_and_fallback_text() -> None:
    sender = create_whatsapp_sender(
        provider_mode="mock",
        access_token="",
        phone_number_id="",
        api_version="v20.0",
    )
    handoff = make_handoff()

    asyncio.run(sender.send_session_handoff("919988776655", handoff))

    assert sender.sent_handoffs == [("919988776655", handoff)]
    assert sender.sent_messages[-1].text == handoff.fallback_text
    assert sender.sent_messages[-1].channel == "private"
