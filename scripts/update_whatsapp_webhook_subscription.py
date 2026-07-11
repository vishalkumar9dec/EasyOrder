#!/usr/bin/env python3
"""Update the Meta WhatsApp webhook callback URL from local backend env."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from urllib import error, parse, request

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ENV = REPO_ROOT / "src/backend/.env"
DEFAULT_APP_ID = "823160707397760"


def load_backend_env() -> dict[str, str]:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Update Meta WhatsApp webhook callback URL")
    parser.add_argument("callback_url", help="Full callback URL ending in /api/whatsapp/webhook")
    parser.add_argument("--app-id", default=DEFAULT_APP_ID)
    parser.add_argument("--api-version", default="v21.0")
    args = parser.parse_args()

    env = load_backend_env()
    app_secret = env.get("WHATSAPP_APP_SECRET")
    verify_token = env.get("WHATSAPP_VERIFY_TOKEN")
    if not app_secret or not verify_token:
        print("Missing WHATSAPP_APP_SECRET or WHATSAPP_VERIFY_TOKEN in src/backend/.env")
        sys.exit(1)

    body = parse.urlencode(
        {
            "object": "whatsapp_business_account",
            "callback_url": args.callback_url,
            "verify_token": verify_token,
            "fields": "messages",
            "access_token": f"{args.app_id}|{app_secret}",
        }
    ).encode("utf-8")
    endpoint = f"https://graph.facebook.com/{args.api_version}/{args.app_id}/subscriptions"
    graph_request = request.Request(endpoint, data=body, method="POST")

    try:
        with request.urlopen(graph_request, timeout=20) as response:
            print(response.status)
            print(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        print(f"Graph API error {exc.code}")
        response_body = exc.read().decode("utf-8", errors="replace")
        try:
            print(json.dumps(json.loads(response_body), indent=2))
        except json.JSONDecodeError:
            print(response_body)
        sys.exit(1)


if __name__ == "__main__":
    main()
