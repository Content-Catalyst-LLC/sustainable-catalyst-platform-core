from __future__ import annotations
from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..services import visual_composition as svc

router=APIRouter(prefix='/v1/visual-runtime/composition',tags=['Interactive Renderer & View Composition'])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
    if not request.app.state.settings.interactive_renderer_composition_enabled: raise HTTPException(status_code=503,detail='Interactive Renderer & View Composition is disabled.')
def call(fn,*a,**kw):
    try:return fn(*a,**kw)
    except ValueError as e: raise HTTPException(status_code=422,detail=str(e)) from e
@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    enabled(request);o=svc.readiness(db);o['migration_0066_applied']='0066' in migration_status(request.app.state.database)['applied'];return o
@router.post('/renderers',dependencies=[Depends(require_write)])
def renderer(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.create_renderer_profile,db,payload.data)
@router.post('/scenes/{scene_id}/compositions',dependencies=[Depends(require_write)])
def composition(scene_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.create_composition,db,scene_id,payload.data)
@router.post('/compositions/{cid}/assignments',dependencies=[Depends(require_write)])
def assignment(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.assign_view,db,cid,payload.data)
@router.post('/compositions/{cid}/link-groups',dependencies=[Depends(require_write)])
def link_group(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_link_group,db,cid,payload.data)
@router.post('/compositions/{cid}/interaction-states',dependencies=[Depends(require_write)])
def state(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_interaction_state,db,cid,payload.data)
@router.post('/compositions/{cid}/renderer-resolutions',dependencies=[Depends(require_write)])
def resolution(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.resolve_renderer,db,cid,payload.data)
@router.get('/compositions/{cid}/bundle',dependencies=[Depends(require_read)])
def bundle(cid:str,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.composition_bundle,db,cid)
@router.post('/compositions/{cid}/snapshots',dependencies=[Depends(require_write)])
def snapshot(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.create_snapshot,db,cid,payload.data)
