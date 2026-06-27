# Architectural & Code Design Review - EasyOrder

This document presents the design review of [hld.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/hld.md) and [lld.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/lld.md) against the [easyorder-prd.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/easyorder-prd.md) requirements.

---

## 1. Spec Alignment & Gaps (review Skill)

We verified all PRD user stories against the HLD component boundaries and LLD interfaces. The following gaps and corrections were identified:

| PRD Requirement / User Story | Design Coverage | Identified Gap | Recommended Resolution |
| :--- | :--- | :--- | :--- |
| **US-8 / US-9:** Host Swiggy OAuth & sequential checkouts | Covered in sequential checkout flow | **PWA Client Host Identification:** When the PWA opens in the browser, how does it know the client is the Host (vs a Guest)? | The WhatsApp bot will send a tokenized host link to the host (via DM or encrypted url parameter): `/session/123?token=host_sec_xyz`. The PWA client will read the token and save it to localStorage. |
| **US-7:** Stock & price verification before redirect | Covered in checkout flow | **Alternative Search Endpoint:** The LLD indicates returning alternatives on out-of-stock, but the `ISwiggyMcpClient` has no method to fetch substitutions. | Add `getSubstituteItems(itemId: string): Promise<SubstituteItem[]>` to `ISwiggyMcpClient` interface in [lld.md](file:///Users/vishalkumar/projects/swiggy_builder_prog/docs/lld.md). |
| **US-10:** WhatsApp delivery status updates | Covered in HLD boundaries | **No callback endpoint in LLD:** There is no API route in the LLD to receive Swiggy callback webhooks for order status updates. | Add a callback API route: `POST /api/swiggy/callback/delivery` that parses status payload and triggers the WhatsApp Gateway. |

---

## 2. Interface Depth & Testability (codebase-design Skill)

* **Interface Depth Check (Pass):** 
  * The `Orchestrator` interface (`processGroupRequest(sessionId, prompt)`) is exceptionally deep. It hides prompt parsing, async parallel execution of workers, timeout logic, and DB state synchronization under a single method call.
  * The `BaseWorker` structure isolates the individual vertical fetching complexity.
* **Testing Seams Check (Pass):**
  * By injecting the `ISwiggyMcpClient` interface, we successfully decouple our workers from live Swiggy staging APIs.
  * *Local Mock Server Design:* To run end-to-end integration tests locally, we can run a mock Express server mimicking Swiggy MCP JSON outputs on `http://localhost:5050` and configure the client to point to this address in the dev environment.

---

## 3. Local-First & Freemium Strategy

To support local debugging with zero cloud costs, our architecture will implement the following freemium strategy:

### 3.1 Local Emulation Stack
1. **Local PostgreSQL via Docker / Supabase CLI:** 
   * Avoid calling live Supabase during development. Developers can boot a full local Supabase stack (PostgreSQL, Auth, Realtime) using:
     `npx supabase start` or simply `docker compose up db` for PostgreSQL-only
   * The PWA client and Backend Orchestrator connect to `http://localhost:54321` if `NODE_ENV === 'development'`.
2. **Local Webhook Proxying:**
   * WhatsApp requires HTTPS webhook endpoints to send events. Use the free tier of **localtunnel** or **ngrok** to expose the local server:
     `lt --port 8000` or `ngrok http 8000`
   * Register the generated proxy URL (e.g., `https://xxxx.localtunnel.me/api/whatsapp/webhook`) in the Meta Developer Console.

### 3.2 Freemium Resource Optimization
* **Google AI Studio Free Tier (Gemini 1.5 Flash):**
  * Gemini 1.5 Flash is free for development but subject to rate limits (15 RPM, 1500 RPD).
  * **Optimization:** Instead of sending full Swiggy menus to the Orchestrator on every request (which balloons token count and triggers rate limits), we will implement local caching of menu categories on the backend. The Orchestrator will query the cached category schemas and only pull full menus for specific restaurants once selected.
* **Supabase Free Tier limits:**
  * 500MB database storage, unlimited API requests, 50K monthly active users, and Realtime channels included.
  * **Optimization:** PWA clients must debounce database writes on the quantity slider (e.g., waiting 400ms after the user stops dragging before committing the update) to minimize unnecessary Realtime broadcasts.
