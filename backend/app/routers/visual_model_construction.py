from __future__ import annotations
from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import visual_model_construction as svc
router=APIRouter(prefix='/v1/visual-runtime/model-construction',tags=['Visual Model Construction'])
public_router=APIRouter(prefix='/api/v1/visual-runtime/model-construction',tags=['Unified Public API — Visual Model Construction'])
class Payload(BaseModel):data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
    if not request.app.state.settings.visual_model_construction_enabled:raise HTTPException(status_code=503,detail='Visual Model Construction is disabled.')
def call(fn,*a,**kw):
    try:return fn(*a,**kw)
    except ValueError as e:raise HTTPException(status_code=422,detail=str(e)) from e
@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    enabled(request);o=svc.readiness(db);o['migration_0070_applied']='0070' in migration_status(request.app.state.database)['applied'];return o
@router.post('/canvases/{canvas_id}/constructions',dependencies=[Depends(require_write)])
def construction(canvas_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_construction,db,canvas_id,payload.data)
@router.post('/constructions/{cid}/components',dependencies=[Depends(require_write)])
def component(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_component,db,cid,payload.data)
@router.post('/constructions/{cid}/relationships',dependencies=[Depends(require_write)])
def relationship(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_relationship,db,cid,payload.data)
@router.post('/constructions/{cid}/assumptions',dependencies=[Depends(require_write)])
def assumption(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_assumption,db,cid,payload.data)
@router.post('/constructions/{cid}/constraints',dependencies=[Depends(require_write)])
def constraint(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_constraint,db,cid,payload.data)
@router.post('/constructions/{cid}/interventions',dependencies=[Depends(require_write)])
def intervention(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_intervention,db,cid,payload.data)
@router.post('/constructions/{cid}/handoffs',dependencies=[Depends(require_write)])
def handoff(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_handoff,db,cid,payload.data)
@router.get('/constructions/{cid}/bundle',dependencies=[Depends(require_read)])
def bundle(cid:str,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.construction_bundle,db,cid)
@router.post('/constructions/{cid}/snapshots',dependencies=[Depends(require_write)])
def snapshot(cid:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_snapshot,db,cid,payload.data)
@public_router.get('/constructions/{cid}/bundle',response_model=PublicEnvelope)
def public_bundle(cid:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    enabled(request);return PublicEnvelope(data=call(svc.construction_bundle,db,cid,public_only=True),meta={'api_version':'v1','request_id':request.state.request_id})
