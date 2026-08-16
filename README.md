# EasyOrder

EasyOrder is a WhatsApp-first group ordering system for coordinating Swiggy Food and
Instamart carts. The live WhatsApp MVP uses a direct conversation with the EasyOrder
business/test number: a host summarizes the final group decision with an `@EasyOrder`
prompt, and EasyOrder replies privately to that host's WhatsApp `wa_id` with the
host link and a shareable guest planning link. The app still starts as a mobile-first
web app opened from a WhatsApp link, with mock integrations by default so the product
flow can be tested locally before live WhatsApp, Swiggy, OAuth, or Supabase credentials
are required.

## Project Structure

```text
.
├── docs/                    # Product, architecture, ADRs, implementation plans, runbooks
├── infra/                   # Local infra (Postgres) + production Docker Compose topology
├── scripts/                 # Migration runner, retention job, deployment rehearsal, demo/security smoke
├── services/
│   └── mock-swiggy-mcp/     # Standalone mock Swiggy MCP server (own Dockerfile, own tests)
├── src/
│   ├── backend/             # FastAPI service (own Dockerfile)
│   └── frontend/            # React/Vite web app (own Dockerfile + Caddyfile)
├── Makefile                 # Common local commands
└── README.md
```

## Requirements

- Python 3.12+
- Node.js 22+
- Docker, for local PostgreSQL, the mock Swiggy MCP server, and the production stack rehearsal

## Backend Setup

```bash
make setup
cp src/backend/.env.example src/backend/.env
make backend-dev
```

Health checks:

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
```

Run backend tests:

```bash
make backend-test
```

## Frontend Setup

```bash
make setup
cp src/frontend/.env.example src/frontend/.env
make frontend-dev
```

Open the web app at [http://localhost:5173](http://localhost:5173).

The local app starts as a pre-session playground. It uses deterministic mock data only:
no LLM, WhatsApp, Swiggy, OAuth, Supabase, sessions, tokens, or RLS calls are made.

Build the frontend:

```bash
make frontend-build
```

## Local Database

Start PostgreSQL:

```bash
make db-up
```

Verify the database:

```bash
docker compose -f infra/docker-compose.yml exec db psql -U easyorder -d easyorder -c "SELECT 1;"
```

Apply the session/cart persistence migration:

```bash
make db-migrate
```

Rollback is available during local development:

```bash
make db-rollback
```

Stop PostgreSQL:

```bash
make db-down
```

Supabase local stack support can be added in later slices when Auth and Realtime are
needed. For now, PostgreSQL is the local persistence base and all external integrations
default to mock mode.

## Mock Swiggy MCP Server

`services/mock-swiggy-mcp/` is a standalone mock of Swiggy's MCP server — a real
MCP-protocol server (official `mcp` SDK, Streamable HTTP), independent of the backend,
with its own Dockerfile and tests. In a real deployment, Swiggy would host an MCP
endpoint and hand EasyOrder a URL and credentials; this service lets that integration
be built and tested before real Swiggy partner access exists.

```bash
make mock-mcp-install
make mock-mcp-up            # serves http://127.0.0.1:9100/mcp
make mock-mcp-test           # in a second terminal
```

Point the backend at it (`src/backend/.env`):

```bash
SWIGGY_CLIENT_MODE=mcp
SWIGGY_MCP_SERVER_URL=http://localhost:9100/mcp
SWIGGY_MCP_AUTH_TOKEN=dev-token   # must match MOCK_MCP_AUTH_TOKEN
```

Leave `SWIGGY_CLIENT_MODE=mock` (the default) to use the in-process mock client
instead — no server to run, used by the test suite and local demo.

## LLM Intent Parsing

`LLM_MODE=mock` (default) uses a deterministic regex parser — no API key needed, and
what the test suite and local demo use. `LLM_MODE=openai` uses a real OpenAI call
(`OPENAI_API_KEY`, `OPENAI_MODEL`) for budget/headcount/dietary/query extraction, with
an automatic fallback to the deterministic parser if the API call fails, so an LLM
outage degrades gracefully instead of breaking the whole flow. `make backend-dev`
refuses to start with `LLM_MODE=openai` and no key set (fail-closed).

## Manual Verification

To prepare, verify, and launch the full local stack in one command:

```bash
make up
```

This starts PostgreSQL, applies migrations, runs backend and frontend checks, builds the
frontend, then launches the backend and frontend dev servers. Use `Ctrl+C` to stop the
dev servers and tear down the local database.

From a clean checkout, run setup once:

```bash
make setup
cp src/backend/.env.example src/backend/.env
cp src/frontend/.env.example src/frontend/.env
```

### One-command smoke test

The fastest way to check the whole tagged-prompt → mock sequential-checkout flow works,
with no servers to start or stop:

```bash
make setup
make demo-smoke
```

Expected output:

- `session_id` starts with `session_`.
- `guest_role` is `guest`.
- `cart_items_after_edit` is `3`.
- `checkout_groups` is `2` for the normal biryani + Instamart fixture.
- `checkout_urls` contains one Food restaurant URL and one Instamart URL.
- `final_status` is `ORDERED`.

See [docs/runbooks/local-demo.md](docs/runbooks/local-demo.md) for the full runbook this
is drawn from.

### Full local stack

Start the services in separate terminals:

```bash
make db-up
make backend-dev
make frontend-dev
```

Verify the running services:

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
docker compose -f infra/docker-compose.yml exec db psql -U easyorder -d easyorder -c "SELECT 1;"
make db-migrate
```

