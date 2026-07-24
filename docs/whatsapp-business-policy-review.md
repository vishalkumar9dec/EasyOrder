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
| **24-hour customer service window** | `[TODO: verify]` — the code does not currently check message timestamps against the 24-hour window before sending free-form replies (e.g. order-history answers, deletion confirmations). If a user's last inbound message is older than 24h, a free-form reply may fail delivery or violate policy; only a template message is allowed outside the window. This should be added as an explicit check before general availability. |
| **Data minimization / no unrelated data collection** | Only phone number, order request text (redacted for PII), and derived cart/order data are stored. No location, payment, or unrelated personal data is collected in the current build. | `docs/privacy-policy-draft.md` |
| **User control over data** | Users can request deletion of all their EasyOrder data via WhatsApp ("delete my data confirm"), with an explicit two-step confirm-before-delete flow so it can't happen by accident. | `services/privacy.py`, `services/intent_router.py` |
| **Opt-out / consent** | New users see a short privacy notice (what's stored, how to delete it) in the onboarding reply the first time they greet EasyOrder. `[TODO: this is a lightweight, non-blocking notice, not a recorded/auditable consent capture — evaluate whether DPDP/Meta policy requires an explicit opt-in step before the first substantive reply, not just a notice alongside it.]` | `services/intent_router.py::ONBOARDING_REPLY` |
| **Commerce policy (facilitating a third-party purchase)** | EasyOrder recommends items and builds a cart, but the actual order/checkout happens on Swiggy's platform, not inside the WhatsApp conversation. No payment collection happens in WhatsApp. | `docs/adr/0005-host-mediated-group-flow.md`; production-readiness.md |

## Known gaps before a real onboarding review

1. **24-hour window enforcement is not implemented.** Every free-form
   reply (order history, share, deletion) should check whether the
   session is still within Meta's 24-hour customer service window and
   fall back to an approved template (or decline) outside it. Currently
   assumed to always be within-window because the pilot audience is small
   and responds quickly — this assumption will not hold at scale.
2. **Template content has not been submitted to Meta for approval** in
   this environment; `WHATSAPP_HANDOFF_TEMPLATE_NAME` is empty by default.
   A real launch needs at least one approved template for business-
   initiated handoff messages outside the 24-hour window.
3. **No documented WhatsApp Business Platform onboarding/verification**
   has been completed for a production WABA (WhatsApp Business Account) —
   the current setup uses a test number. Business verification with Meta
   is required before sending to real users at volume.
4. **Consent notice, not explicit consent capture.** See the opt-out/consent
   row above — worth a deliberate product decision on whether a notice is
   sufficient or an explicit "I agree" step is needed.

## Recommendation

Treat this checklist as a starting point for the actual Meta Business
verification/policy review, not a replacement for it. File a follow-up
task to: (a) implement 24-hour-window checks before free-form replies,
(b) get at least one template approved, (c) complete WhatsApp Business
Platform verification, before onboarding real users beyond a small private
pilot.
