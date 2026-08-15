from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..models import HumanitarianCondition, LiveDataObservation
from ..public_api_auth import PublicApiContext, require_public_scope
from ..services.humanitarian import (
    CONDITION_KINDS, CURRENT_CONDITION_ROLES, SEMANTIC_ROLES, SERVICE_DOMAINS,
    country_summary, create_condition, materialize_live_observation, query_conditions,
)

router = APIRouter(prefix="/v1/humanitarian", tags=["Humanitarian Access & Essential Services"])
public_router = APIRouter(prefix="/api/v1/humanitarian", tags=["Unified Public API — Humanitarian Conditions"])

class ConditionCreate(BaseModel):
    country_code: str = Field(min_length=3, max_length=3)
    service_domain: str
    condition_kind: str
    observed_at: datetime
    publisher: str = Field(min_length=1, max_length=400)
    semantic_role: str = "humanitarian-indicator"
    status_value: str | None = Field(default=None, max_length=160)
    value_number: float | None = None
    value_text: str | None = None
    unit: str | None = None
    admin_area: str | None = None
    locality: str | None = None
    facility_id: str | None = None
    published_at: datetime | None = None
    source_id: str | None = None
    connector_id: str | None = None
    source_record_id: str | None = None
    source_url: str | None = None
    evidence_class: str = "published-evidence"
    geographic_scope: str | None = None
    methodology: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    dimensions: dict[str, Any] = Field(default_factory=dict)
    details: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    public: bool = True

def _row(row: HumanitarianCondition) -> dict[str, Any]:
    return {
        "id": row.id, "country_code": row.country_code, "admin_area": row.admin_area,
        "locality": row.locality, "facility_id": row.facility_id,
        "service_domain": row.service_domain, "condition_kind": row.condition_kind,
        "semantic_role": row.semantic_role, "current_conditions_eligible": row.semantic_role in CURRENT_CONDITION_ROLES,
        "status_value": row.status_value, "value_number": row.value_number, "value_text": row.value_text,
        "unit": row.unit, "observed_at": row.observed_at, "published_at": row.published_at,
        "publisher": row.publisher, "source_id": row.source_id, "connector_id": row.connector_id,
        "source_record_id": row.source_record_id, "source_url": row.source_url,
        "evidence_class": row.evidence_class, "geographic_scope": row.geographic_scope,
        "methodology": row.methodology, "confidence": row.confidence,
        "dimensions": row.dimensions_json, "details": row.details_json, "provenance": row.provenance_json,
        "public": row.public, "created_at": row.created_at,
    }

@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    return {
        "release": request.app.state.settings.version,
        "migration_0014_applied": True,
        "service_domains": sorted(SERVICE_DOMAINS),
        "condition_kinds": sorted(CONDITION_KINDS),
        "semantic_roles": sorted(SEMANTIC_ROLES),
        "records": len(db.scalars(select(HumanitarianCondition.id)).all()),
        "structured_source_materialization_only": True,
        "reliefweb_report_metadata_promoted_to_operational_claim": False,
        "synthetic_severity_scoring": False,
        "automatic_legal_conclusions": False,
        "zero_records_mean_normal_conditions": False,
        "external_provider_health_release_blocking": False,
        "auto_materialize_structured_observations": request.app.state.settings.humanitarian_auto_materialize,
        "status": "ready" if request.app.state.settings.humanitarian_fabric_enabled else "disabled",
    }

@router.post("/conditions", dependencies=[Depends(require_write)])
def create(payload: ConditionCreate, db: Session = Depends(get_session)):
    try:
        return _row(create_condition(db, **payload.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@router.get("/conditions", dependencies=[Depends(require_read)])
def list_internal(country_code: str | None = None, service_domain: str | None = None, condition_kind: str | None = None, facility_id: str | None = None, semantic_role: str | None = None, limit: int = Query(500, ge=1, le=5000), db: Session = Depends(get_session)):
    try:
        rows = query_conditions(db, country_code=country_code, service_domain=service_domain, condition_kind=condition_kind, facility_id=facility_id, semantic_role=semantic_role, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"items": [_row(x) for x in rows], "total": len(rows)}

@public_router.get("/conditions")
def list_public(country_code: str | None = None, service_domain: str | None = None, condition_kind: str | None = None, facility_id: str | None = None, semantic_role: str | None = None, limit: int = Query(500, ge=1, le=5000), _context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    try:
        rows = query_conditions(db, country_code=country_code, service_domain=service_domain, condition_kind=condition_kind, facility_id=facility_id, semantic_role=semantic_role, public_only=True, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"items": [_row(x) for x in rows], "total": len(rows)}

@router.get("/country/{country_code}/summary", dependencies=[Depends(require_read)])
def summary(country_code: str, db: Session = Depends(get_session)):
    try:
        return country_summary(db, country_code)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@public_router.get("/country/{country_code}/summary")
def public_summary(country_code: str, _context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    try:
        return country_summary(db, country_code, public_only=True)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@router.post("/materialize/live-observation/{observation_id}", dependencies=[Depends(require_write)])
def materialize(observation_id: str, db: Session = Depends(get_session)):
    obs = db.get(LiveDataObservation, observation_id)
    if not obs:
        raise HTTPException(status_code=404, detail="live-data observation not found")
    try:
        row, reason = materialize_live_observation(db, obs)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"materialized": row is not None, "reason": reason, "condition": _row(row) if row else None}
