from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parents[3] / "infra" / "migrations"
MIGRATION = MIGRATIONS_DIR / "0001_session_persistence.sql"
DOWN_MIGRATION = MIGRATIONS_DIR / "0001_session_persistence.down.sql"
EVENTS_MIGRATION = MIGRATIONS_DIR / "0002_session_events.sql"
EVENTS_DOWN_MIGRATION = MIGRATIONS_DIR / "0002_session_events.down.sql"


def test_session_persistence_migration_defines_required_tables_constraints_and_indexes() -> None:
    sql = MIGRATION.read_text()

    assert "CREATE TABLE IF NOT EXISTS sessions" in sql
    assert "CREATE TABLE IF NOT EXISTS cart_items" in sql
    assert "REFERENCES sessions(session_id) ON DELETE CASCADE" in sql
    status_check = (
        "CHECK (status IN "
        "('INITIALIZING','ACTIVE','DEGRADED','CHECKOUT_READY','CHECKOUT_PARTIAL','ORDERED'))"
    )
    assert status_check in sql
    assert "CHECK (dietary_preference IN ('VEG','NON-VEG','ANY'))" in sql
    assert "CHECK (dietary_tag IN ('VEG','NON-VEG','ANY'))" in sql
    assert "CHECK (vertical IN ('food','instamart'))" in sql
    assert "restaurant_id TEXT" in sql
    assert "restaurant_name TEXT" in sql
    assert "brand_name TEXT" in sql
    assert "source_label TEXT" in sql
    assert "CONSTRAINT cart_items_source_attribution" in sql
    assert "idx_sessions_whatsapp_group_id" in sql
    assert "idx_cart_items_session_id" in sql
    assert "idx_cart_items_session_vertical" in sql


def test_session_persistence_migration_defines_rls_and_realtime_publication_hook() -> None:
    sql = MIGRATION.read_text()

    assert "ALTER TABLE sessions ENABLE ROW LEVEL SECURITY" in sql
    assert "ALTER TABLE cart_items ENABLE ROW LEVEL SECURITY" in sql
    assert "CREATE POLICY sessions_read" in sql
    assert "CREATE POLICY sessions_host_update" in sql
    assert "CREATE POLICY cart_items_session_access" in sql
    assert "x-guest-token" in sql
    assert "x-host-token" in sql
    assert "digest(" in sql
    assert "ALTER PUBLICATION supabase_realtime ADD TABLE cart_items" in sql


def test_session_persistence_down_migration_drops_owned_objects() -> None:
    sql = DOWN_MIGRATION.read_text()

    assert "DROP POLICY IF EXISTS cart_items_session_access ON cart_items" in sql
    assert "DROP POLICY IF EXISTS sessions_host_update ON sessions" in sql
    assert "DROP POLICY IF EXISTS sessions_read ON sessions" in sql
    assert "DROP TABLE IF EXISTS cart_items" in sql
    assert "DROP TABLE IF EXISTS sessions" in sql


def test_session_events_migration_defines_dedupe_table_and_unique_index() -> None:
    sql = EVENTS_MIGRATION.read_text()

    assert "CREATE TABLE IF NOT EXISTS session_events" in sql
    assert "message_id   TEXT" in sql
    assert "event_type  TEXT NOT NULL" in sql
    assert "REFERENCES sessions(session_id) ON DELETE CASCADE" in sql
    assert "'whatsapp_tagged_message'" in sql
    assert "CREATE UNIQUE INDEX IF NOT EXISTS idx_session_events_message_id_event_type" in sql
    assert "ON session_events (message_id, event_type)" in sql
    assert "ALTER TABLE session_events ENABLE ROW LEVEL SECURITY" in sql


def test_session_events_down_migration_drops_owned_objects() -> None:
    sql = EVENTS_DOWN_MIGRATION.read_text()

    assert "DROP INDEX IF EXISTS idx_session_events_message_id_event_type" in sql
    assert "DROP TABLE IF EXISTS session_events" in sql
