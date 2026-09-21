from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import computation_lineage as svc
router=APIRouter(prefix="/v1/research/computation-lineage",tags=["Computation, Analysis & Execution Lineage"])
public_router=APIRouter(prefix="/api/v1/research/computation-lineage",tags=["Unified Public API — Computation, Analysis & Execution Lineage"])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
 if not request.app.state.settings.computation_analysis_execution_lineage_enabled: raise HTTPException(503,"Computation, Analysis & Execution Lineage is disabled.")
def call(fn,*args):
 try:return fn(*args)
 except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)): enabled(request); out=svc.readiness(db); out["migration_0091_applied"]="0091" in migration_status(request.app.state.database)["applied"]; return out
@router.post("/executions",dependencies=[Depends(require_write)])
def create(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_execution,db,payload.data)
@router.post("/executions/{execution_id}/inputs",dependencies=[Depends(require_write)])
def add_input(execution_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_input,db,execution_id,payload.data)
@router.post("/executions/{execution_id}/parameters",dependencies=[Depends(require_write)])
def add_parameter(execution_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_parameter,db,execution_id,payload.data)
@router.post("/executions/{execution_id}/assumptions",dependencies=[Depends(require_write)])
def add_assumption(execution_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_assumption,db,execution_id,payload.data)
@router.post("/executions/{execution_id}/environments",dependencies=[Depends(require_write)])
def add_environment(execution_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_environment,db,execution_id,payload.data)
@router.post("/executions/{execution_id}/steps",dependencies=[Depends(require_write)])
def add_step(execution_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_step,db,execution_id,payload.data)
@router.post("/executions/{execution_id}/outputs",dependencies=[Depends(require_write)])
def add_output(execution_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_output,db,execution_id,payload.data)
@router.post("/executions/{execution_id}/research-bindings",dependencies=[Depends(require_write)])
def add_binding(execution_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_research_binding,db,execution_id,payload.data)
@router.post("/executions/{execution_id}/dependencies",dependencies=[Depends(require_write)])
def add_dependency(execution_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_dependency,db,execution_id,payload.data)
@router.post("/executions/{execution_id}/verifications",dependencies=[Depends(require_write)])
def add_verification(execution_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_verification,db,execution_id,payload.data)
@router.post("/executions/{execution_id}/revisions",dependencies=[Depends(require_write)])
def revise(execution_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise_execution,db,execution_id,payload.data)
@router.post("/executions/{execution_id}/snapshots",dependencies=[Depends(require_write)])
def snapshot(execution_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,execution_id,payload.data)
@router.get("/executions/{execution_id}/summary",dependencies=[Depends(require_read)])
def summary(execution_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.descriptive_summary,db,execution_id)
@router.get("/executions/{execution_id}/lineage",dependencies=[Depends(require_read)])
def lineage(execution_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,execution_id)
@router.get("/executions/{execution_id}/bundle",dependencies=[Depends(require_read)])
def bundle(execution_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,execution_id)
@public_router.get("/executions/{execution_id}/summary",response_model=PublicEnvelope)
def public_summary(execution_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.descriptive_summary,db,execution_id,True),meta={"release":"2.87.0","contract":svc.CONTRACT})
@public_router.get("/executions/{execution_id}/lineage",response_model=PublicEnvelope)
def public_lineage(execution_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,execution_id,True),meta={"release":"2.87.0","contract":svc.CONTRACT})
@public_router.get("/executions/{execution_id}/bundle",response_model=PublicEnvelope)
def public_bundle(execution_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,execution_id,True),meta={"release":"2.87.0","contract":svc.CONTRACT})
