# Session Summary — EasyOrder Collaborative Concierge

**Date:** 2026-06-26 (Thursday)  
**Duration:** ~7 hours (18:05 IST → 01:04 IST)  
**Project:** EasyOrder — collaborative food & supply ordering via WhatsApp + PWA  
**Model Used:** Started with Gemini 3.5 Flash, later switched to Claude Opus 4.6 (Thinking)

---

## 1. Chronological Timeline

### Phase 1: Setup & Skill Discovery (18:05 – 20:30)

| Time | What I did | Prompt (verbatim or summarized) |
|------|-----------|------|
| 18:05 | Explored BMAD methodology | `do you know about BMAD?` |
| 20:20 | Connected BMAD to Antigravity workflow | `Yes, I am talking about "Build More Architect Dreams"... How can I apply BMAD in antigravity?` |
| 20:26 | Evaluated skills.sh marketplace | `What do you think of skills in https://www.skills.sh/?` |
| 20:29 | Chose skills for each role | `I want to use the skills for product analyst, system design, ui design, test, code review. Tell me the skills which I can import from skills.sh` |
| 20:31 | Installed skills | `okay install these skills here` |
| 20:34 | Learned how to invoke skills | `okay good. now how do I invoke the skills?` |

**Skills installed from skills.sh:**
- `grilling` (grill-me) — stress-test plans via interview
- `review` — standards + spec compliance review
- `tdd` — test-driven development
- `frontend-design` — UI/UX design guidance
- `codebase-design` — deep modules, testing seams
- `domain-modeling` — ubiquitous language, glossary
- `design-an-interface` — "design it twice" interface comparison
- Additional skills: `diagnosing-bugs`, `doc-coauthoring`, `deploy-to-vercel`, `brand-guidelines`, `canvas-design`, `pdf`, `pptx`, `xlsx`, `docx`

---

### Phase 2: PRD Creation (20:42 – 20:48)

| Time | What I did | Prompt |
|------|-----------|------|
| 20:42 | Analyzed raw product doc + grilled on architecture + generated PRD | `Analyze @[docs/product-documentation.md], /grill-me on my architecture and plan and finally create a PRD using the /to-prd skill` |
| 20:43–20:46 | Answered grill questions (4 rounds of yes/agree) | `2`, `yes, agree`, `Yes`, `yes` |

**Skills invoked:** `grilling`, `to-prd` (custom)  
**Deliverable:** [docs/easyorder-prd.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/easyorder-prd.md)

---

### Phase 3: HLD & LLD Design (20:48 – 21:05)

| Time | What I did | Prompt |
|------|-----------|------|
| 20:48 | Asked which skills to use for HLD/LLD | `now which skill will you use to prepare the HLD and LLD for this project? be specific` |
| 20:52 | Created reusable prompt for HLD/LLD | `okay good. Now write a prompt for me to create HLD and LLD using these skills. We will track the prompts in docs/prompts folder.` |
| 20:53 | Executed the HLD/LLD prompt | `Create HLD and LLD for this project by reading @[docs/prompts/hld-lld-prompt.md]` |
| 20:54–21:01 | Answered design questions (5 rounds) | `yes`, `Agree`, `yes agree`, `yes` |

**Skills invoked:** `domain-modeling`, `codebase-design`, `design-an-interface`  
**Deliverables:**
- [docs/hld.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/hld.md) — High-Level Design
- [docs/lld.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/lld.md) — Low-Level Design
- [CONTEXT.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/CONTEXT.md) — Domain glossary
- [docs/adr/0001-firestore-realtime-sync.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/adr/0001-firestore-realtime-sync.md)
- [docs/adr/0002-sequential-checkout-splits.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/adr/0002-sequential-checkout-splits.md)
- [docs/adr/0003-mention-only-webhook.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/adr/0003-mention-only-webhook.md)

---

### Phase 4: Design Review (21:03 – 21:07)

| Time | What I did | Prompt |
|------|-----------|------|
| 21:03 | Asked which skill for review | `now what skill should I use to review the HLD and LLD?` |
| 21:05 | Created review prompt (freemium-focused) | `okay write a prompt for this to me so that hld and lld can be reviewed. Also, I should be able to launch, debug, test the app locally and then cloud services can be used. But our focus should be to use freemium services as much as possible.` |
| 21:07 | Executed the review | `review using @[docs/prompts/review-hld-lld-prompt.md]` |

