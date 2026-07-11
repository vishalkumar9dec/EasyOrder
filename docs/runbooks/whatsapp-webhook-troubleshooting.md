# WhatsApp Webhook Troubleshooting Runbook

This runbook captures the Meta WhatsApp Cloud API webhook issue debugged during
local EasyOrder testing. Use it when outbound WhatsApp sends work, but inbound
messages from a handset do not produce backend logs or EasyOrder replies.

## What Happened

The local backend, tunnel, and EasyOrder webhook handler were healthy, but real
handset messages were not reaching the backend.

The confusing part was that synthetic tests worked:

- `python3 scripts/test_whatsapp_api.py --send-template ...` eventually worked.
- `python3 scripts/test_whatsapp_api.py --send-text ...` worked.
- A signed control webhook POST to the local backend worked.
- A signed control webhook POST through the public tunnel worked.
- The handset received EasyOrder replies from those control webhook replays.

But real messages sent from the handset to the Meta test number did not create
`whatsapp_webhook_received` backend logs.

The root causes were:

1. The app webhook subscription in Meta still pointed to a stale localtunnel URL:
   `https://easyorder-api-dev.loca.lt/api/whatsapp/webhook`.
2. The active backend tunnel had changed to a different URL:
   `https://chatty-horse-53.loca.lt/api/whatsapp/webhook`.
3. The WhatsApp Business Account was not subscribed to the EasyOrder app. It was
   only showing Meta's DevX webhook app in `/{waba-id}/subscribed_apps`.
4. The running backend sometimes had older `.env` values loaded, so changes to
   `WHATSAPP_ACCESS_TOKEN` or `PUBLIC_APP_BASE_URL` did not take effect until the
   backend was restarted.
5. Localtunnel sometimes returned a random URL even when a stable subdomain was
   requested. The URL printed by localtunnel is authoritative.

`WHATSAPP_PHONE_NUMBER_ID=1259090637280209` was not the problem. That value was
the correct sender phone number ID for the Meta test number `+1 555-605-3706`.

## Expected Healthy Flow

1. The handset sends:

   ```text
   @EasyOrder get biryani for 4 under 2000
   ```

2. Meta POSTs a `messages` webhook to:

   ```text
   https://<backend-tunnel>/api/whatsapp/webhook
   ```

3. Backend logs show:

   ```text
   whatsapp_webhook_received ...
   whatsapp_webhook_parsed ... messages_seen=1 tagged_messages=1
   whatsapp_handoff_sending ... recipient_id=<sender-wa-id>
   whatsapp_session_created ... session_id=session_...
   ```

4. EasyOrder sends a direct WhatsApp reply to the inbound sender `wa_id` with:

   - private host link
   - shareable guest link

## Where To Look For Logs

The logs appear in the terminal running the backend:

```bash
make backend-dev
```

If you use `make up`, the same logs appear in the `make up` terminal mixed with
frontend and setup output. For live Meta debugging, separate terminals are easier:

```bash
make db-up
make db-migrate
make backend-dev
make frontend-dev
npx -y localtunnel --port 8000 --subdomain easyorder-api-dev
npx -y localtunnel --port 5173 --subdomain easyorder-web-dev
```

## Required Environment Variables

In `src/backend/.env`:

```bash
WHATSAPP_PROVIDER_MODE=meta
WHATSAPP_ACCESS_TOKEN=<current-meta-access-token>
WHATSAPP_PHONE_NUMBER_ID=<meta-phone-number-id>
WHATSAPP_WABA_ID=<whatsapp-business-account-id>
WHATSAPP_APP_SECRET=<meta-app-secret>
WHATSAPP_VERIFY_TOKEN=<chosen-verify-token>
WHATSAPP_API_VERSION=v21.0
PUBLIC_APP_BASE_URL=https://<frontend-tunnel-or-deployed-url>
```

Important details:

