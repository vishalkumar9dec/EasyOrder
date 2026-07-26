-- Targeted single-restaurant orders + scheduled delivery-window orders.
--
-- Separate from `sessions` (a shared multi-guest planning cart): an order
-- here is a single restaurant, single requester, host-only order placed (or
-- scheduled) from a targeted WhatsApp prompt. No RLS (ADR 0007 — the app
-- connects as the table-owner role, so RLS is structurally inert; the real
-- authorization boundary is application-layer, same as every other table
-- since migration 0007).

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    wa_id TEXT NOT NULL,
    restaurant_id TEXT NOT NULL,
    restaurant_name TEXT NOT NULL,
    items JSONB NOT NULL,
    total NUMERIC(10,2) NOT NULL CHECK (total > 0),
    budget_limit NUMERIC(10,2),
    delivery_deadline TIMESTAMPTZ,
    target_placement_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'PLACED'
        CHECK (status IN (
            'PENDING_CONFIRMATION','SCHEDULED','PLACED','DELIVERED','CANCELLED','FAILED'
        )),
    swiggy_order_id TEXT,
    failure_reason TEXT,
    source_message_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_wa_id
    ON orders (wa_id);

-- Poller lookup: due scheduled orders.
CREATE INDEX IF NOT EXISTS idx_orders_status_target_placement
    ON orders (status, target_placement_at);

-- At most one pending-confirmation order per user at a time.
CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_pending_confirmation_unique
    ON orders (wa_id) WHERE status = 'PENDING_CONFIRMATION';

-- Idempotency: a webhook retry must not create a second order for the same
-- inbound message, mirroring session_events' (message_id, event_type) dedup.
CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_source_message_id
    ON orders (source_message_id) WHERE source_message_id IS NOT NULL;
