from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import visual_forensics_workbench as svc
router=APIRouter(prefix='/v1/visual-runtime/forensics',tags=['Visual Forensics Workbench'])
public_router=APIRouter(prefix='/api/v1/visual-runtime/forensics',tags=['Unified Public API — Visual Forensics Workbench'])
class Payload(BaseModel):data:dict[str,Any]=Field(default_factory=dict)
def enabled(r):
 if not r.app.state.settings.visual_forensics_workbench_enabled:raise HTTPException(503,'Visual Forensics Workbench is disabled.')
def call(fn,*a):
 try:return fn(*a)
 except ValueError as e:raise HTTPException(422,str(e)) from e
@router.get('/readiness',dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):enabled(request);o=svc.readiness(db);o['migration_0072_applied']='0072' in migration_status(request.app.state.database)['applied'];return o
@router.post('/compositions/{cid}/workspaces',dependencies=[Depends(require_write)])
def workspace(cid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_workspace,db,cid,p.data)
@router.post('/workspaces/{wid}/evidence-bindings',dependencies=[Depends(require_write)])
def evidence_route(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.evidence,db,wid,p.data)
@router.post('/workspaces/{wid}/claim-overlays',dependencies=[Depends(require_write)])
def claims_route(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.claims,db,wid,p.data)
@router.post('/workspaces/{wid}/timeline-layers',dependencies=[Depends(require_write)])
def timeline_route(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.timeline,db,wid,p.data)
@router.post('/workspaces/{wid}/spatial-temporal-layers',dependencies=[Depends(require_write)])
def spatial_route(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.spatial,db,wid,p.data)
@router.post('/workspaces/{wid}/media-layers',dependencies=[Depends(require_write)])
def media_route(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.media,db,wid,p.data)
@router.post('/workspaces/{wid}/reconstruction-bindings',dependencies=[Depends(require_write)])
def reconstruction_route(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.reconstruction,db,wid,p.data)
@router.post('/workspaces/{wid}/documentary-bindings',dependencies=[Depends(require_write)])
def documentary_route(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.documentary,db,wid,p.data)
@router.post('/workspaces/{wid}/graph-bindings',dependencies=[Depends(require_write)])
def graph_route(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.graph,db,wid,p.data)
@router.get('/workspaces/{wid}/bundle',dependencies=[Depends(require_read)])
def bundle(wid:str,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.bundle,db,wid)
@router.post('/workspaces/{wid}/snapshots',dependencies=[Depends(require_write)])
def snapshot(wid:str,p:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.snapshot,db,wid,p.data)
@public_router.get('/workspaces/{wid}/bundle',response_model=PublicEnvelope)
def public_bundle(wid:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope('read:visual'))):enabled(request);return PublicEnvelope(data=call(svc.bundle,db,wid,True),meta={'release':'2.68.0','contract':svc.CONTRACT})
