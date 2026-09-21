from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import unified_inference as svc
router=APIRouter(prefix="/v1/research/inferences",tags=["Unified Findings, Claims & Inference Engine"])
public_router=APIRouter(prefix="/api/v1/research/inferences",tags=["Unified Public API — Findings, Claims & Inference"])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
 if not request.app.state.settings.unified_findings_claims_inference_enabled: raise HTTPException(503,"Unified Findings, Claims & Inference Engine is disabled.")
def call(fn,*args):
 try:return fn(*args)
 except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)): enabled(request); out=svc.readiness(db); out["migration_0092_applied"]="0092" in migration_status(request.app.state.database)["applied"]; return out
@router.post("",dependencies=[Depends(require_write)])
def create(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_inference,db,payload.data)
@router.post("/{inference_id}/classifications",dependencies=[Depends(require_write)])
def classification(inference_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_classification,db,inference_id,payload.data)
@router.post("/{inference_id}/basis",dependencies=[Depends(require_write)])
def basis(inference_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_basis,db,inference_id,payload.data)
@router.post("/{inference_id}/assumptions",dependencies=[Depends(require_write)])
def assumption(inference_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_assumption,db,inference_id,payload.data)
@router.post("/{inference_id}/uncertainties",dependencies=[Depends(require_write)])
def uncertainty(inference_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_uncertainty,db,inference_id,payload.data)
@router.post("/{inference_id}/relations",dependencies=[Depends(require_write)])
def relation(inference_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_relation,db,inference_id,payload.data)
@router.post("/{inference_id}/challenges",dependencies=[Depends(require_write)])
def challenge(inference_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_challenge,db,inference_id,payload.data)
@router.post("/{inference_id}/revisions",dependencies=[Depends(require_write)])
def revise(inference_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise_inference,db,inference_id,payload.data)
@router.post("/{inference_id}/snapshots",dependencies=[Depends(require_write)])
def snapshot(inference_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,inference_id,payload.data)
@router.get("/{inference_id}/summary",dependencies=[Depends(require_read)])
def summary(inference_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.descriptive_summary,db,inference_id)
@router.get("/{inference_id}/lineage",dependencies=[Depends(require_read)])
def lineage(inference_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,inference_id)
@router.get("/{inference_id}/bundle",dependencies=[Depends(require_read)])
def bundle(inference_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,inference_id)
@public_router.get("/{inference_id}/summary",response_model=PublicEnvelope)
def public_summary(inference_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.descriptive_summary,db,inference_id,True),meta={"release":"2.88.0","contract":svc.CONTRACT})
@public_router.get("/{inference_id}/lineage",response_model=PublicEnvelope)
def public_lineage(inference_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,inference_id,True),meta={"release":"2.88.0","contract":svc.CONTRACT})
@public_router.get("/{inference_id}/bundle",response_model=PublicEnvelope)
def public_bundle(inference_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,inference_id,True),meta={"release":"2.88.0","contract":svc.CONTRACT})
