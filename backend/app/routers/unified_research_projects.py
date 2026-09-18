from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import unified_research_projects as svc

router=APIRouter(prefix="/v1/research/projects",tags=["Unified Research Project Object Model"])
public_router=APIRouter(prefix="/api/v1/research/projects",tags=["Unified Public API — Research Projects"])
class Payload(BaseModel): data: dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
    if not request.app.state.settings.unified_research_project_model_enabled: raise HTTPException(503,"Unified Research Project Object Model is disabled.")
def call(fn,*args):
    try:return fn(*args)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc

@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):
    enabled(request); out=svc.readiness(db); out["migration_0076_applied"]="0076" in migration_status(request.app.state.database)["applied"]; return out
@router.post("",dependencies=[Depends(require_write)])
def create(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_project,db,payload.data)
@router.post("/{project_id}/profile",dependencies=[Depends(require_write)])
def adopt(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.adopt_project,db,project_id,payload.data)
@router.post("/{project_id}/questions",dependencies=[Depends(require_write)])
def add_question(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.question,db,project_id,payload.data)
@router.post("/{project_id}/objectives",dependencies=[Depends(require_write)])
def add_objective(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.objective,db,project_id,payload.data)
@router.post("/{project_id}/components",dependencies=[Depends(require_write)])
def add_component(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.component,db,project_id,payload.data)
@router.post("/{project_id}/relationships",dependencies=[Depends(require_write)])
def add_relationship(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.relationship,db,project_id,payload.data)
@router.post("/{project_id}/provenance",dependencies=[Depends(require_write)])
def add_provenance(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.provenance,db,project_id,payload.data)
@router.post("/{project_id}/handoffs",dependencies=[Depends(require_write)])
def add_handoff(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.handoff,db,project_id,payload.data)
@router.get("/{project_id}/bundle",dependencies=[Depends(require_read)])
def get_bundle(project_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,project_id)
@router.post("/{project_id}/snapshots",dependencies=[Depends(require_write)])
def add_snapshot(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,project_id,payload.data)
@public_router.get("/{project_id}/bundle",response_model=PublicEnvelope)
def public_bundle(project_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    enabled(request); return PublicEnvelope(data=call(svc.bundle,db,project_id,True),meta={"release":"2.72.0","contract":svc.CONTRACT})
