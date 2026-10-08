from __future__ import annotations

import argparse
import re
import time
from datetime import datetime, timezone

from sqlalchemy import desc, select

from app.config import Settings
from app.database import Database
from app.models import ConnectorWorkItem, LiveDataConnector
from app.services.connector_execution_profiles import (
    profile_requested_by,
    resolve_profile_parameters,
    scheduled_profiles,
    validate_profile_against_connector,
)
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

    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", policy)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        total = hours * 3600 + minutes * 60 + seconds
        return total if total > 0 else None

    match = re.fullmatch(r"P(\d+)D", policy)
    if match:
        return int(match.group(1)) * 86400

    return None


def has_required_parameters(connector: LiveDataConnector) -> bool:
    config = dict(connector.configuration_json or {})
    return bool(config.get("required_parameters") or config.get("required_one_of"))


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
                    f"skip={connector.id} reason=unsupported-refresh-policy policy={connector.refresh_policy}",
                    flush=True,
                )
                continue

            if has_required_parameters(connector):
                counters["parameterized"] += 1
                continue

            config_state = runtime.connector_configuration_status(connector)
            if config_state != "configured":
                counters["blocked"] += 1
                print(f"skip={connector.id} reason={config_state}", flush=True)
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
            priority = max(1, min(500, interval // 60))

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
                f"queued={work.id} connector={connector.id} refresh={connector.refresh_policy} priority={priority}",
                flush=True,
            )

    print(
        "scheduler-pass " + " ".join(f"{key}={value}" for key, value in counters.items()),
        flush=True,
    )
    return counters


def _has_active_profile_work(db, profile_id: str) -> bool:
    requested_by = profile_requested_by(profile_id)
    return (
        db.scalar(
            select(ConnectorWorkItem.id)
            .where(
                ConnectorWorkItem.requested_by == requested_by,
                ConnectorWorkItem.status.in_(["pending", "claimed"]),
            )
            .limit(1)
        )
        is not None
    )


def _latest_profile_activity(db, profile_id: str):
    requested_by = profile_requested_by(profile_id)
    row = db.scalar(
        select(ConnectorWorkItem)
        .where(ConnectorWorkItem.requested_by == requested_by)
        .order_by(desc(ConnectorWorkItem.created_at))
        .limit(1)
    )
    if row is None:
        return None
    return ensure_utc(row.completed_at or row.created_at)


def schedule_parameterized_profiles(database, runtime):
    settings = runtime.settings
    profiles = scheduled_profiles()
    allowlist = set(settings.parameterized_profile_scheduler_ids)
    counters = {
        "enabled": int(bool(settings.parameterized_profile_scheduler_enabled)),
        "profiles": len(profiles),
        "selected": 0,
        "due": 0,
        "queued": 0,
        "current": 0,
        "active": 0,
        "blocked": 0,
        "invalid": 0,
        "allowlist_filtered": 0,
        "max_per_pass": settings.parameterized_profile_max_per_pass,
    }

    if not settings.parameterized_profile_scheduler_enabled:
        print(
            "profile-scheduler " + " ".join(f"{key}={value}" for key, value in counters.items()),
            flush=True,
        )
        return counters

    now = utcnow()

    with database.session_factory() as db:
        for profile in profiles:
            if counters["queued"] >= settings.parameterized_profile_max_per_pass:
                break

            if allowlist and profile.profile_id not in allowlist:
                counters["allowlist_filtered"] += 1
                continue

            counters["selected"] += 1
            connector = db.get(LiveDataConnector, profile.connector_id)

            if connector is None or not connector.enabled or connector.status != "active":
                counters["blocked"] += 1
                print(
                    f"profile-skip={profile.profile_id} connector={profile.connector_id} reason=connector-unavailable",
                    flush=True,
                )
                continue

            config_state = runtime.connector_configuration_status(connector)
            if config_state != "configured":
                counters["blocked"] += 1
                print(
                    f"profile-skip={profile.profile_id} connector={profile.connector_id} reason={config_state}",
                    flush=True,
                )
                continue

            try:
                parameters = resolve_profile_parameters(profile, now=now)
                validate_profile_against_connector(profile, connector, parameters=parameters)
            except ValueError as exc:
                counters["invalid"] += 1
                print(
                    f"profile-skip={profile.profile_id} connector={profile.connector_id} reason=invalid-profile detail={str(exc)[:300]}",
                    flush=True,
                )
                continue

            interval = refresh_seconds(profile.refresh_policy)
            if interval is None:
                counters["invalid"] += 1
                print(
                    f"profile-skip={profile.profile_id} reason=unsupported-refresh-policy policy={profile.refresh_policy}",
                    flush=True,
                )
                continue

            if _has_active_profile_work(db, profile.profile_id):
                counters["active"] += 1
                continue

            activity = _latest_profile_activity(db, profile.profile_id)
            if activity is not None:
                age = (now - activity).total_seconds()
                if age < interval:
                    counters["current"] += 1
                    continue

            counters["due"] += 1
            work = queue_connector_work(
                db,
                profile.connector_id,
                parameters=parameters,
                requested_by=profile_requested_by(profile.profile_id),
                priority=profile.priority,
                max_attempts=profile.max_attempts,
            )
            counters["queued"] += 1
            print(
                f"profile-queued={work.id} profile={profile.profile_id} connector={profile.connector_id} refresh={profile.refresh_policy} priority={profile.priority}",
                flush=True,
            )

    print(
        "profile-scheduler " + " ".join(f"{key}={value}" for key, value in counters.items()),
        flush=True,
    )
    return counters


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    settings = Settings.from_env()
    database = Database(settings.database_url)
    runtime = LiveDataRuntime(settings)

    while True:
        try:
            scheduler_pass(database, runtime)
            schedule_parameterized_profiles(database, runtime)
        except Exception as exc:
            print(f"scheduler-error={type(exc).__name__}: {exc}", flush=True)
            if args.once:
                raise

        if args.once:
            break

        time.sleep(max(10, args.poll_seconds))


if __name__ == "__main__":
    main()
