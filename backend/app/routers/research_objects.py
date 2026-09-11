from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_objects

router = APIRouter(prefix="/v1/research-objects", tags=["Research Object & Model Foundation"])
public_router = APIRouter(prefix="/api/v1/research-objects", tags=["Unified Public API — Research Objects"])


class ResearchObjectCreate(BaseModel):
    object_type: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=300)
    slug: str | None = Field(default=None, max_length=200)
    description: str | None = None
    entity_id: str | None = Field(default=None, max_length=255)
    visibility: str = Field(default="public", max_length=30)
    status: str = Field(default="active", max_length=50)
    attributes: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


def bad(exc: Exception) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    return HTTPException(status_code=422, detail=str(exc))


def require_public_metadata_enabled(request: Request) -> None:
    if not request.app.state.settings.research_object_public_metadata_enabled:
        raise HTTPException(status_code=404, detail="Research object public metadata API is disabled.")


@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    data = research_objects.readiness(db)
    migrations = migration_status(request.app.state.database)
    data.update({
        "release": request.app.state.settings.version,
        "enabled": request.app.state.settings.research_object_model_enabled,
        "migration_0031_applied": "0031" in migrations["applied"],
        "universal_entity_registry_integrated": True,
        "knowledge_graph_integrated": True,
        "evidence_and_provenance_inherited": True,
    })
    return data


@router.post("", dependencies=[Depends(require_write)])
def create(payload: ResearchObjectCreate, request: Request, db: Session = Depends(get_session)):
    if not request.app.state.settings.research_object_model_enabled:
        raise HTTPException(status_code=503, detail="Research Object & Model Foundation is disabled.")
    try:
        return research_objects.create_object(
            db,
            object_type=payload.object_type,
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            entity_id=payload.entity_id,
            visibility=payload.visibility,
            entity_status=payload.status,
            attributes=payload.attributes,
            metadata=payload.metadata,
            release=request.app.state.settings.version,
        )
    except Exception as exc:
        raise bad(exc)


@router.get("", dependencies=[Depends(require_read)])
def list_all(
    request: Request,
    object_type: str | None = None,
    project_entity_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    limit = min(limit, request.app.state.settings.page_size_max)
    try:
        items, total = research_objects.list_objects(
            db,
            object_type=object_type,
            project_entity_id=project_entity_id,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        raise bad(exc)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/projects/{project_entity_id}/bundle", dependencies=[Depends(require_read)])
def project_bundle(project_entity_id: str, db: Session = Depends(get_session)):
    try:
        return research_objects.project_bundle(db, project_entity_id)
    except Exception as exc:
        raise bad(exc)


@router.get("/{entity_id:path}", dependencies=[Depends(require_read)])
def detail(entity_id: str, db: Session = Depends(get_session)):
    return research_objects.object_read(db, entity_id)


@public_router.get("/readiness", response_model=PublicEnvelope)
def public_readiness(
    request: Request,
    db: Session = Depends(get_session),
    _context: PublicApiContext = Depends(require_public_scope("data:read")),
):
    require_public_metadata_enabled(request)
    data = research_objects.readiness(db)
    safe = {
        "enabled": request.app.state.settings.research_object_model_enabled,
        "object_types": data["object_types"],
        "counts": data["counts"],
        "graph_native": True,
        "model_execution_by_core": False,
        "model_execution_targets": data["model_execution_targets"],
        "automatic_truth_promotion": False,
        "release": request.app.state.settings.version,
    }
    return PublicEnvelope(data=safe, meta={"api_version": "v1", "request_id": request.state.request_id})


@public_router.get("", response_model=PublicEnvelope)
def public_list(
    request: Request,
    object_type: str | None = None,
    project_entity_id: str | None = None,
    limit: int = Query(default=100, ge=1),
    offset: int = Query(default=0, ge=0),
    context: PublicApiContext = Depends(require_public_scope("data:read")),
    db: Session = Depends(get_session),
):
    require_public_metadata_enabled(request)
    limit = min(limit, context.plan.max_page_size, request.app.state.settings.page_size_max)
    try:
        items, total = research_objects.list_objects(
            db,
            object_type=object_type,
            project_entity_id=project_entity_id,
            public_only=True,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        raise bad(exc)
    return PublicEnvelope(
        data=items,
        meta={
            "api_version": "v1",
            "request_id": request.state.request_id,
            "pagination": {"total": total, "limit": limit, "offset": offset},
        },
    )


@public_router.get("/projects/{project_entity_id}/bundle", response_model=PublicEnvelope)
def public_project_bundle(
    project_entity_id: str,
    request: Request,
    db: Session = Depends(get_session),
    _context: PublicApiContext = Depends(require_public_scope("data:read")),
):
    require_public_metadata_enabled(request)
    try:
        bundle = research_objects.project_bundle(db, project_entity_id, public_only=True)
    except Exception as exc:
        raise bad(exc)
    return PublicEnvelope(data=bundle, meta={"api_version": "v1", "request_id": request.state.request_id})


@public_router.get("/{entity_id:path}", response_model=PublicEnvelope)
def public_detail(
    entity_id: str,
    request: Request,
    db: Session = Depends(get_session),
    _context: PublicApiContext = Depends(require_public_scope("data:read")),
):
    require_public_metadata_enabled(request)
    return PublicEnvelope(
        data=research_objects.object_read(db, entity_id, public_only=True),
        meta={"api_version": "v1", "request_id": request.state.request_id},
    )
