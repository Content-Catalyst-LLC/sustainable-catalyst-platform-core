from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..models import AlertRule, ConnectorWorkItem, DeadLetterRecord, GeographicSubscription
from ..public_api_auth import PublicApiContext, require_public_scope
from ..services.reliability import (
    list_stream_events,
    process_next_work,
    queue_connector_work,
    replay_dead_letter,
    resolve_failover,
    sse_encode,
    stale_connectors,
)

router = APIRouter(prefix="/v1/reliability", tags=["Streaming, Alerts, and Source Reliability"])
public_router = APIRouter(prefix="/api/v1/reliability", tags=["Unified Public API — Reliability"])


class QueueWorkRequest(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)
    requested_by: str = "platform-core"
    priority: int = Field(default=100, ge=0, le=1000)
    max_attempts: int = Field(default=3, ge=1, le=20)


class WorkerRunRequest(BaseModel):
    worker_id: str = Field(min_length=1, max_length=200)


class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    domain: str | None = None
    metric: str | None = None
    connector_id: str | None = None
    source_id: str | None = None
    operator: str = "exists"
    threshold_number: float | None = None
    geography: dict[str, Any] | None = None
    severity: str = "info"
    enabled: bool = True
    public: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class GeographicSubscriptionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    geometry: dict[str, Any]
    domains: list[str] = Field(default_factory=list)
    connector_ids: list[str] = Field(default_factory=list)
    event_types: list[str] = Field(default_factory=list)
    active: bool = True
    public: bool = False


def _work(row: ConnectorWorkItem) -> dict[str, Any]:
    return {
        "id": row.id, "connector_id": row.connector_id, "status": row.status,
        "priority": row.priority, "attempt_count": row.attempt_count, "max_attempts": row.max_attempts,
        "available_at": row.available_at, "lease_owner": row.lease_owner,
        "lease_expires_at": row.lease_expires_at, "last_error": row.last_error,
        "ingestion_run_id": row.ingestion_run_id, "execution_connector_id": row.execution_connector_id, "created_at": row.created_at,
        "updated_at": row.updated_at, "completed_at": row.completed_at,
    }


@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    settings = request.app.state.settings
    stale = stale_connectors(db, include_never=False)
    open_dead = len(db.scalars(select(DeadLetterRecord).where(DeadLetterRecord.status == "open")).all())
    pending = len(db.scalars(select(ConnectorWorkItem).where(ConnectorWorkItem.status == "pending")).all())
    return {
        "release": settings.version,
        "streaming_enabled": settings.streaming_enabled,
        "worker_enabled": settings.reliability_worker_enabled,
        "provider_failover_enabled": settings.provider_failover_enabled,
        "pending_work_items": pending,
        "open_dead_letters": open_dead,
        "stale_connectors": len(stale),
        "external_provider_health_release_blocking": False,
        "status": "ready" if settings.streaming_enabled else "disabled",
    }


@router.post("/queue/{connector_id}", dependencies=[Depends(require_write)])
def queue(connector_id: str, payload: QueueWorkRequest, db: Session = Depends(get_session)):
    try:
        row = queue_connector_work(
            db, connector_id, parameters=payload.parameters, requested_by=payload.requested_by,
            priority=payload.priority, max_attempts=payload.max_attempts,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _work(row)


@router.get("/queue", dependencies=[Depends(require_read)])
def queue_list(status: str | None = None, limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_session)):
    query = select(ConnectorWorkItem)
    if status:
        query = query.where(ConnectorWorkItem.status == status)
    rows = db.scalars(query.order_by(desc(ConnectorWorkItem.created_at)).limit(limit)).all()
    return {"items": [_work(row) for row in rows], "total": len(rows)}


@router.post("/worker/run-once", dependencies=[Depends(require_write)])
async def worker_run_once(payload: WorkerRunRequest, request: Request, db: Session = Depends(get_session)):
    if not request.app.state.settings.reliability_worker_enabled:
        raise HTTPException(status_code=503, detail="Connector worker is disabled.")
    row = await process_next_work(
        db, request.app.state.live_data_runtime, worker_id=payload.worker_id,
        lease_seconds=request.app.state.settings.reliability_worker_lease_seconds,
    )
    return {"processed": row is not None, "work_item": _work(row) if row else None}


@router.get("/stale-sources", dependencies=[Depends(require_read)])
def stale_sources(include_never: bool = True, db: Session = Depends(get_session)):
    rows = stale_connectors(db, include_never=include_never)
    return {"items": rows, "total": len(rows)}


@router.get("/failover/{connector_id}", dependencies=[Depends(require_read)])
def failover(connector_id: str, request: Request, db: Session = Depends(get_session)):
    if not request.app.state.settings.provider_failover_enabled:
        raise HTTPException(status_code=503, detail="Provider failover is disabled.")
    try:
        return resolve_failover(db, connector_id, request.app.state.live_data_runtime)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/dead-letters", dependencies=[Depends(require_read)])
