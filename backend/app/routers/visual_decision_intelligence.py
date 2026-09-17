from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import visual_decision_intelligence as svc
router=APIRouter(prefix="/v1/visual-runtime/decision",tags=["Visual Decision Intelligence"])
public_router=APIRouter(prefix="/api/v1/visual-runtime/decision",tags=["Unified Public API — Visual Decision Intelligence"])
class Payload(BaseModel):data:dict[str,Any]=Field(default_factory=dict)
def enabled(r):
 if not r.app.state.settings.visual_decision_intelligence_enabled:raise HTTPException(503,"Visual Decision Intelligence is disabled.")
def call(fn,*a):
 try:return fn(*a)
 except ValueError as e:raise HTTPException(422,str(e)) from e
@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):enabled(request);o=svc.readiness(db);o["migration_0073_applied"]="0073" in migration_status(request.app.state.database)["applied"];return o
@router.post("/compositions/{cid}/workspaces",dependencies=[Depends(require_write)])
def workspace(cid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_workspace,db,cid,p.data)
@router.post("/workspaces/{wid}/alternatives",dependencies=[Depends(require_write)])
def alternative(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.alternative,db,wid,p.data)
@router.post("/workspaces/{wid}/criteria",dependencies=[Depends(require_write)])
def criterion(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.criterion,db,wid,p.data)
@router.post("/workspaces/{wid}/evidence-bindings",dependencies=[Depends(require_write)])
def evidence(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.evidence,db,wid,p.data)
@router.post("/workspaces/{wid}/scenario-bindings",dependencies=[Depends(require_write)])
def scenario(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.scenario,db,wid,p.data)
@router.post("/workspaces/{wid}/risk-overlays",dependencies=[Depends(require_write)])
def risk(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.risk,db,wid,p.data)
@router.post("/workspaces/{wid}/tradeoffs",dependencies=[Depends(require_write)])
def tradeoff(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.tradeoff,db,wid,p.data)
@router.post("/workspaces/{wid}/rationales",dependencies=[Depends(require_write)])
def rationale(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.rationale,db,wid,p.data)
@router.post("/workspaces/{wid}/handoffs",dependencies=[Depends(require_write)])
def handoff(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.handoff,db,wid,p.data)
@router.get("/workspaces/{wid}/bundle",dependencies=[Depends(require_read)])
def bundle(wid:str,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.bundle,db,wid)
@router.post("/workspaces/{wid}/snapshots",dependencies=[Depends(require_write)])
def snapshot(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.snapshot,db,wid,p.data)
@public_router.get("/workspaces/{wid}/bundle",response_model=PublicEnvelope)
def public_bundle(wid:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("read:visual"))):enabled(request);return PublicEnvelope(data=call(svc.bundle,db,wid,True),meta={"release":"2.69.0","contract":svc.CONTRACT})
