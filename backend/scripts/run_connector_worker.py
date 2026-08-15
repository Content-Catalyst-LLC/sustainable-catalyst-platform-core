from __future__ import annotations

import argparse
import asyncio
import os
import socket
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import Settings
from app.database import Database
from app.migrations import run_migrations
from app.services.live_data import LiveDataRuntime
from app.services.reliability import process_next_work, prune_stream_events


async def run(*, once: bool, worker_id: str, idle_seconds: float) -> int:
    settings = Settings.from_env()
    if not settings.reliability_worker_enabled:
        print("ERROR - SC_CORE_RELIABILITY_WORKER_ENABLED is false")
        return 2
    database = Database(settings.database_url)
    run_migrations(database)
    runtime = LiveDataRuntime(settings)
    processed = 0
    while True:
        with database.session_factory() as db:
            prune_stream_events(db, retention_hours=settings.streaming_retention_hours)
            row = await process_next_work(
                db,
                runtime,
                worker_id=worker_id,
                lease_seconds=settings.reliability_worker_lease_seconds,
            )
        if row is not None:
            processed += 1
            print(f"processed={row.id} connector={row.connector_id} status={row.status}")
        elif once:
            print("queue-empty")
        if once:
            break
        if row is None:
            await asyncio.sleep(max(0.25, idle_seconds))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Sustainable Catalyst Core v2.12.0 connector worker")
    parser.add_argument("--once", action="store_true", help="Process at most one queued item and exit")
    parser.add_argument("--worker-id", default=f"{socket.gethostname()}:{os.getpid()}")
    parser.add_argument("--idle-seconds", type=float, default=2.0)
    args = parser.parse_args()
    return asyncio.run(run(once=args.once, worker_id=args.worker_id, idle_seconds=args.idle_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
