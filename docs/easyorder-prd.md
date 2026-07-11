# Product Requirements Document (PRD) - EasyOrder

## Problem Statement

Group food and supply ordering is currently a high-friction coordination problem. Hosts face decision fatigue, dietary collection hassles, and manual order compilation. Gathering preferences in chat groups leads to cart abandonment, while combining main dishes (from restaurant menus) and grocery/supplies (drinks, ice, plates) requires ordering via separate visual screens and payment processes. 

## Solution

EasyOrder is a WhatsApp-first agentic assistant linked with a collaborative Web
PWA canvas. It has two complementary WhatsApp operating modes:

1. **Mention-triggered group planning:** the host sends a concise `@EasyOrder`
   prompt to the EasyOrder business/test number after a group has already agreed
   on intent.
2. **Dedicated EasyOrder business chat:** the user chats directly with the
   EasyOrder business account for list management, reorder help, order status,
   restaurant discovery, offers, and support-style queries.

In both modes, EasyOrder parses intent via an Orchestrator-Workers LLM pattern,
recommends selections via a multi-user visual planning canvas, and compiles
unified carts. It then hands over sequential checkout sessions to the host using
secure Swiggy OAuth. The agent can prepare, update, and explain carts, but it
must not place or pay for an order without explicit user review and confirmation.

## Product Assessment: Next Direction

The proposed next steps are directionally strong, but they should not all be
treated as the same feature.

- Showing inbound WhatsApp messages in the UI is a natural continuation of the
  current architecture. It makes the PWA feel connected to the WhatsApp trigger
  and gives users confidence that EasyOrder understood the right request.
- Replacing long raw URLs with a WhatsApp-native call-to-action is a product
  polish and trust improvement. It should use supported WhatsApp interactive or
  template message capabilities rather than trying to render arbitrary HTML-style
  `href` text inside a normal WhatsApp text body.
- A dedicated EasyOrder business account is useful, but it expands the product
  from "session creator" into "persistent commerce assistant." That is not hard
  in spirit, but it adds identity, history, intent routing, support-policy,
  template approval, and privacy requirements. It should be built as a second
  surface on the same backend, not as a replacement for the `@EasyOrder` flow.
- Wishlist/order-list mode is a strong repeat-use case, especially for household
  and monthly replenishment. It should start with a short command grammar and
  confirmation loop before attempting full free-form shopping autonomy.

Recommended sequencing:

1. Add message timeline visibility in the session UI.
2. Replace raw handoff URLs with a WhatsApp-native CTA/button or approved
   template where available, falling back to short links in plain text.
3. Add a persistent EasyOrder business-chat intent router.
4. Add saved lists/wishlists and list-to-cart conversion.
5. Add order history/status/offers/recommendation intents once identity and data
   access are reliable.

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
14. As a host, I want the WhatsApp message that created a session to appear in the PWA session timeline, so that I can verify the canvas came from the right request.
15. As a WhatsApp user, I want EasyOrder's reply to contain a clear call-to-action button or short branded link instead of a long tokenized URL, so that the handoff feels trustworthy and easy to tap.
16. As a returning user, I want to chat directly with the EasyOrder business account without using `@EasyOrder`, so that I can ask about previous orders, active sessions, offers, and recommendations.
17. As a returning user, I want to maintain named order lists such as `house monthly list` or `match night snacks`, so that I can add items over time and convert the list into a cart when ready.
18. As a user building a list in WhatsApp, I want a short command grammar such as `@EasyOrder vim bar` or `add vim bar to monthly`, so that adding items does not feel like writing a long prompt.
19. As a host, I want EasyOrder to share a guest planning link or order summary into a group only after I explicitly ask it to, so that private host links and personal order history are not leaked.
20. As a user, I want EasyOrder to answer discovery questions such as "nearest best chole bhature" and "best upcoming offers" with source-attributed results, so that I can decide whether to start a cart.

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
* **Mention-Only Group-Planning Intake:** The current group-planning flow processes direct messages containing the `@EasyOrder` mention to protect user privacy and optimize API usage. Normal consumer group-chat bot participation is not part of the live MVP.
* **Dedicated Business Chat Intake:** A user may also chat directly with the EasyOrder business account. In that dedicated context, EasyOrder can process free-form assistant intents because the user has explicitly opened a business chat. The system must still enforce intent routing, privacy redaction, and confirmation before cart checkout.
* **No Passive Group Reading:** EasyOrder must not silently process ordinary consumer group conversations. If group operation is added later, it should require explicit user action, supported WhatsApp platform capabilities, and a clear privacy model.
* **Platform Constraint — No Group Bot:** Meta's WhatsApp Business Cloud API does not allow a business number to join consumer groups and delivers no group-message webhooks. All group collaboration is therefore host-mediated: the host talks to EasyOrder directly, and the group joins through the shared guest link in the PWA. See [ADR 0005](adr/0005-host-mediated-group-flow.md).
* **WhatsApp-Native Handoff:** Session handoff should prefer supported interactive messages or approved templates with CTA buttons. If unavailable, EasyOrder should send concise copy plus short branded links. Raw one-time tokens should remain embedded in URLs but should not dominate the visible message body.
* **Template-Driven Event Nudges:** Proactive notifications (e.g., for sports events or weather changes) are scheduled using official, pre-approved WhatsApp Business Message Templates. They are only sent to users who explicitly opted in during a previous session.

