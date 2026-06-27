# Prompt: Create High-Level Design (HLD) and Low-Level Design (LLD)

You can copy and paste the prompt below into the assistant chat to initiate the HLD/LLD design phase:

```text
Please read the EasyOrder PRD in docs/easyorder-prd.md.

I want you to prepare the High-Level Design (HLD) and Low-Level Design (LLD) for the EasyOrder system by applying the following skills:

1. High-Level Design (HLD) using the 'domain-modeling' (via 'grill-with-docs') and 'decision-mapping' skills:
   - Identify the core domain terms and build our system glossary in `CONTEXT.md` (e.g., Session, Host, Guest, Consolidated Cart, Degraded State).
   - Draft and create Architectural Decision Records (ADRs) under `docs/adr/` for significant decisions (such as using Firebase/Firestore for real-time synchronization, sequential checkouts for Food/Instamart, and mention-only WhatsApp polling).
   - Define system-wide block diagrams showing the interactions between the WhatsApp Bot gateway, the Collaborative PWA, the Orchestrator backend, and the Swiggy MCP servers.

2. Low-Level Design (LLD) using the 'codebase-design' and 'design-an-interface' skills:
   - Design the backend modules (Orchestrator, FoodWorker, InstamartWorker, BudgetQtyWorker, SessionStore, and SwiggyMcpClient) as deep modules.
   - Define the exact class signatures, interfaces, dependencies (injecting MCP clients), and error modes.
   - Identify clear testing seams for unit and integration testing (e.g., how to mock the Swiggy MCP server latency to test the 2.5-second timeout and graceful degradation).
   - If there are multiple interface designs for the Orchestrator state updates, use the 'design-an-interface' ("design it twice") approach to compare alternatives and choose the best interface.

Please initiate this design phase by first asking me the most critical design questions one-by-one to align on our HLD.
```
