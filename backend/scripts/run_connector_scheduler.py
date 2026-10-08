from __future__ import annotations

import argparse
import re
import time
from datetime import datetime, timezone

from sqlalchemy import select

from app.config import Settings
from app.database import Database
from app.models import ConnectorWorkItem, LiveDataConnector
from app.services.live_data import LiveDataRuntime
from app.services.reliability import queue_connector_work


def utcnow():
    return datetime.now(timezone.utc)


def ensure_utc(value):
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def refresh_seconds(policy: str | None) -> int | None:
    policy = (policy or "").strip().upper()

    if not policy or policy == "MANUAL":
        return None

    m = re.fullmatch(
        r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
        policy,
    )

    if m:
        hours = int(m.group(1) or 0)
        minutes = int(m.group(2) or 0)
        seconds = int(m.group(3) or 0)

        total = hours * 3600 + minutes * 60 + seconds
        return total if total > 0 else None

    m = re.fullmatch(r"P(\d+)D", policy)

    if m:
        return int(m.group(1)) * 86400

    return None


def has_required_parameters(connector: LiveDataConnector) -> bool:
    config = dict(connector.configuration_json or {})

    return bool(
        config.get("required_parameters")
        or config.get("required_one_of")
    )


def has_active_work(db, connector_id: str) -> bool:
    row = db.scalar(
        select(ConnectorWorkItem.id)
        .where(
            ConnectorWorkItem.connector_id == connector_id,
            ConnectorWorkItem.status.in_(["pending", "claimed"]),
        )
        .limit(1)
    )

    return row is not None


def latest_activity(connector: LiveDataConnector):
    values = [
        ensure_utc(connector.last_success_at),
        ensure_utc(connector.last_failure_at),
    ]

    values = [value for value in values if value is not None]

    return max(values) if values else None


def scheduler_pass(database, runtime):
    now = utcnow()

    counters = {
        "examined": 0,
        "eligible": 0,
        "due": 0,
        "queued": 0,
        "current": 0,
        "active": 0,
        "parameterized": 0,
        "manual": 0,
        "blocked": 0,
        "unsupported_policy": 0,
    }

    with database.session_factory() as db:
        connectors = list(
            db.scalars(
                select(LiveDataConnector)
                .where(
                    LiveDataConnector.enabled.is_(True),
                    LiveDataConnector.status == "active",
                )
                .order_by(LiveDataConnector.id)
            ).all()
        )

        for connector in connectors:
            counters["examined"] += 1

            if connector.refresh_policy == "manual":
                counters["manual"] += 1
                continue

            interval = refresh_seconds(connector.refresh_policy)

            if interval is None:
                counters["unsupported_policy"] += 1
                print(
                    f"skip={connector.id} "
                    f"reason=unsupported-refresh-policy "
                    f"policy={connector.refresh_policy}",
                    flush=True,
                )
                continue

            if has_required_parameters(connector):
                counters["parameterized"] += 1
                continue

            config_state = runtime.connector_configuration_status(connector)

            if config_state != "configured":
                counters["blocked"] += 1
                print(
                    f"skip={connector.id} "
                    f"reason={config_state}",
                    flush=True,
                )
                continue

            counters["eligible"] += 1

            if has_active_work(db, connector.id):
                counters["active"] += 1
                continue

            activity = latest_activity(connector)

            if activity is not None:
                age = (now - activity).total_seconds()

                if age < interval:
                    counters["current"] += 1
                    continue

            counters["due"] += 1

            priority = max(
                1,
                min(500, interval // 60),
            )

            work = queue_connector_work(
                db,
                connector.id,
                parameters={},
                requested_by="connector-scheduler",
                priority=priority,
                max_attempts=3,
            )

            counters["queued"] += 1

            print(
                f"queued={work.id} "
                f"connector={connector.id} "
                f"refresh={connector.refresh_policy} "
                f"priority={priority}",
                flush=True,
            )

    print(
        "scheduler-pass "
        + " ".join(
            f"{key}={value}"
            for key, value in counters.items()
        ),
        flush=True,
    )

    return counters


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=60,
    )

    parser.add_argument(
        "--once",
        action="store_true",
    )

    args = parser.parse_args()

    settings = Settings.from_env()
    database = Database(settings.database_url)
    runtime = LiveDataRuntime(settings)

    while True:
        try:
            scheduler_pass(database, runtime)
        except Exception as exc:
            print(
                f"scheduler-error={type(exc).__name__}: {exc}",
                flush=True,
            )

            if args.once:
                raise

        if args.once:
            break

        time.sleep(max(10, args.poll_seconds))


if __name__ == "__main__":
    main()