Verify the local WhatsApp webhook mock:

```bash
curl "http://localhost:8000/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=local-verify-token&hub.challenge=challenge-123"
```

The response should be the exact challenge text: `challenge-123`.

Create a real session through the webhook fixture (this is what actually exercises the
tagging → agent → cart pipeline, as opposed to the pre-session playground below):

```bash
curl -s -X POST http://localhost:8000/api/whatsapp/webhook \
  -H 'Content-Type: application/json' \
  --data @docs/api-test-data/whatsapp-tagged-normal.json
```

In mock mode the private host link is captured by `MockWhatsAppSender` in-process (not
sent anywhere) — use `make demo-smoke` or the automated tests when you need to exercise
host-only checkout without live WhatsApp. Open the guest link the webhook response
returned to load the planning canvas, then check:

- Guest link opens the planning canvas.
- Cart rows show Food restaurant and Instamart source labels.
- Guest can add a manual Instamart item.
- Host view shows checkout groups split by Food restaurant and Instamart.
- Host validation reaches `Stock and prices validated`.
- Host mock cart creation shows one checkout link per group.

### Pre-session playground

Open the web app at [http://localhost:5173](http://localhost:5173) with no session
active. The app should render the local playground.

Review these mock use cases from the selector:

- Normal group order
- Over-budget cart
- Dietary mismatch
- Degraded Food availability
- Degraded Instamart availability
- Stock change at validation
- Price change at validation

For each use case, test the host-style prompt, editable cart quantities, budget and
dietary warnings, degraded-state messaging, host/guest toggle, and mock checkout
validation state. On the interactive demo, confirm the food preference control is a
compact inline toggle (Any / Veg / Non-veg) — not a separate oversized card.

Verify observability:

```bash
curl http://localhost:8000/metrics | grep easyorder_
```

Should list `easyorder_http_requests_total`, `easyorder_webhook_events_total`, and
`easyorder_agent_errors_total`.

Verify the self-service data-deletion flow (business chat — a direct message to the
configured `WHATSAPP_PHONE_NUMBER_ID`, not a group message):

1. Send `get biryani for 4 under 2000` to create a session.
2. Send `delete my data` — expect a warning reply, and the session still exists.
3. Send `delete my data confirm` — expect a confirmation reply naming how many
   sessions were deleted, and the session is now gone.

Verify targeted single-restaurant orders, the budget-confirmation flow, and
scheduled delivery (business chat, same direct-message number as above; see
`docs/mock-swiggy-restaurant-call-flow.md` for the full call flow):

1. Send `Order paneer tikka and chicken 65 from MotiMahal restaurant and if
   the budget exceeds INR 400, let me know before placing the order` —
   expect a reply stating the total exceeds your budget and asking to
   reply YES or NO. Nothing is placed yet.
2. Send a **separate** message: `yes` — expect a "Placed!" confirmation.
   This is a genuine two-message exchange, not a same-message confirm word.
3. Send `Order Egg Biryani for me from BiryaniByKilo and it should reach by
   8PM` — expect an immediate "Scheduled" reply; the order is not placed
   yet (deadlines are interpreted as UTC, not IST — see the doc above for
   why). The background scheduler places it automatically once the
   computed placement time arrives (`ORDER_SCHEDULER_POLL_SECONDS`, default
   30s poll interval).
4. Log in to the PWA and open [http://localhost:5173/orders/live](http://localhost:5173/orders/live) —
   confirm the Scheduled/Ongoing/Historical tabs show the orders above.

Stop the long-running services when you are done:

```bash
make db-down
```

Use `Ctrl+C` in the backend and frontend terminals.

## Common Commands

```bash
make setup
make backend-smoke
make backend-test
make frontend-test
make frontend-build
make test
make smoke
make demo-smoke
make security-smoke
make up
```

`make security-smoke` runs the release-blocking privacy and authorization checks
in-process: untagged messages ignored, injection rejected, host token not exposed
to guests or mock group messages, invalid/cross-session tokens rejected, guest checkout
blocked, and checkout cart creation gated behind host OAuth. In live Meta mode, the
WhatsApp handoff is direct-user only and replies to the inbound sender `wa_id`.

Mock Swiggy MCP service:

```bash
make mock-mcp-install
make mock-mcp-up
make mock-mcp-test
```

Versioned database migrations (tracks applied migrations in `schema_migrations`;
safe to run repeatedly — see [docs/data-retention-policy.md](docs/data-retention-policy.md)
for the cascading-delete behavior this relies on):

```bash
make db-migrate-versioned
make db-migrate-versioned-down   # rolls back exactly the most recent migration
```

Data retention (deletes sessions older than N days; see
[docs/data-retention-policy.md](docs/data-retention-policy.md)):

```bash
make data-retention-dry-run RETENTION_DAYS=90
make data-retention RETENTION_DAYS=90
```

Production stack (build + run the full db → migrate → backend → frontend/Caddy
topology locally — see [Production Deployment](#production-deployment) below):

```bash
make prod-build
make prod-up
make prod-down
```

## Production Deployment

See [docs/runbooks/deployment.md](docs/runbooks/deployment.md) for the full operator
runbook (topology diagram, required environment variables, first-time setup, deploying
an update, rollback, log retention).

To verify the entire production topology works — builds every image, deploys
db → migrate → backend → frontend/Caddy, confirms the static PWA serves and `/api/*`
actually reaches the backend (not just the SPA fallback), checks security headers and
log rotation, rehearses a full simulated instance loss + recovery, then tears
everything down — run:

```bash
scripts/rehearse-deployment.sh
```

Requires Docker running; no real credentials needed (every integration rehearses in
mock mode — an ephemeral password is generated per run). Add `--skip-unit-tests` to
skip the `make test` gate and just rehearse the Docker topology:

```bash
scripts/rehearse-deployment.sh --skip-unit-tests
```

Prints `PASS` only if every step actually succeeded, and always cleans up after
itself (containers, network, volumes, images) even on failure or Ctrl+C.

## Troubleshooting

For live Meta WhatsApp webhook issues, especially when handset messages do not
produce backend logs, see
[docs/runbooks/whatsapp-webhook-troubleshooting.md](docs/runbooks/whatsapp-webhook-troubleshooting.md).

If port `8000` is already in use, stop the old backend process or run the backend on a
different port:

```bash
make backend-dev BACKEND_PORT=8001
```

If port `5173` is already in use, stop the old frontend process or run the web app on a
different port:

```bash
make frontend-dev FRONTEND_PORT=5174
```

## Environment

Environment samples live at:

- `src/backend/.env.example`
- `src/frontend/.env.example`

Do not commit real secrets. Mock mode is the expected local default for WhatsApp, Swiggy,
and LLM behavior. New since the production-hardening pass: `SWIGGY_MCP_SERVER_URL` /
`SWIGGY_MCP_AUTH_TOKEN` (real MCP mode), `OPENAI_API_KEY` / `OPENAI_MODEL` (real LLM
mode), `LOG_LEVEL` / `LOG_FORMAT` / `SENTRY_DSN` (observability) — all optional, all
default to mock/no-op behavior.

## Documentation

- Product scope: `docs/easyorder-prd.md`
- Product strategy narrative: `docs/product-documentation.md`
- High-level design: `docs/hld.md`
- Low-level design: `docs/lld.md`
- Delivery plan: `docs/implementation-plan.md`
- Task list: `docs/implementation-tasks.md`
- Production readiness assessment: `docs/production-readiness.md`
- WhatsApp → agent → Swiggy MCP call flow (sequence diagrams, mock vs real MCP mode): `docs/mock-swiggy-restaurant-call-flow.md`
- WhatsApp operating modes ADR: `docs/adr/0004-whatsapp-operating-modes.md`
- Domain glossary: `CONTEXT.md`
- Local demo runbook: `docs/runbooks/local-demo.md`
- Submission video voiceover script (2:00 / 0:60 cuts): `docs/promo-video-script.md`
- Business Model Canvas (content: `docs/business-model-canvas.md`, slide: `docs/assets/business-model-canvas.html`)
- Operations runbook: `docs/runbooks/operations.md`
- **Deployment runbook: `docs/runbooks/deployment.md`**
- Tunnel 408/502 blank-page fix: `docs/runbooks/tunnel-408-502-blank-page.md`
- ngrok stable dev tunnel: `docs/runbooks/ngrok-dev-tunnel.md`
- Data retention & erasure: `docs/data-retention-policy.md`
- Privacy Policy (draft, needs legal review): `docs/privacy-policy-draft.md`
- Terms of Service (draft, needs legal review): `docs/terms-of-service-draft.md`
- WhatsApp Business policy self-assessment: `docs/whatsapp-business-policy-review.md`
- Mock Swiggy MCP service: `services/mock-swiggy-mcp/README.md`

## Live WhatsApp Tunnel Helpers

Localtunnel may return a different URL even when a subdomain is requested. Use
the URL printed by localtunnel when configuring the Meta webhook callback.

```bash
npx -y localtunnel --port 8000 --subdomain easyorder-api-dev
npx -y localtunnel --port 5173 --subdomain easyorder-web-dev
```
