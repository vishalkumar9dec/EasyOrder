# ADR 0005: Host-Mediated Group Flow (No WhatsApp Group Bot)

## Status

Accepted

## Context

Early product framing implied EasyOrder could participate in consumer WhatsApp
group chats: members tag `@EasyOrder` in their group, and the bot responds
there. Meta's WhatsApp Business Cloud API does not support this — a business
phone number cannot be added to consumer groups, and no webhooks are delivered
for group conversations. There is no bot-in-group model on WhatsApp comparable
to Telegram or Slack.

At the same time, the `@EasyOrder` mention handling itself is nearly free to
keep: detection is one string check, and every subsystem built alongside it
(webhook ingestion, signature verification, guardrails, session creation,
short-link handoff, timeline, wamid dedup) is equally required by the dedicated
business chat (ADR 0004). The mention is also the only deterministic trigger:
the business-chat intent router is heuristic keyword matching and can misread
ambiguous messages, while a tagged message always creates a session with no
interpretation.

## Decision

1. **Group collaboration is host-mediated.** The production flow is:
   the group agrees informally in their own chat (EasyOrder absent) → the host
   messages the EasyOrder business number directly (tag optional) → EasyOrder
   replies with a private host link and a shareable guest short link → the host
   shares the guest link into the group → members collaborate in the PWA
   (realtime cart, timeline) → the host checks out.
2. **The `@EasyOrder` mention path stays**, as the deterministic
   start-a-session override inside the direct chat, for forwarded messages that
   carry the tag, and as readiness if Meta ever ships group APIs. It is not a
   group mechanism today and documentation must not describe it as one.
3. **Mock "group" constructs are local simulation only.** The
   `group_ipl_fans_1` fixture id, the mock sender's group channel, and the
   `sessions.whatsapp_group_id` column exercise the mention flow and privacy
   assertions locally. They are not production surfaces and are kept to avoid
   breaking working code and tests; live Meta mode routes replies by the
   inbound sender `wa_id`.

## Consequences

- Product copy, PRD user stories, and demos describe "one person summons
  EasyOrder, the group joins through the link" — never a bot inside the group.
- The `Share with group` handoff affordance is the bridge between WhatsApp and
  the collaborative PWA session, and deserves first-class UX attention.
- Proactive messages to users outside Meta's 24-hour customer-service window
  require approved templates (see whatsapp-handoff-templates runbook).
- No code removal: mention handling, mock group simulation, and the
  `whatsapp_group_id` column remain; all existing use cases execute unchanged.
- If Meta later exposes group messaging, mention-triggered planning can extend
  to real groups behind explicit user action and a reviewed privacy model
  (ADR 0003, ADR 0004).
