# Postgres Persistence (Task 10.7)

## Enable

```bash
make db-up && make db-migrate       # start container, apply ALL migrations
# in src/backend/.env:
PERSISTENCE_MODE=postgres
# restart the backend (settings are read at startup)
```

`make db-migrate` is idempotent and applies every `infra/migrations/0*.sql`
in order — including `0004_cart_source_attribution_backfill.sql`, which
converges databases initialized before the source-attribution columns existed
(`CREATE TABLE IF NOT EXISTS` skips stale tables silently).

## What becomes durable

Sessions, cart items, timeline events (`session_events`), wamid dedup ledger,
and short links (`short_links`). After a backend restart: old tokenized links
and short links keep working, and Meta webhook retries still dedupe.

## Verify

```bash
curl -s localhost:8000/readyz   # "database": "postgres_ok"
```

Then follow MT-10.7-A in the manual test plan (create session → restart →
same links work).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `"database": "postgres_error"` in readyz | `make db-up`; check `DATABASE_URL`; Docker daemon running? |
| `Failed to create session` + `UndefinedColumnError` | Old volume — rerun `make db-migrate` (0004 converges it) |
| Old links dead after restart | `PERSISTENCE_MODE` still `memory` — set it and restart |
| Fully reset local data | `make db-down && docker volume rm easyorder-postgres-data && make db-up && make db-migrate` |
