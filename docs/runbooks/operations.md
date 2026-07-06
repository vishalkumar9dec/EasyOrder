# EasyOrder Operations Runbook

## Environment Setup

Default local mode uses mock providers:

```bash
APP_ENV=local
WHATSAPP_PROVIDER_MODE=mock
SWIGGY_CLIENT_MODE=mock
LLM_MODE=mock
PUBLIC_APP_BASE_URL=http://localhost:5173
```

Sandbox integration mode requires provider credentials:

```bash
WHATSAPP_PROVIDER_MODE=meta
WHATSAPP_ACCESS_TOKEN=<sandbox-token>
WHATSAPP_PHONE_NUMBER_ID=<sandbox-phone-number-id>
WHATSAPP_APP_SECRET=<webhook-secret>
SWIGGY_CLIENT_MODE=mcp
SWIGGY_MCP_SERVER_PATH=/absolute/path/to/swiggy-mcp-server
SWIGGY_MCP_SERVER_ENV={"SWIGGY_ENV":"sandbox"}
```

Never commit real secrets.

## Structured Logging

Every HTTP response includes `x-request-id`. If a caller supplies `x-request-id`,
the backend preserves it. Backend request logs use the `easyorder.api` logger and
include:

- `request_id`
- `method`
- `path`
- `status_code`
- `latency_ms`
- `session_id` when the route path includes one

Do not log session tokens, OAuth codes, phone numbers, emails, or card-like
values.

## Session Inspection SQL

Run against local PostgreSQL:

```sql
SELECT
  session_id,
  whatsapp_group_id,
  status,
  budget_limit,
  head_count,
  dietary_preference,
  budget_warning,
  degraded_verticals,
  created_at
FROM sessions
WHERE session_id = '<session_id>';
```

```sql
SELECT
  id,
  item_id,
  name,
  quantity,
  price,
  vertical,
  restaurant_id,
  restaurant_name,
  brand_name,
  source_label
FROM cart_items
WHERE session_id = '<session_id>'
ORDER BY id;
```

## Common Failures

Invalid or expired session link:

- Symptom: `401 Invalid session token`.
- Check that the URL token belongs to the same `session_id`.
- Do not paste host tokens into group chats.

Webhook fixture ignored:

- Symptom: response has `status=ignored`.
- Check the message contains `@EasyOrder`.
- Untagged messages must remain ignored by design.

Checkout validation blocked:

- Symptom: `409` with `ITEM_UNAVAILABLE` or `PRICE_CHANGED`.
- Inspect response `issues`.
- Replace or remove affected items, then retry validation.

Partial checkout:

- Symptom: session status is `CHECKOUT_PARTIAL`.
- Preserve successful checkout URLs.
- Retry or replace failed groups before declaring the order complete.

MCP mode fails on startup:

- Symptom: `SWIGGY_MCP_SERVER_PATH is required` or tool-call failure.
- Confirm `SWIGGY_CLIENT_MODE=mcp`.
- Confirm the MCP command exists and returns JSON on stdout.
- Use `SWIGGY_CLIENT_MODE=mock` to restore local development.

Meta WhatsApp send fails:

- Symptom: `502 Session was created but WhatsApp handoff failed`.
- Confirm sandbox access token, phone number id, and allowed recipient numbers.
- Check Meta Graph API error code in provider logs.
- For inbound handset messages that do not reach the backend, see
  [WhatsApp Webhook Troubleshooting](whatsapp-webhook-troubleshooting.md).

## Release Validation Checklist

- `make test`
- `make frontend-build`
- `src/backend/.venv/bin/python -m ruff check src/backend/app src/backend/tests`
- `make demo-smoke`
- `make security-smoke`
- Verify `.env.example` contains all required variables without secrets.
- Confirm open PR test report lists skipped live-provider checks.
