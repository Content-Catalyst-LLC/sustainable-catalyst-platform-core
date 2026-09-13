from __future__ import annotations
from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Query,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import model_canvas

router=APIRouter(prefix='/v1/model-canvases',tags=['Interactive Model Canvas'])
public_router=APIRouter(prefix='/api/v1/model-canvases',tags=['Unified Public API — Interactive Model Canvas'])
class CanvasCreate(BaseModel):
    name:str=Field(min_length=1,max_length=300);slug:str|None=None;description:str|None=None;entity_id:str|None=None;visibility:str='public';status:str='active';reasoning_purpose:str='explore';project_entity_id:str;model_entity_id:str;model_version_entity_id:str|None=None;canvas_state:str='draft';interaction_mode:str='inspect-configure';execution_target:str='external';lens:dict[str,Any]=Field(default_factory=dict);filters:dict[str,Any]=Field(default_factory=dict);assumptions:list[Any]=Field(default_factory=list);metadata:dict[str,Any]=Field(default_factory=dict);created_by:str='operator'
class ChildCreate(BaseModel):data:dict[str,Any]=Field(default_factory=dict)
class CompileSpec(BaseModel):spec_key:str='model-canvas-default';revision:int|None=None;spec_kind:str='diagram';title:str|None=None;preferred_renderer_key:str|None=None;renderer_policy:str='compatible';layout_constraints:dict[str,Any]=Field(default_factory=dict);metadata:dict[str,Any]=Field(default_factory=dict);created_by:str='operator'
def bad(exc):return exc if isinstance(exc,HTTPException) else HTTPException(status_code=422,detail=str(exc))
def public_enabled(request):
    if not request.app.state.settings.interactive_model_canvas_public_metadata_enabled:raise HTTPException(status_code=404,detail='Interactive Model Canvas public metadata API is disabled.')
@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    data=model_canvas.readiness(db);m=migration_status(request.app.state.database);data.update({'release':request.app.state.settings.version,'enabled':request.app.state.settings.interactive_model_canvas_enabled,'migration_0037_applied':'0037' in m['applied']});return data
@router.post('',dependencies=[Depends(require_write)])
def create(payload:CanvasCreate,request:Request,db:Session=Depends(get_session)):
    if not request.app.state.settings.interactive_model_canvas_enabled:raise HTTPException(status_code=503,detail='Interactive Model Canvas is disabled.')
    try:return model_canvas.create_canvas(db,payload.model_dump(),release=request.app.state.settings.version)
    except Exception as exc:raise bad(exc)
@router.get('',dependencies=[Depends(require_read)])
def list_all(request:Request,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    items,total=model_canvas.list_canvases(db,limit=min(limit,request.app.state.settings.page_size_max),offset=offset);return {'items':items,'total':total,'limit':limit,'offset':offset}
@router.get('/{visual_entity_id}',dependencies=[Depends(require_read)])
def detail(visual_entity_id:str,db:Session=Depends(get_session)):return model_canvas.read_canvas(db,visual_entity_id)
@router.get('/{visual_entity_id}/bundle',dependencies=[Depends(require_read)])
def bundle(visual_entity_id:str,db:Session=Depends(get_session)):return model_canvas.bundle(db,visual_entity_id)
@router.get('/{visual_entity_id}/validate',dependencies=[Depends(require_read)])
def validate(visual_entity_id:str,db:Session=Depends(get_session)):return model_canvas.validate_structure(db,visual_entity_id)
@router.post('/{visual_entity_id}/nodes',dependencies=[Depends(require_write)])
def node(visual_entity_id:str,payload:ChildCreate,db:Session=Depends(get_session)):
    try:return model_canvas.add_node(db,visual_entity_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/{visual_entity_id}/edges',dependencies=[Depends(require_write)])
def edge(visual_entity_id:str,payload:ChildCreate,db:Session=Depends(get_session)):
    try:return model_canvas.add_edge(db,visual_entity_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/{visual_entity_id}/controls',dependencies=[Depends(require_write)])
def control(visual_entity_id:str,payload:ChildCreate,db:Session=Depends(get_session)):
    try:return model_canvas.add_control(db,visual_entity_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/{visual_entity_id}/states',dependencies=[Depends(require_write)])
def state(visual_entity_id:str,payload:ChildCreate,db:Session=Depends(get_session)):
    try:return model_canvas.save_state(db,visual_entity_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/{visual_entity_id}/views',dependencies=[Depends(require_write)])
def view(visual_entity_id:str,payload:ChildCreate,db:Session=Depends(get_session)):
    try:return model_canvas.add_view(db,visual_entity_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/{visual_entity_id}/compile-specification',dependencies=[Depends(require_write)])
def compile_spec(visual_entity_id:str,payload:CompileSpec,db:Session=Depends(get_session)):
    try:return model_canvas.compile_specification(db,visual_entity_id,payload.model_dump())
    except Exception as exc:raise bad(exc)
@public_router.get('/readiness',response_model=PublicEnvelope)
def public_readiness(request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):public_enabled(request);data=model_canvas.readiness(db);data.update({'release':request.app.state.settings.version,'enabled':request.app.state.settings.interactive_model_canvas_enabled});return PublicEnvelope(data=data,meta={'api_version':'v1','request_id':request.state.request_id})
@public_router.get('',response_model=PublicEnvelope)
def public_list(request:Request,limit:int=Query(100,ge=1),offset:int=Query(0,ge=0),ctx:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):
    public_enabled(request);limit=min(limit,ctx.plan.max_page_size,request.app.state.settings.page_size_max);items,total=model_canvas.list_canvases(db,public_only=True,limit=limit,offset=offset);return PublicEnvelope(data=items,meta={'api_version':'v1','request_id':request.state.request_id,'pagination':{'total':total,'limit':limit,'offset':offset}})
@public_router.get('/{visual_entity_id}/bundle',response_model=PublicEnvelope)
def public_bundle(visual_entity_id:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):public_enabled(request);return PublicEnvelope(data=model_canvas.bundle(db,visual_entity_id,public_only=True),meta={'api_version':'v1','request_id':request.state.request_id})
@public_router.get('/{visual_entity_id}',response_model=PublicEnvelope)
def public_detail(visual_entity_id:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):public_enabled(request);return PublicEnvelope(data=model_canvas.read_canvas(db,visual_entity_id,public_only=True),meta={'api_version':'v1','request_id':request.state.request_id})
