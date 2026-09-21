from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_protocols as svc
router=APIRouter(prefix="/v1/research/protocols",tags=["Scientific Study & Investigation Protocol Model"])
public_router=APIRouter(prefix="/api/v1/research/protocols",tags=["Unified Public API — Scientific Study & Investigation Protocol Model"])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
 if not request.app.state.settings.scientific_study_investigation_protocol_enabled: raise HTTPException(503,"Scientific Study & Investigation Protocol Model is disabled.")
def call(fn,*args):
 try:return fn(*args)
 except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)): enabled(request); out=svc.readiness(db); out["migration_0090_applied"]="0090" in migration_status(request.app.state.database)["applied"]; return out
@router.post("",dependencies=[Depends(require_write)])
def create(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_protocol,db,payload.data)
for_path=[]
@router.post("/{protocol_id}/objectives",dependencies=[Depends(require_write)])
def objective(protocol_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_objective,db,protocol_id,payload.data)
@router.post("/{protocol_id}/scope",dependencies=[Depends(require_write)])
def scope(protocol_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_scope,db,protocol_id,payload.data)
@router.post("/{protocol_id}/measures",dependencies=[Depends(require_write)])
def measure(protocol_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_measure,db,protocol_id,payload.data)
@router.post("/{protocol_id}/sources",dependencies=[Depends(require_write)])
def source(protocol_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_source,db,protocol_id,payload.data)
@router.post("/{protocol_id}/acquisition-plans",dependencies=[Depends(require_write)])
def acquisition(protocol_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_acquisition,db,protocol_id,payload.data)
@router.post("/{protocol_id}/methods",dependencies=[Depends(require_write)])
def method(protocol_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_method,db,protocol_id,payload.data)
@router.post("/{protocol_id}/assumptions",dependencies=[Depends(require_write)])
def assumption(protocol_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_assumption,db,protocol_id,payload.data)
@router.post("/{protocol_id}/validation-plans",dependencies=[Depends(require_write)])
def validation(protocol_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_validation,db,protocol_id,payload.data)
@router.post("/{protocol_id}/outputs",dependencies=[Depends(require_write)])
def output(protocol_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_output,db,protocol_id,payload.data)
@router.post("/{protocol_id}/deviations",dependencies=[Depends(require_write)])
def deviation(protocol_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_deviation,db,protocol_id,payload.data)
@router.post("/{protocol_id}/revisions",dependencies=[Depends(require_write)])
def revise(protocol_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise_protocol,db,protocol_id,payload.data)
@router.post("/{protocol_id}/snapshots",dependencies=[Depends(require_write)])
def snapshot(protocol_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,protocol_id,payload.data)
@router.get("/{protocol_id}/summary",dependencies=[Depends(require_read)])
def summary(protocol_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.descriptive_summary,db,protocol_id)
@router.get("/{protocol_id}/lineage",dependencies=[Depends(require_read)])
def lineage(protocol_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,protocol_id)
@router.get("/{protocol_id}/bundle",dependencies=[Depends(require_read)])
def bundle(protocol_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,protocol_id)
@public_router.get("/{protocol_id}/summary",response_model=PublicEnvelope)
def public_summary(protocol_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.descriptive_summary,db,protocol_id,True),meta={"release":"2.86.0","contract":svc.CONTRACT})
@public_router.get("/{protocol_id}/lineage",response_model=PublicEnvelope)
def public_lineage(protocol_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,protocol_id,True),meta={"release":"2.86.0","contract":svc.CONTRACT})
@public_router.get("/{protocol_id}/bundle",response_model=PublicEnvelope)
def public_bundle(protocol_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,protocol_id,True),meta={"release":"2.86.0","contract":svc.CONTRACT})
