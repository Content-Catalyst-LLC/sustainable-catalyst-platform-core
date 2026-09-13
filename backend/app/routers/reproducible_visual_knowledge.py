from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import reproducible_visual_knowledge as rvk

router = APIRouter(prefix="/v1/reproducible-visual-knowledge", tags=["Reproducible Visual Knowledge Layer"])
public_router = APIRouter(prefix="/api/v1/reproducible-visual-knowledge", tags=["Public Reproducible Visual Knowledge Layer"])

class Payload(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)

def bad(exc):
    return exc if isinstance(exc, HTTPException) else HTTPException(status_code=422, detail=str(exc))

def enabled(request: Request):
    if not request.app.state.settings.reproducible_visual_knowledge_enabled:
        raise HTTPException(status_code=404, detail="Reproducible Visual Knowledge Layer is disabled.")

def public_enabled(request: Request):
    enabled(request)
    if not request.app.state.settings.reproducible_visual_knowledge_public_metadata_enabled:
        raise HTTPException(status_code=404, detail="Public reproducible visual knowledge metadata is disabled.")

@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    enabled(request); data=rvk.readiness(db); data.update({"release": request.app.state.settings.version, "enabled": True}); return data

@router.post("", dependencies=[Depends(require_write)])
def create(request: Request, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return rvk.create_package(db, payload.data)
    except Exception as exc: raise bad(exc)

@router.get("", dependencies=[Depends(require_read)])
def packages(request: Request, project_entity_id: str | None = None, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), db: Session = Depends(get_session)):
    enabled(request); items,total=rvk.list_packages(db, project_entity_id=project_entity_id, limit=limit, offset=offset); return {"items":items,"total":total,"limit":limit,"offset":offset}

@router.get("/{package_id}/bundle", dependencies=[Depends(require_read)])
def bundle(request: Request, package_id: str, db: Session = Depends(get_session)):
    enabled(request); return rvk.bundle(db, package_id)

@router.get("/{package_id}/manifest", dependencies=[Depends(require_read)])
def manifest(request: Request, package_id: str, db: Session = Depends(get_session)):
    enabled(request); return rvk.manifest(db, package_id)

@router.get("/{package_id}/validate", dependencies=[Depends(require_read)])
def validate(request: Request, package_id: str, db: Session = Depends(get_session)):
    enabled(request); return rvk.validate_package(db, package_id)

@router.post("/{package_id}/inputs", dependencies=[Depends(require_write)])
def add_input(request: Request, package_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return rvk.add_input(db, package_id, payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/{package_id}/environments", dependencies=[Depends(require_write)])
def add_environment(request: Request, package_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return rvk.add_environment(db, package_id, payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/{package_id}/replay-plans", dependencies=[Depends(require_write)])
def add_replay_plan(request: Request, package_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return rvk.add_replay_plan(db, package_id, payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/{package_id}/verifications", dependencies=[Depends(require_write)])
def verification(request: Request, package_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return rvk.record_verification(db, package_id, payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/{package_id}/snapshots", dependencies=[Depends(require_write)])
def snapshot(request: Request, package_id: str, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return rvk.create_snapshot(db, package_id, payload.data)
    except Exception as exc: raise bad(exc)

@router.get("/{package_id}/portable-package", dependencies=[Depends(require_read)])
def portable(request: Request, package_id: str, db: Session = Depends(get_session)):
    enabled(request); return rvk.portable_package(db, package_id)

@public_router.get("/readiness", response_model=PublicEnvelope)
def public_readiness(request: Request, db: Session = Depends(get_session), _ctx: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request); data=rvk.readiness(db); data.update({"release":request.app.state.settings.version,"enabled":True}); return PublicEnvelope(data=data, meta={"api_version":"v1","request_id":request.state.request_id})

@public_router.get("", response_model=PublicEnvelope)
def public_packages(request: Request, project_entity_id: str | None = None, limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), ctx: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    public_enabled(request); limit=min(limit,ctx.plan.max_page_size,request.app.state.settings.page_size_max); items,total=rvk.list_packages(db,project_entity_id=project_entity_id,public_only=True,limit=limit,offset=offset); return PublicEnvelope(data=items,meta={"api_version":"v1","request_id":request.state.request_id,"pagination":{"total":total,"limit":limit,"offset":offset}})

@public_router.get("/{package_id}/bundle", response_model=PublicEnvelope)
def public_bundle(package_id: str, request: Request, db: Session = Depends(get_session), _ctx: PublicApiContext = Depends(require_public_scope("data:read"))):
    public_enabled(request); return PublicEnvelope(data=rvk.bundle(db, package_id, public_only=True),meta={"api_version":"v1","request_id":request.state.request_id})
