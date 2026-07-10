-- Idempotency ledger for processed WhatsApp webhook messages.
-- Meta's Cloud API retries webhook deliveries with the same wamid; the unique
-- index guarantees each (message_id, event_type) pair is recorded exactly once.

CREATE TABLE IF NOT EXISTS session_events (
    id BIGSERIAL PRIMARY KEY,
    message_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    session_id TEXT REFERENCES sessions(session_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_session_events_message_id_event_type
    ON session_events (message_id, event_type);

-- No policies: session_events is service-role only, never client-readable.
ALTER TABLE session_events ENABLE ROW LEVEL SECURITY;
