# EasyOrder promo voiceover script

*Swiggy Builders Program submission. Target runtime: **1:52–2:00** — hard cap 2:00.*

Written for an AI voice agent to read aloud over a screen recording of the real app.
Two cuts below: the **2-minute primary** (three use cases + architecture + business model)
and a **60-second** version for platforms that cap submissions at a minute. Pick one per
recording — don't mix.

Companion docs:
- `docs/prompts/demo.md` — the longer (~3:00) comedic *Tale of Two Rohans* sketch. Same
  three use cases, so B-roll is interchangeable; opposite register.
- `docs/business-model-canvas.md` — source of truth for beat 6.
- `docs/user-profile-agent.md` — the design behind the roadmap line that closes beat 5.
  Not implemented; see the honesty rule for how it must be labelled on screen.
- `docs/assets/business-model-canvas.html` — the slide you actually put on screen.

> **On the budget.** Beats 5 and 6 (architecture, business model) take 46 seconds of a
> 120-second video, and the product beats carry the rest at roughly one point each. That's
> the
> right trade for a judged submission: the demo proves it works, the architecture proves
> you can build, the canvas proves you know why anyone should pay for it. If your
> platform allows 2:30, use the **extended alternates** given under beats 5 and 6 rather
> than padding the product beats back out.

---

## Before you record (5 minutes, saves the take)

Env drift has burned this demo before — a `.env` left in `mcp` mode with no MCP server
running yields a silently empty cart mid-recording (see `docs/runbooks/local-demo.md`).

```bash
grep -E "^SWIGGY_CLIENT_MODE|^LLM_MODE|^WHATSAPP_PROVIDER_MODE" src/backend/.env
```

- Safe demo config: `SWIGGY_CLIENT_MODE=mock`, `LLM_MODE=mock`.
- Prove the golden path is alive right before you hit record:

```bash
make demo-smoke
```

- Then bring the stack up: `make up` (or `make db-up` / `make backend-dev` / `make frontend-dev`).
- Do one full dry run of all three prompts. Confirm the reply text matches what's
  scripted below, *then* record the take you keep.
- Record WhatsApp **Web** in a clean browser window, not a phone camera — crisp text
  matters more than authenticity here.
- **Log in to the PWA by OTP before you record.** Beat 4 needs `/orders/live` and
  `/orders` already open; an OTP round-trip on camera is dead air.
- **Open the guest link in an incognito window** for the beat 2 split — same browser
  profile in two tabs shares cookies and quietly defeats the point of the shot.
- Open the BMC slide full-screen ahead of time so beat 6 is one window switch, not a
  file hunt:

```bash
open docs/assets/business-model-canvas.html
```

---

## 2-minute version

### Shot list

Record in this order. Voiceover timings below are cut to match.

| # | Time | Screen | On-screen text overlay |
|---|---|---|---|
| 1 | 0:00–0:11 | Home page (`/`) — hero *"Craft Your Feast, Together"*, one quick scroll through **How It Works** | — |
| 2 | 0:11–0:31 | WhatsApp Web: group-order prompt → reply carrying **both** links → forward the guest link into a real group → cut to the PWA. **Two windows side by side** (normal + incognito): host view left, guest view right. Guest bumps a quantity; it updates on the host's screen. Then pan the host's **Check out** control and land on the guest window, where it isn't there. | `Host link · private` / `Guest link · shared` then `Guests edit. Only the host checks out.` |
| 3 | 0:31–0:43 | WhatsApp: MotiMahal prompt with the budget gate → reply naming the total and asking YES/NO → `yes` as a **separate** message → `Placed!` | `Nothing is placed until you say yes` |
| 4 | 0:43–1:01 | WhatsApp: BiryaniByKilo "reach by 8 PM" → `Scheduled —…` → jump-cut (caption `Meanwhile…`) to `/orders/live`: **Scheduled** tab with its count, then the flip to **Ongoing** with the `Placed!` notification in the same shot → quick cut to `/orders` (My orders), landing on the **Total spent** panel | `Scheduled / Ongoing / Historical`, then `Placed 7:31 PM. You were in a meeting.`, then `Total spent · lifetime, not this page` |
| 5 | 1:01–1:41 | **Architecture**, closing on the roadmap card — see the detailed sub-shot list below | Callouts timed to the read; the last one **must** read `NEXT — not shipped yet` |
| 6 | 1:41–1:53 | **Business Model Canvas** — `docs/assets/business-model-canvas.html` full-screen | `Phase 1 monetizes nobody` |
| 7 | 1:53–2:00 | Back to home page / logo, end card held under the closing line | End card (below) |

