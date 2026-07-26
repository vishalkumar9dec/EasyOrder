# EasyOrder Local Demo Runbook

This runbook verifies the MVP flow from a WhatsApp-style tagged prompt to mock
sequential checkout without live WhatsApp or Swiggy credentials.

## Before You Demo Live

`make backend-dev` and `make frontend-dev` intentionally do **not** override
`SWIGGY_CLIENT_MODE`, `LLM_MODE`, or `WHATSAPP_PROVIDER_MODE` — they run
with whatever is currently in `src/backend/.env`, because that's exactly
what you want when you're deliberately testing a real integration. The
failure mode: if `.env` was last used to test something real (e.g.
`SWIGGY_CLIENT_MODE=mcp` pointed at a mock-swiggy-mcp server that isn't
running right now), a live demo silently gets an empty cart instead of the
happy path — found exactly this way once already.

Before demoing, check `src/backend/.env`:

```bash
grep -E "^SWIGGY_CLIENT_MODE|^LLM_MODE|^WHATSAPP_PROVIDER_MODE" src/backend/.env
```

- For the safe, always-works demo: `SWIGGY_CLIENT_MODE=mock`, `LLM_MODE=mock`.
  (`make demo-smoke` and the `backend-verify-mock` preview config both pin
  these explicitly regardless of `.env`, so they're safe to trust as-is.)
- If you deliberately want to demo `SWIGGY_CLIENT_MODE=mcp`, confirm the
  mock MCP server is actually running first: `make mock-mcp-up` (or check
  `curl http://localhost:9100/mcp` isn't refused).
- If `LLM_MODE=openai`, confirm `OPENAI_API_KEY` is set (the app fails to
  boot without it, so this one can't drift silently — but do budget for
  real API latency/cost during a live demo).
- If `WHATSAPP_PROVIDER_MODE=meta`, you're demoing against real WhatsApp —
  make sure that's intentional and you have a real device/number ready to
  send from, not the `curl` fixture below (which won't have a valid
  signature against a real `WHATSAPP_APP_SECRET`).

When in doubt, run `make demo-smoke` right before you go live — it's
hermetic (ignores `.env` for these three settings) and proves the golden
path works independent of whatever state your `.env` is currently in.

## One-Command Smoke

From the repository root:

```bash
make setup
make demo-smoke
```

Expected output:

- `session_id` starts with `session_`.
- `guest_role` is `guest`.
- `cart_items_after_edit` is `3`.
- `checkout_groups` is `2` for the normal biryani + Instamart fixture.
- `checkout_urls` contains one Food restaurant URL and one Instamart URL.
- `final_status` is `ORDERED`.

## Full Local Stack

```bash
make setup
make db-up
make db-migrate
make backend-dev
make frontend-dev
```

Open [http://localhost:5173](http://localhost:5173).

In another terminal, create a session through the webhook fixture:

```bash
curl -s -X POST http://localhost:8000/api/whatsapp/webhook \
  -H 'Content-Type: application/json' \
  --data @docs/api-test-data/whatsapp-tagged-normal.json
```

Use the returned guest link to open the PWA session. In mock mode the private host
link is captured by `MockWhatsAppSender` in-process, so use automated tests or
`make demo-smoke` when you need to exercise host-only checkout without live
WhatsApp.

## Browser Checklist

- Guest link opens the planning canvas.
- Cart rows show Food restaurant and Instamart source labels.
- Guest can add a manual Instamart item.
- Host view shows checkout groups split by Food restaurant and Instamart.
- Host validation reaches `Stock and prices validated`.
- Host mock cart creation shows one checkout link per group.
- `/orders/live` (after OTP login) shows Scheduled / Ongoing / Historical
  tabs with correct counts.

## Targeted Order + Scheduled Delivery (business chat)

Direct messages to the configured `WHATSAPP_PHONE_NUMBER_ID` (not a group
message — see `docs/mock-swiggy-restaurant-call-flow.md` for the full call
flow and sequence diagram):

1. `Order paneer tikka and chicken 65 from MotiMahal restaurant and if the
   budget exceeds INR 400, let me know before placing the order` — expect a
   reply naming the total, that it exceeds the budget, and asking for
   YES/NO. No order is placed yet.
2. A **separate** follow-up message `yes` — expect "Placed!". This proves
   the real multi-turn confirmation (a distinct later message resolves it,
   not a same-message "...confirm" suffix).
3. `Order Egg Biryani for me from BiryaniByKilo and it should reach by 8PM`
   — expect an immediate "Scheduled" reply. The order is not placed yet;
   the background scheduler (`order_scheduler_poll_seconds`, default 30s)
   places it automatically once `target_placement_at` (the deadline minus
   the restaurant's ETA) arrives. Note the deadline is interpreted as UTC
   of the message's date, not IST — the app has no timezone-awareness
   anywhere today.
4. Open `/orders/live` after logging in — the budget-gated order should
   show under Ongoing (once placed) and the scheduled one under Scheduled.

This is new-enough scope that a fast local check without waiting for the
scheduler's real-time poll is `pytest tests/test_order_scheduler.py -v`,
which drives `OrderScheduler.tick()` directly.

## Cleanup

```bash
make db-down
```
