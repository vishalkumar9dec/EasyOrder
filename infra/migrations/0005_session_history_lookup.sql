-- Task 10.6 phase 1: order-history answers query the latest session per host.

CREATE INDEX IF NOT EXISTS idx_sessions_host_phone_created_at
    ON sessions (host_phone, created_at DESC);
