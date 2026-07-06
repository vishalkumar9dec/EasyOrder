# AI Food & Occasion Concierge Product Documentation

## 1. Product Summary

**Product name:** EasyOrder

EasyOrder is a WhatsApp-first agentic AI assistant and collaborative Web/PWA interface that helps groups plan, optimize, and order food/supplies using Swiggy MCP (Model Context Protocol).

Instead of a single host facing decision fatigue and manual cart building, EasyOrder captures the group's final decision from the host in a direct WhatsApp conversation with the EasyOrder business/test number. It then coordinates preferences via a shared Web/PWA planning canvas, builds unified baskets across Swiggy verticals, and hands over consolidated checkout links to the host via Swiggy OAuth.

The next product direction adds a second WhatsApp surface: a dedicated EasyOrder
business chat for saved lists, reorder help, order-status questions, discovery,
offers, and support-style interactions. This should be built on the same backend
as the current `@EasyOrder` planning flow, but treated as a separate operating
mode with different privacy and intent-routing rules.

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

EasyOrder solves this by meeting the host where the coordination already happened (WhatsApp), accepting the final agreed prompt in a direct EasyOrder conversation, and moving the visual execution to a collaborative shared canvas (PWA) powered by Swiggy's MCP.

For recurring purchases, EasyOrder also solves a second problem: users do not
want to rebuild household or event lists from scratch. A lightweight saved-list
mode lets users add items over time in WhatsApp, then turn the list into a
reviewable cart when they are ready.

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
1. **Agree in WhatsApp, initiate privately:** The group discusses options in a normal WhatsApp group. Once the menu is clear, the host sends the final prompt to the EasyOrder WhatsApp business/test number: `@EasyOrder 6 of us want biryani and starters under Rs 3000, arriving in 45 mins.`
2. **AI Intent Parsing & MCP Lookup:** The orchestrator agent calls the Swiggy `/food` MCP tool to search for matching restaurants, cross-referencing rating and ETA constraints while preserving restaurant identity for every Food item.
3. **The Magic Canvas Handoff:** EasyOrder replies privately to the host's WhatsApp `wa_id` with a WhatsApp-native CTA button or approved template where possible:
   > *"EasyOrder is ready. Review the plan, invite guests, and place the order when you are happy."*
   >
   > CTA: `Review order`

   If CTA/template messaging is unavailable in the current sandbox, EasyOrder falls
   back to concise short branded links. Long tokenized URLs should not be the
   dominant visible content of the WhatsApp reply.
4. **Collaborative Planning Canvas (PWA):**
   - Clicking the link opens a lightweight, mobile-first Web PWA.
   - The session shows the initiating WhatsApp message and key EasyOrder activity
     as a compact timeline.
   - All group members can join the active session.
   - The host sees the AI-recommended biryani and starter packages.
   - Every Food item shows which restaurant it comes from.
   - Every Instamart item shows brand/source context where available.
   - Group members can tap to add cold drinks or ice from Swiggy Instamart (`/im`) to the same planning session.
   - Dietary preferences (veg/non-veg split) are clearly visible.
5. **Secure Checkout Handoff:** Once the group is satisfied, the host taps "Order via Swiggy". The PWA previews the required Swiggy orders: one checkout per Food restaurant plus a separate Instamart checkout when grocery items exist. This triggers the Swiggy OAuth login, matches the delivery address, builds each checkout payload, and redirects the host through the required Swiggy checkout pages.
6. **WhatsApp Tracking:** EasyOrder sends status and delivery updates privately to the host, who can forward the relevant updates to the group.

## 7. Expansion Use Case: Occasion Concierge & Contextual Recommendations

Once the collaborative food engine is stable, EasyOrder will expand into a proactive occasion concierge:

- **Context-Aware Event Triggers (e.g., FIFA / IPL Tournaments):** The bot monitors external calendars and events. During a match or tournament, it proactively nudges opted-in hosts:
  > *"Hey! The India vs. Pakistan match starts in 2 hours. 🏏 Chicken tikka platters and chilled drinks are trending near you. Should I set up a group plan?"*
