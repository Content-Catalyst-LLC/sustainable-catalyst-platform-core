from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import cross_product_visual_research as cpvr

router = APIRouter(prefix="/v1/cross-product-visual-research", tags=["Cross-Product Visual Research Objects"])
public_router = APIRouter(prefix="/api/v1/cross-product-visual-research", tags=["Public Cross-Product Visual Research Objects"])


class Payload(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


def bad(exc):
    return exc if isinstance(exc, HTTPException) else HTTPException(status_code=422, detail=str(exc))


def enabled(request: Request):
    if not request.app.state.settings.cross_product_visual_research_enabled:
        raise HTTPException(status_code=404, detail="Cross-Product Visual Research Objects is disabled.")


def public_enabled(request: Request):
    enabled(request)
    if not request.app.state.settings.cross_product_visual_research_public_metadata_enabled:
        raise HTTPException(status_code=404, detail="Public cross-product visual research metadata is disabled.")


@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    enabled(request); data = cpvr.readiness(db); data.update({"release": request.app.state.settings.version, "enabled": True}); return data


@router.post("", dependencies=[Depends(require_write)])
def create(request: Request, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return cpvr.create_object(db, payload.data)
    except Exception as exc: raise bad(exc)


@router.get("", dependencies=[Depends(require_read)])
def objects(request: Request, project_entity_id: str | None = None, object_kind: str | None = None, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), db: Session = Depends(get_session)):
    enabled(request); items, total = cpvr.list_objects(db, project_entity_id=project_entity_id, object_kind=object_kind, limit=limit, offset=offset); return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{object_id}/bundle", dependencies=[Depends(require_read)])
def bundle(request: Request, object_id: str, db: Session = Depends(get_session)):
    enabled(request); return cpvr.bundle(db, object_id)


@router.get("/{object_id}/validate", dependencies=[Depends(require_read)])
def validate(request: Request, object_id: str, db: Session = Depends(get_session)):
    enabled(request); return cpvr.validate_object(db, object_id)


@router.post("/{object_id}/members", dependencies=[Depends(require_write)])
def member(request: Request, object_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return cpvr.add_member(db, object_id, payload.data)
    except Exception as exc: raise bad(exc)


@router.post("/{object_id}/relations", dependencies=[Depends(require_write)])
def relation(request: Request, object_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return cpvr.add_relation(db, object_id, payload.data)
    except Exception as exc: raise bad(exc)


@router.post("/{object_id}/views", dependencies=[Depends(require_write)])
def view(request: Request, object_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return cpvr.add_view(db, object_id, payload.data)
    except Exception as exc: raise bad(exc)


@router.get("/{object_id}/visualization", dependencies=[Depends(require_read)])
def visualization(request: Request, object_id: str, view_id: str | None = None, db: Session = Depends(get_session)):
    enabled(request)
    try: return cpvr.visualization_spec(db, object_id, view_id)
    except Exception as exc: raise bad(exc)


@router.post("/{object_id}/snapshots", dependencies=[Depends(require_write)])
def snapshot(request: Request, object_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return cpvr.create_snapshot(db, object_id, payload.data)
    except Exception as exc: raise bad(exc)


@router.get("/{object_id}/portable-package", dependencies=[Depends(require_read)])
def portable_package(request: Request, object_id: str, db: Session = Depends(get_session)):
    enabled(request); return cpvr.portability_package(db, object_id)


@router.post("/{object_id}/runtime-handoff", dependencies=[Depends(require_write)])
def runtime_handoff(request: Request, object_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return cpvr.runtime_handoff(db, object_id, payload.data)
    except Exception as exc: raise bad(exc)


@public_router.get("/readiness", response_model=PublicEnvelope)
def public_readiness(request: Request, db: Session = Depends(get_session), _ctx: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request); data = cpvr.readiness(db); data.update({"release": request.app.state.settings.version, "enabled": True}); return PublicEnvelope(data=data, meta={"api_version": "v1", "request_id": request.state.request_id})


@public_router.get("", response_model=PublicEnvelope)
def public_objects(request: Request, project_entity_id: str | None = None, object_kind: str | None = None, limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), ctx: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    public_enabled(request); limit = min(limit, ctx.plan.max_page_size, request.app.state.settings.page_size_max); items, total = cpvr.list_objects(db, project_entity_id=project_entity_id, object_kind=object_kind, public_only=True, limit=limit, offset=offset); return PublicEnvelope(data=items, meta={"api_version": "v1", "request_id": request.state.request_id, "pagination": {"total": total, "limit": limit, "offset": offset}})


@public_router.get("/{object_id}/bundle", response_model=PublicEnvelope)
def public_bundle(object_id: str, request: Request, db: Session = Depends(get_session), _ctx: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request); return PublicEnvelope(data=cpvr.bundle(db, object_id, public_only=True), meta={"api_version": "v1", "request_id": request.state.request_id})
