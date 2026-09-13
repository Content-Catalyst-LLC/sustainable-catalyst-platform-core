from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import causal_systems as cs
router=APIRouter(prefix='/v1/causal-systems',tags=['Causal Systems Explorer'])
public_router=APIRouter(prefix='/api/v1/causal-systems',tags=['Public Causal Systems Explorer'])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def bad(exc): return exc if isinstance(exc,HTTPException) else HTTPException(status_code=422,detail=str(exc))
def enabled(request):
    if not request.app.state.settings.causal_systems_explorer_enabled: raise HTTPException(status_code=404,detail='Causal Systems Explorer is disabled.')
def public_enabled(request):
    enabled(request)
    if not request.app.state.settings.causal_systems_public_metadata_enabled: raise HTTPException(status_code=404,detail='Public causal metadata is disabled.')
@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    enabled(request);d=cs.readiness(db);d.update({'release':request.app.state.settings.version,'enabled':True});return d
@router.post('/graphs',dependencies=[Depends(require_write)])
def create_graph(request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return cs.create_graph(db,payload.data)
    except Exception as exc:raise bad(exc)
@router.get('/graphs',dependencies=[Depends(require_read)])
def graphs(limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    items,total=cs.list_graphs(db,limit=limit,offset=offset);return {'items':items,'total':total,'limit':limit,'offset':offset}
@router.get('/graphs/{graph_id}',dependencies=[Depends(require_read)])
def graph(graph_id:str,db:Session=Depends(get_session)):return cs.read_graph(db,graph_id)
@router.get('/graphs/{graph_id}/bundle',dependencies=[Depends(require_read)])
def bundle(graph_id:str,db:Session=Depends(get_session)):return cs.bundle(db,graph_id)
@router.post('/graphs/{graph_id}/variables',dependencies=[Depends(require_write)])
def variable(graph_id:str,payload:Payload,db:Session=Depends(get_session)):
    try:return cs.add_variable(db,graph_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/graphs/{graph_id}/edges',dependencies=[Depends(require_write)])
def edge(graph_id:str,payload:Payload,db:Session=Depends(get_session)):
    try:return cs.add_edge(db,graph_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.get('/graphs/{graph_id}/validate',dependencies=[Depends(require_read)])
def validate(graph_id:str,db:Session=Depends(get_session)):return cs.validate_graph(db,graph_id)
@router.get('/graphs/{graph_id}/paths',dependencies=[Depends(require_read)])
def paths(graph_id:str,source_variable_id:str,target_variable_id:str,db:Session=Depends(get_session)):return cs.paths(db,graph_id,source_variable_id,target_variable_id)
@router.get('/graphs/{graph_id}/adjustment-candidates',dependencies=[Depends(require_read)])
def adjustment(graph_id:str,treatment_variable_id:str,outcome_variable_id:str,db:Session=Depends(get_session)):return cs.adjustment_candidates(db,graph_id,treatment_variable_id,outcome_variable_id)
@router.post('/graphs/{graph_id}/interventions',dependencies=[Depends(require_write)])
def intervention(graph_id:str,payload:Payload,db:Session=Depends(get_session)):
    try:return cs.add_intervention(db,graph_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/graphs/{graph_id}/identifications',dependencies=[Depends(require_write)])
def identification(graph_id:str,payload:Payload,db:Session=Depends(get_session)):
    try:return cs.add_identification(db,graph_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/graphs/{graph_id}/estimates',dependencies=[Depends(require_write)])
def estimate(graph_id:str,payload:Payload,db:Session=Depends(get_session)):
    try:return cs.add_estimate(db,graph_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/graphs/{graph_id}/diagnostics',dependencies=[Depends(require_write)])
def diagnostic(graph_id:str,payload:Payload,db:Session=Depends(get_session)):
    try:return cs.add_diagnostic(db,graph_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post('/graphs/{graph_id}/runtime-handoff',dependencies=[Depends(require_write)])
def handoff(graph_id:str,payload:Payload,db:Session=Depends(get_session)):
    try:return cs.runtime_handoff(db,graph_id,payload.data)
    except Exception as exc:raise bad(exc)
@public_router.get('/readiness',response_model=PublicEnvelope)
def public_readiness(request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    public_enabled(request);d=cs.readiness(db);d.update({'release':request.app.state.settings.version,'enabled':True});return PublicEnvelope(data=d,meta={'api_version':'v1','request_id':request.state.request_id})
@public_router.get('/graphs',response_model=PublicEnvelope)
def public_graphs(request:Request,limit:int=Query(100,ge=1),offset:int=Query(0,ge=0),ctx:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):
    public_enabled(request);limit=min(limit,ctx.plan.max_page_size,request.app.state.settings.page_size_max);items,total=cs.list_graphs(db,public_only=True,limit=limit,offset=offset);return PublicEnvelope(data=items,meta={'api_version':'v1','request_id':request.state.request_id,'pagination':{'total':total,'limit':limit,'offset':offset}})
@public_router.get('/graphs/{graph_id}/bundle',response_model=PublicEnvelope)
def public_bundle(graph_id:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope('data:read'))):
    public_enabled(request);return PublicEnvelope(data=cs.bundle(db,graph_id,public_only=True),meta={'api_version':'v1','request_id':request.state.request_id})
