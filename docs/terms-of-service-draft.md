# EasyOrder Terms of Service — DRAFT

> **Status: draft, not legal advice.** Not reviewed by a lawyer. Do not
> publish, link from the app, or present to users as final terms until
> qualified counsel has reviewed it. Placeholders are marked `[TODO: ...]`.

## 1. What EasyOrder does

EasyOrder is a WhatsApp assistant that helps a group plan and check out a
Swiggy Food and/or Instamart order together. EasyOrder recommends items and
prepares a cart; **the order itself is placed on Swiggy's platform**, not by
EasyOrder. `[TODO: confirm this framing once real Swiggy checkout (not the
current mock/host-only-checkout handoff) is live — see
docs/production-readiness.md blocker B2.]`

## 2. Who can place the actual order

Only the session **host** — the person who first messaged EasyOrder to
start a session — can complete checkout. Guests can view and edit the
shared cart but cannot check out (`docs/adr/0005-host-mediated-group-flow.md`).
This is enforced in code, not just policy: guest tokens are rejected by the
checkout route.

## 3. Accuracy of recommendations

EasyOrder's item search, pricing, and availability come from Swiggy (or a
mock data source during development/pilot phases). Prices, availability,
and delivery estimates can change between when EasyOrder shows them and
when you check out on Swiggy. EasyOrder is not responsible for
discrepancies that arise on Swiggy's platform.

## 4. What EasyOrder does not do

- EasyOrder does not process payments or store payment information.
- EasyOrder does not guarantee delivery, food quality, or order
  fulfillment — those are Swiggy's responsibility once checkout completes.
- EasyOrder does not currently handle refunds, cancellations, or payment
  disputes; those must be raised directly with Swiggy.
  `[TODO: confirm this scope boundary with product/legal before launch —
  see docs/easyorder-prd.md "out of scope" section.]`

## 5. Acceptable use

Don't use EasyOrder to send content that violates WhatsApp's own terms, or
attempt to manipulate its parsing/agent logic (e.g. prompt injection). Inputs
are screened for known injection patterns and rejected
(`services/agent.py`, `InputGuardrails`); repeated abuse may result in your
number being blocked from using the service. `[TODO: define and document
the actual enforcement process once one exists.]`

## 6. Your data

See the [Privacy Policy](privacy-policy-draft.md) — in short, you can
request deletion of all your EasyOrder data at any time by messaging
"delete my data confirm".

## 7. Changes to these terms

`[TODO: define a real change-notification process — e.g. a pinned WhatsApp
message or an in-app notice — before publishing.]`

## 8. Governing law and disputes

`[TODO: legal review required — jurisdiction, dispute resolution process,
and limitation of liability clauses all need counsel input specific to
where EasyOrder operates and is incorporated.]`

---
_Last updated: [TODO — set on actual publish date]._
