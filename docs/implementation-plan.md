# EasyOrder Implementation Plan

## Purpose

This plan turns the EasyOrder PRD, HLD, LLD, ADRs, glossary, and diagrams into an implementation sequence that can be followed after the GitHub repository is created. It is ordered by dependency: foundation first, then backend contracts, agent orchestration, persistence, collaborative PWA, checkout, external integrations, and release hardening.

## Source Of Truth

- Product scope: [easyorder-prd.md](easyorder-prd.md)
- Architecture: [hld.md](hld.md)
- Code-level design: [lld.md](lld.md)
- Domain language: [../CONTEXT.md](../CONTEXT.md)
- Architecture diagrams: [diagrams/](diagrams/)
- Accepted decisions:
  - [ADR 0001: PostgreSQL (Supabase) for Real-Time Session State Synchronization](adr/0001-firestore-realtime-sync.md)
  - [ADR 0002: Sequential Checkout Splits for Food and Grocery Carts](adr/0002-sequential-checkout-splits.md)
  - [ADR 0003: Mention-Only Listening for the WhatsApp Group Bot](adr/0003-mention-only-webhook.md)

ADR 0001 supersedes older Firestore/Firebase references in the PRD or README. The implementation should use PostgreSQL/Supabase for persistence, row-level security, and realtime collaboration.

## Implementation Principles

1. Build vertical slices that can be manually tested before depending on them.
2. Keep production integrations behind interfaces so local mocks can exercise the complete flow without paid services.
3. Treat security controls as product behavior, not late-stage hardening.
4. Prefer deterministic tests around orchestration, tokens, persistence, and checkout splitting.
5. Keep the agent non-authoritative: it recommends and compiles carts, but only the host can authorize checkout.
6. Make degraded behavior visible and testable whenever Food, Instamart, LLM, OAuth, or Realtime dependencies fail.

## Recommended Repository Standards

### Branching

- `main`: always releasable.
- `develop`: integration branch for completed task slices.
- `feature/<task-id>-short-name`: one task or one coherent task group.
- `fix/<issue-id>-short-name`: defects found during testing.

### Pull Request Expectations

Each pull request should include:

- Linked task ID from [implementation-tasks.md](implementation-tasks.md).
- Scope summary and screenshots or API examples where relevant.
- Automated test evidence.
- Manual validation notes.
- Known limitations or follow-up tasks.

### Quality Gates

Every merged task should pass the relevant subset of:

- Backend formatting and linting.
- Backend type checks.
- Backend unit tests.
- Backend integration tests for database and API slices.
- Frontend formatting and linting.
- Frontend unit/component tests.
- End-to-end smoke tests for critical user flows once the PWA exists.
- Security regression tests for token separation, RLS, webhook verification, and prompt-injection blocking.

### Definition Of Done

A task is complete when:

- The implementation matches the relevant HLD/LLD contract.
- Automated tests cover success, failure, and edge behavior proportional to risk.
- The manual test steps can be followed locally.
- Logs and error responses are actionable.
- Documentation or environment samples are updated when setup changes.
- No mock-only behavior is accidentally exposed as production behavior.

## Phased Delivery Plan

### Phase 0: Repository And Local Foundation

Create the monorepo structure, toolchains, local environment files, Docker services, and baseline CI. This phase exists to prevent later tasks from inventing setup conventions independently.

Exit criteria:

- Backend, frontend, and database can start locally.
- CI can run lint and test commands.
- Environment variables are documented in sample files.
- Mock integrations are selected by configuration.

### Phase 1: Domain Contracts And Persistence

Implement shared schemas, database migrations, token generation, and storage adapter interfaces. This phase makes the session and cart model real before API and PWA features are layered on top.

Exit criteria:

- Sessions and cart items can be created, read, updated, and deleted locally.
- Host and guest tokens are generated and hashed according to the LLD.
- RLS policies are implemented and testable.
- Supabase Realtime is enabled for `cart_items`.

### Phase 2: Backend API Skeleton

Implement the FastAPI application shell, configuration, middleware, health checks, webhook verification, and checkout route contracts. The routes can return mock or stubbed responses until downstream services are ready.

Exit criteria:

- FastAPI starts locally and exposes documented endpoints.
- WhatsApp webhook verification works.
- Non-`@EasyOrder` messages are ignored with `200 OK` and no session creation.
- Request logging, CORS, and structured error responses are in place.

### Phase 3: Agentic Orchestration

Implement LangGraph state, guardrails, intent parsing, Swiggy worker calls, budget/dietary validation, degradation handling, and database persistence. Keep the Swiggy client mocked by default for local work.

Exit criteria:

- A tagged WhatsApp-style prompt can create an `ACTIVE` or `DEGRADED` session.
- Prompt injection is blocked before LLM ingestion.
- PII is sanitized before intent parsing.
- Worker timeouts return partial results within the 2.5-second SLA.
- Recommendations and warnings are persisted.

