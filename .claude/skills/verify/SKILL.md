---
name: verify
description: Verify EasyOrder changes end-to-end by running an isolated backend+frontend stack and driving the WhatsApp webhook -> session API -> PWA surface.
---

# EasyOrder Verify Recipe

## Caution first

The user's own backend (`:8000`) is often launched with `src/backend/.env`, which may set
`WHATSAPP_PROVIDER_MODE=meta` with a **real access token**. Posting a webhook to it makes a
real Graph API send to the fixture's `wa_id`. **Never drive webhooks against the user's
running backend — always spin up an isolated instance in mock mode.**

## Isolated backend (:8001)

```bash
cd src/backend && APP_ENV=local PUBLIC_APP_BASE_URL=http://localhost:5174 \
  WHATSAPP_PROVIDER_MODE=mock WHATSAPP_VERIFY_TOKEN=verify-test \
  WHATSAPP_APP_SECRET=verify-secret SWIGGY_CLIENT_MODE=mock LLM_MODE=mock DATABASE_URL= \
  .venv/bin/python -m uvicorn app.main:app --port 8001
```

- `SWIGGY_CLIENT_MODE=mock` wires `MockAgentService` with an in-memory DB — no Postgres needed.
- Setting `WHATSAPP_APP_SECRET` keeps HMAC signature verification ON (good — exercises it).
  Leave it empty to skip signatures (that's what `make test` does).

## Signed webhook post

```bash
SIG=$(python3 -c "import hashlib,hmac;print(hmac.new(b'verify-secret',open('docs/api-test-data/whatsapp-tagged-normal.json','rb').read(),hashlib.sha256).hexdigest())")
curl -s -X POST http://localhost:8001/api/whatsapp/webhook \
  -H "Content-Type: application/json" -H "X-Hub-Signature-256: sha256=$SIG" \
  --data-binary @docs/api-test-data/whatsapp-tagged-normal.json
```

Response contains `guest_link` with the session id + guest token. Host token is never
returned over HTTP (by design) — host-view checks live in backend unit tests only.
`scripts/replay_whatsapp_webhook.py` does the same signing but reads the secret from
`src/backend/.env` (the user's real one) — only use it against a backend running that env.

## Frontend (:5174) pointed at the isolated backend

`.claude/launch.json` has a `frontend-verify` config: vite on 5174 with
`VITE_API_BASE_URL=http://localhost:8001` (the proxy target env var is read via `loadEnv`
in `src/frontend/vite.config.ts`). Start it with `preview_start`, then navigate the
preview browser to the `guest_link` URL (swap host to `localhost:5174`).

## Cart mutation API gotchas

`POST /api/session/{id}/cart-items?token=...` — field is `price` (not `unit_price`),
`vertical` is lowercase (`food`/`instamart`), `dietary_tag` is UPPERCASE (`VEG`/`NON-VEG`/`ANY`).
Food items require `restaurant_id` + `restaurant_name`; Instamart requires `source_label`.

## Flows worth driving

- Tagged fixture -> guest bootstrap -> `timeline` array (whatsapp_inbound, session_created, links_sent).
- Redaction: send a tagged message containing phone/email/card/`host_...` -> all `[redacted]`.
- Untagged fixture -> `{"status":"ignored"}`; tampered/missing signature -> 401.
- Cart mutation response must include `timeline` (regression: UI hides Activity section after edits if missing).
- Invalid token -> "Link not authorized" page, no timeline leak.
