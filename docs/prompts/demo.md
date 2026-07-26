# EasyOrder Demo — "A Tale of Two Rohans"

*Swiggy Builders Program submission video. Target runtime: 2:45–3:00.*

**Tagline:** *It was the best of orders, it was the worst of orders.*

**The bit:** One guy, Rohan, played by the same actor (or the same AI-generated
character) on both halves of a split screen — Left-Rohan lives without
EasyOrder, Right-Rohan lives with it. Same WhatsApp group, same order, same
Friday night. Their fortunes diverge immediately and never recover. A small
"Chaos-O-Meter" gauge sits in the corner of the frame throughout Part 1 —
redlining on the left, barely twitching on the right — as the one running
visual gag that ties all three vignettes together.

---

## Top use cases (reference)

1. **Group ordering**: "2 chicken biryani, 1 mixed veg, 3 tandoori roti from
   the best restaurant under 2000 INR." Host and guests see, verify, and
   modify the order on a shared link.
2. **Named restaurant + budget gate**: "Order paneer tikka and chicken 65
   from MotiMahal restaurant and if the budget exceeds INR 800, let me know
   before placing the order."
3. **Scheduled delivery**: "Order Egg Biryani for me from BiryaniByKilo and
   it should reach by 8PM" — interpreted as a ~30-minute arrival window.

---

## Full script

### 0:00–0:12 — Cold open

Full-frame, not split yet. Rohan looks at camera, mid-chaos, phone in one
hand, calculator app in the other, seven browser tabs of restaurant menus
behind him.

> **ROHAN:** Every Friday, my friend group asks me the same three questions.
> "What's the food plan?" "Is it under budget?" And — my personal
> favorite — "Bro where's my biryani."

Freeze frame. Screen does a comic-book "SPLIT" wipe down the middle —
camera pulls back to reveal **two Rohans**, one per half.

**TITLE CARD:** *A Tale of Two Rohans* — *(one WhatsApp group, two
realities)*

---

### 0:12–0:37 — Vignette 1: Group Ordering

| | **LEFT — No EasyOrder** | **RIGHT — With EasyOrder** |
|---|---|---|
| **Visual** | Rohan alt-tabs between three Swiggy restaurant pages, thumb-scrolling furiously. Sticky note on his monitor reads "BUDGET: ₹2000" with three items crossed out and rewritten. Group chat notification badge climbs: 1... 4... 12... | Rohan types ONE WhatsApp message. Leans back. Sips chai. Phone buzzes once — a clean summary card: 3 items, 2 restaurants, ₹1,840 of ₹2,000, one shareable link. |
| **Chaos-O-Meter** | Needle slams into the red. | Needle doesn't move off "chill." |
| **Line** | **ROHAN (L):** *"Wait, did I already order the mixed veg? WHO ADDED FOUR TANDOORI ROTI—"* | **ROHAN (R):** *"...and that's dinner sorted. Anyone want to see the receipt? I'll just forward the link."* |
| **On-screen text** | `⏱ 14 minutes. 3 restaurant tabs. 1 minor breakdown.` | `⏱ 11 seconds. 1 message. 0 breakdowns.` |

---

### 0:37–1:00 — Vignette 2: Ordering from a specific restaurant

| | **LEFT** | **RIGHT** |
|---|---|---|
| **Visual** | Rohan opens the Swiggy app, searches "MotiMahal," scrolls past 40 menu items hunting for Chicken 65, adds to cart, opens his banking app in a *second* window to eyeball his balance before checkout. | Rohan sends one line to EasyOrder. Phone replies instantly: *"comes to ₹580, reply YES to place."* He taps yes without even sitting up straight. |
| **Chaos-O-Meter** | Redlines again, smoke curling off the gauge. | A single, satisfied blip. |
| **Line** | **ROHAN (L):** *(squinting at his phone bill)* *"...okay but do I NEED the butter naan though."* | **ROHAN (R):** *"It already told me the total. It's basically doing my mental math AND my life admin."* |
| **On-screen text** | `4 taps to find the dish. 1 tab-switch to check his bank balance.` | `1 message. 1 confirmation. Budget checked automatically.` |

---

### 1:00–1:25 — Vignette 3: Scheduled delivery

