from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_notebooks as svc
router=APIRouter(prefix='/v1/research/notebooks',tags=['Research Notebook & Analytical Narrative'])
public_router=APIRouter(prefix='/api/v1/research/notebooks',tags=['Unified Public API — Research Notebooks'])
class Payload(BaseModel):data:dict[str,Any]=Field(default_factory=dict)
def enabled(request):
 if not request.app.state.settings.research_notebook_analytical_narrative_enabled:raise HTTPException(503,'Research Notebook & Analytical Narrative is disabled.')
def call(fn,*args):
 try:return fn(*args)
 except ValueError as exc:raise HTTPException(422,str(exc)) from exc
@router.get('/readiness',dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):
 enabled(request);out=svc.readiness(db);out['migration_0080_applied']='0080' in migration_status(request.app.state.database)['applied'];return out
@router.post('/projects/{project_id}/notebooks',dependencies=[Depends(require_write)])
def cn(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_notebook,db,project_id,payload.data)
@router.post('/notebooks/{notebook_id}/sections',dependencies=[Depends(require_write)])
def sec(notebook_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.add_section,db,notebook_id,payload.data)
@router.post('/notebooks/{notebook_id}/entries',dependencies=[Depends(require_write)])
def ent(notebook_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.add_entry,db,notebook_id,payload.data)
@router.post('/entries/{entry_id}/bindings',dependencies=[Depends(require_write)])
def bind(entry_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.add_binding,db,entry_id,payload.data)
@router.post('/entries/{entry_id}/citations',dependencies=[Depends(require_write)])
def cit(entry_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.add_citation,db,entry_id,payload.data)
@router.post('/notebooks/{notebook_id}/narratives',dependencies=[Depends(require_write)])
def nar(notebook_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.create_narrative,db,notebook_id,payload.data)
@router.post('/narratives/{narrative_id}/blocks',dependencies=[Depends(require_write)])
def blk(narrative_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.add_narrative_block,db,narrative_id,payload.data)
@router.get('/notebooks/{notebook_id}/bundle',dependencies=[Depends(require_read)])
def gb(notebook_id:str,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.bundle,db,notebook_id)
@router.post('/notebooks/{notebook_id}/revisions',dependencies=[Depends(require_write)])
def rev(notebook_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.add_revision,db,notebook_id,payload.data)
@router.post('/notebooks/{notebook_id}/snapshots',dependencies=[Depends(require_write)])
def snap(notebook_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)):enabled(request);return call(svc.snapshot,db,notebook_id,payload.data)
@public_router.get('/notebooks/{notebook_id}/bundle',response_model=PublicEnvelope)
def pb(notebook_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope('data:read'))):enabled(request);return PublicEnvelope(data=call(svc.bundle,db,notebook_id,True),meta={'release':'2.76.0','contract':svc.CONTRACT})
