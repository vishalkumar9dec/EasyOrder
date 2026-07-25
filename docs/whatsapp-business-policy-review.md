# WhatsApp Business Messaging Policy — Self-Assessment

> **Status: engineering self-review, not a compliance sign-off.** This
> checks EasyOrder's current message-handling behavior against the *shape*
> of Meta's WhatsApp Business Messaging Policy from what's implemented in
> code. It is not a substitute for an actual policy review by Meta (via the
> WhatsApp Business Platform onboarding/verification process) or by legal
> counsel before onboarding real users at scale. Meta's policy text can
> change — always check the current policy at business.whatsapp.com before
> relying on this document.

## What's implemented and how it maps to policy themes

| Policy theme | EasyOrder's behavior today | Evidence |
|---|---|---|
| **No scanning of messages you're not part of** | EasyOrder ignores every message unless it's explicitly tagged `@EasyOrder`, or sent as a direct message to the EasyOrder business number. Untagged group messages are never read, logged, or processed. | `docs/adr/0003-mention-only-webhook.md`; `services/intent_router.py::classify_chat_mode` |
| **User-initiated contact** | A session only starts when a user messages EasyOrder first (tag or direct message). EasyOrder never cold-messages a number it hasn't heard from, except the session handoff messages sent as part of an already-initiated flow. | `api/whatsapp.py` webhook handler |
| **Template approval for business-initiated messages** | The host handoff can use an approved template name (`WHATSAPP_HANDOFF_TEMPLATE_NAME`) when configured, falling back to an interactive CTA message within the 24-hour customer service window otherwise. | `services/whatsapp_sender.py`; `.env.example` |
| **24-hour customer service window** | Verified structurally satisfied today, not just assumed: every free-form reply (order-history answer, share, deletion confirmation) is a synchronous reply to `message.sender_id` — the same `wa_id` whose inbound message is being processed in that same webhook call — so the recipient's last inbound message is always milliseconds old. The session handoff in `meta` mode follows the same pattern. There is no code path today where EasyOrder messages someone who hasn't just messaged it. This stops being true the day any proactive/asynchronous send is added (e.g. a delivery-status push, a reminder) — a real timestamp-based window check becomes a hard requirement *for that feature*, not before. | `api/whatsapp.py:222` (business-chat replies), `api/whatsapp.py:338` (handoff), `services/whatsapp_sender.py:219-220` (no group-chat concept in Meta's API — "group" send is code-identical to a 1:1 send) |
| **Data minimization / no unrelated data collection** | Only phone number, order request text (redacted for PII), and derived cart/order data are stored. No location, payment, or unrelated personal data is collected in the current build. | `docs/privacy-policy-draft.md` |
| **User control over data** | Users can request deletion of all their EasyOrder data via WhatsApp ("delete my data confirm"), with an explicit two-step confirm-before-delete flow so it can't happen by accident. | `services/privacy.py`, `services/intent_router.py` |
| **Opt-out / consent** | New users see a short privacy notice (what's stored, how to delete it) in the onboarding reply the first time they greet EasyOrder. `[TODO: this is a lightweight, non-blocking notice, not a recorded/auditable consent capture — evaluate whether DPDP/Meta policy requires an explicit opt-in step before the first substantive reply, not just a notice alongside it.]` | `services/intent_router.py::ONBOARDING_REPLY` |
| **Commerce policy (facilitating a third-party purchase)** | EasyOrder recommends items and builds a cart, but the actual order/checkout happens on Swiggy's platform, not inside the WhatsApp conversation. No payment collection happens in WhatsApp. | `docs/adr/0005-host-mediated-group-flow.md`; production-readiness.md |

## Known gaps before a real onboarding review

1. **Template content has not been submitted to Meta for approval** in
   this environment; `WHATSAPP_HANDOFF_TEMPLATE_NAME` is empty by default.
   A real launch needs at least one approved template for business-
   initiated handoff messages outside the 24-hour window.
2. **No documented WhatsApp Business Platform onboarding/verification**
   has been completed for a production WABA (WhatsApp Business Account) —
   the current setup uses a test number. Business verification with Meta
   is required before sending to real users at volume.
3. **Consent notice, not explicit consent capture.** See the opt-out/consent
   row above — worth a deliberate product decision on whether a notice is
   sufficient or an explicit "I agree" step is needed.

(24-hour window enforcement was on this list; removed as a live gap after
verifying the current message model makes it structurally moot — see the
"24-hour customer service window" row above for the reasoning and the
condition under which it becomes a real requirement again.)

## Recommendation

Treat this checklist as a starting point for the actual Meta Business
verification/policy review, not a replacement for it. File a follow-up
task to: (a) get at least one template approved, (b) complete WhatsApp
Business Platform verification, before onboarding real users beyond a
small private pilot. Add an explicit 24-hour-window timestamp check as a
prerequisite *whenever* a proactive/asynchronous send (one not triggered
synchronously by the recipient's own inbound message) is first added to
the product — not before, per the reasoning above.
