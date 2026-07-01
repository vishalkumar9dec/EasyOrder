# Issue #6 Test Report: Session Bootstrap Planning Canvas

Date: 2026-07-01
Branch: `codex/issue-6-session-bootstrap-canvas`

## Scope

Implemented tokenized session bootstrap for the PWA route:

- `GET /api/session/{session_id}?token=...` validates guest and host tokens.
- Guest responses return redacted cart, warning, degraded-state, and role data.
- Host responses return host role and checkout eligibility without exposing token material.
- React route `/session/:sessionId` loads the backend state through the Vite `/api` proxy.
- Session cart rows display Food restaurant names and Instamart brand/source context.
- Loading, unauthorized, not-found, guest, host, and degraded session states are represented.

## Automated Checks

| Command | Result | Notes |
|---|---|---|
| `cd src/backend && .venv/bin/python -m pytest tests/test_session_api.py` | Passed | 4 tests covered guest bootstrap, host bootstrap, invalid/cross-session token rejection, and missing-session `404`. |
| `cd src/frontend && npm run test` | Passed | 2 test files and 15 tests passed, including route parsing and API adapter coverage. |
| `make test` | Passed | Backend: 42 tests passed. Frontend: 2 test files and 15 tests passed. |
| `make frontend-build` | Passed | Vite production build completed successfully. |
| `src/backend/.venv/bin/python -m ruff check src/backend/app src/backend/tests` | Passed | All checks passed. |
| Local API smoke against `localhost:8000` | Passed | Created a session through the WhatsApp webhook, loaded guest bootstrap, verified no host token field, invalid token `401`, and missing session `404`. |

## Browser/Manual Verification Notes

Python Playwright was not installed in the local Python environment. Node
Playwright was available, but the Node browser runtime could not reach localhost
from this sandbox. The frontend route was still verified through TypeScript,
production build, route/adapter tests, and backend API smoke. Manual browser
verification should follow `UI-11` through `UI-14` in
`docs/manual-ui-test-plan.md`.

## Regression Notes

No regressions found in automated tests, frontend production build, Ruff, or the
local API smoke. The new route is read-only; cart mutation and realtime behavior
remain planned for issue #7.
