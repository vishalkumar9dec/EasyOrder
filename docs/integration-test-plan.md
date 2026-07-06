# EasyOrder Integration Test Plan

Last updated: 2026-07-02.

This document covers testing with **real provider credentials** — WhatsApp Meta
Cloud API, Swiggy MCP server, Supabase Realtime, and Swiggy OAuth. The
[manual-ui-test-plan.md](manual-ui-test-plan.md) covers mock-mode testing only.

> [!IMPORTANT]
> All MVP automated tests (`make test`, `make demo-smoke`, `make security-smoke`)
> run in mock mode and pass without any credentials. This plan is for verifying
> live integrations that mock mode cannot cover.

> [!IMPORTANT]
> The current repository is ready to validate Meta webhook verification, real
> inbound WhatsApp messages, direct-user replies, and session creation. In
> `WHATSAPP_PROVIDER_MODE=meta`, EasyOrder replies to the inbound sender `wa_id`
> with a private host link and a shareable guest planning link. The mock-only
> group handoff remains available for local demos, but live Meta testing should
> use a direct conversation with the Meta WhatsApp test/business number.

> [!NOTE]
> Testing in an ordinary consumer WhatsApp group is also not supported by this
> code path today. The expected live flow is: people discuss in a normal group,
> the host sends the final `@EasyOrder ...` prompt from their own WhatsApp number
> to the EasyOrder business/test number, and EasyOrder continues privately with
> that sender. Free-form enquiry/Q&A messages are not implemented yet; only
> tagged order prompts containing `@EasyOrder` are routed to the order-session
> flow.

---

## Prerequisites

### Environment File

Create or update [src/backend/.env](../src/backend/.env.example) (never commit
real credentials). `make backend-dev` runs from `src/backend`, and the backend
settings loader reads `.env` from that directory:

```bash
# ── Core ──
APP_ENV=sandbox
PUBLIC_APP_BASE_URL=https://<frontend-tunnel-or-deployed-url>
BACKEND_CORS_ORIGINS=http://localhost:5173,https://<frontend-tunnel-or-deployed-url>

# ── WhatsApp Meta Cloud API ──
WHATSAPP_PROVIDER_MODE=meta
WHATSAPP_ACCESS_TOKEN=<meta-sandbox-access-token>
WHATSAPP_PHONE_NUMBER_ID=<meta-sandbox-phone-number-id>
WHATSAPP_WABA_ID=<meta-whatsapp-business-account-id>
WHATSAPP_APP_SECRET=<meta-webhook-app-secret>
WHATSAPP_VERIFY_TOKEN=<your-chosen-verify-token>

# ── Swiggy MCP ──
# Keep mock while validating WhatsApp plumbing. Switch to mcp only when the
# Swiggy MCP server is available and tested standalone.
SWIGGY_CLIENT_MODE=mock
SWIGGY_MCP_SERVER_PATH=
SWIGGY_MCP_SERVER_ENV={}

# ── Database ──
DATABASE_URL=postgresql://easyorder:easyorder@localhost:5432/easyorder

# ── LLM ──
LLM_MODE=mock
```

If you use a local frontend tunnel, the frontend itself may also need
[src/frontend/.env](../src/frontend/.env.example) values for any browser-facing
API base URL supported by the current frontend build.

### Provider Setup Checklists

#### Meta WhatsApp Business API (Sandbox)

