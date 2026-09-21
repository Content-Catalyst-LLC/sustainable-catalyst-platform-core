from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_quality_audit as svc
router=APIRouter(prefix="/v1/research/quality-audits",tags=["Research Quality, Bias & Methodological Audit Engine"])
public_router=APIRouter(prefix="/api/v1/research/quality-audits",tags=["Unified Public API — Research Quality Audits"])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
 if not request.app.state.settings.research_quality_bias_methodological_audit_enabled: raise HTTPException(503,"Research Quality, Bias & Methodological Audit Engine is disabled.")
def call(fn,*args):
 try:return fn(*args)
 except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)): enabled(request); out=svc.readiness(db); out["migration_0093_applied"]="0093" in migration_status(request.app.state.database)["applied"]; return out
@router.post("",dependencies=[Depends(require_write)])
def create(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_audit,db,payload.data)
@router.post("/{audit_id}/subjects",dependencies=[Depends(require_write)])
def subject(audit_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_subject,db,audit_id,payload.data)
@router.post("/{audit_id}/checks",dependencies=[Depends(require_write)])
def check(audit_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_check,db,audit_id,payload.data)
@router.post("/{audit_id}/findings",dependencies=[Depends(require_write)])
def finding(audit_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_finding,db,audit_id,payload.data)
@router.post("/{audit_id}/evidence",dependencies=[Depends(require_write)])
def evidence(audit_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_evidence,db,audit_id,payload.data)
@router.post("/{audit_id}/bias-assessments",dependencies=[Depends(require_write)])
def bias(audit_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_bias_assessment,db,audit_id,payload.data)
@router.post("/{audit_id}/method-assessments",dependencies=[Depends(require_write)])
def method(audit_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_method_assessment,db,audit_id,payload.data)
@router.post("/{audit_id}/responses",dependencies=[Depends(require_write)])
def response(audit_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_response,db,audit_id,payload.data)
@router.post("/{audit_id}/revisions",dependencies=[Depends(require_write)])
def revise(audit_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise_audit,db,audit_id,payload.data)
@router.post("/{audit_id}/snapshots",dependencies=[Depends(require_write)])
def snapshot(audit_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,audit_id,payload.data)
@router.get("/{audit_id}/summary",dependencies=[Depends(require_read)])
def summary(audit_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.descriptive_summary,db,audit_id)
@router.get("/{audit_id}/lineage",dependencies=[Depends(require_read)])
def lineage(audit_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,audit_id)
@router.get("/{audit_id}/bundle",dependencies=[Depends(require_read)])
def bundle(audit_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,audit_id)
@public_router.get("/{audit_id}/summary",response_model=PublicEnvelope)
def public_summary(audit_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.descriptive_summary,db,audit_id,True),meta={"release":"2.89.0","contract":svc.CONTRACT})
@public_router.get("/{audit_id}/lineage",response_model=PublicEnvelope)
def public_lineage(audit_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,audit_id,True),meta={"release":"2.89.0","contract":svc.CONTRACT})
@public_router.get("/{audit_id}/bundle",response_model=PublicEnvelope)
def public_bundle(audit_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,audit_id,True),meta={"release":"2.89.0","contract":svc.CONTRACT})
