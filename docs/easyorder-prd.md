# Product Requirements Document (PRD) - EasyOrder

## Problem Statement

Group food and supply ordering is currently a high-friction coordination problem. Hosts face decision fatigue, dietary collection hassles, and manual order compilation. Gathering preferences in chat groups leads to cart abandonment, while combining main dishes (from restaurant menus) and grocery/supplies (drinks, ice, plates) requires ordering via separate visual screens and payment processes. 

## Solution

EasyOrder is a WhatsApp-first agentic assistant linked with a collaborative Web PWA canvas. It captures the group's final ordering intent from the host in a direct WhatsApp conversation with the EasyOrder business/test number, parses constraints via an Orchestrator-Workers LLM pattern, recommends selections via a multi-user visual planning canvas, and compiles unified carts. It then hands over sequential checkout sessions to the host using secure Swiggy OAuth.

## User Stories

1. As a party host, I want to send EasyOrder the final menu we agreed on from my WhatsApp number, so that it can turn the group decision into an order plan.
2. As a party host, I want to request biryani and starters for a group of 6 under a specific budget, so that the AI can suggest options matching my pricing constraints.
3. As a group member, I want the host to share a collaborative link after EasyOrder creates the session, so that I can view and customize the group's order from my own device.
4. As a group guest, I want to open the shared PWA link, so that I can see the host's selected food packages, the restaurant each Food item comes from, and add my own choice of drinks from Instamart.
5. As a group member, I want to see real-time updates when other guests add items to the canvas, so that we do not duplicate selections.
6. As a guest with dietary restrictions, I want to mark my additions as vegetarian or gluten-free on the canvas, so that the host can ensure my preferences are respected.
7. As a host, I want the bot to perform a final stock and price check, so that I don't attempt to order items that recently went out of stock.
8. As a host, I want to log in using Swiggy OAuth, so that my cart is created directly on my Swiggy account.
9. As a host, I want food items grouped by restaurant and grocery items grouped by Instamart brand/vendor context, so that I know exactly where every item will be ordered from before payment.
10. As a host, I want to checkout sequentially for each required Swiggy order, so that Food items from different restaurants and Instamart items are placed as separate Swiggy orders when Swiggy requires it.
11. As a host, I want EasyOrder to send order status and delivery updates privately to me, so that I can forward or summarize updates for the group.
12. As a group host, I want to opt in to sports or tournament updates during PWA session setup, so that the bot can nudge us with relevant food deals during matches.
13. As a WhatsApp user, I want EasyOrder to ignore general conversations and only act on messages tagged with `@EasyOrder`, so that my privacy is respected.

## Implementation Decisions

### 1. WhatsApp to PWA Session State & Handoff
* **Tokenized Access:** EasyOrder generates unique session URLs formatted as `https://easyorder.app/session/<session_id>?token=<guest_token>`. The guest token provides passwordless read/write access to the specific cart, while the host token links to the initiating WhatsApp `wa_id` for Swiggy OAuth checkout.
* **Real-time Sync:** A shared state store (e.g., Firebase Firestore or Realtime Database) synchronizes mutations instantly across up to 10 active PWA clients in the same session.

### 2. Orchestrator-Worker Concurrency and Fault Tolerance
* **Orchestrator-Workers Design Pattern:** Inspired by Anthropic's multi-agent architecture. The main Orchestrator LLM parses the group's natural language intent and delegates tasks to:
  * **Food Worker** (queries `/food` MCP endpoints)
  * **IM Worker** (queries `/im` MCP endpoints)
  * **Budget & Qty Worker** (computes cost analysis and serving estimates)
* **Parallel Execution & Timeout:** Workers are invoked concurrently (e.g., via `Promise.all` or `asyncio.gather`). A strict 2.5-second timeout is enforced per worker thread.
* **Graceful Degradation:** If one worker fails or times out, the orchestrator proceeds with a partial payload (e.g., serving the PWA link with only food items and notifying the user that grocery items can be added later on the canvas).
* **Source Attribution:** Every recommended and manually added cart item must carry a displayable source:
  * Food items must include `restaurant_id` and `restaurant_name`.
  * Instamart items must include `brand_name` when available and an Instamart source/store label when available.
  * The PWA must display this source context on cart rows so collaborators and the host know where each item will be ordered from.
* **Food Restaurant Grouping:** The agent should prefer coherent Food recommendations from one restaurant when that satisfies the prompt and budget. If group choices require multiple restaurants, the session must preserve separate restaurant groups instead of pretending they can become one Swiggy Food cart.

### 3. Swiggy OAuth & Checkout Handoff
* **Sequential Checkout:** Since Swiggy treats Food and Instamart as separate delivery verticals, the backend generates separate Swiggy carts using the host's Swiggy OAuth session token. The PWA leads the host through a sequential checkout experience.
* **Restaurant-Specific Food Orders:** Swiggy Food does not support a single Food order containing items from multiple restaurants. EasyOrder must split Food checkout payloads by `restaurant_id`. A session with items from two restaurants creates two separate Food checkout steps, followed by the Instamart checkout step when Instamart items exist.
* **Checkout Step Visibility:** Before OAuth handoff, the host must see the number of Swiggy orders required, grouped by restaurant or Instamart source, with each group's subtotal and item list.
* **Inventory Verification:** Immediately before OAuth redirection, the PWA validates item pricing and stock levels. If an item is out of stock, the client displays a replacement modal (e.g., suggesting a substitute brand) before confirming the final order creation.

### 4. WhatsApp Privacy & Proactive Prompts
* **Mention-Only Direct Intake:** The WhatsApp webhook only processes direct messages containing the `@EasyOrder` mention to protect user privacy and optimize API usage. Normal consumer group-chat bot participation is not part of the live MVP.
* **Template-Driven Event Nudges:** Proactive notifications (e.g., for sports events or weather changes) are scheduled using official, pre-approved WhatsApp Business Message Templates. They are only sent to users who explicitly opted in during a previous session.

## Testing Decisions

* **Orchestrator-Worker Concurrency Unit Tests:** Mock Swiggy MCP server latency to verify that individual worker timeouts (2.5 seconds) degrade gracefully and return partial carts.
* **Real-time Sync Integration Tests:** Simulate 5 concurrent clients modifying a single session cart via WebSockets/Firebase to ensure state consistency and verify that there are no race conditions.
* **Handoff Token Validation Tests:** Verify that token-based guest access is secure, session-scoped, and restricted from accessing checkout or payment settings.
* **Vendor/Brand Display Tests:** Verify that Food cart rows display restaurant names and Instamart rows display brand/source context.
* **Mock OAuth Redirection Tests:** Assert that sequential cart generation compiles independent checkout payloads by Food restaurant and Instamart source, including multi-restaurant Food sessions.

## Out of Scope

* Dineout table availability and reservations (`/dineout`).
* Automated UPI payment splitting calculations or payment links (slated for Phase 2).
* Proactive conversational analysis of group messages without `@EasyOrder` tag.
* Native mobile application wrappers (iOS or Android app store downloads).

## Further Notes

* **LLM Strategy:** Ollama is utilized for local development; Gemini 1.5 Flash is used for remote staging due to its context window; and GPT-4o mini is selected for production to achieve lowest latency and robust JSON schema generation.
