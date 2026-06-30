# EasyOrder Manual UI Test Plan

Last verified: 2026-06-29.

This document reflects the current project state from `docs/easyorder-prd.md`,
`docs/implementation-tasks.md`, the local worktree, and live GitHub issue status.

## Current Scope

The current UI is the local product-validation playground from GitHub issue
[#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). The backend now has
the issue [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4) mock agent
initialization path, but the browser UI is not yet the production PWA session route
backed by persisted sessions, realtime cart updates, or Swiggy checkout APIs.

Current GitHub status:

| Order | Issue | Scope | Status |
|---:|---|---|---|
| 01 | [#1](https://github.com/vishalkumar9dec/EasyOrder/issues/1) | Tasks 0.1-1.1: foundation, local infra, app shell | Closed |
| 02 | [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2) | Product validation slice: local app playground | Closed |
| 03 | [#14](https://github.com/vishalkumar9dec/EasyOrder/issues/14) | Tasks 1.2-2.1: domain, persistence, tokens, RLS | Closed |
| 04 | [#3](https://github.com/vishalkumar9dec/EasyOrder/issues/3) | Tasks 3.1-3.2: mention-only WhatsApp intake | Closed |
| 05 | [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4) | Tasks 2.2, 4.1-4.5: agent initializes consolidated cart | Source attribution implemented; manual verification pending |
| 06 | [#5](https://github.com/vishalkumar9dec/EasyOrder/issues/5) | WhatsApp group/host link handoff | Open, ready next |
| 07-14 | [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6)-[#13](https://github.com/vishalkumar9dec/EasyOrder/issues/13) | Session PWA, realtime, warnings, checkout, integrations, E2E, hardening | Open, blocked |

## Verification I Performed

Commands run locally:

```bash
make test
make frontend-build
```

Results:

- `make test`: backend tests passed with 35 tests; frontend tests passed with 1 test file and 11 tests.
- `make frontend-build`: production build passed.
- Browser UI verification on `http://localhost:5174/`: 93 scripted checks passed.
- Browser console errors during scripted UI verification: none.

Browser checks covered:

- Demo renders on desktop and mobile viewports.
- All 7 scenario tabs switch correctly.
- Each scenario shows its expected WhatsApp prompt, signal/warning, and checkout state.
- Mock checkout actions are visible but do not navigate away from the playground.
- Host can validate checkout.
- Guest cannot see the validate checkout button and sees guest-only guidance.
- Manual Food and Instamart item additions update the cart.
- Setting an item quantity to `0` removes that item.
- Mobile viewport renders the demo and guest/degraded-state cues.

## UI Changes From Issue #4

No browser-visible UI changed in issue [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4).
The current web app is still the local playground with hard-coded scenarios. The new
development is backend/API behavior: tagged WhatsApp webhook payloads now run through
the mock-first agent initialization path and create initialized `ACTIVE` or `DEGRADED`
sessions in the local in-memory mock store. The agent-generated backend cart now
preserves source attribution: Food items include restaurant id/name, and Instamart
items include a source label plus brand name when available.

What this means for manual testing:

- Use `UI-01` through `UI-10` to regression-test the current browser playground.
- Use `API-01` through `API-11` below to test the new backend agent path.
- You cannot yet open the returned `/session/...` guest link in a real session UI; that
  comes with the PWA bootstrap work in issue [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6).

## Required UI Changes From Vendor/Restaurant Discovery

These requirements are now enforced in the backend cart contract and remain pending
for browser display in the later PWA/session UI issues:

- Food cart rows must display the restaurant name for every item.
- Instamart cart rows must display brand/source context when available.
- Session summaries and checkout previews must show how many Swiggy orders the host will place.
- Food checkout preview must group items by restaurant because Swiggy Food cannot place one order across multiple restaurants.
- If a session includes two restaurants plus Instamart, the host should see three checkout steps before payment.

## How To Run The Current UI

From the repository root:

```bash
make setup
make frontend-test
make frontend-build
make frontend-dev
```

Open [http://localhost:5173](http://localhost:5173). If port `5173` is busy:

```bash
make frontend-dev FRONTEND_PORT=5174
```

The full-stack convenience command is also available:

```bash
make up
```

Use `Ctrl+C` to stop the long-running dev servers.

## Manual UI Tests Available Now

| ID | Use case | Steps | Validate | Current coverage | Next related issue |
|---|---|---|---|---|---|
| UI-01 | Normal group order | Open the app, go to the interactive demo, select `Normal`, keep role as `Host`, click `Validate Checkout`, then click both mock checkout actions. | Prompt mentions biryani, paneer rolls, cold drinks, 6 people, and budget 3000. Cart has Food and Instamart items. Checkout shows `Ready for mock checkout`. Food and Instamart mock checkout actions are visible and clicking them keeps you on the EasyOrder playground. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Real agent-generated cart in [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4), persisted session loading in [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6), local E2E demo in [#12](https://github.com/vishalkumar9dec/EasyOrder/issues/12). |
| UI-02 | Over-budget cart | Select `Budget`, click `Validate Checkout`. Try reducing item quantities with the quantity controls. | Total is above budget at first, budget section says over budget, warnings mention the overage, and checkout remains allowed with `Budget warning only`. Reducing quantities updates the total and can recover the budget state. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Backend output guardrails in [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4); real warning UI in [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). |
| UI-03 | Dietary mismatch | Select `Dietary`, choose `Veg` in `Food preference`, click `Validate Checkout`, then switch to `Non-veg` and validate again. | With `Veg`, a non-veg item appears, warnings include vegetarian mismatch, and checkout shows `Dietary review needed`. With `Non-veg`, the dietary warning clears and checkout changes to `Ready for mock checkout`. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Backend dietary warning persistence in [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4); actionable PWA warning UI in [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). |
| UI-04 | Degraded Food availability | Select `Food down`, add a Food item manually, then click `Validate Checkout`. | Food degraded badge appears. Existing cart contains Instamart items. Manual Food addition appears in the cart. Checkout shows `Partial mock checkout`. The Instamart mock checkout action stays inside the playground when clicked. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Worker degradation from the agent in [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4); manual degraded-state UX in [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). |
| UI-05 | Degraded Instamart availability | Select `IM down`, add an Instamart item manually, then click `Validate Checkout`. | Instamart degraded badge appears. Existing cart contains Food items. Manual Instamart addition appears. Checkout shows `Food checkout only`. The Food mock checkout action stays inside the playground when clicked. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Worker degradation from the agent in [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4); real UI states in [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). |
| UI-06 | Stock change at validation | Select `Stock`, inspect the affected item, click `Validate Checkout`. | The item has an unavailable tag, substitute copy mentions `Butterscotch ice cream tub`, and checkout is `Blocked` with `Unavailable item`. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Real pre-checkout validation API in [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9); sequential checkout flow in [#10](https://github.com/vishalkumar9dec/EasyOrder/issues/10). |
| UI-07 | Price change at validation | Select `Price`, inspect the affected item, click `Validate Checkout`. | The item has a price-changed tag, warning mentions price change before payment, and checkout is `Blocked` with `Price changed`. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Real pre-checkout validation API in [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9). |
| UI-08 | Host-only checkout affordance | In any scenario, select `Host`, then select `Guest`. | Host sees `Validate Checkout`. Guest does not see the button and sees `Guests can edit the cart. Only the host can validate and checkout.` | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2), but role is local UI state only. | Backend-derived host/guest role in [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6); host-only checkout entry in [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9); security hardening in [#13](https://github.com/vishalkumar9dec/EasyOrder/issues/13). |
| UI-09 | Guest cart editing | Select `Guest`, use `+ Food`, `+ Instamart`, and quantity controls. | Guest can add manual items and edit quantities. Checkout remains unavailable to guest. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2), local-only state. | Session mutation API and realtime collaboration in [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7). |
| UI-10 | Mobile usability smoke | Open the app in a narrow mobile viewport, go to the demo, switch scenarios and role. | Scenario tabs, cart, warnings, and guest restriction remain usable without blocking the main flow. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Real PWA mobile session route in [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6). |

## Backend/API Tests Available After Issue #4

These tests verify the new initialized-session backend path before the production
PWA session UI exists.

### Start The Backend

In terminal 1:

```bash
make backend-dev
```

The local backend runs on [http://localhost:8000](http://localhost:8000).
Local mode skips WhatsApp signature verification when no app secret is configured, so
these sample payloads can be posted directly with `curl`.

### Sample Payload Files

The sample webhook payloads live in [docs/api-test-data](/Users/vishalkumar/projects/swiggy_builder_prog/docs/api-test-data):

- [whatsapp-tagged-normal.json](/Users/vishalkumar/projects/swiggy_builder_prog/docs/api-test-data/whatsapp-tagged-normal.json): normal tagged prompt.
- [whatsapp-low-budget.json](/Users/vishalkumar/projects/swiggy_builder_prog/docs/api-test-data/whatsapp-low-budget.json): low-budget tagged prompt.
- [whatsapp-vegetarian.json](/Users/vishalkumar/projects/swiggy_builder_prog/docs/api-test-data/whatsapp-vegetarian.json): vegetarian tagged prompt.
- [whatsapp-injection.json](/Users/vishalkumar/projects/swiggy_builder_prog/docs/api-test-data/whatsapp-injection.json): prompt-injection rejection case.
- [whatsapp-untagged.json](/Users/vishalkumar/projects/swiggy_builder_prog/docs/api-test-data/whatsapp-untagged.json): privacy regression case with no `@EasyOrder` mention.

### Copy-Paste API Checks

Run these from the repository root in terminal 2.

| ID | Use case | Command | Expected response |
|---|---|---|---|
| API-01 | Tagged prompt creates initialized session | `curl -s -X POST http://localhost:8000/api/whatsapp/webhook -H 'Content-Type: application/json' --data @docs/api-test-data/whatsapp-tagged-normal.json` | JSON has `"status":"created"` and first session has `"status":"ACTIVE"` plus a `/session/...` guest link. |
| API-02 | Untagged prompt is ignored | `curl -s -X POST http://localhost:8000/api/whatsapp/webhook -H 'Content-Type: application/json' --data @docs/api-test-data/whatsapp-untagged.json` | JSON is `"status":"ignored"` with reason `"no_easyorder_mention"`. |
| API-03 | Injection is blocked before parsing | `curl -i -s -X POST http://localhost:8000/api/whatsapp/webhook -H 'Content-Type: application/json' --data @docs/api-test-data/whatsapp-injection.json` | HTTP status is `400`; body detail is `Tagged message was rejected by input guardrails`. |
| API-04 | Low-budget prompt creates a session | `curl -s -X POST http://localhost:8000/api/whatsapp/webhook -H 'Content-Type: application/json' --data @docs/api-test-data/whatsapp-low-budget.json` | JSON has `"status":"created"` and first session has `"status":"ACTIVE"`. Budget-warning internals are covered by `make backend-test` until the session-read API exists. |
| API-05 | Vegetarian prompt creates a session | `curl -s -X POST http://localhost:8000/api/whatsapp/webhook -H 'Content-Type: application/json' --data @docs/api-test-data/whatsapp-vegetarian.json` | JSON has `"status":"created"` and first session has `"status":"ACTIVE"`. Dietary-warning internals are covered by `make backend-test` until the session-read API exists. |

The current webhook response intentionally returns only session id, guest link, and
session status. It does not return cart items or warnings yet. To inspect cart and
warning internals manually before the session API exists, run this in-process smoke:

```bash
cd src/backend
.venv/bin/python - <<'PY'
import asyncio
from app.models.whatsapp import IncomingMessage
from app.services.mock_agent import MockAgentService

async def main():
    agent = MockAgentService()
    msg = IncomingMessage(
        sender_id="919988776655",
        message_id="wamid.manual",
        message_text="@EasyOrder get biryani and drinks for 4 under 3000",
        phone_number_id="group_ipl_fans_1",
        timestamp="1782489000",
        is_easyorder_tagged=True,
    )
    session = await agent.handle_tagged_message(msg)
    print("status:", session.status)
    print(
        "cart:",
        [
            (
                item.name,
                item.vertical,
                item.quantity,
                item.restaurant_name,
                item.brand_name,
                item.source_label,
            )
            for item in session.cart_items
        ],
    )
    print("warnings:", [warning.code for warning in session.warnings])

asyncio.run(main())
PY
```

Expected output: `ACTIVE`, one Food item with restaurant name `Biryani House`, one
Instamart item with source label `Instamart Mock Store`, and no warnings for the
normal prompt.

### Automated Backend Coverage

The cases that require internal state inspection are covered by automated tests:

| ID | Use case | Test coverage |
|---|---|---|
| API-06 | Low budget creates warning without blocking | `tests/test_agent_service.py` asserts `budget_warning=true` for a low-budget prompt. |
| API-07 | Vegetarian prompt flags non-veg recommendation | `tests/test_agent_service.py` asserts `DIETARY_MISMATCH` warning behavior. |
| API-08 | Instamart timeout degrades gracefully | `tests/test_agent_service.py` asserts `DEGRADED` session with `VERTICAL_TIMEOUT` for Instamart. |
| API-09 | Full worker timeout still creates traceable session | `tests/test_agent_service.py` asserts both verticals are degraded and no cart items are persisted. |
| API-10 | Mock Swiggy scenario coverage | `tests/test_mock_swiggy.py` covers normal search, empty results, substitute lookup, unavailable item, and price-change item. |
| API-11 | Source attribution is preserved and malformed source-less results are skipped | `tests/test_session_domain.py`, `tests/test_agent_service.py`, `tests/test_db_adapter.py`, `tests/test_mock_swiggy.py`, and `tests/test_migrations.py` assert Food restaurant metadata, Instamart source labels, DB persistence, migration constraints, and `SOURCE_ATTRIBUTION_MISSING` warnings. |

## PRD Use Cases Not Fully Testable In The UI Yet

| PRD story | Desired manual test | Why not complete today | Planned issue |
|---|---|---|---|
| 1, 12 | Send WhatsApp messages with and without `@EasyOrder`; verify only tagged messages create sessions. | Backend webhook exists, but the current UI is not yet connected to created sessions. | Closed backend slice [#3](https://github.com/vishalkumar9dec/EasyOrder/issues/3); UI/session handoff continues in [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4), [#5](https://github.com/vishalkumar9dec/EasyOrder/issues/5), and [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6). |
| 2, 3 | Send a natural-language order request and open the generated session link. | Backend agent initialization is now testable in mock mode, but the generated session link does not yet open a production PWA session page backed by persisted session APIs. | [#5](https://github.com/vishalkumar9dec/EasyOrder/issues/5) for WhatsApp link handoff, then [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6) for PWA bootstrap. |
| 4 | Open guest link and customize the real session cart. | Current cart edits are local React state, not API-backed. | [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6) and [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7). |
| 5 | Open the same session in two browser windows and confirm realtime cart updates. | Realtime subscription and cart mutation API are not implemented yet. | [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7). |
| 6 | Persist guest dietary additions and verify host-visible warnings. | Current dietary state is scenario fixture data only. | [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). |
| 7 | Run final stock and price validation against mock Swiggy state. | Current stock/price changes are pre-modeled UI states, not API responses. | [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9). |
| 8, 9, 10 | Host completes mock Swiggy OAuth and sees one checkout step per Food restaurant plus Instamart when needed. | Current links are static mock URLs. OAuth confirmation, restaurant-grouped Food checkout creation, and sequential cart creation are not implemented yet. | [#10](https://github.com/vishalkumar9dec/EasyOrder/issues/10), then real MCP and WhatsApp work in [#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11). |
| 10 | Delivery updates are posted back to WhatsApp group. | Deferred unless delivery-status hooks are available. | Scaffold/provider placeholder in [#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11), broader demo/runbook coverage in [#12](https://github.com/vishalkumar9dec/EasyOrder/issues/12). |
| 11 | Host opts into sports/tournament nudges during setup. | Deferred for MVP; only template-message placeholder is planned. | [#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11). |

## Suggested Regression Pass Before Starting Issue #5

Run these before changing WhatsApp link handoff or PWA bootstrap behavior:

```bash
make backend-test
make frontend-test
make frontend-build
```

Then manually retest `UI-01` through `UI-07` in the playground and `API-01` through
`API-11` at the backend seams. The issue [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4)
agent now produces session/cart states that future PWA work can load in place of the
hard-coded playground fixtures.
