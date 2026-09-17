from __future__ import annotations
from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import visual_predictive_intelligence as svc
router=APIRouter(prefix='/v1/visual-runtime/predictive',tags=['Visual Predictive Intelligence'])
public_router=APIRouter(prefix='/api/v1/visual-runtime/predictive',tags=['Unified Public API — Visual Predictive Intelligence'])
class Payload(BaseModel):data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
    if not request.app.state.settings.visual_predictive_intelligence_enabled:raise HTTPException(status_code=503,detail='Visual Predictive Intelligence is disabled.')
def call(fn,*a,**kw):
    try:return fn(*a,**kw)
    except ValueError as e:raise HTTPException(status_code=422,detail=str(e)) from e
@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    enabled(request);o=svc.readiness(db);o['migration_0071_applied']='0071' in migration_status(request.app.state.database)['applied'];return o
@router.post('/compositions/{composition_id}/workspaces',dependencies=[Depends(require_write)])
def create_workspace(composition_id:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_workspace,db,composition_id,p.data)
@router.post('/workspaces/{wid}/forecast-overlays',dependencies=[Depends(require_write)])
def forecast(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_forecast_overlay,db,wid,p.data)
@router.post('/workspaces/{wid}/uncertainty-displays',dependencies=[Depends(require_write)])
def uncertainty(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_uncertainty_display,db,wid,p.data)
@router.post('/workspaces/{wid}/calibration-displays',dependencies=[Depends(require_write)])
def calibration(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_calibration_display,db,wid,p.data)
@router.post('/workspaces/{wid}/ensemble-comparisons',dependencies=[Depends(require_write)])
def ensemble(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_ensemble_comparison,db,wid,p.data)
@router.post('/workspaces/{wid}/monitoring-overlays',dependencies=[Depends(require_write)])
def monitoring(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_monitoring_overlay,db,wid,p.data)
@router.post('/workspaces/{wid}/spatial-temporal-layers',dependencies=[Depends(require_write)])
def spatial(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_spatial_temporal_layer,db,wid,p.data)
@router.post('/workspaces/{wid}/causal-overlays',dependencies=[Depends(require_write)])
def causal(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_causal_overlay,db,wid,p.data)
@router.post('/workspaces/{wid}/decision-bindings',dependencies=[Depends(require_write)])
def decision(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_decision_binding,db,wid,p.data)
@router.get('/workspaces/{wid}/bundle',dependencies=[Depends(require_read)])
def bundle(wid:str,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.workspace_bundle,db,wid)
@router.post('/workspaces/{wid}/snapshots',dependencies=[Depends(require_write)])
def snapshot(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_snapshot,db,wid,p.data)
@public_router.get('/workspaces/{wid}/bundle',response_model=PublicEnvelope)
def public_bundle(wid:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope('read:visual'))):
    enabled(request);return PublicEnvelope(data=call(svc.workspace_bundle,db,wid,True),meta={'release':'2.67.0','contract':svc.CONTRACT})
