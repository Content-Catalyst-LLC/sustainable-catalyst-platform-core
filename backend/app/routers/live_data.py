from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from ..connectors import ADAPTERS
from ..dependencies import get_session, require_read, require_write
from ..models import LiveDataConnector, LiveDataSource
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import (
    LiveDataConnectorCreate,
    LiveDataConnectorPublicRead,
    LiveDataConnectorRead,
    LiveDataConnectorUpdate,
    LiveDataHealthConnector,
    LiveDataHealthSnapshot,
    LiveDataIngestRequest,
    LiveDataIngestionRunRead,
    LiveDataObservationRead,
    LiveDataSourceCreate,
    LiveDataSourceRead,
    LiveDataSourceUpdate,
    LiveDataStats,
    PublicEnvelope,
)
from ..services.live_data import (
    APPROVED_SOURCE_STATUSES,
    LiveDataRuntimeError,
    get_connector_or_404,
    get_observation_or_404,
    get_run_or_404,
    get_source_or_404,
    list_connectors,
    list_observations,
    list_runs,
    list_sources,
    live_data_stats,
    observation_provenance,
)

router = APIRouter(prefix="/v1/live", tags=["Free Live Data Gateway"])
public_router = APIRouter(prefix="/api/v1/live", tags=["Unified Public API — Live Data"])


def _public_envelope(request: Request, data, *, meta: dict | None = None) -> PublicEnvelope:
    payload_meta = {
        "api_version": "v1",
        "request_id": request.state.request_id,
        "documentation": "/docs#tag/Unified-Public-API-Live-Data",
    }
    if meta:
        payload_meta.update(meta)
    return PublicEnvelope(data=jsonable_encoder(data), meta=payload_meta)


def _check_https(value: str, *, environment: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=422, detail="Connector URLs must use HTTP or HTTPS.")
    if environment == "production" and parsed.scheme != "https":
        raise HTTPException(status_code=422, detail="Production connector URLs must use HTTPS.")


def _enforce_free_source(settings, *, access_cost: str, credit_card_required: bool, active: bool) -> None:
    if settings.live_data_strict_free_sources and active:
        if access_cost != "free" or credit_card_required:
            raise HTTPException(
                status_code=422,
                detail="Active sources must be free and must not require a credit card.",
            )


@router.get("/sources", response_model=list[LiveDataSourceRead], dependencies=[Depends(require_read)])
def sources(
    active: bool | None = True,
    review_status: str | None = None,
    db: Session = Depends(get_session),
):
    return list_sources(db, active=active, review_status=review_status)


@router.get("/sources/{source_id}", response_model=LiveDataSourceRead, dependencies=[Depends(require_read)])
def source(source_id: str, db: Session = Depends(get_session)):
    return get_source_or_404(db, source_id)


@router.post("/sources", response_model=LiveDataSourceRead, dependencies=[Depends(require_write)])
def create_source(payload: LiveDataSourceCreate, request: Request, db: Session = Depends(get_session)):
    if db.get(LiveDataSource, payload.id) is not None:
        raise HTTPException(status_code=409, detail="A live-data source with this ID already exists.")
    data = payload.model_dump()
    metadata = data.pop("metadata")
    for key in ("homepage_url", "documentation_url", "license_url"):
        if data.get(key) is not None:
            data[key] = str(data[key])
    _enforce_free_source(
        request.app.state.settings,
        access_cost=data["access_cost"],
        credit_card_required=data["credit_card_required"],
        active=data["active"],
    )
    record = LiveDataSource(**data, metadata_json=metadata)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/sources/{source_id}", response_model=LiveDataSourceRead, dependencies=[Depends(require_write)])
