from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import unified_visual_reasoning as svc
router=APIRouter(prefix="/v1/visual-runtime/unified",tags=["Unified Visual Reasoning Engine"])
public_router=APIRouter(prefix="/api/v1/visual-runtime/unified",tags=["Unified Public API — Visual Reasoning"])
class Payload(BaseModel):data:dict[str,Any]=Field(default_factory=dict)
def enabled(r):
 if not r.app.state.settings.unified_visual_reasoning_engine_enabled:raise HTTPException(503,"Unified Visual Reasoning Engine is disabled.")
def call(fn,*a):
 try:return fn(*a)
 except ValueError as e:raise HTTPException(422,str(e)) from e
@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):enabled(request);o=svc.readiness(db);o["migration_0074_applied"]="0074" in migration_status(request.app.state.database)["applied"];return o
@router.post("/compositions/{cid}/workspaces",dependencies=[Depends(require_write)])
def workspace(cid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_workspace,db,cid,p.data)
@router.post("/workspaces/{wid}/layer-bindings",dependencies=[Depends(require_write)])
def layer_binding(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.layer_binding,db,wid,p.data)
@router.post("/workspaces/{wid}/reasoning-paths",dependencies=[Depends(require_write)])
def reasoning_path(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.reasoning_path,db,wid,p.data)
@router.post("/workspaces/{wid}/state-bridges",dependencies=[Depends(require_write)])
def state_bridge(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.state_bridge,db,wid,p.data)
@router.post("/workspaces/{wid}/evidence-chains",dependencies=[Depends(require_write)])
def evidence_chain(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.evidence_chain,db,wid,p.data)
@router.post("/workspaces/{wid}/handoffs",dependencies=[Depends(require_write)])
def handoff(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.handoff,db,wid,p.data)
@router.post("/workspaces/{wid}/package-bindings",dependencies=[Depends(require_write)])
def package_binding(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.package_binding,db,wid,p.data)
@router.post("/workspaces/{wid}/replay-states",dependencies=[Depends(require_write)])
def replay_state(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.replay_state,db,wid,p.data)
@router.get("/workspaces/{wid}/bundle",dependencies=[Depends(require_read)])
def bundle(wid:str,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.bundle,db,wid)
@router.post("/workspaces/{wid}/snapshots",dependencies=[Depends(require_write)])
def snapshot(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.snapshot,db,wid,p.data)
@public_router.get("/workspaces/{wid}/bundle",response_model=PublicEnvelope)
def public_bundle(wid:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("read:visual"))):enabled(request);return PublicEnvelope(data=call(svc.bundle,db,wid,True),meta={"release":"2.70.0","contract":svc.CONTRACT})