| | **LEFT** | **RIGHT** |
|---|---|---|
| **Visual** | Rohan's stuck in a meeting, sets a phone alarm labeled "ORDER DINNER!!" Meeting runs long. Alarm goes off, gets silenced without looking. Cut to 9:40 PM: Rohan alone, eating instant noodles, string of cheese hanging tragically. | Same meeting. Rohan sends EasyOrder one message before it even starts, then forgets about food entirely. At 8:00 PM sharp, phone buzzes: *"Placed! Your BiryaniByKilo order — total INR 300.00."* Cut to Rohan opening the door to a delivery guy, mid-high-five. |
| **Chaos-O-Meter** | Redlines, then just... dies. Little puff of smoke. | Doesn't even react. It's asleep. It's that easy. |
| **Line** | **ROHAN (L):** *(mouth full of instant noodles)* *"...I was gonna order real food. I was."* | **ROHAN (R):** *"I didn't even remember I ordered this. Ten out of ten timing."* |
| **On-screen text** | `Forgot to order. Ate noodles. Again.` | `Scheduled once. Arrived on time. Zero reminders needed.` |

---

### 1:25–1:35 — The turn

Both Rohans, side by side, look directly at camera. Right-Rohan takes a
bite of biryani. Left-Rohan side-eyes him, noodle cup in hand.

> **ROHAN (L):** *"...okay but is this real, or is he just CGI?"*
>
> **ROHAN (R):** *(to camera, deadpan)* *"It's real. Watch."*

Hard cut. Chaos-O-Meter graphic disappears — we're leaving the sketch and
entering the real product.

**ON-SCREEN TEXT (full frame):** `No actors past this point. This is the real app.`

---

### 1:35–2:50 — Live demo (real screen recording)

Straight capture of WhatsApp Web + the EasyOrder PWA, no reenactment. Move
briskly — each beat should land in under 25 seconds. Suggested order,
matching the vignettes 1:1 so the payoff is obvious:

1. **(0:00–0:30) Group order.** Send the exact group-order prompt as a
   direct message to the EasyOrder business number — no `@` tagging, that's
   not a real WhatsApp mention feature and the app doesn't need one; every
   use case here is a plain 1:1 message to the business number. Show the
   reply landing with the shareable session link, then a quick beat of
   Rohan forwarding that link into his actual friend group (this is the
   real sharing mechanic — a host-forwarded link, not a bot-in-group).
   Switch tabs to the session page — cart split by restaurant, budget bar,
   host/guest view. Zoom on the ₹1,840 / ₹2,000 total.
2. **(0:30–0:55) Named restaurant + budget gate.** Send the MotiMahal
   prompt with a budget that actually triggers the gate (e.g. "exceeds INR
   400" — with the current menu, ₹800 won't trigger it, so pick a number
   that will). Show the confirmation question arriving, reply `yes` as a
   **separate** message, show `Placed!`.
3. **(0:55–1:15) Scheduled order.** Send the BiryaniByKilo prompt. Show the
   immediate `Scheduled` reply. Cut — jump-cut/time-lapse effect with a
   caption `Meanwhile...` — to the `/orders/live` page, Scheduled tab
   showing the countdown, then (pre-recorded or sped up) the tab flipping
   to Ongoing once the scheduler fires, with the `Placed!` WhatsApp
   notification appearing in the same shot.
4. **(1:15–1:15) Optional button:** a 3-second pan across the `/orders/live`
   page showing all three orders sitting in their real buckets —
   Scheduled / Ongoing / Historical — as visual proof this isn't smoke and
   mirrors.

---

### 2:50–3:00 — Close

Both Rohans back on screen, Right-Rohan now visibly eating well, Left-Rohan
still holding the noodle cup but grudgingly impressed.

> **ROHAN (R):** *"Same group chat. Same Friday. Very different night."*

**END CARD:**
```
EasyOrder
WhatsApp-first group ordering, powered by Swiggy.

Built for the Swiggy Builders Program.
```

---

## Requirement and tone (unchanged from draft)

Light-hearted, funny, to the point. Under 3 minutes total. Uses one
recurring character across a comedic split-screen, then a real,
unedited product demo as the payoff — the joke earns the credibility, the
credibility earns the score.

---

## Production guide: turning this into video

You have two very different halves to produce: a **comedic animated/AI
sketch** (Part 1, ~1:25) and a **real screen recording** (Part 2, ~1:15).
Treat them as separate pipelines.

### Part 2 first, because it's the easy one

