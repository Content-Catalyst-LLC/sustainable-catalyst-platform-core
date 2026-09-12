from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import visual_reasoning

router = APIRouter(prefix="/v1/visual-reasoning", tags=["Visual Reasoning Object Model"])
public_router = APIRouter(prefix="/api/v1/visual-reasoning", tags=["Unified Public API — Visual Reasoning"])


class VisualObjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    slug: str | None = Field(default=None, max_length=200)
    description: str | None = None
    entity_id: str | None = Field(default=None, max_length=255)
    visibility: str = Field(default="public", max_length=30)
    status: str = Field(default="active", max_length=50)
    visual_kind: str = Field(default="generic", max_length=80)
    reasoning_purpose: str = Field(default="explore", max_length=80)
    semantic_state: str = Field(default="draft", max_length=50)
    coordinate_space: str = Field(default="abstract", max_length=50)
    project_entity_id: str | None = Field(default=None, max_length=255)
    primary_subject_entity_id: str | None = Field(default=None, max_length=255)
    lens: dict[str, Any] = Field(default_factory=dict)
    filters: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[Any] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SemanticChildCreate(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


class SnapshotCreate(BaseModel):
    snapshot_key: str = Field(min_length=1, max_length=180)
    created_by: str = Field(default="operator", max_length=255)
    provenance: dict[str, Any] = Field(default_factory=dict)


def bad(exc: Exception) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    return HTTPException(status_code=422, detail=str(exc))


def require_public_metadata_enabled(request: Request) -> None:
    if not request.app.state.settings.visual_reasoning_public_metadata_enabled:
        raise HTTPException(status_code=404, detail="Visual reasoning public metadata API is disabled.")


@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    data = visual_reasoning.readiness(db)
    migrations = migration_status(request.app.state.database)
    data.update({
        "release": request.app.state.settings.version,
        "enabled": request.app.state.settings.visual_reasoning_object_model_enabled,
        "migration_0032_applied": "0032" in migrations["applied"],
        "universal_entity_registry_integrated": True,
        "research_object_model_integrated": True,
        "knowledge_graph_integrated": True,
        "evidence_and_provenance_inherited": True,
    })
    return data


@router.post("/objects", dependencies=[Depends(require_write)])
def create(payload: VisualObjectCreate, request: Request, db: Session = Depends(get_session)):
    if not request.app.state.settings.visual_reasoning_object_model_enabled:
        raise HTTPException(status_code=503, detail="Visual Reasoning Object Model is disabled.")
    try:
        return visual_reasoning.create_object(
            db,
            name=payload.name, slug=payload.slug, description=payload.description,
            entity_id=payload.entity_id, visibility=payload.visibility, entity_status=payload.status,
            visual_kind=payload.visual_kind, reasoning_purpose=payload.reasoning_purpose,
            semantic_state=payload.semantic_state, coordinate_space=payload.coordinate_space,
            project_entity_id=payload.project_entity_id, primary_subject_entity_id=payload.primary_subject_entity_id,
            lens=payload.lens, filters=payload.filters, assumptions=payload.assumptions,
            metadata=payload.metadata, release=request.app.state.settings.version,
        )
    except Exception as exc:
        raise bad(exc)


@router.get("/objects", dependencies=[Depends(require_read)])
def list_all(
    request: Request,
    visual_kind: str | None = None,
    project_entity_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    limit = min(limit, request.app.state.settings.page_size_max)
    try:
        items, total = visual_reasoning.list_objects(db, visual_kind=visual_kind, project_entity_id=project_entity_id, limit=limit, offset=offset)
    except Exception as exc:
        raise bad(exc)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/objects/{visual_entity_id}/elements", dependencies=[Depends(require_write)])
def add_element(visual_entity_id: str, payload: SemanticChildCreate, db: Session = Depends(get_session)):
    try: return visual_reasoning.add_element(db, visual_entity_id, payload.data)
    except Exception as exc: raise bad(exc)


@router.post("/objects/{visual_entity_id}/relations", dependencies=[Depends(require_write)])
def add_relation(visual_entity_id: str, payload: SemanticChildCreate, db: Session = Depends(get_session)):
    try: return visual_reasoning.add_relation(db, visual_entity_id, payload.data)
    except Exception as exc: raise bad(exc)


@router.post("/objects/{visual_entity_id}/layers", dependencies=[Depends(require_write)])
def add_layer(visual_entity_id: str, payload: SemanticChildCreate, db: Session = Depends(get_session)):
    try: return visual_reasoning.add_layer(db, visual_entity_id, payload.data)
    except Exception as exc: raise bad(exc)


@router.post("/objects/{visual_entity_id}/annotations", dependencies=[Depends(require_write)])
def add_annotation(visual_entity_id: str, payload: SemanticChildCreate, db: Session = Depends(get_session)):
    try: return visual_reasoning.add_annotation(db, visual_entity_id, payload.data)
    except Exception as exc: raise bad(exc)


@router.post("/objects/{visual_entity_id}/snapshots", dependencies=[Depends(require_write)])
def create_snapshot(visual_entity_id: str, payload: SnapshotCreate, db: Session = Depends(get_session)):
    try: return visual_reasoning.create_snapshot(db, visual_entity_id, snapshot_key=payload.snapshot_key, created_by=payload.created_by, provenance=payload.provenance)
    except Exception as exc: raise bad(exc)


@router.get("/objects/{visual_entity_id}/bundle", dependencies=[Depends(require_read)])
def get_bundle(visual_entity_id: str, db: Session = Depends(get_session)):
    return visual_reasoning.bundle(db, visual_entity_id)


@router.get("/objects/{visual_entity_id}", dependencies=[Depends(require_read)])
def detail(visual_entity_id: str, db: Session = Depends(get_session)):
    return visual_reasoning.object_read(db, visual_entity_id)


@public_router.get("/readiness", response_model=PublicEnvelope)
def public_readiness(
    request: Request,
    db: Session = Depends(get_session),
    _context: PublicApiContext = Depends(require_public_scope("data:read")),
):
    require_public_metadata_enabled(request)
    data = visual_reasoning.readiness(db)
    safe = {
        "enabled": request.app.state.settings.visual_reasoning_object_model_enabled,
        "visual_kinds": data["visual_kinds"],
        "reasoning_purposes": data["reasoning_purposes"],
        "counts": data["counts"],
        "graph_native": True,
        "renderer_neutral": True,
        "renderer_registry_in_core": True,
        "layout_engine_in_core": False,
        "automatic_truth_promotion": False,
        "release": request.app.state.settings.version,
    }
    return PublicEnvelope(data=safe, meta={"api_version": "v1", "request_id": request.state.request_id})


@public_router.get("/objects", response_model=PublicEnvelope)
def public_list(
    request: Request,
    visual_kind: str | None = None,
    project_entity_id: str | None = None,
    limit: int = Query(default=100, ge=1),
    offset: int = Query(default=0, ge=0),
    context: PublicApiContext = Depends(require_public_scope("data:read")),
    db: Session = Depends(get_session),
):
    require_public_metadata_enabled(request)
    limit = min(limit, context.plan.max_page_size, request.app.state.settings.page_size_max)
    try:
        items, total = visual_reasoning.list_objects(db, visual_kind=visual_kind, project_entity_id=project_entity_id, public_only=True, limit=limit, offset=offset)
    except Exception as exc:
        raise bad(exc)
    return PublicEnvelope(data=items, meta={"api_version":"v1","request_id":request.state.request_id,"pagination":{"total":total,"limit":limit,"offset":offset}})


@public_router.get("/objects/{visual_entity_id}/bundle", response_model=PublicEnvelope)
def public_bundle(
    visual_entity_id: str,
    request: Request,
    db: Session = Depends(get_session),
    _context: PublicApiContext = Depends(require_public_scope("data:read")),
):
    require_public_metadata_enabled(request)
    return PublicEnvelope(data=visual_reasoning.bundle(db, visual_entity_id, public_only=True), meta={"api_version":"v1","request_id":request.state.request_id})


@public_router.get("/objects/{visual_entity_id}", response_model=PublicEnvelope)
def public_detail(
    visual_entity_id: str,
    request: Request,
    db: Session = Depends(get_session),
    _context: PublicApiContext = Depends(require_public_scope("data:read")),
):
    require_public_metadata_enabled(request)
    return PublicEnvelope(data=visual_reasoning.object_read(db, visual_entity_id, public_only=True), meta={"api_version":"v1","request_id":request.state.request_id})
