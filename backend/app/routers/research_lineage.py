from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_lineage as svc

router=APIRouter(prefix="/v1/research/lineage",tags=["Research Lineage & Provenance Graph"])
public_router=APIRouter(prefix="/api/v1/research/lineage",tags=["Unified Public API — Research Lineage"])
class Payload(BaseModel): data: dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
    if not request.app.state.settings.research_lineage_provenance_graph_enabled: raise HTTPException(503,"Research Lineage & Provenance Graph is disabled.")
def call(fn,*args):
    try:return fn(*args)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc

@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):
    enabled(request); out=svc.readiness(db); out["migration_0077_applied"]="0077" in migration_status(request.app.state.database)["applied"]; return out
@router.post("/projects/{project_id}/graphs",dependencies=[Depends(require_write)])
def create_graph(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_graph,db,project_id,payload.data)
@router.post("/graphs/{graph_id}/nodes",dependencies=[Depends(require_write)])
def add_node(graph_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_node,db,graph_id,payload.data)
@router.post("/graphs/{graph_id}/edges",dependencies=[Depends(require_write)])
def add_edge(graph_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_edge,db,graph_id,payload.data)
@router.post("/graphs/{graph_id}/activities",dependencies=[Depends(require_write)])
def add_activity(graph_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_activity,db,graph_id,payload.data)
@router.post("/graphs/{graph_id}/transformations",dependencies=[Depends(require_write)])
def add_transformation(graph_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_transformation,db,graph_id,payload.data)
@router.post("/graphs/{graph_id}/source-bindings",dependencies=[Depends(require_write)])
def add_source_binding(graph_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_source_binding,db,graph_id,payload.data)
@router.post("/graphs/{graph_id}/traces",dependencies=[Depends(require_write)])
def add_trace(graph_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_trace,db,graph_id,payload.data)
@router.get("/graphs/{graph_id}/bundle",dependencies=[Depends(require_read)])
def get_bundle(graph_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,graph_id)
@router.post("/graphs/{graph_id}/snapshots",dependencies=[Depends(require_write)])
def add_snapshot(graph_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,graph_id,payload.data)
@public_router.get("/graphs/{graph_id}/bundle",response_model=PublicEnvelope)
def public_bundle(graph_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    enabled(request); return PublicEnvelope(data=call(svc.bundle,db,graph_id,True),meta={"release":"2.73.0","contract":svc.CONTRACT})
