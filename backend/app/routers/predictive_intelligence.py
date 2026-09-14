from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import predictive_intelligence as svc

router=APIRouter(prefix="/v1/predictive-intelligence",tags=["Predictive Intelligence"])
public_router=APIRouter(prefix="/api/v1/predictive-intelligence",tags=["Public Predictive Intelligence"])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def bad(exc): return exc if isinstance(exc,HTTPException) else HTTPException(status_code=422,detail=str(exc))
def enabled(request):
    if not request.app.state.settings.predictive_intelligence_enabled: raise HTTPException(status_code=404,detail="Predictive Intelligence is disabled.")
def public_enabled(request):
    enabled(request)
    if not request.app.state.settings.predictive_intelligence_public_metadata_enabled: raise HTTPException(status_code=404,detail="Public Predictive Intelligence metadata is disabled.")
@router.get("/readiness",dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    enabled(request); data=svc.readiness(db); data.update({"release":request.app.state.settings.version,"enabled":True}); return data
@router.post("/models",dependencies=[Depends(require_write)])
def create_model(request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.create_model(db,payload.data)
    except Exception as exc:raise bad(exc)
@router.get("/models",dependencies=[Depends(require_read)])
def models(request:Request,project_entity_id:str|None=None,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    enabled(request); items,total=svc.list_models(db,project_entity_id=project_entity_id,limit=limit,offset=offset); return {"items":items,"total":total,"limit":limit,"offset":offset}
@router.get("/models/{model_id}/bundle",dependencies=[Depends(require_read)])
def bundle(model_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return svc.bundle(db,model_id)
@router.post("/models/{model_id}/targets",dependencies=[Depends(require_write)])
def target(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_target(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/features",dependencies=[Depends(require_write)])
def feature(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_feature(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/training-windows",dependencies=[Depends(require_write)])
def window(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_training_window(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/forecast-runs",dependencies=[Depends(require_write)])
def run(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_forecast_run(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/forecast-runs/{run_id}/observations",dependencies=[Depends(require_write)])
def observation(model_id:str,run_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_forecast_observation(db,model_id,run_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/evaluations",dependencies=[Depends(require_write)])
def evaluation(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_evaluation(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/handoffs",dependencies=[Depends(require_write)])
def handoff(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_handoff(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/snapshots",dependencies=[Depends(require_write)])
def snapshot(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.create_snapshot(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@public_router.get("/readiness",response_model=PublicEnvelope)
def public_readiness(request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); data=svc.readiness(db); data.update({"release":request.app.state.settings.version,"enabled":True}); return PublicEnvelope(data=data,meta={"api_version":"v1","request_id":request.state.request_id})
@public_router.get("/models",response_model=PublicEnvelope)
def public_models(request:Request,project_entity_id:str|None=None,limit:int=Query(100,ge=1),offset:int=Query(0,ge=0),ctx:PublicApiContext=Depends(require_public_scope("data:read")),db:Session=Depends(get_session)):
    public_enabled(request); limit=min(limit,ctx.plan.max_page_size,request.app.state.settings.page_size_max); items,total=svc.list_models(db,project_entity_id=project_entity_id,public_only=True,limit=limit,offset=offset); return PublicEnvelope(data=items,meta={"api_version":"v1","request_id":request.state.request_id,"pagination":{"total":total,"limit":limit,"offset":offset}})
@public_router.get("/models/{model_id}/bundle",response_model=PublicEnvelope)
def public_bundle(model_id:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); return PublicEnvelope(data=svc.bundle(db,model_id,public_only=True),meta={"api_version":"v1","request_id":request.state.request_id})
