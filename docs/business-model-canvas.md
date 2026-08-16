# EasyOrder — Business Model Canvas

*Source of truth for the BMC slide shown in the submission video
(`docs/assets/business-model-canvas.html`). Drawn from
`docs/product-documentation.md` (§13–16) and `docs/builder-program-positioning.md`.*

The framing that matters for the Swiggy Builders Program: **EasyOrder does not
monetize the consumer.** Phase 1 value accrues to Swiggy as GMV — bigger group
carts, two verticals per plan, fewer abandoned coordination attempts. EasyOrder's
own revenue starts in Phase 2, on the B2B side, where a subscription is a natural
fit and doesn't tax the consumer flow.

---

## 1. Customer Segments

- **Group hosts** — the one person in every WhatsApp group who ends up compiling
  the order (flatmates, hostel floors, 6–10 person Friday plans). The buyer of the
  pain.
- **Group guests** — join by link, no signup, no app install.
- **Phase 2: corporate admins / team leads** — recurring team lunches with a
  per-head budget.
- **Swiggy** — not a paying customer in Phase 1, but the party the value accrues
  to. Stated explicitly on the canvas so the business case is unambiguous.

## 2. Value Propositions

- **For hosts:** removes the coordination tax. One message → one shared cart →
  host-controlled checkout. No screenshots, no manual tallying, no chasing.
- **For guests:** edit your own items on a link. No app, no account.
- **For Swiggy:** higher AOV on its highest-value order type; cross-vertical
  consolidation (Food + Instamart in one plan) that the visual consumer app can't
  easily do; lower group-cart abandonment; a WhatsApp-native acquisition surface
  reaching users where the plan is actually born.
- **For companies (Phase 2):** consolidated team lunch, per-head budgets enforced
  before spend, zero spreadsheets.

## 3. Channels

- **WhatsApp Business number** — the primary surface. The product lives where the
  group already is.
- **Host-forwarded share link** — the growth loop. Every session puts EasyOrder in
  front of a whole group at zero acquisition cost.
- **PWA planning canvas** — the visual surface for editing and checkout.
- **Swiggy checkout via OAuth** — the transaction always completes on Swiggy.
- **Phase 6: Slack / Microsoft Teams** — the same flow for corporate workspaces.

## 4. Customer Relationships

- **Conversational self-serve** — no onboarding, no tutorial; the first message is
  the first order.
- **Host-mediated trust** — the host owns the session and the checkout; guests hold
  scoped tokens and can never check out. Trust boundary is a product feature, not
  just a security control.
- **Recurring memory** — saved household/event lists turn repeat intent into a
  reviewable cart.
- **Never autonomous** — nothing is ordered or charged without an explicit human
  yes. The budget gate is the visible proof of that promise.

## 5. Revenue Streams

- **Phase 1 — none, by design.** Free consumer tool. Return to Swiggy is GMV and
  AOV uplift; the commercial shape is partner funding or rev-share, not a consumer
  charge.
- **Phase 2 — B2B SaaS subscription.** Per-company/per-seat pricing for corporate
  team-lunch coordination (budgets, consolidated delivery, Slack/Teams).
- **Phase 3 — occasion service fee.** Premium fee on full event planning: food,
  groceries, and Dineout bookings in one plan.
- **Adjacent (optional) —** sponsored placement in the discovery/offers intent,
  only if it can be done without polluting a recommendation the user trusts.

## 6. Key Activities

- Agentic orchestration: routing, intent parsing, guardrails, worker fan-out.
- MCP integration with Swiggy Food and Instamart; keeping the client honest against
  a real provider endpoint when partner access lands.
- Real-time collaborative session state (chat → canvas handoff, live cart sync).
- Scheduling and reliability: the background placer, degraded-vertical handling.
- WhatsApp Business policy compliance and data-retention/erasure operations.

## 7. Key Resources

- **The agent harness** — LangGraph state machine, input/output guardrails, the
  deterministic fallback parser. This is the actual IP.
- **The MCP client layer** — provider-agnostic; swapping the mock for a real Swiggy
  endpoint is a URL and a token.
- **Session/cart state store** — Postgres, with the host/guest token model.
- **WhatsApp Business account and message templates.**
- **The skill-driven build harness** — a locked skill set (`skills-lock.json`) that
  produced the PRD, HLD/LLD, ADRs, runbooks and tests. It's why one person ships at
  this scope; that's a resource, not a footnote.

## 8. Key Partners

- **Swiggy** — Food, Instamart, OAuth, checkout; eventually the MCP endpoint itself.
  The dependency is real and should be named honestly on the canvas.
- **Meta / WhatsApp Business Platform** — the delivery channel.
- **LLM provider** — a model ladder (local → free tier → production) so cost and
  vendor risk both stay controllable.
- **Infrastructure** — Postgres/Supabase, container hosting.
- **Phase 5: Dineout venues** for the occasion planner.

## 9. Cost Structure

- **LLM inference per message** — the dominant variable cost, deliberately
  suppressed: a deterministic router answers non-order messages with no model call,
  and a regex parser is the fallback path.
- **WhatsApp conversation fees** — Meta's per-conversation pricing; scales with
  active sessions, not with group size, since replies go to the host.
- **Infrastructure** — modest; the workload is bursty and small per session.
- **Compliance and legal** — privacy policy, ToS, retention jobs.
- **Build cost** — one engineer plus an agentic toolchain.

---

## Before you put this on screen

Two numbers make this canvas land, and neither should be invented:

1. **AOV delta** — group cart vs. solo cart. If you don't have real data, label the
   block *"hypothesis to validate in Phase 1"* rather than printing a number. Judges
   punish invented figures far harder than honest gaps.
2. **Cost per session** — you *can* state this structurally without measurement:
   one LLM parse plus the WhatsApp conversations for a session. Say the shape, not
   a rupee figure, unless you've metered it.

The slide at `docs/assets/business-model-canvas.html` is already written this way —
claims where there's evidence, labelled hypotheses where there isn't.
