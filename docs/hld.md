# High-Level Design (HLD) - EasyOrder Collaborative Concierge

This document specifies the system architecture for **EasyOrder**—a collaborative food and supply coordination service built using Python, FastAPI, LangGraph, PostgreSQL (Supabase), and the Swiggy Model Context Protocol (MCP).

The architecture is presented in three layers: a high-level overview showing all components and the request flow, followed by two detailed deep-dives — one for the FastAPI application setup and one for the Agentic AI framework.

---

## 1. High-Level System Architecture & Request Flow

The system is composed of five blocks: **WhatsApp** and **Mobile App (PWA)** as client ingress points on the left, the **EasyOrder Server** (containing the FastAPI application and LangGraph Agentic Framework) in the center, **Swiggy MCP** as the external commerce platform on the right, and **PostgreSQL (Supabase)** as the persistence and real-time sync layer at the bottom.

```mermaid
graph LR
    %% ── Client Ingress (Left) ──
    WA[WhatsApp]
    APP[Mobile App / PWA]

    %% ── EasyOrder Server (Center) ──
    subgraph SERVER [EasyOrder Server]
        direction LR
        FAPI[FastAPI App]
        LG[LangGraph Agentic Framework]
        FAPI <--> LG
    end

    %% ── Swiggy (Right) ──
    SWIGGY[Swiggy MCP]

    %% ── Database (Bottom) ──
    DB[(PostgreSQL / Supabase)]

    %% ── Connections ──
    WA -->|Webhook Events| FAPI
    FAPI -->|Send Template Messages| WA
    APP -->|API Calls| FAPI
    APP <-->|Supabase Realtime| DB
    LG -->|Tool Calls: Search, Menu, Cart| SWIGGY
    SWIGGY -->|Results| LG
    FAPI -->|Read/Write Sessions| DB
    LG -->|Save Recommendations| DB

    %% ── Styling ──
    classDef client fill:#D94A38,stroke:#D94A38,color:#fff
    classDef server fill:#1E7C55,stroke:#1E7C55,color:#fff
    classDef agent fill:#5B21B6,stroke:#5B21B6,color:#fff
    classDef external fill:#64748B,stroke:#64748B,color:#fff
    classDef storage fill:#F6C453,stroke:#F6C453,color:#263238

    class WA,APP client
    class FAPI server
    class LG agent
    class SWIGGY external
    class DB storage
```

### End-to-End Request → Response Lifecycle

| Step | What happens | Components involved |
|------|-------------|-------------------|
| 1 | Host sends `@EasyOrder get biryani for 4, budget ₹2000` in WhatsApp group | WhatsApp → EasyOrder Server |
| 2 | FastAPI receives the webhook, validates Meta signature, filters for `@EasyOrder` tag | FastAPI App |
| 3 | FastAPI creates a session ID and invokes the LangGraph agent with the raw prompt | FastAPI App → LangGraph |
| 4 | Agent runs Input Guardrails (prompt injection check, PII sanitization) | LangGraph Agentic Framework |
| 5 | Agent parses intent via LLM — extracts budget, headcount, dietary preferences | LangGraph → LLM (Gemini/GPT) |
| 6 | Agent concurrently queries Swiggy Food and Instamart via MCP tool calls | LangGraph → Swiggy MCP |
| 7 | Agent runs Output Guardrails (budget check, dietary validation, stock filter) | LangGraph Agentic Framework |
| 8 | Agent writes the session record and recommended cart to PostgreSQL via Supabase | LangGraph → PostgreSQL (Supabase) |
| 9 | FastAPI sends WhatsApp template messages: guest link to group, host link via DM | FastAPI App → WhatsApp |
| 10 | Group members open the Mobile App (PWA), collaborate on cart in real-time via Supabase Realtime channels | Mobile App ↔ PostgreSQL (Supabase) |
| 11 | Host triggers checkout; FastAPI handles Swiggy OAuth and sequential cart creation | Mobile App → FastAPI App → Swiggy MCP |

---

## 2. Detailed Architecture A: FastAPI Application Setup

This section zooms into the FastAPI application gateway — its routing structure, database integration, authentication flows, and local development sandbox.

### 2.1 FastAPI Router Structure

