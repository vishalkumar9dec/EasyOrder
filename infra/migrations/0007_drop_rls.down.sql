-- Rollback for 0007_drop_rls.sql — re-enables RLS and recreates the exact
-- original policies from 0001/0002/0003/0006. Note: this restores the SQL,
-- not its effectiveness — it was inert before (see 0007_drop_rls.sql) and
-- would be inert again unless paired with a non-owner connection role.

ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE cart_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE short_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE login_otps ENABLE ROW LEVEL SECURITY;
ALTER TABLE web_sessions ENABLE ROW LEVEL SECURITY;

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

CREATE POLICY session_events_read ON session_events
    FOR SELECT
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
    );
