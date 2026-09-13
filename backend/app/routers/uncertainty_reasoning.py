from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import uncertainty_reasoning

router=APIRouter(prefix="/v1/uncertainty-reasoning",tags=["Uncertainty, Sensitivity & Ensemble Reasoning"])
public_router=APIRouter(prefix="/api/v1/uncertainty-reasoning",tags=["Unified Public API — Uncertainty Reasoning"])

class DataCreate(BaseModel): data: dict[str,Any]=Field(default_factory=dict)
class UncertaintyCreate(BaseModel):
    uncertainty_key:str;name:str;description:str|None=None;visibility:str="private";project_entity_id:str;subject_entity_id:str;uncertainty_kind:str="epistemic";distribution_family:str="interval";parameters:dict[str,Any]=Field(default_factory=dict);lower_bound:float|None=None;upper_bound:float|None=None;unit:str|None=None;confidence_level:float|None=None;source:dict[str,Any]=Field(default_factory=dict);provenance:dict[str,Any]=Field(default_factory=dict);assumptions:list[Any]=Field(default_factory=list);state:str="declared";metadata:dict[str,Any]=Field(default_factory=dict);created_by:str="operator"
class StudyCreate(BaseModel):
    study_key:str;name:str;description:str|None=None;visibility:str="private";project_entity_id:str;model_entity_id:str;model_version_entity_id:str;compute_plan_id:str|None=None;method:str="local";output_metric:str|None=None;study_state:str="draft";execution_product:str="lab";configuration:dict[str,Any]=Field(default_factory=dict);assumptions:list[Any]=Field(default_factory=list);metadata:dict[str,Any]=Field(default_factory=dict);created_by:str="operator"
class EnsembleCreate(BaseModel):
    ensemble_key:str;name:str;description:str|None=None;visibility:str="private";project_entity_id:str;model_entity_id:str;model_version_entity_id:str;compute_plan_id:str|None=None;ensemble_state:str="draft";combination_policy:dict[str,Any]=Field(default_factory=dict);assumptions:list[Any]=Field(default_factory=list);metadata:dict[str,Any]=Field(default_factory=dict);created_by:str="operator"

def bad(exc): return exc if isinstance(exc,HTTPException) else HTTPException(status_code=422,detail=str(exc))
def public_enabled(request:Request):
    if not request.app.state.settings.uncertainty_reasoning_public_metadata_enabled: raise HTTPException(status_code=404,detail="Uncertainty reasoning public metadata API is disabled.")

@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    data=uncertainty_reasoning.readiness(db);m=migration_status(request.app.state.database);data.update({'release':request.app.state.settings.version,'enabled':request.app.state.settings.uncertainty_reasoning_enabled,'migration_0039_applied':'0039' in m['applied']});return data

@router.post('/uncertainties',dependencies=[Depends(require_write)])
def create_uncertainty(payload:UncertaintyCreate,request:Request,db:Session=Depends(get_session)):
    if not request.app.state.settings.uncertainty_reasoning_enabled: raise HTTPException(status_code=503,detail='Uncertainty reasoning is disabled.')
    try:return uncertainty_reasoning.create_uncertainty(db,payload.model_dump())
    except Exception as exc:raise bad(exc)
