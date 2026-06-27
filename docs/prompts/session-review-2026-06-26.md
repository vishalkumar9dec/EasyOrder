# AI Architect Review — Session Efficiency Analysis

**Reviewed by:** AI Architect  
**Session under review:** [session-summary-2026-06-26.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/prompts/session-summary-2026-06-26.md)  
**Verdict:** You produced strong deliverables, but **~40% of your 7 hours was avoidable waste.** The same output could have been achieved in **2–2.5 hours** with better prompt discipline and phase ordering.

---

## Part 1: Where Your Time Actually Went

```
Phase 1: Skill Discovery        ██████████████████████░░░░░  2h 25m  (35%)  ← EXPLORATION
Phase 2: PRD Creation           █░░░░░░░░░░░░░░░░░░░░░░░░░  6m      (1%)   ← EFFICIENT ✓
Phase 3: HLD & LLD              ██░░░░░░░░░░░░░░░░░░░░░░░░  17m     (4%)   ← EFFICIENT ✓
Phase 4: Design Review           █░░░░░░░░░░░░░░░░░░░░░░░░░  4m      (1%)   ← EFFICIENT ✓
Phase 5: Mermaid Debugging       █░░░░░░░░░░░░░░░░░░░░░░░░░  5m      (1%)   ← AVOIDABLE WASTE
Phase 6: Visual & Call Flows    ████░░░░░░░░░░░░░░░░░░░░░░░  41m     (10%)  ← HAD 1 REJECTION
Phase 7: Tech Stack Decisions   ██░░░░░░░░░░░░░░░░░░░░░░░░░  17m     (4%)   ← WRONG ORDERING
Phase 8: Architecture Refactor  ████████████████░░░░░░░░░░░  2h      (29%)  ← BIGGEST WASTE
────────────────────────────────────────────────────────────────────
Meta-questions ("which skill?")                              ~15m    (4%)   ← AVOIDABLE
Confirmation rounds ("yes" ×15)                              ~10m    (2%)   ← AVOIDABLE
────────────────────────────────────────────────────────────────────
Total productive time:           ~1h 25m
Total avoidable waste:           ~2h 45m
Total exploration (one-time):    ~2h 25m
```

> **Bottom line:** Phases 2–4 and 7 were excellent — fast, skill-driven, prompt-based. Phase 8 was a 2-hour feedback loop that could have been 15 minutes with one good prompt.

---

## Part 2: Eight Improvement Areas

### 1. 🔴 Your Phase Ordering Was Wrong

**What happened:** You created HLD/LLD (Phase 3) *before* deciding on the tech stack (Phase 7). Then you had to go back and retrofit the architecture with Python/FastAPI/LangGraph details.

**Why it matters:** Architecture decisions depend on tech stack constraints. Designing an HLD without knowing if you're using Django vs. FastAPI, or LangChain vs. raw OpenAI, produces a generic document that has to be rewritten.

**Fix:**
```
WRONG:  PRD → HLD/LLD → Review → Tech Stack → Retrofit architecture
RIGHT:  PRD → Tech Stack → HLD/LLD (informed by tech stack) → Review
```

---

### 2. 🔴 Phase 8 Was a 2-Hour Feedback Loop — Your Prompts Lacked Acceptance Criteria

**What happened:** You spent 5+ iterations rejecting architecture diagrams because:
- v1: "not professional"
- v2: "missing agentic section"
- v3: "structure was wrong"
- v4: "still not professional"
- v5: "not visible, undo"

**Root cause:** Your prompts described *what to build* but never *what good looks like*. "Refactor it. Feel free to use /design-an-interface" gives zero visual constraints. The agent had to guess your mental model.

**Fix:** Include acceptance criteria in your prompt. One prompt with a reference image and structural spec would have replaced all 5 iterations:

```text
BAD PROMPT:
"The system architecture is not professional. I don't like it. Refactor it."

GOOD PROMPT:
"Refactor the Section 1 architecture diagram with these constraints:
- Structure: 3 sections — (1) bird's-eye overview with only component boxes
  and connections, (2) detailed FastAPI internals, (3) detailed LangGraph pipeline
- Layout: Clients LEFT, Server CENTER (FastAPI + LangGraph side-by-side inside
  one container), Swiggy RIGHT, DB BOTTOM
- Style: Panel-based with color-coded backgrounds per section, subtitles on
  each box, numbered flow arrows
- Reference: [attach image] — match this visual style
- Format: Generate as .png, NOT Mermaid (Mermaid won't render this complexity)"
```

---

