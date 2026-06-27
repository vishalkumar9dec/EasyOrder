# AI Food & Occasion Concierge Product Documentation

## 1. Product Summary

**Product name:** EasyOrder

EasyOrder is a WhatsApp-first agentic AI assistant and collaborative Web/PWA interface that helps groups plan, optimize, and order food/supplies using Swiggy MCP (Model Context Protocol). 

Instead of a single host facing decision fatigue and manual cart building, EasyOrder integrates into WhatsApp group chats to capture group intent, automatically coordinates preferences via a shared Web/PWA planning canvas, builds unified baskets across Swiggy verticals, and hands over a consolidated checkout link to the host via Swiggy OAuth.

## 2. Swiggy Builder Program Context

This product exists because of the Swiggy Builder Program, also called Builders Club. The program gives accepted developers a path to build AI agents and applications on top of Swiggy's MCP servers.

Swiggy MCP exposes three major commerce surfaces:

| MCP server | Endpoint path | Product area |
| --- | --- | --- |
| Food | `/food` | Restaurant discovery, menus, ordering, and order-related flows |
| Instamart | `/im` | Grocery, snacks, party supplies, and quick commerce flows |
| Dineout | `/dineout` | Restaurant discovery, table availability, and reservations |

The important strategic difference is that EasyOrder is not based on scraping Swiggy or reverse engineering private APIs. The proposed product is based on approved Swiggy Builder Program access, with local development, staging access, and production access governed by Swiggy's review process.

Current understanding of the Builder Program:

- Developers can build local agents that call Swiggy MCP endpoints.
- Localhost is only the developer's local app environment and OAuth redirect target, not the Swiggy MCP server.
- Swiggy MCP runs on Swiggy-controlled cloud endpoints such as `mcp.swiggy.com/{server}`.
- Staging credentials and production credentials are gated by Swiggy review.
- The product must comply with Swiggy's OAuth, user consent, safety, and production approval requirements.

This matters because the biggest risk is not "there is no Swiggy API." The real risk is dependency on Swiggy's Builder Program policies, available MCP tools, rate limits, staging approval, production approval, and permitted user experience.

Detailed positioning strategy and checklist for Builder Program evaluation is documented in [builder-program-positioning.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/builder-program-positioning.md).

## 3. Why This Product

Food ordering apps are excellent for solo browsing, but group food ordering is fundamentally a **planning and coordination problem** that happens in communication channels.

Current pain points of group ordering:
- **The Host Burden:** One person is forced to collect orders, check dietary restrictions, pass their phone around, or copy-paste individual items.
- **Cart Abandonment:** Group alignment takes so long that delivery times shift, items go out of stock, or users simply lose momentum.
- **Vertical Silos:** Buying food (`/food`) and party supplies/drinks (`/im`) requires placing separate orders in separate visual funnels.

EasyOrder solves this by intercepting the group coordination where it naturally happens (WhatsApp) and moving the visual execution to a collaborative shared canvas (PWA) powered by Swiggy's MCP.

## 4. Core Positioning

EasyOrder should not be positioned as "Swiggy on WhatsApp." That sounds like a thin wrapper over an existing app.

The stronger positioning is:

> A social commerce layer for local commerce that turns group intent into single-tap consolidated orders.

EasyOrder solves group planning moments:
- Friends hosting a party / watching a game
- Families arranging a vegetarian dinner and dessert
- Office managers organizing team lunches
- Last-minute get-togethers needing both meals and grocery supplies

## 5. Target Users

Primary users:
- **Urban Professionals & Roommates:** High-frequency food orderers who host friends often.
- **Office/Team Managers:** People who coordinate lunch orders for 5–15 people weekly.
- **Busy Couples/Families:** Coordinating dinner while commuting home.

## 6. MVP Use Case: Collaborative Party Ordering

The first version focuses on a group of 4–10 people planning food and drinks.

### User Flow:
1. **Initiate on WhatsApp:** The host adds the EasyOrder bot to their WhatsApp group chat and prompts: `@EasyOrder 6 of us want biryani and starters under Rs 3000, arriving in 45 mins.`
2. **AI Intent Parsing & MCP Lookup:** The orchestrator agent calls the Swiggy `/food` MCP tool to search for matching restaurants, cross-referencing rating and ETA constraints.
3. **The Magic Canvas Link:** The bot posts a reply in the WhatsApp group chat: 
   > *"I found 3 great biryani options. Tap this link to add your favorite drinks, customize plates, and checkout: `[easyorder.app/session/123]`"*
