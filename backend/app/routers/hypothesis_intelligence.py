from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import hypothesis_intelligence as svc

router = APIRouter(prefix="/v1/research/hypotheses", tags=["Hypothesis & Competing Explanation Engine"])
public_router = APIRouter(prefix="/api/v1/research/hypotheses", tags=["Unified Public API — Hypothesis Intelligence"])


class Payload(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


def enabled(request: Request):
    if not request.app.state.settings.hypothesis_competing_explanation_engine_enabled:
        raise HTTPException(503, "Hypothesis & Competing Explanation Engine is disabled.")


def call(fn, *args):
    try:
        return fn(*args)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/readiness", dependencies=[Depends(require_read)])
def ready(request: Request, db: Session = Depends(get_session)):
    enabled(request)
    out = svc.readiness(db)
    out["migration_0082_applied"] = "0082" in migration_status(request.app.state.database)["applied"]
    return out


@router.post("/projects/{project_id}/sets", dependencies=[Depends(require_write)])
def create_set(project_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.create_hypothesis_set, db, project_id, payload.data)


@router.post("/sets/{set_id}/hypotheses", dependencies=[Depends(require_write)])
def create_hypothesis(set_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.create_hypothesis, db, set_id, payload.data)


@router.post("/{hypothesis_id}/revisions", dependencies=[Depends(require_write)])
def revise_hypothesis(hypothesis_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.revise_hypothesis, db, hypothesis_id, payload.data)


@router.post("/{hypothesis_id}/evidence-assessments", dependencies=[Depends(require_write)])
def evidence_assessment(hypothesis_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.add_evidence_assessment, db, hypothesis_id, payload.data)


@router.post("/{hypothesis_id}/predictions", dependencies=[Depends(require_write)])
def prediction(hypothesis_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.add_prediction, db, hypothesis_id, payload.data)


@router.post("/{hypothesis_id}/assumptions", dependencies=[Depends(require_write)])
def assumption(hypothesis_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.add_assumption, db, hypothesis_id, payload.data)


@router.post("/sets/{set_id}/relations", dependencies=[Depends(require_write)])
def relation(set_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.add_hypothesis_relation, db, set_id, payload.data)


@router.post("/sets/{set_id}/discrimination-gaps", dependencies=[Depends(require_write)])
def discrimination_gap(set_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.add_discrimination_gap, db, set_id, payload.data)


@router.get("/sets/{set_id}/comparison", dependencies=[Depends(require_read)])
def comparison(set_id: str, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.comparison_matrix, db, set_id)


@router.get("/sets/{set_id}/bundle", dependencies=[Depends(require_read)])
def hypothesis_bundle(set_id: str, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.bundle, db, set_id)


@router.post("/sets/{set_id}/snapshots", dependencies=[Depends(require_write)])
def hypothesis_snapshot(set_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.snapshot, db, set_id, payload.data)


@public_router.get("/sets/{set_id}/comparison", response_model=PublicEnvelope)
def public_comparison(
    set_id: str,
    request: Request,
    db: Session = Depends(get_session),
    ctx: PublicApiContext = Depends(require_public_scope("data:read")),
):
    enabled(request)
    return PublicEnvelope(
        data=call(svc.comparison_matrix, db, set_id, True),
        meta={"release": "2.78.0", "contract": svc.CONTRACT},
    )


@public_router.get("/sets/{set_id}/bundle", response_model=PublicEnvelope)
def public_bundle(
    set_id: str,
    request: Request,
    db: Session = Depends(get_session),
    ctx: PublicApiContext = Depends(require_public_scope("data:read")),
):
    enabled(request)
    return PublicEnvelope(
        data=call(svc.bundle, db, set_id, True),
        meta={"release": "2.78.0", "contract": svc.CONTRACT},
    )
