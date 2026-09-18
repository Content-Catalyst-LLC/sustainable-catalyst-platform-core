from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import cross_product_visual_runtime_integration as svc

router = APIRouter(prefix="/v1/visual-runtime/integrations", tags=["Cross-Product Visual Runtime Integration"])
public_router = APIRouter(prefix="/api/v1/visual-runtime/integrations", tags=["Unified Public API — Visual Runtime Integration"])

class Payload(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)

def enabled(request: Request):
    if not request.app.state.settings.cross_product_visual_runtime_integration_enabled:
        raise HTTPException(503, "Cross-Product Visual Runtime Integration is disabled.")

def call(fn, *args):
    try: return fn(*args)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc

@router.get("/readiness", dependencies=[Depends(require_read)])
def ready(request: Request, db: Session = Depends(get_session)):
    enabled(request); out = svc.readiness(db); out["migration_0075_applied"] = "0075" in migration_status(request.app.state.database)["applied"]; return out

@router.post("/workspaces/{workspace_id}/products", dependencies=[Depends(require_write)])
def create_product_integration(workspace_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request); return call(svc.create_integration, db, workspace_id, payload.data)

@router.post("/integrations/{integration_id}/object-bindings", dependencies=[Depends(require_write)])
def create_object_binding(integration_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request); return call(svc.object_binding, db, integration_id, payload.data)

@router.post("/integrations/{integration_id}/context-bindings", dependencies=[Depends(require_write)])
def create_context_binding(integration_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request); return call(svc.context_binding, db, integration_id, payload.data)

@router.post("/integrations/{integration_id}/capabilities", dependencies=[Depends(require_write)])
def create_capability_binding(integration_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request); return call(svc.capability_binding, db, integration_id, payload.data)

@router.post("/integrations/{integration_id}/view-bindings", dependencies=[Depends(require_write)])
def create_view_binding(integration_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request); return call(svc.view_binding, db, integration_id, payload.data)

@router.post("/workspaces/{workspace_id}/handoff-routes", dependencies=[Depends(require_write)])
def create_handoff_route(workspace_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request); return call(svc.handoff_route, db, workspace_id, payload.data)

@router.post("/workspaces/{workspace_id}/sync-records", dependencies=[Depends(require_write)])
def create_sync_record(workspace_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request); return call(svc.sync_record, db, workspace_id, payload.data)

@router.get("/workspaces/{workspace_id}/bundle", dependencies=[Depends(require_read)])
def get_bundle(workspace_id: str, request: Request, db: Session = Depends(get_session)):
    enabled(request); return call(svc.bundle, db, workspace_id)

@router.post("/workspaces/{workspace_id}/snapshots", dependencies=[Depends(require_write)])
def create_snapshot(workspace_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request); return call(svc.snapshot, db, workspace_id, payload.data)

@public_router.get("/workspaces/{workspace_id}/bundle", response_model=PublicEnvelope)
def public_bundle(workspace_id: str, request: Request, db: Session = Depends(get_session), ctx: PublicApiContext = Depends(require_public_scope("read:visual"))):
    enabled(request); return PublicEnvelope(data=call(svc.bundle, db, workspace_id, True), meta={"release": "2.71.0", "contract": svc.CONTRACT})
