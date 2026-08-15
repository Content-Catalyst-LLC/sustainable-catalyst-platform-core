from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import json
from typing import Any, Iterable

from sqlalchemy import and_, asc, delete, desc, or_, select
from sqlalchemy.orm import Session

from ..models import (
    AlertRule,
    ConnectorWorkItem,
    DeadLetterRecord,
    GeographicSubscription,
    LiveDataConnector,
    LiveDataObservation,
    StreamEvent,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


SENSITIVE_PARAMETER_PARTS = ("api_key", "apikey", "token", "secret", "password", "authorization", "credential", "registrationkey", "user_id", "userid")

def sanitize_queue_parameters(value: Any) -> Any:
    """Remove credential-like parameters before work is persisted.

    Connector credentials belong in deployment settings, not durable work records.
    """
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in SENSITIVE_PARAMETER_PARTS):
                continue
            result[key] = sanitize_queue_parameters(item)
        return result
    if isinstance(value, list):
        return [sanitize_queue_parameters(item) for item in value]
    return value


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def emit_event(
    db: Session,
    event_type: str,
    subject_type: str,
    subject_id: str | None,
    payload: dict[str, Any] | None = None,
    *,
    public: bool = True,
    commit: bool = True,
) -> StreamEvent:
    row = StreamEvent(
        event_type=event_type,
        subject_type=subject_type,
        subject_id=subject_id,
        payload_json=dict(payload or {}),
        public=public,
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
    return row


def queue_connector_work(
    db: Session,
    connector_id: str,
    *,
    parameters: dict[str, Any] | None = None,
    requested_by: str = "platform-core",
    priority: int = 100,
    max_attempts: int = 3,
    available_at: datetime | None = None,
) -> ConnectorWorkItem:
    if db.get(LiveDataConnector, connector_id) is None:
        raise ValueError("Unknown live-data connector.")
    row = ConnectorWorkItem(
        connector_id=connector_id,
        parameters_json=sanitize_queue_parameters(dict(parameters or {})),
        requested_by=requested_by,
        priority=max(0, min(int(priority), 1000)),
        max_attempts=max(1, min(int(max_attempts), 20)),
        available_at=available_at or utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    emit_event(
        db,
        "connector.work.queued",
        "connector_work_item",
        row.id,
        {"connector_id": row.connector_id, "priority": row.priority},
        public=False,
    )
    return row


def release_expired_leases(db: Session, *, now: datetime | None = None) -> int:
    now = now or utcnow()
    rows = db.scalars(
        select(ConnectorWorkItem).where(
            ConnectorWorkItem.status == "claimed",
            ConnectorWorkItem.lease_expires_at.is_not(None),
            ConnectorWorkItem.lease_expires_at < now,
        )
    ).all()
    for row in rows:
        row.status = "pending"
        row.lease_owner = None
        row.lease_expires_at = None
        row.updated_at = now
        db.add(row)
    if rows:
        db.commit()
    return len(rows)


def claim_next_work(
    db: Session,
    *,
    worker_id: str,
    lease_seconds: int = 60,
    now: datetime | None = None,
) -> ConnectorWorkItem | None:
    now = now or utcnow()
    release_expired_leases(db, now=now)
    row = db.scalar(
        select(ConnectorWorkItem)
        .where(
            ConnectorWorkItem.status == "pending",
            ConnectorWorkItem.available_at <= now,
        )
        .order_by(asc(ConnectorWorkItem.priority), asc(ConnectorWorkItem.created_at))
        .limit(1)
    )
    if row is None:
        return None
    row.status = "claimed"
    row.attempt_count += 1
    row.lease_owner = worker_id
    row.lease_expires_at = now + timedelta(seconds=max(5, min(lease_seconds, 3600)))
    row.updated_at = now
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def complete_work(db: Session, row: ConnectorWorkItem, ingestion_run_id: str | None, *, execution_connector_id: str | None = None) -> ConnectorWorkItem:
    now = utcnow()
    row.status = "completed"
    row.ingestion_run_id = ingestion_run_id
    row.execution_connector_id = execution_connector_id or row.connector_id
    row.completed_at = now
    row.lease_owner = None
    row.lease_expires_at = None
    row.last_error = None
    row.updated_at = now
    db.add(row)
    db.commit()
    db.refresh(row)
    emit_event(
        db,
        "connector.work.completed",
        "connector_work_item",
        row.id,
        {"connector_id": row.connector_id, "execution_connector_id": row.execution_connector_id, "ingestion_run_id": ingestion_run_id},
        public=False,
    )
    return row


def fail_work(
    db: Session,
    row: ConnectorWorkItem,
    error: str,
    *,
    retry_delay_seconds: int = 30,
) -> tuple[ConnectorWorkItem, DeadLetterRecord | None]:
    now = utcnow()
    row.last_error = str(error)[:8000]
    row.lease_owner = None
    row.lease_expires_at = None
    row.updated_at = now
    dead: DeadLetterRecord | None = None
    if row.attempt_count >= row.max_attempts:
        row.status = "dead_letter"
        row.completed_at = now
        dead = DeadLetterRecord(
            work_item_id=row.id,
            connector_id=row.connector_id,
            parameters_json=dict(row.parameters_json or {}),
            error_message=row.last_error or "Unknown connector failure.",
            attempt_count=row.attempt_count,
        )
        db.add(dead)
    else:
        row.status = "pending"
        row.available_at = now + timedelta(seconds=max(0, min(retry_delay_seconds, 86400)))
    db.add(row)
    db.commit()
    db.refresh(row)
    if dead is not None:
        db.refresh(dead)
        emit_event(
            db,
            "connector.work.dead_lettered",
            "dead_letter_record",
            dead.id,
            {"connector_id": row.connector_id, "attempt_count": row.attempt_count},
            public=False,
        )
    else:
        emit_event(
            db,
            "connector.work.retry_scheduled",
            "connector_work_item",
            row.id,
            {"connector_id": row.connector_id, "attempt_count": row.attempt_count},
            public=False,
        )
    return row, dead


async def process_next_work(db: Session, runtime, *, worker_id: str, lease_seconds: int = 60) -> ConnectorWorkItem | None:
    row = claim_next_work(db, worker_id=worker_id, lease_seconds=lease_seconds)
    if row is None:
        return None
    parameters = dict(row.parameters_json or {})
    try:
        run = await runtime.ingest(
            db,
            row.connector_id,
            parameters=parameters,
            requested_by=row.requested_by,
            run_type="worker",
        )
        complete_work(db, row, run.id, execution_connector_id=row.connector_id)
    except Exception as primary_exc:
        primary = db.get(LiveDataConnector, row.connector_id)
        compatible = bool((primary.configuration_json or {}).get("failover_parameters_compatible")) if primary else False
        settings = getattr(runtime, "settings", None)
        failover_enabled = bool(getattr(settings, "provider_failover_enabled", False))
        if failover_enabled and compatible and primary is not None:
            resolution = resolve_failover(db, row.connector_id, runtime)
            backup_id = resolution.get("selected_connector_id")
            if backup_id and backup_id != row.connector_id:
                try:
                    backup_run = await runtime.ingest(
                        db,
                        backup_id,
                        parameters=parameters,
                        requested_by=row.requested_by,
                        run_type="worker_failover",
                    )
                    complete_work(db, row, backup_run.id, execution_connector_id=backup_id)
                    emit_event(
                        db,
                        "connector.failover.completed",
                        "connector_work_item",
                        row.id,
                        {"requested_connector_id": row.connector_id, "selected_connector_id": backup_id, "ingestion_run_id": backup_run.id},
                        public=False,
                    )
                    return row
                except Exception as backup_exc:
                    fail_work(db, row, f"primary={primary_exc}; failover={backup_exc}")
                    return row
        fail_work(db, row, str(primary_exc))
    return row


def replay_dead_letter(db: Session, dead_letter_id: str, *, requested_by: str = "replay") -> ConnectorWorkItem:
    dead = db.get(DeadLetterRecord, dead_letter_id)
    if dead is None:
        raise ValueError("Unknown dead-letter record.")
    work = queue_connector_work(
        db,
        dead.connector_id,
        parameters=dict(dead.parameters_json or {}),
        requested_by=requested_by,
        priority=50,
    )
    dead.replay_count += 1
    dead.last_replayed_at = utcnow()
    dead.status = "replayed"
    db.add(dead)
    db.commit()
    emit_event(
        db,
        "dead_letter.replayed",
        "dead_letter_record",
        dead.id,
        {"connector_id": dead.connector_id, "work_item_id": work.id},
        public=False,
    )
    return work


def connector_staleness(connector: LiveDataConnector, *, now: datetime | None = None) -> dict[str, Any]:
    now = now or utcnow()
    last = _aware(connector.last_success_at)
    window = max(60, int(connector.freshness_window_seconds or 86400))
    if last is None:
        state = "never_succeeded"
        age_seconds = None
    else:
        age_seconds = max(0, int((now - last).total_seconds()))
        state = "stale" if age_seconds > window else "current"
    return {
        "connector_id": connector.id,
        "source_id": connector.source_id,
        "domain": connector.domain,
        "state": state,
        "last_success_at": last,
        "age_seconds": age_seconds,
        "freshness_window_seconds": window,
    }


def stale_connectors(db: Session, *, now: datetime | None = None, include_never: bool = True) -> list[dict[str, Any]]:
    rows = db.scalars(select(LiveDataConnector).where(LiveDataConnector.enabled.is_(True))).all()
    result = []
    for row in rows:
        item = connector_staleness(row, now=now)
        if item["state"] == "stale" or (include_never and item["state"] == "never_succeeded"):
            result.append(item)
    return result


def _failover_group(connector: LiveDataConnector) -> str:
    return str((connector.configuration_json or {}).get("failover_group") or "").strip()


def _failover_priority(connector: LiveDataConnector) -> int:
    try:
        return int((connector.configuration_json or {}).get("failover_priority", 100))
    except (TypeError, ValueError):
        return 100


def resolve_failover(db: Session, connector_id: str, runtime, *, now: datetime | None = None) -> dict[str, Any]:
    primary = db.get(LiveDataConnector, connector_id)
    if primary is None:
        raise ValueError("Unknown live-data connector.")
    group = _failover_group(primary)
    candidates = [primary]
    if group:
        candidates = [
            row for row in db.scalars(select(LiveDataConnector).where(LiveDataConnector.enabled.is_(True))).all()
            if _failover_group(row) == group
        ]
    candidates.sort(key=lambda row: (_failover_priority(row), row.id))
    evaluated = []
    chosen = None
    for row in candidates:
        configuration = runtime.connector_configuration_status(row)
        freshness = connector_staleness(row, now=now)
        operational = (
            row.enabled
            and row.status == "active"
            and configuration == "configured"
            and row.last_health_status not in {"degraded", "failed", "unavailable", "circuit_open"}
        )
        evaluated.append({
            "connector_id": row.id,
            "priority": _failover_priority(row),
            "configuration_status": configuration,
            "health_status": row.last_health_status,
            "freshness_state": freshness["state"],
            "eligible": operational,
        })
        if chosen is None and operational:
            chosen = row
    return {
        "requested_connector_id": connector_id,
        "failover_group": group or None,
        "selected_connector_id": chosen.id if chosen else None,
        "failover_used": bool(chosen and chosen.id != connector_id),
        "candidates": evaluated,
    }


def _compare(operator: str, value: float | None, threshold: float | None) -> bool:
    if operator == "exists":
        return value is not None
    if value is None or threshold is None:
        return False
    return {
        "gt": value > threshold,
        "gte": value >= threshold,
        "lt": value < threshold,
        "lte": value <= threshold,
        "eq": value == threshold,
        "neq": value != threshold,
    }.get(operator, False)


def _point_from_geometry(geometry: dict | None) -> tuple[float, float] | None:
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        return None
    coords = geometry.get("coordinates")
    if not isinstance(coords, list) or len(coords) < 2:
        return None
    try:
        return float(coords[0]), float(coords[1])
    except (TypeError, ValueError):
        return None


def _matches_geography(rule_geometry: dict | None, observation_geometry: dict | None) -> bool:
    if not rule_geometry:
        return True
    point = _point_from_geometry(observation_geometry)
    if point is None:
        return False
    if rule_geometry.get("type") == "bbox":
        bbox = rule_geometry.get("bbox") or []
        if len(bbox) != 4:
            return False
        lon, lat = point
        return float(bbox[0]) <= lon <= float(bbox[2]) and float(bbox[1]) <= lat <= float(bbox[3])
    return rule_geometry == observation_geometry


def evaluate_alerts(db: Session, observation: LiveDataObservation) -> list[StreamEvent]:
    rules = db.scalars(select(AlertRule).where(AlertRule.enabled.is_(True))).all()
    emitted = []
    for rule in rules:
        if rule.domain and rule.domain != observation.domain:
            continue
        if rule.metric and rule.metric != observation.metric:
            continue
        if rule.connector_id and rule.connector_id != observation.connector_id:
            continue
        if rule.source_id and rule.source_id != observation.source_id:
            continue
        if not _matches_geography(rule.geography_json, observation.geometry_json):
            continue
        if rule.operator == "exists":
            matched = observation.value_number is not None or bool((observation.value_text or "").strip())
        else:
            matched = _compare(rule.operator, observation.value_number, rule.threshold_number)
        if not matched:
            continue
        emitted.append(emit_event(
            db,
            "alert.triggered",
            "live_data_observation",
            observation.id,
            {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "severity": rule.severity,
                "connector_id": observation.connector_id,
                "source_id": observation.source_id,
                "domain": observation.domain,
                "metric": observation.metric,
                "value_number": observation.value_number,
                "unit": observation.unit,
                "observed_at": observation.observed_at.isoformat(),
            },
            public=bool(rule.public and observation.public),
        ))
    return emitted


def prune_stream_events(db: Session, *, retention_hours: int = 168, now: datetime | None = None) -> int:
    cutoff = (now or utcnow()) - timedelta(hours=max(1, min(int(retention_hours), 8760)))
    result = db.execute(delete(StreamEvent).where(StreamEvent.created_at < cutoff))
    db.commit()
    return int(result.rowcount or 0)


def list_stream_events(
    db: Session,
    *,
    after_id: int = 0,
    event_type: str | None = None,
    public_only: bool = False,
    limit: int = 100,
) -> list[StreamEvent]:
    conditions = [StreamEvent.id > max(0, after_id)]
    if event_type:
        conditions.append(StreamEvent.event_type == event_type)
    if public_only:
        conditions.append(StreamEvent.public.is_(True))
    return db.scalars(
        select(StreamEvent).where(and_(*conditions)).order_by(asc(StreamEvent.id)).limit(max(1, min(limit, 1000)))
    ).all()


def sse_encode(events: Iterable[StreamEvent]) -> str:
    chunks = []
    for event in events:
        data = json.dumps(event.payload_json or {}, sort_keys=True, default=str, separators=(",", ":"))
        chunks.append(f"id: {event.id}\nevent: {event.event_type}\ndata: {data}\n\n")
    return "".join(chunks)
