# EasyOrder — Production Readiness Analysis

_Assessment date: 2026-07-15. Basis: full audit of `src/backend`, `src/frontend`,
`infra/`, and CI. This is a point-in-time snapshot; line references may drift._

## 1. Verdict

EasyOrder is a **cohesive, well-tested prototype** with one genuinely
production-grade subsystem (the Meta WhatsApp send/webhook path) and a clean
domain model. It is **not production-ready**. Two gaps sit on the critical
path and are not solvable by coding alone:

1. **There is no real Swiggy integration.** The "real" client shells out to an
   MCP server binary that does not exist in this repo; all cart creation,
   checkout URLs, and OAuth are simulated. Without Swiggy partner API access,
   the product cannot place an order — its core function.
2. **There is no deployment path.** No app container, no host config, no CD.
   The frontend's only route to the backend (`/api` proxy) is a Vite
   dev-server feature that does not exist in a static production build.

Everything else — security hardening, Postgres durability, observability — is
standard productionization that the team controls. But until #1 and #2 are
answered, "go live" is blocked regardless of code quality.

## 2. Readiness scorecard

| Area | Status | One-line |
|---|---|---|
| WhatsApp integration | 🟢 Ready | Real Graph API sends, HMAC verify, template handoff w/ fallbacks; needs creds + approved template + non-local env |
| Domain model & API design | 🟢 Solid | Clean Pydantic models, token roles, checkout grouping |
| Automated tests | 🟡 Good unit, thin integration | 133 backend + 28 frontend unit tests; no load tests, real-dependency integration is mocked |
| Security | 🔴 Blockers | OTP code printed to logs; no OTP rate limit; signature check auto-skips in `local` |
| Data / persistence | 🔴 Not prod-shaped | Defaults to in-memory (state lost on restart); connect-per-query; RLS is dead code |
| Deployment / infra | 🔴 None | No Dockerfile, no host, no CD; frontend has no prod route to backend |
| Observability | 🔴 Minimal | Access logs + health endpoints only; no metrics, no error tracking, logging unconfigured |
| Swiggy (search + checkout) | 🔴 Mock / stub | Real MCP server binary absent; checkout & OAuth simulated |
| LLM / intent | 🟡 Mock-only, works for happy path | `LLM_MODE` inert; deterministic regex parser always runs |
| Realtime cart sync | 🟡 Polling (fine) | 2.5s client poll, not Supabase; functional, not a blocker |
| Compliance / legal | 🔴 Unaddressed | PII (phone numbers) stored; no retention policy, consent, or WhatsApp-policy review |

## 3. The critical path (owner decisions, not code)

Before sequencing engineering work, two questions gate everything:

- **Do you have Swiggy partner API access?** The entire checkout half of the
  product depends on it. If access is not yet secured, that procurement is the
  long pole — start it now, in parallel with everything else. The code is
  structured for it (`SWIGGY_CLIENT_MODE=mcp` + an MCP server implementing six
  tools at `swiggy_mcp.py:85-165`), but the server itself must be built against
  real Swiggy partner APIs, including a real OAuth authorize→callback flow
  (none exists today).
- **Where will this be hosted?** Backend (FastAPI/uvicorn) + Postgres +
  outbound to Meta/Swiggy; frontend as a static PWA behind something that
  routes `/api` to the backend. The choice (single VM + reverse proxy vs.
  managed PaaS + managed Postgres vs. containers) determines most of the
  Tier-1 infra work.

## 4. Blockers (Tier 0 — cannot go live)

