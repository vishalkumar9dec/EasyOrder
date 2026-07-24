"""Versioned migration runner for EasyOrder's Postgres schema.

Replaces the shell-loop pattern (`make db-migrate`: reapplies every *.sql
file every time, relying on each migration being written idempotently) with
real version tracking: a `schema_migrations` table records which migrations
have already run, so this script only ever applies what's new. Safe to run
repeatedly (e.g. on every deploy) — a fully up-to-date database is a no-op.

Usage:
    python3 scripts/run_migrations.py                # apply pending migrations
    python3 scripts/run_migrations.py --down          # roll back the most recent one
    python3 scripts/run_migrations.py --database-url postgresql://...
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = REPO_ROOT / "infra" / "migrations"

_VERSION_RE = re.compile(r"^(\d+)_")


def migration_version(path: Path) -> str:
    match = _VERSION_RE.match(path.name)
    if not match:
        raise ValueError(f"Migration file {path.name} does not start with a numeric version")
    return match.group(1)


def discover_migrations() -> list[Path]:
    files = [
        path
        for path in MIGRATIONS_DIR.glob("*.sql")
        if not path.name.endswith(".down.sql")
    ]
    return sorted(files, key=lambda path: migration_version(path))


def down_file_for(up_file: Path) -> Path:
    return up_file.with_name(up_file.name.replace(".sql", ".down.sql"))


async def ensure_tracking_table(connection) -> None:
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version     TEXT PRIMARY KEY,
            filename    TEXT NOT NULL,
            applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )


async def applied_versions(connection) -> set[str]:
    rows = await connection.fetch("SELECT version FROM schema_migrations")
    return {row["version"] for row in rows}


async def apply_up(connection, *, quiet: bool = False) -> int:
    await ensure_tracking_table(connection)
    already_applied = await applied_versions(connection)

    applied_count = 0
    for migration in discover_migrations():
        version = migration_version(migration)
        if version in already_applied:
            continue
        sql = migration.read_text(encoding="utf-8")
        async with connection.transaction():
            await connection.execute(sql)
            await connection.execute(
                "INSERT INTO schema_migrations (version, filename) VALUES ($1, $2)",
                version,
                migration.name,
            )
        if not quiet:
            print(f"applied {migration.name}")
        applied_count += 1

    if applied_count == 0 and not quiet:
        print("database is already up to date")
    return applied_count


async def apply_down(connection, *, quiet: bool = False) -> int:
    await ensure_tracking_table(connection)
    row = await connection.fetchrow(
        "SELECT version, filename FROM schema_migrations ORDER BY version DESC LIMIT 1"
    )
    if row is None:
        if not quiet:
            print("no migrations have been applied; nothing to roll back")
        return 0

    up_file = MIGRATIONS_DIR / row["filename"]
    down_file = down_file_for(up_file)
    if not down_file.exists():
        raise FileNotFoundError(f"No down migration found for {row['filename']} ({down_file.name})")

    sql = down_file.read_text(encoding="utf-8")
    async with connection.transaction():
        await connection.execute(sql)
        await connection.execute(
            "DELETE FROM schema_migrations WHERE version = $1", row["version"]
        )
    if not quiet:
        print(f"rolled back {up_file.name} (via {down_file.name})")
    return 1


async def run(database_url: str, *, down: bool) -> int:
    import asyncpg

    connection = await asyncpg.connect(database_url)
    try:
        if down:
            return await apply_down(connection)
        return await apply_up(connection)
    finally:
        await connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        default=None,
        help="Postgres connection URL (default: DATABASE_URL env var, or "
        "EasyOrder's local dev default)",
    )
    parser.add_argument(
        "--down",
        action="store_true",
        help="Roll back the single most recently applied migration",
    )
    args = parser.parse_args()

    import os

    database_url = (
        args.database_url
        or os.environ.get("DATABASE_URL")
        or "postgresql://easyorder:easyorder@localhost:5432/easyorder"
    )
    asyncio.run(run(database_url, down=args.down))
    return 0


if __name__ == "__main__":
    sys.exit(main())
