from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..public_api_auth import PublicApiContext,require_public_scope
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..services import research_validation_challenge as svc
from ..schemas import PublicEnvelope
router=APIRouter(prefix="/v1/research/validation-challenges",tags=["research-validation-challenge"])
public_router=APIRouter(prefix="/api/v1/research/validation-challenges",tags=["public-research-validation-challenge"])
class Payload(BaseModel): data:dict=Field(default_factory=dict)
def enabled(r):
 if not r.app.state.settings.research_validation_challenge_engine_enabled: raise HTTPException(503,"research validation & challenge engine disabled")
def call(fn,*a):
 try:return fn(*a)
 except ValueError as e: raise HTTPException(400,str(e))
@router.get("/readiness",dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)): enabled(request); out=svc.readiness(db); out["migration_0098_applied"]="0098" in migration_status(request.app.state.database)["applied"]; return out
@router.post("/challenges",dependencies=[Depends(require_write)])
def challenge(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_challenge,db,payload.data)
@router.post("/targets",dependencies=[Depends(require_write)])
def target(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bind_target,db,payload.data)
@router.post("/alternatives",dependencies=[Depends(require_write)])
def alternative(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_alternative_hypothesis,db,payload.data)
@router.post("/contradiction-tests",dependencies=[Depends(require_write)])
def contradiction(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_contradiction_test,db,payload.data)
@router.post("/counterevidence",dependencies=[Depends(require_write)])
def counterevidence(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_counterevidence,db,payload.data)
@router.post("/sensitivity-checks",dependencies=[Depends(require_write)])
def sensitivity(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_sensitivity_check,db,payload.data)
@router.post("/robustness-checks",dependencies=[Depends(require_write)])
def robustness(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_robustness_check,db,payload.data)
@router.post("/replications",dependencies=[Depends(require_write)])
def replication(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_replication_attempt,db,payload.data)
@router.post("/reviewer-challenges",dependencies=[Depends(require_write)])
def reviewer(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_reviewer_challenge,db,payload.data)
@router.post("/responses",dependencies=[Depends(require_write)])
def response(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.respond,db,payload.data)
@router.post("/revisions",dependencies=[Depends(require_write)])
def revision(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise,db,payload.data)
@router.post("/snapshots",dependencies=[Depends(require_write)])
def snapshot(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,payload.data)
@router.get("/projects/{project_ref:path}/summary",dependencies=[Depends(require_read)])
def summary(project_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.descriptive_summary,db,project_ref)
@router.get("/projects/{project_ref:path}/lineage",dependencies=[Depends(require_read)])
def lineage(project_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,project_ref)
@router.get("/projects/{project_ref:path}/bundle",dependencies=[Depends(require_read)])
def bundle(project_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,project_ref)
@public_router.get("/projects/{project_ref:path}/summary",response_model=PublicEnvelope)
def public_summary(project_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.descriptive_summary,db,project_ref,True),meta={"release":"2.94.0","contract":svc.CONTRACT})
@public_router.get("/projects/{project_ref:path}/lineage",response_model=PublicEnvelope)
def public_lineage(project_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,project_ref,True),meta={"release":"2.94.0","contract":svc.CONTRACT})
@public_router.get("/projects/{project_ref:path}/bundle",response_model=PublicEnvelope)
def public_bundle(project_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,project_ref,True),meta={"release":"2.94.0","contract":svc.CONTRACT})