def dead_letters(status: str | None = None, limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_session)):
    query = select(DeadLetterRecord)
    if status:
        query = query.where(DeadLetterRecord.status == status)
    rows = db.scalars(query.order_by(desc(DeadLetterRecord.created_at)).limit(limit)).all()
    return {"items": [{
        "id": row.id, "work_item_id": row.work_item_id, "connector_id": row.connector_id,
        "error_message": row.error_message, "attempt_count": row.attempt_count, "status": row.status,
        "replay_count": row.replay_count, "last_replayed_at": row.last_replayed_at,
        "created_at": row.created_at, "resolved_at": row.resolved_at,
    } for row in rows], "total": len(rows)}


@router.post("/dead-letters/{dead_letter_id}/replay", dependencies=[Depends(require_write)])
def replay(dead_letter_id: str, db: Session = Depends(get_session)):
    try:
        row = replay_dead_letter(db, dead_letter_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _work(row)


@router.post("/alerts/rules", dependencies=[Depends(require_write)])
def create_alert_rule(payload: AlertRuleCreate, db: Session = Depends(get_session)):
    if payload.operator not in {"exists", "gt", "gte", "lt", "lte", "eq", "neq"}:
        raise HTTPException(status_code=422, detail="Unsupported alert operator.")
    if payload.operator != "exists" and payload.threshold_number is None:
        raise HTTPException(status_code=422, detail="Threshold is required for this operator.")
    row = AlertRule(
        name=payload.name, domain=payload.domain, metric=payload.metric,
        connector_id=payload.connector_id, source_id=payload.source_id,
        operator=payload.operator, threshold_number=payload.threshold_number,
        geography_json=payload.geography, severity=payload.severity,
        enabled=payload.enabled, public=payload.public, metadata_json=payload.metadata,
    )
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "name": row.name, "operator": row.operator, "threshold_number": row.threshold_number,
            "domain": row.domain, "metric": row.metric, "severity": row.severity, "enabled": row.enabled, "public": row.public}


@router.get("/alerts/rules", dependencies=[Depends(require_read)])
def alert_rules(db: Session = Depends(get_session)):
    rows = db.scalars(select(AlertRule).order_by(AlertRule.name)).all()
    return {"items": [{"id": r.id, "name": r.name, "domain": r.domain, "metric": r.metric, "operator": r.operator,
                       "threshold_number": r.threshold_number, "severity": r.severity, "enabled": r.enabled, "public": r.public} for r in rows], "total": len(rows)}


@router.post("/subscriptions/geographic", dependencies=[Depends(require_write)])
def create_geo_subscription(payload: GeographicSubscriptionCreate, db: Session = Depends(get_session)):
    geometry = payload.geometry
    if geometry.get("type") == "bbox":
        bbox = geometry.get("bbox") or []
        if len(bbox) != 4:
            raise HTTPException(status_code=422, detail="bbox subscriptions require four coordinates.")
    row = GeographicSubscription(
        name=payload.name, geometry_json=geometry, domains_json=payload.domains,
        connector_ids_json=payload.connector_ids, event_types_json=payload.event_types,
        active=payload.active, public=payload.public,
    )
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "name": row.name, "geometry": row.geometry_json, "domains": row.domains_json,
            "connector_ids": row.connector_ids_json, "event_types": row.event_types_json, "active": row.active, "public": row.public}


@router.get("/subscriptions/geographic", dependencies=[Depends(require_read)])
def geo_subscriptions(db: Session = Depends(get_session)):
    rows = db.scalars(select(GeographicSubscription).order_by(GeographicSubscription.name)).all()
    return {"items": [{"id": r.id, "name": r.name, "geometry": r.geometry_json, "domains": r.domains_json,
                       "connector_ids": r.connector_ids_json, "event_types": r.event_types_json,
                       "active": r.active, "public": r.public} for r in rows], "total": len(rows)}


def _stream_generator(request: Request, *, after_id: int, event_type: str | None, public_only: bool, once: bool):
    async def generate():
        cursor = after_id
        while True:
            if await request.is_disconnected():
                break
            with request.app.state.database.session_factory() as session:
                events = list_stream_events(session, after_id=cursor, event_type=event_type, public_only=public_only, limit=200)
            if events:
                cursor = events[-1].id
                yield sse_encode(events)
            elif once:
                yield ": no-events\n\n"
            else:
                yield ": keepalive\n\n"
            if once:
                break
            await asyncio.sleep(request.app.state.settings.streaming_poll_seconds)
    return generate()


def _resume_id(request: Request, after_id: int) -> int:
    if after_id > 0:
        return after_id
    raw = (request.headers.get("last-event-id") or "").strip()
    try:
        return max(0, int(raw)) if raw else 0
    except ValueError:
        return 0


@router.get("/stream", dependencies=[Depends(require_read)])
def stream(request: Request, after_id: int = 0, event_type: str | None = None, once: bool = False):
    cursor = _resume_id(request, after_id)
    return StreamingResponse(_stream_generator(request, after_id=cursor, event_type=event_type, public_only=False, once=once), media_type="text/event-stream")


@public_router.get("/stream")
def public_stream(
    request: Request, after_id: int = 0, event_type: str | None = None, once: bool = False,
    _context: PublicApiContext = Depends(require_public_scope("data:read")),
):
    cursor = _resume_id(request, after_id)
    return StreamingResponse(_stream_generator(request, after_id=cursor, event_type=event_type, public_only=True, once=once), media_type="text/event-stream")
