from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..models import CountryEvidenceReconciliation
from ..public_api_auth import PublicApiContext, require_public_scope
from ..services.country_evidence import (
    AUTHORITY_PRECEDENCE, country_candidates, country_federation, persist_reconciliation, reconcile_candidates,
)

router = APIRouter(prefix="/v1/country-evidence", tags=["Country Evidence Federation & Reconciliation"])
public_router = APIRouter(prefix="/api/v1/country-evidence", tags=["Unified Public API — Country Evidence"])

class CandidateIn(BaseModel):
    record_family: str = "external-candidate"
    record_id: str | None = None
    concept: str | None = None
    source_id: str | None = None
    connector_id: str | None = None
    publisher: str | None = None
    authority_role: str | None = None
    evidence_class: str | None = None
    semantic_role: str | None = None
    semantic_class: str | None = None
    geography_code: str | None = None
    geographic_scope: str | None = None
    reference_period: str | None = None
    period: str | None = None
    value_number: float | None = None
    value_text: str | None = None
    status_value: str | None = None
    unit: str | None = None
    status: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class ReconcileIn(BaseModel):
    country_code: str = Field(min_length=3, max_length=3)
    concept: str = Field(min_length=1, max_length=500)
    candidates: list[CandidateIn] = Field(min_length=1, max_length=100)
    persist: bool = True
    public: bool = True


def _audit(row: CountryEvidenceReconciliation) -> dict[str, Any]:
    return {
        "id": row.id, "country_code": row.country_code, "concept": row.concept,
        "decision_state": row.decision_state, "selected_record_family": row.selected_record_family,
        "selected_record_id": row.selected_record_id, "selected_source": row.selected_source,
        "selected_authority_role": row.selected_authority_role, "request_fingerprint": row.request_fingerprint,
        "candidates": row.candidates_json, "rationale": row.rationale_json, "public": row.public,
        "created_at": row.created_at,
    }

@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    status = migration_status(request.app.state.database)
    return {
        "release": request.app.state.settings.version, "migration_0015_applied": "0015" in status["applied"],
        "authority_precedence": AUTHORITY_PRECEDENCE, "exact_concept_required": True,
        "unit_compatibility_required": True, "geographic_scope_compatibility_required": True,
        "structural_operational_separation": True, "different_periods_are_not_conflicts": True,
        "automatic_averaging": False, "subnational_scope_can_replace_national": False,
        "knowledge_context_truth_precedence": "excluded", "status": "ready" if request.app.state.settings.country_evidence_federation_enabled else "disabled",
    }

@router.get("/country/{country_code}/federation", dependencies=[Depends(require_read)])
def federation(country_code: str, db: Session = Depends(get_session)):
    try: return country_federation(db, country_code)
    except ValueError as exc: raise HTTPException(422, str(exc))

@public_router.get("/country/{country_code}/federation")
def public_federation(country_code: str, _context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    try: return country_federation(db, country_code, public_only=True)
    except ValueError as exc: raise HTTPException(422, str(exc))

@router.get("/country/{country_code}/reconcile", dependencies=[Depends(require_read)])
def reconcile_country(country_code: str, concept: str, db: Session = Depends(get_session)):
    try:
        candidates = country_candidates(db, country_code, concept=concept)
        return reconcile_candidates(country_code, concept, candidates)
    except ValueError as exc: raise HTTPException(422, str(exc))

@public_router.get("/country/{country_code}/reconcile")
def public_reconcile_country(country_code: str, concept: str, _context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    try:
        candidates = country_candidates(db, country_code, concept=concept, public_only=True)
        return reconcile_candidates(country_code, concept, candidates)
    except ValueError as exc: raise HTTPException(422, str(exc))

@router.post("/reconcile", dependencies=[Depends(require_write)])
def reconcile_explicit(payload: ReconcileIn, db: Session = Depends(get_session)):
    try:
        result = reconcile_candidates(payload.country_code, payload.concept, [x.model_dump(exclude_none=True) for x in payload.candidates])
    except ValueError as exc: raise HTTPException(422, str(exc))
    if payload.persist:
        row = persist_reconciliation(db, result, public=payload.public)
        result["audit"] = _audit(row)
    return result

@router.get("/reconciliations", dependencies=[Depends(require_read)])
def reconciliations(country_code: str | None = None, concept: str | None = None, limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_session)):
    q = select(CountryEvidenceReconciliation)
    if country_code: q = q.where(CountryEvidenceReconciliation.country_code == country_code.upper())
    if concept: q = q.where(CountryEvidenceReconciliation.concept == concept.lower().replace("_", "-"))
    rows = db.scalars(q.order_by(desc(CountryEvidenceReconciliation.created_at)).limit(limit)).all()
    return {"items": [_audit(x) for x in rows], "total": len(rows)}
