from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations


def main() -> int:
    settings = Settings.from_env()
    database = Database(settings.database_url)
    run_migrations(database)
    status = migration_status(database)
    payload = {
        "version": settings.version,
        "migration_0012_applied": "0012" in status["applied"],
        "pending_migrations": status["pending"],
        "streaming_enabled": settings.streaming_enabled,
        "worker_enabled": settings.reliability_worker_enabled,
        "provider_failover_enabled": settings.provider_failover_enabled,
        "external_provider_health_release_blocking": False,
    }
    print(json.dumps(payload, indent=2))
    if settings.version != "2.11.0" or not payload["migration_0012_applied"] or status["pending"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