| # | Blocker | Evidence | Fix shape |
|---|---|---|---|
| B1 | **OTP login code printed to stdout** — plaintext code in logs on every request; anyone with log access logs in as any phone | `api/account.py:87` (also `54, 74-77, 85`) | Delete the stray `print()`s (a redacted `logger` already exists at `account.py:96`) |
| B2 | **No Swiggy integration** — cart/checkout/OAuth simulated; real MCP server binary absent | `swiggy_mcp.py:39-82`, `mock_swiggy.py:188-221` | Obtain Swiggy partner access; build MCP server; add real OAuth flow |
| B3 | **No deployment path** — no Dockerfile/host/CD; prod frontend has no route to backend | `vite.config.ts:76-84` (dev-only proxy); only `infra/docker-compose.yml` (dev Postgres) + `ci.yml` (test-only) | Build backend image, static frontend host, reverse proxy for `/api`, migration runner |
| B4 | **No OTP-request rate limit** — real WhatsApp message per call, no throttle; repeat calls also reset the brute-force counter | `api/account.py:72-97`, `web_auth.py:125` | Per-phone + per-IP rate limiting |
| B5 | **Signature check auto-skips in `local`** — `APP_ENV=local` + empty app secret bypasses webhook HMAC; a misconfigured prod deploy accepts forged webhooks | `config.py:47-49`, `api/whatsapp.py:92-113` | Gate on explicit flag; assert `app_env != local` at startup |

## 5. Durability & infra (Tier 1 — required for a real service)

- **Switch to Postgres and make it prod-shaped.** Default is `memory`
  (`config.py:13`), which loses sessions, carts, timelines, OTPs, logins, and
  short links on restart — and wipes the webhook dedup ledger, so Meta retries
  create **duplicate sessions**. Then: add **connection pooling**
  (`db/adapter.py:31-44` opens a fresh connection per query) and either wire up
  **Row-Level Security** (policies exist in migrations but `db/rls.py` has zero
  callers and the app runs as the table owner, so RLS is inert) or stop
  treating it as a control. Migrations are raw SQL via a shell loop with no
  version tracking — replace with a real migration runner.
- **Secrets management.** A live-looking Meta token + app secret sit in
  plaintext `src/backend/.env` (gitignored, never committed — verified). Rotate
  them and move to a secrets manager.
- **Observability.** Logging is unconfigured (no level/format/JSON); no metrics
  (Prometheus/OTel) and no error tracking (Sentry). You will be blind under
  load. `readyz` exists but reports mode strings without validating that
  `meta`/`mcp` credentials are present.
- **Config hardening.** Ship a production config profile that fails fast when
  mock modes or `local` env are set with real traffic.

## 6. Product quality (Tier 2)

- **The "AI agent" is regex, not an LLM.** `LLM_MODE` is inert (read only by
  the health check, `main.py:115`); `MockIntentParser` always runs
  (`agent.py:196,202`). Fine for demo phrasing, brittle on real messages.
  Wiring a real LLM parser is the biggest lever on conversational quality — not
  a hard blocker for a narrow pilot.
- **"Realtime" is 2.5s polling** (`useSupabaseCartRealtime.ts:46`), not
  Supabase despite the name. Functionally fine; only revisit for scale/battery.
- **PII redaction is India-phone-only regex** — international numbers and
  oddly-formatted cards pass through to the stored timeline.

## 7. Dimensions not yet covered

### 7.1 Testing & QA
- **Strong unit coverage** (133 backend, 28 frontend), deterministic mocks make
  CI fast and reliable. Real gaps: **no load/soak testing** (and the
  connect-per-query DB pattern is exactly what load testing would expose); the
  **real Swiggy and real-LLM paths have no tests** because they don't exist;
  **no end-to-end test against Meta sandbox** in CI. `integration-test-plan.md`
  documents manual steps but they aren't automated.
- Before GA: a load test at target concurrency, a staging environment wired to
  Meta sandbox + a Swiggy test tenant, and a smoke suite that runs against it.

### 7.2 Scalability & cost
- **Horizontal scaling is currently impossible.** In-memory adapters, the
  idempotency ledger, OTP store, and short-link map are all process-local — two
  replicas would double-create sessions and lose each other's logins. Moving
  everything to Postgres (Tier 1) is the prerequisite for running more than one
  instance behind a load balancer.
