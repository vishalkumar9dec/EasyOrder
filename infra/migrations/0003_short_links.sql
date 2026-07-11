-- Short-link aliases for tokenized session URLs (task 10.2 / task 10.7).
-- Codes are opaque and carry no token material; the mapping is resolved
-- server-side by GET /api/r/{code}. Service-role only, never client-readable.

CREATE TABLE IF NOT EXISTS short_links (
    code        TEXT PRIMARY KEY,
    target_path TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE short_links ENABLE ROW LEVEL SECURITY;
