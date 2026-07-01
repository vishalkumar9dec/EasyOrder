# Issue #7 Cart Mutation And Realtime Collaboration Test Report

Date: 2026-07-01
Branch: `codex/issue-7-cart-realtime`

## Scope

Issue [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7) implements Task
5.2 and Task 6.2:

- Session-scoped cart item create, update, and delete API routes.
- Guest/host token authorization for cart mutations.
- Source-attribution validation for newly created cart items.
- API-backed cart controls on the PWA session route.
- Realtime connection state plus local polling fallback so multiple clients can
  converge on the latest cart state.

## Automated Verification

| Command | Result | Coverage |
|---|---|---|
| `cd src/backend && .venv/bin/python -m pytest tests/test_session_api.py` | Pass: 7 tests | Session bootstrap, guest/host role bootstrap, invalid/cross-session links, cart CRUD, cross-session mutation rejection, source-attribution validation, missing cart item `404`. |
| `cd src/frontend && npm run test` | Pass: 2 files, 16 tests | Session route parsing, bootstrap adapter, API id mapping, realtime snapshot reconciliation without duplicates. |
| `cd src/frontend && npm run build` | Pass | TypeScript project build and Vite production bundle. |
| `make test` | Pass: 45 backend tests, 16 frontend tests | Full backend and frontend regression suite. |
| `make frontend-build` | Pass | Production frontend bundle. |
| `src/backend/.venv/bin/python -m ruff check src/backend/app src/backend/tests` | Pass | Backend lint check. |
| `python3 .agents/skills/easyorder-daily-status/scripts/daily_status.py --repo-root .` | Pass | Full local verification, WhatsApp fixture probes, and documentation signal scan. |

## Local HTTP Smoke

Started the backend with `make backend-dev`, posted
`docs/api-test-data/whatsapp-tagged-normal.json` to the WhatsApp webhook, extracted
the generated guest session link, then called the new cart mutation routes:

- `POST /api/session/{session_id}/cart-items?token=...`: created `Smoke napkins`.
- `PATCH /api/session/{session_id}/cart-items/{cart_item_id}?token=...`: changed quantity to `3`.
- `DELETE /api/session/{session_id}/cart-items/{cart_item_id}?token=...`: removed the item.

Result: pass. Final session returned to the original two recommended cart items.

## Manual Verification To Run

Use [manual-ui-test-plan.md](../manual-ui-test-plan.md):

- `UI-11`: guest opens a generated session link and sees the realtime strip.
- `UI-15`: guest adds Food and Instamart items, changes quantity, and removes an item.
- `UI-16`: two windows opened on the same session converge through the polling fallback.
- `API-17` through `API-19`: cart mutation CRUD, cross-session rejection, and validation coverage.

## Manual Verification Completed

Ran a Playwright smoke against local backend/frontend dev servers managed by
`webapp-testing/scripts/with_server.py`.

Result: pass.

- `UI-11`: generated a mock WhatsApp session, opened the guest session route,
  verified `Planning canvas`, guest role, source-attributed cart rows, realtime
  connected state, and no `host_` token exposure.
- `UI-15`: added Food and Instamart rows through the real session API, verified
  `Manual restaurant` and `Manual brand · Manual Instamart source`, changed Food
  quantity, and removed rows.
- `UI-16`: opened the same guest session in a second browser page, added an
  Instamart item in the first page, and verified the second page refreshed to one
  synced row without duplicates.
- Browser console errors: none.

## Regressions

No regressions found in targeted checks, the full verification suite, or the local
HTTP smoke.

## Known Limits

The browser currently uses a polling fallback over `GET /api/session/{session_id}`
instead of a native Supabase Realtime WebSocket subscription. The hook boundary is
isolated in `useSupabaseCartRealtime.ts` so event-channel wiring can replace the
fallback once the frontend has a Supabase client dependency and browser-safe
configuration.