4. **Collaborative Planning Canvas (PWA):**
   - Clicking the link opens a lightweight, mobile-first Web PWA.
   - All group members can join the active session.
   - The host sees the AI-recommended biryani and starter packages.
   - Group members can tap to add cold drinks or ice from Swiggy Instamart (`/im`) to the same planning session.
   - Dietary preferences (veg/non-veg split) are clearly visible.
5. **Secure Checkout Handoff:** Once the group is satisfied, the host taps "Order via Swiggy". This triggers the Swiggy OAuth login, matches their delivery address, builds the cart, and redirects them to Swiggy's secure checkout page.
6. **WhatsApp Tracking:** The bot updates the WhatsApp group chat in real-time as the delivery status changes.

## 7. Expansion Use Case: Occasion Concierge & Contextual Recommendations

Once the collaborative food engine is stable, EasyOrder will expand into a proactive occasion concierge:

- **Context-Aware Event Triggers (e.g., FIFA / IPL Tournaments):** The bot monitors external calendars and events. During a match or tournament, it proactively nudges the WhatsApp group:
  > *"Hey! The India vs. Pakistan match starts in 2 hours. 🏏 Chicken tikka platters and chilled drinks are trending near you. Should I set up a group plan?"*
- **Romantic Dinners:** Reserving tables via Dineout (`/dineout`) and ordering flowers/gifts via Instamart (`/im`) as a single, coordinated flow.
- **Birthdays:** Suggesting food, ordering a cake/candles via Instamart, and coordinating invitations.
- **B2B Team Meal Budgets:** Allowing team members to add items to a corporate cart up to their individual budget limits (e.g., Rs. 300 per person), consolidating them automatically into a single Swiggy order.

## 8. Product Surface

- **WhatsApp Group Bot** handles:
  - Natural language triggers and prompts
  - Session link generation
  - Contextual match/tournament prompts (e.g., "FIFA is on tonight, suggest wings")
  - Team status/updates and delivery tracking
  - Reordering shortcuts

- **Collaborative PWA** handles:
  - Multi-user real-time cart collaboration (no app install required)
  - Rich visual display of menus, ratings, and Instamart stock
  - Swiggy OAuth authentication
  - UPI payment splitting or consolidated host checkout
  - Address confirmation

## 9. Agentic Architecture: Orchestrator-Workers Pattern

To support both **modular subagent reasoning** and **low latency**, EasyOrder implements Anthropic's **Orchestrator-Workers** architecture pattern. Rather than executing agents in a slow, sequential loop, workers are executed concurrently using asynchronous parallel processing.

```text
User on WhatsApp Group / PWA Canvas
  │
  ▼
Messaging Gateway / Webhook
  │
  ▼
┌────────────────────────────────────────────────────────┐
│              Orchestrator LLM Agent                    │
│  - Parses raw group intent & constraints               │
│  - Decides which Workers to invoke                     │
│  - Synthesizes final results & updates Session Store    │
└──────────────────────────┬─────────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       │ (Parallel Async)  │ (Parallel Async)  │ (Parallel Async)
       ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Food Worker  │    │  IM Worker   │    │ Budget & Qty │
│ (Food MCP)   │    │  (IM MCP)    │    │ Worker (LLM) │
└──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │ (Synthesis)
                           ▼
               Real-time Session Store
                           │
                           ▼
                Collaborative PWA / Link
```

### Flow Breakdown:
1. **Dynamic Decomposition:** The central Orchestrator LLM receives the input (e.g. `@EasyOrder 5 people watching IPL, budget Rs. 2000, need chicken starters and cold drinks`).
2. **Concurrent Delegation:** The Orchestrator delegates subtasks to specialized Workers:
   - **Food Worker:** Queries `/food` MCP endpoints in parallel for top-rated starter joints with low ETAs.
   - **IM Worker:** Queries `/im` MCP endpoints for cold drinks, chips, and snacks.
   - **Budget & Qty Worker:** Computes serving sizes and validates the combined cost against the budget constraint.
