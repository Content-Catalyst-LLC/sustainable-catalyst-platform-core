from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import visual_runtime as svc

router=APIRouter(prefix="/v1/visual-runtime",tags=["Visual Reasoning Runtime & Scene Graph"])
public_router=APIRouter(prefix="/api/v1/visual-runtime",tags=["Unified Public API — Visual Runtime"])

class Payload(BaseModel):
    data: dict[str,Any] = Field(default_factory=dict)

def enabled(request:Request):
    if not request.app.state.settings.visual_reasoning_runtime_enabled:
        raise HTTPException(status_code=503,detail="Visual Reasoning Runtime is disabled.")

def call(fn,*args,**kwargs):
    try:return fn(*args,**kwargs)
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc

@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    enabled(request); out=svc.readiness(db); out['migration_0065_applied']='0065' in migration_status(request.app.state.database)['applied']; return out

@router.post('/scenes',dependencies=[Depends(require_write)])
def create_scene(payload:Payload,request:Request,db:Session=Depends(get_session)):
    enabled(request);return call(svc.create_scene,db,payload.data)

@router.get('/scenes',dependencies=[Depends(require_read)])
def list_scenes(request:Request,project_entity_id:str|None=None,limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    enabled(request);items,total=svc.list_scenes(db,project_entity_id,limit,offset);return {'items':items,'total':total,'limit':limit,'offset':offset}

@router.post('/scenes/{scene_id}/layers',dependencies=[Depends(require_write)])
def layer(scene_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):
    enabled(request);return call(svc.add_layer,db,scene_id,payload.data)

@router.post('/scenes/{scene_id}/nodes',dependencies=[Depends(require_write)])
def node(scene_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):
    enabled(request);return call(svc.add_node,db,scene_id,payload.data)

@router.post('/scenes/{scene_id}/edges',dependencies=[Depends(require_write)])
def edge(scene_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):
    enabled(request);return call(svc.add_edge,db,scene_id,payload.data)

@router.post('/scenes/{scene_id}/annotations',dependencies=[Depends(require_write)])
def annotation(scene_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):
    enabled(request);return call(svc.add_annotation,db,scene_id,payload.data)

@router.post('/scenes/{scene_id}/views',dependencies=[Depends(require_write)])
def view(scene_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):
    enabled(request);return call(svc.add_view,db,scene_id,payload.data)

@router.post('/scenes/{scene_id}/bindings',dependencies=[Depends(require_write)])
def binding(scene_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):
    enabled(request);return call(svc.add_binding,db,scene_id,payload.data)

@router.get('/scenes/{scene_id}/bundle',dependencies=[Depends(require_read)])
def bundle(scene_id:str,request:Request,db:Session=Depends(get_session)):
    enabled(request);return call(svc.scene_bundle,db,scene_id)

@router.post('/scenes/{scene_id}/snapshots',dependencies=[Depends(require_write)])
def snapshot(scene_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):
    enabled(request);return call(svc.create_snapshot,db,scene_id,payload.data)

@public_router.get('/scenes/{scene_id}/bundle',response_model=PublicEnvelope)
def public_bundle(scene_id:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    enabled(request);return PublicEnvelope(data=call(svc.scene_bundle,db,scene_id,public_only=True),meta={'api_version':'v1','request_id':request.state.request_id})
