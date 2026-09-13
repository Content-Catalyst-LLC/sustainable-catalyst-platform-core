from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_visual_explanations as rve

router = APIRouter(prefix="/v1/research-visual-explanations", tags=["Research Librarian Visual Explanation"])
public_router = APIRouter(prefix="/api/v1/research-visual-explanations", tags=["Public Research Librarian Visual Explanation"])


class Payload(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


def bad(exc):
    return exc if isinstance(exc, HTTPException) else HTTPException(status_code=422, detail=str(exc))


def enabled(request: Request):
    if not request.app.state.settings.research_librarian_visual_explanation_enabled:
        raise HTTPException(status_code=404, detail="Research Librarian Visual Explanation is disabled.")


def public_enabled(request: Request):
    enabled(request)
    if not request.app.state.settings.research_librarian_visual_explanation_public_metadata_enabled:
        raise HTTPException(status_code=404, detail="Public research visual explanation metadata is disabled.")


@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    enabled(request); data = rve.readiness(db); data.update({"release": request.app.state.settings.version, "enabled": True}); return data


@router.post("", dependencies=[Depends(require_write)])
def create(request: Request, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return rve.create_explanation(db, payload.data)
    except Exception as exc: raise bad(exc)


@router.get("", dependencies=[Depends(require_read)])
def explanations(
    request: Request, project_entity_id: str | None = None, explanation_kind: str | None = None,
    limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), db: Session = Depends(get_session),
):
    enabled(request); items, total = rve.list_explanations(db, project_entity_id=project_entity_id, explanation_kind=explanation_kind, limit=limit, offset=offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{explanation_id}", dependencies=[Depends(require_read)])
def explanation(request: Request, explanation_id: str, db: Session = Depends(get_session)):
    enabled(request); return rve.read_explanation(db, explanation_id)


@router.get("/{explanation_id}/bundle", dependencies=[Depends(require_read)])
def bundle(request: Request, explanation_id: str, db: Session = Depends(get_session)):
    enabled(request); return rve.bundle(db, explanation_id)


@router.post("/{explanation_id}/nodes", dependencies=[Depends(require_write)])
def node(request: Request, explanation_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return rve.add_node(db, explanation_id, payload.data)
    except Exception as exc: raise bad(exc)


@router.post("/{explanation_id}/relations", dependencies=[Depends(require_write)])
def relation(request: Request, explanation_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return rve.add_relation(db, explanation_id, payload.data)
    except Exception as exc: raise bad(exc)


@router.post("/{explanation_id}/citations", dependencies=[Depends(require_write)])
def citation(request: Request, explanation_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return rve.add_citation(db, explanation_id, payload.data)
    except Exception as exc: raise bad(exc)


@router.post("/{explanation_id}/views", dependencies=[Depends(require_write)])
def view(request: Request, explanation_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return rve.add_view(db, explanation_id, payload.data)
    except Exception as exc: raise bad(exc)


@router.get("/{explanation_id}/citation-coverage", dependencies=[Depends(require_read)])
def citation_coverage(request: Request, explanation_id: str, db: Session = Depends(get_session)):
    enabled(request); return rve.citation_coverage(db, explanation_id)


@router.get("/{explanation_id}/visualization", dependencies=[Depends(require_read)])
def visualization(request: Request, explanation_id: str, view_id: str | None = None, db: Session = Depends(get_session)):
    enabled(request)
    try: return rve.visualization_spec(db, explanation_id, view_id)
    except Exception as exc: raise bad(exc)


@router.post("/{explanation_id}/snapshots", dependencies=[Depends(require_write)])
def snapshot(request: Request, explanation_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return rve.create_snapshot(db, explanation_id, payload.data)
    except Exception as exc: raise bad(exc)


@router.post("/{explanation_id}/runtime-handoff", dependencies=[Depends(require_write)])
def handoff(request: Request, explanation_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return rve.runtime_handoff(db, explanation_id, payload.data)
    except Exception as exc: raise bad(exc)


@public_router.get("/readiness", response_model=PublicEnvelope)
def public_readiness(request: Request, db: Session = Depends(get_session), _ctx: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request); data = rve.readiness(db); data.update({"release": request.app.state.settings.version, "enabled": True}); return PublicEnvelope(data=data, meta={"api_version": "v1", "request_id": request.state.request_id})


@public_router.get("", response_model=PublicEnvelope)
def public_explanations(
    request: Request, project_entity_id: str | None = None, explanation_kind: str | None = None,
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0),
    ctx: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session),
):
    public_enabled(request); limit = min(limit, ctx.plan.max_page_size, request.app.state.settings.page_size_max)
    items, total = rve.list_explanations(db, project_entity_id=project_entity_id, explanation_kind=explanation_kind, public_only=True, limit=limit, offset=offset)
    return PublicEnvelope(data=items, meta={"api_version": "v1", "request_id": request.state.request_id, "pagination": {"total": total, "limit": limit, "offset": offset}})


@public_router.get("/{explanation_id}/bundle", response_model=PublicEnvelope)
def public_bundle(explanation_id: str, request: Request, db: Session = Depends(get_session), _ctx: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request); return PublicEnvelope(data=rve.bundle(db, explanation_id, public_only=True), meta={"api_version": "v1", "request_id": request.state.request_id})