```text
FastAPI Application (main.py)
├── GET  /api/whatsapp/webhook     → Webhook verification (Meta challenge-response)
├── POST /api/whatsapp/webhook     → Message ingestion, @EasyOrder filtering, agent invocation
├── POST /api/session/checkout     → Pre-checkout stock/price validation
├── POST /api/session/checkout/confirm → Swiggy OAuth code exchange + cart creation
└── Middleware: CORS, Rate Limiting, Request Logging
```

### 2.2 PostgreSQL Real-time Sync (Supabase Realtime)
* **Direct Client Sync:** PWA clients use the Supabase JS SDK to subscribe to `postgres_changes` channels on the `cart_items` table. Inserts, updates, and deletes broadcast instantly to all connected devices via WebSocket.
* **Backend Writes:** The FastAPI backend (and the LangGraph agent) write to PostgreSQL via the `supabase-py` SDK (service role key) for session initialization and status updates. LangGraph also uses `langgraph-checkpoint-postgres` for native agent state persistence.
* **Row Level Security (RLS):** PostgreSQL RLS policies enforce that guests can only modify rows in `cart_items` where `session_id` matches their token, while session metadata (budget, status, address) is restricted to the host token.

### 2.3 Swiggy OAuth Checkout Handoff
1. PWA triggers a pre-checkout validation via `POST /api/session/checkout` — the backend verifies stock and pricing against Swiggy MCP.
2. On success, the PWA redirects the host to Swiggy's OAuth portal.
3. Swiggy redirects back with an authorization code.
4. PWA sends the code to `POST /api/session/checkout/confirm` — the backend exchanges it for an access token, creates one checkout payload per Food restaurant plus a separate Instamart payload when needed, and returns the ordered checkout redirect URLs.

### 2.4 Authentication & Token Separation
* **Host Token:** SHA-256 derived, sent privately via WhatsApp DM. Grants full session control and checkout privileges.
* **Guest Token:** Random UUID, posted publicly in the group chat. Grants cart item read/write only.
* **Supabase Auth:** PWA clients authenticate via Supabase Anonymous Auth (or magic link). The JWT is passed in API headers and evaluated by RLS policies on every database operation.

### 2.5 Local Development & Free-Tier Sandbox
* **WhatsApp Sandbox:** Meta's free developer sandbox supports 5 pre-registered test numbers at no cost.
* **Webhook Tunneling:** `npx localtunnel --port 8000` or `ngrok http 8000` to expose the local FastAPI server to Meta's HTTPS webhook requirements.
* **Local PostgreSQL:** `docker compose up db` starts PostgreSQL locally. No cloud account required. Supabase CLI (`npx supabase start`) optionally provides the full Supabase stack (Auth, Realtime, Storage) locally.
* **Mock Swiggy MCP:** A local mock client returns static restaurant/item data, with configurable latency to test timeout degradation.

---

## 3. Detailed Architecture B: Agentic AI Framework (LangGraph, Guardrails & Harness)

This section zooms into the LangGraph-based AI system — its state machine, node structure, prompt harness, safety guardrails, and degradation policies.

### 3.1 LangGraph State Machine Overview

The agent is a deterministic state graph. Each node performs one task and mutates a shared typed state dictionary. The flow is: sanitize → parse → search (parallel) → validate → persist.

```mermaid
stateDiagram-v2
    [*] --> InputGuardrail : Raw WhatsApp prompt

    state InputGuardrail {
        [*] --> InjectionCheck
        InjectionCheck --> PIISanitizer : Safe
        InjectionCheck --> Reject : Malicious
    }
    Reject --> [*] : Return 400

    PIISanitizer --> IntentParser : Clean text

    state IntentParser {
        [*] --> LLMToolCall : System prompt + raw text
        LLMToolCall --> StructuredOutput : JSON schema
    }

    StructuredOutput --> WorkerFork : budget, headcount, keywords

    state WorkerFork <<fork>>
    WorkerFork --> FoodWorker
    WorkerFork --> InstamartWorker
    WorkerFork --> BudgetWorker

    state FoodWorker {
        [*] --> SearchFood : Swiggy /food MCP
    }
    state InstamartWorker {
        [*] --> SearchIM : Swiggy /im MCP
    }
    state BudgetWorker {
        [*] --> CalcServings : Portions math
    }

    FoodWorker --> WorkerJoin
    InstamartWorker --> WorkerJoin
    BudgetWorker --> WorkerJoin

    state WorkerJoin <<join>>
    WorkerJoin --> OutputGuardrail : Combined results

    state OutputGuardrail {
        [*] --> BudgetCheck : Soft limit comparison
        BudgetCheck --> DietaryCheck : Tag validation
        DietaryCheck --> StockFilter : Availability check
    }

    OutputGuardrail --> WriteDB : Validated cart
    WriteDB --> [*] : Session ACTIVE
```

