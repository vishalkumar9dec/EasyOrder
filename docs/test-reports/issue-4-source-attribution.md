# Test Report: Issue #4 Source Attribution

Date: 2026-06-30
Branch: `codex/issue-4-source-attribution`
PR: https://github.com/vishalkumar9dec/EasyOrder/pull/15

## Scope

This report covers the issue #4 source-attribution follow-up for the EasyOrder
agent-created cart. The implementation adds and verifies:

- Food cart item source fields: `restaurant_id` and `restaurant_name`.
- Instamart cart item source fields: `source_label` and optional `brand_name`.
- Domain validation and migration constraints for required source fields.
- Mock Swiggy restaurant/brand/source metadata.
- Agent guardrails that skip malformed source-less results with
  `SOURCE_ATTRIBUTION_MISSING`.
- Manual verification documentation updates in `docs/manual-ui-test-plan.md`.
- Playground cart rows now display source attribution under item names.

## UI Fix Follow-Up

After manual review, the playground UI was still showing only vertical/dietary
tags on cart rows. The follow-up fix adds source metadata to the frontend
playground fixtures and renders a compact source line under each item name.

Expected visible examples in the `Normal` scenario:

- `Chicken dum biryani family pack` shows `Biryani House`.
- `Paneer tikka rolls` shows `Roll House`.
- `Cola 2L bottle` shows `Thums Up · Instamart Mock Store`.

## Automated Test Results

| Command | Result | Notes |
|---|---|---|
| `cd src/backend && .venv/bin/python -m pytest` | PASS | 37 backend tests passed. |
| `make test` | PASS | Backend 37 tests passed; frontend 12 tests passed. |
| `make frontend-build` | PASS | Production frontend build completed. |
| `src/backend/.venv/bin/python -m ruff check src/backend/app src/backend/tests` | PASS | No lint issues found. |
| `cd src/frontend && npm run test` | PASS | 12 frontend tests passed, including source-context coverage for visible cart rows. |

## API Fixture Smoke Results

Executed against FastAPI `TestClient` using payloads from `docs/api-test-data`.

| Payload | Result |
|---|---|
| `whatsapp-injection.json` | PASS: `400 Tagged message was rejected by input guardrails` |
| `whatsapp-low-budget.json` | PASS: `200 created` |
| `whatsapp-tagged-normal.json` | PASS: `200 created` |
| `whatsapp-untagged.json` | PASS: `200 ignored` |
| `whatsapp-vegetarian.json` | PASS: `200 created` |

## Source Attribution Smoke Result

Executed the in-process mock-agent smoke from `docs/manual-ui-test-plan.md`.

Observed output:

```text
status: ACTIVE
food-chicken-biryani food rest-biryani-house Biryani House None None
im-cola instamart None None Thums Up Instamart Mock Store
warnings: []
```

Result: PASS.

The normal tagged prompt creates one Food item with restaurant identity and one
Instamart item with brand/source context. No warnings are produced for the valid
normal prompt.

## Regression Assessment

No regressions were found in automated tests, frontend build, linting, webhook
fixture smoke tests, or the source-attribution smoke test.

Existing response-boundary behavior is unchanged: the WhatsApp webhook still
returns session status and links, not full cart internals. Cart source details
remain manually inspectable through the in-process backend smoke until the
session-read API is implemented in a later task. The local playground now also
shows source context using hard-coded fixture metadata until persisted session
loading is implemented.

## Manual Verification

Use `docs/manual-ui-test-plan.md`.

- Run `UI-01` through `UI-10` for current browser playground regression.
- In `UI-01`, confirm Food rows show `Biryani House` and `Roll House`, and the
  Instamart row shows `Thums Up · Instamart Mock Store`.
- In `UI-09`, confirm manually added Food rows show `Manual restaurant`, and
  manually added Instamart rows show `Manual brand · Manual Instamart source`.
- Run `API-01` through `API-11` for backend/API verification.
- For source attribution, run the in-process smoke script and confirm:
  - session status is `ACTIVE`;
  - Food cart item includes restaurant name `Biryani House`;
  - Instamart cart item includes brand `Thums Up`;
  - Instamart cart item includes source label `Instamart Mock Store`;
  - warnings are empty for the normal prompt.

## Merge Readiness

The implementation is ready for manual verification. PR #15 should remain
unmerged until manual approval is complete.
