# EasyOrder Privacy Policy — DRAFT

> **Status: draft, not legal advice.** This document was generated to give
> the product team a starting point grounded in what the code actually does
> (see file/ADR references below). It has **not** been reviewed by a lawyer
> and must not be published, linked from the app, or represented to users as
> a final privacy policy until qualified counsel has reviewed it for DPDP
> Act 2023 compliance, Meta's WhatsApp Business Messaging Policy, and any
> other applicable law. Placeholders are marked `[TODO: ...]`.

## What EasyOrder is

EasyOrder is a WhatsApp-based assistant that helps a group agree on and
place a Swiggy Food/Instamart order. This policy describes what personal
data EasyOrder collects, why, and how a user can have it deleted.

## Data we collect

| Data | Source | Why | Code reference |
|---|---|---|---|
| WhatsApp phone number (`wa_id`) | Every message you send us | Identifies the session host/guest; required to reply on WhatsApp | `models/session.py` (`host_phone`, `sender_wa_id`) |
| Order request text | Messages that explicitly tag `@EasyOrder`, or direct messages to our business number | Parsed to build your cart (budget, headcount, dietary preference, dishes) | `services/agent.py` |
| Cart contents and order history | Generated from the above | Lets you view/share your session and answer "what was my last order" | `services/order_history.py` |
| OTP codes and web login sessions | When you log in to the EasyOrder web app | Proves you control the phone number before showing your session | `services/web_auth.py` |

We do **not** read ordinary group chat messages. EasyOrder only processes a
message if it is explicitly tagged `@EasyOrder`, or sent directly to our
business number — every other message is ignored without being logged,
stored, or forwarded anywhere, including to any LLM. See
[ADR 0003](adr/0003-mention-only-webhook.md).

Free-text message content is redacted before storage: phone numbers,
email addresses, and card-like digit sequences are replaced with
`[redacted]` (`services/agent.py`, `InputGuardrails`). `[TODO: legal review —
confirm this redaction is sufficient for the categories of PII the DPDP Act
treats as sensitive, and whether the current regex (India phone numbers
only) needs to cover other formats.]`

## What we do not collect

- Payment or card details — checkout happens entirely on Swiggy's site;
  no payment information ever reaches EasyOrder.
- Precise location — a fixed default coordinate is used for restaurant
  search in the current build (`DEFAULT_LAT`/`DEFAULT_LNG`,
  `services/agent.py`); this will need updating if real location is added.

## How long we keep it

Sessions, carts, and order history are retained until deleted — either by
you (see below) or automatically by our retention job, which deletes
sessions older than **90 days** by default
(`scripts/easyorder_data_retention.py`). `[TODO: legal review — confirm 90
days is an appropriate retention period for this data category under DPDP's
purpose-limitation principle, and document the chosen period here once
decided.]`

## Your right to delete your data

Message **"delete my data confirm"** to our WhatsApp business number at any
time. This permanently deletes every EasyOrder session, cart, and order
history tied to your phone number — it cannot be undone
(`services/privacy.py`, `services/intent_router.py`). A first message
without "confirm" shows a warning instead of deleting anything, so this
can never happen by accident.

## Who we share data with

- **Swiggy**: order placement happens on Swiggy's platform; the checkout
  handoff sends your cart contents to Swiggy the same way it would if you
  ordered directly from their app.
- **Meta/WhatsApp**: as the messaging channel, Meta processes message
  metadata per its own terms.
- We do not sell or share your data with any other third party.
  `[TODO: legal review — confirm this statement, and add any data
  processors used for hosting/observability once Tier-1 infra is chosen.]`

## Contact

`[TODO: add a real contact email/address and a grievance officer, as
required under the DPDP Act, before publishing.]`

---
_Last updated: [TODO — set on actual publish date]._
