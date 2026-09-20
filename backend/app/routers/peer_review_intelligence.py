from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import peer_review_intelligence as svc

router = APIRouter(prefix="/v1/research/peer-review", tags=["Peer Review, Replication & Rebuttal Intelligence"])
public_router = APIRouter(prefix="/api/v1/research/peer-review", tags=["Unified Public API — Peer Review, Replication & Rebuttal Intelligence"])

class Payload(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)

def enabled(request: Request):
    if not request.app.state.settings.peer_review_replication_rebuttal_enabled:
        raise HTTPException(503, "Peer Review, Replication & Rebuttal Intelligence is disabled.")

def call(fn, *args):
    try: return fn(*args)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc

@router.get("/readiness", dependencies=[Depends(require_read)])
def ready(request: Request, db: Session = Depends(get_session)):
    enabled(request); out = svc.readiness(db); out["migration_0086_applied"] = "0086" in migration_status(request.app.state.database)["applied"]; return out

@router.post("/publications/{publication_id}/reviews", dependencies=[Depends(require_write)])
def create_review(publication_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)): enabled(request); return call(svc.create_review, db, publication_id, payload.data)

@router.post("/reviews/{review_id}/comments", dependencies=[Depends(require_write)])
def add_comment(review_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)): enabled(request); return call(svc.add_comment, db, review_id, payload.data)

@router.post("/comments/{comment_id}/responses", dependencies=[Depends(require_write)])
def add_response(comment_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)): enabled(request); return call(svc.add_response, db, comment_id, payload.data)

@router.post("/reviews/{review_id}/revisions", dependencies=[Depends(require_write)])
def revise_review(review_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)): enabled(request); return call(svc.revise_review, db, review_id, payload.data)

@router.post("/publications/{publication_id}/replications", dependencies=[Depends(require_write)])
def create_replication(publication_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)): enabled(request); return call(svc.create_replication_study, db, publication_id, payload.data)

@router.post("/replications/{study_id}/attempts", dependencies=[Depends(require_write)])
def add_attempt(study_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)): enabled(request); return call(svc.add_replication_attempt, db, study_id, payload.data)

@router.post("/replications/{study_id}/comparisons", dependencies=[Depends(require_write)])
def add_comparison(study_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)): enabled(request); return call(svc.add_replication_comparison, db, study_id, payload.data)

@router.post("/publications/{publication_id}/rebuttals", dependencies=[Depends(require_write)])
def create_rebuttal(publication_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)): enabled(request); return call(svc.create_rebuttal, db, publication_id, payload.data)

@router.post("/rebuttals/{rebuttal_id}/points", dependencies=[Depends(require_write)])
def add_rebuttal_point(rebuttal_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)): enabled(request); return call(svc.add_rebuttal_point, db, rebuttal_id, payload.data)

@router.post("/publications/{publication_id}/snapshots", dependencies=[Depends(require_write)])
def snapshot(publication_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)): enabled(request); return call(svc.snapshot, db, publication_id, payload.data)

@router.get("/publications/{publication_id}/summary", dependencies=[Depends(require_read)])
def summary(publication_id: str, request: Request, db: Session = Depends(get_session)): enabled(request); return call(svc.descriptive_summary, db, publication_id)

@router.get("/publications/{publication_id}/lineage", dependencies=[Depends(require_read)])
def lineage(publication_id: str, request: Request, db: Session = Depends(get_session)): enabled(request); return call(svc.lineage, db, publication_id)

@router.get("/publications/{publication_id}/bundle", dependencies=[Depends(require_read)])
def bundle(publication_id: str, request: Request, db: Session = Depends(get_session)): enabled(request); return call(svc.bundle, db, publication_id)

@public_router.get("/publications/{publication_id}/summary", response_model=PublicEnvelope)
def public_summary(publication_id: str, request: Request, db: Session = Depends(get_session), ctx: PublicApiContext = Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.descriptive_summary, db, publication_id, True), meta={"release":"2.82.0","contract":svc.CONTRACT})

@public_router.get("/publications/{publication_id}/lineage", response_model=PublicEnvelope)
def public_lineage(publication_id: str, request: Request, db: Session = Depends(get_session), ctx: PublicApiContext = Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage, db, publication_id, True), meta={"release":"2.82.0","contract":svc.CONTRACT})

@public_router.get("/publications/{publication_id}/bundle", response_model=PublicEnvelope)
def public_bundle(publication_id: str, request: Request, db: Session = Depends(get_session), ctx: PublicApiContext = Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle, db, publication_id, True), meta={"release":"2.82.0","contract":svc.CONTRACT})
