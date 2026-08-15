from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..models import HumanitarianCondition, LiveDataObservation, OperationalFacility, StreamEvent

SERVICE_DOMAINS = {
    "health", "education", "food", "water", "electricity", "fuel",
    "displacement", "communications", "shelter", "humanitarian-access",
    "protection", "other",
}
CONDITION_KINDS = {
    "operational-status", "access-status", "availability", "interruption",
    "throughput", "population-affected", "displacement", "food-security",
    "nutrition", "supply-status", "damage-status", "capacity-status",
    "operational-presence", "funding", "other",
}
SEMANTIC_ROLES = {
    "operational-condition", "humanitarian-indicator", "structural-baseline",
    "classification", "contextual-report", "other",
}
CURRENT_CONDITION_ROLES = {"operational-condition", "humanitarian-indicator", "classification"}

# Only normalized resources with an explicit semantic mapping are promoted automatically.
# Report metadata (for example ReliefWeb reports) is not itself an operational condition.
HDX_HAPI_METRIC_MAP: dict[str, tuple[str, str, str]] = {
    "affected_people_idps": ("displacement", "displacement", "humanitarian-indicator"),
    "affected_people_humanitarian_needs": ("humanitarian-access", "population-affected", "humanitarian-indicator"),
    "coordination_context_operational_presence": ("humanitarian-access", "operational-presence", "humanitarian-indicator"),
    "coordination_context_funding": ("humanitarian-access", "funding", "humanitarian-indicator"),
    "food_security_nutrition_poverty_food_security": ("food", "food-security", "classification"),
}


def normalize_country(value: str) -> str:
    code = (value or "").strip().upper()
    if len(code) != 3 or not code.isalpha():
        raise ValueError("country_code must be an ISO3-like three-letter code")
    return code


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def create_condition(
    db: Session,
    *,
    country_code: str,
    service_domain: str,
    condition_kind: str,
    observed_at: datetime,
    publisher: str,
    semantic_role: str = "humanitarian-indicator",
    status_value: str | None = None,
    value_number: float | None = None,
    value_text: str | None = None,
    unit: str | None = None,
    admin_area: str | None = None,
    locality: str | None = None,
    facility_id: str | None = None,
    published_at: datetime | None = None,
    source_id: str | None = None,
    connector_id: str | None = None,
    source_record_id: str | None = None,
    source_url: str | None = None,
    evidence_class: str = "published-evidence",
    geographic_scope: str | None = None,
    methodology: str | None = None,
    confidence: float | None = None,
    dimensions: dict | None = None,
    details: dict | None = None,
    provenance: dict | None = None,
    public: bool = True,
) -> HumanitarianCondition:
    code = normalize_country(country_code)
    domain = service_domain.strip().lower()
    kind = condition_kind.strip().lower()
    role = semantic_role.strip().lower()
    if domain not in SERVICE_DOMAINS:
        raise ValueError(f"unsupported service_domain: {service_domain}")
    if kind not in CONDITION_KINDS:
        raise ValueError(f"unsupported condition_kind: {condition_kind}")
    if role not in SEMANTIC_ROLES:
        raise ValueError(f"unsupported semantic_role: {semantic_role}")
    if confidence is not None and not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if not any([status_value and status_value.strip(), value_number is not None, value_text and value_text.strip()]):
        raise ValueError("a condition requires status_value, value_number, or value_text")
    if facility_id:
        facility = db.get(OperationalFacility, facility_id)
        if not facility:
            raise ValueError("facility not found")
        if facility.country_code != code:
            raise ValueError("facility country does not match condition country")
    observed_at = _aware(observed_at)
    if published_at is not None:
        published_at = _aware(published_at)

    if source_id and source_record_id:
        existing = db.scalar(
            select(HumanitarianCondition).where(
                HumanitarianCondition.source_id == source_id,
                HumanitarianCondition.source_record_id == source_record_id,
                HumanitarianCondition.service_domain == domain,
                HumanitarianCondition.condition_kind == kind,
                HumanitarianCondition.observed_at == observed_at,
            )
        )
        if existing:
            return existing

    row = HumanitarianCondition(
        country_code=code,
        admin_area=admin_area,
        locality=locality,
        facility_id=facility_id,
        service_domain=domain,
        condition_kind=kind,
        semantic_role=role,
        status_value=status_value.strip().lower() if status_value else None,
        value_number=value_number,
        value_text=value_text.strip() if value_text else None,
        unit=unit,
        observed_at=observed_at,
        published_at=published_at,
        publisher=publisher.strip(),
        source_id=source_id,
        connector_id=connector_id,
        source_record_id=source_record_id,
        source_url=source_url,
        evidence_class=evidence_class,
        geographic_scope=geographic_scope,
        methodology=methodology,
        confidence=confidence,
        dimensions_json=dimensions or {},
        details_json=details or {},
        provenance_json=provenance or {},
        public=public,
    )
    db.add(row)
    db.flush()
    db.add(StreamEvent(
        event_type="humanitarian.condition.created",
        subject_type="humanitarian-condition",
        subject_id=row.id,
        public=public,
        payload_json={
            "condition_id": row.id,
            "country_code": code,
            "service_domain": domain,
            "condition_kind": kind,
            "semantic_role": role,
            "status_value": row.status_value,
            "observed_at": observed_at.isoformat(),
            "publisher": publisher,
            "facility_id": facility_id,
        },
    ))
    db.commit()
    db.refresh(row)
    return row


