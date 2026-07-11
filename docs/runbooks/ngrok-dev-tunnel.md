# ngrok Dev Tunnel Setup (Permanent Blank-Page Fix)

## Why

loca.lt free tunnels repeatedly broke local WhatsApp testing:

- **Zombie leases**: after a tunnel client restart (or a vite config edit,
  which restarts vite's HTTP server in-process), loca.lt kept the old agent
  registered and answered `408 Request Timeout` with an **empty body** —
  which Safari renders as a blank white page.
- **Random subdomain fallback**: while a zombie lease held the subdomain,
  restarts got random URLs (`rude-otter-94.loca.lt`), breaking
  `PUBLIC_APP_BASE_URL` and every link already sent to WhatsApp.
- Transient `502/503` while leases settled.

ngrok's free plan includes **one static domain** that never changes, so the
whole stack — PWA links, API, Meta webhook — rides one stable hostname:

```text
Meta webhook ─┐
Handset PWA ──┼─→ https://<yours>.ngrok-free.app ─→ vite :5173 ─→ /api proxy ─→ backend :8000
Guest links ──┘
```

## One-Time Setup (~10 minutes)

1. Sign up free at <https://dashboard.ngrok.com/signup>.
2. In the dashboard, open **Universal Gateway → Domains** and claim your free
   static domain, e.g. `easyorder-dev.ngrok-free.app`. Note it down.
3. Install and authenticate the agent:

   ```bash
   brew install ngrok
   ngrok config add-authtoken <token-from-dashboard>
   ```

4. Point the backend's public base URL at the static domain in
   `src/backend/.env`:

   ```bash
   PUBLIC_APP_BASE_URL=https://<yours>.ngrok-free.app
   ```

   Then **restart the backend** — settings are cached at startup, and
   `--reload` does not watch `.env`. (Restart wipes in-memory sessions and
   short links; old WhatsApp links die. Do it at a natural break.)

5. Start the tunnel and re-point the Meta webhook **once** (tunnel must be up
   first — Meta calls the GET verify endpoint during subscription):

   ```bash
   ngrok http 5173 --domain=<yours>.ngrok-free.app
   python3 scripts/update_whatsapp_webhook_subscription.py \
     https://<yours>.ngrok-free.app/api/whatsapp/webhook
   ```

   Expect `200 {"success":true}`.

The vite dev server already allows ngrok hosts (`allowedHosts` in
`src/frontend/vite.config.ts` includes `.ngrok-free.app`).

## Daily Dev Loop

One command, same URL every day, no `.env` edits, no Meta re-pointing:

```bash
ngrok http 5173 --domain=<yours>.ngrok-free.app
```

Start order: backend (`:8000`) → frontend (`:5173`) → ngrok. Editing
`vite.config.ts` no longer requires a tunnel restart — ngrok reconnects to the
restarted vite server cleanly.

## Verify The Chain Is Healthy

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  "https://<yours>.ngrok-free.app/api/session/x?token=x"
```

- `404` → the whole chain works (that is the backend answering through
  tunnel + vite proxy). Anything else is infra, not app code.
- Then send `@EasyOrder get biryani for 4 under 2000` from the handset and
  tap the buttons in the reply.

## Expected First-Visit Interstitial

The free tier shows an ngrok warning page ("You are about to visit…") on the
**first browser visit only** — tap **Visit Site** once; it sets a cookie.
Webhook POSTs and API calls are never intercepted. This replaces loca.lt's
tunnel-password page.

## Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| `ERR_NGROK_108` on start | Free plan allows one agent session — stop the other `ngrok` process. |
| `ERR_NGROK_3200` in browser | Tunnel not running — start the daily-loop command. |
| Links open but API calls fail | Backend down or vite proxy misconfigured — run the chain check above; `404` means app-side, else restart backend/vite. |
| WhatsApp reply links show the wrong host | `PUBLIC_APP_BASE_URL` stale — fix `.env`, restart backend, send a fresh message. |
| Short link `404 Unknown or expired link` | Backend restarted since the message was sent (mappings are in-memory) — send a fresh `@EasyOrder` message. |

## Decommission loca.lt

Once ngrok works end-to-end, stop both `npx localtunnel` processes
(`easyorder-web-dev`, `easyorder-api-dev`). Nothing references loca.lt at
runtime after `PUBLIC_APP_BASE_URL` and the Meta subscription move over;
`.loca.lt` stays in vite `allowedHosts` as a harmless fallback.
