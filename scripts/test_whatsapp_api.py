#!/usr/bin/env python3
"""Quick WhatsApp Cloud API test -- run standalone, no server needed.

Usage:
    python scripts/test_whatsapp_api.py --send-template --to YOUR_PHONE_NUMBER
    python scripts/test_whatsapp_api.py --send-text --to YOUR_PHONE_NUMBER --message "Hello from EasyOrder!"
    python scripts/test_whatsapp_api.py --check-number
"""

import argparse
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ENV = REPO_ROOT / "src/backend/.env"
DEFAULT_API_VERSION = "v21.0"
API_VERSION = DEFAULT_API_VERSION


def load_backend_env() -> dict[str, str]:
    """Load simple KEY=VALUE pairs from src/backend/.env without printing secrets."""
    values: dict[str, str] = {}
    if not BACKEND_ENV.exists():
        return values

    for line in BACKEND_ENV.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def api_call(method: str, endpoint: str, token: str, payload: dict | None = None) -> dict:
    """Make a Graph API call and return JSON response."""
    url = f"https://graph.facebook.com/{API_VERSION}/{endpoint}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"\nAPI Error {e.code}:")
        try:
            err_json = json.loads(body)
            print(json.dumps(err_json, indent=2))
        except json.JSONDecodeError:
            print(body)
        sys.exit(1)


def send_template(token: str, to: str, phone_number_id: str) -> None:
    """Send the pre-approved hello_world template message."""
    print(f"\nSending hello_world template to {to}...")
    result = api_call("POST", f"{phone_number_id}/messages", token, {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {"code": "en_US"},
        },
    })
    print("Message sent.")
    print(json.dumps(result, indent=2))


def send_text(token: str, to: str, phone_number_id: str, message: str) -> None:
    """Send a plain text message (only works within 24h service window)."""
    print(f"\nSending text message to {to}...")
    result = api_call("POST", f"{phone_number_id}/messages", token, {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    })
    print("Message sent.")
    print(json.dumps(result, indent=2))


def check_phone_number(token: str, phone_number_id: str) -> None:
    """Verify the phone number registration status."""
    print(f"\nChecking phone number {phone_number_id}...")
    result = api_call("GET", f"{phone_number_id}", token)
    print("Phone number info:")
    print(json.dumps(result, indent=2))


def check_waba_subscription(token: str, waba_id: str) -> None:
    """Check if the app is subscribed to the WABA."""
    print(f"\nChecking WABA subscription for {waba_id}...")
    result = api_call("GET", f"{waba_id}/subscribed_apps", token)
    print("Subscription info:")
    print(json.dumps(result, indent=2))


def main() -> None:
    backend_env = load_backend_env()
    parser = argparse.ArgumentParser(description="Test WhatsApp Cloud API")
    parser.add_argument(
        "--token",
        default=os.environ.get("WHATSAPP_ACCESS_TOKEN") or backend_env.get("WHATSAPP_ACCESS_TOKEN"),
        help="Access token. Defaults to WHATSAPP_ACCESS_TOKEN or src/backend/.env.",
    )
    parser.add_argument(
        "--phone-number-id",
        default=(
            os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
            or backend_env.get("WHATSAPP_PHONE_NUMBER_ID")
        ),
        help="Sender phone number id. Defaults to WHATSAPP_PHONE_NUMBER_ID or src/backend/.env.",
    )
    parser.add_argument(
        "--waba-id",
        default=os.environ.get("WHATSAPP_WABA_ID") or backend_env.get("WHATSAPP_WABA_ID"),
        help="WABA id. Defaults to WHATSAPP_WABA_ID or src/backend/.env.",
    )
    parser.add_argument(
        "--api-version",
        default=(
            os.environ.get("WHATSAPP_API_VERSION")
            or backend_env.get("WHATSAPP_API_VERSION")
            or DEFAULT_API_VERSION
        ),
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--send-template", action="store_true",
                       help="Send hello_world template message")
    group.add_argument("--send-text", action="store_true",
                       help="Send a text message (needs open service window)")
    group.add_argument("--check-number", action="store_true",
                       help="Check phone number registration status")
    group.add_argument("--check-subscription", action="store_true",
                       help="Check WABA app subscription")

    parser.add_argument("--to", help="Recipient phone number (with country code, no +)")
    parser.add_argument("--message", default="Hello from EasyOrder!",
                        help="Text message body (for --send-text)")

    args = parser.parse_args()

    if not args.token:
        print("No access token. Set WHATSAPP_ACCESS_TOKEN in env/src/backend/.env or pass --token.")
        sys.exit(1)

    global API_VERSION
    API_VERSION = args.api_version

    if not args.phone_number_id and not args.check_subscription:
        print("No phone number id. Set WHATSAPP_PHONE_NUMBER_ID in env/src/backend/.env.")
        sys.exit(1)

    if args.send_template:
        if not args.to:
            print("--to is required. Example: --to 919876543210")
            sys.exit(1)
        send_template(args.token, args.to, args.phone_number_id)

    elif args.send_text:
        if not args.to:
            print("--to is required. Example: --to 919876543210")
            sys.exit(1)
        send_text(args.token, args.to, args.phone_number_id, args.message)

    elif args.check_number:
        check_phone_number(args.token, args.phone_number_id)

    elif args.check_subscription:
        if not args.waba_id:
            print("No WABA id. Set WHATSAPP_WABA_ID in env/src/backend/.env or pass --waba-id.")
            sys.exit(1)
        check_waba_subscription(args.token, args.waba_id)


if __name__ == "__main__":
    main()
