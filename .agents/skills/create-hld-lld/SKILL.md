---
name: create-hld-lld
description: Create generic High-Level Design (HLD) and Low-Level Design (LLD) documents from a PRD, product brief, issue set, or early project requirements. Use when the user asks to produce architecture/design docs, initiate an HLD/LLD design phase, turn requirements into system design, or prepare implementation-ready design artifacts using dependent skills such as domain-modeling, grill-with-docs, decision-mapping, codebase-design, and design-an-interface.
---

# Create HLD/LLD

## Workflow

Use this skill to turn requirements into durable HLD and LLD artifacts for any project. Treat project names, paths, domain terms, services, and cloud choices as variables discovered from the repository and the user.

1. Locate the source requirements.
   - Prefer a user-specified PRD, product brief, issue list, README, or docs folder.
   - If no source is specified, inspect likely files such as `docs/*prd*.md`, `docs/*requirements*.md`, `README.md`, project issue trackers, or planning docs.
   - Confirm the chosen source briefly if multiple credible sources conflict.

2. Apply domain discovery before design.
   - Use `domain-modeling` directly or through `grill-with-docs` when available.
   - Extract core domain terms, actors, workflows, states, invariants, and external dependencies.
   - Update or create the project glossary in the repository's established location. Prefer existing files such as `CONTEXT.md`, `docs/glossary.md`, or `docs/domain.md`; if none exist, use `CONTEXT.md`.

3. Ask only the critical unresolved design questions.
   - Ask one question at a time when the answer materially changes architecture.
   - Focus on product scope, nonfunctional requirements, integration constraints, data ownership, deployment environment, privacy/security expectations, cost constraints, and local development needs.
   - Continue with explicit assumptions when a question is useful but not blocking.

4. Create the HLD.
   - Use `decision-mapping` when available to sequence key architecture choices.
   - Document system context, actors, major components, data flows, integration points, deployment/runtime shape, trust boundaries, observability, operational risks, and major tradeoffs.
   - Include diagrams when they clarify the design. Use Mermaid unless the repository has an established diagram format.
   - Record significant decisions as ADRs in the repo's established ADR directory. Prefer `docs/adr/`.

5. Create the LLD.
   - Use `codebase-design` to define deep modules, clear ownership boundaries, and testing seams.
   - Use `design-an-interface` when an important interface has multiple plausible shapes or affects many downstream modules.
   - Specify module responsibilities, public interfaces, data models, API contracts, persistence schema, dependency injection points, error modes, retries/timeouts, idempotency, authorization checks, and local test doubles.
   - Tie every important interface back to a requirement, user story, or domain invariant.

6. Produce implementation-ready artifacts.
   - Prefer existing filenames if the repo has conventions.
   - Otherwise write HLD to `docs/hld.md` and LLD to `docs/lld.md`.
   - Include an implementation handoff section with open questions, risks, and test strategy.

## Output Standards

Keep the HLD readable by product and engineering stakeholders. Keep the LLD precise enough that another agent or engineer can implement from it without rediscovering core decisions.

The final response should summarize:

- The source requirements used.
- The files created or updated.
- The major assumptions and unresolved questions.
- Any dependent skills that were unavailable or not used.

## Dependency Handling

This skill assumes the dependent skills may or may not be installed in the current project. If a named skill is available, read and follow it. If it is missing, continue with equivalent general engineering practice and state the gap in the final response.