### 3. 🟡 You Asked "Which Skill Should I Use?" Too Many Times

**What happened:** You asked this meta-question 4 separate times:
- "which skill will you use to prepare the HLD and LLD?"
- "what skill should I use to review the HLD and LLD?"
- "Tell me which skill should I use to generate call flow diagram"
- "which skill should be used to decide the architecture?"

Each meta-question cost ~3 minutes plus a follow-up confirmation. That's ~15 minutes of overhead.

**Fix:** Create a **skill lookup table** once and reference it. You already started this with `docs/prompts/skills_prompt.md` — but it's incomplete and you didn't actually use it. A better version:

```markdown
| I want to...                    | Use this skill           | Prompt pattern                           |
|---------------------------------|--------------------------|------------------------------------------|
| Validate an idea                | /grill-me                | "Analyze X, /grill-me on my plan"        |
| Write a PRD                     | /to-prd                  | "Create a PRD using /to-prd"             |
| Build domain glossary           | /domain-modeling         | "Build domain model for X"               |
| Design system architecture      | /codebase-design         | "Design deep modules for X"              |
| Compare interface alternatives  | /design-an-interface     | "Design it twice for X"                  |
| Document tech stack decisions   | /decision-mapping        | "Map decisions for X"                    |
| Review docs against spec        | /review                  | "Review X against Y"                     |
| Generate visual diagrams        | generate_image           | "Generate .png diagram of X"             |
| Generate call flow sequences    | (manual Mermaid)         | "Create sequence diagrams for each UC"   |
```

---

### 4. 🟡 You Used Mermaid for a Job That Needed a Design Tool

**What happened:** You spent ~45 minutes trying to make Mermaid produce professional panel-based diagrams. Mermaid is a *documentation tool*, not a *design tool*. It will never produce the visual quality of the reference image you shared.

**Fix:** For architecture diagrams that need to look professional:
- Use `generate_image` immediately for panel/visual diagrams
- Use Mermaid ONLY for simple flowcharts and sequence diagrams that don't need color panels
- Or use draw.io / Excalidraw for interactive editing

**Rule of thumb:**
```
Simple flow (A → B → C)           → Mermaid ✓
Sequence diagram (who calls whom)  → Mermaid ✓
Panel-based architecture diagram   → generate_image or draw.io
State machine                      → Mermaid stateDiagram ✓
```

---

### 5. 🟡 No Git — You Couldn't Revert

**What happened:** When you said "undo", there was no git history. The agent had to manually reconstruct the previous file version from memory. This is fragile and error-prone.

**Fix:** Initialize git at the start of every project. Commit after each phase completes.

```bash
# Phase 0 (before anything else)
git init && git add -A && git commit -m "initial: raw product doc"

# After each phase
git add -A && git commit -m "phase 2: PRD via grilling + to-prd"
git add -A && git commit -m "phase 3: HLD/LLD via domain-modeling + codebase-design"
```

Now `git diff` shows exactly what changed, and `git checkout -- docs/hld.md` reverts instantly.

---

### 6. 🟡 "Yes" Fatigue — You Confirmed 15+ Times Without Adding Signal

**What happened:** During grilling and design phases, you responded `yes`, `agree`, `proceed` about 15 times across the session. Many of these were the agent asking permission to do what you already told it to do.

**Why it matters:** Each confirmation round costs 30–60 seconds of context switching.

**Fix:** Use the `/goal` slash command for multi-step tasks. It runs autonomously without stopping for confirmation at every step. Or add to your prompts:

```text
"Execute all steps without stopping to ask for confirmation.
If you need a decision, list options and pick the best one.
Only stop if there's a genuine ambiguity."
```

---

### 7. 🟢 Your Prompt Versioning Is Good — But Incomplete

**What you did well:** Storing prompts in `docs/prompts/` is smart and reusable.

**What's missing:**
- No prompt for architecture diagram generation (the Phase 8 prompt was verbal, not saved)
- No prompt for call flow diagrams
- No prompt for visual guide generation
- The `skills_prompt.md` is a skeleton, not a working reference

**Fix:** After every phase, save the *winning prompt* (the one that produced accepted output). You'll never have to figure it out again.

---

### 8. 🟢 You Installed Many Skills You Never Used

**What happened:** You installed 15+ skills but only used 9. Skills like `tdd`, `diagnosing-bugs`, `doc-coauthoring`, `deploy-to-vercel`, `brand-guidelines`, `pdf`, `pptx`, `xlsx`, `docx` were never invoked.

