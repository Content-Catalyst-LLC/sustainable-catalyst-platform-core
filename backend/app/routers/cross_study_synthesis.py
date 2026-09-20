from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import cross_study_synthesis as svc

router = APIRouter(prefix="/v1/research/evidence-synthesis", tags=["Cross-Study Evidence Synthesis & Meta-Research"])
public_router = APIRouter(prefix="/api/v1/research/evidence-synthesis", tags=["Unified Public API — Cross-Study Evidence Synthesis & Meta-Research"])

class Payload(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)

def enabled(request: Request):
    if not request.app.state.settings.cross_study_evidence_synthesis_enabled:
        raise HTTPException(503, "Cross-Study Evidence Synthesis & Meta-Research is disabled.")

def call(fn,*args):
    try: return fn(*args)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc

@router.get("/readiness", dependencies=[Depends(require_read)])
def ready(request: Request, db: Session=Depends(get_session)):
    enabled(request); out=svc.readiness(db); out["migration_0087_applied"]="0087" in migration_status(request.app.state.database)["applied"]; return out

@router.post("/projects/{project_id}", dependencies=[Depends(require_write)])
def create(project_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_synthesis,db,project_id,payload.data)

@router.post("/syntheses/{synthesis_id}/studies", dependencies=[Depends(require_write)])
def add_study(synthesis_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_study,db,synthesis_id,payload.data)

@router.post("/syntheses/{synthesis_id}/outcomes", dependencies=[Depends(require_write)])
def add_outcome(synthesis_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_outcome,db,synthesis_id,payload.data)

@router.post("/syntheses/{synthesis_id}/effects", dependencies=[Depends(require_write)])
def add_effect(synthesis_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_effect,db,synthesis_id,payload.data)

@router.post("/syntheses/{synthesis_id}/meta-analyses", dependencies=[Depends(require_write)])
def add_meta(synthesis_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_meta_analysis,db,synthesis_id,payload.data)

@router.post("/syntheses/{synthesis_id}/assessments", dependencies=[Depends(require_write)])
def add_assessment(synthesis_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_assessment,db,synthesis_id,payload.data)

@router.post("/syntheses/{synthesis_id}/relations", dependencies=[Depends(require_write)])
def add_relation(synthesis_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_relation,db,synthesis_id,payload.data)

@router.post("/syntheses/{synthesis_id}/gaps", dependencies=[Depends(require_write)])
def add_gap(synthesis_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_gap,db,synthesis_id,payload.data)

@router.post("/syntheses/{synthesis_id}/revisions", dependencies=[Depends(require_write)])
def revise(synthesis_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise_synthesis,db,synthesis_id,payload.data)

@router.post("/syntheses/{synthesis_id}/snapshots", dependencies=[Depends(require_write)])
def snapshot(synthesis_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,synthesis_id,payload.data)

@router.get("/syntheses/{synthesis_id}/summary", dependencies=[Depends(require_read)])
def summary(synthesis_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.descriptive_summary,db,synthesis_id)

@router.get("/syntheses/{synthesis_id}/lineage", dependencies=[Depends(require_read)])
def lineage(synthesis_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,synthesis_id)

@router.get("/syntheses/{synthesis_id}/bundle", dependencies=[Depends(require_read)])
def bundle(synthesis_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,synthesis_id)

@public_router.get("/syntheses/{synthesis_id}/summary", response_model=PublicEnvelope)
def public_summary(synthesis_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.descriptive_summary,db,synthesis_id,True),meta={"release":"2.83.0","contract":svc.CONTRACT})

@public_router.get("/syntheses/{synthesis_id}/lineage", response_model=PublicEnvelope)
def public_lineage(synthesis_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,synthesis_id,True),meta={"release":"2.83.0","contract":svc.CONTRACT})

@public_router.get("/syntheses/{synthesis_id}/bundle", response_model=PublicEnvelope)
def public_bundle(synthesis_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,synthesis_id,True),meta={"release":"2.83.0","contract":svc.CONTRACT})