- **Cost drivers to model before launch:** Meta charges per 24-hour
  conversation (and per template message) — every WhatsApp handoff has a
  marginal cost; a real LLM adds per-message inference cost; Swiggy partner
  terms may have their own. None of this is instrumented today, so there is no
  per-order cost visibility.
- **DB connection exhaustion** is the first thing that breaks under load given
  connect-per-query + a fresh connection per health check (`main.py:98-106`).

### 7.3 Compliance & legal
- **PII.** Phone numbers are stored raw by design (`sender_wa_id`), and the
  timeline stores redacted message text. For an India-facing product this
  implicates the **DPDP Act** (consent, purpose limitation, retention,
  erasure). There is no retention policy, no deletion path, and no consent
  capture.
- **WhatsApp Business Policy.** Unsolicited messaging and the 24-hour service
  window are policy-enforced; template content needs Meta approval. A policy
  review is required before onboarding real users.
- **Payments.** Checkout happens on Swiggy, so PCI scope is largely offloaded —
  a genuine architectural advantage. Confirm no card data ever transits
  EasyOrder (today it doesn't).
- **Terms/Privacy.** None present; both are table stakes for a public launch.

### 7.4 Operational readiness
- **Runbooks exist** for local demo, tunnels, WhatsApp handoff, and webhook
  troubleshooting — a good start. Missing: **backup/restore** for Postgres, an
  **incident/on-call** process, a **rollback** procedure, and **alerting** on
  the health endpoints.
- **No backups** are configured because there's no managed DB yet.

## 8. Phased go-live plan

A pragmatic path that de-risks without waiting for everything:

**Phase 0 — Internal pilot (mock Swiggy, real WhatsApp).** Ship to a private
allowlist where checkout is explicitly simulated. Requires: B1, B4, B5
(security), Tier-1 Postgres + pooling, a basic deploy (B3), Meta creds +
approved template. This proves the WhatsApp→PWA→cart loop with real users and
is achievable without Swiggy access.

**Phase 1 — Limited launch (real Swiggy).** Add B2 (Swiggy MCP server + OAuth),
real-dependency staging + smoke tests, error tracking, and a load test. This is
the first launch where a real order can complete.

**Phase 2 — GA.** Real LLM intent parser, RLS enforced, cost instrumentation,
compliance (DPDP retention/consent, Terms/Privacy, WhatsApp policy sign-off),
alerting, backups, and an incident process.

## 9. Effort sizing (rough, engineering-only)

| Item | Tier | Rough size |
|---|---|---|
| Remove OTP prints, harden signature gate | 0 | hours |
| OTP rate limiting | 0 | 1–2 days |
| Deploy path (backend image + static host + `/api` routing + migration runner) | 0/1 | ~1 week |
| Postgres default + connection pooling | 1 | 2–3 days |
| RLS enforcement (or formally drop it) | 1 | 3–5 days |
| Observability (structured logs, metrics, Sentry) | 1 | 3–5 days |
| Swiggy MCP server + OAuth flow | 0 | **Large / unknown — gated on partner access** |
| Real LLM intent parser | 2 | 3–5 days |
| Compliance (retention, consent, Terms/Privacy, policy review) | 2 | cross-functional, not just eng |

## 10. Open decisions for the owner

1. Is Swiggy partner API access secured or in progress? (Longest pole.)
2. Target hosting (managed PaaS + managed Postgres is the fastest path).
3. Is a **mock-checkout internal pilot** acceptable as Phase 0, or must the
   first launch place real orders?
4. Real LLM at launch, or ship the regex parser for a narrow pilot first?

---

**Immediate, in-repo quick wins I can take now:** the Tier-0 security fixes
(remove the OTP `print`s, add OTP rate limiting, harden the signature-skip
default) and the deployment scaffolding (backend Dockerfile, static frontend
host config, `/api` reverse-proxy, a migration runner). The Swiggy and hosting
questions above are prerequisites I can't resolve from the code.