@router.get('/uncertainties',dependencies=[Depends(require_read)])
def uncertainties(request:Request,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    items,total=uncertainty_reasoning.list_uncertainties(db,limit=min(limit,request.app.state.settings.page_size_max),offset=offset);return {'items':items,'total':total,'limit':limit,'offset':offset}
@router.get('/uncertainties/{uncertainty_id}',dependencies=[Depends(require_read)])
def uncertainty_detail(uncertainty_id:str,db:Session=Depends(get_session)):return uncertainty_reasoning.read_uncertainty(db,uncertainty_id)

@router.post('/sensitivity-studies',dependencies=[Depends(require_write)])
def create_study(payload:StudyCreate,db:Session=Depends(get_session)):
    try:return uncertainty_reasoning.create_study(db,payload.model_dump())
    except Exception as exc:raise bad(exc)
@router.get('/sensitivity-studies',dependencies=[Depends(require_read)])
def studies(request:Request,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    items,total=uncertainty_reasoning.list_studies(db,limit=min(limit,request.app.state.settings.page_size_max),offset=offset);return {'items':items,'total':total,'limit':limit,'offset':offset}
@router.post('/sensitivity-studies/{study_id}/factors',dependencies=[Depends(require_write)])
def add_factor(study_id:str,payload:DataCreate,db:Session=Depends(get_session)):
    try:return uncertainty_reasoning.add_factor(db,study_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/sensitivity-studies/{study_id}/measures',dependencies=[Depends(require_write)])
def add_measure(study_id:str,payload:DataCreate,db:Session=Depends(get_session)):
    try:return uncertainty_reasoning.add_measure(db,study_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.get('/sensitivity-studies/{study_id}/summary',dependencies=[Depends(require_read)])
def study_summary(study_id:str,db:Session=Depends(get_session)):return uncertainty_reasoning.sensitivity_summary(db,study_id)
@router.get('/sensitivity-studies/{study_id}/bundle',dependencies=[Depends(require_read)])
def study_bundle(study_id:str,db:Session=Depends(get_session)):return uncertainty_reasoning.sensitivity_bundle(db,study_id)

@router.post('/ensembles',dependencies=[Depends(require_write)])
def create_ensemble(payload:EnsembleCreate,db:Session=Depends(get_session)):
    try:return uncertainty_reasoning.create_ensemble(db,payload.model_dump())
    except Exception as exc:raise bad(exc)
@router.get('/ensembles',dependencies=[Depends(require_read)])
def ensembles(request:Request,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    items,total=uncertainty_reasoning.list_ensembles(db,limit=min(limit,request.app.state.settings.page_size_max),offset=offset);return {'items':items,'total':total,'limit':limit,'offset':offset}
@router.post('/ensembles/{ensemble_id}/members',dependencies=[Depends(require_write)])
def add_member(ensemble_id:str,payload:DataCreate,db:Session=Depends(get_session)):
    try:return uncertainty_reasoning.add_member(db,ensemble_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/ensembles/{ensemble_id}/statistics',dependencies=[Depends(require_write)])
def add_statistic(ensemble_id:str,payload:DataCreate,db:Session=Depends(get_session)):
    try:return uncertainty_reasoning.add_statistic(db,ensemble_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.get('/ensembles/{ensemble_id}/summary',dependencies=[Depends(require_read)])
def ensemble_summary(ensemble_id:str,db:Session=Depends(get_session)):return uncertainty_reasoning.ensemble_summary(db,ensemble_id)
@router.get('/ensembles/{ensemble_id}/bundle',dependencies=[Depends(require_read)])
def ensemble_bundle(ensemble_id:str,db:Session=Depends(get_session)):return uncertainty_reasoning.ensemble_bundle(db,ensemble_id)

@public_router.get('/readiness',response_model=PublicEnvelope)
def public_readiness(request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    public_enabled(request);data=uncertainty_reasoning.readiness(db);data.update({'release':request.app.state.settings.version,'enabled':request.app.state.settings.uncertainty_reasoning_enabled});return PublicEnvelope(data=data,meta={'api_version':'v1','request_id':request.state.request_id})
@public_router.get('/uncertainties',response_model=PublicEnvelope)
def public_uncertainties(request:Request,limit:int=Query(100,ge=1),offset:int=Query(0,ge=0),ctx:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):
    public_enabled(request);limit=min(limit,ctx.plan.max_page_size,request.app.state.settings.page_size_max);items,total=uncertainty_reasoning.list_uncertainties(db,public_only=True,limit=limit,offset=offset);return PublicEnvelope(data=items,meta={'api_version':'v1','request_id':request.state.request_id,'pagination':{'total':total,'limit':limit,'offset':offset}})
@public_router.get('/sensitivity-studies',response_model=PublicEnvelope)
def public_studies(request:Request,limit:int=Query(100,ge=1),offset:int=Query(0,ge=0),ctx:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):
    public_enabled(request);limit=min(limit,ctx.plan.max_page_size,request.app.state.settings.page_size_max);items,total=uncertainty_reasoning.list_studies(db,public_only=True,limit=limit,offset=offset);return PublicEnvelope(data=items,meta={'api_version':'v1','request_id':request.state.request_id,'pagination':{'total':total,'limit':limit,'offset':offset}})
@public_router.get('/sensitivity-studies/{study_id}/summary',response_model=PublicEnvelope)
def public_study_summary(study_id:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    public_enabled(request);return PublicEnvelope(data=uncertainty_reasoning.sensitivity_summary(db,study_id,public_only=True),meta={'api_version':'v1','request_id':request.state.request_id})
@public_router.get('/ensembles',response_model=PublicEnvelope)
def public_ensembles(request:Request,limit:int=Query(100,ge=1),offset:int=Query(0,ge=0),ctx:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):
    public_enabled(request);limit=min(limit,ctx.plan.max_page_size,request.app.state.settings.page_size_max);items,total=uncertainty_reasoning.list_ensembles(db,public_only=True,limit=limit,offset=offset);return PublicEnvelope(data=items,meta={'api_version':'v1','request_id':request.state.request_id,'pagination':{'total':total,'limit':limit,'offset':offset}})
@public_router.get('/ensembles/{ensemble_id}/summary',response_model=PublicEnvelope)
def public_ensemble_summary(ensemble_id:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    public_enabled(request);return PublicEnvelope(data=uncertainty_reasoning.ensemble_summary(db,ensemble_id,public_only=True),meta={'api_version':'v1','request_id':request.state.request_id})
