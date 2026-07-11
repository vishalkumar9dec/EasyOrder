---
name: review-hld-lld
description: Review High-Level Design (HLD) and Low-Level Design (LLD) documents against requirements, codebase realities, architecture quality, interface depth, testability, local development readiness, and cost/deployment constraints. Use when the user asks to review design docs, find gaps before implementation, validate HLD/LLD against a PRD, or prepare a design for execution using dependent skills such as review and codebase-design.
---

# Review HLD/LLD

## Workflow

Use this skill to critique HLD and LLD artifacts for any project. Treat filenames, domain names, technologies, and constraints as project-specific inputs discovered from the repo and user prompt.

1. Locate the review inputs.
   - Prefer user-specified HLD, LLD, PRD, requirements, ADRs, diagrams, and codebase paths.
   - If unspecified, look for likely files such as `docs/hld.md`, `docs/lld.md`, `docs/*prd*.md`, `docs/adr/`, `README.md`, and existing implementation plans.
   - Inspect enough of the codebase to verify whether the design matches actual project structure and conventions.

2. Review spec alignment.
   - Use the `review` skill when available.
   - Trace each important user story, requirement, workflow, actor, integration, and nonfunctional constraint from the PRD or source requirements into the HLD and LLD.
   - Identify missing API contracts, data models, permissions, error states, operational flows, and UX/backend handoffs.

3. Review architecture and interface depth.
   - Use `codebase-design` when available.
   - Check whether modules are deep enough, responsibilities are cohesive, boundaries are clear, and dependencies flow in the intended direction.
   - Challenge shallow wrappers, leaky interfaces, hidden global state, ambiguous ownership, unclear lifecycle rules, and underspecified failure behavior.

4. Review testability and local execution.
   - Verify explicit unit, integration, end-to-end, and manual testing seams.
   - Look for local doubles/emulators for external services, realistic fixture data, reproducible setup commands, seed/reset flows, observability hooks, and debugger-friendly runbooks.
   - Flag designs that require live paid or production-like services for ordinary development unless justified.

5. Review deployment, cost, and operations.
   - Evaluate whether the design states hosting/runtime assumptions, environment variables, secrets, scaling limits, quotas, logging/metrics, alerting, data retention, backup/restore, and rollout strategy.
   - If the user asks for a freemium or low-cost posture, verify the architecture uses free tiers, local emulators, and cheap managed services where practical, while calling out quota and lock-in risks.

6. Report findings.
   - Lead with findings ordered by severity.
   - Ground each finding in file paths and, when possible, line numbers.
   - For every gap, explain impact and a concrete recommended improvement.
   - Include open questions only when they materially affect implementation.

## Output Standards

Use a code-review style report:

- Findings first, ordered by severity.
- Then open questions or assumptions.
- Then a brief summary of strengths or readiness.

Prefer precise, implementable recommendations over general advice. If the design is ready, say so clearly and name any residual risks or test gaps.

## Dependency Handling

This skill assumes the dependent skills may or may not be installed in the current project. If a named skill is available, read and follow it. If it is missing, continue with equivalent general engineering review practice and state the gap in the final response.
