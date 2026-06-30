# EasyOrder — Agent Rules

These rules are automatically loaded by the AI agent at the start of every conversation in this workspace. They encode lessons learned from the design phase and the user's working style preferences.

---

## Process Rules

1. **Git-first workflow.** Always ensure git is initialized. Commit after each completed phase with a descriptive message (e.g., `phase 3: HLD + LLD via domain-modeling`). Never do work that can't be reverted.
2. **Phase ordering.** Follow this strict sequence: PRD → Tech Stack Decisions → HLD/LLD → Review → Architecture Diagrams → Implementation. Never design architecture before choosing the tech stack.
3. **Prompt versioning.** After completing any phase, save the winning prompt (the one that produced accepted output) to `docs/prompts/`. Name it descriptively (e.g., `hld-lld-prompt.md`).
4. **Document-first, code-later.** Complete all design documents (PRD, HLD, LLD, ADRs, decision map) before writing any implementation code.

## Communication Rules

5. **Don't ask "which skill should I use?"** Consult the skill lookup table below and pick the right skill. If genuinely uncertain, offer 2 options with trade-offs — don't ask an open-ended question.
6. **Execute without stopping for confirmation** on multi-step tasks unless there is genuine ambiguity. Short replies like `yes`, `agree`, `proceed` mean go ahead — do not re-confirm.
7. **Don't re-summarize.** After creating or updating an artifact, do not restate its contents. Point to the file and highlight only open questions.
8. **When the user rejects output**, identify the root cause before re-generating. Ask one clarifying question to understand the gap, don't just produce another guess.
9. Sacrifice grammar when talking to me for the sake of saving tokens. However, the documentation, codebase must follow the correct grammar

## Architecture & Design Rules

9. **3-tier architecture structure.** Architecture documentation must always have exactly 3 sections: (1) High-level bird's-eye overview (component boxes + connections + request flow), (2) Detailed application layer, (3) Detailed agentic AI layer.
10. **Professional diagrams = PNG, not Mermaid.** For panel-based, color-coded, or visually complex architecture diagrams, use `generate_image` to produce `.png` files. Save to `docs/diagrams/`. Use Mermaid only for simple flowcharts, sequence diagrams, and state machines inside `.md` files.
11. **Acceptance criteria are mandatory.** Every architecture prompt must specify: structure (sections/layout), visual style (panels/arrows/colors), format (PNG vs Mermaid), and ideally include a reference image.
12. **Keep Mermaid simple.** No emojis, no multi-line labels with special characters, no deeply nested subgraphs. If Mermaid won't render cleanly in VS Code preview, switch to PNG.

## Tech Stack (Locked Decisions)

13. **Backend:** Python 3.12 + FastAPI
14. **Agentic framework:** LangGraph + LangChain
15. **Database:** PostgreSQL via Supabase (real-time sync via Supabase Realtime channels on client, `supabase-py` service role on server, `langgraph-checkpoint-postgres` for agent state)
16. **LLM ladder:** Ollama / Llama 3.1 8B (local dev) → Gemini 1.5 Flash (staging) → GPT-4o mini (production)
17. **MCP transport:** Stdio JSON-RPC via `mcp` Python SDK
18. **Frontend:** Vite + React PWA
19. **Auth:** SHA-256 host token + UUID guest token + Supabase Anonymous Auth
20. **Freemium first:** Always prefer free-tier services. Local dev must run at zero cost (WhatsApp Sandbox, local PostgreSQL via Docker, Ollama, localtunnel).

## Domain Language

21. **Use the glossary.** All code, docs, and conversations must use the domain terms defined in `CONTEXT.md`. Do not invent synonyms (e.g., use "Session" not "Order", use "Host" not "Admin").

## Quality Gates

22. **Every deliverable must be reviewed.** After generating HLD/LLD or code, run the `/review` skill against the PRD before considering the phase complete.
23. **Test seams are mandatory.** Every module must have a `Protocol` interface so production clients can be swapped for mocks in tests.

---

## Skill Lookup Table

Use this instead of asking "which skill should I use?":

| I want to...                          | Use this skill         | Prompt pattern                                        |
|---------------------------------------|------------------------|-------------------------------------------------------|
| Validate or stress-test an idea       | `/grill-me`            | `Analyze X, /grill-me on my plan`                     |
| Write a PRD from raw product doc      | `/to-prd`              | `Create a PRD using /to-prd`                          |
| Build domain glossary (CONTEXT.md)    | `/domain-modeling`     | `Build domain model for X`                            |
| Document tech stack decisions         | `/decision-mapping`    | `Use /decision-mapping to document choices for X`     |
| Design system architecture / modules  | `/codebase-design`     | `Design deep modules for X using /codebase-design`    |
| Compare interface alternatives        | `/design-an-interface` | `Design it twice for X`                               |
| Review docs against PRD               | `/review`              | `Review @[docs/hld.md] against @[docs/easyorder-prd.md]` |
| Generate professional diagram PNGs    | `generate_image`       | `Generate .png diagram of X with [constraints]`       |
| Create call flow sequence diagrams    | *(manual Mermaid)*     | `Create sequenceDiagram for each use case in PRD`     |
| Build or style UI components          | `/frontend-design`     | `Design the PWA layout using /frontend-design`        |
| Write tests first, then implement     | `/tdd`                 | `Implement X using /tdd (red-green-refactor)`         |
| Debug a broken feature                | `/diagnosing-bugs`     | `Diagnose why X is failing`                           |
| Deploy to production                  | `/deploy-to-vercel`    | `Deploy and give me the link`                         |
| Build a food ordering website         | `/food-ordering-website` | `Build a modern food ordering site for [brand]`     |

---

## File Conventions

| Path | Purpose |
|------|---------|
| `CONTEXT.md` | Domain glossary — single source of truth for terminology |
| `docs/easyorder-prd.md` | Product Requirements Document |
| `docs/hld.md` | High-Level Design (3 sections: overview, app, agentic) |
| `docs/lld.md` | Low-Level Design (3 sections: shared, app specs, agentic specs) |
| `docs/adr/` | Architectural Decision Records |
| `docs/decision-map.md` | Tech stack decision rationale |
| `docs/diagrams/` | PNG architecture diagrams |
| `docs/prompts/` | Reusable prompts for each phase |
| `docs/easyorder-call-flows.md` | Technical sequence diagrams per use case |
