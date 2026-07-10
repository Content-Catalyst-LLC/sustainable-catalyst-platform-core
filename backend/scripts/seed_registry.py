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
from app.schemas import SiteIntelligenceManifest
from app.services.imports import import_site_intelligence_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        default=str(BACKEND / "data" / "platform_core_seed_v2.1.0.json"),
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Accepted for deployment compatibility; imports are idempotent.",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    database = Database(settings.database_url)
    run_migrations(database)

    data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    manifest = SiteIntelligenceManifest.model_validate(data)
    with database.session_factory() as db:
        job = import_site_intelligence_manifest(db, manifest)
        print(
            json.dumps(
                {
                    "job_id": job.id,
                    "status": job.status,
                    "entities_created": job.entities_created,
                    "entities_updated": job.entities_updated,
                    "relationships_created": job.relationships_created,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