**Skills invoked:** `review`, `codebase-design`  
**Deliverable:** [docs/design-review-results.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/design-review-results.md)

---

### Phase 5: Mermaid Diagram Debugging (22:02 – 22:07)

| Time | What I did | Prompt |
|------|-----------|------|
| 22:02 | Reported Mermaid rendering issue | `I am not seeing mermaid diagrams properly check and fix this` |
| 22:06 | Reported issue persists | `No it is still the same, when I open it in preview it does not work` |

**Outcome:** Fixed Mermaid syntax (escaped characters, special chars in labels)

---

### Phase 6: Visual Guide & Call Flow Diagrams (22:07 – 22:48)

| Time | What I did | Prompt |
|------|-----------|------|
| 22:07 | Requested visual flows + sample UI | `I want to see some flow diagrams, mermaid diagrams which shows the flow, the diagram, the backend and the sample UI, so that I understand the application properly and how the PWA would look like...` |
| 22:30 | **Rejected output** — missing technical depth | `but this does is not the call flow diagram, I don't know what tech stack or what backend service will be invoked for a particular use case. This document is bullshit. Tell me which skill should I use to generate call flow diagram for each use case mentioned in the easyorder-prd.md` |

**Skills invoked:** `canvas-design` (initial visual guide), then `easyorder-call-flows` (custom sequence diagrams)  
**Deliverables:**
- [docs/easyorder-visual-guide.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/easyorder-visual-guide.md)
- [docs/easyorder-call-flows.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/easyorder-call-flows.md)

---

### Phase 7: Tech Stack & Architecture Decision (22:48 – 23:05)

| Time | What I did | Prompt |
|------|-----------|------|
| 22:48 | Asked about tech stack skill | `What should be the backend and frontend techstack for the PWA and which skill should be used to decide the architecture, system design, tech stack etc` |
| 22:50 | Chose Python + LangGraph stack | `Use the /decision-mapping alongside the /domain-modeling skill systematically choose and document the tech stack, system design, and architecture. I want to use Python as the backend, langchain and langGraph as the Agentic framework, is it possible?` |
| 22:52–23:00 | Confirmed decisions (5 rounds) | `yes` × 5 |

**Skills invoked:** `domain-modeling`, `decision-mapping` (custom)  
**Deliverable:** [docs/decision-map.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/decision-map.md)

---

### Phase 8: Architecture Refactoring (23:05 – 01:04)

This was the longest and most iterative phase. I wanted the architecture diagrams to be clear, professional, and split into 3 parts.

| Time | What I did | Prompt |
|------|-----------|------|
| 23:05 | Asked for next steps | `okay now what should be the next step?` |
| 23:10 | Requested HLD update with architecture diagrams | `Before we do that, I want you to update the @[docs/hld.md] with the PWA application architecture which explains the tech stack using mermaid diagram. How the request from the enduser will reach to PWA and eventually to Swiggy MCP...` |
| 23:48 | **Rejected v1** — not professional | `The system architecture is not professional. I don't like it. It also seems incomplete. Refactor it. Feel free to use /design-an-interface or any other skill available to design the system architecture` |
| 00:03 | **Rejected implementation plan** — wanted architecture update only | `No, I asked you to update/refactor the architecture not to give me the implementation plan` |
| 00:10 | Liked v2 but wanted Agentic AI section | `good, I like it. However, I noticed there is nothing mentioned about the AI Agentic architecture, harness, guardrails etc.` |
| 00:15 | Approved implementation plan for 3-part structure | *(approved artifact)* |
| 00:20 | **Rejected v3** — structure was wrong | `No this is not what I wanted. The high level architecture should just mention that we have components for fastapi, swiggy, agentic framework, whatsapp, cloud etc. how they are connected...` |
| 00:25 | Re-stated requirement clearly | `The high level architecture should just mention that we have components... Then there will be 2 detailed architectures one for FastAPI application setup, and the second one is Agentic Framework.` |
| 00:32 | Liked structure, wanted sketch-based refinement | `Okay this is close to what I was expecting. But still we need to refine it. I have a rough sketch for the high level architecture.` *(attached hand-drawn sketch)* |
| 00:49 | Still not satisfied, shared reference image | `It is still not professional and clear. I have give one more example snapshot. update the high level system architecture like this...` *(attached professional reference diagram)* |
| 00:55 | **Rejected emoji/complex Mermaid** — not rendering | `Nope, undo. It's not visible. Let's just create a panel based .png separately and revert the hld.md to previous version` |