- `WHATSAPP_PHONE_NUMBER_ID` is the sending phone number ID, not the WABA ID.
- `WHATSAPP_WABA_ID` is needed for `--check-subscription`.
- `PUBLIC_APP_BASE_URL` controls links sent to WhatsApp users.
- Restart the backend after changing `.env`.
- Never commit real tokens or app secrets.

## Localtunnel Gotcha

Do not assume localtunnel gave the subdomain you requested. This command:

```bash
npx -y localtunnel --port 8000 --subdomain easyorder-api-dev
```

may print either:

```text
your url is: https://easyorder-api-dev.loca.lt
```

or a random fallback:

```text
your url is: https://chatty-horse-53.loca.lt
```

The printed URL is the one to use in Meta.

If the printed URL differs from Meta's callback URL, handset messages will not
hit your backend. Verify the active callback:

```bash
python3 scripts/test_whatsapp_api.py --check-number
```

Look for:

```json
"webhook_configuration": {
  "application": "https://<backend-tunnel>/api/whatsapp/webhook"
}
```

Also verify the public endpoint directly:

```bash
curl -i "https://<backend-tunnel>/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=<verify-token>&hub.challenge=abc123"
```

Expected:

```text
HTTP/1.1 200 OK

abc123
```

## Meta UI Setup Checklist

When creating a new app from Meta UI:

1. Go to **Meta Developers → My Apps → Your App**.
2. Add or open the **WhatsApp** product.
3. In **Step 1. Try it out**, copy:
   - test phone number
   - phone number ID
   - WhatsApp Business Account ID
   - temporary access token
4. Add and verify your handset as a test recipient.
5. In **Step 2. Production setup**, configure webhooks:
   - Callback URL: `https://<backend-tunnel>/api/whatsapp/webhook`
   - Verify token: same value as `WHATSAPP_VERIFY_TOKEN`
   - Client certificate toggle: off for local testing
6. In the **Webhook fields** table, subscribe `messages`.
7. Ensure the EasyOrder app is subscribed to the WABA itself. This is the part
   that fixed real handset delivery during the incident. The UI may show the
   callback as verified, and may show the `messages` field as subscribed, while
   the WABA subscribed-apps list still does not contain your app. Verify with:

   ```bash
   python3 scripts/test_whatsapp_api.py --check-subscription
   ```

   The healthy response must include your app:

   ```json
   {
     "whatsapp_business_api_data": {
       "name": "easyorder",
       "id": "823160707397760"
     }
   }
   ```

   Seeing Meta's `WA DevX Webhook Events 1P App` alone is not enough. That app
   is Meta's internal test harness. It can make test webhook payloads appear in
   the dashboard, but it does not mean real WABA events are being delivered to
   EasyOrder.
8. Restart the backend after changing `.env`:

   ```bash
   make dev-down
   make backend-dev
   ```

### UI Equivalent Of The WABA Subscription Fix

Meta changes this navigation often, but the concepts are stable:

1. Open the exact Meta app used by EasyOrder: `823160707397760`.
2. Open the WhatsApp product or the app-level **Webhooks** settings.
3. Select the webhook object **WhatsApp Business Account**.
4. Choose the WABA from Step 1: `27488993034053054`.
5. Subscribe the app to that WABA.
6. Subscribe the `messages` field.
7. Save, then run:

   ```bash
   python3 scripts/test_whatsapp_api.py --check-subscription --waba-id 27488993034053054
   ```

If the output only lists `WA DevX Webhook Events 1P App`, real handset messages
are still not wired to EasyOrder. The output should list both apps during local
testing:

- `easyorder` / `823160707397760`
- `WA DevX Webhook Events 1P App` / `2202427980234937`

## Why We Used APIs Instead Of Only The UI

The Meta UI showed parts of the setup as complete, but the authoritative Graph
API state still had mismatches:

- The app webhook subscription callback URL was stale.
- The WABA subscribed-apps list did not include the EasyOrder app.
- The phone number webhook configuration was still pointing to a stale tunnel.

The API calls answered questions the UI did not make obvious:

- Which callback URL is actually attached to the app subscription?
- Which callback URL is actually attached to the phone number?
- Which apps are actually subscribed to the WABA?
- Is the current access token valid?
- Can the current sender phone number send text messages?

Using APIs also made the fix repeatable and auditable. The UI is still fine for
initial setup, but Graph API checks should be used when behavior contradicts what
the UI seems to show.

## Exact Fix Applied During The Incident

There were two separate Meta states to fix.

### 1. Update The App Webhook Callback

Before the fix, the app webhook subscription still pointed to an old tunnel:

```text
https://easyorder-api-dev.loca.lt/api/whatsapp/webhook
```

But the running backend tunnel was:

```text
https://chatty-horse-53.loca.lt/api/whatsapp/webhook
```

We updated the app subscription with this Graph API call:

```http
POST https://graph.facebook.com/v21.0/823160707397760/subscriptions
Content-Type: application/x-www-form-urlencoded
```

Form body:

```text
object=whatsapp_business_account
callback_url=https://chatty-horse-53.loca.lt/api/whatsapp/webhook
verify_token=easyorder_webhook_verify_2026
fields=messages
access_token=823160707397760|<WHATSAPP_APP_SECRET>
```

Expected response:

```json
{"success": true}
```

This tells Meta which public backend URL to call for the EasyOrder app's
`whatsapp_business_account` webhook subscription.

### 2. Subscribe The EasyOrder App To The WABA

Before the fix, `/{waba-id}/subscribed_apps` only showed Meta's DevX app:

```json
{
  "data": [
    {
      "whatsapp_business_api_data": {
        "category": "Business",
        "link": "https://www.facebook.com/games/?app_id=2202427980234937",
        "name": "WA DevX Webhook Events 1P App",
        "id": "2202427980234937"
      }
    }
  ]
}
```

That meant the WABA was not delivering real events to the EasyOrder app, even
though the Meta dashboard could still show test webhook payloads.

We attached EasyOrder to the WABA with this Graph API call:

```http
POST https://graph.facebook.com/v21.0/27488993034053054/subscribed_apps
Content-Type: application/x-www-form-urlencoded
Authorization: Bearer <WHATSAPP_ACCESS_TOKEN>
```

Form body:

```text
access_token=<WHATSAPP_ACCESS_TOKEN>
```

Expected response:

```json
{"success": true}
```

After the fix, the subscribed-apps check showed both apps:

```json
{
  "data": [
    {
      "whatsapp_business_api_data": {
        "link": "https://www.facebook.com/games/?app_id=823160707397760",
        "name": "easyorder",
        "id": "823160707397760"
      }
    },
    {
      "whatsapp_business_api_data": {
        "category": "Business",
        "link": "https://www.facebook.com/games/?app_id=2202427980234937",
        "name": "WA DevX Webhook Events 1P App",
        "id": "2202427980234937"
      }
    }
  ]
}
```

That second state change was the key fix for real handset messages. The app
callback decides where EasyOrder receives webhooks; the WABA subscribed-apps
relationship decides whether this WABA delivers real events to EasyOrder at all.

`WHATSAPP_PHONE_NUMBER_ID=1259090637280209` was unrelated to this inbound
delivery issue. That value is used for outbound sends and replies. The inbound
delivery relationship is controlled by the app subscription callback and the
WABA subscribed-apps list.

## Meta APIs Used

These are the Meta Graph API calls used during troubleshooting. Replace IDs,
tokens, and URLs with the current values.

### Check Phone Number Configuration

Purpose: verify the sender phone number ID, token validity, and current webhook
configuration.

Script:

```bash
python3 scripts/test_whatsapp_api.py --check-number
```

Underlying API:

```http
GET /v21.0/{phone-number-id}
Authorization: Bearer {WHATSAPP_ACCESS_TOKEN}
```

Important response field:

```json
{
  "webhook_configuration": {
    "application": "https://<backend-tunnel>/api/whatsapp/webhook"
  }
}
```

### Check WABA Subscribed Apps