def update_source(
    source_id: str,
    payload: LiveDataSourceUpdate,
    request: Request,
    db: Session = Depends(get_session),
):
    record = get_source_or_404(db, source_id)
    data = payload.model_dump(exclude_unset=True)
    metadata = data.pop("metadata", None)
    for key in ("homepage_url", "documentation_url", "license_url"):
        if data.get(key) is not None:
            data[key] = str(data[key])
    proposed_cost = data.get("access_cost", record.access_cost)
    proposed_card = data.get("credit_card_required", record.credit_card_required)
    proposed_active = data.get("active", record.active)
    _enforce_free_source(
        request.app.state.settings,
        access_cost=proposed_cost,
        credit_card_required=proposed_card,
        active=proposed_active,
    )
    for key, value in data.items():
        setattr(record, key, value)
    if metadata is not None:
        record.metadata_json = metadata
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/connectors", response_model=list[LiveDataConnectorRead], dependencies=[Depends(require_read)])
def connectors(
    domain: str | None = None,
    source_id: str | None = None,
    enabled: bool | None = True,
    db: Session = Depends(get_session),
):
    return list_connectors(db, domain=domain, source_id=source_id, enabled=enabled)


@router.get("/connectors/health", response_model=LiveDataHealthSnapshot, dependencies=[Depends(require_read)])
def connector_health(request: Request, db: Session = Depends(get_session)):
    settings = request.app.state.settings
    runtime = request.app.state.live_data_runtime
    rows = list_connectors(db, enabled=None)
    items: list[LiveDataHealthConnector] = []
    configured = 0
    for row in rows:
        configuration_status = runtime.connector_configuration_status(row)
        if configuration_status == "configured":
            configured += 1
        items.append(
            LiveDataHealthConnector(
                id=row.id,
                source_id=row.source_id,
                domain=row.domain,
                status=row.status,
                configuration_status=configuration_status,
                last_health_status=row.last_health_status,
                last_health_checked_at=row.last_health_checked_at,
                last_success_at=row.last_success_at,
                last_failure_at=row.last_failure_at,
                last_error=row.last_error,
            )
        )
    if not settings.live_data_enabled:
        overall = "disabled"
    elif configured == len(rows):
        overall = "operational"
    elif configured > 0:
        overall = "operational_with_configuration_required"
    else:
        overall = "configuration_required"
    return LiveDataHealthSnapshot(
        enabled=settings.live_data_enabled,
        ingest_enabled=settings.live_data_ingest_enabled,
        strict_free_sources=settings.live_data_strict_free_sources,
        overall_status=overall,
        source_count=len(list_sources(db, active=None)),
        connector_count=len(rows),
        operational_connectors=configured,
        connectors=items,
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/connectors/{connector_id}", response_model=LiveDataConnectorRead, dependencies=[Depends(require_read)])
def connector(connector_id: str, db: Session = Depends(get_session)):
    return get_connector_or_404(db, connector_id)


@router.post("/connectors", response_model=LiveDataConnectorRead, dependencies=[Depends(require_write)])
def create_connector(
    payload: LiveDataConnectorCreate,
    request: Request,
    db: Session = Depends(get_session),
):
    if db.get(LiveDataConnector, payload.id) is not None:
        raise HTTPException(status_code=409, detail="A live-data connector with this ID already exists.")
    source = get_source_or_404(db, payload.source_id)
    if request.app.state.settings.live_data_strict_free_sources:
        if source.access_cost != "free" or source.credit_card_required or source.review_status not in APPROVED_SOURCE_STATUSES:
            raise HTTPException(status_code=422, detail="The connector source does not pass the free-source gate.")
    if payload.adapter not in ADAPTERS:
        raise HTTPException(status_code=422, detail="Unknown connector adapter.")
    data = payload.model_dump()
    configuration = data.pop("configuration")
    data["base_url"] = str(data["base_url"])
    _check_https(data["base_url"], environment=request.app.state.settings.environment)
    record = LiveDataConnector(**data, configuration_json=configuration)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/connectors/{connector_id}", response_model=LiveDataConnectorRead, dependencies=[Depends(require_write)])
def update_connector(
    connector_id: str,
    payload: LiveDataConnectorUpdate,
    request: Request,
    db: Session = Depends(get_session),
):
    record = get_connector_or_404(db, connector_id)
    data = payload.model_dump(exclude_unset=True)
    configuration = data.pop("configuration", None)
    if data.get("base_url") is not None:
        data["base_url"] = str(data["base_url"])
    if data.get("source_id"):
        source = get_source_or_404(db, data["source_id"])
        if request.app.state.settings.live_data_strict_free_sources:
            if source.access_cost != "free" or source.credit_card_required or source.review_status not in APPROVED_SOURCE_STATUSES:
                raise HTTPException(status_code=422, detail="The connector source does not pass the free-source gate.")
    if data.get("adapter") and data["adapter"] not in ADAPTERS:
        raise HTTPException(status_code=422, detail="Unknown connector adapter.")
    if data.get("base_url"):
        _check_https(data["base_url"], environment=request.app.state.settings.environment)
    for key, value in data.items():
        setattr(record, key, value)
    if configuration is not None:
        record.configuration_json = configuration
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post(
    "/connectors/{connector_id}/ingest",
    response_model=LiveDataIngestionRunRead,
    dependencies=[Depends(require_write)],
)
async def ingest_connector(
    connector_id: str,
    payload: LiveDataIngestRequest,
    request: Request,
    db: Session = Depends(get_session),
):
    try:
        return await request.app.state.live_data_runtime.ingest(
            db,
            connector_id,
            parameters=payload.parameters,
            requested_by=payload.requested_by,
            run_type=payload.run_type,
        )
    except LiveDataRuntimeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/runs", response_model=dict, dependencies=[Depends(require_read)])
def runs(
    connector_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    items, total = list_runs(db, connector_id=connector_id, status=status, limit=limit, offset=offset)
    return {"items": [LiveDataIngestionRunRead.model_validate(item).model_dump(mode="json", by_alias=True) for item in items], "total": total, "limit": limit, "offset": offset}


@router.get("/runs/{run_id}", response_model=LiveDataIngestionRunRead, dependencies=[Depends(require_read)])
def run(run_id: str, db: Session = Depends(get_session)):
    return get_run_or_404(db, run_id)


@router.get("/observations/latest", response_model=dict, dependencies=[Depends(require_read)])
def latest_observations(
    connector_id: str | None = None,
    source_id: str | None = None,
    domain: str | None = None,
    metric: str | None = None,
    freshness_status: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    items, total = list_observations(
        db,
        connector_id=connector_id,
        source_id=source_id,
        domain=domain,
        metric=metric,
        freshness_status=freshness_status,
        limit=limit,
        offset=offset,
    )
    return {"items": [LiveDataObservationRead.model_validate(item).model_dump(mode="json", by_alias=True) for item in items], "total": total, "limit": limit, "offset": offset}


@router.get("/timeseries", response_model=dict, dependencies=[Depends(require_read)])
def timeseries(
    metric: str,
    connector_id: str | None = None,
    source_id: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    items, total = list_observations(
        db,
        connector_id=connector_id,
        source_id=source_id,
        metric=metric,
        start=start,
        end=end,
        limit=limit,
        offset=offset,
    )
    return {"items": [LiveDataObservationRead.model_validate(item).model_dump(mode="json", by_alias=True) for item in items], "total": total, "limit": limit, "offset": offset}


@router.get("/observations/{observation_id}", response_model=LiveDataObservationRead, dependencies=[Depends(require_read)])
def observation(observation_id: str, db: Session = Depends(get_session)):
    return get_observation_or_404(db, observation_id)


@router.get("/provenance/{observation_id}", response_model=dict, dependencies=[Depends(require_read)])
def provenance(observation_id: str, db: Session = Depends(get_session)):
    record = get_observation_or_404(db, observation_id)
    return jsonable_encoder(observation_provenance(db, record))


@router.get("/stats", response_model=LiveDataStats, dependencies=[Depends(require_read)])
def stats(db: Session = Depends(get_session)):
    return live_data_stats(db)


# Scoped public API. Internal connector URLs, adapters, configuration, raw payloads,
# and non-public observations are deliberately excluded.
@public_router.get("/sources", response_model=PublicEnvelope)
def public_sources(
    request: Request,
    _context: PublicApiContext = Depends(require_public_scope("data:read")),
    db: Session = Depends(get_session),
):
    rows = list_sources(db, active=True, public_only=True)
    return _public_envelope(request, [LiveDataSourceRead.model_validate(row) for row in rows], meta={"total": len(rows)})


@public_router.get("/connectors", response_model=PublicEnvelope)
def public_connectors(
    request: Request,
    domain: str | None = None,
    _context: PublicApiContext = Depends(require_public_scope("data:read")),
    db: Session = Depends(get_session),
):
    rows = list_connectors(db, domain=domain, enabled=True, public_only=True)
    return _public_envelope(
        request,
        [LiveDataConnectorPublicRead.model_validate(row) for row in rows],
        meta={"total": len(rows)},
    )


@public_router.get("/observations/latest", response_model=PublicEnvelope)
def public_latest_observations(
    request: Request,
    connector_id: str | None = None,
    source_id: str | None = None,
    domain: str | None = None,
    metric: str | None = None,
    freshness_status: str | None = None,
    limit: int = Query(default=100, ge=1),
    offset: int = Query(default=0, ge=0),
    context: PublicApiContext = Depends(require_public_scope("data:read")),
    db: Session = Depends(get_session),
):
    limit = min(limit, context.plan.max_page_size, request.app.state.settings.page_size_max)
    rows, total = list_observations(
        db,
        connector_id=connector_id,
        source_id=source_id,
        domain=domain,
        metric=metric,
        freshness_status=freshness_status,
        public_only=True,
        limit=limit,
        offset=offset,
    )
    return _public_envelope(
        request,
        [LiveDataObservationRead.model_validate(row) for row in rows],
        meta={"pagination": {"total": total, "limit": limit, "offset": offset}},
    )


@public_router.get("/timeseries", response_model=PublicEnvelope)
def public_timeseries(
    request: Request,
    metric: str,
    connector_id: str | None = None,
    source_id: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(default=100, ge=1),
    offset: int = Query(default=0, ge=0),
    context: PublicApiContext = Depends(require_public_scope("data:read")),
    db: Session = Depends(get_session),
):
    limit = min(limit, context.plan.max_page_size, request.app.state.settings.page_size_max)
    rows, total = list_observations(
        db,
        connector_id=connector_id,
        source_id=source_id,
        metric=metric,
        start=start,
        end=end,
        public_only=True,
        limit=limit,
        offset=offset,
    )
    return _public_envelope(
        request,
        [LiveDataObservationRead.model_validate(row) for row in rows],
        meta={"pagination": {"total": total, "limit": limit, "offset": offset}},
    )


@public_router.get("/provenance/{observation_id}", response_model=PublicEnvelope)
def public_provenance(
    request: Request,
    observation_id: str,
    _context: PublicApiContext = Depends(require_public_scope("data:read")),
    db: Session = Depends(get_session),
):
    record = get_observation_or_404(db, observation_id, public_only=True)
    payload = observation_provenance(db, record)
    # Remove internal connector routing and run request details.
    source = payload.get("source")
    if source:
        payload["source"] = LiveDataSourceRead.model_validate(source)
    connector = payload.get("connector")
    if connector:
        payload["connector"] = LiveDataConnectorPublicRead.model_validate(connector)
    run = payload.get("ingestion_run")
    if run:
        payload["ingestion_run"] = {
            "id": run.id,
            "connector_id": run.connector_id,
            "status": run.status,
            "records_received": run.records_received,
            "records_created": run.records_created,
            "records_updated": run.records_updated,
            "records_rejected": run.records_rejected,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
        }
    return _public_envelope(request, payload)
