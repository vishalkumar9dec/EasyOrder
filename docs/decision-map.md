# EasyOrder Decision Map

This document tracks the technical investigation tickets and resolved architectural choices for EasyOrder.

---

## Resolved Decisions

### #1: Python, FastAPI & LangGraph Backend
* **Type:** Grilling / Architectural Choice
* **Question:** Can we use Python as the backend and LangGraph as the agentic framework?
* **Decision:** Yes. We will use **FastAPI** for our web server and **LangGraph** for our stateful multi-agent Orchestrator-Workers graph. LangGraph manages the consolidated cart in its graph state, and FastAPI handles async HTTP/SSE requests.
* **Date Resolved:** 2026-06-26

### #2: Supabase PostgreSQL Integration in Python Backend
* **Type:** Research / Grilling
* **Question:** How do we configure and initialize the Supabase client in Python on a free serverless environment without committing secret keys to Git?
* **Decision:** Use the `supabase-py` Python SDK initialized with two environment variables (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`). For local development, run PostgreSQL via Docker Compose and point `SUPABASE_URL` to `http://localhost:54321`. The service role key bypasses Row Level Security for backend operations, while the anon key is used on the frontend with RLS enforcement.
* **Date Resolved:** 2026-06-26 (updated 2026-06-27)

### #3: Swiggy MCP Client Invocation in Python
* **Type:** Research / Prototype
* **Question:** How does the Python backend execute and communicate with the Swiggy MCP servers? Since Swiggy MCP servers are built as standard Node/Stdio packages, can the Python backend spin them up using a subprocess wrapper, or do we require a Python-native MCP client library?
* **Decision:** Use the official Python MCP SDK (`mcp`) to manage subprocess communication over standard I/O (stdio) via `StdioServerParameters`. To decouple local development from Swiggy's Node/staging environment, define a shared `ISwiggyMcpClient` interface, injecting a `MockSwiggyMcpClient` returning static mock data in dev environments.
* **Date Resolved:** 2026-06-26

### #4: WhatsApp Webhook & Verification Endpoint in FastAPI
* **Type:** Prototype
* **Question:** How do we implement the standard Meta webhook validation (`GET /api/whatsapp/webhook` with `hub.verify_token`) and event parsing (`POST /api/whatsapp/webhook`) in FastAPI?
* **Decision:** Implement GET verify routes using FastAPI's `Query(alias="hub...")` matching to retrieve and echo back the raw challenge string. Use standard JSON parsing on the POST handler to extract incoming sender IDs and message text, filtering for the `@EasyOrder` tag to execute orchestrator tasks.
* **Date Resolved:** 2026-06-26

### #5: PostgreSQL (Supabase) Replacing Cloud Firestore
* **Type:** Architectural Pivot
* **Question:** Should we use Cloud Firestore or PostgreSQL for session state storage and real-time sync?
* **Decision:** Switch from Cloud Firestore to **PostgreSQL via Supabase**. Key drivers: (1) LangGraph has native PostgreSQL checkpointing (`langgraph-checkpoint-postgres`), eliminating custom Firestore adapters; (2) relational data model fits sessions/carts/users better than document-based NoSQL; (3) Supabase Realtime provides WebSocket-based change broadcasting equivalent to Firestore's `onSnapshot`; (4) PostgreSQL runs locally in Docker with zero cloud dependencies, simplifying local dev; (5) Row Level Security replaces Firestore security rules with more expressive SQL-based policies.
* **Date Resolved:** 2026-06-27

---

## Open Tickets (The Frontier)

* **No open tickets.** The frontier has been fully resolved for this architectural planning phase.
