# EasyOrder Local Demo Runbook

This runbook verifies the MVP flow from a WhatsApp-style tagged prompt to mock
sequential checkout without live WhatsApp or Swiggy credentials.

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

## Cleanup

```bash
make db-down
```
