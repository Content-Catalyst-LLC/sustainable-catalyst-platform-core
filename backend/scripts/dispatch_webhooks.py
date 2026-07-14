#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import Settings
from app.database import Database
from app.migrations import run_migrations
from app.services.developers import dispatch_pending_webhooks


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dispatch pending Sustainable Catalyst webhooks."
    )
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    settings = Settings.from_env()
    database = Database(settings.database_url)
    run_migrations(database)

    with database.session_factory() as db:
        result = dispatch_pending_webhooks(
            db,
            master_secret=settings.webhook_signing_secret,
            timeout=settings.webhook_delivery_timeout,
            limit=max(1, min(args.limit, 1000)),
        )
        print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
