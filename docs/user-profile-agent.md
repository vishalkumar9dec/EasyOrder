# User onboarding and profile building — design proposal

> **Status: proposed, not implemented.** Nothing in this document ships today. It is
> written so the roadmap beat in `docs/promo-video-script.md` has something real behind
> it, and so the build can start from a decision rather than a blank page.

## The goal, in one line

After a user onboards, EasyOrder reads their Swiggy order history once, derives a small
set of typed preferences, and uses them to fill in what a prompt *doesn't* say — so
"order lunch" becomes a good order instead of a clarifying question.

## What a preference actually is here

Not a personality profile. A set of **defaults for the slots the intent parser already
has**, plus a few signals that change how candidates are ranked:

| Preference | Fills / affects | Derived from |
|---|---|---|
| Typical budget (p50) and ceiling (p90) | `ParsedIntent.budget_limit` (currently a hardcoded 3000) | Order totals |
| Usual headcount | `ParsedIntent.head_count` (currently a hardcoded 4) | Item counts, group vs. solo orders |
| Dietary tendency | `ParsedIntent.dietary_preference` | Item tags across orders |
| Favourite restaurants | Ranking bias in the Food worker | Frequency x recency |
| Cuisine affinity | Query expansion for vague prompts ("something spicy") | Item names, LLM-classified |
| Ordering rhythm — modal days, modal hour | Scheduling defaults ("dinner" → their actual dinner time) | Order timestamps |
| Complaint themes | Suppression rules (avoid a restaurant they complained about twice) | Free-text support/feedback |

The first six are **arithmetic**. Only the last two need a language model. That split is
the whole design.

## Shape: two components, one on the request path and one off it

### 1. Profile Builder — off the request path

Triggered once at onboarding, then incrementally after each completed order. It is a
**workflow, not an agent**: a fixed pipeline with no tool-choice loop, no autonomy, and a
deterministic path.

```
fetch history (MCP get_order_history)
  → normalize to a flat order/item table
  → aggregate (SQL/Python: percentiles, frequencies, histograms)
  → one LLM structured-extraction pass (cuisine affinity, complaint themes)
  → write user_profiles row (typed, versioned, with provenance)
```

Calling this an "agent" would be marketing. It has no decisions to make at runtime;
making it agentic would buy nothing and cost determinism, testability and money. The
existing `EasyOrderGraph` is the right host for it — same node discipline, run on a
background task rather than in the webhook's request.

**Do not ask the LLM to compute the statistics.** Percentiles and modal hours are exact,
cheap and verifiable in SQL, and an LLM will get them subtly wrong in a way no test
catches. The model's job is only the part that's actually language: reading
"the biryani was cold again" and returning `{theme: "temperature", restaurant_id: ...}`.

### 2. `profile_defaults` — on the request path

One new node in the existing graph, between `intent_parser` and `swiggy_workers`:

```
input_guardrails → intent_parser → profile_defaults → swiggy_workers → output_guardrails → persist
```

It fills **only unspecified slots**. Three rules, none negotiable:

1. **Explicit input always wins.** If the prompt says "under 800", the profile's 1,800 is
   irrelevant. The node only ever writes to a field the parser left at its default.
2. **Applied defaults are stated in the reply.** *"Using your usual ₹1,800 — reply
   'budget 3000' to change it."* A silent default that's wrong is indistinguishable from
   a bug, and the user has no way to correct something they can't see.
3. **A profile never places an order.** It changes what gets *proposed*. The existing
   product rule — nothing is charged without an explicit yes (`docs/hld.md` §3.6, and the
   budget gate the demo shows) — still holds. This is worth being firm about: "based on
   the user's preference the order is placed" is exactly the feature that turns one wrong
   inference into a wrong charge, and the trust cost of that is not recoverable.

## Data model sketch

Migration `0009_user_profiles.sql`:

```sql
CREATE TABLE user_profiles (
    wa_id            TEXT PRIMARY KEY,
    typical_budget   NUMERIC(10,2),
    budget_ceiling   NUMERIC(10,2),
    usual_headcount  INTEGER,
    dietary_tendency TEXT,
    favourites       JSONB NOT NULL DEFAULT '[]'::jsonb,  -- [{restaurant_id, score, last_ordered}]
    rhythm           JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {modal_days, modal_hour, ...}
    avoid            JSONB NOT NULL DEFAULT '[]'::jsonb,  -- [{restaurant_id, reason, evidence_count}]
    observations     INTEGER NOT NULL DEFAULT 0,          -- how many orders this is built from
    source_version   INTEGER NOT NULL DEFAULT 1,          -- bump to force a rebuild
    built_at         TIMESTAMPTZ NOT NULL,
    updated_at       TIMESTAMPTZ NOT NULL
);
```

