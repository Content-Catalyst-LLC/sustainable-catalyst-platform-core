from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_programs as svc

router = APIRouter(prefix="/v1/research/programs", tags=["Research Program & Longitudinal Knowledge Graph"])
public_router = APIRouter(prefix="/api/v1/research/programs", tags=["Unified Public API — Research Program & Longitudinal Knowledge Graph"])

class Payload(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)

def enabled(request: Request):
    if not request.app.state.settings.research_program_longitudinal_knowledge_graph_enabled:
        raise HTTPException(503, "Research Program & Longitudinal Knowledge Graph is disabled.")

def call(fn,*args):
    try: return fn(*args)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc

@router.get("/readiness", dependencies=[Depends(require_read)])
def ready(request: Request, db: Session=Depends(get_session)):
    enabled(request); out=svc.readiness(db); out["migration_0088_applied"]="0088" in migration_status(request.app.state.database)["applied"]; return out

@router.post("", dependencies=[Depends(require_write)])
def create(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_program,db,payload.data)

@router.post("/{program_id}/projects", dependencies=[Depends(require_write)])
def add_project(program_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_project,db,program_id,payload.data)

@router.post("/{program_id}/objectives", dependencies=[Depends(require_write)])
def add_objective(program_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_objective,db,program_id,payload.data)

@router.post("/{program_id}/milestones", dependencies=[Depends(require_write)])
def add_milestone(program_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_milestone,db,program_id,payload.data)

@router.post("/{program_id}/longitudinal/nodes", dependencies=[Depends(require_write)])
def add_node(program_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_node,db,program_id,payload.data)

@router.post("/{program_id}/longitudinal/edges", dependencies=[Depends(require_write)])
def add_edge(program_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_edge,db,program_id,payload.data)

@router.post("/{program_id}/knowledge-states", dependencies=[Depends(require_write)])
def add_state(program_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_knowledge_state,db,program_id,payload.data)

@router.post("/{program_id}/evolution-events", dependencies=[Depends(require_write)])
def add_event(program_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_evolution_event,db,program_id,payload.data)

@router.post("/{program_id}/revisions", dependencies=[Depends(require_write)])
def revise(program_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise_program,db,program_id,payload.data)

@router.post("/{program_id}/snapshots", dependencies=[Depends(require_write)])
def snapshot(program_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,program_id,payload.data)

@router.get("/{program_id}/summary", dependencies=[Depends(require_read)])
def summary(program_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.descriptive_summary,db,program_id)

@router.get("/{program_id}/graph", dependencies=[Depends(require_read)])
def graph(program_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.graph,db,program_id)

@router.get("/{program_id}/timeline", dependencies=[Depends(require_read)])
def timeline(program_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.timeline,db,program_id)

@router.get("/{program_id}/lineage", dependencies=[Depends(require_read)])
def lineage(program_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,program_id)

@router.get("/{program_id}/bundle", dependencies=[Depends(require_read)])
def bundle(program_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,program_id)

@public_router.get("/{program_id}/summary", response_model=PublicEnvelope)
def public_summary(program_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.descriptive_summary,db,program_id,True),meta={"release":"2.84.0","contract":svc.CONTRACT})

@public_router.get("/{program_id}/graph", response_model=PublicEnvelope)
def public_graph(program_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.graph,db,program_id,True),meta={"release":"2.84.0","contract":svc.CONTRACT})

@public_router.get("/{program_id}/timeline", response_model=PublicEnvelope)
def public_timeline(program_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.timeline,db,program_id,True),meta={"release":"2.84.0","contract":svc.CONTRACT})

@public_router.get("/{program_id}/lineage", response_model=PublicEnvelope)
def public_lineage(program_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,program_id,True),meta={"release":"2.84.0","contract":svc.CONTRACT})

@public_router.get("/{program_id}/bundle", response_model=PublicEnvelope)
def public_bundle(program_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,program_id,True),meta={"release":"2.84.0","contract":svc.CONTRACT})
