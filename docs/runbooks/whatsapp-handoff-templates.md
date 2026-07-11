# WhatsApp Handoff: CTA, Templates, And Short Links

Task 10.2 replaces raw tokenized session URLs in WhatsApp copy with a
capability-aware handoff. This runbook documents the message shapes, the
template contract, fallback rules, and short-link behavior.

## Message Selection Order (Meta mode)

1. **Approved template** — only when `WHATSAPP_HANDOFF_TEMPLATE_NAME` is set.
2. **Interactive CTA-URL message** — the default. No template approval is
   needed and it is valid inside the 24-hour customer-service window that the
   inbound `@EasyOrder` message just opened.
3. **Plain-text fallback** — concise copy with short links, sent automatically
   if Graph rejects the rich payload (logged as
   `whatsapp_handoff_rich_payload_failed`).

Mock mode captures the handoff object and its text fallback for assertions;
group/private mock messages also carry short links only.

## Interactive CTA Messages

WhatsApp allows only **one URL button per interactive message**, so the CTA
handoff sends **two messages**:

1. Body: session-ready copy; button `Review order` → **host short link**.
2. Body: share copy including the **guest short link** as copyable text
   (so it can be forwarded to the group); button `Open planning canvas` →
   the same guest short link.

No approval process applies. Requires the 24h session window, which is always
open for the initiating sender because they just messaged the business number.
For a single message with both buttons, use the approved template below.

## Template Contract

Template messages are only needed outside the 24h window (proactive sends).
The default template name we register is `easyorder_session_handoff`.

| Field | Value |
|---|---|
| Template name | `WHATSAPP_HANDOFF_TEMPLATE_NAME` (suggested: `easyorder_session_handoff`) |
| Language | `WHATSAPP_HANDOFF_TEMPLATE_LANGUAGE` (default `en`) |
| Body variable `{{1}}` | Guest short URL (shareable planning canvas) |
| URL button index 0 parameter | Host short URL (`Review order`, private review/checkout) |
| URL button index 1 parameter | Guest short URL (`Open planning canvas`) |
| Category | `UTILITY` |

Templates support up to two URL buttons, which is why the approved template is
the only way to get both links as buttons in a single message.

Approval requirements:

- The template must be approved in WhatsApp Manager for the WABA
  (`WHATSAPP_WABA_ID`) before enabling it via env.
- The URL button's registered base URL must be token-free; the dynamic
  parameter supplies the short link.
- Rejection or `132000`-class Graph errors fall back to plain text
  automatically — no config change needed to recover.

## Short Links

- Outbound copy never contains `token=`, `host_…`, or `guest_…` material.
- `GET /api/r/{code}` returns `307` to the tokenized session URL under
  `PUBLIC_APP_BASE_URL`; unknown codes return `404 Unknown or expired link`.
- Codes are opaque (`secrets.token_urlsafe`), stored server-side in
  `InMemoryShortLinkService`, and scoped to the backend process — they reset
  together with in-memory sessions, so a code can never outlive its session.
- The same target path always reuses its existing code (idempotent with the
  wamid dedup ledger on webhook retries).

## Debugging

- CTA send fails in Meta → check `whatsapp_handoff_rich_payload_failed` logs
  for the Graph error body; verify phone number id, template approval state,
  and API version before changing copy.
- Short link 404s → backend restarted since the message was sent (mappings are
  in-memory); send a fresh `@EasyOrder` message.
- Wrong host in redirect target → check `PUBLIC_APP_BASE_URL` and restart the
  backend after editing `.env` (settings are cached at startup).
