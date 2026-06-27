# Prompt: Review High-Level Design (HLD) and Low-Level Design (LLD)

You can copy and paste the prompt below into the assistant chat to initiate the design review and local-first execution planning phase:

```text
Please read our HLD in docs/hld.md and LLD in docs/lld.md, referencing the PRD in docs/easyorder-prd.md.

I want you to perform a design review using the 'review' and 'codebase-design' skills, with a focus on local development, debuggability, testing, and maximizing freemium cloud services.

Specifically, evaluate our designs along these axes:

1. Spec Alignment ('review' skill):
   - Do the class interfaces, API contracts, and database models in the HLD/LLD cover every user story defined in the PRD?
   - Identify if there are gaps (e.g., how the WhatsApp webhook validates user numbers, how split UPI codes are calculated, or how cart timeouts are reported back to the group).

2. Interface Depth & Testability ('codebase-design' skill):
   - Are the interfaces for Orchestrator, Worker modules, and the Swiggy MCP wrapper sufficiently deep?
   - Are the testing seams clear? Do we have a concrete design for mocking Swiggy MCP servers locally so that we can run end-to-end flow tests without connecting to live staging environments?

3. Local-First & Freemium Strategy:
   - Does the design specify a way to launch, test, and debug the entire application locally (e.g., local Firestore emulator, local Mock Swiggy MCP server, and a local ngrok/localtunnel webhook tunnel for WhatsApp payloads)?
   - Verify that the architecture prioritizes freemium services (such as Firebase Free Tier, Google AI Studio Free Developer Tier for Gemini, and free tunnel/webhook wrappers) to minimize operating costs.

Please report your findings, highlighting any gaps or recommended improvements.
```
