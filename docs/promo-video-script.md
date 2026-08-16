# EasyOrder promo voiceover script

*Swiggy Builders Program submission. Target runtime: **2:20–2:24**.*

Written for an AI voice agent to read aloud over a screen recording of the real app, after
a single sketch shot that states the problem before the product answers it.
Two cuts below: the **primary** (four product beats + architecture + business model)
and a **60-second** version for platforms that cap submissions at a minute. Pick one per
recording — don't mix.

Companion docs:
- `docs/prompts/demo.md` — the full (~3:00) comedic *Tale of Two Rohans* sketch. This cut
  borrows its **cold open, its hinge card and its before/after captions** and leaves the
  rest; that doc also holds the production guide for generating the character shot.
  Note its Part 2 live-demo section predates host/guest, spend, onboarding, the profile,
  the architecture beat and the canvas — this script is the source of truth for what the
  live demo shows.
- `docs/business-model-canvas.md` — source of truth for beat 7.
- `docs/user-profile-agent.md` — the design behind beat 6, including what the profile
  deliberately does *not* do yet.
- `docs/assets/business-model-canvas.html` — the slide you actually put on screen.

> **On the runtime.** This cut runs **2:24**. The cold open costs only ~3 seconds net,
> because it replaces the narrated hook rather than adding to it — the sketch *shows* the
> coordination tax in the time the narration used to spend *asserting* it. The rest of the
> growth is beat 6, which expanded when personalization shipped and again when onboarding
> joined it; that arc is the strongest thing in the video and does not compress into a
> sentence.
>
> **Three documented ways back down**, in the order I'd take them:
>
> 1. **−14s:** drop the cold open and restore the old narrated hook (it is preserved
>    below the voiceover script). Do this if the character shot doesn't come out well —
>    a mediocre AI clip costs more credibility than the beat buys. Lands at ~2:10.
> 2. **−9s:** drop the onboarding half of beat 6 (its first two sentences and sub-shots
>    a–b), leaving the learned-behaviour demo. Lands at ~2:15.
> 3. **−23s:** also cut beat 3 (the budget gate) and renumber. It is the most expendable
>    of the product beats *only* because beat 6 now makes the same point — your explicit
>    instruction always wins — and the `Placed!` confirmation still appears in beat 4.
>
> Nothing else in this cut is redundant with anything else.

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
- **Beat 6 needs two WhatsApp numbers** — one with no history at all for the onboarding
  shots, one with three or more orders for the learned ones. This is the only prep in the
  whole script you cannot do at the last minute.
