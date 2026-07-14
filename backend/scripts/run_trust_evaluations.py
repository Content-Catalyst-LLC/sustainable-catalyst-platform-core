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
from app.schemas import EvaluationSuiteRequest
from app.services.trust import run_suite


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Sustainable Catalyst Trust Center evaluations.")
    parser.add_argument("--context", type=Path, help="Optional JSON file with definition_ids, contexts, environment, and target_entity_id.")
    parser.add_argument("--triggered-by", default="trust-evaluation-cli")
    args = parser.parse_args()

    payload = {}
    if args.context:
        payload = json.loads(args.context.read_text(encoding="utf-8"))
    payload.setdefault("triggered_by", args.triggered_by)

    settings = Settings.from_env()
    database = Database(settings.database_url)
    run_migrations(database)
    with database.session_factory() as db:
        result = run_suite(db, EvaluationSuiteRequest.model_validate(payload), settings)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
