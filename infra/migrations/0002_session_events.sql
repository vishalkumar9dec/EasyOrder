-- EasyOrder session events — persisted activity timeline for the PWA and
-- idempotency ledger for processed WhatsApp webhook messages.
-- Events are written server-side and never expose host tokens or secrets.
-- Meta's Cloud API retries webhook deliveries with the same wamid; the unique
-- index guarantees each (message_id, event_type) pair is recorded exactly once.

CREATE TABLE IF NOT EXISTS session_events (
    id          BIGSERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    event_type  TEXT NOT NULL
                    CHECK (event_type IN (
                        'whatsapp_inbound',
                        'session_created',
                        'links_sent',
                        'whatsapp_tagged_message'
                    )),
    -- Redacted inbound message text (PII stripped by guardrails before storage)
    message_text TEXT,
    -- Derived intent label produced by the intent parser
    intent_label TEXT,
    -- WhatsApp message id, safe to surface
    message_id   TEXT,
    -- Normalised sender identifier (wa_id), never a host token
    sender_wa_id TEXT,
    -- Operating mode at event time: 'mock' | 'meta'
    mode         TEXT,
    -- Opaque correlation id for log linkage
    request_id   TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_session_events_session_id
    ON session_events (session_id, created_at);

CREATE UNIQUE INDEX IF NOT EXISTS idx_session_events_message_id_event_type
    ON session_events (message_id, event_type);

ALTER TABLE session_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS session_events_read ON session_events;
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
