from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_methodology as svc
router=APIRouter(prefix='/v1/research/methodology',tags=['Methodology & Analysis Run Registry'])
public_router=APIRouter(prefix='/api/v1/research/methodology',tags=['Unified Public API — Research Methodology'])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def enabled(request):
 if not request.app.state.settings.methodology_analysis_run_registry_enabled: raise HTTPException(503,'Methodology & Analysis Run Registry is disabled.')
def call(fn,*args):
 try:return fn(*args)
 except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.get('/readiness',dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):
 enabled(request);out=svc.readiness(db);out['migration_0078_applied']='0078' in migration_status(request.app.state.database)['applied'];return out
@router.post('/projects/{project_id}/methodologies',dependencies=[Depends(require_write)])
def cm(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.create_methodology,db,project_id,payload.data)
@router.post('/methodologies/{methodology_id}/versions',dependencies=[Depends(require_write)])
def av(methodology_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_version,db,methodology_id,payload.data)
@router.post('/methodologies/{methodology_id}/variables',dependencies=[Depends(require_write)])
def vv(methodology_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_variable,db,methodology_id,payload.data)
@router.post('/methodologies/{methodology_id}/assumptions',dependencies=[Depends(require_write)])
def aa(methodology_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_assumption,db,methodology_id,payload.data)
@router.post('/methodologies/{methodology_id}/parameters',dependencies=[Depends(require_write)])
def ap(methodology_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_parameter,db,methodology_id,payload.data)
@router.post('/projects/{project_id}/environments',dependencies=[Depends(require_write)])
def ae(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_environment,db,project_id,payload.data)
@router.post('/projects/{project_id}/runs',dependencies=[Depends(require_write)])
def cr(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.create_run,db,project_id,payload.data)
@router.post('/runs/{run_id}/inputs',dependencies=[Depends(require_write)])
def ai(run_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_input,db,run_id,payload.data)
@router.post('/runs/{run_id}/outputs',dependencies=[Depends(require_write)])
def ao(run_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_output,db,run_id,payload.data)
@router.get('/projects/{project_id}/bundle',dependencies=[Depends(require_read)])
def gb(project_id:str,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.bundle,db,project_id)
@router.post('/projects/{project_id}/snapshots',dependencies=[Depends(require_write)])
def ss(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.snapshot,db,project_id,payload.data)
@public_router.get('/projects/{project_id}/bundle',response_model=PublicEnvelope)
def pb(project_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope('data:read'))): enabled(request);return PublicEnvelope(data=call(svc.bundle,db,project_id,True),meta={'release':'2.74.0','contract':svc.CONTRACT})
