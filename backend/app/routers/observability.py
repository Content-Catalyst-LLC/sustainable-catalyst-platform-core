from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import observability

router=APIRouter(prefix="/v1/observability",tags=["Observability, SLOs & Production Operations"])
public_router=APIRouter(prefix="/api/v1/observability",tags=["Unified Public API — Production Status"])
class MetricCreate(BaseModel):
    service:str="platform-core"; metric_name:str; value:float; unit:str="count"; labels:dict=Field(default_factory=dict)
class SloCreate(BaseModel):
    service:str="platform-core"; name:str=Field(min_length=1,max_length=240); indicator:str; target:float; comparison:str|None=None; window_minutes:int=Field(default=60,ge=1,le=10080); minimum_samples:int=Field(default=1,ge=1); metadata:dict=Field(default_factory=dict); enabled:bool=True
class DeploymentCreate(BaseModel):
    release:str; environment:str="production"; state:str="deployed"; commit_sha:str|None=None; actor:str="operator"; metadata:dict=Field(default_factory=dict)
def rowdict(row): return {c.key:getattr(row,c.key) for c in row.__table__.columns}
def bad(e): return HTTPException(status_code=422,detail=str(e))
@router.get('/readiness',dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):
    d=observability.readiness(db,request.app.state.settings); m=migration_status(request.app.state.database); d.update({"release":request.app.state.settings.version,"migration_0021_applied":"0021" in m['applied'],"pending_migrations":m['pending'],"status":"ready" if d['enabled'] else "disabled"}); return d
@router.get('/metrics/summary',dependencies=[Depends(require_read)])
def metrics_summary(request:Request,service:str='platform-core',window_minutes:int=Query(default=60,ge=1,le=10080),db:Session=Depends(get_session)): return observability.summary(db,service,window_minutes)
@router.post('/metrics',dependencies=[Depends(require_write)])
def metric(payload:MetricCreate,db:Session=Depends(get_session)): return jsonable_encoder(rowdict(observability.record_metric(db,service=payload.service,metric_name=payload.metric_name,value=payload.value,unit=payload.unit,labels=payload.labels)))
@router.post('/slos',dependencies=[Depends(require_write)])
def slo_create(payload:SloCreate,db:Session=Depends(get_session)):
    try:return jsonable_encoder(rowdict(observability.create_slo(db,**payload.model_dump())))
    except ValueError as e: raise bad(e)
@router.get('/slos',dependencies=[Depends(require_read)])
def slos(service:str|None=None,db:Session=Depends(get_session)): return {"items":jsonable_encoder([rowdict(x) for x in observability.list_slos(db,service)])}
@router.get('/slos/evaluate',dependencies=[Depends(require_read)])
def slo_eval(service:str|None=None,db:Session=Depends(get_session)): return {"items":observability.evaluate_all(db,service)}
@router.post('/deployments',dependencies=[Depends(require_write)])
def deployment(payload:DeploymentCreate,db:Session=Depends(get_session)):
    try:return jsonable_encoder(rowdict(observability.create_deployment_marker(db,**payload.model_dump())))
    except ValueError as e: raise bad(e)
@router.get('/deployments',dependencies=[Depends(require_write)])
def deployments(limit:int=Query(100,ge=1,le=1000),db:Session=Depends(get_session)): return {"items":jsonable_encoder([rowdict(x) for x in observability.list_deployments(db,limit)])}
@router.post('/retention/compact',dependencies=[Depends(require_write)])
def compact(request:Request,db:Session=Depends(get_session)): return {"deleted_metric_samples":observability.compact_metrics(db,request.app.state.settings.observability_retention_hours)}
@public_router.get('/status')
def public_status(request:Request,db:Session=Depends(get_session),_context:PublicApiContext=Depends(require_public_scope('data:read'))):
    settings=request.app.state.settings
    if not settings.observability_public_status_enabled: raise HTTPException(status_code=404,detail='Public production status is disabled.')
    r=observability.readiness(db,settings); s=observability.summary(db,'platform-core',settings.observability_default_window_minutes); evals=observability.evaluate_all(db,'platform-core')
    safe={"release":settings.version,"status":"ready" if r['enabled'] else "disabled","window_minutes":s['window_minutes'],"sample_count":s['sample_count'],"availability_percent":s['availability_percent'],"error_rate_percent":s['error_rate_percent'],"latency_p95_ms":s['latency_p95_ms'],"slo_states":[{"name":x['name'],"indicator":x['indicator'],"state":x['state']} for x in evals],"latest_deployment_release":r['latest_deployment_release'],"latest_deployment_state":r['latest_deployment_state'],"external_monitoring_provider_required":False,"request_ids_publicly_exposed":False,"operator_metadata_publicly_exposed":False}
    return PublicEnvelope(data=safe,meta={"api_version":"v1","request_id":request.state.request_id})
