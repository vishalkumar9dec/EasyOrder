# ADR 0006: Unified Account API With WhatsApp OTP Login

## Status

Accepted

## Context

Task 10.6 phases 1-2 shipped order history and share commands as WhatsApp
chat replies. The data path went through a shared service layer, but there
was no HTTP account API and no browser identity, so the PWA could not show
the same information. The product owner rejected chat-only account features
as unshippable: whatever WhatsApp can answer must be available in the PWA,
served by the same APIs, with Swiggy MCP providing deeper detail behind
those same APIs.

The blocker for PWA parity was identity: WhatsApp delivers a verified
`wa_id` with every message; a browser proves nothing. A login mechanism was
required, and magic-link-only access was rejected.

## Decision

1. **One account API for all surfaces.** Account features are exposed as
   HTTP APIs (`/api/me`, `/api/me/orders`, ...) backed by the same services
   the webhook responders use. Chat replies and PWA views are thin renderers
   over identical data. New account features must land as API + both
   surfaces, never chat-only or web-only.
2. **PWA login is WhatsApp OTP.** The user enters their phone number; a
   one-time code is sent through the existing EasyOrder WhatsApp number;
   verifying it issues an HTTP-only web session cookie bound to the
   `wa_id`. Web identity therefore equals WhatsApp identity — history is
   unified across surfaces by construction, with no account-linking step
   and no SMS provider.
3. **Sessions and tokens follow existing conventions.** Web session tokens
   are opaque, stored hashed, durable in postgres persistence mode, and
   revocable. OTP codes are stored hashed with expiry and attempt limits.
4. **Swiggy MCP enrichment** (menus, live status, discovery) attaches
   behind the account API when scopes allow, serving both surfaces at once.

## Consequences

- The PWA gains login, and account pages become possible (My Orders first).
- Users without WhatsApp cannot log in to the PWA; acceptable for a
  WhatsApp-first product, revisit if the audience widens (SMS OTP fallback).
- Sending OTPs uses the standing WhatsApp send path; in mock mode codes are
  captured locally, so the full login flow is testable offline.
- The 24h customer-service window does not constrain OTPs in practice: the
  user just initiated login, and template-based sends remain the documented
  fallback for cold sends.
- Chat responders (order history, share) are consumers of the account
  service; any drift between chat and PWA answers is a bug.