**Impact:** Minimal (they don't slow anything down), but it clutters your mental model of available tools.

**Fix:** Install skills on-demand, not upfront. Or organize into tiers:
- **Tier 1 (always install):** grilling, domain-modeling, codebase-design, review
- **Tier 2 (install when needed):** tdd, frontend-design, deploy-to-vercel
- **Tier 3 (install per-task):** pdf, pptx, xlsx, brand-guidelines

---

## Part 3: Anti-Patterns Identified

| Anti-Pattern | You did this | Better alternative |
|-------------|-------------|-------------------|
| **Incremental revelation** | Revealed your mental model through 5 rejections instead of one specification | State structure + visual reference + acceptance criteria in the first prompt |
| **Tool mismatch** | Used Mermaid for professional visual diagrams | Use `generate_image` for visuals, Mermaid for documentation |
| **Phase disorder** | Designed architecture before choosing tech stack | Tech stack → Architecture (always) |
| **Meta-prompting** | "Which skill should I use?" (×4) | Build a lookup table, consult it |
| **Unversioned work** | No git, so "undo" was manual reconstruction | `git init` at Phase 0 |
| **Over-confirmation** | 15+ "yes/agree" responses | Use `/goal` or "execute without stopping" |
| **Verbal prompts for complex work** | Architecture diagram requirements were conversational, not written | Write a structured prompt with constraints, save it |

---

## Part 4: How I Would Have Done the Same Thing

### Target: Same 11 deliverables in ~2 hours

```
PHASE 0: Bootstrap (5 min)
─────────────────────────
$ git init && git add -A && git commit -m "init: raw product doc"
Install skills: grilling, domain-modeling, codebase-design,
  design-an-interface, review
(Skip tdd, pdf, pptx, docx — not needed for design phase)
```

```
PHASE 1: PRD (10 min)
─────────────────────
PROMPT:
"Analyze @[docs/product-documentation.md].
/grill-me on the architecture — ask up to 3 critical questions,
then create a PRD using /to-prd.
Execute without stopping for confirmation on each step.
Save output to docs/easyorder-prd.md."

$ git add -A && git commit -m "phase 1: PRD"
```

```
PHASE 2: Tech Stack Decisions (10 min)
──────────────────────────────────────
PROMPT:
"Use /decision-mapping to document tech stack choices for EasyOrder.
Constraints I've already decided:
  - Backend: Python 3.12 + FastAPI
  - Agentic: LangGraph + LangChain
  - Database: Cloud Firestore
  - LLM ladder: Ollama (dev) → Gemini Flash (staging) → GPT-4o mini (prod)
  - MCP: Stdio JSON-RPC
  - Frontend: Vite + React PWA
  - Freemium services only for local dev
Document trade-offs for the decisions I haven't locked:
  Auth strategy, deployment platform, testing framework.
Save to docs/decision-map.md."

$ git add -A && git commit -m "phase 2: tech stack decisions"
```

```
PHASE 3: HLD + LLD + Domain Model (30 min)
───────────────────────────────────────────
PROMPT:
"Read @[docs/easyorder-prd.md] and @[docs/decision-map.md].

Create HLD (docs/hld.md) with exactly 3 sections:
  §1 — High-level bird's-eye: just component boxes (WhatsApp, FastAPI,
       LangGraph, Swiggy MCP, Firestore) with connections and E2E
       request-response flow table. Use simple Mermaid (graph LR,
       one subgraph for server, no emojis).
  §2 — Detailed FastAPI Application: routes, middleware, auth, checkout,
       Firestore sync, local sandbox.
  §3 — Detailed Agentic Framework: LangGraph state machine (use
       stateDiagram-v2), node responsibilities table, prompt harness,
       input/output guardrails, degradation policies.

Create LLD (docs/lld.md) mirroring the same 3-section structure with
code-level interfaces, Pydantic schemas, Protocol types, and test seams.

Also create:
  - CONTEXT.md — domain glossary using /domain-modeling
  - docs/adr/ — 3 ADRs for Firestore sync, sequential checkout, webhook

Use /codebase-design for deep module design.
Use /design-an-interface if the Orchestrator state interface
has viable alternatives.
Execute all steps. Do not stop for confirmation."

$ git add -A && git commit -m "phase 3: HLD + LLD + domain model + ADRs"
```

```
PHASE 4: Architecture Diagrams as PNGs (15 min)
────────────────────────────────────────────────
PROMPT:
"Generate 3 professional .png architecture diagrams using generate_image:

1. HIGH-LEVEL (01-high-level-architecture.png):
   Panel layout — Clients (WhatsApp, PWA) LEFT in red panel,
   EasyOrder Server (FastAPI + LangGraph side-by-side) CENTER in green panel,
   Swiggy MCP RIGHT in blue panel, Cloud Firestore BOTTOM in yellow panel.
   Each box has name + subtitle. Numbered flow arrows.
   Reference style: [attach reference image]

2. FASTAPI DETAIL (02-fastapi-application-architecture.png):
   Panels for Ingress, Middleware, Core, Checkout, Auth, Adapters.

3. AGENTIC PIPELINE (03-agentic-framework-architecture.png):
   Top-down pipeline: User Query → Input Guardrails → Intent Parser →
   Concurrent Workers (fork) → Output Guardrails → Write DB.
   Side panels for Response Outcomes and Tech Stack.
   Reference style: [attach agentic pipeline reference image]

Save all to docs/diagrams/."

$ git add -A && git commit -m "phase 4: architecture diagram PNGs"
```

```
PHASE 5: Call Flows (15 min)
────────────────────────────
PROMPT:
"For each use case in @[docs/easyorder-prd.md], create a technical
sequence diagram (Mermaid sequenceDiagram) in docs/easyorder-call-flows.md.
Each diagram must show: which HTTP endpoint is hit, which backend module
processes it, which MCP tool is called, what gets written to Firestore,
and what response goes back to the client.
Cover: session creation, cart collaboration, checkout, degradation."

$ git add -A && git commit -m "phase 5: call flow diagrams"
```

```
PHASE 6: Design Review (10 min)
───────────────────────────────
PROMPT:
"Use /review to evaluate @[docs/hld.md] and @[docs/lld.md] against
@[docs/easyorder-prd.md]. Check:
1. Spec coverage — every PRD user story has a corresponding interface
2. Interface depth — are modules deep or shallow?
3. Test seams — can Swiggy MCP be mocked locally?
4. Freemium viability — can everything run locally at zero cost?
Save to docs/design-review-results.md."

$ git add -A && git commit -m "phase 6: design review"
```

```
PHASE 7: Save Prompts (5 min)
─────────────────────────────
Save all winning prompts from phases 1–6 into docs/prompts/.
Create skill lookup table.
$ git add -A && git commit -m "phase 7: prompt library"
```

### Time Comparison

| Phase | You (actual) | Optimized | Savings |
|-------|-------------|-----------|---------|
| Skill discovery | 2h 25m | 5m (pre-known) | 2h 20m |
| PRD | 6m | 10m | — |
| Tech stack | 17m | 10m | 7m |
| HLD/LLD | 17m | 30m | +13m (more upfront) |
| Review | 4m | 10m | +6m |
| Mermaid debugging | 5m | 0m | 5m |
| Visual guide + call flows | 41m | 15m | 26m |
| Architecture diagrams | 2h | 15m | 1h 45m |
| Meta-questions | 15m | 0m | 15m |
| Confirmations | 10m | 0m | 10m |
| **Total** | **~7h** | **~1h 40m** | **~5h 20m** |

> **Note:** The 2h 25m skill discovery is a one-time cost. On your second project, your actual production time was ~4h 35m. The optimized version targets ~1h 35m of pure production work.

---

## Part 5: Your Strengths (What to Keep)

Not everything needs improvement. These are genuinely strong patterns:

1. **Document-first discipline** — most people skip to code. You didn't. This is a professional strength.
2. **Prompt versioning** — saving reusable prompts is rare and smart. Keep doing it.
3. **Skill composition** — combining `/grill-me` + `/to-prd` in one prompt is advanced usage.
4. **Domain modeling before design** — CONTEXT.md as the source of truth is textbook DDD.
5. **ADRs** — recording *why* decisions were made, not just *what*. Most teams skip this.
6. **Ownership mindset** — "I want to be the owner of the codebase" drives better documentation.

---

## Part 6: Rules to Internalize

Save these as `.agents/AGENTS.md` so the agent follows them automatically:

```markdown
# Project Rules

1. Always init git before any work. Commit after each phase.
2. Tech stack decisions come BEFORE architecture design, never after.
3. For professional diagrams, use generate_image (PNG), not Mermaid.
4. Every prompt must include acceptance criteria or a reference image.
5. Do not ask "which skill should I use?" — consult the skill lookup table.
6. Execute multi-step tasks without stopping for confirmation unless
   there is genuine ambiguity.
7. After each phase, save the winning prompt to docs/prompts/.
8. Architecture diagrams have exactly 3 tiers:
   bird's-eye overview, app-layer detail, agentic-layer detail.
```
