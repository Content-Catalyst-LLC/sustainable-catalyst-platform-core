from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import uncertainty_probabilistic_evidence as svc
router=APIRouter(prefix="/v1/analytics/uncertainty-evidence",tags=["uncertainty-evidence-v3210"])
public_router=APIRouter(prefix="/api/v1/analytics/uncertainty-evidence",tags=["public-uncertainty-evidence-v3210"])
class Payload(BaseModel): data:dict
def enabled(request):
    if not request.app.state.settings.uncertainty_probabilistic_evidence_enabled: raise HTTPException(404,"feature disabled")
def call(fn,*a):
    try:return fn(*a)
    except ValueError as e: raise HTTPException(400,str(e)) from e
@router.get("/readiness",dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)): enabled(request); return svc.readiness(db)
@router.post("/ingest",dependencies=[Depends(require_write)])
def ingest(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.ingest,db,payload.data)
@router.get("/{study_ref}/bundle",dependencies=[Depends(require_read)])
def bundle(study_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,study_ref)
@router.post("/{study_ref}/interpretations",dependencies=[Depends(require_write)])
def interpretation(study_ref:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.interpret,db,study_ref,payload.data)
@router.post("/{study_ref}/snapshots",dependencies=[Depends(require_write)])
def snap(study_ref:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); x=call(svc.snapshot,db,study_ref,payload.data); db.commit(); return x
@public_router.get("/readiness",response_model=PublicEnvelope)
def public_readiness(request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=svc.readiness(db),meta={"release":svc.RELEASE,"contract":svc.CONTRACT})
