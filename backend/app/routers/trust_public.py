from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_session
from ..models import EvaluationDefinition, EvaluationRun, KnownLimitation, TrustAttestation, TrustIncident
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services.trust import build_trust_status, evaluation_run_read

router = APIRouter(prefix="/api/v1/trust", tags=["Unified Public API — Trust"])


def envelope(request: Request, data, *, meta: dict | None = None) -> PublicEnvelope:
    values = {"api_version": "v1", "request_id": request.state.request_id, "documentation": "/trust"}
    if meta: values.update(meta)
    return PublicEnvelope(data=jsonable_encoder(data), meta=values)


@router.get("/status", response_model=PublicEnvelope)
def public_trust_status(request: Request, _context: PublicApiContext = Depends(require_public_scope("trust:read")), db: Session = Depends(get_session)):
    return envelope(request, build_trust_status(db, request.app.state.settings, public_only=True))


@router.get("/evaluations", response_model=PublicEnvelope)
def public_evaluations(request: Request, domain: str | None = None, limit: int = Query(default=100, ge=1, le=200), _context: PublicApiContext = Depends(require_public_scope("trust:read")), db: Session = Depends(get_session)):
    filters = [EvaluationDefinition.public.is_(True), EvaluationDefinition.active.is_(True)]
    if domain: filters.append(EvaluationDefinition.domain == domain)
    definitions = list(db.scalars(select(EvaluationDefinition).where(*filters).order_by(EvaluationDefinition.sort_order).limit(limit)).all())
    data = []
    for definition in definitions:
        run = db.scalar(select(EvaluationRun).where(EvaluationRun.definition_id == definition.id, EvaluationRun.public.is_(True)).order_by(EvaluationRun.completed_at.desc()).limit(1))
        data.append({"definition": definition, "latest_run": evaluation_run_read(db, run) if run else None})
    return envelope(request, data, meta={"total": len(data)})


@router.get("/incidents", response_model=PublicEnvelope)
def public_incidents(request: Request, include_resolved: bool = False, _context: PublicApiContext = Depends(require_public_scope("trust:read")), db: Session = Depends(get_session)):
    filters = [TrustIncident.public.is_(True)]
    if not include_resolved: filters.append(TrustIncident.status != "resolved")
    records = list(db.scalars(select(TrustIncident).where(*filters).order_by(TrustIncident.started_at.desc())).all())
    return envelope(request, records, meta={"total": len(records)})


@router.get("/limitations", response_model=PublicEnvelope)
def public_limitations(request: Request, include_retired: bool = False, _context: PublicApiContext = Depends(require_public_scope("trust:read")), db: Session = Depends(get_session)):
    filters = [KnownLimitation.public.is_(True)]
    if not include_retired: filters.append(KnownLimitation.status != "retired")
    records = list(db.scalars(select(KnownLimitation).where(*filters).order_by(KnownLimitation.domain, KnownLimitation.title)).all())
    return envelope(request, records, meta={"total": len(records)})


@router.get("/attestations", response_model=PublicEnvelope)
def public_attestations(request: Request, _context: PublicApiContext = Depends(require_public_scope("trust:read")), db: Session = Depends(get_session)):
    records = list(db.scalars(select(TrustAttestation).where(TrustAttestation.public.is_(True), TrustAttestation.status == "active").order_by(TrustAttestation.valid_from.desc())).all())
    return envelope(request, records, meta={"total": len(records)})
