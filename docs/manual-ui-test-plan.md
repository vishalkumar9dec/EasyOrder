# EasyOrder Manual UI Test Plan

Last verified: 2026-07-06.

This document reflects the current project state from `docs/easyorder-prd.md`,
`docs/implementation-tasks.md`, the local worktree, and live GitHub issue status.

## Current Scope

The current UI includes the local product-validation playground from GitHub issue
[#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2), the issue
[#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6) session bootstrap route,
and the issue [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7)
API-backed cart editing slice. The session route can load backend-created mock
sessions by token, render a mobile-first planning canvas, add/update/delete cart
items through the session API, and keep multiple local clients refreshed through a
polling realtime fallback. The issue [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8)
branch adds budget, dietary, and degraded-state review UI on the real session
route. The issue [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9)
branch adds host-only checkout entry UI and the pre-checkout validation API. The
issue [#10](https://github.com/vishalkumar9dec/EasyOrder/issues/10) branch adds
mock Swiggy OAuth confirmation and sequential cart creation. The issue
[#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11) branch adds the
real Swiggy MCP client boundary and Meta WhatsApp sandbox sender coverage.
The issue [#12](https://github.com/vishalkumar9dec/EasyOrder/issues/12)
branch adds the repeatable local demo smoke, request-id logging, and runbooks.
The issue [#13](https://github.com/vishalkumar9dec/EasyOrder/issues/13)
branch adds the consolidated security smoke and final documentation hardening pass.

The `codex/issue-15-whatsapp-timeline` branch (Task 10.1) adds the
WhatsApp activity timeline: inbound message events and links-sent events are
persisted to a new `session_events` table and surfaced in the PWA session route
as a compact "Activity" strip below the planning canvas.

The next proposed wave (not yet implemented) covers:

- Replacing long visible WhatsApp handoff URLs with CTA/template messaging where
  supported, or short branded links as fallback.
- Adding a dedicated EasyOrder business-chat assistant mode.
- Adding saved lists/wishlists and list-to-cart review.

Current GitHub status:

| Order | Issue | Scope | Status |
|---:|---|---|---|
| 01 | [#1](https://github.com/vishalkumar9dec/EasyOrder/issues/1) | Tasks 0.1-1.1: foundation, local infra, app shell | Closed |
| 02 | [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2) | Product validation slice: local app playground | Closed |
| 03 | [#14](https://github.com/vishalkumar9dec/EasyOrder/issues/14) | Tasks 1.2-2.1: domain, persistence, tokens, RLS | Closed |
| 04 | [#3](https://github.com/vishalkumar9dec/EasyOrder/issues/3) | Tasks 3.1-3.2: mention-only WhatsApp intake | Closed |
| 05 | [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4) | Tasks 2.2, 4.1-4.5: agent initializes consolidated cart | Closed |
| 06 | [#5](https://github.com/vishalkumar9dec/EasyOrder/issues/5) | WhatsApp group/host link handoff | Closed |
| 07 | [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6) | Session bootstrap planning canvas | Closed |
| 08 | [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7) | Cart mutation API and realtime fallback collaboration | Closed |
| 09 | [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8) | Budget, dietary, and degraded-state session UI | Closed |
| 10 | [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9) | Host-only checkout entry UI and pre-checkout validation | Closed |
| 11 | [#10](https://github.com/vishalkumar9dec/EasyOrder/issues/10) | Mock OAuth confirmation and sequential checkout cart creation | Closed |
| 12 | [#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11) | Real Swiggy MCP boundary and Meta sender sandbox coverage | Closed |
| 13 | [#12](https://github.com/vishalkumar9dec/EasyOrder/issues/12) | Local demo, observability, and runbooks | Closed |
| 14 | [#13](https://github.com/vishalkumar9dec/EasyOrder/issues/13) | Security, privacy, and documentation hardening | Implemented in PR branch; manual verification pending |

## Verification I Performed

Commands run locally:

```bash
make test
make frontend-build
src/backend/.venv/bin/python -m ruff check src/backend/app src/backend/tests
python3 .agents/skills/easyorder-daily-status/scripts/daily_status.py --repo-root .
```

Results:

- `make test`: backend tests passed with 65 tests; frontend tests passed with 2 test files and 20 tests.
- `make frontend-build`: production build passed.
- Backend Ruff check passed.
- Local API smoke passed for session bootstrap guest access, invalid-token `401`, and missing-session `404`.
- Local API route coverage passed for session-scoped cart create/update/delete, cross-session rejection, source-attribution validation, and missing cart-item `404`.
- Frontend reducer coverage passed for API cart id mapping and repeated realtime snapshot reconciliation without duplicate rows.
- Frontend adapter coverage passed for budget warning, dietary row warning, and structured signal-title derivation.
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

Issue [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4) now includes a
small browser-visible playground update for source attribution. Cart rows display
a source line under the item name: Food rows show the restaurant name, and
Instamart rows show brand plus source/store context when available.

The current web app is still the local playground with hard-coded scenarios. The
backend/API behavior is also updated: tagged WhatsApp webhook payloads run through
the mock-first agent initialization path and create initialized `ACTIVE` or
`DEGRADED` sessions in the local in-memory mock store. The agent-generated
backend cart preserves source attribution: Food items include restaurant id/name,
and Instamart items include a source label plus brand name when available.

What this means for manual testing:

- Use `UI-01` through `UI-10` to regression-test the current browser playground.
- Use `API-01` through `API-16` below to test the backend agent, WhatsApp handoff,
  and tokenized session bootstrap path.
- Use `UI-11` through `UI-14` below to verify the real session route after creating
  a mock session through the webhook.

## Backend/API Changes From Issue #5

Issue [#5](https://github.com/vishalkumar9dec/EasyOrder/issues/5) adds the
outbound WhatsApp sender boundary. In mock mode, tagged webhook handling captures
two outbound messages: a group message with only the guest planning link, and a
private host message with the host-only link. The webhook response remains
group-safe and does not include the host token. A Meta Cloud API sender is
available behind the same interface for sandbox configuration. In live Meta mode,
the handoff is direct-user only: EasyOrder replies to the inbound sender `wa_id`
with a private host link and a shareable guest link. Proactive template-message
placeholders remain disabled for the MVP.

## UI/API Changes From Issue #6

Issue [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6) adds
`GET /api/session/{session_id}?token=...` and a React `/session/:sessionId` route.
Guest tokens return a redacted planning-canvas payload with guest role, cart,
warnings, degraded verticals, and source-attributed rows. Host tokens return host
role and checkout eligibility without exposing token material. Invalid or
cross-session tokens return `401`; unknown sessions return `404`.

## UI/API Changes From Issue #7

Issue [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7) adds
session-scoped cart mutation endpoints:

- `POST /api/session/{session_id}/cart-items?token=...`
- `PATCH /api/session/{session_id}/cart-items/{cart_item_id}?token=...`
- `DELETE /api/session/{session_id}/cart-items/{cart_item_id}?token=...`

Guest and host tokens can mutate only their own session cart. Cross-session tokens
return `401`, missing cart items return `404`, and invalid payloads return `422`.
Food item creation still requires restaurant id/name; Instamart item creation
still requires a source/store label. The React session page now exposes API-backed
`+ Food`, `+ Instamart`, quantity, and remove controls, and shows a realtime
connection strip. Local collaboration currently uses a polling fallback over the
session API; the Supabase event-channel integration remains a future wiring detail
once browser Supabase credentials/client dependency are introduced.

## UI Changes From Issue #8

Issue [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8) keeps the same
session API contract but makes warning states clearer on the React session page.
The frontend now preserves structured warning objects instead of flattening them
to strings, then derives:

- A budget review strip and highlighted budget panel when `budget_warning=true` or
  the cart total exceeds the budget.
- Dietary review chips on affected cart rows, including vegetarian sessions that
  contain non-veg Food items.
- Structured signal cards for budget, dietary, degraded availability, and source
  review warnings.
- Degraded vertical badges remain visible while Food and Instamart manual add
  controls stay available.

## UI/API Changes From Issue #9

Issue [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9) adds
host-only checkout validation for real sessions:

- `POST /api/session/{session_id}/checkout?token=...` validates only host tokens.
- Guests receive `403` and cannot trigger checkout validation.
- Food checkout previews are grouped by restaurant. Instamart remains a separate
  checkout group.
- Successful validation returns `checkout_ready=true`, planned checkout groups,
  and updates the session status to `CHECKOUT_READY`.
- Mock unavailable item and price-change responses return `409` with structured
  issue details and substitute suggestions when available.
- The React session page shows host-only checkout steps and a `Validate checkout`
  action. Guests see guidance but no validation button.

## UI/API Changes From Issue #10

Issue [#10](https://github.com/vishalkumar9dec/EasyOrder/issues/10) adds mock
Swiggy OAuth confirmation and sequential cart creation:

- `POST /api/session/{session_id}/checkout/confirm?token=...` requires a host
  token and an OAuth code body.
- Mock OAuth code `mock-oauth-code` creates checkout carts; `mock-oauth-fail`
  returns `400`.
- Food carts are created one restaurant at a time, followed by Instamart when
  present.
- Food-only and Instamart-only sessions skip empty verticals cleanly.
- Successful confirmation returns checkout URLs and updates session status to
  `ORDERED`.
- Partial creation failure returns `partial_success=true`, successful checkout
  URLs, failed-step details, and updates session status to `CHECKOUT_PARTIAL`.
- The host session page can create mock Swiggy carts after validation and show
  each checkout link or failed step.

## API Changes From Issue #11

Issue [#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11) adds
production-shaped integration boundaries while keeping local mock mode as the
default:

- `SWIGGY_CLIENT_MODE=mock` remains the local/test default.
- `SWIGGY_CLIENT_MODE=mcp` selects `SwiggyMcpClient` and requires
  `SWIGGY_MCP_SERVER_PATH`.
- `SWIGGY_MCP_SERVER_ENV` accepts a JSON object of environment variables for the
  MCP stdio command.
- Real Swiggy MCP responses are normalized to the same item shape as mock
  responses, including Food restaurant id/name and Instamart brand/source labels.
- MCP tool errors are mapped to application exceptions before they reach route
  handlers.
- `WHATSAPP_PROVIDER_MODE=meta` selects the Meta Cloud API sender; mock remains
  default. The sandbox payload is covered without making live network calls.

Manual sandbox verification requires provider credentials:

```bash
SWIGGY_CLIENT_MODE=mcp
SWIGGY_MCP_SERVER_PATH=/absolute/path/to/swiggy-mcp-server
SWIGGY_MCP_SERVER_ENV={"SWIGGY_ENV":"sandbox"}
WHATSAPP_PROVIDER_MODE=meta
WHATSAPP_ACCESS_TOKEN=<sandbox-token>
WHATSAPP_PHONE_NUMBER_ID=<sandbox-phone-number-id>
```

## Demo And Runbook Changes From Issue #12

Issue [#12](https://github.com/vishalkumar9dec/EasyOrder/issues/12) adds a
repeatable mock-mode demo and operational debugging path:

- `make demo-smoke` runs the complete local flow in-process: WhatsApp fixture,
  guest session bootstrap, guest cart edit, host checkout validation, and mock
  sequential checkout confirmation.
- `scripts/easyorder_demo_smoke.py` prints session id, cart count, checkout group
  count, checkout URLs, and final status.
- Backend responses include `x-request-id`; request logs use the `easyorder.api`
  logger with request id, route, status, latency, and session id when available.
- Local demo steps live in [local-demo.md](/Users/vishalkumar/projects/swiggy_builder_prog/docs/runbooks/local-demo.md).
- Environment setup, SQL inspection snippets, common failures, and release
  checks live in [operations.md](/Users/vishalkumar/projects/swiggy_builder_prog/docs/runbooks/operations.md).

## Security And Documentation Changes From Issue #13

Issue [#13](https://github.com/vishalkumar9dec/EasyOrder/issues/13) adds a
single local security regression smoke that exercises the release-blocking
privacy and authorization paths together:

- `make security-smoke` runs the in-process privacy suite.
- `scripts/easyorder_security_smoke.py` verifies request-id propagation,
  mention-only webhook privacy, prompt-injection rejection, group-safe guest
  links, guest bootstrap redaction, invalid token rejection, cross-session write
  rejection, guest checkout blocking, OAuth failure safety, and host-only
  pre-checkout validation.
- The release checklist now includes the security smoke alongside test, build,
  lint, and demo smoke commands.

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
| UI-01 | Normal group order | Open the app, go to the interactive demo, select `Normal`, keep role as `Host`, click `Validate Checkout`, then click both mock checkout actions. | Prompt mentions biryani, paneer rolls, cold drinks, 6 people, and budget 3000. Cart has Food and Instamart items. Food rows show source lines `Biryani House` and `Roll House`; the Instamart row shows `Thums Up · Instamart Mock Store`. Checkout shows `Ready for mock checkout`. Food and Instamart mock checkout actions are visible and clicking them keeps you on the EasyOrder playground. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2), source display from issue [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4). | Persisted session loading in [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6), local E2E demo in [#12](https://github.com/vishalkumar9dec/EasyOrder/issues/12). |
| UI-02 | Over-budget cart | Select `Budget`, click `Validate Checkout`. Try reducing item quantities with the quantity controls. | Total is above budget at first, budget section says over budget, warnings mention the overage, and checkout remains allowed with `Budget warning only`. Reducing quantities updates the total and can recover the budget state. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Backend output guardrails in [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4); real warning UI in [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). |
| UI-03 | Dietary mismatch | Select `Dietary`, choose `Veg` in `Food preference`, click `Validate Checkout`, then switch to `Non-veg` and validate again. | With `Veg`, a non-veg item appears, warnings include vegetarian mismatch, and checkout shows `Dietary review needed`. With `Non-veg`, the dietary warning clears and checkout changes to `Ready for mock checkout`. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Backend dietary warning persistence in [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4); actionable PWA warning UI in [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). |
| UI-04 | Degraded Food availability | Select `Food down`, add a Food item manually, then click `Validate Checkout`. | Food degraded badge appears. Existing cart contains Instamart items. Manual Food addition appears in the cart. Checkout shows `Partial mock checkout`. The Instamart mock checkout action stays inside the playground when clicked. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Worker degradation from the agent in [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4); manual degraded-state UX in [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). |
| UI-05 | Degraded Instamart availability | Select `IM down`, add an Instamart item manually, then click `Validate Checkout`. | Instamart degraded badge appears. Existing cart contains Food items. Manual Instamart addition appears. Checkout shows `Food checkout only`. The Food mock checkout action stays inside the playground when clicked. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Worker degradation from the agent in [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4); real UI states in [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). |
| UI-06 | Stock change at validation | Select `Stock`, inspect the affected item, click `Validate Checkout`. | The item has an unavailable tag, substitute copy mentions `Butterscotch ice cream tub`, and checkout is `Blocked` with `Unavailable item`. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Real pre-checkout validation API in [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9); sequential checkout flow in [#10](https://github.com/vishalkumar9dec/EasyOrder/issues/10). |
| UI-07 | Price change at validation | Select `Price`, inspect the affected item, click `Validate Checkout`. | The item has a price-changed tag, warning mentions price change before payment, and checkout is `Blocked` with `Price changed`. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Real pre-checkout validation API in [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9). |
| UI-08 | Host-only checkout affordance | In any scenario, select `Host`, then select `Guest`. | Host sees `Validate Checkout`. Guest does not see the button and sees `Guests can edit the cart. Only the host can validate and checkout.` | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2), but role is local UI state only. | Backend-derived host/guest role in [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6); host-only checkout entry in [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9); security hardening in [#13](https://github.com/vishalkumar9dec/EasyOrder/issues/13). |
| UI-09 | Guest cart editing | Select `Guest`, use `+ Food`, `+ Instamart`, and quantity controls. | Guest can add manual items and edit quantities. Manual Food rows show `Manual restaurant`; manual Instamart rows show `Manual brand · Manual Instamart source`. Checkout remains unavailable to guest. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2), source display from issue [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4), local-only state. | Session mutation API and realtime collaboration in [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7). |
| UI-10 | Mobile usability smoke | Open the app in a narrow mobile viewport, go to the demo, switch scenarios and role. | Scenario tabs, cart, warnings, and guest restriction remain usable without blocking the main flow. | Current playground, issue [#2](https://github.com/vishalkumar9dec/EasyOrder/issues/2). | Real PWA mobile session route in [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6). |
| UI-11 | Guest opens session link | Start backend and frontend, create a session with `API-01`, copy the returned guest link, and open it in a mobile viewport. | The page shows `Planning canvas`, role `Guest`, source-attributed cart rows such as `Biryani House` and `Thums Up · Instamart Mock Store`, a realtime connection strip, and the guest checkout note. It must not show any `host_` token text. | Issues [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6) and [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7). | Warning/dietary UI in [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). |
| UI-12 | Host opens private session link | Use the host link from the mock sender or backend tests, then open `/session/<session_id>?token=<host_token>`. | The page shows role `Host`, cart rows with source attribution, and host checkout eligibility copy. It must not display raw token or token hash values. | Issue [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6). | Checkout validation in [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9). |
| UI-13 | Unauthorized session link | Open `/session/<valid_session_id>` without a token or with `?token=guest_wrong`. | The page shows `Link not authorized` and does not render cart data. | Issue [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6). | Security hardening in [#13](https://github.com/vishalkumar9dec/EasyOrder/issues/13). |
| UI-14 | Missing session link | Open `/session/session_missing?token=guest_any`. | The page shows `Session not found` and does not render cart data. | Issue [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6). | E2E demo and runbook coverage in [#12](https://github.com/vishalkumar9dec/EasyOrder/issues/12). |
| UI-15 | Guest mutates real session cart | Open a valid guest session link. Click `+ Food`, click `+ Instamart`, use `+` and `-` on the new rows, then click `Remove`. | New Food rows show `Manual restaurant`; new Instamart rows show `Manual brand · Manual Instamart source`. Totals and item count update after each API-backed action. Reducing quantity to `0` removes the row. Checkout remains unavailable to guest. | Issue [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7). | Dietary preference editing and warnings in [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). |
| UI-16 | Two-window cart refresh | Open the same guest session link in two browser windows. Add or remove an item in one window, then wait for the realtime strip to report `connected` in the other window. | The second window reflects the changed cart within the polling interval without duplicate rows. Both windows keep source-attributed cart rows. | Issue [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7) polling realtime fallback. | Supabase event-channel wiring can replace polling when browser credentials/client dependency are introduced. |
| UI-17 | Budget and dietary review session | Start backend and frontend, create a session with `API-04` or `API-05`, copy the returned guest link, and open it in a mobile viewport. | If the session is over budget, the page shows a budget review strip, highlighted budget panel, over-budget amount, and `Budget review` signal. If the session is vegetarian with a non-veg Food item, the affected cart row shows `Dietary review` while preserving its restaurant name. Editing controls remain available. | Issue [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). | Checkout validation in [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9). |
| UI-18 | Degraded availability review session | Start backend and frontend, create or load a session whose `degraded_verticals` includes Food or Instamart. Open the guest link in a mobile viewport. | The page shows a degraded alert strip, structured degraded availability signal, degraded vertical badge, and still exposes `+ Food` and `+ Instamart` controls for manual recovery. Existing cart rows keep source labels. | Issue [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). | Real checkout validation and recovery in [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9). |
| UI-19 | Host validates real session checkout | Start backend and frontend, create a session with `API-01`, open the private host link from the mock sender or backend test helper, then click `Validate checkout`. | Host sees grouped checkout steps before clicking. A normal biryani session shows one Food restaurant step and one Instamart step. After validation, the panel says `Stock and prices validated` and the session remains token-redacted. | Issue [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9). | OAuth confirmation and sequential cart creation in [#10](https://github.com/vishalkumar9dec/EasyOrder/issues/10). |
| UI-20 | Guest cannot validate real session checkout | Open the same session with the guest link. | The checkout panel shows guest guidance only. There is no `Validate checkout` button. Cart editing controls remain available. | Issue [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9). | Checkout security hardening in [#13](https://github.com/vishalkumar9dec/EasyOrder/issues/13). |
| UI-21 | Multi-restaurant checkout preview | Open a host session, add a manual Food item with a different restaurant through the session UI or `API-18`, then refresh and inspect checkout. | Checkout preview shows one step per Food restaurant, followed by Instamart when present. For two restaurants plus Instamart, the host sees three planned Swiggy orders before validation. | Issue [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9). | Sequential checkout URLs in [#10](https://github.com/vishalkumar9dec/EasyOrder/issues/10). |
| UI-22 | Host creates mock Swiggy checkout carts | Open a real host session, click `Validate checkout`, then click `Create Swiggy carts`. | The panel changes to `Swiggy carts created`, shows one checkout link per planned group, and the links include the relevant Food restaurant id or Instamart step. | Issue [#10](https://github.com/vishalkumar9dec/EasyOrder/issues/10). | Real Swiggy MCP integration in [#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11). |
| UI-23 | Partial checkout creation is visible | Configure the mock client or run the automated `API-30` path with Instamart cart failure. Reopen the host session after confirmation. | Successful Food checkout links remain visible, failed Instamart step shows a recovery warning, and the session status is `CHECKOUT_PARTIAL`. | Issue [#10](https://github.com/vishalkumar9dec/EasyOrder/issues/10). | Partial recovery hardening in [#13](https://github.com/vishalkumar9dec/EasyOrder/issues/13). |
| UI-24 | WhatsApp message appears in session timeline | Proposed: send a tagged WhatsApp message, open the generated session link, and inspect the session header/activity area. | The initiating message appears as a redacted timeline event with timestamp and session-created activity. Host token material is not visible. | Proposed Task 10.1. | Build message-event persistence and PWA timeline. |
| UI-25 | WhatsApp handoff CTA/short-link polish | Proposed: send a tagged WhatsApp message in Meta mode with CTA/template support configured. | WhatsApp shows a concise CTA such as `Review order` or a short branded fallback link. It does not show two long raw tokenized URLs as the primary message body. | Proposed Task 10.2. | Build capability-aware WhatsApp sender. |
| UI-26 | Dedicated business chat discovery | Proposed: in the EasyOrder business chat, send `nearest best chole bhature`. | EasyOrder returns source-attributed discovery results or a graceful unsupported response in mock/live-limited mode. | Proposed Task 10.3. | Build dedicated-chat intent router. |
| UI-27 | Saved list management | Proposed: send `add vim bar to monthly`, then `show monthly list`. | EasyOrder confirms the item was added and shows the named list scoped to the sender identity. | Proposed Task 10.4. | Build saved-list storage and command grammar. |
| UI-28 | List-to-cart review | Proposed: send `add today's list to cart`, then open the generated review link. | PWA shows source-attributed items, substitutions/offers, and requires review before checkout. | Proposed Task 10.5. | Build list-to-session conversion and review gating. |

## Backend/API Tests Available After Issue #4

These tests verify the new initialized-session backend path before the production
PWA session UI exists.

The completed automated and smoke-test report for the issue #4 source-attribution
follow-up is available at [issue-4-source-attribution.md](/Users/vishalkumar/projects/swiggy_builder_prog/docs/test-reports/issue-4-source-attribution.md).

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
| API-01 | Tagged prompt creates initialized session | `curl -s -X POST http://localhost:8000/api/whatsapp/webhook -H 'Content-Type: application/json' --data @docs/api-test-data/whatsapp-tagged-normal.json` | JSON has `"status":"created"` and first session has `"status":"ACTIVE"` plus an absolute guest link containing a `guest_` token. The response must not include a `host_` token. |
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
| API-12 | Group link handoff excludes host token | `tests/test_whatsapp_webhook.py::test_tagged_message_creates_mock_session` | The mock WhatsApp sender captures a group message to `group_ipl_fans_1` with the guest planning link only; the group text does not contain `host_`. |
| API-13 | Private host link handoff includes host token | `tests/test_whatsapp_webhook.py::test_tagged_message_creates_mock_session` | The mock WhatsApp sender captures a private message to the sender WhatsApp id with the host link containing the one-time `host_` token. Template-message placeholders remain disabled until proactive updates are implemented. |
| API-13a | Meta mode uses direct sender handoff | `tests/test_whatsapp_webhook.py::test_meta_mode_sends_direct_handoff_to_inbound_sender` | In Meta mode, EasyOrder sends one private handoff to the inbound sender `wa_id`, not to the business `phone_number_id`/mock group id. The webhook response still excludes `host_`. |
| API-14 | Guest token bootstraps session state | `tests/test_session_api.py::test_guest_token_bootstraps_redacted_session_state` | Guest token returns role `guest`, cart, warnings, degraded state, source attribution, and no host token/hash/phone fields. |
| API-15 | Host token bootstraps host state | `tests/test_session_api.py::test_host_token_bootstraps_host_role_without_exposing_token_material` | Host token returns role `host` and checkout eligibility while keeping raw token and host-token hash out of the response. |
| API-16 | Invalid, cross-session, and missing links fail safely | `tests/test_session_api.py` | Invalid or cross-session token returns `401`; missing session returns `404`. |
| API-17 | Session cart mutation CRUD | `tests/test_session_api.py::test_guest_can_create_update_and_delete_cart_item_for_session` | Guest token can add an Instamart item with source label, update quantity/price, and delete it from the same session. |
| API-18 | Cross-session mutation is rejected | `tests/test_session_api.py::test_cart_mutation_rejects_cross_session_token` | A token from another session receives `401` when attempting to mutate this session's cart. |
| API-19 | Mutation payload validation | `tests/test_session_api.py::test_cart_mutation_validates_source_attribution_and_missing_items` | Food item creation without restaurant id/name returns `422`; missing cart item update returns `404`. |
| API-20 | Warning UI adapter derivation | `src/frontend/src/sessionBootstrap.test.ts` | Frontend preserves structured warnings and derives budget overage, dietary item flags, and human-readable signal titles. |
| API-21 | Host checkout validation success | `tests/test_session_api.py::test_host_can_validate_checkout_with_grouped_steps` | Host token can call `POST /api/session/{session_id}/checkout`; response has `checkout_ready=true`, one Food restaurant group, one Instamart group, and the session status becomes `CHECKOUT_READY`. |
| API-22 | Guest checkout validation is forbidden | `tests/test_session_api.py::test_guest_cannot_validate_checkout` | Guest token receives `403` from checkout validation even though guests can still edit cart items. |
| API-23 | Unavailable item validation conflict | `tests/test_session_api.py::test_checkout_validation_returns_unavailable_item_conflict` | Mock unavailable item returns `409` with `ITEM_UNAVAILABLE`, source label, and substitute suggestions. |
| API-24 | Price-change validation conflict | `tests/test_session_api.py::test_checkout_validation_returns_price_change_conflict` | Mock price change returns `409` with `PRICE_CHANGED`, affected item id, source label, and new price. |
| API-25 | Multi-restaurant checkout grouping | `tests/test_session_api.py::test_checkout_validation_groups_multiple_food_restaurants` and `src/frontend/src/sessionBootstrap.test.ts` | Food items from two restaurants produce two Food checkout groups; Instamart remains a separate group after Food. |
| API-26 | Host checkout confirmation success | `tests/test_session_api.py::test_host_can_confirm_checkout_with_sequential_urls` | Host token and mock OAuth code create checkout URLs for each planned group and update session status to `ORDERED`. |
| API-27 | Guest checkout confirmation is forbidden | `tests/test_session_api.py::test_guest_cannot_confirm_checkout` | Guest token receives `403` from checkout confirmation. |
| API-28 | Multi-restaurant confirmation split | `tests/test_session_api.py::test_checkout_confirm_groups_multiple_food_restaurants_sequentially` | Two Food restaurants create two Food checkout URLs, followed by the Instamart checkout URL. |
| API-29 | Empty verticals are skipped | `tests/test_session_api.py::test_checkout_confirm_skips_empty_verticals` | Food-only sessions create Food checkout steps only; Instamart-only sessions create Instamart checkout steps only. |
| API-30 | Partial checkout failure recovery | `tests/test_session_api.py::test_checkout_confirm_reports_partial_failure` | Mock Instamart cart creation failure returns `partial_success=true`, preserves successful Food URL, and updates session status to `CHECKOUT_PARTIAL`. |
| API-31 | OAuth exchange failure | `tests/test_session_api.py::test_checkout_confirm_reports_oauth_failure` | Mock OAuth failure returns `400` without creating checkout carts. |
| API-32 | Swiggy MCP response normalization | `tests/test_swiggy_mcp.py` | Real-client fixtures normalize Food restaurant id/name, Instamart brand/source labels, price, dietary tag, OAuth token, and checkout URL into the mock-compatible shape. |
| API-33 | Swiggy MCP error mapping | `tests/test_swiggy_mcp.py::test_swiggy_mcp_client_maps_tool_errors` | MCP tool error payloads raise application exceptions instead of leaking raw tool responses. |
| API-34 | Swiggy client mode selection | `tests/test_swiggy_mcp.py::test_swiggy_client_factory_keeps_mock_default_and_validates_mcp_config` | Mock mode remains default; MCP mode requires `SWIGGY_MCP_SERVER_PATH`. |
| API-35 | Meta WhatsApp sandbox sender payload | `tests/test_whatsapp_sender.py` | Meta sender builds the Graph API text-message payload, maps HTTP errors, and is selected by `WHATSAPP_PROVIDER_MODE=meta`. |
| API-36 | Local demo smoke | `make demo-smoke` and `tests/test_demo_smoke.py` | Mock-mode flow creates a session from the WhatsApp fixture, opens guest state, edits cart, validates checkout, creates checkout URLs, and ends as `ORDERED`. |
| API-37 | Request id observability | `tests/test_health.py::test_request_logging_middleware_sets_request_id_header` | Backend preserves incoming `x-request-id` and returns it on the response for log correlation. |
| API-38 | Runbook coverage | `docs/runbooks/local-demo.md` and `docs/runbooks/operations.md` | Runbooks cover local setup, demo command, session SQL inspection, common failures, and release validation checklist. |
| API-39 | Security smoke | `make security-smoke` and `tests/test_security_smoke.py` | Consolidated release-blocking suite passes for untagged privacy, prompt-injection blocking, token redaction, invalid-token reads, cross-session writes, guest checkout attempts, failed host OAuth, and host-only validation. |

## PRD Use Cases Not Fully Testable In The UI Yet

| PRD story | Desired manual test | Why not complete today | Planned issue |
|---|---|---|---|
| 1, 12 | Send WhatsApp messages with and without `@EasyOrder`; verify only tagged messages create sessions. | Backend webhook, mock outbound handoff, and Meta-mode direct sender routing are testable locally; live Meta sandbox sending still needs configured provider credentials and a claimed test number. | Closed backend slice [#3](https://github.com/vishalkumar9dec/EasyOrder/issues/3); handoff in [#5](https://github.com/vishalkumar9dec/EasyOrder/issues/5); PWA bootstrap continues in [#6](https://github.com/vishalkumar9dec/EasyOrder/issues/6). |
| 2, 3 | Send a natural-language order request and open the generated session link. | Testable in local mock mode through webhook fixtures and the PWA session route. Live WhatsApp sandbox needs configured provider credentials and should be tested as a direct conversation with the EasyOrder business/test number. | Backend/PWA slices through [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7); live integration in [#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11). |
| 4 | Open guest link and customize the real session cart. | Testable locally with API-backed add/update/delete controls. Rich preference-specific editing is still pending. | Base cart editing in [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7); dietary/warning controls in [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). |
| 5 | Open the same session in two browser windows and confirm realtime cart updates. | Testable with the local polling fallback. Native Supabase browser event-channel wiring is pending credentials/client setup. | [#7](https://github.com/vishalkumar9dec/EasyOrder/issues/7) fallback; future Supabase wiring when configured. |
| 6 | Persist guest dietary additions and verify host-visible warnings. | Current dietary state is scenario fixture data only. | [#8](https://github.com/vishalkumar9dec/EasyOrder/issues/8). |
| 7 | Run final stock and price validation against mock Swiggy state. | Current stock/price changes are pre-modeled UI states, not API responses. | [#9](https://github.com/vishalkumar9dec/EasyOrder/issues/9). |
| 8, 9, 10 | Host completes mock Swiggy OAuth and sees one checkout step per Food restaurant plus Instamart when needed. | Testable locally with mock OAuth and mock checkout URLs. Real Swiggy OAuth/MCP credentials and live cart creation remain pending. | Mock path in [#10](https://github.com/vishalkumar9dec/EasyOrder/issues/10), then real MCP and WhatsApp work in [#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11). |
| 10 | Delivery updates are sent privately to the host. | Deferred unless delivery-status hooks are available. | Scaffold/provider placeholder in [#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11), broader demo/runbook coverage in [#12](https://github.com/vishalkumar9dec/EasyOrder/issues/12). |
| 11 | Host opts into sports/tournament nudges during setup. | Deferred for MVP; only template-message placeholder is planned. | [#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11). |

## Suggested Regression Pass Before Checkout Or Integration Changes

Run these before changing warning, dietary, or checkout-readiness behavior:

```bash
make backend-test
make frontend-test
make frontend-build
make security-smoke
```

Then manually retest `UI-01` through `UI-07` in the playground and `API-01` through
`API-13a` plus `API-39` at the backend seams. The issue [#4](https://github.com/vishalkumar9dec/EasyOrder/issues/4)
agent now produces session/cart states, and issue [#5](https://github.com/vishalkumar9dec/EasyOrder/issues/5)
keeps mock guest/host channels for privacy tests while Meta mode uses direct-user handoff.

---

## Task 10.1 — WhatsApp Message Timeline Manual Verification

Branch: `codex/issue-15-whatsapp-timeline`

### MT-10.1-A: Timeline appears after webhook creates a session

**Steps:**

1. Start the backend: `make backend-dev` (or `APP_ENV=local uvicorn app.main:app --reload`).
2. Start the frontend: `make frontend-dev`.
3. Start public tunnels for both services. Use the URL printed by localtunnel:

```bash
npx -y localtunnel --port 8000 --subdomain easyorder-api-dev
npx -y localtunnel --port 5173 --subdomain easyorder-web-dev
```

4. Set `PUBLIC_APP_BASE_URL` in `src/backend/.env` to the frontend tunnel URL
   printed by localtunnel, then restart or reload the backend:

```bash
PUBLIC_APP_BASE_URL=https://<frontend-tunnel>.loca.lt
```

5. Verify the frontend tunnel serves the PWA and proxies API calls to the backend:

```bash
curl -i https://<frontend-tunnel>.loca.lt/
curl -i "https://<frontend-tunnel>.loca.lt/api/session/not-a-real-session?token=guest_test"
```

Expected preflight:

- The first command returns `200 OK` with the Vite HTML shell.
- The second command returns the backend JSON `{"detail":"Session not found"}`.
- It must not return `403 Blocked request...allowedHosts`, `408`, or `503`.

6. For local mock verification, POST a tagged WhatsApp webhook using the fixture:

```bash
curl -s -X POST http://localhost:8000/api/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d @docs/api-test-data/whatsapp-tagged-normal.json | jq .
```

7. For live Meta verification, send this from the registered sandbox handset:

```text
@EasyOrder get biryani for 4 under 2000
```

8. Open the guest or private host link received in WhatsApp.

**Expected:**

- The PWA session canvas loads.
- Below the planning canvas there is an **Activity** strip with at least two events:
  - `WhatsApp message received` — shows the original tagged message text and the sender wa_id.
  - `Session links sent` — shows a green dot.
- No host token or hash appears anywhere on the page.
- Live links use the frontend tunnel URL from `PUBLIC_APP_BASE_URL`, not a stale
  or disconnected tunnel.

---

### MT-10.1-B: Guest and host both see the Activity strip

**Steps:**

1. After step 8 above, open the **guest link** in one browser tab and the **host link** in another.

**Expected:**

- Both tabs show the Activity strip with the same events.
- Guest view does not expose any additional fields beyond what the host sees.

---

### MT-10.1-C: Empty timeline — no crash when no events

**Steps:**

1. Manually create a session via the session API without sending a webhook.
2. Open the session URL.

**Expected:**

- The planning canvas renders normally.
- The Activity strip is **not rendered** (the component is hidden when `timeline.length === 0`).

---

### MT-10.1-D: Timeline redaction — no token material in browser dev tools

**Steps:**

1. Open the session with a host token.
2. Open browser DevTools → Network → find the `GET /api/session/{id}?token=...` request.
3. Inspect the JSON response body.

**Expected:**

- `timeline` array is present.
- Each event object has: `event_type`, `message_text` (inbound only), `sender_wa_id`, `created_at`, `mode`.
- **No field contains** `host_token`, `host_token_hash`, or any bearer credential.

---

## Task 10.2 — CTA And Short-Link Handoff Manual Verification

Last verified: 2026-07-11 (mock mode, automated + local API drive).

Behavior change: WhatsApp handoff messages no longer contain raw tokenized
session URLs. Copy carries opaque short links (`…/api/r/{code}`); Meta mode
sends an interactive CTA message (button `Review order`) with the guest short
link in the body, falling back to concise text if Graph rejects the payload.
See [whatsapp-handoff-templates.md](runbooks/whatsapp-handoff-templates.md).

### MT-10.2-A: Handset receives CTA handoff, not raw URLs (meta mode)

**Steps:**

1. Ensure the backend runs with `WHATSAPP_PROVIDER_MODE=meta` and tunnels are up.
2. Send `@EasyOrder get biryani for 4 under 2000` from the handset.
3. Inspect the reply in WhatsApp.

**Expected:**

- **Two replies**: one with a **Review order** button (host view) and one with
  a **Share with group** button (guest view). On fallback, one short text
  message with two `…/api/r/…` links.
- **No visible URL in either message body** — buttons only.

### MT-10.2-B: Short links open the correct views

**Steps:**

1. Tap the **Review order** button.
2. Separately tap **Share with group** in another browser.

**Expected:**

- The button/host link lands on the planning canvas with role **Host**
  (checkout controls visible).
- The guest short link lands on the same session with role **Guest**
  (no checkout button).
- The browser address bar ends up on the tokenized `/session/{id}?token=…`
  URL after the redirect — tokens exist only after the click, never in chat.

### MT-10.2-C: Unknown or expired short code fails closed

**Steps:**

1. Open `{PUBLIC_APP_BASE_URL}/api/r/doesnotexist` in a browser.
2. Restart the backend, then re-open a short link from before the restart.

**Expected:**

- Both return `404` with `{"detail": "Unknown or expired link"}` — codes are
  process-scoped, matching in-memory session lifetime.

### MT-10.2-D: Webhook response exposes short guest link only

**Steps:**

1. POST a signed tagged fixture (see `scripts/replay_whatsapp_webhook.py`).
2. Inspect the JSON response.

**Expected:**

- `sessions[0].guest_short_link` is present and contains no `token=`.
- `sessions[0].guest_link` (tokenized, host's own response) is unchanged.
- No `host_` material anywhere in the response.

### MT-10.2-E: Timeline is a verifiable record of WhatsApp activity

Every WhatsApp interaction must appear in the PWA Activity timeline with a
timestamp, so UI state can be checked against what actually happened in chat.

**Steps:**

1. Send `@EasyOrder get biryani for 4 under 2000` from the handset.
2. Note the WhatsApp message times (inbound send, reply arrival).
3. Open the session (Review order button) and scroll to **Activity**.

**Expected:**

- Events in order, each with a time matching the WhatsApp chat within ~a minute:
  1. *WhatsApp message received* — your exact (redacted) message text
  2. *Session created*
  3. *Session links created*
  4. *Links delivered on WhatsApp* (solid green dot) — present **only if** the
     reply actually arrived on the handset
- If the reply never arrived, the timeline instead shows
  *WhatsApp delivery failed* (red dot) — a delivered reply with a "failed"
  event, or a missing reply with a "delivered" event, is a real bug.


---

## Task 10.3 — Dedicated Business-Chat Intent Router Manual Verification

Behavior: untagged messages sent **directly to the EasyOrder business number**
are now routed by intent (no `@EasyOrder` needed). Untagged group messages
remain ignored. Toggle with `WHATSAPP_BUSINESS_CHAT_ENABLED`.

### MT-10.3-A: Business chat answers without the tag

**Steps:** From the handset, send each of these directly to the EasyOrder
number: `get started`, `nearest best chole bhature`, `what was my last order?`

**Expected:**

- `get started` → onboarding reply explaining how to order and the
  `@EasyOrder` group flow.
- `nearest best chole bhature` → discovery "coming soon" reply.
- `what was my last order?` → order-history "coming soon" reply.
- No sessions are created for any of the three (no new links arrive).

### MT-10.3-B: Direct order request creates a session without the tag

**Steps:** Send `get biryani for 4 under 2000` (no `@EasyOrder`) to the
business number.

**Expected:** Same handoff experience as the tagged flow — Review order +
Share with group buttons, session opens with the Activity timeline showing
the message and delivery events.

### MT-10.3-C: Mention flow and group privacy unchanged

**Steps:** Send `@EasyOrder get biryani for 4 under 2000`; then post an
untagged message in a (mock) group fixture via
`scripts/replay_whatsapp_webhook.py --fixture docs/api-test-data/whatsapp-untagged.json`.

**Expected:** Tagged message still creates a session. The untagged group
fixture still returns `{"status": "ignored"}` — passive listening stays off.

---

## Task 10.7 — Durable Postgres Persistence Manual Verification

### MT-10.7-A: Sessions and links survive a backend restart

**Steps:**

1. `make db-up && make db-migrate`
2. Start the backend with `PERSISTENCE_MODE=postgres` in `src/backend/.env`.
3. Send `@EasyOrder get biryani for 4 under 2000` (or replay a fixture) and
   open the session; note the Activity timeline.
4. Stop the backend entirely, start it again.
5. Reload the same session link and click the short link from WhatsApp.

**Expected:**

- The session loads with the same cart and full timeline after the restart.
- The short link still 307-redirects to the session.
- Re-delivering the same webhook (Meta retry) returns `{"status":"duplicate"}`
  even though the backend restarted — the dedup ledger is durable.
- `curl localhost:8000/readyz` shows `"database": "postgres_ok"`.

### MT-10.7-B: Memory mode unchanged

**Steps:** Remove/unset `PERSISTENCE_MODE` (or set `memory`), restart, create a
session, restart again, open the old link.

**Expected:** Old links 404/unauthorized after restart (process-local stores),
exactly as before this task; `readyz` shows `"database": "memory"`.
