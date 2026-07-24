"""Purge EasyOrder sessions (and cascading cart/timeline data) past retention.

DPDP-style data retention: EasyOrder stores phone numbers and order history
indefinitely today (docs/production-readiness.md). This script deletes
sessions older than a configurable cutoff. Intended to run on a schedule
(cron/CI job) against the production database; safe to run repeatedly.

Usage:
    python3 scripts/easyorder_data_retention.py --retention-days 90
    python3 scripts/easyorder_data_retention.py --retention-days 90 --dry-run
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "src" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.api.whatsapp import create_db_adapter_for_settings  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.services.memory_db import InMemoryDBAdapter  # noqa: E402


async def run_retention(retention_days: int, *, dry_run: bool) -> int:
    settings = get_settings()
    db = create_db_adapter_for_settings(settings)
    if isinstance(db, InMemoryDBAdapter):
        print(
            "PERSISTENCE_MODE=memory: sessions do not survive a restart, "
            "nothing to purge. This script is only meaningful in postgres mode."
        )
        return 0

    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    if dry_run:
        print(f"[dry-run] would delete sessions created before {cutoff.isoformat()}")
        return 0

    deleted = await db.delete_sessions_older_than(cutoff)
    print(f"Deleted {deleted} session(s) created before {cutoff.isoformat()}")
    return deleted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--retention-days",
        type=int,
        default=90,
        help="Delete sessions older than this many days (default: 90)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report the cutoff without deleting anything",
    )
    args = parser.parse_args()

    import asyncio

    asyncio.run(run_retention(args.retention_days, dry_run=args.dry_run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
