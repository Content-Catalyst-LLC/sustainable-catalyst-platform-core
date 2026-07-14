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
    parser = argparse.ArgumentParser(
        description="Import a Platform Core/Site Intelligence registry manifest."
    )
    parser.add_argument("manifest")
    args = parser.parse_args()

    payload = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    manifest = SiteIntelligenceManifest.model_validate(payload)

    settings = Settings.from_env()
    database = Database(settings.database_url)
    run_migrations(database)

    with database.session_factory() as db:
        job = import_site_intelligence_manifest(db, manifest)
        print(json.dumps({"id": job.id, "status": job.status}, indent=2))


if __name__ == "__main__":
    main()
