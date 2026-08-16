from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import workload_governance as workload

router=APIRouter(prefix="/v1/workload-governance",tags=["Distributed Quotas, Admission Control & Workload Governance"])
public_router=APIRouter(prefix="/api/v1/workload-governance",tags=["Unified Public API — Workload Governance"])
class Strict(BaseModel): model_config=ConfigDict(extra="forbid")
class ClassWrite(Strict):
    class_key:str=Field(min_length=1,max_length=120); name:str=Field(min_length=1,max_length=255); priority:int=Field(default=100,ge=0,le=1000)
    queue_weight:float=Field(default=1.0,gt=0,le=1000); max_concurrent_leases:int=Field(default=64,ge=1,le=1000000); max_request_units:float=Field(default=1000,gt=0)
    allow_when_slo_breached:bool=False; allow_when_capacity_critical:bool=False; enabled:bool=True; public_summary:bool=True; metadata:dict=Field(default_factory=dict)
class PolicyWrite(Strict):
    policy_key:str=Field(min_length=1,max_length=255); name:str=Field(min_length=1,max_length=300); subject_scope:str="product"; subject_key:str="*"; resource_type:str="requests"
    workload_class_key:str|None=None; window_seconds:int|None=Field(default=None,ge=1,le=86400); limit_units:float=Field(default=1000,gt=0); burst_units:float=Field(default=0,ge=0)
    enforcement_mode:str="enforce"; enabled:bool=True; public_summary:bool=False; metadata:dict=Field(default_factory=dict)
class AdmitWrite(Strict):
    request_key:str=Field(min_length=1,max_length=255); subject_scope:str="product"; subject_key:str=Field(min_length=1,max_length=255); resource_type:str="requests"
    workload_class_key:str="standard"; requested_units:float=Field(default=1,gt=0); lease_key:str|None=Field(default=None,max_length=255); lease_seconds:int|None=Field(default=None,ge=1,le=86400); metadata:dict=Field(default_factory=dict)

def bad(e): return HTTPException(status_code=422,detail=str(e))
@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    body=workload.readiness(db,request.app.state.settings); m=migration_status(request.app.state.database); body.update({'release':request.app.state.settings.version,'migration_0029_applied':'0029' in m['applied'],'pending_migrations':m['pending']}); return body
@router.post('/bootstrap',dependencies=[Depends(require_write)])
def bootstrap(request:Request,db:Session=Depends(get_session)):
    classes,policies=workload.bootstrap_defaults(db,request.app.state.settings); return {'classes':jsonable_encoder([workload.workload_class_dict(x) for x in classes]),'policies':jsonable_encoder([workload.policy_dict(x) for x in policies])}
@router.post('/classes',dependencies=[Depends(require_write)])
def write_class(payload:ClassWrite,db:Session=Depends(get_session)):
    try:return jsonable_encoder(workload.workload_class_dict(workload.upsert_workload_class(db,**payload.model_dump())))
    except ValueError as e: raise bad(e)
@router.get('/classes',dependencies=[Depends(require_read)])
def classes(enabled_only:bool=Query(False),db:Session=Depends(get_session)):return {'items':jsonable_encoder([workload.workload_class_dict(x) for x in workload.list_workload_classes(db,enabled_only)])}
@router.post('/quotas',dependencies=[Depends(require_write)])
def write_policy(payload:PolicyWrite,request:Request,db:Session=Depends(get_session)):
    try:return jsonable_encoder(workload.policy_dict(workload.upsert_policy(db,request.app.state.settings,**payload.model_dump())))
    except ValueError as e:raise bad(e)
@router.get('/quotas',dependencies=[Depends(require_read)])
def quotas(enabled_only:bool=Query(False),db:Session=Depends(get_session)):return {'items':jsonable_encoder([workload.policy_dict(x) for x in workload.list_policies(db,enabled_only)])}
@router.post('/admit',dependencies=[Depends(require_write)])
def admit(payload:AdmitWrite,request:Request,db:Session=Depends(get_session)):
    try:
        d,l=workload.admit(db,request.app.state.settings,**payload.model_dump()); return {'decision':jsonable_encoder(workload.decision_dict(d)),'lease':jsonable_encoder(workload.lease_dict(l)) if l else None}
    except ValueError as e:raise bad(e)
@router.post('/leases/{lease_id}/release',dependencies=[Depends(require_write)])
def release(lease_id:str,db:Session=Depends(get_session)):
    try:return jsonable_encoder(workload.lease_dict(workload.release_lease(db,lease_id)))
    except ValueError as e:raise bad(e)
@router.get('/decisions',dependencies=[Depends(require_read)])
def decisions(limit:int=Query(200,ge=1,le=5000),db:Session=Depends(get_session)):return {'items':jsonable_encoder([workload.decision_dict(x) for x in workload.list_decisions(db,limit)])}
@router.get('/leases',dependencies=[Depends(require_read)])
def leases(state:str|None=Query(None),limit:int=Query(200,ge=1,le=5000),db:Session=Depends(get_session)):return {'items':jsonable_encoder([workload.lease_dict(x) for x in workload.list_leases(db,state,limit)])}
@public_router.get('/status')
def public_status(request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    safe=workload.public_status(db,request.app.state.settings); safe['release']=request.app.state.settings.version; return PublicEnvelope(data=safe,meta={'api_version':'v1','request_id':request.state.request_id})