### Phase 4: Collaborative PWA Canvas

Implement the mobile-first PWA session page, token bootstrap, cart display, item editing, Supabase Realtime subscriptions, budget warnings, dietary tags, degraded-state banners, and host-only checkout controls.

Exit criteria:

- A guest link opens a session and displays the current cart.
- Multiple local browser clients see cart changes in realtime.
- Guests cannot see or trigger host-only checkout actions.
- Budget and dietary warnings are visible without blocking collaboration.

### Phase 5: Checkout And OAuth Handoff

Implement pre-checkout validation, substitute suggestions, Swiggy OAuth callback confirmation, Food/Instamart cart splitting, sequential checkout URLs, and partial checkout recovery.

Exit criteria:

- Host can validate the cart before checkout.
- Out-of-stock or price-changed items block checkout with useful recovery guidance.
- Food and Instamart payloads are split according to ADR 0002.
- Sequential checkout state is tracked against the EasyOrder session.

### Phase 6: External Integrations And Sandbox Readiness

Connect the WhatsApp sandbox, Swiggy MCP client, local tunnel workflow, production-like environment configuration, and template-message stubs.

Exit criteria:

- Meta webhook verification and message ingestion work through a tunnel.
- Swiggy MCP client can be swapped between mock and real modes.
- Host and group messages are sent through the configured WhatsApp provider.
- Integration failures degrade or retry according to documented behavior.

### Phase 7: Hardening, Observability, And Release Candidate

Add audit logging, tracing, rate limiting, security tests, load/concurrency checks, frontend accessibility passes, and release documentation.

Exit criteria:

- A complete local demo can run from WhatsApp-style prompt to sequential checkout mock.
- Critical security paths have regression tests.
- Logs support debugging a session by `session_id`.
- Runbooks exist for local setup, common failures, and release validation.

## Cross-Cutting Test Strategy

### Unit Tests

Use unit tests for pure or interface-driven behavior:

- Token generation and hashing.
- Pydantic schema validation.
- Prompt-injection detection.
- PII sanitization.
- Intent parser schema handling with mocked LLM responses.
- Budget calculation, dietary validation, mock-item filtering.
- Cart split logic.

### Integration Tests

Use integration tests where behavior depends on infrastructure boundaries:

- FastAPI route behavior with dependency overrides.
- PostgreSQL migrations and repository methods.
- RLS policy checks with host, guest, and invalid tokens.
- Supabase Realtime event flow where local stack support exists.
- Swiggy MCP client against mock server.
- OAuth callback confirmation against mock Swiggy token and cart endpoints.

### End-To-End Tests

Use browser/API tests for complete user flows:

- Host starts a session from a tagged WhatsApp webhook payload.
- Guest opens the PWA link and edits cart items.
- Two browser clients receive realtime cart updates.
- Host sees checkout controls and guest does not.
- Checkout validation detects unavailable items.
- Host completes mocked sequential checkout for Food and Instamart.

### Manual Testing

Every task should preserve a local manual path. Prefer curl commands, local browser URLs, and mock toggles over requiring live provider accounts during feature development.

Manual testing should verify:

- Expected happy path.
- One failure or degraded path.
- Logs or UI state make the result understandable.

## Debugging Strategy

### Backend

- Log every request with `request_id`, `session_id` when available, route, status code, and latency.
- Log agent node transitions with node name, duration, status, warning count, and error count.
- Redact tokens, OAuth codes, phone numbers, emails, and card-like values.
- Include dependency mode in startup logs: mock or real WhatsApp, mock or real Swiggy MCP, local or hosted Supabase.

### Database

- Use migration checks in CI.
- Keep seed fixtures small and deterministic.
- Provide SQL snippets for inspecting a session, cart items, RLS visibility, and checkout status.

### Agent

- Preserve sanitized input, parsed intent, warnings, and degraded verticals.
- Store enough structured state to reproduce failures without storing private raw chat content unnecessarily.
- Add timeout metrics per worker.

### Frontend

- Expose non-sensitive session/debug status in development mode only.
- Use browser console logging for realtime subscribe/unsubscribe lifecycle in development.
- Add clear UI states for loading, disconnected, degraded, unauthorized, validation failed, and checkout partial completion.

## Release Readiness Checklist

- All MVP user stories from the PRD are mapped to implementation tasks or explicitly deferred.
- `@EasyOrder` mention-only behavior is verified.
- Host and guest authorization boundaries are verified.
- RLS prevents cross-session data access.
- Agent cannot place orders or charge users.
- Checkout requires explicit host action.
- Food and Instamart checkout split is covered by tests.
- Degraded state is visible in the PWA.
- Local setup can be completed from a clean clone.
- Secrets are documented but not committed.
- Diagrams and docs reflect Supabase as the realtime source of truth.