1. Go to [Meta for Developers](https://developers.facebook.com/) → create or
   select an app → add WhatsApp product.
2. Under WhatsApp → Getting Started, copy:
   - **Temporary access token** → `WHATSAPP_ACCESS_TOKEN`
   - **Phone number ID** → `WHATSAPP_PHONE_NUMBER_ID`
   - **App Secret** (Settings → Basic) → `WHATSAPP_APP_SECRET`
3. Add up to 5 test phone numbers in the sandbox.
4. Under Webhooks, configure:
   - **Callback URL**: `https://<your-tunnel>/api/whatsapp/webhook`
   - **Verify token**: match `WHATSAPP_VERIFY_TOKEN` in `.env`
   - Subscribe to `messages` field.

If handset messages do not produce backend logs, follow
[WhatsApp Webhook Troubleshooting](runbooks/whatsapp-webhook-troubleshooting.md)
to verify the actual app subscription callback URL and WABA subscribed-apps list
through Meta Graph API.

> [!TIP]
> For end-to-end link opening, expose both backend and frontend:
> ```bash
> npx -y localtunnel --port 8000 --subdomain easyorder-api-dev
> npx -y localtunnel --port 5173 --subdomain easyorder-web-dev
> ```
> Then set `PUBLIC_APP_BASE_URL=https://easyorder-web-dev.loca.lt` and configure
> the Meta callback URL as
> `https://easyorder-api-dev.loca.lt/api/whatsapp/webhook`.

#### Swiggy MCP Server

1. Obtain or build the Swiggy MCP server binary/script.
2. Confirm it accepts JSON-RPC on stdin and responds on stdout.
3. Test it standalone:
   ```bash
   echo '{"tool":"search_restaurants","arguments":{"lat":12.97,"lng":77.59,"query":"biryani"}}' | /path/to/swiggy-mcp-server
   ```
4. Set `SWIGGY_MCP_SERVER_PATH` to the absolute path.
5. Set `SWIGGY_MCP_SERVER_ENV` to any required env (e.g., API keys, region).

#### Supabase (for Realtime)

1. Create a Supabase project at [supabase.com](https://supabase.com).
2. Run the migration: `psql $DATABASE_URL < infra/migrations/0001_session_persistence.sql`.
3. Enable Realtime on the `cart_items` table in Supabase Dashboard → Database →
   Replication.
4. Copy the Supabase anon key and URL for frontend env vars (future wiring).

#### Swiggy OAuth (when available)

1. Register an OAuth app with Swiggy developer portal.
2. Set the redirect URI to `https://<your-tunnel>/api/session/{session_id}/checkout/callback`.
3. Note the client ID and secret for the OAuth exchange.

---

## Integration Test Matrix

### Phase 1: WhatsApp Integration

Current status:

- **Ready now:** Meta webhook verification, HMAC validation, inbound tagged
  message parsing, mention-only filtering, direct-user replies, and session
  creation.
- **Mock-only today:** group guest-link handoff and private host-link handoff are
  fully covered by `make demo-smoke`, `make security-smoke`, and webhook tests.
- **Not supported today:** adding EasyOrder to a normal WhatsApp group and
  using `@EasyOrder` there as a bot mention.

| ID | Test | Steps | Expected | Env vars required |
|---|---|---|---|---|
| INT-01 | Webhook verification handshake | Start backend with sandbox env. Meta dashboard sends verification GET to `/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=<token>&hub.challenge=<challenge>`. | Backend returns the challenge string with 200. Dashboard shows ✅ verified. | `WHATSAPP_VERIFY_TOKEN` |
| INT-02 | Webhook HMAC signature validation | Send a POST to `/api/whatsapp/webhook` with a valid `X-Hub-Signature-256` header. Then send one with a tampered signature. | Valid signature: processed normally. Tampered: 403 rejected. | `WHATSAPP_APP_SECRET` |
| INT-03 | Tagged message → session creation | From a registered sandbox test phone, send `@EasyOrder get biryani for 4 under 2000` to the Meta WhatsApp test/business number. | Backend receives the webhook, creates a session, and in `WHATSAPP_PROVIDER_MODE=meta` sends the private handoff back to the sender `wa_id`. | `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`; `WHATSAPP_PROVIDER_MODE=meta`, `WHATSAPP_ACCESS_TOKEN`, and `WHATSAPP_PHONE_NUMBER_ID` for live reply |
| INT-04 | Untagged message → silence | From the sandbox phone, send `let's order pizza tonight` without `@EasyOrder`. | No session is created. Backend returns/records `status=ignored`. No outbound WhatsApp response should be sent. | Same as INT-03 |
| INT-05 | Guest link opens from WhatsApp or copied link | After session creation, open the generated guest link from logs, a mock smoke output, or a fixed live WhatsApp response. | PWA session page loads with role `Guest`, source-attributed cart rows, and no host token visible. | `PUBLIC_APP_BASE_URL` must be accessible from the phone |
| INT-06 | Host link opens from private/direct handoff | After session creation, open the generated host link from test helper/logs or a fixed direct WhatsApp response. | PWA session page loads with role `Host`, checkout eligibility, and no raw token values displayed. | Same as INT-05 |
| INT-07 | Live direct-user outbound reply | Send a tagged prompt from the sandbox phone after configuring Meta credentials. | WhatsApp receives one private EasyOrder reply to the sender `wa_id` containing the private host link and shareable guest link. The webhook HTTP response must not contain `host_`. | `WHATSAPP_PROVIDER_MODE=meta`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` |
| INT-08 | Free-form enquiry limitation | Send `what can you order for my party?` without `@EasyOrder`, then send `@EasyOrder what can you order for my party?`. | Untagged message is ignored. Tagged enquiry currently enters the order-session guardrail/parser path; there is no general Q&A answer route yet. | Same as INT-03 |

**How to run:**

```bash
# Terminal 1: expose local backend
npx -y localtunnel --port 8000 --subdomain easyorder-api-dev

# Terminal 2: start backend in sandbox mode
make db-up && make db-migrate
make backend-dev  # reads .env automatically

# Terminal 3: start frontend (point to tunnel for links)
npx -y localtunnel --port 5173 --subdomain easyorder-web-dev
make frontend-dev

# Then send WhatsApp messages from your registered sandbox test phone to the
# Meta WhatsApp test/business number.
```

---

### Phase 2: Swiggy MCP Integration

| ID | Test | Steps | Expected | Env vars required |
|---|---|---|---|---|
| INT-10 | Restaurant search returns real results | Start backend with `SWIGGY_CLIENT_MODE=mcp`. Send a tagged webhook: `@EasyOrder get biryani and drinks for 4 under 3000`. | Backend creates a session with cart items from real Swiggy Food restaurants. Each Food item has a real `restaurant_id` and `restaurant_name`. | `SWIGGY_CLIENT_MODE=mcp`, `SWIGGY_MCP_SERVER_PATH` |
| INT-11 | Instamart search returns real results | Same as INT-10 with a prompt that includes beverages. | Cart includes Instamart items with real `brand_name` and `source_label` values from the MCP response. | Same as INT-10 |
| INT-12 | MCP timeout degrades gracefully | Temporarily set `SWIGGY_MCP_SERVER_ENV` to trigger a timeout scenario, or throttle the server. | Session is created with `DEGRADED` status. Degraded vertical badge appears. Non-degraded vertical items are still present. | Same as INT-10 |
| INT-13 | MCP server not found | Set `SWIGGY_MCP_SERVER_PATH` to a nonexistent path. Send a tagged message. | Backend returns 500 with `Swiggy MCP server could not be started`. No session is created. | `SWIGGY_CLIENT_MODE=mcp`, invalid path |
| INT-14 | Fallback to mock mode | Set `SWIGGY_CLIENT_MODE=mock`. Send the same tagged message. | Mock session is created normally. Verify app still works in mock mode after MCP testing. | `SWIGGY_CLIENT_MODE=mock` |

**How to run:**

```bash
# Verify MCP server standalone first
echo '{"tool":"search_restaurants","arguments":{"lat":12.97,"lng":77.59,"query":"biryani"}}' \
  | $SWIGGY_MCP_SERVER_PATH

# Then start backend with MCP mode
SWIGGY_CLIENT_MODE=mcp make backend-dev

# Send a tagged webhook
curl -s -X POST http://localhost:8000/api/whatsapp/webhook \
  -H 'Content-Type: application/json' \
  --data @docs/api-test-data/whatsapp-tagged-normal.json | python3 -m json.tool
```

**Inspect real MCP response normalization:**

```bash
cd src/backend
.venv/bin/python - <<'PY'
import asyncio
from app.services.swiggy_mcp import create_swiggy_client

async def main():
    client = create_swiggy_client(
        mode="mcp",
        server_path="/path/to/swiggy-mcp-server",
        server_env='{"SWIGGY_ENV":"sandbox"}',
    )
    results = await client.search_restaurants(12.97, 77.59, "biryani")
    for item in results:
        print(f"  {item['name']} @ {item['restaurant_name']} — ₹{item['price']}")

    im_results = await client.search_instamart(12.97, 77.59, "cola")
    for item in im_results:
        print(f"  {item['name']} · {item.get('brand_name', '?')} — {item['source_label']}")

asyncio.run(main())
PY
```

---

### Phase 3: Swiggy OAuth & Real Checkout

| ID | Test | Steps | Expected | Env vars required |
|---|---|---|---|---|
| INT-20 | OAuth code exchange returns access token | Call the Swiggy MCP `exchange_oauth_code` tool with a real OAuth code. | Returns a `Bearer <token>` string. No token is logged. | MCP mode + Swiggy OAuth credentials |
| INT-21 | Real cart creation for Food | After OAuth, call `create_cart` with Food items and the real auth header. | Returns a checkout URL pointing to Swiggy's Food checkout page for the correct restaurant. | Same as INT-20 |
| INT-22 | Real cart creation for Instamart | After OAuth, call `create_cart` with Instamart items. | Returns a checkout URL for Instamart checkout. | Same as INT-20 |
| INT-23 | Sequential multi-restaurant checkout | Create a session with Food items from two restaurants. Validate checkout, then confirm with a real OAuth code. | Two Food checkout URLs (one per restaurant) plus one Instamart URL. Each URL opens a separate Swiggy order. | Same as INT-20 |
| INT-24 | OAuth failure is handled safely | Use an expired or invalid OAuth code. | Backend returns 400. No checkout carts are created. Session remains in `CHECKOUT_READY` state. | Same as INT-20 |

> [!WARNING]
> Real OAuth testing creates **actual Swiggy orders** if the checkout URLs are
> visited and payment is completed. Use sandbox/test Swiggy accounts only.

**How to run:**

```bash
# After INT-10 passes, create a session and validate checkout
SESSION_ID=<from-INT-10>
HOST_TOKEN=<from-backend-logs-or-test-helper>

# Validate checkout
curl -s -X POST "http://localhost:8000/api/session/$SESSION_ID/checkout?token=$HOST_TOKEN" \
  | python3 -m json.tool

# Confirm with real OAuth code (obtain from Swiggy OAuth redirect)
curl -s -X POST "http://localhost:8000/api/session/$SESSION_ID/checkout/confirm?token=$HOST_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"oauth_code": "<real-oauth-code>"}' \
  | python3 -m json.tool
```

---

### Phase 4: Supabase Realtime (Future Wiring)

The frontend currently uses a 2.5-second polling fallback in
[useSupabaseCartRealtime.ts](../src/frontend/src/useSupabaseCartRealtime.ts).
Switching to native Supabase channels requires:

1. Add `@supabase/supabase-js` to the frontend.
2. Set `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` env vars.
3. Replace the `setInterval` polling with a Supabase Realtime channel subscription
   on the `cart_items` table filtered by `session_id`.

| ID | Test | Steps | Expected | What needs to change |
|---|---|---|---|---|
| INT-30 | Realtime cart insert | Open two browser tabs on the same session. Add an item in tab 1. | Tab 2 receives the new row within ~500ms (vs 2.5s polling). | Frontend Supabase client wiring |
| INT-31 | Realtime cart update | Change quantity in tab 1. | Tab 2 reflects updated quantity in real time. | Same |
| INT-32 | Realtime cart delete | Remove an item in tab 1. | Tab 2 removes the row in real time. | Same |
| INT-33 | Reconnection after network drop | Disconnect tab 2's network briefly, reconnect. | Tab 2 reconnects and catches up with any missed changes. | Supabase channel reconnect handling |

> [!NOTE]
> Until Supabase browser client is wired, the polling fallback is functional.
> INT-30 through INT-33 remain future tests that will become executable once
> the Supabase JS client is added to the frontend.

---

## Integration Boundary Reference

### Code Files

| Integration | Factory function | Protocol | Config vars |
|---|---|---|---|
| WhatsApp sender | [create_whatsapp_sender](../src/backend/app/services/whatsapp_sender.py#L122-L135) | [IWhatsAppSender](../src/backend/app/services/protocols.py#L36-L45) | `WHATSAPP_PROVIDER_MODE`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_API_VERSION` |
| Swiggy MCP | [create_swiggy_client](../src/backend/app/services/swiggy_mcp.py#L249-L264) | [ISwiggyMcpClient](../src/backend/app/services/protocols.py#L68-L98) | `SWIGGY_CLIENT_MODE`, `SWIGGY_MCP_SERVER_PATH`, `SWIGGY_MCP_SERVER_ENV` |
| Webhook auth | [Settings.skip_signature_verification](../src/backend/app/config.py#L37-L40) | — | `APP_ENV`, `WHATSAPP_APP_SECRET` |
| Frontend realtime | [useSupabaseCartRealtime](../src/frontend/src/useSupabaseCartRealtime.ts) | — | Future: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` |

### All Integration Env Vars

| Variable | Default | Required for | Notes |
|---|---|---|---|
| `APP_ENV` | `local` | Webhook signature skip | Set to `sandbox` or `production` to enforce HMAC |
| `WHATSAPP_PROVIDER_MODE` | `mock` | INT-03 → INT-08 | Use `mock` for local/demo checks; use `meta` for live direct-user WhatsApp replies. |
| `WHATSAPP_ACCESS_TOKEN` | (empty) | INT-07 | Meta sandbox temporary token or system-user token for outbound sends. |
| `WHATSAPP_PHONE_NUMBER_ID` | (empty) | INT-07 | Meta sandbox/business phone number id used as the sender. |
| `WHATSAPP_APP_SECRET` | (empty) | INT-02 | Meta app secret for HMAC |
| `WHATSAPP_VERIFY_TOKEN` | `local-verify-token` | INT-01 | Must match Meta dashboard config |
| `WHATSAPP_API_VERSION` | `v20.0` | INT-07 | Meta Graph API version |
| `SWIGGY_CLIENT_MODE` | `mock` | INT-10 → INT-14 | `mock` or `mcp` |
| `SWIGGY_MCP_SERVER_PATH` | (empty) | INT-10 → INT-13 | Absolute path to MCP binary/script |
| `SWIGGY_MCP_SERVER_ENV` | `{}` | INT-10 → INT-12 | JSON object of MCP env vars |
| `PUBLIC_APP_BASE_URL` | `http://localhost:5173` | INT-05 → INT-07 | Must be accessible from WhatsApp devices when links are sent or copied. |
| `DATABASE_URL` | (local pg) | All | PostgreSQL connection string |
| `LLM_MODE` | `mock` | All | Keep `mock` until real LLM integration |

---

## Quick Smoke: Which Integrations Work Today?

Run this checklist to determine what you can test right now:

```bash
# 1. Do you have Meta WhatsApp sandbox credentials?
echo "WHATSAPP_ACCESS_TOKEN=${WHATSAPP_ACCESS_TOKEN:-(not set)}"
echo "WHATSAPP_PHONE_NUMBER_ID=${WHATSAPP_PHONE_NUMBER_ID:-(not set)}"

# 2. Do you have a Swiggy MCP server binary?
ls -la ${SWIGGY_MCP_SERVER_PATH:-(not set)} 2>/dev/null || echo "MCP server not found"

# 3. Is your local backend accessible from the internet?
curl -s https://<your-tunnel>/healthz || echo "Tunnel not reachable"
```

| If you have... | You can test... |
|---|---|
| Nothing | Mock mode only (existing manual-ui-test-plan.md) |
| Meta sandbox app + backend tunnel | Phase 1 inbound checks (INT-01 → INT-04) |
| Meta sandbox credentials | Phase 1 live direct-user outbound checks (INT-05 → INT-07) |
| Swiggy MCP server binary | Phase 2 (INT-10 → INT-14) |
| Both + Swiggy OAuth | Phase 3 (INT-20 → INT-24) |
| Supabase project + frontend wiring | Phase 4 (INT-30 → INT-33) |

---

## Regression Safety

After any integration test session, verify mock mode still works:

```bash
# Reset to mock mode
unset WHATSAPP_ACCESS_TOKEN WHATSAPP_PHONE_NUMBER_ID WHATSAPP_APP_SECRET
export SWIGGY_CLIENT_MODE=mock
export WHATSAPP_PROVIDER_MODE=mock
export APP_ENV=local

# Full regression
make test
make demo-smoke
make security-smoke
make frontend-build
```

All 68 backend + 20 frontend tests must still pass.
