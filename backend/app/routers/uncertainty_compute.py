from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import uncertainty_compute as uc

router=APIRouter(prefix='/v1/uncertainty-compute',tags=['Uncertainty Compute Runtime'])
public_router=APIRouter(prefix='/api/v1/uncertainty-compute',tags=['Public Uncertainty Compute Runtime'])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def bad(exc):
    if isinstance(exc,HTTPException):return exc
    return HTTPException(status_code=422,detail=str(exc))
def enabled(request:Request):
    if not request.app.state.settings.uncertainty_compute_runtime_enabled:raise HTTPException(status_code=404,detail='Uncertainty compute runtime is disabled.')
def public_enabled(request:Request):
    enabled(request)
    if not request.app.state.settings.uncertainty_compute_public_metadata_enabled:raise HTTPException(status_code=404,detail='Public uncertainty compute metadata is disabled.')

@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    enabled(request);d=uc.readiness(db);d.update({'release':request.app.state.settings.version,'enabled':True,'max_samples':request.app.state.settings.uncertainty_compute_max_samples});return d
@router.post('/sampling/design',dependencies=[Depends(require_write)])
def sampling(request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request);d=payload.data
    try:
        factors=d.get('factors') or (uc.factors_from_uncertainty_definitions(db,list(d.get('uncertainty_definition_ids') or [])) if d.get('uncertainty_definition_ids') else [])
        result=uc.generate_design(factors,str(d.get('method') or 'monte-carlo'),int(d.get('sample_count',1000)),int(d.get('seed',42)),request.app.state.settings.uncertainty_compute_max_samples,int(d.get('levels',6)))
        if d.get('persist'): result['run']=uc.persist_run(db,{**d,'method':str(d.get('method') or 'monte-carlo'),'input_manifest':{'factors':factors}}, {'manifest_sha256':result['manifest_sha256'],'total_evaluations':result.get('total_evaluations')})
        return result
    except Exception as exc:raise bad(exc)
@router.post('/sensitivity/sobol',dependencies=[Depends(require_write)])
def sobol(request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:
        result=uc.analyze_sobol(payload.data)
        if payload.data.get('persist'):result['run']=uc.persist_run(db,{**payload.data,'method':'sobol-analysis','input_manifest':{'vector_lengths':{'A':len(payload.data.get('A') or []),'B':len(payload.data.get('B') or [])}}},result)
        return result
    except Exception as exc:raise bad(exc)
@router.post('/sensitivity/morris',dependencies=[Depends(require_write)])
def morris(request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:
        result=uc.analyze_morris(payload.data)
        if payload.data.get('persist'):result['run']=uc.persist_run(db,{**payload.data,'method':'morris-analysis','input_manifest':{'sample_count':len(payload.data.get('samples') or [])}},result)
        return result
    except Exception as exc:raise bad(exc)
@router.post('/ensembles/normalize-weights',dependencies=[Depends(require_write)])
def normalize(request:Request,payload:Payload):
    enabled(request)
    try:return uc.normalize_weights(list(payload.data.get('weights') or []),str(payload.data.get('policy') or 'explicit'))
    except Exception as exc:raise bad(exc)
@router.post('/ensembles/statistics',dependencies=[Depends(require_write)])
def stats(request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:
        result=uc.ensemble_statistics(list(payload.data.get('values') or []),payload.data.get('weights'),payload.data.get('quantiles'))
        if payload.data.get('persist'):result['run']=uc.persist_run(db,{**payload.data,'method':'ensemble-statistics','input_manifest':{'value_count':len(payload.data.get('values') or [])}},result)
        return result
    except Exception as exc:raise bad(exc)
@router.post('/probabilities/exceedance',dependencies=[Depends(require_write)])
def exceedance(request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:
        result=uc.exceedance_probability(list(payload.data.get('values') or []),float(payload.data.get('threshold')),str(payload.data.get('operator') or '>'))
        if payload.data.get('persist'):result['run']=uc.persist_run(db,{**payload.data,'method':'exceedance-probability','input_manifest':{'value_count':len(payload.data.get('values') or [])}},result)
        return result
    except Exception as exc:raise bad(exc)
@router.post('/runtime-handoffs',dependencies=[Depends(require_write)])
def handoff(request:Request,payload:Payload):
    enabled(request)
    try:return uc.runtime_handoff(payload.data)
    except Exception as exc:raise bad(exc)
@router.get('/runs',dependencies=[Depends(require_read)])
def runs(limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    items,total=uc.list_runs(db,limit,offset);return {'items':items,'total':total,'limit':limit,'offset':offset}
@router.get('/runs/{run_id}',dependencies=[Depends(require_read)])
def run(run_id:str,db:Session=Depends(get_session)):return uc.read_run(db,run_id)

@public_router.get('/readiness',response_model=PublicEnvelope)
def public_readiness(request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    public_enabled(request);d=uc.readiness(db);d.update({'release':request.app.state.settings.version,'enabled':True,'max_samples':request.app.state.settings.uncertainty_compute_max_samples});return PublicEnvelope(data=d,meta={'api_version':'v1','request_id':request.state.request_id})
