#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import Settings
from app.database import Database
from app.migrations import run_migrations
from app.schemas import LiveDataIngestionRunRead
from app.services.live_data import LiveDataRuntime, LiveDataRuntimeError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one Sustainable Catalyst Platform Core live-data connector."
    )
    parser.add_argument("--connector", required=True, help="Connector ID")
    parser.add_argument(
        "--parameters",
        default="{}",
        help="JSON object containing connector parameters",
    )
    parser.add_argument("--requested-by", default="live-data-cli")
    parser.add_argument(
        "--run-type",
        default="scheduled",
        choices=["manual", "scheduled", "replay", "validation"],
    )
    return parser.parse_args()


async def run() -> int:
    args = parse_args()
    try:
        parameters = json.loads(args.parameters)
    except json.JSONDecodeError as exc:
        print(json.dumps({"ok": False, "error": f"Invalid --parameters JSON: {exc}"}))
        return 2
    if not isinstance(parameters, dict):
        print(json.dumps({"ok": False, "error": "--parameters must decode to a JSON object."}))
        return 2

    settings = Settings.from_env()
    database = Database(settings.database_url)
    run_migrations(database)
    runtime = LiveDataRuntime(settings)
    with database.session_factory() as session:
        try:
            result = await runtime.ingest(
                session,
                args.connector,
                parameters=parameters,
                requested_by=args.requested_by,
                run_type=args.run_type,
            )
        except LiveDataRuntimeError as exc:
            print(json.dumps({"ok": False, "status_code": exc.status_code, "error": exc.detail}))
            return 1
        payload = LiveDataIngestionRunRead.model_validate(result).model_dump(
            mode="json", by_alias=True
        )
        print(json.dumps({"ok": True, "run": payload}, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
