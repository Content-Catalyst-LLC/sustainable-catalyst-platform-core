from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import visualization_registry

router = APIRouter(prefix="/v1/visualization", tags=["Visualization Specification & Renderer Registry"])
public_router = APIRouter(prefix="/api/v1/visualization", tags=["Unified Public API — Visualization Registry"])


class SpecificationCreate(BaseModel):
    visual_entity_id: str = Field(min_length=1, max_length=255)
    spec_key: str = Field(default="default", min_length=1, max_length=180)
    revision: int = Field(default=1, ge=1)
    spec_version: str = Field(default="1.0", max_length=30)
    spec_kind: str = Field(default="generic", max_length=80)
    title: str | None = Field(default=None, max_length=300)
    preferred_renderer_key: str | None = Field(default=None, max_length=180)
    renderer_policy: str = Field(default="compatible", max_length=50)
    encoding: dict[str, Any] = Field(default_factory=dict)
    interaction: dict[str, Any] = Field(default_factory=dict)
    accessibility: dict[str, Any] = Field(default_factory=dict)
    layout_constraints: dict[str, Any] = Field(default_factory=dict)
    export: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str = Field(default="operator", max_length=255)


class RendererCreate(BaseModel):
    renderer_key: str = Field(min_length=1, max_length=180)
    name: str = Field(min_length=1, max_length=300)
    description: str | None = None
    renderer_family: str = Field(default="custom", max_length=100)
    runtime: str = Field(default="external-runtime", max_length=80)
    execution_mode: str = Field(default="external-runtime", max_length=80)
    enabled: bool = True
    executable_by_core: bool = False
    public_summary: bool = True
    supported_spec_versions: list[str] = Field(default_factory=lambda: ["1.0"])
    capabilities: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RendererVersionCreate(BaseModel):
    version: str = Field(min_length=1, max_length=80)
    status: str = Field(default="active", max_length=50)
    contract_version: str = Field(default="1.0", max_length=30)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompatibilityRuleCreate(BaseModel):
    visual_kind: str = Field(default="*", max_length=80)
    spec_kind: str = Field(default="generic", max_length=80)
    priority: int = 100
    required_capabilities: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResolveRequest(BaseModel):
    requested_renderer_key: str | None = Field(default=None, max_length=180)
    created_by: str = Field(default="operator", max_length=255)


def bad(exc: Exception) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    return HTTPException(status_code=422, detail=str(exc))


def public_enabled(request: Request) -> None:
    if not request.app.state.settings.visualization_spec_public_metadata_enabled:
        raise HTTPException(status_code=404, detail="Visualization registry public metadata API is disabled.")


@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    data = visualization_registry.readiness(db)
    migrations = migration_status(request.app.state.database)
    data.update({
        "release": request.app.state.settings.version,
        "enabled": request.app.state.settings.visualization_renderer_registry_enabled,
        "migration_0033_applied": "0033" in migrations["applied"],
        "visual_reasoning_object_model_integrated": True,
        "renderer_contracts_are_non_executing": True,
    })
    return data


@router.post("/specifications", dependencies=[Depends(require_write)])
def create_spec(payload: SpecificationCreate, request: Request, db: Session = Depends(get_session)):
    if not request.app.state.settings.visualization_renderer_registry_enabled:
        raise HTTPException(status_code=503, detail="Visualization Specification & Renderer Registry is disabled.")
    try:
        return visualization_registry.create_specification(db, payload.model_dump())
    except Exception as exc:
        raise bad(exc)


@router.get("/specifications", dependencies=[Depends(require_read)])
def list_specs(visual_entity_id: str | None = None, limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), db: Session = Depends(get_session)):
    items, total = visualization_registry.list_specifications(db, visual_entity_id=visual_entity_id, limit=limit, offset=offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/specifications/{specification_id}", dependencies=[Depends(require_read)])
def spec_detail(specification_id: str, db: Session = Depends(get_session)):
    return visualization_registry.specification_read(db, specification_id)


@router.post("/specifications/{specification_id}/resolve", dependencies=[Depends(require_write)])
def resolve(specification_id: str, payload: ResolveRequest, db: Session = Depends(get_session)):
    try:
        return visualization_registry.resolve_renderer(db, specification_id, requested_renderer_key=payload.requested_renderer_key, created_by=payload.created_by)
    except Exception as exc:
        raise bad(exc)


@router.get("/renderers", dependencies=[Depends(require_read)])
def renderers(db: Session = Depends(get_session)):
    return {"items": visualization_registry.list_renderers(db), "total": len(visualization_registry.list_renderers(db))}


@router.get("/renderers/{renderer_key}", dependencies=[Depends(require_read)])
def renderer_detail(renderer_key: str, db: Session = Depends(get_session)):
    return visualization_registry.renderer_read(db, renderer_key)


@router.post("/renderers", dependencies=[Depends(require_write)])
def register_renderer(payload: RendererCreate, request: Request, db: Session = Depends(get_session)):
    if not request.app.state.settings.visualization_renderer_registry_enabled:
        raise HTTPException(status_code=503, detail="Visualization Specification & Renderer Registry is disabled.")
    try:
        return visualization_registry.register_renderer(db, payload.model_dump())
    except Exception as exc:
        raise bad(exc)


@router.post("/renderers/{renderer_key}/versions", dependencies=[Depends(require_write)])
def register_renderer_version(renderer_key: str, payload: RendererVersionCreate, db: Session = Depends(get_session)):
    try:
        return visualization_registry.register_renderer_version(db, renderer_key, payload.model_dump())
    except Exception as exc:
        raise bad(exc)


@router.post("/renderers/{renderer_key}/compatibility-rules", dependencies=[Depends(require_write)])
def register_compatibility_rule(renderer_key: str, payload: CompatibilityRuleCreate, db: Session = Depends(get_session)):
    try:
        return visualization_registry.register_compatibility_rule(db, renderer_key, payload.model_dump())
    except Exception as exc:
        raise bad(exc)


@router.get("/specifications/{specification_id}/resolutions", dependencies=[Depends(require_read)])
def resolution_history(specification_id: str, db: Session = Depends(get_session)):
    return {"items": visualization_registry.list_resolutions(db, specification_id)}


@public_router.get("/readiness", response_model=PublicEnvelope)
def public_readiness(request: Request, db: Session = Depends(get_session), _context: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request)
    data = visualization_registry.readiness(db)
    data.update({"enabled": request.app.state.settings.visualization_renderer_registry_enabled, "release": request.app.state.settings.version})
    return PublicEnvelope(data=data, meta={"api_version": "v1", "request_id": request.state.request_id})


@public_router.get("/renderers", response_model=PublicEnvelope)
def public_renderers(request: Request, db: Session = Depends(get_session), _context: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request)
    return PublicEnvelope(data=visualization_registry.list_renderers(db, public_only=True), meta={"api_version":"v1","request_id":request.state.request_id})


@public_router.get("/specifications", response_model=PublicEnvelope)
def public_specs(request: Request, visual_entity_id: str | None = None, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0), context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    public_enabled(request)
    limit = min(limit, context.plan.max_page_size, request.app.state.settings.page_size_max)
    items, total = visualization_registry.list_specifications(db, visual_entity_id=visual_entity_id, public_only=True, limit=limit, offset=offset)
    return PublicEnvelope(data=items, meta={"api_version":"v1","request_id":request.state.request_id,"pagination":{"total":total,"limit":limit,"offset":offset}})
