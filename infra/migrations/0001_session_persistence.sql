-- EasyOrder session persistence, cart items, and RLS policies.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    whatsapp_group_id TEXT NOT NULL,
    host_phone TEXT NOT NULL,
    host_token_hash TEXT NOT NULL,
    guest_token TEXT NOT NULL,
    budget_limit NUMERIC(10,2) NOT NULL DEFAULT 3000.00,
    head_count INTEGER NOT NULL DEFAULT 4 CHECK (head_count > 0),
    dietary_preference TEXT NOT NULL DEFAULT 'ANY'
        CHECK (dietary_preference IN ('VEG','NON-VEG','ANY')),
    status TEXT NOT NULL DEFAULT 'INITIALIZING'
        CHECK (status IN ('INITIALIZING','ACTIVE','DEGRADED','CHECKOUT_READY','ORDERED')),
    budget_warning BOOLEAN NOT NULL DEFAULT FALSE,
    degraded_verticals TEXT[] NOT NULL DEFAULT '{}',
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cart_items (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    item_id TEXT NOT NULL,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity >= 0 AND quantity <= 99),
    price NUMERIC(10,2) NOT NULL CHECK (price > 0),
    added_by TEXT NOT NULL,
    dietary_tag TEXT NOT NULL DEFAULT 'ANY'
        CHECK (dietary_tag IN ('VEG','NON-VEG','ANY')),
    vertical TEXT NOT NULL
        CHECK (vertical IN ('food','instamart')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_whatsapp_group_id
    ON sessions (whatsapp_group_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_guest_token
    ON sessions (guest_token);

CREATE INDEX IF NOT EXISTS idx_sessions_host_token_hash
    ON sessions (host_token_hash);

CREATE INDEX IF NOT EXISTS idx_cart_items_session_id
    ON cart_items (session_id);

CREATE INDEX IF NOT EXISTS idx_cart_items_session_vertical
    ON cart_items (session_id, vertical);

ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE cart_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS sessions_read ON sessions;
CREATE POLICY sessions_read ON sessions
    FOR SELECT
    USING (
        guest_token = current_setting('request.headers', true)::jsonb->>'x-guest-token'
        OR host_token_hash = encode(
            digest(
                convert_to(COALESCE(current_setting('request.headers', true)::jsonb->>'x-host-token', ''), 'UTF8'),
                'sha256'
            ),
            'hex'
        )
    );

DROP POLICY IF EXISTS sessions_host_update ON sessions;
CREATE POLICY sessions_host_update ON sessions
    FOR UPDATE
    USING (
        host_token_hash = encode(
            digest(
                convert_to(COALESCE(current_setting('request.headers', true)::jsonb->>'x-host-token', ''), 'UTF8'),
                'sha256'
            ),
            'hex'
        )
    )
    WITH CHECK (
        host_token_hash = encode(
            digest(
                convert_to(COALESCE(current_setting('request.headers', true)::jsonb->>'x-host-token', ''), 'UTF8'),
                'sha256'
            ),
            'hex'
        )
    );

DROP POLICY IF EXISTS cart_items_session_access ON cart_items;
CREATE POLICY cart_items_session_access ON cart_items
    FOR ALL
    USING (
        session_id IN (
            SELECT session_id
            FROM sessions
            WHERE guest_token = current_setting('request.headers', true)::jsonb->>'x-guest-token'
               OR host_token_hash = encode(
                    digest(
                        convert_to(COALESCE(current_setting('request.headers', true)::jsonb->>'x-host-token', ''), 'UTF8'),
                        'sha256'
                    ),
                    'hex'
                )
        )
    )
    WITH CHECK (
        session_id IN (
            SELECT session_id
            FROM sessions
            WHERE guest_token = current_setting('request.headers', true)::jsonb->>'x-guest-token'
               OR host_token_hash = encode(
                    digest(
                        convert_to(COALESCE(current_setting('request.headers', true)::jsonb->>'x-host-token', ''), 'UTF8'),
                        'sha256'
                    ),
                    'hex'
                )
        )
    );

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime') THEN
        IF NOT EXISTS (
            SELECT 1
            FROM pg_publication_tables
            WHERE pubname = 'supabase_realtime'
              AND schemaname = 'public'
              AND tablename = 'cart_items'
        ) THEN
            ALTER PUBLICATION supabase_realtime ADD TABLE cart_items;
        END IF;
    END IF;
END $$;
