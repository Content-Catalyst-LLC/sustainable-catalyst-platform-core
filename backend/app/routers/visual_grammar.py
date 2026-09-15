from __future__ import annotations
from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import visual_grammar as svc

router=APIRouter(prefix='/v1/visual-runtime/grammar',tags=['Analytical Visualization Grammar'])
public_router=APIRouter(prefix='/api/v1/visual-runtime/grammar',tags=['Unified Public API — Analytical Visualization Grammar'])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
    if not request.app.state.settings.analytical_visualization_grammar_enabled: raise HTTPException(status_code=503,detail='Analytical Visualization Grammar is disabled.')
def call(fn,*a,**kw):
    try:return fn(*a,**kw)
    except ValueError as e: raise HTTPException(status_code=422,detail=str(e)) from e
@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    enabled(request);o=svc.readiness(db);o['migration_0067_applied']='0067' in migration_status(request.app.state.database)['applied'];return o
@router.post('/specifications',dependencies=[Depends(require_write)])
def specification(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.create_specification,db,payload.data)
@router.post('/specifications/{sid}/data-bindings',dependencies=[Depends(require_write)])
def data_binding(sid:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_data_binding,db,sid,payload.data)
@router.post('/specifications/{sid}/marks',dependencies=[Depends(require_write)])
def mark(sid:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_mark,db,sid,payload.data)
@router.post('/specifications/{sid}/scales',dependencies=[Depends(require_write)])
def scale(sid:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_scale,db,sid,payload.data)
@router.post('/specifications/{sid}/encodings',dependencies=[Depends(require_write)])
def encoding(sid:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_encoding,db,sid,payload.data)
@router.post('/specifications/{sid}/transforms',dependencies=[Depends(require_write)])
def transform(sid:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_transform,db,sid,payload.data)
@router.post('/specifications/{sid}/guides',dependencies=[Depends(require_write)])
def guide(sid:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.add_guide,db,sid,payload.data)
@router.get('/specifications/{sid}/bundle',dependencies=[Depends(require_read)])
def bundle(sid:str,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.specification_bundle,db,sid)
@router.post('/specifications/{sid}/snapshots',dependencies=[Depends(require_write)])
def snapshot(sid:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request);return call(svc.create_snapshot,db,sid,payload.data)
@public_router.get('/specifications/{sid}/bundle',response_model=PublicEnvelope)
def public_bundle(sid:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    enabled(request);return PublicEnvelope(data=call(svc.specification_bundle,db,sid,public_only=True),meta={'api_version':'v1','request_id':request.state.request_id})
