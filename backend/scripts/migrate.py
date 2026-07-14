#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations


def main() -> None:
    settings = Settings.from_env()
    database = Database(settings.database_url)
    applied = run_migrations(database)
    status = migration_status(database)
    print(json.dumps({"newly_applied": applied, **status}, indent=2))


if __name__ == "__main__":
    main()