- **Work the take from the [message sheet](#message-sheet--what-to-type-in-order)** — every
  message in send order, the reply each must produce, and the voiceover line it plays
  under. Its pre-record table is the seeding you must finish *before* rolling.
- **Open the guest link in an incognito window** for the beat 2 split — same browser
  profile in two tabs shares cookies and quietly defeats the point of the shot.
- Open the BMC slide full-screen ahead of time so beat 6 is one window switch, not a
  file hunt:

```bash
open docs/assets/business-model-canvas.html
```

---

## Primary cut (2:24)

### Shot list

Record in this order. Voiceover timings below are cut to match.

| # | Time | Screen | On-screen text overlay |
|---|---|---|---|
| 1 | 0:00–0:14 | **Cold open — the one sketch shot.** Rohan to camera, mid-chaos: phone in one hand, calculator in the other, restaurant tabs behind him. He says his line (below), freeze-frame, title card, then the hinge card. No narrator over this. | `A Tale of Two Rohans` *(title card)* then, full frame, `No actors past this point. This is the real app.` |
| 2 | 0:14–0:34 | WhatsApp Web: group-order prompt → reply carrying **both** links → forward the guest link into a real group → cut to the PWA. **Two windows side by side** (normal + incognito): host view left, guest view right. Guest bumps a quantity; it updates on the host's screen. Then pan the host's **Check out** control and land on the guest window, where it isn't there. `14 minutes. 3 restaurant tabs. 1 minor breakdown.` → `11 seconds. 1 message.` *(before/after flash over the send)*, then `Host link · private` / `Guest link · shared`, then `Guests edit. Only the host checks out.` |
| 3 | 0:34–0:46 | WhatsApp: MotiMahal prompt with the budget gate → reply naming the total and asking YES/NO → `yes` as a **separate** message → `Placed!` `4 taps to find the dish. 1 tab-switch to check the balance.` → `1 message. Budget checked automatically.`, then `Nothing is placed until you say yes` |
| 4 | 0:46–1:04 | WhatsApp: BiryaniByKilo "reach by 8 PM" → `Scheduled —…` → jump-cut (caption `Meanwhile…`) to `/orders/live`: **Scheduled** tab with its count, then the flip to **Ongoing** with the `Placed!` notification in the same shot → quick cut to `/orders` (**Group plans**), landing on the **Total spent** panel | `Forgot to order. Ate noodles. Again.` → `Scheduled once. Arrived on time.`, then `Scheduled / Ongoing / Historical`, then `Total spent · lifetime, not this page` |
| 5 | 1:04–1:35 | **Architecture** — see the detailed sub-shot list below | Callouts, timed to the read |
| 6 | 1:35–2:05 | **Onboarding → learning, live.** Four quick cuts: (a) a **fresh** WhatsApp number sends `hi` — show the whole onboarding reply, privacy line included; (b) `/orders` after one order — the greyed **Your usual** card reading *"2 more orders until EasyOrder starts using this"*; (c) the seasoned number sends just `get biryani`, and the reply discloses *"You didn't say, so I used your usual budget of INR 600 (from your last 3 orders)"*; (d) the same number sends `get biryani for 8 under 2500` — **no** disclosure line. End on the confident **Your usual** card. | `First message: what it is, what it stores` then `Learning · 2 more orders` then `You said 8 words. It filled the rest.` then `Your number always wins` |
| 7 | 2:05–2:17 | **Business Model Canvas** — `docs/assets/business-model-canvas.html` full-screen | `Phase 1 monetizes nobody` |
| 8 | 2:17–2:24 | Back to home page / logo, end card held under the closing line | End card (below) |

> **On the before/after overlays.** Beats 2–4 open with a paired flash — the without-
> EasyOrder cost, then the with-EasyOrder one — lifted from the *Two Rohans* sketch in
> `docs/prompts/demo.md`. They cost no speech time and carry the comedy the voiceover
> deliberately doesn't, which is what lets the read stay dry. Two lines, ~1.5s each, top
> of the beat, gone before the demo lands. Don't let them run over the evidence.

### Voiceover script

**[0:00–0:14] — Cold open (spoken in-shot by Rohan, not the narrator)**
> Every Friday, my friend group asks me the same three questions. "What's the food plan?"
> "Is it under budget?" And — my personal favourite — "Bro where's my biryani."

*Freeze. Title card. Hard cut to the hinge card, then straight into the app. The narrator
does not speak until 0:14 — the sketch has already made the argument.*

**[0:14–0:34] — Group ordering + host and guest (WhatsApp → PWA)**
> That's the coordination tax. One message removes it. EasyOrder searches Swiggy Food and
> Instamart at once and hands back two
> links — a private one for the host, a shared one for everyone else. Guests add and edit
> their own items, live; only the host can check out.

**[0:34–0:46] — Named restaurant + budget gate**
> It comes back at five eighty — over the four hundred you set — and then it stops.
> Nothing is placed until you reply yes.

**[0:46–1:04] — Scheduled delivery + the host's orders page**
> Or order for later. It works backwards from the delivery time and places it at the right
> moment. The host's page holds the record — what's scheduled, what's on its way, what's
> delivered, and what it has all cost.

**[1:04–1:35] — Under the hood (architecture)**
> Underneath: a deterministic router runs first, so "hi" never costs a model call. Real
> orders enter a LangGraph state machine. The model does one job — a sentence into a
> strict JSON schema — with a deterministic parser standing by. Food and Instamart run
> concurrently over MCP, Swiggy's own protocol. A slow vertical degrades. It doesn't fail.
> Built the way it runs: agent-first, from a locked skill set.

**[1:35–2:05] — Onboarding, and what it learns**
> It starts knowing nothing. Say hi, and the first reply tells you how to order,
> what it stores, and how to erase it — before you've given it anything. Then it watches.
> Three orders later it stops counting down and starts filling in what you leave out: your
> usual budget, the place you keep going back to. Name a number and your number wins.
> Either way, it says which.

**[2:05–2:17] — Business model**
> Free for the group, because the value lands on Swiggy — bigger carts, fewer abandoned
> ones. Revenue starts in Phase two: corporate lunches, on subscription.

**[2:17–2:24] — Close**
> Group orders are Swiggy's biggest carts. Coordination is what kills them. EasyOrder
> takes it off the table.

### Fallback hook (if you drop the cold open)

Restores beat 1 to 0:00–0:11 over the home page hero, with the narrator opening the video.
Beat 2 then loses its first two sentences ("That's the coordination tax. One message
removes it.") and starts at "EasyOrder searches…".

> Every group order starts the same way. Forty messages, three menus, one person doing
> arithmetic they never volunteered for. That person is the coordination tax.

### End card (not narrated — text overlay, held ~4s)

```
EasyOrder
WhatsApp-first group ordering, checked out on Swiggy.

Built for the Swiggy Builders Program.
```

### Word count / timing check

291 narrated words, plus 29 spoken in-shot by Rohan:

| Beat | Words | @140 wpm |
|---|---|---|
| 1 Cold open *(in-shot dialogue)* | 29 | ~14s incl. freeze + cards |
| 2 Group order + host/guest | 48 | 21s |
| 3 Budget gate | 25 | 11s |
| 4 Scheduled + orders page | 39 | 17s |
| 5 Architecture | 68 | 29s |
| 6 Onboarding + learning | 69 | 30s |
| 7 Business model | 25 | 11s |
| 8 Close | 17 | 7s |
| **Total narrated** | **291** | **125s (2:05)** |

- At 150 wpm → **116s (1:56)**
- At 140 wpm → **125s (2:05)**
- At 130 wpm → **134s (2:14)**

The shot list runs 2:24. At 140 wpm the narration lands at 2:05 — but 14 of those seconds
belong to the cold open, where the narrator is silent, so the real narration window is
2:10 for 2:05 of read. That is tighter than it looks: **read at 140–150 wpm**, and treat
the cold open's own pacing as fixed rather than something to trim later.

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

- **`/orders/live`** (**Orders**) — Scheduled / Ongoing / Historical, each tab showing its **count**.
  This is where the scheduled biryani visibly moves from one bucket to the next when the
  background scheduler fires. Time the take so that flip happens on camera; that
  transition is the proof the scheduler is real.
- **`/orders`** (**Group plans**) — past planning sessions with date, item count and total,
  plus a review link back into each cart.

### What's true today, and what isn't

Two things you asked to show don't exist in the code yet. Both are small, but neither
should be narrated until it does — a judge who opens the repo will check.

| Claim | Status |
|---|---|
| Host / guest split access | **Real.** Host token vs. guest token; guest bootstrap redacts the host token; guest checkout and confirm both `403`. Verified in `make security-smoke`. |
| Pending + historical orders in the PWA | **Real.** `/orders/live` buckets by status, `/orders` lists past sessions. Per-order totals shown on both. |
| Onboarding reply | **Real.** A first message routes to `IntentFamily.START_SESSION` and answers with orientation plus the data-retention line in one reply, before the user has shared anything. `intent_router.py`, `ONBOARDING_REPLY`. |
| Learned preferences | **Real.** `profile_defaults` runs in the graph between `intent_parser` and `swiggy_workers`, filling only slots the prompt left unsaid, above a 3-order threshold, and disclosing what it applied in the reply. Deterministic — medians and frequencies, no model call. |
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
| 1:04–1:10 | `docs/diagrams/03-agentic-framework-architecture.png`, full-frame | `Router → intent families (no LLM call)` | *"a deterministic router runs first"* |
| 1:10–1:20 | Same diagram; slow push-in on the graph nodes. Or, better, the rendered state machine from `docs/hld.md` §3.1 (GitHub renders the Mermaid — screenshot it beforehand). | `LangGraph: guardrails → intent → workers → guardrails → persist` then `LLM → strict JSON schema · deterministic fallback` | *"LangGraph state machine"* … *"strict JSON schema"* |
| 1:20–1:29 | `docs/diagrams/01-high-level-architecture.png` — or split-screen the `services/mock-swiggy-mcp` terminal showing live `POST /mcp` lines, which is far more convincing than a static box | `MCP · Food ∥ Instamart · 2.5s each · degrade, don't fail` | *"concurrently over MCP"* |
| 1:29–1:35 | Quick pan over the repo docs tree — `docs/` (PRD, HLD, LLD, `adr/`, `runbooks/`) — then `skills-lock.json` | `60+ locked skills · PRD → HLD/LLD → ADRs → tests` | *"agent-first, from a locked skill set"* |

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
| **Profile defaults** | Derives the sender's profile live from committed history — median spend, usual headcount, dietary tendency, favourite restaurants, modal day and hour — and fills only the slots the prompt left unsaid. Explicit input always wins; below 3 committed orders nothing is applied; whatever is applied is named in the reply. Pure arithmetic, no LLM. | `services/profile_builder.py`, `agent.py` (`apply_profile_defaults`) |
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

Adds ~9s. Replaces everything after *"It doesn't fail."*:

> Nothing here is autonomous, by the way. The agent recommends, compiles and schedules —
> a human always says yes before money moves. That's a design rule, not a missing feature.
> And it was built the way it runs: agent-first, from a locked skill set — the PRD, the
> design docs and the ADRs on screen all came out of that same harness.

This line pairs specifically with beat 6, which follows it: personalization has to land
as *better defaults*, not as an agent deciding for you. "Nothing is autonomous" and "it
fills in what you didn't say" are one beat apart, and they only sound consistent if the
first is said plainly.

Gives beat 5 ~40 seconds (1:04–1:44) and pushes the total to about 2:33 — or about 2:43
with the canvas extension below as well. Only use these if your cap is genuinely 2:30+.

---

## Beat 6 in detail — staging onboarding and the learning demo

This beat needs **two different WhatsApp numbers**, and that is the whole trick: one that
has never messaged EasyOrder, and one with history. A number cannot be both, and history
is the one thing you cannot fake at record time. Seed both before you start.

### Number A — never used before (the onboarding shots)

Its first message must genuinely be its first, so pick a number you have not tested with,
or wipe it first by sending `delete my data` then `delete my data confirm`.

1. Send `hi`. The reply is the whole onboarding beat in one message:
   > Hi! I'm EasyOrder. Tell me what to order, for example: get biryani for 4 under 2000.
   > In a group chat, tag @EasyOrder with the same request.
   >
   > We store your phone number and order details to run your sessions. Message
   > "delete my data confirm" anytime to erase them.

   Hold on it. Orientation and the data promise arrive together, unprompted, before the
   user has given anything up — worth a beat of silence rather than narration.

   ⚠️ **The middle sentence contradicts the rest of the video.** *"In a group chat, tag
   @EasyOrder with the same request"* puts a group-tagging instruction on screen, while
   every other beat — and every prompt on the message sheet — is a plain 1:1 message to
   the business number. `docs/prompts/demo.md` is blunt about why: tagging a business
   number is not a real WhatsApp mention feature, and the product does not need one. The
   host forwards a link; that is the sharing mechanic.

   The code does still route tagged messages (`ChatMode.MENTION_PLANNING`), so the line
   is not false — it just advertises the one path you cannot demonstrate. Three ways to
   handle it, best first:

   1. **Change the copy** in `ONBOARDING_REPLY` (`services/intent_router.py`) so onboarding
      describes the flow the product actually runs. One line, one test.
   2. **Frame the shot** on the first and last sentences. Works, but you are hiding a line
      rather than fixing it, and a judge who scrolls the chat sees it anyway.
   3. **Leave it** and accept that the most-watched frame of your onboarding beat tells
      the viewer to do something the demo never does.
2. Place **one** order from this number, log in, and open `/orders` (**Group plans**).
   The **Your usual** card is there but greyed and dashed, reading *"2 more orders until
   EasyOrder starts using this."* That frame is what makes the threshold real: the system
   is visibly learning and visibly not yet acting.

### Number B — three or more orders (the learned shots)

1. Place **at least three** orders so the profile clears `MIN_OBSERVATIONS = 3`. The
   quickest is the MotiMahal targeted prompt three times — each places immediately:
   > `Order paneer tikka and chicken 65 from MotiMahal restaurant`
2. Check what the profile learned before you trust it on camera:

```bash
curl -s -b cookies.txt http://localhost:8000/api/me/profile
```

3. Confirm `is_confident` is `true` and `typical_budget` is a number you're happy to see
   quoted out loud. If a bad order skewed it, place another or reset and reseed.

### The shot (number B)

- Send **exactly** `get biryani` — no budget, no headcount, nothing else. The whole point
  is how little the user said.
- Let the reply land and **hold on the disclosure line**. It is the beat:
  *"You didn't say, so I used your usual budget of INR 600 (from your last 3 orders).
  Say it in your message to override."*
- Then send `get biryani for 8 under 2500` and show that **no** disclosure line appears —
  the profile stood down because the user was explicit. Two messages, five seconds, and
  the "does it overrule me?" question is answered before anyone asks it.
- Cut to `/orders` and land on the **Your usual** card: usual budget, the restaurant they
  keep returning to, the day and hour they order.

### What to say if asked

The number is a median over committed orders — placed and delivered ones only. Scheduled,
pending and cancelled orders are intent, not evidence, and don't count. Below three
orders the card renders greyed with a countdown and the graph applies nothing: a default
guessed from one order is worse than no default.

---

## Beat 7 in detail — the Business Model Canvas

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

> **On the before/after overlays.** Beats 2–4 open with a paired flash — the without-
> EasyOrder cost, then the with-EasyOrder one — lifted from the *Two Rohans* sketch in
> `docs/prompts/demo.md`. They cost no speech time and carry the comedy the voiceover
> deliberately doesn't, which is what lets the read stay dry. Two lines, ~1.5s each, top
> of the beat, gone before the demo lands. Don't let them run over the evidence.

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

## Message sheet — what to type, in order

Everything you send on camera, in recording order, with the reply it must produce and the
voiceover line it plays under. If a reply doesn't match, stop and fix it before the take:
the read quotes these numbers out loud.

### Before you hit record — cannot be done live

| Do | Why |
|---|---|
| From **number B**, send `Order paneer tikka and chicken 65 from MotiMahal restaurant` **three times** | Gets B over the 3-order threshold so beat 6 has a profile to show. Each places immediately at ₹580. |
| From **number A**, send `get biryani for 4 under 2000` **once** | Gives A exactly one order, so its card reads *"2 more orders until EasyOrder starts using this"* — the learning-in-progress shot. |
| `curl -s -b cookies.txt http://localhost:8000/api/me/profile` for B | Confirm `is_confident: true` and a `typical_budget` you're happy to hear quoted. |
| OTP-log in both numbers in separate browser profiles | An OTP round-trip on camera is dead air. |
| Confirm **number A has never messaged EasyOrder** otherwise | Its `hi` must genuinely be a first contact. Reset with `delete my data` → `delete my data confirm`. |

### On camera, in order

| # | Beat | Send verbatim | Expect back | Plays under |
|---|---|---|---|---|
| 1 | 2 | `2 chicken biryani, 1 mixed veg and 3 tandoori roti from the best restaurant under 2000 INR` | Two messages: the shareable canvas link, and the private host link | *"That's the coordination tax. One message removes it…"* |
| 2 | 3 | `Order paneer tikka and chicken 65 from MotiMahal restaurant and if the budget exceeds INR 400, let me know before placing the order` | `…comes to INR 580.00, which exceeds your INR 400 budget. Reply YES to place it anyway, or NO to cancel.` | *"It comes back at five eighty — over the four hundred you set…"* |
| 3 | 3 | `yes` — a **separate** message, not appended | `Placed! MotiMahal order — total INR 580.00.` | *"…Nothing is placed until you reply yes."* |
| 4 | 4 | `Order Egg Biryani for me from BiryaniByKilo and it should reach by <NEXT HOUR>PM` — see the timing recipe below | `Got it — Egg Biryani from BiryaniByKilo (INR 300.00) is scheduled so it reaches by H:00 PM UTC.` | *"Or order for later. It works backwards from the delivery time…"* |
| 5 | 6 | From **number A**: `hi` | The onboarding reply — orientation plus the data-retention line, in one message | *(silent — hold on the reply)* |
| 6 | 6 | From **number B**: `get biryani` | Host link, plus `You didn't say, so I used your usual budget of INR 600 (from your last 3 orders). Say it in your message to override.` | *"…starts filling in what you leave out…"* |
| 7 | 6 | From **number B**: `get biryani for 8 under 2500` | Host link, and **no** disclosure line | *"Name a number and your number wins."* |

Rows 2, 3, 6 and 7 are exact — that copy comes from the order and profile services and does
not vary by provider mode. Row 1's wording differs between mock mode and live Meta mode
(template/CTA handoff vs. plain short links), so confirm it on your dry run rather than
trusting the phrasing above.

### The scheduled order is the one that can't wait for you

The deadline parser reads only the **hour**, and treats it as **UTC** of the message's
date. BiryaniByKilo's ETA is 45 minutes, so the order is placed at *deadline − 45 min* —
which always lands at **:15 past the preceding hour**, whatever you type.

So `by 8PM` schedules a placement at **19:15 UTC**. Send that at 13:10 and you are waiting
six hours for the Scheduled → Ongoing flip.

To catch the flip inside a take, send between **:00 and :12 past the hour** and name the
**next** hour:

> sent 13:10 UTC · `…reach by 2PM` → deadline 14:00 UTC → **places 13:15 UTC**, about
> 5 minutes later

The scheduler polls every 30 seconds, so it fires within half a minute of that. Five
minutes is still too long to hold one continuous shot — cut away to beat 5, come back for
the flip, and drop the `Meanwhile…` caption over the join. If the maths lands badly on the
day, pre-record the flip and cut to it; nothing in the read depends on it being one take.

⚠️ The reply prints the deadline **in UTC** (`2:00 PM UTC`), not IST. On camera that reads
oddly to an Indian audience — pick an hour whose UTC label you're comfortable showing, or
crop the reply to the `Got it — …is scheduled` half.

### If the mock menu changes

The voiceover quotes ₹580 and ₹400 aloud, and beat 6 quotes ₹600. A menu edit silently
makes all three wrong. Re-run rows 2 and 6 before any re-record and update the read to
match — `docs/prompts/demo.md` flagged this same trap for the original ₹800 figure.

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
- **Beat 6 is real, but it is the beat most likely to be doubted** — "it learned my
  budget" sounds like a claim. Defend it in-shot rather than in narration: send the bare
  prompt live, let the reply quote the number back with `from your last 3 orders`, then
  send an explicit budget and show the profile standing down. Two messages beat any
  assertion. `docs/user-profile-agent.md` documents what it does and does not do.

---

## Delivery notes for the AI voice agent (both versions)

- **Tone**: dry and confident — a senior engineer demoing to peers, not an ad announcer.
  The humor is in the writing, so read the jokes *straight*. "Arithmetic they never
  volunteered for" and "so 'hi' never costs a model call" are throwaways, not punchlines;
  landing on them too hard kills them. No exclamation points.
- **Pace**: 140 wpm. This cut has less slack than the 60-second one — see the timing note
  above before slowing down.
- **The narrator is silent for the first 14 seconds.** The cold open is Rohan's, and the
  first narrated words are "That's the coordination tax" — a reply to him, not an
  introduction. Read that line as an answer, and it stitches the sketch to the product.
- **Register shift at 1:04**: the architecture beat should sound *flatter* and more
  matter-of-fact than the product beats, not more excited. Technical confidence reads as
  calm. Then lift slightly again for the canvas and the close.
- **Emphasis**: land on **"coordination tax"** in the first narrated line and
  **"coordination"** in the close — that's the through-line and the callback. Hit **"and then it stops"** in the
  budget beat, **"It doesn't fail"** in the architecture beat, and **"the value lands on
  Swiggy"** in the canvas beat.
- **Pauses**: a half-beat at every beat boundary — those are the cuts. A full beat after
  "and then it stops," after "while you were in a meeting," and after "It doesn't fail."
- **Numbers and initialisms**: read prices as words ("five eighty"), not "INR 580." Read **MCP** as three letters, and **LangGraph** as one word — check the
  TTS pronunciation of both before you commit to a take.

## Production notes

- **The cold-open shot** is the only thing here you cannot screen-record. It is one clip,
  ~10 seconds, one character, one line to camera — generate it with any of the tools in
  `docs/prompts/demo.md` (Veo 3 handles the synced dialogue itself; the 2D-explainer route
  is the low-risk one if time is short). You need **one** take, not the sketch's six, and
  character consistency stops mattering the moment you only have one shot.
- **Recording**: QuickTime (`File → New Screen Recording`) is enough. OBS if you want
  WhatsApp Web and `/orders/live` in one frame for beat 4, or the diagram and the live
  `POST /mcp` terminal side by side for beat 5.
- **Voice**: ElevenLabs or Murf. Generate the voice track *first*, then cut the video to
  it — trimming silence is easy, stretching a read is not.
- **Edit**: CapCut (free, good auto-captions — many judges watch muted) or DaVinci
  Resolve. Burn in the overlay text from the shot lists verbatim; it's written short on
  purpose, don't paraphrase it into narration.
- **Music**: light comedic bed under the cold open, cut dead on the hinge card — the
  silence after `No actors past this point` is what sells the change of register. Bring a
  light bed back for beats 7–8 only. Drop it out for the product
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
