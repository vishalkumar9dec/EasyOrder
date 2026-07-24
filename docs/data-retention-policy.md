# EasyOrder Data Retention & Erasure

Engineering-facing companion to the [Privacy Policy draft](privacy-policy-draft.md).
Describes the two mechanisms that back the "how long we keep it" and "your
right to delete" sections of that policy, and how to operate them.

## What's stored, and where

Sessions, cart items, and timeline events are the PII-bearing tables
(`infra/migrations/0001_session_persistence.sql`,
`0002_session_events.sql`). `cart_items` and `session_events` both have
`ON DELETE CASCADE` on `sessions.session_id`, so deleting a `sessions` row
removes all of its cart and timeline data in one statement — there is
nothing else to clean up per session.

## 1. Self-service erasure (user-triggered, real-time)

A user can delete all of *their own* EasyOrder data at any time by
messaging the EasyOrder business number:

- `"delete my data"` (or "erase my info", "forget me", etc.) → replies with
  a warning and does **not** delete anything.
- `"delete my data confirm"` → deletes every session (and cascading cart/
  timeline data) tied to that WhatsApp number, and confirms how many
  sessions were removed.

Requiring the confirmation word in the *same* message (rather than a
stateful two-turn flow) keeps the implementation simple while still making
accidental deletion effectively impossible — see
`services/intent_router.py` (`_DATA_DELETION_PATTERNS`,
`_DELETION_CONFIRMATION`) and `services/privacy.py`.

This only ever deletes the requesting number's own data —
`IDBAdapter.delete_sessions_for_host` filters by `host_phone`, so it cannot
affect other users' sessions.

## 2. Scheduled retention (operator-triggered, batch)

`scripts/easyorder_data_retention.py` deletes sessions older than a
configurable cutoff (default **90 days**):

```bash
# Report what would be deleted, without deleting anything
make data-retention-dry-run RETENTION_DAYS=90

# Actually delete
make data-retention RETENTION_DAYS=90
```

Run this on a schedule (cron, a CI scheduled job, etc.) against the
production database. It is a no-op — and says so — when
`PERSISTENCE_MODE=memory`, since in-memory sessions don't survive a
restart anyway.

`[TODO: decide and document the actual retention period with product/legal
before launch — 90 days here is a reasonable engineering default, not a
reviewed policy decision. Wire this script into an actual scheduler
(cron/CI) once a hosting decision is made — see docs/production-readiness.md.]`

## What this does not yet cover

- **Login state** (`login_otps`, `web_sessions` in `services/web_auth.py`)
  is not touched by either mechanism. OTPs expire in 5 minutes and web
  sessions in 30 days by design, so they aren't indefinite PII storage, but
  a thorough DPDP review should confirm that's an acceptable position
  rather than an oversight.
- **Short links** (`short_links` table) are not explicitly purged when
  their target session is deleted. A dangling short link resolves to a
  session that no longer exists, which the redirect endpoint already
  handles as "not found" — not a data leak, just an orphaned row.
  `[TODO: consider a cleanup job if the short_links table grows large
  enough to matter operationally.]`
