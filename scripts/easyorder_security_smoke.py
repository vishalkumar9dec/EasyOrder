"""Run EasyOrder security and privacy regression checks locally."""

from __future__ import annotations

import copy
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


def load_fixture(name: str) -> dict:
    return json.loads((REPO_ROOT / "docs" / "api-test-data" / name).read_text())


def set_message(fixture: dict, *, message_id: str, body: str) -> dict:
    next_fixture = copy.deepcopy(fixture)
    message = next_fixture["entry"][0]["changes"][0]["value"]["messages"][0]
    message["id"] = message_id
    message["text"]["body"] = body
    return next_fixture


def resolve_short_link(client: TestClient, short_url: str) -> str:
    """Follow a short-link redirect and return the tokenized session URL."""
    path = urlparse(short_url).path
    response = client.get(path, follow_redirects=False)
    if response.status_code != 307:
        raise RuntimeError(f"Short link {path} did not redirect: {response.status_code}")
    return response.headers["location"]


def create_session(
    client: TestClient,
    sender: MockWhatsAppSender,
    fixture: dict,
) -> tuple[str, str, str, str]:
    messages_before = len(sender.sent_messages)
    webhook = client.post("/api/whatsapp/webhook", json=fixture)
    webhook.raise_for_status()
    body = webhook.json()
    session_id, guest_token = parse_session_link(body["sessions"][0]["guest_link"])

    group_message, private_message = sender.sent_messages[messages_before:]
    host_short_url = private_message.text.split()[-1]
    if "token=" in host_short_url or "host_" in host_short_url:
        raise RuntimeError("Private host message must carry a short link, not a tokenized URL")
    host_session_id, host_token = parse_session_link(
        resolve_short_link(client, host_short_url)
    )
    if host_session_id != session_id:
        raise RuntimeError("Host and guest links point at different sessions")
    if "host_" in group_message.text or "host_" in str(body):
        raise RuntimeError("Host token leaked to the group response")
    return session_id, guest_token, host_token, group_message.text


def expect_status(response, status_code: int, check_name: str) -> None:
    if response.status_code != status_code:
        raise AssertionError(
            f"{check_name} expected {status_code}, got {response.status_code}: {response.text}"
        )


def run_security_smoke() -> dict[str, object]:
    app = create_app()
    client = TestClient(app)
    sender = app.state.whatsapp_sender
    if not isinstance(sender, MockWhatsAppSender):
        raise RuntimeError("Security smoke expects WHATSAPP_PROVIDER_MODE=mock")

    checks: list[str] = []

    request_id_response = client.get("/healthz", headers={"x-request-id": "sec-smoke-1"})
    expect_status(request_id_response, 200, "request_id_header")
    assert request_id_response.headers["x-request-id"] == "sec-smoke-1"
    checks.append("request_id_header")

    untagged = client.post(
        "/api/whatsapp/webhook",
        json=load_fixture("whatsapp-untagged.json"),
    )
    expect_status(untagged, 200, "untagged_privacy")
    assert untagged.json()["status"] == "ignored"
    checks.append("untagged_privacy")

    injection = client.post(
        "/api/whatsapp/webhook",
        json=load_fixture("whatsapp-injection.json"),
    )
    expect_status(injection, 400, "prompt_injection_guardrail")
    assert injection.json()["detail"] == "Tagged message was rejected by input guardrails"
    checks.append("prompt_injection_guardrail")

    base_fixture = load_fixture("whatsapp-tagged-normal.json")
    first_fixture = set_message(
        base_fixture,
        message_id="wamid.security-smoke-1",
        body="@EasyOrder get biryani and drinks for 4 under 3000",
    )
    second_fixture = set_message(
        base_fixture,
        message_id="wamid.security-smoke-2",
        body="@EasyOrder get pizza for 3 under 1200",
    )
    first_session_id, guest_token, host_token, group_text = create_session(
        client,
        sender,
        first_fixture,
    )
    second_session_id, second_guest_token, _second_host_token, _second_group_text = create_session(
        client,
        sender,
        second_fixture,
    )
    # Task 10.2: outbound copy carries opaque short links only — no raw token
    # material of either kind may appear in the shared group message.
    assert "guest_" not in group_text and "host_" not in group_text
    assert "/api/r/" in group_text
    guest_target = resolve_short_link(client, group_text.split()[-1])
    resolved_session_id, resolved_guest_token = parse_session_link(guest_target)
    assert resolved_session_id == first_session_id
    assert resolved_guest_token == guest_token
    checks.append("group_message_short_link_only")

    guest_bootstrap = client.get(
        f"/api/session/{first_session_id}",
        params={"token": guest_token},
    )
    expect_status(guest_bootstrap, 200, "guest_bootstrap_redacted")
    guest_body = guest_bootstrap.json()
    assert guest_body["role"] == "guest"
    assert "host_token" not in guest_body
    assert "host_token_hash" not in guest_body
    assert "host_phone" not in guest_body
    assert host_token not in guest_bootstrap.text
    checks.append("guest_bootstrap_redacted")

    invalid_read = client.get(
        f"/api/session/{first_session_id}",
        params={"token": "guest_wrong"},
    )
    expect_status(invalid_read, 401, "invalid_token_read")
    checks.append("invalid_token_read")

    cross_session_write = client.post(
        f"/api/session/{first_session_id}/cart-items",
        params={"token": second_guest_token},
        json={
            "name": "Security smoke dosa",
            "quantity": 1,
            "price": "120.00",
            "dietary_tag": "VEG",
            "vertical": "food",
            "restaurant_id": "rest-smoke-dosa",
            "restaurant_name": "Smoke Dosa Corner",
        },
    )
    expect_status(cross_session_write, 401, "cross_session_write_blocked")
    checks.append("cross_session_write_blocked")

    guest_checkout = client.post(
        f"/api/session/{first_session_id}/checkout",
        params={"token": guest_token},
    )
    expect_status(guest_checkout, 403, "guest_checkout_blocked")
    checks.append("guest_checkout_blocked")

    guest_confirm = client.post(
        f"/api/session/{first_session_id}/checkout/confirm",
        params={"token": guest_token},
        json={"oauth_code": "mock-oauth-code"},
    )
    expect_status(guest_confirm, 403, "guest_confirm_blocked")
    checks.append("guest_confirm_blocked")

    failed_oauth = client.post(
        f"/api/session/{first_session_id}/checkout/confirm",
        params={"token": host_token},
        json={"oauth_code": "mock-oauth-fail"},
    )
    expect_status(failed_oauth, 400, "host_oauth_failure_safe")
    checks.append("host_oauth_failure_safe")

    host_validation = client.post(
        f"/api/session/{first_session_id}/checkout",
        params={"token": host_token},
    )
    expect_status(host_validation, 200, "host_checkout_validation_allowed")
    assert "checkout_url" not in host_validation.text
    checks.append("host_checkout_validation_allowed")

    return {
        "status": "passed",
        "sessions_checked": [first_session_id, second_session_id],
        "checks": checks,
    }


def main() -> None:
    print(json.dumps(run_security_smoke(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
