# ADR 0004: Separate WhatsApp Operating Modes

## Status

Accepted

## Context

EasyOrder now has two useful WhatsApp entry points:

1. A concise `@EasyOrder` prompt that starts a collaborative ordering session.
2. A dedicated EasyOrder business chat where a user can ask for saved lists,
   order history, status, discovery, offers, and shareable summaries.

These two surfaces look similar because both arrive through Meta WhatsApp
webhooks, but they have different privacy expectations. A group-planning trigger
should stay narrow and explicit. A dedicated business chat can support broader
assistant behavior because the user intentionally opened a conversation with the
EasyOrder business account.

## Decision

EasyOrder will model WhatsApp ingestion with explicit operating modes:

- `mention_planning`: a tagged prompt such as `@EasyOrder get biryani for 4 under
  2000` starts or updates an ordering session.
- `business_chat`: a direct chat with the EasyOrder business account can route
  free-form messages to assistant intents such as saved lists, order history,
  active order status, discovery, offers, share requests, or unsupported replies.

EasyOrder will not passively process ordinary WhatsApp group conversations.
If future group participation is added, it must require explicit user action,
supported platform capabilities, and a clear privacy model.

Session handoff should use supported WhatsApp interactive/template messages when
configured, with short branded links as fallback. Normal WhatsApp text should
not be treated as an HTML surface that can hide long URLs behind arbitrary link
text.

Saved lists and wishlist flows can prepare carts, but checkout remains
review-before-order. The agent must not autonomously place or pay for an order.

## Consequences

- The webhook handler needs an intent router before invoking the ordering agent.
- Tests must cover both mode classification and intent routing.
- The PWA should show user-safe message timeline events so users can connect the
  WhatsApp request to the generated session.
- Order history and status queries require reliable user identity and official
  Swiggy data access; until then, they must fail gracefully.
- The product can grow into a real business assistant without weakening the
  privacy boundary that made the original `@EasyOrder` flow safe.