### 5. Message Timeline And Session Context
* **Inbound Message Persistence:** The backend should persist the inbound message metadata needed to explain session creation: message id, sender `wa_id`, timestamp, normalized body, mode, and derived intent. Raw content should be limited to what is necessary for session explanation and debugging.
* **PWA Timeline:** The PWA session page should show a compact timeline that starts with the initiating WhatsApp message and then displays key EasyOrder events: session created, cart initialized, guest edits, checkout validation, checkout confirmation, and outbound handoff status.
* **Observability Boundary:** Backend logs remain the source for operational debugging; the PWA timeline is a user-facing activity feed and must not reveal secrets, tokens, signatures, access tokens, or internal stack traces.

### 6. Saved Lists, Wishlist, And Order Memory
* **Saved Lists:** Users can create persistent named lists, such as `house monthly`, `office chai`, or `match night snacks`.
* **Short Add Grammar:** EasyOrder should support concise list commands, starting with deterministic patterns before full free-form reasoning:
  * `@EasyOrder vim bar`
  * `add vim bar to monthly`
  * `show monthly list`
  * `add today's list to cart`
* **Review Before Order:** A saved list can become a session/cart, but the user must review availability, substitutions, offers, and checkout groups before placing the order.
* **Offer Optimization:** "Place the best offers" means EasyOrder may rank available items by price, discount, quantity, brand preference, and delivery feasibility, but it must explain substitutions before checkout.

## Testing Decisions

* **Orchestrator-Worker Concurrency Unit Tests:** Mock Swiggy MCP server latency to verify that individual worker timeouts (2.5 seconds) degrade gracefully and return partial carts.
* **Real-time Sync Integration Tests:** Simulate 5 concurrent clients modifying a single session cart via WebSockets/Firebase to ensure state consistency and verify that there are no race conditions.
* **Handoff Token Validation Tests:** Verify that token-based guest access is secure, session-scoped, and restricted from accessing checkout or payment settings.
* **Vendor/Brand Display Tests:** Verify that Food cart rows display restaurant names and Instamart rows display brand/source context.
* **Mock OAuth Redirection Tests:** Assert that sequential cart generation compiles independent checkout payloads by Food restaurant and Instamart source, including multi-restaurant Food sessions.
* **Message Timeline Tests:** Assert that an inbound WhatsApp message creates a redacted user-facing timeline event visible through the session API and PWA.
* **WhatsApp CTA Tests:** Assert that Meta-mode handoff uses the configured interactive/template sender path when available, and falls back to concise short-link text without leaking raw host tokens in response bodies.
* **Dedicated Chat Intent Tests:** Assert that direct business-chat messages route to the correct intent family: start session, saved list, order history/status, discovery/offers, or unsupported request.
* **Saved List Tests:** Assert that list item adds, show-list queries, list-to-cart conversion, and review-before-checkout constraints work across sessions for the same user identity.

## Out of Scope

* Dineout table availability and reservations (`/dineout`).
* Automated UPI payment splitting calculations or payment links (slated for Phase 2).
* Proactive conversational analysis of group messages without `@EasyOrder` tag.
* Autonomous purchase execution from a wishlist without explicit user review.
* Full customer-support automation for refunds, cancellations, or payment disputes unless supported by official Swiggy MCP/order-management scopes.
* Native mobile application wrappers (iOS or Android app store downloads).

## Further Notes

* **LLM Strategy:** Ollama is utilized for local development; Gemini 1.5 Flash is used for remote staging due to its context window; and GPT-4o mini is selected for production to achieve lowest latency and robust JSON schema generation.
