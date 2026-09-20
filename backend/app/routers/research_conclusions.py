from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_conclusions as svc

router = APIRouter(prefix="/v1/research/conclusions", tags=["Research Decision Trace & Conclusion Governance"])
public_router = APIRouter(prefix="/api/v1/research/conclusions", tags=["Unified Public API — Research Conclusion Governance"])

class Payload(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)

def enabled(request: Request):
    if not request.app.state.settings.research_decision_trace_conclusion_governance_enabled:
        raise HTTPException(503, "Research Decision Trace & Conclusion Governance is disabled.")

def call(fn, *args):
    try: return fn(*args)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc

@router.get("/readiness", dependencies=[Depends(require_read)])
def ready(request: Request, db: Session = Depends(get_session)):
    enabled(request); out=svc.readiness(db); out["migration_0084_applied"]="0084" in migration_status(request.app.state.database)["applied"]; return out

@router.post("/arguments/{argument_id}", dependencies=[Depends(require_write)])
def create_conclusion(argument_id: str, payload: Payload, request: Request, db: Session=Depends(get_session)):
    enabled(request); return call(svc.create_conclusion, db, argument_id, payload.data)

@router.post("/{conclusion_id}/evidence-bindings", dependencies=[Depends(require_write)])
def add_binding(conclusion_id: str, payload: Payload, request: Request, db: Session=Depends(get_session)):
    enabled(request); return call(svc.add_evidence_binding, db, conclusion_id, payload.data)

@router.post("/{conclusion_id}/caveats", dependencies=[Depends(require_write)])
def add_caveat(conclusion_id: str, payload: Payload, request: Request, db: Session=Depends(get_session)):
    enabled(request); return call(svc.add_caveat, db, conclusion_id, payload.data)

@router.post("/{conclusion_id}/dissent", dependencies=[Depends(require_write)])
def add_dissent(conclusion_id: str, payload: Payload, request: Request, db: Session=Depends(get_session)):
    enabled(request); return call(svc.add_dissent, db, conclusion_id, payload.data)

@router.post("/{conclusion_id}/decision-trace", dependencies=[Depends(require_write)])
def add_trace(conclusion_id: str, payload: Payload, request: Request, db: Session=Depends(get_session)):
    enabled(request); return call(svc.add_trace_step, db, conclusion_id, payload.data)

@router.post("/{conclusion_id}/reviews", dependencies=[Depends(require_write)])
def add_review(conclusion_id: str, payload: Payload, request: Request, db: Session=Depends(get_session)):
    enabled(request); return call(svc.add_review, db, conclusion_id, payload.data)

@router.post("/{conclusion_id}/revisions", dependencies=[Depends(require_write)])
def revise(conclusion_id: str, payload: Payload, request: Request, db: Session=Depends(get_session)):
    enabled(request); return call(svc.revise_conclusion, db, conclusion_id, payload.data)

@router.get("/{conclusion_id}/governance", dependencies=[Depends(require_read)])
def governance(conclusion_id: str, request: Request, db: Session=Depends(get_session)):
    enabled(request); return call(svc.governance_summary, db, conclusion_id)

@router.get("/{conclusion_id}/bundle", dependencies=[Depends(require_read)])
def conclusion_bundle(conclusion_id: str, request: Request, db: Session=Depends(get_session)):
    enabled(request); return call(svc.bundle, db, conclusion_id)

@router.post("/{conclusion_id}/snapshots", dependencies=[Depends(require_write)])
def conclusion_snapshot(conclusion_id: str, payload: Payload, request: Request, db: Session=Depends(get_session)):
    enabled(request); return call(svc.snapshot, db, conclusion_id, payload.data)

@public_router.get("/{conclusion_id}/governance", response_model=PublicEnvelope)
def public_governance(conclusion_id: str, request: Request, db: Session=Depends(get_session), ctx: PublicApiContext=Depends(require_public_scope("data:read"))):
    enabled(request); return PublicEnvelope(data=call(svc.governance_summary, db, conclusion_id, True), meta={"release":"2.80.0","contract":svc.CONTRACT})

@public_router.get("/{conclusion_id}/bundle", response_model=PublicEnvelope)
def public_bundle(conclusion_id: str, request: Request, db: Session=Depends(get_session), ctx: PublicApiContext=Depends(require_public_scope("data:read"))):
    enabled(request); return PublicEnvelope(data=call(svc.bundle, db, conclusion_id, True), meta={"release":"2.80.0","contract":svc.CONTRACT})
