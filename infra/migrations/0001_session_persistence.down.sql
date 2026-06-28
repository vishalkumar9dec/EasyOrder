-- Roll back EasyOrder session persistence objects.

DROP POLICY IF EXISTS cart_items_session_access ON cart_items;
DROP POLICY IF EXISTS sessions_host_update ON sessions;
DROP POLICY IF EXISTS sessions_read ON sessions;

DROP TABLE IF EXISTS cart_items;
DROP TABLE IF EXISTS sessions;
