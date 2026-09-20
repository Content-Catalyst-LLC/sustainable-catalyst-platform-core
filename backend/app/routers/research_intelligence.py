from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_intelligence as svc

router=APIRouter(prefix='/v1/research/intelligence',tags=['Finding, Claim & Evidence Intelligence'])
public_router=APIRouter(prefix='/api/v1/research/intelligence',tags=['Unified Public API — Research Intelligence'])
class Payload(BaseModel):data:dict[str,Any]=Field(default_factory=dict)
def enabled(request):
 if not request.app.state.settings.finding_claim_evidence_intelligence_enabled:raise HTTPException(503,'Finding, Claim & Evidence Intelligence is disabled.')
def call(fn,*args):
 try:return fn(*args)
 except ValueError as exc:raise HTTPException(422,str(exc)) from exc

@router.get('/readiness',dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):
 enabled(request);out=svc.readiness(db);out['migration_0081_applied']='0081' in migration_status(request.app.state.database)['applied'];return out

@router.post('/projects/{project_id}/findings',dependencies=[Depends(require_write)])
def finding(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_finding,db,project_id,payload.data)
@router.post('/findings/{finding_id}/revisions',dependencies=[Depends(require_write)])
def finding_revision(finding_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.revise_finding,db,finding_id,payload.data)
@router.post('/projects/{project_id}/interpretations',dependencies=[Depends(require_write)])
def interpretation(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_interpretation,db,project_id,payload.data)
@router.post('/projects/{project_id}/claims',dependencies=[Depends(require_write)])
def claim(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_claim,db,project_id,payload.data)
@router.post('/claims/{claim_id}/revisions',dependencies=[Depends(require_write)])
def claim_revision(claim_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.revise_claim,db,claim_id,payload.data)
@router.post('/projects/{project_id}/evidence-links',dependencies=[Depends(require_write)])
def evidence_link(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.add_evidence_link,db,project_id,payload.data)
@router.post('/projects/{project_id}/derivations',dependencies=[Depends(require_write)])
def derivation(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.add_derivation_link,db,project_id,payload.data)
@router.get('/projects/{project_id}/contradiction-candidates',dependencies=[Depends(require_read)])
def contradiction_candidates(project_id:str,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.contradiction_candidates,db,project_id)
@router.post('/projects/{project_id}/contradictions',dependencies=[Depends(require_write)])
def contradiction(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_contradiction,db,project_id,payload.data)
@router.get('/projects/{project_id}/bundle',dependencies=[Depends(require_read)])
def project_bundle(project_id:str,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.bundle,db,project_id)
@router.post('/projects/{project_id}/snapshots',dependencies=[Depends(require_write)])
def project_snapshot(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.snapshot,db,project_id,payload.data)

@public_router.get('/projects/{project_id}/bundle',response_model=PublicEnvelope)
def public_bundle(project_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope('data:read'))):enabled(request);return PublicEnvelope(data=call(svc.bundle,db,project_id,True),meta={'release':'2.77.0','contract':svc.CONTRACT})
@public_router.get('/projects/{project_id}/contradiction-candidates',response_model=PublicEnvelope)
def public_candidates(project_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope('data:read'))):enabled(request);return PublicEnvelope(data=call(svc.contradiction_candidates,db,project_id,True),meta={'release':'2.77.0','contract':svc.CONTRACT})