Purpose: verify that the EasyOrder app is subscribed to the WhatsApp Business
Account, not only Meta's DevX test app.

Script:

```bash
python3 scripts/test_whatsapp_api.py --check-subscription
```

Underlying API:

```http
GET /v21.0/{waba-id}/subscribed_apps
Authorization: Bearer {WHATSAPP_ACCESS_TOKEN}
```

Healthy response includes the EasyOrder app:

```json
{
  "whatsapp_business_api_data": {
    "name": "easyorder",
    "id": "823160707397760"
  }
}
```

### Check App Webhook Subscriptions

Purpose: inspect the callback URL and subscribed webhook fields configured on the
Meta app.

Underlying API:

```http
GET /v21.0/{app-id}/subscriptions?access_token={app-id}|{app-secret}
```

Healthy response:

```json
{
  "object": "whatsapp_business_account",
  "callback_url": "https://<backend-tunnel>/api/whatsapp/webhook",
  "active": true,
  "fields": [
    {"name": "messages", "version": "v25.0"}
  ]
}
```

### Update App Webhook Subscription Callback

Purpose: update the app webhook subscription to the current backend tunnel URL.
This fixed the stale `easyorder-api-dev.loca.lt` callback during the incident.

Underlying API:

```http
POST /v21.0/{app-id}/subscriptions
Content-Type: application/x-www-form-urlencoded

object=whatsapp_business_account
callback_url=https://<backend-tunnel>/api/whatsapp/webhook
verify_token={WHATSAPP_VERIFY_TOKEN}
fields=messages
access_token={app-id}|{app-secret}
```

Expected response:

```json
{"success": true}
```

### Subscribe App To WABA

Purpose: ensure real WABA events are delivered to the EasyOrder app.

Underlying API:

```http
POST /v21.0/{waba-id}/subscribed_apps
Authorization: Bearer {WHATSAPP_ACCESS_TOKEN}
```

Form body:

```text
access_token={WHATSAPP_ACCESS_TOKEN}
```

Expected response:

```json
{"success": true}
```

### Send Template Message

Purpose: verify outbound provider credentials can send an approved template.

Script:

```bash
python3 scripts/test_whatsapp_api.py --send-template --to <recipient-wa-id>
```

Underlying API:

```http
POST /v21.0/{phone-number-id}/messages
Authorization: Bearer {WHATSAPP_ACCESS_TOKEN}
Content-Type: application/json
```

Payload shape:

```json
{
  "messaging_product": "whatsapp",
  "to": "<recipient-wa-id>",
  "type": "template",
  "template": {
    "name": "hello_world",
    "language": {"code": "en_US"}
  }
}
```

### Send Text Message

Purpose: verify the same outbound message type EasyOrder uses for handoff
replies. This only works inside the WhatsApp customer service window.

Script:

```bash
python3 scripts/test_whatsapp_api.py --send-text --to <recipient-wa-id> --message "EasyOrder debug text"
```

Underlying API:

```http
POST /v21.0/{phone-number-id}/messages
Authorization: Bearer {WHATSAPP_ACCESS_TOKEN}
Content-Type: application/json
```

Payload shape:

```json
{
  "messaging_product": "whatsapp",
  "to": "<recipient-wa-id>",
  "type": "text",
  "text": {
    "preview_url": false,
    "body": "EasyOrder debug text"
  }
}
```

## Local Verification Commands

### Verify Backend Callback

```bash
curl -i "https://<backend-tunnel>/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=<verify-token>&hub.challenge=abc123"
```

Expected:

```text
200 OK
abc123
```

### Replay A Signed Control Webhook

Purpose: prove that the public tunnel, FastAPI webhook, signature validation,
session creation, and WhatsApp handoff all work without waiting for a handset
message.

Run from `src/backend`:

