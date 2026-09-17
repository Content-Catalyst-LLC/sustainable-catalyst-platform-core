from __future__ import annotations
from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import visual_query_exploration as svc
router=APIRouter(prefix='/v1/visual-runtime/query',tags=['Visual Query & Exploration Engine'])
public_router=APIRouter(prefix='/api/v1/visual-runtime/query',tags=['Unified Public API — Visual Query & Exploration Engine'])
class Payload(BaseModel):data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
    if not request.app.state.settings.visual_query_exploration_enabled:raise HTTPException(status_code=503,detail='Visual Query & Exploration Engine is disabled.')
def call(fn,*a,**kw):
    try:return fn(*a,**kw)
    except ValueError as e:raise HTTPException(status_code=422,detail=str(e)) from e
@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    enabled(request);o=svc.readiness(db);o['migration_0069_applied']='0069' in migration_status(request.app.state.database)['applied'];return o
@router.post('/compositions/{cid}/sessions',dependencies=[Depends(require_write)])
def session(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_session,db,cid,payload.data)
@router.post('/sessions/{sid}/targets',dependencies=[Depends(require_write)])
def target(sid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_target,db,sid,payload.data)
@router.post('/sessions/{sid}/queries',dependencies=[Depends(require_write)])
def query(sid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_query,db,sid,payload.data)
@router.post('/queries/{qid}/predicates',dependencies=[Depends(require_write)])
def predicate(qid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_predicate,db,qid,payload.data)
@router.post('/queries/{qid}/traversals',dependencies=[Depends(require_write)])
def traversal(qid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_traversal,db,qid,payload.data)
@router.post('/queries/{qid}/results',dependencies=[Depends(require_write)])
def result(qid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_result_binding,db,qid,payload.data)
@router.post('/sessions/{sid}/saved-states',dependencies=[Depends(require_write)])
def saved_state(sid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_saved_state,db,sid,payload.data)
@router.get('/sessions/{sid}/bundle',dependencies=[Depends(require_read)])
def bundle(sid:str,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.session_bundle,db,sid)
@router.post('/sessions/{sid}/snapshots',dependencies=[Depends(require_write)])
def snapshot(sid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_snapshot,db,sid,payload.data)
@public_router.get('/sessions/{sid}/bundle',response_model=PublicEnvelope)
def public_bundle(sid:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    enabled(request);return PublicEnvelope(data=call(svc.session_bundle,db,sid,public_only=True),meta={'api_version':'v1','request_id':request.state.request_id})