**Skills invoked:** `design-an-interface`, `generate_image`  
**Final deliverables:**
- [docs/hld.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/hld.md) — Reverted to clean 3-part structure (Mermaid-lite)
- [docs/diagrams/01-high-level-architecture.png](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/diagrams/01-high-level-architecture.png)
- [docs/diagrams/02-fastapi-application-architecture.png](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/diagrams/02-fastapi-application-architecture.png)
- [docs/diagrams/03-agentic-framework-architecture.png](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/diagrams/03-agentic-framework-architecture.png)

---

## 2. All Deliverables Produced

| # | File | Created via | Purpose |
|---|------|------------|---------|
| 1 | [docs/easyorder-prd.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/easyorder-prd.md) | `grilling` + `to-prd` | Product Requirements Document |
| 2 | [CONTEXT.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/CONTEXT.md) | `domain-modeling` | Domain glossary (Session, Host, Guest, etc.) |
| 3 | [docs/hld.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/hld.md) | `domain-modeling` + `codebase-design` | High-Level Design (3 sections) |
| 4 | [docs/lld.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/lld.md) | `codebase-design` + `design-an-interface` | Low-Level Design (3 sections) |
| 5 | [docs/adr/](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/adr) (3 files) | `domain-modeling` | Architectural Decision Records |
| 6 | [docs/decision-map.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/decision-map.md) | `decision-mapping` | Tech stack decisions with rationale |
| 7 | [docs/design-review-results.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/design-review-results.md) | `review` | HLD/LLD gap analysis |
| 8 | [docs/easyorder-call-flows.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/easyorder-call-flows.md) | Manual (sequence diagrams) | Technical call flows per use case |
| 9 | [docs/easyorder-visual-guide.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/easyorder-visual-guide.md) | `canvas-design` | UI mockup descriptions |
| 10 | [docs/diagrams/](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/diagrams) (3 PNGs) | `generate_image` | Panel-based architecture diagrams |
| 11 | [docs/prompts/](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/prompts) (3 files) | Manual | Reusable prompts for each phase |

---

## 3. Skills Invoked — Full Map

| Skill | Used for | Trigger prompt pattern |
|-------|---------|----------------------|
| **grilling** (`/grill-me`) | Stress-test the product idea before writing PRD | `Analyze X, /grill-me on my architecture and plan` |
| **to-prd** | Generate structured PRD from raw product doc | `create a PRD using the /to-prd skill` |
| **domain-modeling** | Build glossary in CONTEXT.md, identify bounded contexts | `Use the /domain-modeling skill...` |
| **codebase-design** | Design deep modules, testing seams, Protocol interfaces | Included in HLD/LLD prompt |
| **design-an-interface** | Compare alternative interface designs | `Feel free to use /design-an-interface` |
| **decision-mapping** | Document tech stack choices with rationale | `Use the /decision-mapping alongside the /domain-modeling skill` |
| **review** | Review HLD/LLD against PRD, find gaps | `review using @[docs/prompts/review-hld-lld-prompt.md]` |
| **canvas-design** | Generate visual UI mockup descriptions | Triggered when asking for "sample UI" |
| **generate_image** | Create professional .png architecture diagrams | `Let's just create a panel based .png separately` |

---

## 4. What I Liked ✅

1. **Skill-based workflow** — asking "which skill should I use for X?" and then composing skills together produced better results than freeform prompting
2. **Prompt versioning** — storing reusable prompts in `docs/prompts/` so I can re-run them on new projects
3. **Domain modeling first** — building the glossary in `CONTEXT.md` before writing code ensured consistent terminology everywhere
4. **ADR approach** — recording architectural decisions with rationale made the "why" traceable
5. **Decision mapping** — systematically evaluating tech stack options with trade-off tables
6. **3-part HLD structure** — separating High-Level Overview → FastAPI Details → Agentic AI Details made the architecture digestible
7. **Panel-based PNG diagrams** — professional visual output when Mermaid diagrams didn't render well
8. **Grilling before building** — the `/grill-me` skill caught assumptions early

---

## 5. What I Disliked / Corrected ❌