- **Romantic Dinners:** Reserving tables via Dineout (`/dineout`) and ordering flowers/gifts via Instamart (`/im`) as a single, coordinated flow.
- **Birthdays:** Suggesting food, ordering a cake/candles via Instamart, and coordinating invitations.
- **B2B Team Meal Budgets:** Allowing team members to add items to a corporate cart up to their individual budget limits (e.g., Rs. 300 per person), consolidating them automatically into a single Swiggy order.

## 7A. Expansion Use Case: Dedicated Business Chat And Saved Lists

The dedicated EasyOrder business chat is a practical expansion because users can
interact with it like a normal business assistant rather than remembering a long
prompt. It should support:

- **Saved lists:** `add vim bar to monthly`, `show monthly list`, `add today's
  list to cart`.
- **Order memory:** `what was my last order?` and `repeat last match-night
  snacks`, gated by user identity and available Swiggy scopes.
- **Status:** `when will my order arrive?`, only when EasyOrder has access to the
  relevant active order status.
- **Discovery:** `nearest best chole bhature` and `best upcoming offers`, with
  source attribution and no hidden checkout.
- **Sharing:** `share the order details in the group`, implemented as a safe
  shareable summary or guest link after explicit confirmation.

Professional caution: this is a real product expansion, not just a prompt tweak.
It requires persistent user identity, saved-list storage, intent routing,
privacy-safe summaries, template/interactive message configuration, and graceful
fallbacks when Swiggy order-history or offer scopes are unavailable.

## 8. Product Surface

- **WhatsApp Direct Host Assistant** handles:
  - Natural language triggers and prompts from the host's WhatsApp `wa_id`
  - Session link generation
  - WhatsApp-native CTA/template handoff or short-link fallback
  - User-visible session activity timeline events
  - Contextual match/tournament prompts (e.g., "FIFA is on tonight, suggest wings")
  - Host-facing status updates and delivery tracking
  - Reordering shortcuts

- **Dedicated EasyOrder Business Chat** handles:
  - Free-form direct conversation with the EasyOrder business account
  - Saved-list commands and wishlist-to-cart conversion
  - Discovery and offer questions
  - Order history/status questions where official data access exists
  - Safe share-summary generation

- **Collaborative PWA** handles:
  - Multi-user real-time cart collaboration (no app install required)
  - Rich visual display of menus, ratings, and Instamart stock
  - Swiggy OAuth authentication
  - UPI payment splitting or consolidated host checkout
  - Address confirmation

## 9. Agentic Architecture: Orchestrator-Workers Pattern

To support both **modular subagent reasoning** and **low latency**, EasyOrder implements Anthropic's **Orchestrator-Workers** architecture pattern. Rather than executing agents in a slow, sequential loop, workers are executed concurrently using asynchronous parallel processing.

