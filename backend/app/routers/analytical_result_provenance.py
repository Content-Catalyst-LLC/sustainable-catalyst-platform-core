from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import analytical_result_provenance as svc

router=APIRouter(prefix="/v1/analytics/results",tags=["analytical-result-provenance-v320"])
public_router=APIRouter(prefix="/api/v1/analytics/results",tags=["public-analytical-result-provenance-v320"])
class Payload(BaseModel): data:dict

def enabled(request):
    if not request.app.state.settings.analytical_result_provenance_integration_enabled: raise HTTPException(404,"feature disabled")
def call(fn,*a):
    try:return fn(*a)
    except ValueError as e: raise HTTPException(400,str(e)) from e

@router.get("/readiness",dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)): enabled(request); return svc.readiness(db)
@router.post("/ingest",dependencies=[Depends(require_write)])
def ingest(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.ingest_result,db,payload.data)
@router.get("/{result_ref}/bundle",dependencies=[Depends(require_read)])
def bundle(result_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.result_bundle,db,result_ref)
@router.get("/{result_ref}/lineage",dependencies=[Depends(require_read)])
def lineage(result_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.result_lineage,db,result_ref)
@router.post("/{result_ref}/estimates",dependencies=[Depends(require_write)])
def estimate(result_ref:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_estimate,db,result_ref,payload.data)
@router.post("/{result_ref}/uncertainty",dependencies=[Depends(require_write)])
def uncertainty(result_ref:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_uncertainty,db,result_ref,payload.data)
@router.post("/{result_ref}/lineage",dependencies=[Depends(require_write)])
def add_lineage(result_ref:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_lineage,db,result_ref,payload.data)
@router.post("/{result_ref}/snapshots",dependencies=[Depends(require_write)])
def snapshot(result_ref:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); result=call(svc.create_snapshot,db,result_ref,payload.data); db.commit(); return result

@public_router.get("/readiness",response_model=PublicEnvelope)
def public_readiness(request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=svc.readiness(db),meta={"release":svc.RELEASE,"contract":svc.RESULT_CONTRACT})
@public_router.get("/{result_ref}/bundle",response_model=PublicEnvelope)
def public_bundle(result_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.result_bundle,db,result_ref,True),meta={"release":svc.RELEASE,"contract":svc.RESULT_CONTRACT})
@public_router.get("/{result_ref}/lineage",response_model=PublicEnvelope)
def public_lineage(result_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.result_lineage,db,result_ref,True),meta={"release":svc.RELEASE,"contract":svc.RESULT_CONTRACT})
