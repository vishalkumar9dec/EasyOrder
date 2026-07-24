# ADR 0007: Drop Row Level Security, Application-Layer Authorization Is The Boundary

## Status

Accepted

## Context

Task 1.4 (ADR-predating this one) added PostgreSQL Row Level Security
policies on `sessions`, `cart_items`, and `session_events`, plus RLS-enabled
(policy-less) `short_links`, `login_otps`, and `web_sessions`. The design
assumed a Supabase-managed deployment: a PostgREST-style `request.headers`
session variable populated per-request by a non-owner `authenticated`/`anon`
role, with policies matching a guest/host token against stored hashes.

That deployment shape never happened. This repo's actual Postgres access —
local Docker Compose, production Docker Compose, and every migration — all
connect as `easyorder`, the single role the `postgres` image bootstraps as
database owner. Postgres bypasses RLS for the table owner unless `FORCE ROW
LEVEL SECURITY` is set, which no migration ever set. No second, non-owner
role was ever created. The result: RLS policies existed and looked correct,
but structurally could not run against a single real request, regardless of
whether the `request.headers` session variable was ever populated.

A companion helper module, `src/backend/app/db/rls.py`
(`build_rls_headers`/`encode_rls_headers`/`set_rls_headers`), existed to
populate that session variable — but had zero callers anywhere in
`AsyncPostgresDBAdapter` or any request path. Its only consumer was its own
isolated unit test, which asserted the SQL string was well-formed against a
fake connection, not that RLS actually blocked anything.

Meanwhile, the real authorization boundary was built and has been enforced
the entire time: `authorize_session_role()` in `src/backend/app/api/session.py`
compares the caller's bearer token (guest token, or host token re-hashed
with the same SHA-256 the dead RLS predicate used) against the fetched
session row, in Python, before returning anything. Every session-scoped
endpoint (`session.py`: bootstrap, checkout validation/confirmation, cart
mutations) already goes through this check via `get_authorized_session()`.
`docs/production-readiness.md` (2026-07-15) named this gap explicitly and
sized two options: wire RLS up for real, or formally drop it.

Wiring RLS up for real would require: a second, non-owner Postgres role;
`GRANT`s and `FORCE ROW LEVEL SECURITY` on every table; new policies for
`short_links`/`login_otps`/`web_sessions` (currently policy-less — RLS
enabled with no policy is deny-all, so introducing a non-owner role today
without new policies would break login/OTP/short-links outright); and a
structural rewrite of `AsyncPostgresDBAdapter` so every operation opens a
transaction and calls `set_config` with the caller's token before querying
— non-trivial against the shared `AsyncpgConnectionPool`, since RLS session
state is connection/transaction-scoped, not held by the pool. Sized at
several days, matching production-readiness.md's own 3-5 day estimate.

## Decision

Formally drop RLS. It never provided defense-in-depth in this deployment —
it provided the *appearance* of a second layer while only one layer
(`authorize_session_role`) ever actually ran. A migration
(`0007_drop_rls.sql`) disables RLS and drops every policy on all six
tables; the dead `db/rls.py` module and its isolated unit test are removed.
`authorize_session_role()` is documented as the sole, real authorization
boundary — which is honest about current behavior and matches what's
already fully tested (`test_startup_guards.py`, the session API test suite).

This is reversible: `0007_drop_rls.down.sql` recreates the exact original
policies faithfully, verified against a real Postgres instance in both
directions (`ALTER TABLE ... DISABLE/ENABLE ROW LEVEL SECURITY`, then
`pg_policies`/`pg_class.relrowsecurity` inspected directly) before this ADR
was written.

## Consequences

- **No regression.** The thing that actually protected session/cart data —
  `authorize_session_role()` — is unchanged and was never RLS's doing.
- **No defense-in-depth today.** A bug in `authorize_session_role`, or a
  future endpoint that forgets to call `get_authorized_session`, would not
  be caught by a second database-layer check. This is a real, accepted
  tradeoff, not an oversight — revisit if/when the DB access pattern
  changes (e.g. a non-owner role becomes natural for another reason, at
  which point wiring real RLS policies back in via
  `0007_drop_rls.down.sql`'s recreated policies is a reasonable starting
  point, not a from-scratch design).
- **Docs (`docs/hld.md`, `docs/lld.md`, `infra/README.md`,
  `docs/production-readiness.md`) are updated** to stop describing RLS as
  an active control. Historical planning docs (`docs/implementation-tasks.md`,
  `docs/implementation-plan.md`, `docs/adr/0001-firestore-realtime-sync.md`,
  `docs/decision-map.md`) are left as-is — they're accurate records of what
  was originally planned/built at the time, and per this repo's own
  documentation convention, ADRs (not retroactively edited planning docs)
  are the source of truth when they disagree.
- **Migration history is not rewritten.** `0001`/`0002`/`0003`/`0006` still
  show RLS being enabled — that's what those migrations did at the time.
  `0007` is a new forward migration, matching this repo's append-only
  migration convention (and the versioned migration runner introduced
  alongside it, `scripts/run_migrations.py`, which tracks applied versions
  rather than blindly re-running every file).
