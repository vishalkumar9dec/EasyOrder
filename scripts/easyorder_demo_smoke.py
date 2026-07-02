"""Run a local EasyOrder demo smoke without live provider credentials."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "src" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import create_app  # noqa: E402
from app.services.whatsapp_sender import MockWhatsAppSender  # noqa: E402


def parse_session_link(link: str) -> tuple[str, str]:
    parsed = urlparse(link)
    session_id = parsed.path.rstrip("/").split("/")[-1]
    token = parse_qs(parsed.query)["token"][0]
    return session_id, token


def run_demo_smoke() -> dict[str, object]:
    app = create_app()
    client = TestClient(app)
    fixture = json.loads((REPO_ROOT / "docs/api-test-data/whatsapp-tagged-normal.json").read_text())
    sender = app.state.whatsapp_sender
    if not isinstance(sender, MockWhatsAppSender):
        raise RuntimeError("Demo smoke expects WHATSAPP_PROVIDER_MODE=mock")

    webhook = client.post("/api/whatsapp/webhook", json=fixture)
    webhook.raise_for_status()
    webhook_body = webhook.json()
    session_id, guest_token = parse_session_link(webhook_body["sessions"][0]["guest_link"])

    private_messages = [message for message in sender.sent_messages if message.channel == "private"]
    if not private_messages:
        raise RuntimeError("Demo smoke did not capture the private host link")
    _host_session_id, host_token = parse_session_link(private_messages[-1].text.split()[-1])

    guest_bootstrap = client.get(f"/api/session/{session_id}", params={"token": guest_token})
    guest_bootstrap.raise_for_status()

    add_item = client.post(
        f"/api/session/{session_id}/cart-items",
        params={"token": guest_token},
        json={
            "name": "Demo paper plates",
            "quantity": 1,
            "price": "140.00",
            "dietary_tag": "ANY",
            "vertical": "instamart",
            "brand_name": "PartyPro",
            "source_label": "Instamart Mock Store",
        },
    )
    add_item.raise_for_status()

    validation = client.post(f"/api/session/{session_id}/checkout", params={"token": host_token})
    validation.raise_for_status()

    confirmation = client.post(
        f"/api/session/{session_id}/checkout/confirm",
        params={"token": host_token},
        json={"oauth_code": "mock-oauth-code"},
    )
    confirmation.raise_for_status()

    final_session = client.get(f"/api/session/{session_id}", params={"token": host_token})
    final_session.raise_for_status()

    return {
        "session_id": session_id,
        "guest_role": guest_bootstrap.json()["role"],
        "cart_items_after_edit": len(add_item.json()["cart_items"]),
        "checkout_groups": len(validation.json()["groups"]),
        "checkout_urls": [
            step["checkout_url"]
            for step in confirmation.json()["steps"]
            if step.get("checkout_url")
        ],
        "final_status": final_session.json()["status"],
    }


def main() -> None:
    print(json.dumps(run_demo_smoke(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
