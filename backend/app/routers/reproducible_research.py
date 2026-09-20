from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import reproducible_research as svc
router=APIRouter(prefix='/v1/research/reproducibility',tags=['Reproducible Research Package Runtime'])
public_router=APIRouter(prefix='/api/v1/research/reproducibility',tags=['Unified Public API — Reproducible Research'])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def enabled(request):
 if not request.app.state.settings.reproducible_research_package_runtime_enabled: raise HTTPException(503,'Reproducible Research Package Runtime is disabled.')
def call(fn,*args):
 try:return fn(*args)
 except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.get('/readiness',dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):
 enabled(request);out=svc.readiness(db);out['migration_0079_applied']='0079' in migration_status(request.app.state.database)['applied'];return out
@router.post('/projects/{project_id}/packages',dependencies=[Depends(require_write)])
def cp(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.create_package,db,project_id,payload.data)
@router.post('/packages/{package_id}/components',dependencies=[Depends(require_write)])
def ac(package_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_component,db,package_id,payload.data)
@router.post('/packages/{package_id}/artifacts',dependencies=[Depends(require_write)])
def aa(package_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_artifact,db,package_id,payload.data)
@router.post('/packages/{package_id}/environments',dependencies=[Depends(require_write)])
def ae(package_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_environment,db,package_id,payload.data)
@router.post('/packages/{package_id}/replay-plans',dependencies=[Depends(require_write)])
def ar(package_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_replay_plan,db,package_id,payload.data)
@router.post('/packages/{package_id}/verifications',dependencies=[Depends(require_write)])
def av(package_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_verification,db,package_id,payload.data)
@router.post('/packages/{package_id}/reviews',dependencies=[Depends(require_write)])
def rv(package_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_review,db,package_id,payload.data)
@router.get('/packages/{package_id}/bundle',dependencies=[Depends(require_read)])
def gb(package_id:str,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.bundle,db,package_id)
@router.post('/packages/{package_id}/snapshots',dependencies=[Depends(require_write)])
def ss(package_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.snapshot,db,package_id,payload.data)
@public_router.get('/packages/{package_id}/bundle',response_model=PublicEnvelope)
def pb(package_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope('data:read'))): enabled(request);return PublicEnvelope(data=call(svc.bundle,db,package_id,True),meta={'release':'2.75.0','contract':svc.CONTRACT})