```bash
.venv/bin/python -c "import hashlib,hmac,json,urllib.request; from app.config import Settings; payload={'object':'whatsapp_business_account','entry':[{'id':Settings().whatsapp_waba_id,'changes':[{'field':'messages','value':{'messaging_product':'whatsapp','metadata':{'display_phone_number':'15556053706','phone_number_id':Settings().whatsapp_phone_number_id},'contacts':[{'wa_id':'<recipient-wa-id>'}],'messages':[{'from':'<recipient-wa-id>','id':'wamid.debug-control','timestamp':'1783175886','type':'text','text':{'body':'@EasyOrder get biryani for 4 under 2000'}}]}}]}]}; body=json.dumps(payload,separators=(',',':')).encode(); sig=hmac.new(Settings().whatsapp_app_secret.encode(), body, hashlib.sha256).hexdigest(); req=urllib.request.Request('https://<backend-tunnel>/api/whatsapp/webhook', data=body, headers={'Content-Type':'application/json','X-Hub-Signature-256':'sha256='+sig}, method='POST'); resp=urllib.request.urlopen(req, timeout=20); print(resp.status); print(resp.read().decode())"
```

Expected:

```text
200
{"status":"created", ...}
```

Backend logs should include:

```text
whatsapp_webhook_received
whatsapp_webhook_parsed ... messages_seen=1 tagged_messages=1
whatsapp_handoff_sending
whatsapp_session_created
```

## Symptom-To-Cause Table

| Symptom | Likely cause | Check | Fix |
|---|---|---|---|
| Meta Verify and Save fails | Callback URL unreachable or verify token mismatch | `curl` the callback verification URL | Use actual tunnel URL and matching `WHATSAPP_VERIFY_TOKEN` |
| `curl` to tunnel returns `502` or `503 Tunnel Unavailable` | Localtunnel is stale or disconnected | `ps aux \| rg localtunnel` | Restart tunnel and update Meta with printed URL |
| No backend logs from handset message | Meta is not POSTing real messages to backend | `--check-number`, `--check-subscription` | Update app callback and subscribe app to WABA |
| Backend logs `messages_seen=0` | Meta sent status/system event, not an inbound text message | Backend logs | Send a fresh text message from handset |
| Backend logs `tagged_messages=0` | Message lacks `@EasyOrder` | Backend logs | Include `@EasyOrder` in the message body |
| Backend returns `502 Session was created but WhatsApp handoff failed` | Outbound text reply failed | Backend `whatsapp_handoff_failed` log | Refresh access token, verify recipient, test `--send-text` |
| Guest/host links use wrong domain | Backend loaded stale `PUBLIC_APP_BASE_URL` | Inspect generated links and `.env` | Update `.env` and restart backend |
| Guest/host link opens a blank page or Vite says host is blocked | Frontend tunnel host is not allowed by Vite | `curl -i https://<frontend-tunnel>/` | Add `.loca.lt` to `server.allowedHosts` in `src/frontend/vite.config.ts` and keep the frontend tunnel running |
| Guest/host link opens but session never loads | Frontend cannot proxy `/api` to backend | `curl -i "https://<frontend-tunnel>/api/session/not-a-real-session?token=guest_test"` | Confirm it returns backend JSON, restart backend/frontend, and verify `VITE_API_BASE_URL`/proxy target |
| Template send works but EasyOrder reply fails | Template and text-message permissions/windows differ | `--send-text` | Open service window by messaging test number, or use template for proactive messages |

## Final Known-Good State From The Incident

The final working configuration had these properties:

- Phone number ID: `1259090637280209`
- WABA ID: `27488993034053054`
- App ID: `823160707397760`
- Backend callback: `https://chatty-horse-53.loca.lt/api/whatsapp/webhook`
- Frontend app base URL: `https://easyorder-web-dev.loca.lt`
- App subscription object: `whatsapp_business_account`
- App subscription fields included `messages`
- WABA subscribed apps included `easyorder` / `823160707397760`
- Signed control webhook returned `200`
- Backend logs showed `whatsapp_session_created`

Do not hardcode those tunnel URLs for future sessions. Localtunnel URLs can
change; always use the URL printed by the running tunnel process and verify it
with `curl`.
