from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_project_state as svc
router=APIRouter(prefix="/v1/research/project-state",tags=["Research Project State, Versioning & Reproducibility"])
public_router=APIRouter(prefix="/api/v1/research/project-state",tags=["Unified Public API — Research Project State"])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
 if not request.app.state.settings.research_project_state_versioning_reproducibility_enabled: raise HTTPException(503,"Research Project State, Versioning & Reproducibility is disabled.")
def call(fn,*args):
 try:return fn(*args)
 except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)): enabled(request); out=svc.readiness(db); out["migration_0096_applied"]="0096" in migration_status(request.app.state.database)["applied"]; return out
@router.post("/states",dependencies=[Depends(require_write)])
def create(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_state,db,payload.data)
@router.post("/states/{state_id}/versions",dependencies=[Depends(require_write)])
def version(state_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_version,db,state_id,payload.data)
@router.post("/states/{state_id}/versions/{version}/bindings",dependencies=[Depends(require_write)])
def binding(state_id:str,version:int,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_binding,db,state_id,version,payload.data)
@router.post("/states/{state_id}/versions/{version}/dependencies",dependencies=[Depends(require_write)])
def dependency(state_id:str,version:int,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_dependency,db,state_id,version,payload.data)
@router.post("/states/{state_id}/versions/{version}/environments",dependencies=[Depends(require_write)])
def environment(state_id:str,version:int,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_environment,db,state_id,version,payload.data)
@router.post("/states/{state_id}/versions/{version}/freeze",dependencies=[Depends(require_write)])
def freeze(state_id:str,version:int,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.freeze_version,db,state_id,version,payload.data)
@router.get("/states/{state_id}/versions/{version}/manifest",dependencies=[Depends(require_read)])
def manifest(state_id:str,version:int,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.historical_manifest,db,state_id,version)
@router.post("/states/{state_id}/checkpoints",dependencies=[Depends(require_write)])
def checkpoint(state_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_checkpoint,db,state_id,payload.data)
@router.post("/states/{state_id}/reconstruction-plans",dependencies=[Depends(require_write)])
def plan(state_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_reconstruction_plan,db,state_id,payload.data)
@router.post("/states/{state_id}/reconstruction-plans/{plan_key}/verifications",dependencies=[Depends(require_write)])
def verification(state_id:str,plan_key:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_verification,db,state_id,plan_key,payload.data)
@router.post("/states/{state_id}/revisions",dependencies=[Depends(require_write)])
def revise(state_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise_state,db,state_id,payload.data)
@router.post("/states/{state_id}/snapshots",dependencies=[Depends(require_write)])
def snapshot(state_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,state_id,payload.data)
@router.get("/states/{state_id}/summary",dependencies=[Depends(require_read)])
def summary(state_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.descriptive_summary,db,state_id)
@router.get("/states/{state_id}/lineage",dependencies=[Depends(require_read)])
def lineage(state_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,state_id)
@router.get("/states/{state_id}/bundle",dependencies=[Depends(require_read)])
def bundle(state_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,state_id)
@public_router.get("/states/{state_id}/summary",response_model=PublicEnvelope)
def public_summary(state_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.descriptive_summary,db,state_id,True),meta={"release":"2.92.0","contract":svc.CONTRACT})
@public_router.get("/states/{state_id}/lineage",response_model=PublicEnvelope)
def public_lineage(state_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,state_id,True),meta={"release":"2.92.0","contract":svc.CONTRACT})
@public_router.get("/states/{state_id}/bundle",response_model=PublicEnvelope)
def public_bundle(state_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,state_id,True),meta={"release":"2.92.0","contract":svc.CONTRACT})
@public_router.get("/states/{state_id}/versions/{version}/manifest",response_model=PublicEnvelope)
def public_manifest(state_id:str,version:int,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.historical_manifest,db,state_id,version,True),meta={"release":"2.92.0","contract":svc.CONTRACT})
