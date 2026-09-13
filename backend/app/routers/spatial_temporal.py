from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..services import spatial_temporal as st

router=APIRouter(prefix='/v1/spatial-temporal',tags=['Spatial & Temporal Visual Reasoning'])
public_router=APIRouter(prefix='/api/v1/spatial-temporal',tags=['Public Spatial & Temporal Visual Reasoning'])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def bad(exc): return exc if isinstance(exc,HTTPException) else HTTPException(status_code=422,detail=str(exc))
def enabled(request):
    if not request.app.state.settings.spatial_temporal_visual_reasoning_enabled: raise HTTPException(status_code=404,detail='Spatial & Temporal Visual Reasoning is disabled.')
def public_enabled(request):
    enabled(request)
    if not request.app.state.settings.spatial_temporal_public_metadata_enabled: raise HTTPException(status_code=404,detail='Public spatial-temporal metadata is disabled.')

@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    enabled(request);d=st.readiness(db);d.update({'release':request.app.state.settings.version,'enabled':True});return d
@router.post('/scenes',dependencies=[Depends(require_write)])
def create_scene(request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return st.create_scene(db,payload.data)
    except Exception as exc:raise bad(exc)
@router.get('/scenes',dependencies=[Depends(require_read)])
def scenes(request:Request,project_entity_id:str|None=None,visibility:str|None=None,db:Session=Depends(get_session)):
    enabled(request);return {'items':st.list_scenes(db,project_entity_id=project_entity_id,visibility=visibility)}
@router.get('/scenes/{scene_id}',dependencies=[Depends(require_read)])
def scene(request:Request,scene_id:str,db:Session=Depends(get_session)):
    enabled(request);return st.read_scene(db,scene_id)
@router.post('/scenes/{scene_id}/features',dependencies=[Depends(require_write)])
def feature(request:Request,scene_id:str,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return st.add_feature(db,scene_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/scenes/{scene_id}/events',dependencies=[Depends(require_write)])
def event(request:Request,scene_id:str,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return st.add_event(db,scene_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/scenes/{scene_id}/trajectories',dependencies=[Depends(require_write)])
def trajectory(request:Request,scene_id:str,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return st.add_trajectory(db,scene_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/trajectories/{trajectory_id}/points',dependencies=[Depends(require_write)])
def trajectory_point(request:Request,trajectory_id:str,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return st.add_trajectory_point(db,trajectory_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.get('/trajectories/{trajectory_id}/summary',dependencies=[Depends(require_read)])
def trajectory_summary(request:Request,trajectory_id:str,db:Session=Depends(get_session)):
    enabled(request);return st.trajectory_summary(db,trajectory_id)
@router.post('/scenes/{scene_id}/changes',dependencies=[Depends(require_write)])
def change(request:Request,scene_id:str,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return st.add_change(db,scene_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/scenes/{scene_id}/views',dependencies=[Depends(require_write)])
def view(request:Request,scene_id:str,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return st.add_view(db,scene_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.get('/scenes/{scene_id}/timeline',dependencies=[Depends(require_read)])
def timeline(request:Request,scene_id:str,db:Session=Depends(get_session)):
    enabled(request);return st.timeline(db,scene_id)
@router.get('/scenes/{scene_id}/visualization',dependencies=[Depends(require_read)])
def visualization(request:Request,scene_id:str,view_id:str|None=None,db:Session=Depends(get_session)):
    enabled(request)
    try:return st.visualization_spec(db,scene_id,view_id)
    except Exception as exc:raise bad(exc)
@router.post('/scenes/{scene_id}/runtime-handoff',dependencies=[Depends(require_write)])
def runtime_handoff(request:Request,scene_id:str,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return st.runtime_handoff(db,scene_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.get('/scenes/{scene_id}/bundle',dependencies=[Depends(require_read)])
def bundle(request:Request,scene_id:str,db:Session=Depends(get_session)):
    enabled(request);return st.bundle(db,scene_id)

@public_router.get('/readiness')
def public_readiness(request:Request,ctx:PublicApiContext=Depends(require_public_scope('core.read')),db:Session=Depends(get_session)):
    public_enabled(request);d=st.readiness(db);d.update({'release':request.app.state.settings.version,'enabled':True});return d
@public_router.get('/scenes')
def public_scenes(request:Request,project_entity_id:str|None=None,ctx:PublicApiContext=Depends(require_public_scope('core.read')),db:Session=Depends(get_session)):
    public_enabled(request);return {'items':st.list_scenes(db,project_entity_id=project_entity_id,public_only=True)}
@public_router.get('/scenes/{scene_id}/bundle')
def public_bundle(request:Request,scene_id:str,ctx:PublicApiContext=Depends(require_public_scope('core.read')),db:Session=Depends(get_session)):
    public_enabled(request);return st.bundle(db,scene_id,public_only=True)
