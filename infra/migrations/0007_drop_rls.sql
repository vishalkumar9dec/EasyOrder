-- Formally drop Row Level Security. See docs/adr/0007-drop-rls-app-layer-authorization.md.
--
-- RLS was structurally inert since the app connects as `easyorder`, the
-- table-owner role created by every migration — Postgres bypasses RLS for
-- table owners unless FORCE ROW LEVEL SECURITY is set, which it never was.
-- No second, non-owner role was ever created, so these policies never ran
-- against a single real request. The actual, tested authorization boundary
-- is application-layer: authorize_session_role() in
-- src/backend/app/api/session.py, which every session-scoped endpoint
-- already goes through. short_links/login_otps/web_sessions had RLS
-- enabled with zero policies (deny-all for any non-owner role) — also
-- dropped here for the same reason.

DROP POLICY IF EXISTS sessions_read ON sessions;
DROP POLICY IF EXISTS sessions_host_update ON sessions;
DROP POLICY IF EXISTS cart_items_session_access ON cart_items;
DROP POLICY IF EXISTS session_events_read ON session_events;

ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE cart_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE session_events DISABLE ROW LEVEL SECURITY;
ALTER TABLE short_links DISABLE ROW LEVEL SECURITY;
ALTER TABLE login_otps DISABLE ROW LEVEL SECURITY;
ALTER TABLE web_sessions DISABLE ROW LEVEL SECURITY;
