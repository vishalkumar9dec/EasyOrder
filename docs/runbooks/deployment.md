# Deployment runbook — production topology

Covers the production Docker Compose topology: `db` → `migrate` (one-shot)
→ `backend` + `frontend`/Caddy. Addresses blocker B3 in
[production-readiness.md](../production-readiness.md): no Dockerfile, no
host config, and the frontend having no production route to the backend
(Vite's `/api` proxy is dev-server-only).

Artifacts: [`infra/docker-compose.production.yml`](../../infra/docker-compose.production.yml),
[`src/backend/Dockerfile`](../../src/backend/Dockerfile),
[`src/frontend/Dockerfile`](../../src/frontend/Dockerfile) +
[`Caddyfile`](../../src/frontend/Caddyfile),
[`infra/migrate.Dockerfile`](../../infra/migrate.Dockerfile).

This is a different, simpler topology from the local dev one
(`infra/docker-compose.yml`, Postgres only — `make db-up`). The production
compose file builds and runs the whole stack.

## Topology

```
                    ┌──────────────┐
  client ─────────▶ │ frontend      │  Caddy: serves the built PWA (dist/)
                    │ (Caddy)       │  and reverse-proxies /api/* to backend
                    └──────┬────────┘
                           │ /api/*
                    ┌──────▼────────┐
                    │ backend       │  FastAPI/uvicorn
                    └──────┬────────┘
                           │
                    ┌──────▼────────┐
              ┌────▶│ db (postgres) │
              │     └───────────────┘
        ┌─────┴──────┐
        │ migrate    │  one-shot: applies pending migrations, then exits 0
        └────────────┘  (backend won't start until this succeeds)
```

The frontend's own `fetch()` calls are all relative (`/api/...`), which is
exactly what makes this work: the static build has no knowledge of where
the backend lives — Caddy decides that at the network layer, based on
which path was requested. See [`Caddyfile`](../../src/frontend/Caddyfile).

## Verify it yourself before handing off

Don't take this runbook on faith — rehearse it locally with real Docker. The
scripted form of everything below:

```bash
scripts/rehearse-deployment.sh                  # full rehearsal, incl. make test
scripts/rehearse-deployment.sh --skip-unit-tests # just the Docker topology
```

It builds every image, deploys `db → migrate → backend → frontend/Caddy`
with an ephemeral generated password and mock-mode credentials, confirms the
static PWA serves and `/api/*` actually reaches the backend, checks security
headers and log rotation, rehearses a full simulated instance loss +
recovery, then tears everything down (containers, network, volumes, images)
— printing `PASS` only if every step actually succeeded.

To inspect things manually instead of trusting the script's checks:

```bash
cat > infra/.env.production <<'EOF'
POSTGRES_PASSWORD=<pick-a-real-password>
APP_ENV=production
PUBLIC_APP_BASE_URL=http://localhost:8090
WHATSAPP_PROVIDER_MODE=mock
WHATSAPP_VERIFY_TOKEN=rehearsal-verify-token
WHATSAPP_APP_SECRET=rehearsal-app-secret
FRONTEND_PORT=8090
EOF

make prod-up
curl http://localhost:8090/                              # static PWA
curl "http://localhost:8090/api/session/x?token=y"        # proxied to backend, real JSON error
make prod-down
```

This is exactly what `scripts/rehearse-deployment.sh` automates: all
images build cleanly, `migrate` applies pending migrations idempotently and
exits 0, `backend` reports healthy, `frontend` serves the built PWA and
correctly proxies `/api/*` to `backend:8000` (confirmed via a real backend
JSON response, not the SPA's `index.html` fallback), and security headers
(`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) are present
on responses. `WHATSAPP_PROVIDER_MODE=mock` and the other integrations'
mock defaults mean this rehearses end-to-end without any real Meta/Swiggy/
OpenAI credentials.

## Required environment (`infra/.env.production`, never committed)

| Var | Required | Notes |
|---|---|---|
| `POSTGRES_PASSWORD` | Yes | Compose refuses to start without it (`${VAR:?...}`) |
| `APP_ENV` | Yes | Must not be `local` — triggers `main.py`'s fail-closed guards (Postgres required, etc.) |
| `PUBLIC_APP_BASE_URL` | Yes | The public URL users will see (used in WhatsApp handoff links) |
| `WHATSAPP_VERIFY_TOKEN` | Yes | Webhook verification token you configure in the Meta dashboard |
| `WHATSAPP_APP_SECRET` | Yes if `WHATSAPP_PROVIDER_MODE=meta` | `create_app()` refuses to boot with `meta` mode and no secret |
| `WHATSAPP_PROVIDER_MODE` | No (default `mock`) | Set to `meta` for real WhatsApp sends |
| `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_WABA_ID` | Only for `meta` mode | |
| `SWIGGY_CLIENT_MODE` | No (default `mock`) | `mcp` requires `SWIGGY_MCP_SERVER_URL` (real Swiggy partner access — see production-readiness.md B2) |
| `LLM_MODE` | No (default `mock`) | `openai` requires `OPENAI_API_KEY` — `create_app()` fails closed without it |
| `SENTRY_DSN` | No | Empty disables error tracking (no-op) |
| `FRONTEND_PORT` | No (default `80`) | Host port the frontend/Caddy container binds |

Every one of these is enforced by either Docker Compose's `${VAR:?...}`
syntax or `create_app()`'s own startup guards (`src/backend/app/main.py`) —
a misconfigured deploy fails to start with a clear error, not a silent
partial boot.

## First-time setup

1. Provision a host with Docker Engine + the Compose plugin.
2. Copy this repo (or just `infra/`, `src/backend/`, `src/frontend/`, and
   `scripts/`) onto the host.
3. Create `infra/.env.production` (owner-only permissions, `chmod 600`,
   outside Git) with the variables above.
4. `make prod-build && make prod-up`.
5. Point DNS at the host if serving a real domain, and put a TLS-terminating
   reverse proxy (or swap the frontend's Caddyfile for a real domain — Caddy
   auto-provisions ACME certificates once a real domain resolves to it) in
   front of port 80. `[TODO: not rehearsed here — requires a real domain and
   public DNS, which this environment doesn't have. The Caddyfile as written
   serves plain HTTP; add a `https://<domain>` site block once a domain is
   chosen, and Caddy will handle certificate provisioning automatically.]`
6. Run the [operator verification checklist](#operator-verification-checklist).

## Deploying an update

```bash
make prod-build   # rebuilds any image whose source changed
make prod-up      # recreates only the changed containers; migrate reruns (no-op if nothing pending)
```

Because `migrate` tracks applied versions in a `schema_migrations` table
([`scripts/run_migrations.py`](../../scripts/run_migrations.py)), rerunning
it is always safe — it only applies what's new, addressing
production-readiness.md's "migrations are a shell loop with no version
tracking" gap.

## Rollback

```bash
git checkout <previous-known-good-commit> -- src/backend src/frontend infra
make prod-build
make prod-up
```

If the update included a migration that needs undoing:

```bash
make db-migrate-versioned-down DATABASE_URL=<production-database-url>
```

This rolls back exactly the single most recently applied migration (not
everything) — check `scripts/run_migrations.py --help` before running this
against production.

## Log retention

Every service in `infra/docker-compose.production.yml` uses the `json-file`
driver capped at **10 MB × 5 files** (`x-logging` anchor), bounding total log
disk usage per container regardless of traffic volume. `LOG_FORMAT=json` on
the backend (set unconditionally in the compose file) means each line is a
single parseable JSON object — see
[`app/observability.py`](../../src/backend/app/observability.py).

## Operator verification checklist

Run after every deploy, rollback, and recovery:

- [ ] `curl http://<host>/` → the PWA's `index.html` loads
- [ ] `curl http://<host>/api/session/x?token=y` → a real JSON error from
      the backend (`{"detail":"Session not found"}`), not the SPA fallback —
      confirms `/api/*` is actually reaching `backend`, not being swallowed
      by the static-file handler
- [ ] `docker compose -f infra/docker-compose.production.yml --env-file infra/.env.production -p $PROJECT ps`
      shows `db`/`backend`/`frontend` all `healthy`/`Up`, and `migrate`
      exited `0`
- [ ] `docker logs <migrate-container>` shows either `applied ...` lines or
      `database is already up to date` — never an error
- [ ] Response headers include `x-frame-options`, `x-content-type-options`,
      `referrer-policy` (confirms Caddy's header block is live)
- [ ] `/metrics` on the backend returns Prometheus text output (only
      reachable directly on the backend's port today — not yet exposed
      through the frontend/Caddy; see "Not yet done" below)

## Not yet done (tracked, not blocking this runbook)

- **TLS/real domain.** Rehearsed on plain HTTP/localhost only — see the
  `[TODO]` in First-time setup step 5.
- **`/metrics` is not exposed externally.** It's reachable on the backend
  container directly; decide whether to proxy it through Caddy (with auth)
  or scrape it from inside the Docker network only.
- **No CD pipeline.** `make prod-build && make prod-up` is a manual
  operator action today; automating it (GitHub Actions → build → push →
  deploy) is a natural next step once a real host/registry is chosen.
- **Swiggy MCP and real LLM credentials** are separate prerequisites (see
  production-readiness.md B2 and this deploy's env var table) — this
  runbook covers hosting, not obtaining those credentials.