```text
Host on WhatsApp Direct Chat / PWA Canvas
  │
  ▼
Messaging Gateway / Webhook
  │
  ▼
┌────────────────────────────────────────────────────────┐
│              Orchestrator LLM Agent                    │
│  - Parses final group intent & constraints             │
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
4. **Synthesis & PWA Update:** The Orchestrator gathers the results, writes the recommended bundle options into the Session Store, and generates a private host link plus a shareable guest PWA link.

## 10. Safety and Trust Rules

- **No Autonomous Ordering:** The agent can never place an order or charge a card without explicit user validation and checkout confirmation on the PWA.
- **Review Before Wishlist Checkout:** Saved lists and wishlists can become carts,
  but user review is mandatory before checkout. Offer-driven substitutions must
  be visible before order confirmation.
- **Cart Sync Verification:** The PWA must re-verify item availability and pricing with Swiggy MCP right before the user initiates OAuth checkout to prevent out-of-stock errors.
- **Source Transparency:** The PWA must show restaurant names for Food items and brand/source context for Instamart items before checkout.
- **Restaurant-Bounded Food Checkout:** Swiggy Food orders cannot span multiple restaurants, so EasyOrder must split Food checkout steps by restaurant instead of presenting one combined Food order.
- **Clear Quantity Hypotheses:** Group sizes must show serving estimates: *"This package contains 3 main dishes and 2 starters (estimated serving: 5-6 moderate eaters)."*
- **No Passive Group Reading:** Dedicated business-chat intelligence must not
  become silent monitoring of ordinary WhatsApp groups. Group sharing requires
  explicit user action and privacy-safe links or summaries.

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

### Dedicated Business Chat Scope Creep
- **Risk:** Turning EasyOrder into a general-purpose shopping/support bot before
  session creation, checkout, identity, and data access are reliable.
- **Response:** Sequence the build: message timeline and CTA polish first, then
  deterministic intent routing, then saved lists, then order history/status and
  offers. Keep unsupported intents graceful and honest.

### WhatsApp Template And Interactive Message Limits
- **Risk:** Product copy assumes arbitrary `href` text or buttons that the
  WhatsApp Cloud API does not render in ordinary text messages.
- **Response:** Design the handoff around supported interactive messages or
  approved templates, with short branded links as fallback.

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
- **Recurring Commerce Memory:** Saved household/event lists convert repeat
  purchase intent into reviewable Swiggy carts.

## 14. MVP Success Metrics

- **Link Click-Through Rate:** % of invited participants who tap the PWA canvas link.
- **Guest Contribution Rate:** Average number of guests who add/modify items on the PWA canvas per session.
- **Checkout Conversion Rate:** % of initiated sessions that complete a Swiggy checkout.
- **Average Order Value (AOV) Boost:** Average basket value comparison between EasyOrder orders and solo Swiggy orders.
- **7-day Cohort Retention:** Repeat group planning sessions within a week.
- **Saved List Activation:** % of users who create at least one named list.
- **List-To-Cart Conversion:** % of saved lists converted into a reviewable cart.
- **WhatsApp CTA Tap Rate:** % of handoff messages where the user taps the CTA or
  short link.

## 15. MVP Scope

### Included in v1:
- WhatsApp direct host assistant parsing `@EasyOrder` prompts sent to the EasyOrder business/test number.
- Inbound WhatsApp message visible in the PWA session timeline.
- WhatsApp handoff with CTA/template where supported, or short branded-link fallback.
- Real-time PWA planning canvas for up to 10 simultaneous users.
- Swiggy Food MCP (`/food`) and Instamart MCP (`/im`) integrations.
- Orchestrator-Workers backend processing queries in parallel.
- Basic visual menu and item selection in the PWA.
- Swiggy OAuth handoff for checkout.
- WhatsApp order status tracking updates sent privately to the host.

### Excluded from v1:
- Dineout table reservations (`/dineout`).
- Automatic UPI splitting payments (introduced in Phase 2).
- Advanced AI preference memory beyond explicitly named saved lists.
- Autonomous purchase from a wishlist without user review.
- Native iOS/Android app wrappers.

## 16. Roadmap

### Phase 1: Collaborative MVP & Parallel Architecture
Build the WhatsApp direct host assistant, Orchestrator-Workers backend, and real-time collaborative PWA canvas for Swiggy Food & Instamart planning.

### Phase 2: WhatsApp Product Surface And Saved Lists
Show inbound WhatsApp messages in the PWA timeline, replace raw URL-heavy
handoff with CTA/template or short-link messaging, and add saved household/event
lists that convert into reviewable carts.

### Phase 3: Dedicated Business Assistant
Add direct EasyOrder business-chat intents for discovery, offers, order history,
active order status, and safe group-share summaries.

### Phase 4: Social, Financial, & Tournament Context
Add UPI deep-link generation for easy group bill splitting and introduce context-aware event triggers (proactive tournament prompts).

### Phase 5: Dineout & Occasions
Introduce `/dineout` table reservations, venue booking suggestions, and complete birthday/occasion planners.

### Phase 6: B2B Slack & Teams Integration
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
