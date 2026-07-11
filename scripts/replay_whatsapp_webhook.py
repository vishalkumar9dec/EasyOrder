#!/usr/bin/env python3
"""Replay a signed WhatsApp webhook fixture to a callback URL."""

from __future__ import annotations

import argparse
import hashlib
import hmac
from pathlib import Path
import sys
from urllib import error, request

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ENV = REPO_ROOT / "src/backend/.env"


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
    parser = argparse.ArgumentParser(description="Replay a signed WhatsApp webhook fixture")
    parser.add_argument("callback_url")
    parser.add_argument(
        "--fixture",
        default="docs/api-test-data/whatsapp-tagged-normal.json",
        help="Fixture path relative to repo root",
    )
    args = parser.parse_args()

    app_secret = load_backend_env().get("WHATSAPP_APP_SECRET")
    if not app_secret:
        print("Missing WHATSAPP_APP_SECRET in src/backend/.env")
        sys.exit(1)

    raw_body = (REPO_ROOT / args.fixture).read_bytes()
    signature = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    webhook_request = request.Request(
        args.callback_url,
        data=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={signature}",
        },
        method="POST",
    )

    try:
        with request.urlopen(webhook_request, timeout=30) as response:
            print(response.status)
            print(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        print(f"Webhook replay failed with {exc.code}")
        print(exc.read().decode("utf-8", errors="replace"))
        sys.exit(1)
    except error.URLError as exc:
        print(f"Webhook replay failed: {exc.reason}")
        sys.exit(1)


if __name__ == "__main__":
    main()