### Voiceover script

**[0:00–0:11] — Hook (home page)**
> Every group order starts the same way. Forty messages, three menus, one person doing
> arithmetic they never volunteered for. That person is the coordination tax.

**[0:11–0:31] — Group ordering + host and guest (WhatsApp → PWA)**
> One message. EasyOrder searches Swiggy Food and Instamart at once and hands back two
> links — a private one for the host, a shared one for everyone else. Guests add and edit
> their own items, live; only the host can check out.

**[0:31–0:43] — Named restaurant + budget gate**
> It comes back at eight seventy-eight — over the eight hundred you set — and then it
> stops. Nothing is placed until you reply yes.

**[0:43–1:01] — Scheduled delivery + the host's orders page**
> Or order for later. It works backwards from the delivery time and places it at the right
> moment. The host's page holds the record — what's scheduled, what's on its way, what's
> delivered, and what it has all cost.

**[1:01–1:41] — Under the hood (architecture, closing on what's next)**
> Underneath: a deterministic router runs first, so "hi" never costs a model call. Real
> orders enter a LangGraph state machine. The model does one job — a sentence into a
> strict JSON schema — with a deterministic parser standing by. Food and Instamart run
> concurrently over MCP, Swiggy's own protocol. A slow vertical degrades. It doesn't fail.
> Built the way it runs: agent-first, from a locked skill set. Next: a profile builder
> that reads your order history at onboarding, so "the usual" finally means something.

**[1:41–1:53] — Business model**
> Free for the group, because the value lands on Swiggy — bigger carts, fewer abandoned
> ones. Revenue starts in Phase two: corporate lunches, on subscription.

**[1:53–2:00] — Close**
> Group orders are Swiggy's biggest carts. Coordination is what kills them. EasyOrder
> takes it off the table.

### End card (not narrated — text overlay, held ~4s)

```
EasyOrder
WhatsApp-first group ordering, checked out on Swiggy.

Built for the Swiggy Builders Program.
```

### Word count / timing check

258 spoken words, by beat:

| Beat | Words | @140 wpm |
|---|---|---|
| 1 Hook | 25 | 11s |
| 2 Group order + host/guest | 42 | 18s |
| 3 Budget gate | 25 | 11s |
| 4 Scheduled + orders page | 39 | 17s |
| 5 Architecture + roadmap | 85 | 36s |
| 6 Business model | 25 | 11s |
| 7 Close | 17 | 7s |
| **Total** | **258** | **111s (1:51)** |

- At 150 wpm → **103s (1:43)**
- At 140 wpm → **111s (1:51)**
- At 130 wpm → **119s (1:59)**

This cut is **deliberately tighter than the 60-second one** — architecture and business
model don't compress. At 140 wpm you have ~9 seconds of slack for the six beat-boundary
pauses, and the end card holds *under* the closing line rather than after it. **Read at
140–150 wpm. At 130 you have zero pause budget and will breach 2:00.**

If your generated track comes in long, cut in this order — each is written to be
droppable without breaking the argument:

1. *"and what it has all cost"* (beat 4, −6 words) — the spend panel is legible on screen.
2. *"with a deterministic parser standing by"* (beat 5, −6 words) — it survives as a callout.
3. *"so 'the usual' finally means something"* (beat 5, −6 words) — keeps the roadmap beat,
   drops its punchline. Cut the joke before you cut the fact.

Do **not** cut *"only the host can check out"* (beat 2), the skills clause, or *"It
doesn't fail"* (beat 5). Those are the three lines this cut exists to deliver: the trust
boundary, the build story, and the resilience story.

---

## Beats 2 & 4 in detail — the PWA, and who's allowed to do what

The two-role split is the most under-sold thing in the product: it's a real
authorization boundary, not a UI toggle, and it's the answer to the obvious judge
question *"so anyone with the link can spend the host's money?"* Show it, don't assert it.

### Recording the host/guest split (beat 2)

1. Open the **host link** (the private one from the WhatsApp reply) in a normal window.
2. Open the **guest link** (the shared one) in an **incognito/private window** — different
   cookie jar, so it's genuinely a different visitor, not the same session in two tabs.
3. Size them side by side, host left, guest right. Record both in one frame.
4. On the guest side, bump an item quantity. It appears on the host side. That single
   move proves collaboration is real and nothing is faked.
5. Pan to the host's **Check out** control, then across to the same spot in the guest
   window, where it isn't there. Hold for a beat. That's the whole trust story in one
   camera move, with no narration needed beyond *"only the host can check out."*

> Optional, and very strong if you have five spare seconds in an extended cut: paste the
> **guest** token into the host-only checkout call and show the `403`. Or just run
> `make security-smoke` on camera — `guest_checkout_blocked` and `guest_confirm_blocked`
> scroll past as named, passing checks. It's a release blocker in this repo, not a claim.

### Recording the orders surfaces (beat 4)

Both need an OTP login first — do that before recording, not on camera.

- **`/orders/live`** — Scheduled / Ongoing / Historical, each tab showing its **count**.
  This is where the scheduled biryani visibly moves from one bucket to the next when the
  background scheduler fires. Time the take so that flip happens on camera; that
  transition is the proof the scheduler is real.
- **`/orders`** ("My orders") — past planning sessions with date, item count and total,
  plus a review link back into each cart.

### What's true today, and what isn't

Two things you asked to show don't exist in the code yet. Both are small, but neither
should be narrated until it does — a judge who opens the repo will check.

| Claim | Status |
|---|---|
| Host / guest split access | **Real.** Host token vs. guest token; guest bootstrap redacts the host token; guest checkout and confirm both `403`. Verified in `make security-smoke`. |
| Pending + historical orders in the PWA | **Real.** `/orders/live` buckets by status, `/orders` lists past sessions. Per-order totals shown on both. |
| Aggregate total spend | **Real.** `GET /api/me/spend` returns lifetime spend split by surface; the panel sits above both listings. Counts committed money only — an ORDERED session and a PLACED or DELIVERED order — so a cart still being planned and an order still scheduled contribute nothing. |
| Order history read from EasyOrder's own database | **Real, and deliberate.** These are orders placed *through* EasyOrder, so the record is already local. MCP is how items get searched and carts get placed; asking Swiggy for history back would be a slower, costlier route to a number we already hold. Say this if a judge asks — it's an architecture decision, not a missing integration. |

**Two things the spend panel is careful about**, worth a beat of narration if you're asked:

- It is a **lifetime** total, aggregated in SQL, not a sum of the rows on screen — the
  listings are paginated, so summing them would quietly under-report.
- **Scheduled ≠ spent.** In the demo the scheduled BiryaniByKilo order is visible on the
  page and *excluded* from the total until the scheduler actually places it. If your take
  catches the bucket flip from Scheduled to Ongoing, the total moves in the same shot —
  that's the single best frame available for the whole orders surface. Worth staging.

---

## Beat 5 in detail — the architecture read

This is the beat that earns the technical points, so it gets its own shot list. Thirty
seconds, four visuals, callouts landing on the clause that names them.

### Sub-shot list

| Time | Screen | Callout overlay | Lands on the words |
|---|---|---|---|
| 1:01–1:07 | `docs/diagrams/03-agentic-framework-architecture.png`, full-frame | `Router → intent families (no LLM call)` | *"a deterministic router runs first"* |
| 1:07–1:18 | Same diagram; slow push-in on the graph nodes. Or, better, the rendered state machine from `docs/hld.md` §3.1 (GitHub renders the Mermaid — screenshot it beforehand). | `LangGraph: guardrails → intent → workers → guardrails → persist` then `LLM → strict JSON schema · deterministic fallback` | *"LangGraph state machine"* … *"strict JSON schema"* |
| 1:18–1:28 | `docs/diagrams/01-high-level-architecture.png` — or split-screen the `services/mock-swiggy-mcp` terminal showing live `POST /mcp` lines, which is far more convincing than a static box | `MCP · Food ∥ Instamart · 2.5s each · degrade, don't fail` | *"concurrently over MCP"* |
| 1:28–1:34 | Quick pan over the repo docs tree — `docs/` (PRD, HLD, LLD, `adr/`, `runbooks/`) — then `skills-lock.json` | `60+ locked skills · PRD → HLD/LLD → ADRs → tests` | *"agent-first, from a locked skill set"* |
| 1:34–1:41 | **Roadmap card.** A still frame, visibly different from the live-product footage — put it on the BMC slide's dark palette so it reads as "deck", not "app". Show the graph again with one greyed-out node appended: `profile_defaults`. | `NEXT — not shipped yet` (top-left, held for the whole card) plus `onboarding → order history → typical budget · favourites · rhythm → defaults you can override` | *"Next: a profile builder…"* |

> The `POST /mcp` terminal is the single most persuasive frame in the whole video: it's
> live protocol traffic, not a diagram of intent. If you show it, run
> `make mock-mcp-up` in a visible terminal and set `SWIGGY_CLIENT_MODE=mcp` for that
> take only — then put `.env` back to `mock` before recording anything else.

### The agentic story, in the order the code actually runs

Every claim below is defensible from a file you can open in a Q&A. Don't say anything
here that isn't on this list.

| Stage | What it does | Where it lives |
|---|---|---|
| **Router** | Classifies each business-chat message into intent families — start session, targeted order, order history, saved lists, share, discovery, privacy/delete, unsupported — with regex, *before* any model call. Cheap paths stay cheap. | `src/backend/app/services/intent_router.py` |
| **Input guardrails** | Rejects prompt-injection patterns; masks emails, phone numbers, card numbers *before* text reaches the LLM. | `agent.py` — `InputGuardrails` |
| **LLM (narrow role)** | One structured-extraction call: `response_format={"type":"json_schema"}` → budget, headcount, food/grocery keywords, dietary tag. A second parser handles targeted orders (restaurant, dishes, budget gate, deadline). Any exception falls back to the deterministic regex parser, so an LLM outage degrades instead of breaking. | `services/llm_intent.py` (schema at `:130`, fallback at `:119`) |
| **Orchestrator + workers** | Food and Instamart searches dispatched concurrently via `asyncio.gather`, each wrapped in `asyncio.wait_for(2.5s)`. Timeout or failure returns a `VERTICAL_TIMEOUT` / `VERTICAL_FAILED` warning and partial results — the session goes DEGRADED, never blank. | `agent.py:346–405`, `WORKER_TIMEOUT_SECONDS = 2.5` |
| **MCP** | A real MCP client — official `mcp` SDK over Streamable HTTP — calling `search_restaurants`, `get_restaurant_menu`, `search_instamart`, `create_cart`, `place_order`. The provider behind it is swappable: mock server today, Swiggy's endpoint the day partner access lands. | `services/swiggy_mcp.py`, `services/mock-swiggy-mcp/` |
| **Output guardrails** | Budget soft-check (warn, don't reject — the group trims it themselves), dietary tag validation, placeholder/mock-item filter, source-attribution check. Runs before anything is persisted. | `agent.py:420–441` |
| **State handoff** | Session + cart persisted to Postgres; host gets a private link, guests get scoped tokens. Chat state becomes canvas state. | `api/session.py`, `services/web_auth.py` |
| **Two-role authorization** | `authorize_session_role` resolves the token to HOST or GUEST on every call. Checkout validation, cart confirm and OAuth are host-only (`403` otherwise); the guest bootstrap payload never contains the host token; cross-session tokens are rejected. | `api/session.py:76–163`, `scripts/easyorder_security_smoke.py:147–207` |
| **Account surfaces** | OTP login, then `/orders` (past sessions, item counts, totals) and `/orders/live` (Scheduled / Ongoing / Historical, bucketed by order status with counts). Served from EasyOrder's own record — see the accuracy table above before claiming MCP here. | `api/account.py:161–205`, `LiveOrdersPage.tsx` |
| **Scheduler** | Background poller places scheduled orders at `target_placement_at` (deadline minus the restaurant's ETA) and notifies on WhatsApp. | `services/order_scheduler.py` |
| **Skills (build-time)** | 60+ locked skills (`skills-lock.json`, `agent/skills/`, `docs/prompts/skill-lookup-table.md`) drove the pipeline: `/to-prd` → `/create-hld-lld` → `/decision-mapping` (ADRs) → `/implement` → `/review` → `/qa`. The PRD, HLD, LLD, seven ADRs and the runbooks on screen are all outputs of that harness. | repo root |

### Three things not to say on camera

- **"Three workers."** The HLD's diagram shows Food / Instamart / Budget workers, but the
  shipped code fans out **two** concurrent workers and does the budget math inside the
  output-guardrail node. Say "Food and Instamart run concurrently" — it's true, and it's
  what the code does. A judge who opens `agent.py` should find exactly what you claimed.
- **Any latency number.** `2.5s` is a *timeout*, not a measured response time. "Two and a
  half seconds each" as a budget is accurate (it's in the callout overlay, not the read);
  "sub-two-second responses" is not, unless you've metered the take you're shipping.
- **"Order history from Swiggy's MCP server."** The orders pages read EasyOrder's own
  Postgres, by design — see the accuracy table under *Beats 2 & 4*. MCP is how items are
  searched and carts are placed, not how history is read.

### Extended alternate (only if your cap is 2:30)

Adds ~19s. Replaces everything after *"It doesn't fail."*:

> Nothing here is autonomous, by the way. The agent recommends, compiles and schedules —
> a human always says yes before money moves. That's a design rule, not a missing feature.
> And it was built the way it runs: agent-first, from a locked skill set — the PRD, the
> design docs and the ADRs on screen all came out of that same harness. Next on that
> graph: a profile builder that reads your order history at onboarding and learns your
> defaults — your usual budget, your regular places, when you actually eat — so "the
> usual" finally means something. Defaults you can always override, on a graph that still
> asks before it spends.

The last clause matters more in this version than in the 2:00 cut: you've just spent a
sentence on "nothing is autonomous," so the personalization line has to land as *better
defaults*, not as an agent that decides for you. Those two ideas are one beat apart, and
a judge will notice if they contradict.

Gives beat 5 ~55 seconds (1:01–1:56) and pushes the total to about 2:15 — or about 2:25
with the canvas extension below as well. Only use these if your platform's cap is
genuinely 2:30.

---

## Beat 6 in detail — the Business Model Canvas

Full-screen `docs/assets/business-model-canvas.html` (16:9, dark, matches the app's
palette — it will cut cleanly against the product footage). Content and reasoning:
`docs/business-model-canvas.md`.

**Camera move:** hold the full canvas for ~3 seconds so the shape registers, then a slow
push-in that ends framed on **Value Propositions** and **Revenue Streams**. Don't try to
make nine blocks readable — the voiceover names three of them, and the rest is texture
that says "this was thought about."

**Highlight order, timed to the read:**

| Words | Block to be framed / highlighted |
|---|---|
| *"Free for the group"* | Revenue Streams — `Phase 1: none, by design` |
| *"the value lands on Swiggy"* | Value Propositions — the Swiggy bullet |
| *"Revenue starts in Phase two"* | Revenue Streams — the B2B SaaS line |

The one line the canvas exists to deliver is already burned into its footer:
**"EasyOrder never charges the group. Swiggy captures the cart."** If a judge remembers
one business fact, make it that one.

**Honesty note:** the AOV-uplift bullet is tagged `hypothesis to validate` on the slide
on purpose. If you have real data by submission time, replace the tag with the number. If
you don't, leave the tag — an unlabelled invented figure is the fastest way to lose a
technically strong judge.

### Extended alternate (only if your cap is 2:30)

Adds ~10s. Replaces the beat-6 read:

> The model, in one frame. Free for the group, because the value lands on Swiggy — bigger
> carts, two verticals in one plan, fewer abandoned coordinations. Revenue starts in Phase
> two, where it belongs: companies paying a subscription for team-lunch coordination, and
> later, a service fee on full occasion planning. One rule holds it together — EasyOrder
> never charges the group. Swiggy captures the cart.

---

## 60-second version

Same hook, then use cases 1 and 3 only. **The architecture and canvas beats are cut
entirely** — thirty seconds of architecture cannot be compressed into six without
becoming buzzwords, and a nine-block canvas held for four seconds reads as clutter. If
you only have 60 seconds, spend them proving the product works and link the architecture
doc in the description.

### Shot list

1. **0:00–0:12** — Home page hero, quick scroll.
2. **0:12–0:32** — WhatsApp group-order prompt → reply with link → session page: split
   cart, budget bar, host/guest. Zoom the total.
3. **0:32–0:48** — WhatsApp scheduled prompt → `Scheduled` reply → jump-cut to
   `/orders/live` flipping Scheduled → Ongoing with the `Placed!` notification.
4. **0:48–0:58** — Home / logo, end card.

### Voiceover script

**[0:00–0:12] — Hook**
> Every group order starts the same way. Forty messages, three menus, one person doing
> arithmetic they never volunteered for. EasyOrder replaces that person.

**[0:12–0:32] — Group ordering**
> One message, in the group's own language. EasyOrder reads the budget, the headcount and
> the preferences, searches Swiggy Food and Instamart together, and returns one shareable
> link. Everyone edits their own items, live — and it asks before it spends over your
> limit.

**[0:32–0:48] — Scheduled delivery**
> Order for later and it works backwards from the delivery time, placing it at exactly
> the right moment. Scheduled, ongoing, delivered — while you were in a meeting.

**[0:48–0:58] — Close**
> Group orders are Swiggy's biggest carts. Coordination is what kills them. EasyOrder
> takes it off the table.

### Word count / timing check

111 spoken words:
- At 150 wpm → **44s**
- At 140 wpm → **48s**
- At 130 wpm → **51s**

Fits under 60s with 7–14 seconds for transitions and the end-card hold.

---

## Exact prompts to send on camera

Use these verbatim — they are the three verified use cases from
`docs/runbooks/local-demo.md`, and the numbers in the voiceover match them.

1. **Group order** (or the `whatsapp-tagged-normal.json` fixture, if you're driving the
   webhook by `curl` off-camera):
   > `2 chicken biryani, 1 mixed veg and 3 tandoori roti from the best restaurant under 2000 INR`

2. **Named restaurant + budget gate** — then `yes` as a **separate** message:
   > `Order paneer tikka and chicken 65 from MotiMahal restaurant and if the budget exceeds INR 800, let me know before placing the order`

   ⚠️ Check the gate actually trips before recording. If the current menu totals under
   ₹800 the confirmation never fires and the beat dies on camera — lower the number in
   the prompt until it trips, and re-record the voiceover line with the matching figures.
   The script above says "eight seventy-eight, over the eight hundred you set."

3. **Scheduled delivery**:
   > `Order Egg Biryani for me from BiryaniByKilo and it should reach by 8PM`

   Deadlines are interpreted as UTC, not IST. Pick a target time that lands correctly in
   your recording session, or pre-record the fire and cut to it.

---

## Honesty guardrails

Judges will assume anything unlabelled is real. Keep these true on screen:

- The product beats run with the **mock Swiggy client** and the **mock LLM parser**. A
  small overlay on the architecture beat — `Mock Swiggy MCP server (real MCP protocol)` —
  costs you nothing and buys credibility.
- "Swiggy's own protocol surface" is a claim about MCP, and it's accurate: the client is
  a genuine MCP client speaking to a genuine MCP server. What's mocked is the *provider*,
  not the plumbing. If you'd rather not thread that needle live, use: *"over MCP — a mock
  Swiggy endpoint today, a real one the day partner access lands."* (+9 words; at 140 wpm
  that still fits inside 2:00.)
- No invented metrics: no latency figure, no AOV number, no user count. The canvas is
  already labelled for this.
- **The roadmap line in beat 5 describes something that does not exist yet.** It is the
  only unbuilt thing narrated anywhere in this script, and it is safe *only* because the
  word "Next" and the `NEXT — not shipped yet` overlay run together. Both, or neither:
  - Keep the overlay up for the whole card, not a flash at the start.
  - Keep the visual obviously a *card*, not app footage. Everything before it in this
    video is real; a roadmap frame that looks like a screenshot retroactively makes a
    judge doubt the parts that were real.
  - Say "Next", not "we have" or "it learns". Present tense is a claim.
  - Design lives in `docs/user-profile-agent.md` — worth linking in the description, and
    worth having open if anyone asks how it would work.

---

## Delivery notes for the AI voice agent (both versions)

- **Tone**: dry and confident — a senior engineer demoing to peers, not an ad announcer.
  The humor is in the writing, so read the jokes *straight*. "Arithmetic they never
  volunteered for" and "so 'hi' never costs a model call" are throwaways, not punchlines;
  landing on them too hard kills them. No exclamation points.
- **Pace**: 140 wpm. This cut has less slack than the 60-second one — see the timing note
  above before slowing down.
- **Register shift at 1:06**: the architecture beat should sound *flatter* and more
  matter-of-fact than the product beats, not more excited. Technical confidence reads as
  calm. Then lift slightly again for the canvas and the close.
- **Emphasis**: land on **"coordination tax"** in the hook and **"coordination"** in the
  close — that's the through-line and the callback. Hit **"and then it stops"** in the
  budget beat, **"It doesn't fail"** in the architecture beat, and **"the value lands on
  Swiggy"** in the canvas beat.
- **Pauses**: a half-beat at every beat boundary — those are the cuts. A full beat after
  "and then it stops," after "while you were in a meeting," and after "It doesn't fail."
- **Numbers and initialisms**: read prices as words ("eight seventy-eight"), not
  "INR 878." Read **MCP** as three letters, and **LangGraph** as one word — check the
  TTS pronunciation of both before you commit to a take.

## Production notes

- **Recording**: QuickTime (`File → New Screen Recording`) is enough. OBS if you want
  WhatsApp Web and `/orders/live` in one frame for beat 4, or the diagram and the live
  `POST /mcp` terminal side by side for beat 5.
- **Voice**: ElevenLabs or Murf. Generate the voice track *first*, then cut the video to
  it — trimming silence is easy, stretching a read is not.
- **Edit**: CapCut (free, good auto-captions — many judges watch muted) or DaVinci
  Resolve. Burn in the overlay text from the shot lists verbatim; it's written short on
  purpose, don't paraphrase it into narration.
- **Music**: light instrumental bed under beats 1 and 7 only. Drop it out for the product
  beats (2–4) so the real app reads as grounded, and keep it out of the architecture beat
  (5) — silence there reads as substance.
- **Diagram legibility**: the three PNGs in `docs/diagrams/` were drawn for a document,
  not a 1080p video frame. Check each one full-screen before you commit; if the labels
  are unreadable, crop to the region the callout names instead of showing the whole
  diagram shrunk to fit.
- **B-roll option**: the in-app animated walkthrough at `/demo` (three scenes: house
  party, budget bouncer, scheduled dinner) is a clean visual for the hook and the close.
  Keep the *evidence* beats (2–4) on real WhatsApp and the real PWA — an animation can't
  do that job.
