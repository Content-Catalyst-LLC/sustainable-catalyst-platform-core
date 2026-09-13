from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import flow_maps

router = APIRouter(prefix="/v1/flow-maps", tags=["Flow Maps"])
public_router = APIRouter(prefix="/api/v1/flow-maps", tags=["Unified Public API — Flow Maps"])


class FlowMapCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    slug: str | None = None
    description: str | None = None
    entity_id: str | None = None
    visibility: str = "public"
    status: str = "active"
    reasoning_purpose: str = "explain"
    flow_purpose: str = "trace"
    flow_domain: str = "generic"
    map_state: str = "draft"
    quantity_mode: str = "mixed"
    default_unit: str | None = None
    time_basis: str = "unspecified"
    conservation_policy: str = "advisory"
    coordinate_space: str = "abstract"
    project_entity_id: str | None = None
    primary_subject_entity_id: str | None = None
    lens: dict[str, Any] = Field(default_factory=dict)
    filters: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[Any] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str = "operator"


class ChildCreate(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


class CompileSpec(BaseModel):
    spec_key: str = "flow-map-default"
    revision: int | None = None
    spec_kind: str = "network"
    title: str | None = None
    preferred_renderer_key: str | None = None
    renderer_policy: str = "compatible"
    layout_constraints: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str = "operator"


def bad(exc: Exception):
    if isinstance(exc, HTTPException):
        return exc
    return HTTPException(status_code=422, detail=str(exc))


def public_enabled(request: Request):
    if not request.app.state.settings.flow_maps_public_metadata_enabled:
        raise HTTPException(status_code=404, detail="Flow Maps public metadata API is disabled.")


@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    data = flow_maps.readiness(db)
    migrations = migration_status(request.app.state.database)
    data.update({
        "release": request.app.state.settings.version,
        "enabled": request.app.state.settings.flow_maps_enabled,
        "migration_0035_applied": "0035" in migrations["applied"],
    })
    return data


@router.post("", dependencies=[Depends(require_write)])
def create(payload: FlowMapCreate, request: Request, db: Session = Depends(get_session)):
    if not request.app.state.settings.flow_maps_enabled:
        raise HTTPException(status_code=503, detail="Flow Maps are disabled.")
    try:
        return flow_maps.create_map(db, payload.model_dump(), release=request.app.state.settings.version)
    except Exception as exc:
        raise bad(exc)


@router.get("", dependencies=[Depends(require_read)])
def list_all(request: Request, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), db: Session = Depends(get_session)):
    items, total = flow_maps.list_maps(db, limit=min(limit, request.app.state.settings.page_size_max), offset=offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{visual_entity_id}", dependencies=[Depends(require_read)])
def detail(visual_entity_id: str, db: Session = Depends(get_session)):
    return flow_maps.read_map(db, visual_entity_id)


@router.get("/{visual_entity_id}/bundle", dependencies=[Depends(require_read)])
def bundle(visual_entity_id: str, db: Session = Depends(get_session)):
    return flow_maps.bundle(db, visual_entity_id)


@router.get("/{visual_entity_id}/validate", dependencies=[Depends(require_read)])
def validate(visual_entity_id: str, db: Session = Depends(get_session)):
    return flow_maps.validate_structure(db, visual_entity_id)


@router.get("/{visual_entity_id}/balance", dependencies=[Depends(require_read)])
def balance(visual_entity_id: str, db: Session = Depends(get_session)):
    return flow_maps.balance_summary(db, visual_entity_id)


@router.post("/{visual_entity_id}/channels", dependencies=[Depends(require_write)])
def channel(visual_entity_id: str, payload: ChildCreate, db: Session = Depends(get_session)):
    try:
        return flow_maps.add_channel(db, visual_entity_id, payload.data)
    except Exception as exc:
        raise bad(exc)


@router.post("/{visual_entity_id}/flows", dependencies=[Depends(require_write)])
def flow(visual_entity_id: str, payload: ChildCreate, db: Session = Depends(get_session)):
    try:
        return flow_maps.add_flow(db, visual_entity_id, payload.data)
    except Exception as exc:
        raise bad(exc)


@router.post("/{visual_entity_id}/node-states", dependencies=[Depends(require_write)])
def node_state(visual_entity_id: str, payload: ChildCreate, db: Session = Depends(get_session)):
    try:
        return flow_maps.add_node_state(db, visual_entity_id, payload.data)
    except Exception as exc:
        raise bad(exc)


@router.post("/{visual_entity_id}/views", dependencies=[Depends(require_write)])
def view(visual_entity_id: str, payload: ChildCreate, db: Session = Depends(get_session)):
    try:
        return flow_maps.add_view(db, visual_entity_id, payload.data)
    except Exception as exc:
        raise bad(exc)


@router.post("/{visual_entity_id}/compile-specification", dependencies=[Depends(require_write)])
def compile_spec(visual_entity_id: str, payload: CompileSpec, db: Session = Depends(get_session)):
    try:
        return flow_maps.compile_specification(db, visual_entity_id, payload.model_dump())
    except Exception as exc:
        raise bad(exc)


@public_router.get("/readiness", response_model=PublicEnvelope)
def public_readiness(request: Request, db: Session = Depends(get_session), _ctx: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request)
    data = flow_maps.readiness(db)
    data.update({"release": request.app.state.settings.version, "enabled": request.app.state.settings.flow_maps_enabled})
    return PublicEnvelope(data=data, meta={"api_version": "v1", "request_id": request.state.request_id})


@public_router.get("", response_model=PublicEnvelope)
def public_list(request: Request, limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), ctx: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    public_enabled(request)
    limit = min(limit, ctx.plan.max_page_size, request.app.state.settings.page_size_max)
    items, total = flow_maps.list_maps(db, public_only=True, limit=limit, offset=offset)
    return PublicEnvelope(data=items, meta={"api_version": "v1", "request_id": request.state.request_id, "pagination": {"total": total, "limit": limit, "offset": offset}})


@public_router.get("/{visual_entity_id}/bundle", response_model=PublicEnvelope)
def public_bundle(visual_entity_id: str, request: Request, db: Session = Depends(get_session), _ctx: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request)
    return PublicEnvelope(data=flow_maps.bundle(db, visual_entity_id, public_only=True), meta={"api_version": "v1", "request_id": request.state.request_id})


@public_router.get("/{visual_entity_id}/balance", response_model=PublicEnvelope)
def public_balance(visual_entity_id: str, request: Request, db: Session = Depends(get_session), _ctx: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request)
    return PublicEnvelope(data=flow_maps.balance_summary(db, visual_entity_id, public_only=True), meta={"api_version": "v1", "request_id": request.state.request_id})


@public_router.get("/{visual_entity_id}", response_model=PublicEnvelope)
def public_detail(visual_entity_id: str, request: Request, db: Session = Depends(get_session), _ctx: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request)
    return PublicEnvelope(data=flow_maps.read_map(db, visual_entity_id, public_only=True), meta={"api_version": "v1", "request_id": request.state.request_id})
