from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_publications as svc

router=APIRouter(prefix="/v1/research/publications",tags=["Research Publication & Scholarly Output"])
public_router=APIRouter(prefix="/api/v1/research/publications",tags=["Unified Public API — Research Publication & Scholarly Output"])
class Payload(BaseModel): data: dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
    if not request.app.state.settings.reproducible_research_publication_enabled: raise HTTPException(503,"Reproducible Research Publication & Scholarly Output Engine is disabled.")
def call(fn,*args):
    try:return fn(*args)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):
    enabled(request); out=svc.readiness(db); out["migration_0085_applied"]="0085" in migration_status(request.app.state.database)["applied"]; return out
@router.post("/projects/{project_id}",dependencies=[Depends(require_write)])
def create(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_publication,db,project_id,payload.data)
@router.post("/{publication_id}/sections",dependencies=[Depends(require_write)])
def section(publication_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_section,db,publication_id,payload.data)
@router.post("/{publication_id}/references",dependencies=[Depends(require_write)])
def reference(publication_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_reference,db,publication_id,payload.data)
@router.post("/{publication_id}/citations",dependencies=[Depends(require_write)])
def citation(publication_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_citation,db,publication_id,payload.data)
@router.post("/{publication_id}/figures",dependencies=[Depends(require_write)])
def figure(publication_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_figure,db,publication_id,payload.data)
@router.post("/{publication_id}/supplements",dependencies=[Depends(require_write)])
def supplement(publication_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_supplement,db,publication_id,payload.data)
@router.post("/{publication_id}/identifiers",dependencies=[Depends(require_write)])
def identifier(publication_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_identifier,db,publication_id,payload.data)
@router.post("/{publication_id}/exports",dependencies=[Depends(require_write)])
def export(publication_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_export_manifest,db,publication_id,payload.data)
@router.post("/{publication_id}/revisions",dependencies=[Depends(require_write)])
def revise(publication_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise_publication,db,publication_id,payload.data)
@router.post("/{publication_id}/snapshots",dependencies=[Depends(require_write)])
def snapshot(publication_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,publication_id,payload.data)
@router.get("/{publication_id}/readiness",dependencies=[Depends(require_read)])
def diagnostics(publication_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.structural_readiness,db,publication_id)
@router.get("/{publication_id}/lineage",dependencies=[Depends(require_read)])
def lineage(publication_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,publication_id)
@router.get("/{publication_id}/bundle",dependencies=[Depends(require_read)])
def bundle(publication_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,publication_id)
@public_router.get("/{publication_id}/readiness",response_model=PublicEnvelope)
def public_diagnostics(publication_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.structural_readiness,db,publication_id,True),meta={"release":"2.81.0","contract":svc.CONTRACT})
@public_router.get("/{publication_id}/lineage",response_model=PublicEnvelope)
def public_lineage(publication_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,publication_id,True),meta={"release":"2.81.0","contract":svc.CONTRACT})
@public_router.get("/{publication_id}/bundle",response_model=PublicEnvelope)
def public_bundle(publication_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,publication_id,True),meta={"release":"2.81.0","contract":svc.CONTRACT})
