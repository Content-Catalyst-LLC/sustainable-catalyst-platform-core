from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import scenario_compute

router = APIRouter(prefix="/v1/scenario-compute", tags=["Scenario Compute Engine"])
public_router = APIRouter(prefix="/api/v1/scenario-compute", tags=["Unified Public API — Scenario Compute Engine"])

class PlanCreate(BaseModel):
    plan_key: str = Field(min_length=1, max_length=180)
    name: str = Field(min_length=1, max_length=300)
    description: str | None = None
    visibility: str = "private"
    project_entity_id: str
    model_entity_id: str
    model_version_entity_id: str
    scenario_landscape_visual_entity_id: str | None = None
    model_canvas_visual_entity_id: str | None = None
    plan_state: str = "draft"
    execution_product: str | None = None
    execution_contract: dict[str, Any] = Field(default_factory=dict)
    output_contract: dict[str, Any] = Field(default_factory=dict)
    concurrency_policy: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str = "operator"

class DataCreate(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)

class PrepareRequest(BaseModel):
    submitted_by: str = "operator"

class BindRunRequest(BaseModel):
    model_run_entity_id: str

def bad(exc):
    return exc if isinstance(exc, HTTPException) else HTTPException(status_code=422, detail=str(exc))

def public_enabled(request: Request):
    if not request.app.state.settings.scenario_compute_engine_public_metadata_enabled:
        raise HTTPException(status_code=404, detail="Scenario Compute Engine public metadata API is disabled.")

@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    data = scenario_compute.readiness(db); m = migration_status(request.app.state.database)
    data.update({"release": request.app.state.settings.version, "enabled": request.app.state.settings.scenario_compute_engine_enabled, "migration_0038_applied": "0038" in m["applied"]})
    return data

@router.post("/plans", dependencies=[Depends(require_write)])
def create_plan(payload: PlanCreate, request: Request, db: Session = Depends(get_session)):
    if not request.app.state.settings.scenario_compute_engine_enabled:
        raise HTTPException(status_code=503, detail="Scenario Compute Engine is disabled.")
    try: return scenario_compute.create_plan(db, payload.model_dump())
    except Exception as exc: raise bad(exc)

@router.get("/plans", dependencies=[Depends(require_read)])
def list_plans(request: Request, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), db: Session = Depends(get_session)):
    items, total = scenario_compute.list_plans(db, limit=min(limit, request.app.state.settings.page_size_max), offset=offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}

@router.get("/plans/{plan_id}", dependencies=[Depends(require_read)])
def detail(plan_id: str, db: Session = Depends(get_session)): return scenario_compute.read_plan(db, plan_id)

@router.get("/plans/{plan_id}/bundle", dependencies=[Depends(require_read)])
def bundle(plan_id: str, db: Session = Depends(get_session)): return scenario_compute.bundle(db, plan_id)

@router.get("/plans/{plan_id}/validate", dependencies=[Depends(require_read)])
def validate(plan_id: str, db: Session = Depends(get_session)): return scenario_compute.validate_plan(db, plan_id)

@router.get("/plans/{plan_id}/summary", dependencies=[Depends(require_read)])
def summary(plan_id: str, db: Session = Depends(get_session)): return scenario_compute.plan_summary(db, plan_id)

@router.post("/plans/{plan_id}/cases", dependencies=[Depends(require_write)])
def add_case(plan_id: str, payload: DataCreate, db: Session = Depends(get_session)):
    try: return scenario_compute.add_case(db, plan_id, payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/plans/{plan_id}/prepare", dependencies=[Depends(require_write)])
def prepare(plan_id: str, payload: PrepareRequest, db: Session = Depends(get_session)):
    try: return scenario_compute.prepare_requests(db, plan_id, submitted_by=payload.submitted_by)
    except Exception as exc: raise bad(exc)

@router.get("/requests/{request_id}", dependencies=[Depends(require_read)])
def request_detail(request_id: str, db: Session = Depends(get_session)): return scenario_compute.read_request(db, request_id)

@router.post("/requests/{request_id}/attempts", dependencies=[Depends(require_write)])
def attempt(request_id: str, payload: DataCreate, db: Session = Depends(get_session)):
    try: return scenario_compute.add_attempt(db, request_id, payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/requests/{request_id}/bind-run", dependencies=[Depends(require_write)])
def bind_run(request_id: str, payload: BindRunRequest, db: Session = Depends(get_session)):
    try: return scenario_compute.bind_model_run(db, request_id, payload.model_run_entity_id)
    except Exception as exc: raise bad(exc)

@router.post("/requests/{request_id}/results", dependencies=[Depends(require_write)])
def bind_result(request_id: str, payload: DataCreate, db: Session = Depends(get_session)):
    try: return scenario_compute.bind_result(db, request_id, payload.data)
    except Exception as exc: raise bad(exc)

@public_router.get("/readiness", response_model=PublicEnvelope)
def public_readiness(request: Request, db: Session = Depends(get_session), _ctx: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request); data = scenario_compute.readiness(db); data.update({"release": request.app.state.settings.version, "enabled": request.app.state.settings.scenario_compute_engine_enabled})
    return PublicEnvelope(data=data, meta={"api_version": "v1", "request_id": request.state.request_id})

@public_router.get("/plans", response_model=PublicEnvelope)
def public_plans(request: Request, limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), ctx: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    public_enabled(request); limit = min(limit, ctx.plan.max_page_size, request.app.state.settings.page_size_max); items, total = scenario_compute.list_plans(db, public_only=True, limit=limit, offset=offset)
    return PublicEnvelope(data=items, meta={"api_version": "v1", "request_id": request.state.request_id, "pagination": {"total": total, "limit": limit, "offset": offset}})

@public_router.get("/plans/{plan_id}", response_model=PublicEnvelope)
def public_plan(plan_id: str, request: Request, db: Session = Depends(get_session), _ctx: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request); return PublicEnvelope(data=scenario_compute.read_plan(db, plan_id, public_only=True), meta={"api_version": "v1", "request_id": request.state.request_id})

@public_router.get("/plans/{plan_id}/bundle", response_model=PublicEnvelope)
def public_bundle(plan_id: str, request: Request, db: Session = Depends(get_session), _ctx: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request); return PublicEnvelope(data=scenario_compute.bundle(db, plan_id, public_only=True), meta={"api_version": "v1", "request_id": request.state.request_id})
