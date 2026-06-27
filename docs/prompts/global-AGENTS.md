# Global Agent Rules — Vishal Kumar

These rules apply to ALL projects and workspaces. They encode my universal working style, communication preferences, and process standards.

For project-specific rules, see `.agents/AGENTS.md` in the workspace root.

---

## Process

1. **Git-first.** Ensure git is initialized before any work. Commit after each completed phase. Never do work that can't be reverted.
2. **Document-first, code-later.** Design documents (PRD, HLD, LLD) must be complete and reviewed before writing implementation code.
3. **Prompt versioning.** After completing any major phase, save the winning prompt to `docs/prompts/`. I re-use these across projects.
4. **Phase ordering.** PRD → Tech Stack → Architecture → Review → Implementation. Never design architecture before choosing the tech stack.
5. **Freemium first.** Always prefer free-tier services for local development. Local dev must run at zero cost.

## Communication

6. **Execute without stopping for confirmation** on multi-step tasks. Short replies like `yes`, `agree`, `proceed` mean go ahead — do not re-confirm or re-summarize.
7. **Don't re-summarize.** After creating or updating a file, point to it and highlight only open questions. Do not restate the contents back to me.
8. **When I reject output**, ask one clarifying question to identify the gap before re-generating. Don't produce another guess without understanding why the first attempt failed.
9. **Be direct.** I give direct feedback (including harsh rejection). Don't take it personally, don't apologize excessively — just fix it.
10. **Pick the right tool yourself.** Don't ask me "which skill should I use?" — consult the skill lookup table in the project's `.agents/AGENTS.md` or pick the best option. If genuinely uncertain, offer 2 options with trade-offs.

## Architecture & Design

11. **3-tier architecture structure.** Architecture docs must have 3 sections: (1) High-level bird's-eye overview, (2) Detailed application layer, (3) Detailed agentic/AI layer (if applicable).
12. **Professional diagrams = PNG.** For panel-based, color-coded, or visually complex architecture diagrams, use `generate_image` to produce `.png` files. Use Mermaid only for simple flowcharts and sequence diagrams.
13. **Keep Mermaid simple.** No emojis in node labels, no deeply nested subgraphs, no special characters that break VS Code preview.
14. **Acceptance criteria on every prompt.** Include structure, visual style, format, and reference image when requesting diagrams or design work.
15. **I am the owner.** Explain everything so I can debug, modify, and extend it myself. I don't want black boxes.

## Code Quality

16. **Test seams are mandatory.** Every module must have a `Protocol` interface so production dependencies can be swapped for mocks.
17. **Domain language.** Use the glossary in `CONTEXT.md` (if it exists) for all code, docs, and conversations. Don't invent synonyms.
18. **ADRs for big decisions.** Record significant architectural decisions in `docs/adr/` with rationale, alternatives considered, and trade-offs.

## File Conventions

19. **Standard docs layout:**
    - `CONTEXT.md` — Domain glossary
    - `docs/<project>-prd.md` — Product Requirements Document
    - `docs/hld.md` — High-Level Design
    - `docs/lld.md` — Low-Level Design
    - `docs/adr/` — Architectural Decision Records
    - `docs/decision-map.md` — Tech stack decisions
    - `docs/diagrams/` — PNG architecture diagrams
    - `docs/prompts/` — Reusable prompts per phase