Record it on your laptop, not your phone:

- Open **WhatsApp Web** (web.whatsapp.com) linked to your phone, in a
  clean browser window/tab — this captures crisp text instead of filming a
  phone screen at an angle.
- Screen-record with **QuickTime Player** (`File → New Screen Recording`,
  built into every Mac, zero setup) or **OBS Studio** (free, more control
  over cropping/multiple sources if you want WhatsApp + the `/orders/live`
  page visible at once).
- Do a full dry run first so your timings match the beats above — send
  each message for real, confirm the reply text matches what's documented,
  *then* record the take you'll keep.
- Keep each clip short and re-cut the boring parts (loading spinners,
  typing) in the editor rather than live — faster than getting one perfect
  unbroken take.

### Part 1: getting a consistent animated character

The hard part is making Left-Rohan and Right-Rohan obviously the *same
person* across six short clips. Two viable approaches, in order of how
much you want AI to do versus how much control you want:

**Option A — AI video generation (best visual quality, most "wow")**

1. Generate one reference image of Rohan first (any image model — Gemini,
   ChatGPT/DALL·E, Midjourney) and lock it in. Reuse the *exact same*
   reference image as the character seed for every clip.
2. Feed each vignette's mini-script (from the tables above) into a
   text-to-video tool that supports character-reference/consistency:
   - **Google Veo 3** (via the Gemini app or Vertex AI) — currently the
     strongest option if you want it to generate synced dialogue and
     lip-sync directly, so you may not need separate voiceover at all.
   - **Runway Gen-4** — strong character consistency via reference images,
     good for stylized comedic shorts.
   - **OpenAI Sora 2** — high motion coherence, supports reference-image
     conditioning on some tiers.
   - **Kling AI / Luma Dream Machine** — solid, cheaper alternatives.
   - Generate Left and Right for each vignette as **separate clips**, then
     composite them into a split screen in your editor (simplest and most
     reliable — don't fight the AI tool into rendering the split itself).
3. Expect to regenerate a handful of times per shot — treat it like
   directing takes, not a single-prompt magic trick.

**Option B — 2D explainer-style animation (fastest, most consistent, easy)**

Tools like **Vyond**, **Powtoon**, or **Animaker** use a rigged character
asset you drag around a timeline — since it's the *same asset* every time,
character consistency is automatic and free, and they come with built-in
scene templates, props (phones, laptops, chat bubbles), and stock AI
voices. Less "cinematic," more "friendly explainer," which honestly suits
a lighthearted 3-minute pitch video fine. This is the lower-risk option if
you're short on time before the submission deadline.

**Recommendation given your constraints:** if you have a few extra hours,
Option A (Veo 3 specifically, for the built-in dialogue) will look more
impressive to judges. If you're tight on time, Option B guarantees you
finish and still looks clean and professional.

### AI voice / speech

If your video tool doesn't generate synced dialogue for you (Runway, Sora,
Kling generally don't; Veo 3 does):

- **ElevenLabs** — the current best for expressive, emotionally-distinct
  TTS. You can create two voice presets (frustrated Left-Rohan, smug
  Right-Rohan) from the same base voice with different delivery settings,
  which is a nice touch given they're meant to be the same guy.
- **Murf.ai** — similar quality, has a built-in timeline editor for
  dropping narration directly onto video, useful if you're not using a
  separate video editor for that step.
- **Play.ht** — another solid alternative if you want to compare voices.

Generate the voice lines first, time your video clips/animation to match
their length, rather than the reverse — it's much easier to trim silence
than to stretch a voice line to fit.

### Putting it together

- **CapCut** (free, fast, excellent auto-captions — important since a lot
  of judges/viewers will watch muted) or **iMovie** (free on Mac, simpler,
  fine for this length) or **DaVinci Resolve** (free, most powerful if you
  want real color grading / multi-track audio control).
- Composite the Left/Right AI clips into a literal split screen (a simple
  two-video-track layout, vertical divider line down the middle) rather
  than relying on any generation tool to do it natively.
- Add a light, slightly comedic royalty-free background track under Part 1
  only — drop it out entirely for Part 2 so the real product demo feels
  grounded and credible by contrast.
- Burn in the on-screen text/captions from the tables above as literal
  overlay text — they're written short and punchy on purpose, don't
  paraphrase them into voiceover-only.