def query_conditions(
    db: Session,
    *,
    country_code: str | None = None,
    service_domain: str | None = None,
    condition_kind: str | None = None,
    facility_id: str | None = None,
    semantic_role: str | None = None,
    public_only: bool = False,
    limit: int = 500,
) -> list[HumanitarianCondition]:
    q = select(HumanitarianCondition)
    if country_code:
        q = q.where(HumanitarianCondition.country_code == normalize_country(country_code))
    if service_domain:
        q = q.where(HumanitarianCondition.service_domain == service_domain.strip().lower())
    if condition_kind:
        q = q.where(HumanitarianCondition.condition_kind == condition_kind.strip().lower())
    if facility_id:
        q = q.where(HumanitarianCondition.facility_id == facility_id)
    if semantic_role:
        q = q.where(HumanitarianCondition.semantic_role == semantic_role.strip().lower())
    if public_only:
        q = q.where(HumanitarianCondition.public.is_(True))
    return list(db.scalars(q.order_by(desc(HumanitarianCondition.observed_at), desc(HumanitarianCondition.created_at)).limit(limit)).all())


def country_summary(db: Session, country_code: str, *, public_only: bool = False) -> dict[str, Any]:
    code = normalize_country(country_code)
    rows = query_conditions(db, country_code=code, public_only=public_only, limit=5000)
    domains: dict[str, int] = {}
    current = 0
    structural = 0
    for row in rows:
        domains[row.service_domain] = domains.get(row.service_domain, 0) + 1
        if row.semantic_role in CURRENT_CONDITION_ROLES:
            current += 1
        if row.semantic_role == "structural-baseline":
            structural += 1
    return {
        "country_code": code,
        "records": len(rows),
        "domains": domains,
        "current_conditions_eligible_records": current,
        "structural_context_records": structural,
        "synthetic_severity_score": None,
        "automatic_legal_conclusion": False,
        "automatic_causal_attribution": False,
        "zero_records_implication": "unknown-not-normal",
    }


def materialize_live_observation(db: Session, observation: LiveDataObservation) -> tuple[HumanitarianCondition | None, str]:
    if observation.domain != "humanitarian":
        return None, "not-humanitarian"
    if observation.connector_id == "ocha.reliefweb-reports":
        return None, "report-metadata-not-operational-condition"
    mapping = HDX_HAPI_METRIC_MAP.get(observation.metric)
    if not mapping:
        explicit = (observation.metadata_json or {}).get("humanitarian_mapping")
        if isinstance(explicit, dict):
            try:
                mapping = (str(explicit["service_domain"]), str(explicit["condition_kind"]), str(explicit.get("semantic_role", "humanitarian-indicator")))
            except KeyError:
                mapping = None
    if not mapping:
        return None, "no-explicit-semantic-mapping"
    dimensions = dict(observation.dimensions_json or {})
    code = dimensions.get("location_code") or dimensions.get("country_code") or (observation.metadata_json or {}).get("country_code")
    if not code:
        return None, "country-code-unavailable"
    domain, kind, role = mapping
    row = create_condition(
        db,
        country_code=str(code),
        service_domain=domain,
        condition_kind=kind,
        semantic_role=role,
        status_value=None,
        value_number=observation.value_number,
        value_text=observation.value_text,
        unit=observation.unit,
        observed_at=observation.observed_at,
        published_at=observation.published_at,
        publisher=observation.attribution or observation.source_id,
        source_id=observation.source_id,
        connector_id=observation.connector_id,
        source_record_id=observation.source_record_id,
        evidence_class="standardized-humanitarian-indicator",
        methodology=observation.methodology_url,
        dimensions=dimensions,
        details={"live_observation_id": observation.id, "quality_status": observation.quality_status, "freshness_status": observation.freshness_status},
        provenance={"raw_record_id": observation.raw_record_id, "raw_record_hash": observation.raw_record_hash},
        public=observation.public,
    )
    return row, "materialized"
