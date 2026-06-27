# ADR 0001: PostgreSQL (Supabase) for Real-Time Session State Synchronization

## Status
Accepted (supersedes original Firestore decision)

## Context
EasyOrder is a collaborative food planning concierge. Up to 10 guests and hosts can edit the consolidated cart simultaneously in a mobile-first PWA canvas. Changes made by one guest must be broadcast instantly to all other clients to prevent duplicate orders and coordinate selections.

We evaluated three alternatives:
1. **Custom WebSocket Server:** Setting up a dedicated Node.js WebSocket backend to broadcast operations.
2. **Cloud Firestore / Firebase Realtime Database:** Using a fully managed real-time NoSQL database with native client SDK listeners.
3. **PostgreSQL via Supabase:** Using a managed PostgreSQL database with built-in Realtime (WebSocket-based change broadcasting), Row Level Security, and a free tier.

## Decision
We chose **PostgreSQL via Supabase** for session state synchronization.

### Rationale
* **LangGraph native checkpointing:** `langgraph-checkpoint-postgres` stores agent state directly in PostgreSQL — no custom adapter needed for Firestore.
* **Relational data model:** Sessions, carts, users, and items are inherently relational. SQL joins (e.g., "all items in session X grouped by user") are trivial vs. Firestore's denormalized queries.
* **Supabase Realtime:** Provides real-time change broadcasting via WebSocket channels (`postgres_changes`), matching Firestore's `onSnapshot` functionality.
* **Row Level Security (RLS):** PostgreSQL-native RLS policies replace Firestore security rules with more expressive and testable access control.
* **Free tier parity:** Supabase free tier provides 500MB database, unlimited API requests, 50K monthly active users, and Realtime channels — sufficient for MVP.
* **Local dev simplicity:** PostgreSQL runs natively via Docker (`docker compose up db`) — no Firebase CLI or emulator setup required.

## Consequences
* **Pros:**
  * Native SQL for complex queries (session analytics, cart aggregation, reporting).
  * LangGraph checkpoint persistence with zero custom code.
  * Testable RLS policies via `pgTAP` or Supabase test helpers.
  * PostgreSQL runs locally in Docker with zero cloud dependencies.
  * Migration path to any PostgreSQL host (Railway, Neon, self-hosted) if Supabase is outgrown.
* **Cons:**
  * Supabase Realtime is channel-based (pub/sub), not document-listener-based like Firestore. PWA code must subscribe to PostgreSQL change channels.
  * Schema migrations required (vs. Firestore's schemaless flexibility). Managed via Supabase CLI or Alembic.
  * Slightly more setup for auth (Supabase Auth replaces Firebase Anonymous Auth).