Typed columns for the fields the graph reads, JSONB only where the shape is genuinely
open. `observations` is what gates application — see below. `source_version` lets a
changed derivation invalidate every profile without a data migration.

Deletion is not optional: `delete my data` already cascades sessions; this table joins
that cascade, and `docs/data-retention-policy.md` needs a line for it.

## Keeping it current — the feedback loop

A profile built once at onboarding is wrong within a month. Four mechanisms, in
descending order of value:

**1. Overrides are the signal.** When `profile_defaults` injects a budget of ₹1,800 and
the user replies "no, keep it under 900", that is a labelled correction — the single most
valuable data point the system will ever get, and it's free. Record it as a
`preference_override` event and weight it far above passive order data. Two overrides in
the same direction should move the default; three should retire it.

**2. Incremental update per completed order.** Each EasyOrder order is a fresh
observation. Update the affected aggregates in place on order completion rather than
re-deriving from history — cheap, and it keeps the profile fresh between rebuilds.

**3. Recency weighting.** Weight every observation by `exp(-age/half_life)` with a
half-life of roughly 90 days. Tastes change; a year-old biryani habit shouldn't outvote
last month's. This is one line in the aggregation and it's what makes the profile feel
alive instead of stale.

**4. Periodic full rebuild.** Weekly, off-peak, per user. Catches drift, deleted orders,
and any change to the derivation logic (`source_version`). The incremental path is an
optimization; the rebuild is the source of truth.

**Confidence gating ties it together.** Below ~5 observations, hold the preference but
don't apply it. A wrong default from thin data is worse than no default, because it
teaches the user the system doesn't know them — and that impression is expensive to
reverse.

## How complex is this, honestly

The code is not the hard part.

| Piece | Effort | Risk |
|---|---|---|
| `user_profiles` table + adapter methods (both adapters) | ~0.5 day | Low — same shape as `orders` |
| Deterministic aggregations (budget percentiles, favourites, rhythm) | ~1 day | Low — pure functions, trivially testable |
| `profile_defaults` node + "explicit input wins" + reply disclosure | ~1 day | Low, but the disclosure copy needs care |
| Override capture + weighting | ~1 day | Medium — needs a real event trail |
| LLM pass for cuisine affinity and complaint themes | ~1 day | Medium — another structured-extraction call, same pattern as `llm_intent.py` |
| Incremental update + weekly rebuild job | ~1–2 days | Medium — scheduling exists (`order_scheduler.py`) but this is per-user fan-out |

**A credible v1 is about a week.** Deterministic aggregates, the defaults node with
disclosure, and override capture — that alone delivers most of the felt value.

The genuinely hard parts are not on that table:

- **Getting the history at all.** `get_order_history` exists on the MCP client and the
  mock server, so locally this works today. Against real Swiggy it needs an OAuth scope
  for a user's past orders — a partner-access and consent question, not an engineering
  one. Everything here is blocked on it, and it's worth asking about early.
- **Knowing whether a preference is right.** There is no test for "is ₹1,800 the right
  default for this user". The only honest measure is behavioural: override rate on
  injected defaults, and whether sessions with defaults convert better than those
  without. Build that counter before building the inference, or you're tuning blind.
- **Consent.** Reading someone's order history to build a behavioural profile is a
  different privacy proposition from taking an order. It needs an explicit opt-in at
  onboarding, a plain-language description of what's inferred, and a working "forget my
  preferences". The existing privacy and retention docs both need updating.

## Suggested v1 slice

1. Opt-in at onboarding, with a one-line explanation of what gets read.
2. Deterministic aggregates only — budget, headcount, favourites, rhythm. No LLM.
3. `profile_defaults` node filling unspecified slots, always disclosed in the reply.
4. Override capture, and a counter for injected-default override rate.

Ship that, watch the override rate for a fortnight, and let it decide whether the LLM
layer is worth building. Cuisine affinity and complaint-theme suppression are the more
impressive demo, but they're the part most likely to be confidently wrong.