3. **Parallel Execution:** In a language like Node.js or Python, these workers are run concurrently (`Promise.all` or `asyncio.gather`), fetching menu and inventory data in parallel, taking only a single API hop delay (~1-2 seconds).
4. **Synthesis & PWA Update:** The Orchestrator gathers the results, writes the recommended bundle options into the Session Store, and generates the collaborative PWA link for the WhatsApp group.

## 10. Safety and Trust Rules

- **No Autonomous Ordering:** The agent can never place an order or charge a card without explicit user validation and checkout confirmation on the PWA.
- **Cart Sync Verification:** The PWA must re-verify item availability and pricing with Swiggy MCP right before the user initiates OAuth checkout to prevent out-of-stock errors.
- **Clear Quantity Hypotheses:** Group sizes must show serving estimates: *"This package contains 3 main dishes and 2 starters (estimated serving: 5-6 moderate eaters)."*

## 11. LLM Model Selection & Cost Analysis

EasyOrder's Orchestrator-Workers pattern requires low latency, strong JSON schema adherence, and cost efficiency. The following comparison highlights the models evaluated for development and production.

### Model Comparison Table

| Model | Dev Cost (per 1M input) | Dev Cost (per 1M output) | Latency / Speed | JSON/Tool Reliability | Context Window | Key Advantage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Ollama (Llama 3.1 8B)** | **$0.00 (Free)** | **$0.00 (Free)** | Medium | Moderate | 8k–32k | Run locally in Docker; completely free for local testing. |
| **GPT-4o mini** | $0.15 | $0.60 | Extremely Fast | Exceptional | 128k | Lowest paid API cost; best structured tool calling performance. |
| **Gemini 1.5 Flash** | $0.35 (Free on Dev Tier) | $1.50 (Free on Dev Tier) | Fast | Very Good | 1M+ | Free developer tier; huge context window for long menu dumps. |
| **Claude 3.5 Haiku** | $0.25 | $1.25 | Fast | Very Good | 200k | High reasoning quality, but more expensive. |

### Development Cost Estimation (1 Month of Active Testing)
- **Daily Volume Assumption:** 150 test runs per day (Orchestrator-Workers planning loops).
- **Average Context per Run:** ~15,000 input tokens (system instructions + menu dumps) and ~1,500 output tokens (structured cart/PWA payloads).
- **Monthly Volume:** 67.5 Million input tokens and 6.75 Million output tokens.

**Estimated Monthly LLM Bill:**
- **Local Ollama (Docker):** $0.00
- **Gemini 1.5 Flash (Google AI Studio Free Tier):** $0.00
- **GPT-4o mini:** ~$14.18
- **Gemini 1.5 Flash (Paid Tier):** ~$33.75
- **Claude 3.5 Haiku:** ~$25.30

### LLM Strategy for EasyOrder
1. **Local Development (Ollama):** Use Ollama with `llama3.1:8b` locally in Docker to prototype parsing loops and basic state transitions for $0.
2. **Staging / Remote Development (Gemini 1.5 Flash):** Leverage Google AI Studio's free tier for remote testing, utilizing the massive context window to process full Swiggy menus.
3. **Production (GPT-4o mini):** Use GPT-4o mini for live users due to its superior speed and highly reliable structured JSON tool outputs.

## 12. Critical Risks and Product Response

### Platform Dependency & OAuth Access
- **Risk:** Gating of production access by Swiggy if EasyOrder duplicates the native Swiggy experience.
- **Response:** Position EasyOrder as a utility that drives **high-value cart creation** (group orders, event bundles, multi-vertical carts) that Swiggy does not natively facilitate. Build against official Swiggy MCP scopes and implement OAuth flows strictly within Swiggy's guidelines.

### Latency and Token Costs
- **Risk:** Sequential agent chains taking 10+ seconds, causing users to abandon the WhatsApp thread.
- **Response:** Use the concurrent Orchestrator-Workers pattern. Execute subagent calls in parallel, cache frequently queried menus locally, and use lightweight models for simple extraction subtasks to keep latency under 2 seconds.

### WhatsApp API Business Costs
- **Risk:** Paying per conversation on WhatsApp Business API with zero commissions or initial revenue.
- **Response:** Keep WhatsApp interactions short. Move users to the free-hosted PWA canvas as quickly as possible. Use WhatsApp messages primarily for high-value transaction notifications (session created, order dispatched).

