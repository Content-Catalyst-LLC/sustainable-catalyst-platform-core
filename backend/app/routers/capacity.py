from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import capacity

router = APIRouter(prefix="/v1/capacity", tags=["Capacity Forecasting & Resource Governance"])
public_router = APIRouter(prefix="/api/v1/capacity", tags=["Unified Public API — Capacity Status"])


class ProfileWrite(BaseModel):
    resource_type: str = Field(min_length=1, max_length=80)
    resource_key: str = Field(min_length=1, max_length=255)
    product_scope: str | None = Field(default=None, max_length=100)
    unit: str = Field(default="count", min_length=1, max_length=80)
    capacity_limit: float = Field(gt=0)
    warning_utilization: float | None = Field(default=None, gt=0, lt=1)
    critical_utilization: float | None = Field(default=None, gt=0, le=1)
    forecast_horizon_hours: int | None = Field(default=None, ge=1, le=8760)
    enabled: bool = True
    public_summary: bool = True
    metadata: dict = Field(default_factory=dict)


class ObservationWrite(BaseModel):
    used_value: float = Field(ge=0)
    demand_value: float | None = Field(default=None, ge=0)
    source: str = Field(default="operator", min_length=1, max_length=120)
    observed_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)


class BudgetWrite(BaseModel):
    budget_key: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=300)
    product_scope: str | None = Field(default=None, max_length=100)
    resource_type: str = Field(min_length=1, max_length=80)
    resource_key: str | None = Field(default=None, max_length=255)
    unit: str = Field(default="count", min_length=1, max_length=80)
    budget_limit: float = Field(gt=0)
    warning_fraction: float = Field(default=0.80, gt=0, lt=1)
    enforcement_mode: str = Field(default="advisory")
    enabled: bool = True
    public_summary: bool = False
    metadata: dict = Field(default_factory=dict)


def bad(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))


@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    body = capacity.readiness(db, request.app.state.settings)
    migrations = migration_status(request.app.state.database)
    body.update({
        "release": request.app.state.settings.version,
        "migration_0027_applied": "0027" in migrations["applied"],
        "pending_migrations": migrations["pending"],
    })
    return body


@router.post("/profiles", dependencies=[Depends(require_write)])
def write_profile(payload: ProfileWrite, request: Request, db: Session = Depends(get_session)):
    try:
        row = capacity.upsert_profile(db, request.app.state.settings, **payload.model_dump())
        return jsonable_encoder(capacity.profile_dict(row))
    except ValueError as exc:
        raise bad(exc)


@router.get("/profiles", dependencies=[Depends(require_read)])
def profiles(
    enabled_only: bool = Query(False),
    product_scope: str | None = Query(None),
    db: Session = Depends(get_session),
):
    return {"items": jsonable_encoder([capacity.profile_dict(row) for row in capacity.list_profiles(db, enabled_only=enabled_only, product_scope=product_scope)])}


@router.post("/profiles/{profile_id}/observations", dependencies=[Depends(require_write)])
def observe(profile_id: str, payload: ObservationWrite, request: Request, db: Session = Depends(get_session)):
    try:
        row = capacity.record_observation(db, request.app.state.settings, profile_id, **payload.model_dump())
        return jsonable_encoder(capacity.observation_dict(row))
    except ValueError as exc:
        raise bad(exc)


@router.get("/profiles/{profile_id}/observations", dependencies=[Depends(require_read)])
def observations(profile_id: str, limit: int = Query(200, ge=1, le=5000), db: Session = Depends(get_session)):
    return {"items": jsonable_encoder([capacity.observation_dict(row) for row in capacity.list_observations(db, profile_id, limit=limit)])}


@router.post("/profiles/{profile_id}/forecast", dependencies=[Depends(require_write)])
def forecast(
    profile_id: str,
    request: Request,
    window_hours: int | None = Query(None, ge=1, le=87600),
    horizon_hours: int | None = Query(None, ge=1, le=8760),
    db: Session = Depends(get_session),
):
    try:
        row = capacity.generate_forecast(db, request.app.state.settings, profile_id, window_hours=window_hours, horizon_hours=horizon_hours)
        return jsonable_encoder(capacity.forecast_dict(row))
    except ValueError as exc:
        raise bad(exc)


@router.get("/forecasts", dependencies=[Depends(require_read)])
def forecasts(profile_id: str | None = Query(None), limit: int = Query(200, ge=1, le=5000), db: Session = Depends(get_session)):
    return {"items": jsonable_encoder([capacity.forecast_dict(row) for row in capacity.list_forecasts(db, profile_id=profile_id, limit=limit)])}


@router.post("/budgets", dependencies=[Depends(require_write)])
def write_budget(payload: BudgetWrite, db: Session = Depends(get_session)):
    try:
        row = capacity.upsert_budget(db, **payload.model_dump())
        return jsonable_encoder(capacity.budget_dict(row))
    except ValueError as exc:
        raise bad(exc)


@router.get("/budgets", dependencies=[Depends(require_read)])
def budgets(enabled_only: bool = Query(False), db: Session = Depends(get_session)):
    return {"items": jsonable_encoder([capacity.budget_dict(row) for row in capacity.list_budgets(db, enabled_only=enabled_only)])}


@router.post("/profiles/{profile_id}/assess", dependencies=[Depends(require_write)])
def assess(profile_id: str, request: Request, db: Session = Depends(get_session)):
    try:
        row = capacity.assess_profile(db, request.app.state.settings, profile_id)
        return jsonable_encoder(capacity.decision_dict(row))
    except ValueError as exc:
        raise bad(exc)


@router.post("/runtime/observe", dependencies=[Depends(require_write)])
def runtime_observe(request: Request, db: Session = Depends(get_session)):
    rows = capacity.collect_runtime_observations(db, request.app.state.settings)
    return {
        "observations": jsonable_encoder([capacity.observation_dict(row) for row in rows]),
        "automatic_collection": True,
        "automatic_actuation": False,
    }


@router.post("/observations/prune", dependencies=[Depends(require_write)])
def prune(request: Request, db: Session = Depends(get_session)):
    return {"pruned": capacity.prune_observations(db, request.app.state.settings)}


@public_router.get("/status")
def public_status(
    request: Request,
    db: Session = Depends(get_session),
    _context: PublicApiContext = Depends(require_public_scope("data:read")),
):
    safe = capacity.public_status(db, request.app.state.settings)
    safe["release"] = request.app.state.settings.version
    return PublicEnvelope(data=safe, meta={"api_version": "v1", "request_id": request.state.request_id})
