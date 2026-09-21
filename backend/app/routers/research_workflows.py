from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_workflows as svc
router=APIRouter(prefix="/v1/research/workflows",tags=["Research Workflow & Orchestration Engine"])
public_router=APIRouter(prefix="/api/v1/research/workflows",tags=["Unified Public API — Research Workflows"])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
 if not request.app.state.settings.research_workflow_orchestration_enabled: raise HTTPException(503,"Research Workflow & Orchestration Engine is disabled.")
def call(fn,*args):
 try:return fn(*args)
 except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)): enabled(request); out=svc.readiness(db); out["migration_0094_applied"]="0094" in migration_status(request.app.state.database)["applied"]; return out
@router.post("",dependencies=[Depends(require_write)])
def create(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_workflow,db,payload.data)
@router.post("/{workflow_id}/stages",dependencies=[Depends(require_write)])
def stage(workflow_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_stage,db,workflow_id,payload.data)
@router.post("/{workflow_id}/transitions",dependencies=[Depends(require_write)])
def transition(workflow_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_transition,db,workflow_id,payload.data)
@router.post("/{workflow_id}/transitions/{transition_key}/apply",dependencies=[Depends(require_write)])
def apply(workflow_id:str,transition_key:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.apply_transition,db,workflow_id,transition_key,payload.data)
@router.post("/{workflow_id}/context-bindings",dependencies=[Depends(require_write)])
def binding(workflow_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_binding,db,workflow_id,payload.data)
@router.post("/{workflow_id}/handoffs",dependencies=[Depends(require_write)])
def handoff(workflow_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_handoff,db,workflow_id,payload.data)
@router.post("/{workflow_id}/checkpoints",dependencies=[Depends(require_write)])
def checkpoint(workflow_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_checkpoint,db,workflow_id,payload.data)
@router.post("/{workflow_id}/events",dependencies=[Depends(require_write)])
def event(workflow_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_event,db,workflow_id,payload.data)
@router.post("/{workflow_id}/policies",dependencies=[Depends(require_write)])
def policy(workflow_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_policy,db,workflow_id,payload.data)
@router.post("/{workflow_id}/revisions",dependencies=[Depends(require_write)])
def revise(workflow_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise_workflow,db,workflow_id,payload.data)
@router.post("/{workflow_id}/snapshots",dependencies=[Depends(require_write)])
def snapshot(workflow_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,workflow_id,payload.data)
@router.get("/{workflow_id}/summary",dependencies=[Depends(require_read)])
def summary(workflow_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.descriptive_summary,db,workflow_id)
@router.get("/{workflow_id}/timeline",dependencies=[Depends(require_read)])
def timeline(workflow_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.timeline,db,workflow_id)
@router.get("/{workflow_id}/lineage",dependencies=[Depends(require_read)])
def lineage(workflow_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,workflow_id)
@router.get("/{workflow_id}/bundle",dependencies=[Depends(require_read)])
def bundle(workflow_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,workflow_id)
@public_router.get("/{workflow_id}/summary",response_model=PublicEnvelope)
def public_summary(workflow_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.descriptive_summary,db,workflow_id,True),meta={"release":"2.90.0","contract":svc.CONTRACT})
@public_router.get("/{workflow_id}/timeline",response_model=PublicEnvelope)
def public_timeline(workflow_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.timeline,db,workflow_id,True),meta={"release":"2.90.0","contract":svc.CONTRACT})
@public_router.get("/{workflow_id}/lineage",response_model=PublicEnvelope)
def public_lineage(workflow_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,workflow_id,True),meta={"release":"2.90.0","contract":svc.CONTRACT})
@public_router.get("/{workflow_id}/bundle",response_model=PublicEnvelope)
def public_bundle(workflow_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,workflow_id,True),meta={"release":"2.90.0","contract":svc.CONTRACT})