### 3.2 Agent Node Responsibilities

| Node | Input | Output | What it does |
|------|-------|--------|-------------|
| **Input Guardrail** | Raw prompt string | Sanitized string or rejection | Blocks prompt injections; masks emails, phone numbers, card numbers |
| **Intent Parser** | Sanitized text | `{budget, headcount, food_keywords, grocery_keywords, dietary_preference}` | LLM tool-call extracts structured constraints from natural language |
| **Food Worker** | lat, lng, food_keywords | List of restaurant/menu results | Queries Swiggy Food MCP (`searchRestaurants`, `getRestaurantMenu`) |
| **Instamart Worker** | lat, lng, grocery_keywords | List of grocery/supply items | Queries Swiggy Instamart MCP (`searchInstamart`) |
| **Budget Worker** | headcount, food_results, im_results | Serving estimates, cost totals | Calculates portion sizes and total cost |
| **Output Guardrail** | Combined results + constraints | Validated cart + warnings | Budget soft-check, dietary tag validation, mock-item filtering |
| **Write DB** | Validated state | Session status = ACTIVE | Persists session record and cart items to PostgreSQL via Supabase |

### 3.3 Cart Source Attribution And Checkout Grouping

Every cart item persisted by the agent or added manually through the PWA must carry
source attribution:

* Food items include `restaurant_id` and `restaurant_name`.
* Instamart items include `brand_name` when available and a store/source label when available.
* The PWA renders this source on every cart row and in checkout previews.

Food checkout payloads are grouped by `restaurant_id` because Swiggy Food does not
support one order spanning multiple restaurants. A consolidated EasyOrder session can
therefore produce multiple Food checkout steps plus one Instamart step. The agent should
prefer single-restaurant Food recommendations when they satisfy the group's prompt,
budget, and dietary constraints.

### 3.4 Prompt Harness & LLM Strategy

* **Intent Parser System Prompt:** Instructs the LLM to output a strict JSON schema with budget, headcount, food/grocery keywords, and dietary preference. Provides defaults (budget=3000, headcount=4) for missing fields.
* **LLM Model Ladder:**
  - **Local Dev:** Ollama (Llama 3.1 8B) — free, runs in Docker, sufficient for testing prompt schemas.
  - **Staging:** Google AI Studio free tier (Gemini 1.5 Flash) — free, massive context window for full menu dumps.
  - **Production:** GPT-4o mini — lowest latency, strongest JSON/tool-calling reliability.

### 3.5 Safety Guardrails

#### Input Guardrails (Pre-LLM)
* **Prompt Injection Detection:** Regex-based pattern matching for override attempts like `"ignore previous instructions"`, `"system prompt bypass"`, etc. Blocks and returns HTTP 400.
* **PII Sanitization:** Masks email addresses, credit card numbers, and phone numbers before the text reaches the LLM.

#### Output Guardrails (Post-LLM, Pre-Persist)
* **Soft Budget Enforcement:** If the recommended cart total exceeds the host's budget, the agent does NOT reject the session. Instead, it writes a `budget_warning` flag to the session record in PostgreSQL. The PWA displays a warning badge, letting collaborators trim items themselves.
* **Dietary Integrity Check:** Validates that items in a VEG-tagged session are actually tagged VEG. Non-matching items trigger a warning.
* **Mock/Placeholder Filter:** Strips items with names containing "mock" or "placeholder" to prevent test data from leaking into production sessions.

### 3.6 Degradation & Timeout Policies

* **2.5-Second Execution SLA:** All concurrent worker searches run inside `asyncio.wait_for(..., timeout=2.5)`. If any vertical times out, the agent proceeds with partial results.
* **Degraded State Flag:** When a vertical fails, the session is initialized with `status: "DEGRADED"` and a human-readable warning (e.g., *"Cold drinks search timed out. You can add items manually on the canvas."*). The PWA renders the available results immediately without blocking.
* **No Autonomous Ordering:** The agent can never place an order or charge a card. It only recommends items and compiles carts. Actual payment requires explicit host action via Swiggy's checkout page.