### Bill Splitting & Payments
- **Risk:** Hosts are hesitant to order for groups because collecting money afterward is a hassle.
- **Response:** Integrate micro-UPI deep links on the PWA checkout screen, allowing guests to tap and pay their share directly to the host's UPI ID, eliminating post-party awkwardness.

### Out of Stock and Pricing Shifts
- **Risk:** Items chosen in the PWA go out of stock by the time the host checks out on Swiggy.
- **Response:** Implement real-time inventory checks on the PWA. If an item runs out, the agent automatically suggests the closest substitute (e.g., Coke instead of Pepsi) directly on the PWA screen.

## 13. Key Differentiators

EasyOrder wins by solving problems Swiggy's standalone consumer app cannot easily address:
- **Collaborative Group Cart:** Multiple phones adding to the same Swiggy cart in real-time.
- **Multi-Vertical Consolidation:** Building a single plan containing both hot food and grocery supplies.
- **Context-Aware Event Hooks:** Proactively initiating plans based on sports, festivals, or weather conditions.
- **Social Integration:** Sitting inside the WhatsApp chat where the plan is born.
- **Built-in Bill Splitting:** Solving the financial friction of group dining.

## 14. MVP Success Metrics

- **Link Click-Through Rate:** % of WhatsApp users who tap the PWA canvas link.
- **Guest Contribution Rate:** Average number of guests who add/modify items on the PWA canvas per session.
- **Checkout Conversion Rate:** % of initiated sessions that complete a Swiggy checkout.
- **Average Order Value (AOV) Boost:** Average basket value comparison between EasyOrder orders and solo Swiggy orders.
- **7-day Cohort Retention:** Repeat group planning sessions within a week.

## 15. MVP Scope

### Included in v1:
- WhatsApp bot listening to group mentions and parsing group constraints.
- Real-time PWA planning canvas for up to 10 simultaneous users.
- Swiggy Food MCP (`/food`) and Instamart MCP (`/im`) integrations.
- Orchestrator-Workers backend processing queries in parallel.
- Basic visual menu and item selection in the PWA.
- Swiggy OAuth handoff for checkout.
- WhatsApp order status tracking updates.

### Excluded from v1:
- Dineout table reservations (`/dineout`).
- Automatic UPI splitting payments (introduced in Phase 2).
- Advanced AI preference memory (remembering past orders).
- Native iOS/Android app wrappers.

## 16. Roadmap

### Phase 1: Collaborative MVP & Parallel Architecture
Build the WhatsApp group bot, Orchestrator-Workers backend, and real-time collaborative PWA canvas for Swiggy Food & Instamart planning.

### Phase 2: Social, Financial, & Tournament Context
Add UPI deep-link generation for easy group bill splitting and introduce context-aware event triggers (proactive tournament prompts).

### Phase 3: Dineout & Occasions
Introduce `/dineout` table reservations, venue booking suggestions, and complete birthday/occasion planners.

### Phase 4: B2B Slack & Teams Integration
Extend EasyOrder to corporate workspaces (Slack/Teams) with budget limits per employee and consolidated office delivery.

## 17. References

- **Anthropic's "Building Effective Agents" Guide (Orchestrator-Workers):** `https://www.anthropic.com/news/building-effective-agents`
- **LangChain/LangGraph Multi-Agent Workflows:** `https://python.langchain.com/docs/concepts/#multi-agent-systems`
- **Swiggy Builders Club:** `https://mcp.swiggy.com/builders/`
- **Swiggy Developer Quickstart:** `https://mcp.swiggy.com/builders/docs/start/developer/`
- **Swiggy Build an Agent:** `https://mcp.swiggy.com/builders/docs/start/developer/build-an-agent/`
- **Swiggy Authentication:** `https://mcp.swiggy.com/builders/docs/start/authenticate/`
- **Swiggy Access and Onboarding:** `https://mcp.swiggy.com/builders/docs/operate/access/`

## 18. Strategic Conclusion

EasyOrder transitions from a standard food chatbot into a **Social Coordination Layer for Local Commerce**. By leveraging the Swiggy Builder Program, EasyOrder demonstrates how agentic AI can streamline group commerce, reduce cart abandonment, and increase Average Order Value—offering a highly defensible, high-value entry point for a venture-backed startup.