1. **Mermaid rendering issues** — complex Mermaid with emojis, subgraphs, and special chars didn't render in VS Code preview. Had to fall back to `.png`.
2. **Overly verbose first drafts** — initial architecture diagrams were too flat and lacked professional structure. Took 5+ iterations.
3. **Agent gave implementation plan when I asked for architecture update** — I had to explicitly say "No, I asked you to update/refactor the architecture not to give me the implementation plan"
4. **Call flow diagrams were missing technical depth** — first attempt was "bullshit" (my words) because it didn't show which backend service gets invoked for each use case
5. **Merging sections** — the agent kept merging the high-level overview with the detailed sections instead of keeping them strictly separate
6. **Unsolicited complexity** — over-engineered Mermaid diagrams with too many nodes/arrows that were unreadable

---

## 6. How I Like to Work — Working Style Preferences

### Process
- **Document-first, code-later** — I want complete PRD → HLD → LLD → Review before writing any code
- **Skill-driven workflow** — I prefer composing named skills (`/grill-me`, `/domain-modeling`, etc.) rather than freeform prompting
- **Prompt versioning** — I store reusable prompts in `docs/prompts/` so they can be re-run
- **Iterative refinement** — I expect to iterate 3–5 times on architecture diagrams until they match my mental model
- **Reference images** — I share hand-drawn sketches and reference screenshots to communicate what I want visually

### Communication
- **Be specific** — I ask "which skill should I use?" not "help me design"
- **Direct rejection** — I say "this is bullshit" or "undo" when output doesn't meet expectations. Don't take it personally.
- **I confirm with short replies** — `yes`, `agree`, `proceed` mean go ahead; don't ask again
- **Don't re-explain** — once I approve, execute. Don't summarize back to me.

### Architecture & Design
- **3-part architecture structure**: High-Level Overview (bird's-eye) → Detailed App Architecture → Detailed Agentic AI Architecture
- **Panel-based diagrams** — I prefer clean, color-coded panels with subtitles over spaghetti graphs
- **Professional quality** — architecture diagrams should look like they came from an engineering design doc, not a tutorial
- **I want to own the codebase** — explain everything so I can debug it myself. I am the owner.
- **Freemium first** — always prefer free-tier services (WhatsApp Sandbox, Firestore Emulator, Ollama, Google AI Studio free tier)

### Tech Preferences
- **Backend:** Python 3.12 + FastAPI
- **Agentic:** LangGraph + LangChain
- **Database:** Cloud Firestore (real-time sync)
- **LLM:** Ollama (local dev) → Gemini Flash (staging) → GPT-4o mini (prod)
- **Frontend:** Vite + React PWA
- **MCP:** Stdio JSON-RPC via `mcp` Python SDK

---

## 7. Reusable Project Setup Playbook

Use this sequence to bootstrap any new project:

```
Phase 1: Skill Setup
  → Install skills from skills.sh: grilling, review, tdd, frontend-design,
    codebase-design, domain-modeling, design-an-interface, canvas-design

Phase 2: Product Analysis
  → Prompt: "Analyze @[docs/product-documentation.md], /grill-me on my
    architecture and plan and finally create a PRD using the /to-prd skill"
  → Output: docs/<project>-prd.md

Phase 3: HLD & LLD Design
  → Prompt: Use saved prompt from docs/prompts/hld-lld-prompt.md
  → Skills: domain-modeling, codebase-design, design-an-interface
  → Outputs: docs/hld.md, docs/lld.md, CONTEXT.md, docs/adr/

Phase 4: Tech Stack Decisions
  → Prompt: "Use the /decision-mapping alongside the /domain-modeling skill
    to systematically choose and document the tech stack"
  → Output: docs/decision-map.md

Phase 5: Design Review
  → Prompt: Use saved prompt from docs/prompts/review-hld-lld-prompt.md
  → Skills: review, codebase-design
  → Output: docs/design-review-results.md

Phase 6: Architecture Diagrams
  → Generate .png panel-based diagrams using generate_image
  → 3 diagrams: high-level, app-detailed, agentic-detailed
  → Output: docs/diagrams/

Phase 7: Implementation
  → (Not started today — next session)
```

---

## 8. Files to Version

All reusable assets to copy into new projects:

```
docs/prompts/
├── skills_prompt.md          # Role → skill mapping
├── hld-lld-prompt.md         # Prompt to generate HLD/LLD
└── review-hld-lld-prompt.md  # Prompt to review HLD/LLD

.agents/skills/               # Installed skill definitions
CONTEXT.md                    # Domain glossary template
docs/adr/                     # ADR template structure
```
