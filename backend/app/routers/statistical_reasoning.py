from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import statistical_reasoning as svc

router=APIRouter(prefix="/v1/analytics/statistical-reasoning",tags=["statistical-reasoning-v330"])
public_router=APIRouter(prefix="/api/v1/analytics/statistical-reasoning",tags=["public-statistical-reasoning-v330"])
class Payload(BaseModel): data:dict

def enabled(request):
    if not request.app.state.settings.statistical_reasoning_object_model_enabled: raise HTTPException(404,"feature disabled")
def call(fn,*a):
    try:return fn(*a)
    except ValueError as e: raise HTTPException(400,str(e)) from e

@router.get("/readiness",dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)): enabled(request); return svc.readiness(db)
@router.post("/ingest-validation",dependencies=[Depends(require_write)])
def ingest_validation(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.ingest_validation_bundle,db,payload.data)
@router.get("/{reasoning_ref}/bundle",dependencies=[Depends(require_read)])
def bundle(reasoning_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.reasoning_bundle,db,reasoning_ref)
@router.post("/{reasoning_ref}/coefficients",dependencies=[Depends(require_write)])
def coefficient(reasoning_ref:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_coefficient,db,reasoning_ref,payload.data)
@router.post("/{reasoning_ref}/intervals",dependencies=[Depends(require_write)])
def interval(reasoning_ref:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_interval,db,reasoning_ref,payload.data)
@router.post("/{reasoning_ref}/interpretations",dependencies=[Depends(require_write)])
def interpretation(reasoning_ref:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_interpretation,db,reasoning_ref,payload.data)
@router.post("/{reasoning_ref}/snapshots",dependencies=[Depends(require_write)])
def snapshot(reasoning_ref:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); x=call(svc.create_snapshot,db,reasoning_ref,payload.data); db.commit(); return x

@public_router.get("/readiness",response_model=PublicEnvelope)
def public_readiness(request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=svc.readiness(db),meta={"release":svc.RELEASE,"contract":svc.CONTRACT})
@public_router.get("/{reasoning_ref}/bundle",response_model=PublicEnvelope)
def public_bundle(reasoning_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.reasoning_bundle,db,reasoning_ref,True),meta={"release":svc.RELEASE,"contract":svc.CONTRACT})
