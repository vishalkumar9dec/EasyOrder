# Issue #8 Warning, Dietary, And Degraded-State UI Test Report

Date: 2026-07-01
Branch: `codex/issue-8-warning-dietary-ui`

## Scope

Issue [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8) implements Task
6.3 for the real PWA session route:

- Preserve structured warning objects in the frontend session view model.
- Highlight budget review states when the API returns `budget_warning=true` or
  the cart total exceeds the session budget.
- Surface dietary review chips on affected cart rows while preserving restaurant
  and source labels.
- Render structured signal cards for budget, dietary, degraded availability, and
  source review warnings.
- Keep manual Food and Instamart item addition controls available while degraded
  vertical warnings are visible.

## Automated Verification

| Command | Result | Coverage |
|---|---|---|
| `cd src/frontend && npm run test` | Pass: 2 files, 17 tests | TypeScript build, session adapter, budget warning derivation, dietary item warning derivation, realtime reconciliation regression. |
| `make test` | Pass: 45 backend tests, 17 frontend tests | Full backend and frontend regression suite. |
| `make frontend-build` | Pass | Production frontend bundle. |
| `src/backend/.venv/bin/python -m ruff check src/backend/app src/backend/tests` | Pass | Backend lint check. |
| `python3 .agents/skills/easyorder-daily-status/scripts/daily_status.py --repo-root .` | Pass | Full local verification, WhatsApp fixture probes, and documentation signal scan. |

## Manual Verification To Run

Use [manual-ui-test-plan.md](../manual-ui-test-plan.md):

- `UI-17`: create a low-budget or vegetarian session and verify budget/dietary
  review states.
- `UI-18`: load a degraded session and verify degraded availability signals while
  manual cart controls stay available.
- `API-20`: confirm frontend adapter coverage for structured warning derivation.

## Manual Verification Completed

Ran a Playwright smoke against local backend/frontend dev servers managed by
`webapp-testing/scripts/with_server.py`.

Result: pass.

- `UI-17`: generated a low-budget session through the WhatsApp webhook and
  verified the budget review strip, highlighted budget panel, over-budget amount,
  and `Budget review` signal. Generated a vegetarian session, added a non-veg
  Food item through the session API, and verified the affected cart row showed
  `Dietary review` while preserving `Kebab Junction`.
- `UI-18`: loaded a degraded bootstrap response and verified the degraded alert
  strip, `Degraded availability` signal, `Food degraded` badge, source-attributed
  Instamart row, and visible `+ Food` / `+ Instamart` manual controls.
- Browser console errors: none.

## Regressions

No regressions found in targeted frontend checks, the full verification suite, or
the manual Playwright smoke.

## Known Limits

Issue #8 does not add new backend warning types or checkout validation. It renders
the warning data already returned by the session bootstrap API. Final stock/price
validation and checkout recovery remain in issue #9.
