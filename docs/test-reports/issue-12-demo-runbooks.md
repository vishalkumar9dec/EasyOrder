# Issue #12 Local Demo And Runbooks Test Report

Date: 2026-07-02
Branch: `codex/issue-12-demo-runbooks`

## Scope

Issue [#12](https://github.com/vishalkumar9dec/EasyOrder/issues/12) implements
Tasks 9.1 and 9.2:

- Add a repeatable mock-mode demo smoke from WhatsApp fixture to sequential
  checkout URLs.
- Add `make demo-smoke`.
- Add request-id response headers and structured request logging fields.
- Add local demo, operations, common failure, SQL inspection, and release
  validation runbooks.
- Update manual verification docs.

## Automated Verification

| Command | Result | Coverage |
|---|---|---|
| `cd src/backend && .venv/bin/python -m pytest tests/test_demo_smoke.py tests/test_health.py` | Pass: 5 tests | Demo smoke flow and request-id middleware behavior. |
| `make demo-smoke` | Pass | In-process WhatsApp-to-checkout demo prints checkout URLs and final `ORDERED` status. |
| `make test` | Pass: 67 backend tests, 20 frontend tests | Full backend and frontend regression suite. |
| `make frontend-build` | Pass | Production frontend bundle. |
| `src/backend/.venv/bin/python -m ruff check src/backend/app src/backend/tests` | Pass | Backend lint check. |

## Manual Verification To Run

Use [manual-ui-test-plan.md](../manual-ui-test-plan.md):

- `API-36`: run `make demo-smoke` and confirm checkout URLs plus `ORDERED` status.
- `API-37`: confirm API responses preserve `x-request-id`.
- `API-38`: follow `docs/runbooks/local-demo.md` and
  `docs/runbooks/operations.md`.

## Manual Verification Completed

`make demo-smoke` was run locally and produced one Food checkout URL, one
Instamart checkout URL, and final session status `ORDERED`.

## Regressions

No regressions found in targeted demo smoke and request-id tests, the full
verification suite, production frontend build, or backend lint.

## Known Limits

The demo smoke is an in-process API flow, not a real browser automation run. Live
provider checks still require sandbox credentials and are covered by the
integration runbook.
