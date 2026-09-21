from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_contributor_provenance as svc
router=APIRouter(prefix="/v1/research/contributors",tags=["Research Roles, Agents & Contributor Provenance"])
public_router=APIRouter(prefix="/api/v1/research/contributors",tags=["Unified Public API — Research Contributor Provenance"])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
 if not request.app.state.settings.research_roles_agents_contributor_provenance_enabled: raise HTTPException(503,"Research Roles, Agents & Contributor Provenance is disabled.")
def call(fn,*args):
 try:return fn(*args)
 except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)): enabled(request); out=svc.readiness(db); out["migration_0097_applied"]="0097" in migration_status(request.app.state.database)["applied"]; return out
@router.post("/contributors",dependencies=[Depends(require_write)])
def contributor(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_contributor,db,payload.data)
@router.post("/roles",dependencies=[Depends(require_write)])
def role(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_role_definition,db,payload.data)
@router.post("/assignments",dependencies=[Depends(require_write)])
def assignment(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.assign_role,db,payload.data)
@router.post("/contributions",dependencies=[Depends(require_write)])
def contribution(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_contribution,db,payload.data)
@router.post("/agents",dependencies=[Depends(require_write)])
def agent(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_agent_profile,db,payload.data)
@router.post("/agent-actions",dependencies=[Depends(require_write)])
def agent_action(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_agent_action,db,payload.data)
@router.post("/authorship",dependencies=[Depends(require_write)])
def authorship(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.assert_authorship,db,payload.data)
@router.post("/responsibility",dependencies=[Depends(require_write)])
def responsibility(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.declare_responsibility,db,payload.data)
@router.post("/reviews",dependencies=[Depends(require_write)])
def review(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.review_contribution,db,payload.data)
@router.post("/revisions",dependencies=[Depends(require_write)])
def revision(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise,db,payload.data)
@router.post("/snapshots",dependencies=[Depends(require_write)])
def snapshot(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,payload.data)
@router.get("/projects/{project_ref:path}/summary",dependencies=[Depends(require_read)])
def summary(project_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.descriptive_summary,db,project_ref)
@router.get("/projects/{project_ref:path}/lineage",dependencies=[Depends(require_read)])
def lineage(project_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,project_ref)
@router.get("/projects/{project_ref:path}/bundle",dependencies=[Depends(require_read)])
def bundle(project_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,project_ref)
@public_router.get("/projects/{project_ref:path}/summary",response_model=PublicEnvelope)
def public_summary(project_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.descriptive_summary,db,project_ref,True),meta={"release":"2.93.0","contract":svc.CONTRACT})
@public_router.get("/projects/{project_ref:path}/lineage",response_model=PublicEnvelope)
def public_lineage(project_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,project_ref,True),meta={"release":"2.93.0","contract":svc.CONTRACT})
@public_router.get("/projects/{project_ref:path}/bundle",response_model=PublicEnvelope)
def public_bundle(project_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,project_ref,True),meta={"release":"2.93.0","contract":svc.CONTRACT})
