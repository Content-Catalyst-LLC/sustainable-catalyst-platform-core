from __future__ import annotations
from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import visual_linked_views as svc
router=APIRouter(prefix='/v1/visual-runtime/linked-views',tags=['Linked Views & Cross-Filtering'])
public_router=APIRouter(prefix='/api/v1/visual-runtime/linked-views',tags=['Unified Public API — Linked Views & Cross-Filtering'])
class Payload(BaseModel):data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
    if not request.app.state.settings.linked_views_cross_filtering_enabled:raise HTTPException(status_code=503,detail='Linked Views & Cross-Filtering is disabled.')
def call(fn,*a,**kw):
    try:return fn(*a,**kw)
    except ValueError as e:raise HTTPException(status_code=422,detail=str(e)) from e
@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    enabled(request);o=svc.readiness(db);o['migration_0068_applied']='0068' in migration_status(request.app.state.database)['applied'];return o
@router.post('/compositions/{cid}/link-policies',dependencies=[Depends(require_write)])
def policy(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_link_policy,db,cid,payload.data)
@router.post('/compositions/{cid}/selection-sets',dependencies=[Depends(require_write)])
def selection(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_selection_set,db,cid,payload.data)
@router.post('/compositions/{cid}/cross-filters',dependencies=[Depends(require_write)])
def cross_filter(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_cross_filter,db,cid,payload.data)
@router.post('/compositions/{cid}/brush-ranges',dependencies=[Depends(require_write)])
def brush(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_brush_range,db,cid,payload.data)
@router.post('/compositions/{cid}/focus-highlights',dependencies=[Depends(require_write)])
def focus(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_focus_highlight,db,cid,payload.data)
@router.post('/compositions/{cid}/propagations',dependencies=[Depends(require_write)])
def propagation(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.record_propagation,db,cid,payload.data)
@router.get('/compositions/{cid}/bundle',dependencies=[Depends(require_read)])
def bundle(cid:str,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.composition_bundle,db,cid)
@router.post('/compositions/{cid}/snapshots',dependencies=[Depends(require_write)])
def snapshot(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_snapshot,db,cid,payload.data)
@public_router.get('/compositions/{cid}/bundle',response_model=PublicEnvelope)
def public_bundle(cid:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    enabled(request);return PublicEnvelope(data=call(svc.composition_bundle,db,cid,public_only=True),meta={'api_version':'v1','request_id':request.state.request_id})
