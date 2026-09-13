from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import uncertainty_reasoning as ur

router=APIRouter(prefix='/v1/uncertainty-reasoning',tags=['Uncertainty, Sensitivity & Ensemble Reasoning'])
public_router=APIRouter(prefix='/api/v1/uncertainty-reasoning',tags=['Unified Public API — Uncertainty Reasoning'])

class DataCreate(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
class UncertaintyCreate(BaseModel):
    uncertainty_key:str;name:str;description:str|None=None;visibility:str='private';project_entity_id:str;model_entity_id:str|None=None;target_entity_id:str;uncertainty_kind:str='interval';distribution_name:str|None=None;unit:str|None=None;lower_bound:float|None=None;upper_bound:float|None=None;confidence_level:float|None=None;parameters:dict[str,Any]=Field(default_factory=dict);empirical_values:list[Any]=Field(default_factory=list);assumptions:list[Any]=Field(default_factory=list);provenance:dict[str,Any]=Field(default_factory=dict);metadata:dict[str,Any]=Field(default_factory=dict);created_by:str='operator'
class SensitivityCreate(BaseModel):
    study_key:str;name:str;description:str|None=None;slug:str|None=None;visibility:str='private';project_entity_id:str;model_entity_id:str;model_version_entity_id:str;compute_plan_id:str|None=None;study_state:str='draft';method:str='one-at-a-time';output_key:str|None=None;sampling_contract:dict[str,Any]=Field(default_factory=dict);execution_product:str='lab';assumptions:list[Any]=Field(default_factory=list);metadata:dict[str,Any]=Field(default_factory=dict);created_by:str='operator'
class EnsembleCreate(BaseModel):
    ensemble_key:str;name:str;description:str|None=None;slug:str|None=None;visibility:str='private';project_entity_id:str;model_entity_id:str;model_version_entity_id:str;compute_plan_id:str|None=None;ensemble_state:str='draft';weighting_policy:str='equal';aggregation_contract:dict[str,Any]=Field(default_factory=dict);assumptions:list[Any]=Field(default_factory=list);metadata:dict[str,Any]=Field(default_factory=dict);created_by:str='operator'

def bad(exc): return exc if isinstance(exc,HTTPException) else HTTPException(status_code=422,detail=str(exc))
def public_enabled(request:Request):
    if not request.app.state.settings.uncertainty_reasoning_public_metadata_enabled: raise HTTPException(status_code=404,detail='Uncertainty reasoning public metadata API is disabled.')

@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    d=ur.readiness(db);m=migration_status(request.app.state.database);d.update({'release':request.app.state.settings.version,'enabled':request.app.state.settings.uncertainty_reasoning_enabled,'migration_0039_applied':'0039' in m['applied']});return d

@router.post('/uncertainty-definitions',dependencies=[Depends(require_write)])
def create_uncertainty(payload:UncertaintyCreate,request:Request,db:Session=Depends(get_session)):
    if not request.app.state.settings.uncertainty_reasoning_enabled: raise HTTPException(status_code=503,detail='Uncertainty reasoning is disabled.')
    try:return ur.create_uncertainty(db,payload.model_dump())
    except Exception as exc:raise bad(exc)

@router.get('/uncertainty-definitions',dependencies=[Depends(require_read)])
def list_uncertainty(limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    items,total=ur.list_uncertainty(db,limit=limit,offset=offset);return {'items':items,'total':total,'limit':limit,'offset':offset}

@router.post('/sensitivity-studies',dependencies=[Depends(require_write)])
def create_study(payload:SensitivityCreate,request:Request,db:Session=Depends(get_session)):
    try:return ur.create_sensitivity_study(db,payload.model_dump(),release=request.app.state.settings.version)
    except Exception as exc:raise bad(exc)
@router.get('/sensitivity-studies',dependencies=[Depends(require_read)])
def list_studies(limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    items,total=ur.list_sensitivity_studies(db,limit=limit,offset=offset);return {'items':items,'total':total,'limit':limit,'offset':offset}
@router.get('/sensitivity-studies/{visual_id}',dependencies=[Depends(require_read)])
def read_study(visual_id:str,db:Session=Depends(get_session)):return ur.read_sensitivity_study(db,visual_id)
@router.get('/sensitivity-studies/{visual_id}/bundle',dependencies=[Depends(require_read)])
def study_bundle(visual_id:str,db:Session=Depends(get_session)):return ur.sensitivity_bundle(db,visual_id)
@router.get('/sensitivity-studies/{visual_id}/validate',dependencies=[Depends(require_read)])
def validate_study(visual_id:str,db:Session=Depends(get_session)):return ur.validate_sensitivity(db,visual_id)
@router.post('/sensitivity-studies/{visual_id}/factors',dependencies=[Depends(require_write)])
def add_factor(visual_id:str,payload:DataCreate,db:Session=Depends(get_session)):
    try:return ur.add_factor(db,visual_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/sensitivity-studies/{visual_id}/results',dependencies=[Depends(require_write)])
def add_result(visual_id:str,payload:DataCreate,db:Session=Depends(get_session)):
    try:return ur.add_sensitivity_result(db,visual_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/sensitivity-studies/{visual_id}/compile-specification',dependencies=[Depends(require_write)])
def compile_study(visual_id:str,payload:DataCreate,db:Session=Depends(get_session)):
    try:return ur.compile_sensitivity_spec(db,visual_id,payload.data)
    except Exception as exc:raise bad(exc)

@router.post('/ensembles',dependencies=[Depends(require_write)])
def create_ensemble(payload:EnsembleCreate,request:Request,db:Session=Depends(get_session)):
    try:return ur.create_ensemble(db,payload.model_dump(),release=request.app.state.settings.version)
    except Exception as exc:raise bad(exc)
@router.get('/ensembles',dependencies=[Depends(require_read)])
def list_ensembles(limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    items,total=ur.list_ensembles(db,limit=limit,offset=offset);return {'items':items,'total':total,'limit':limit,'offset':offset}
@router.get('/ensembles/{visual_id}',dependencies=[Depends(require_read)])
def read_ensemble(visual_id:str,db:Session=Depends(get_session)):return ur.read_ensemble(db,visual_id)
@router.get('/ensembles/{visual_id}/bundle',dependencies=[Depends(require_read)])
def ensemble_bundle(visual_id:str,db:Session=Depends(get_session)):return ur.ensemble_bundle(db,visual_id)
@router.get('/ensembles/{visual_id}/validate',dependencies=[Depends(require_read)])
def validate_ensemble(visual_id:str,db:Session=Depends(get_session)):return ur.validate_ensemble(db,visual_id)
@router.post('/ensembles/{visual_id}/members',dependencies=[Depends(require_write)])
def add_member(visual_id:str,payload:DataCreate,db:Session=Depends(get_session)):
    try:return ur.add_ensemble_member(db,visual_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/ensembles/{visual_id}/statistics',dependencies=[Depends(require_write)])
def add_stat(visual_id:str,payload:DataCreate,db:Session=Depends(get_session)):
    try:return ur.add_ensemble_statistic(db,visual_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/ensembles/{visual_id}/compile-specification',dependencies=[Depends(require_write)])
def compile_ensemble(visual_id:str,payload:DataCreate,db:Session=Depends(get_session)):
    try:return ur.compile_ensemble_spec(db,visual_id,payload.data)
    except Exception as exc:raise bad(exc)

@public_router.get('/readiness',response_model=PublicEnvelope)
def public_readiness(request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    public_enabled(request);d=ur.readiness(db);d.update({'release':request.app.state.settings.version,'enabled':request.app.state.settings.uncertainty_reasoning_enabled});return PublicEnvelope(data=d,meta={'api_version':'v1','request_id':request.state.request_id})
@public_router.get('/uncertainty-definitions',response_model=PublicEnvelope)
def public_uncertainty(request:Request,limit:int=Query(100,ge=1),offset:int=Query(0,ge=0),ctx:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):
    public_enabled(request);limit=min(limit,ctx.plan.max_page_size,request.app.state.settings.page_size_max);items,total=ur.list_uncertainty(db,public_only=True,limit=limit,offset=offset);return PublicEnvelope(data=items,meta={'api_version':'v1','request_id':request.state.request_id,'pagination':{'total':total,'limit':limit,'offset':offset}})
@public_router.get('/sensitivity-studies',response_model=PublicEnvelope)
def public_studies(request:Request,limit:int=Query(100,ge=1),offset:int=Query(0,ge=0),ctx:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):
    public_enabled(request);limit=min(limit,ctx.plan.max_page_size,request.app.state.settings.page_size_max);items,total=ur.list_sensitivity_studies(db,public_only=True,limit=limit,offset=offset);return PublicEnvelope(data=items,meta={'api_version':'v1','request_id':request.state.request_id,'pagination':{'total':total,'limit':limit,'offset':offset}})
@public_router.get('/sensitivity-studies/{visual_id}/bundle',response_model=PublicEnvelope)
def public_study_bundle(visual_id:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    public_enabled(request);return PublicEnvelope(data=ur.sensitivity_bundle(db,visual_id,public_only=True),meta={'api_version':'v1','request_id':request.state.request_id})
@public_router.get('/ensembles',response_model=PublicEnvelope)
def public_ensembles(request:Request,limit:int=Query(100,ge=1),offset:int=Query(0,ge=0),ctx:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):
    public_enabled(request);limit=min(limit,ctx.plan.max_page_size,request.app.state.settings.page_size_max);items,total=ur.list_ensembles(db,public_only=True,limit=limit,offset=offset);return PublicEnvelope(data=items,meta={'api_version':'v1','request_id':request.state.request_id,'pagination':{'total':total,'limit':limit,'offset':offset}})
@public_router.get('/ensembles/{visual_id}/bundle',response_model=PublicEnvelope)
def public_ensemble_bundle(visual_id:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    public_enabled(request);return PublicEnvelope(data=ur.ensemble_bundle(db,visual_id,public_only=True),meta={'api_version':'v1','request_id':request.state.request_id})
