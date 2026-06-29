# EasyOrder Manual UI Test Plan

Last verified: 2026-06-29.

This document reflects the current project state from `docs/easyorder-prd.md`,
`docs/implementation-tasks.md`, the local worktree, and live GitHub issue status.

## Current Scope

The current UI is the local product-validation playground from GitHub issue
[#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). It is not yet the
production PWA session route backed by persisted sessions, realtime cart updates, or
Swiggy checkout APIs.

Current GitHub status:

| Order | Issue | Scope | Status |
|---:|---|---|---|
| 01 | [#1](https://github.com/vishalkumar9dec/EasyOrder/issues/1) | Tasks 0.1-1.1: foundation, local infra, app shell | Closed |
| 02 | [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2) | Product validation slice: local app playground | Closed |
| 03 | [#14](https://github.com/vishalkumar9dec/EasyOrder/issues/14) | Tasks 1.2-2.1: domain, persistence, tokens, RLS | Closed |
| 04 | [#3](https://github.com/vishalkumar9dec/EasyOrder/issues/3) | Tasks 3.1-3.2: mention-only WhatsApp intake | Closed |
| 05 | [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4) | Tasks 2.2, 4.1-4.5: agent initializes consolidated cart | Open, ready next |
| 06-14 | [#5](https://github.com/vishalkumar9dec/EasyOrder/issues/5)-[#13](https://github.com/vishalkumar9dec/EasyOrder/issues/13) | WhatsApp links, session PWA, realtime, warnings, checkout, integrations, E2E, hardening | Open, blocked |

## Verification I Performed

Commands run locally:

```bash
make test
make frontend-build
```

Results:

- `make test`: backend tests passed with 23 tests; frontend tests passed with 1 test file and 11 tests.
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

## PRD Use Cases Not Fully Testable In The UI Yet

| PRD story | Desired manual test | Why not complete today | Planned issue |
|---|---|---|---|
| 1, 12 | Send WhatsApp messages with and without `@EasyOrder`; verify only tagged messages create sessions. | Backend webhook exists, but the current UI is not yet connected to created sessions. | Closed backend slice [#3](https://github.com/vishalkumar9dec/EasyOrder/issues/3); UI/session handoff continues in [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4), [#5](https://github.com/vishalkumar9dec/EasyOrder/issues/5), and [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6). |
| 2, 3 | Send a natural-language order request and open the generated session link. | Agent graph and cart persistence from prompt are next, not implemented in the UI flow yet. | [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4). |
| 4 | Open guest link and customize the real session cart. | Current cart edits are local React state, not API-backed. | [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6) and [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7). |
| 5 | Open the same session in two browser windows and confirm realtime cart updates. | Realtime subscription and cart mutation API are not implemented yet. | [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7). |
| 6 | Persist guest dietary additions and verify host-visible warnings. | Current dietary state is scenario fixture data only. | [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). |
| 7 | Run final stock and price validation against mock Swiggy state. | Current stock/price changes are pre-modeled UI states, not API responses. | [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9). |
| 8, 9 | Host completes mock Swiggy OAuth and sees separate Food and Instamart checkout URLs. | Current links are static mock URLs. OAuth confirmation and sequential cart creation are not implemented yet. | [#10](https://github.com/vishalkumar9dec/EasyOrder/issues/10), then real MCP and WhatsApp work in [#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11). |
| 10 | Delivery updates are posted back to WhatsApp group. | Deferred unless delivery-status hooks are available. | Scaffold/provider placeholder in [#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11), broader demo/runbook coverage in [#12](https://github.com/vishalkumar9dec/EasyOrder/issues/12). |
| 11 | Host opts into sports/tournament nudges during setup. | Deferred for MVP; only template-message placeholder is planned. | [#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11). |

## Suggested Regression Pass Before Starting Issue #4

Run these before changing the agent/cart initialization layer:

```bash
make frontend-test
make frontend-build
```

Then manually retest `UI-01` through `UI-07` in the playground. These scenarios are the
current product contract for the next issue: the agent in [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4)
should eventually produce session/cart states that can replace the hard-coded playground
fixtures without losing the same visible user outcomes.
