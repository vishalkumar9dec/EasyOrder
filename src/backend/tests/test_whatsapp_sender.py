import json
from io import BytesIO
import urllib.error

import pytest

from app.services.whatsapp_sender import (
    MetaCloudWhatsAppSender,
    WhatsAppSendError,
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
