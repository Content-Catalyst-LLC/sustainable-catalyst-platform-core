from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..models import (
    CountryEvidenceReconciliation,
    EconomicDataRecord,
    FacilityObservation,
    HumanitarianCondition,
    OperationalFacility,
)
from .humanitarian import CURRENT_CONDITION_ROLES, normalize_country

AUTHORITY_PRECEDENCE = {
    "primary-official": 10,
    "sector-official": 20,
    "operational-authority": 25,
    "intergovernmental": 40,
    "harmonized-benchmark": 50,
    "published-evidence": 60,
    "knowledge-context": 90,
    "unknown": 100,
}

NON_TRUTH_ROLES = {"knowledge-context", "dataset-discovery", "contextual-report"}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", "-")


def authority_role(*, source_id: str | None = None, publisher: str | None = None, evidence_class: str | None = None, semantic_role: str | None = None, metadata: dict | None = None) -> str:
    metadata = metadata or {}
    explicit = _norm(metadata.get("authority_role"))
    if explicit in AUTHORITY_PRECEDENCE:
        return explicit
    text = " ".join(filter(None, [source_id, publisher, evidence_class])).lower()
    if "pcbs" in text or "palestinian central bureau of statistics" in text:
        return "primary-official"
    if any(token in text for token in ("ministry", "monetary authority", "statistics office", "statistical office", "national statistics")):
        return "sector-official"
    if source_id == "world-bank" or "world bank" in text or _norm(evidence_class) == "harmonized-benchmark":
        return "harmonized-benchmark"
    if any(token in text for token in ("ocha", "hdx", "who", "unicef", "wfp", "unhcr", "iom", "ipc")):
        if _norm(semantic_role) == "operational-condition":
            return "operational-authority"
        return "intergovernmental"
    if any(token in text for token in ("united nations", "imf", "unesco", "fao", "world health organization")):
        return "intergovernmental"
    if _norm(evidence_class) in {"primary-official", "official-statistic", "official-release"}:
        return "primary-official"
    return "published-evidence" if text else "unknown"


def semantic_class(candidate: dict[str, Any]) -> str:
    role = _norm(candidate.get("semantic_role"))
    if role == "structural-baseline" or _norm(candidate.get("evidence_class")) == "harmonized-benchmark":
        return "structural"
    if role in CURRENT_CONDITION_ROLES or role == "operational-condition":
        return "operational"
    if role in NON_TRUTH_ROLES:
        return "context"
    return _norm(candidate.get("semantic_class")) or "published"


def _period_key(candidate: dict[str, Any]) -> str:
    value = candidate.get("reference_period") or candidate.get("period") or candidate.get("observed_at") or candidate.get("period_start")
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).date().isoformat()
    return str(value or "").strip()


def _candidate_key(candidate: dict[str, Any]) -> tuple:
    role = candidate.get("authority_role") or authority_role(
        source_id=candidate.get("source_id"), publisher=candidate.get("publisher"),
        evidence_class=candidate.get("evidence_class"), semantic_role=candidate.get("semantic_role"),
        metadata=candidate.get("metadata") or {},
    )
    candidate["authority_role"] = role
    return (
        AUTHORITY_PRECEDENCE.get(role, 100),
        0 if candidate.get("status") in {"official_release", "published", "source_reported", None} else 1,
        -_period_sort(candidate),
        str(candidate.get("record_id") or ""),
    )


def _period_sort(candidate: dict[str, Any]) -> int:
    raw = candidate.get("period_start") or candidate.get("observed_at") or candidate.get("published_at")
    if isinstance(raw, datetime):
        return int(raw.timestamp())
    text = str(raw or candidate.get("reference_period") or candidate.get("period") or "")
    digits = "".join(ch for ch in text[:10] if ch.isdigit())
    try:
        return int(digits[:8] or 0)
    except ValueError:
        return 0


def _scope(candidate: dict[str, Any]) -> str:
    return _norm(candidate.get("geographic_scope") or candidate.get("geography_code") or candidate.get("country_code"))


def _unit(candidate: dict[str, Any]) -> str:
    return _norm(candidate.get("unit"))


def _value(candidate: dict[str, Any]) -> Any:
    if candidate.get("value_number") is not None:
        return candidate.get("value_number")
    return candidate.get("status_value") if candidate.get("status_value") is not None else candidate.get("value_text")


def reconcile_candidates(country_code: str, concept: str, candidates: list[dict[str, Any]], *, tolerance_ratio: float = 0.01) -> dict[str, Any]:
    code = normalize_country(country_code)
    concept_norm = _norm(concept)
    normalized: list[dict[str, Any]] = []
    for raw in candidates:
        c = dict(raw)
        c["concept"] = _norm(c.get("concept") or concept_norm)
        c["semantic_class"] = semantic_class(c)
        c["authority_role"] = c.get("authority_role") or authority_role(
            source_id=c.get("source_id"), publisher=c.get("publisher"), evidence_class=c.get("evidence_class"),
            semantic_role=c.get("semantic_role"), metadata=c.get("metadata") or {},
        )
        c["reference_period"] = _period_key(c)
        c["geographic_scope"] = c.get("geographic_scope") or c.get("geography_code") or code
        c["value"] = _value(c)
        normalized.append(c)

    exact = [c for c in normalized if c["concept"] == concept_norm and c["semantic_class"] != "context"]
    if not exact:
        return {
            "country_code": code, "concept": concept_norm, "decision_state": "no-comparable-candidates",
            "selected": None, "candidates": normalized, "discrepancies": [], "do_not_blend": True,
            "rationale": {"reason": "No exact non-context candidate matches the requested concept."},
        }

    ranked = sorted(exact, key=_candidate_key)
    selected = ranked[0]
    selected_scope, selected_unit, selected_semantic = _scope(selected), _unit(selected), selected["semantic_class"]
    compatible = [c for c in exact if _scope(c) == selected_scope and _unit(c) == selected_unit and c["semantic_class"] == selected_semantic]
    incompatible = [c for c in exact if c not in compatible]

    period_set = {c["reference_period"] for c in compatible if c["reference_period"]}
    discrepancies: list[dict[str, Any]] = []
    same_period = [c for c in compatible if c["reference_period"] == selected["reference_period"]]
    numeric = [c for c in same_period if isinstance(c.get("value_number"), (int, float))]
    if len(numeric) > 1:
        base = float(selected.get("value_number") or 0.0)
        for c in numeric:
            if c is selected:
                continue
            other = float(c["value_number"])
            denom = max(abs(base), abs(other), 1e-12)
            ratio = abs(base - other) / denom
            if ratio > tolerance_ratio:
                discrepancies.append({
                    "candidate_record_id": c.get("record_id"), "selected_value": base,
                    "candidate_value": other, "relative_difference": ratio,
                    "classification": "material-discrepancy",
                })

    if incompatible:
        state = "scope-or-semantics-differ"
    elif discrepancies:
        state = "material-discrepancy"
    elif len(period_set) > 1:
        state = "different-reference-period"
    elif len(compatible) > 1:
        state = "aligned-comparable-candidates"
    else:
        state = "single-comparable-candidate"

    preferred_present = any(c["authority_role"] in {"primary-official", "sector-official"} for c in exact)
    return {
        "country_code": code,
        "concept": concept_norm,
        "decision_state": state,
        "selected": selected,
        "candidates": normalized,
        "compatible_candidate_count": len(compatible),
        "incompatible_candidate_count": len(incompatible),
        "discrepancies": discrepancies,
        "do_not_blend": True,
        "automatic_averaging": False,
        "preferred_official_candidate_present": preferred_present,
        "rationale": {
            "selection_order": ["exact-concept", "semantic-class", "unit", "geographic-scope", "source-precedence", "authority-role", "reference-period-freshness"],
            "selected_authority_role": selected["authority_role"],
            "different_reference_periods_are_not_conflicts": True,
            "subnational_scope_never_substitutes_for_national_scope": True,
            "structural_baselines_never_substitute_for_operational_conditions": True,
            "fallback_reason": None if preferred_present else "preferred-official-source-not-in-candidate-set",
        },
    }


def _economic_candidate(row: EconomicDataRecord) -> dict[str, Any]:
    metadata = row.metadata_json or {}
    return {
        "record_family": "economic-statistic", "record_id": row.id,
        "concept": metadata.get("canonical_concept") or row.indicator_code or row.subject,
        "source_id": row.source_id, "connector_id": row.connector_id,
        "publisher": metadata.get("publisher") or row.attribution or row.source_id,
        "evidence_class": metadata.get("evidence_class") or ("harmonized-benchmark" if row.source_id == "world-bank" else "official-statistic"),
        "semantic_role": metadata.get("semantic_role") or "structural-baseline",
        "geography_code": row.geography_code, "geographic_scope": metadata.get("geographic_scope") or row.geography_code,
        "period": row.period, "period_start": row.period_start, "published_at": row.published_at,
        "value_number": row.value_number, "value_text": row.value_text, "unit": row.unit,
        "status": row.status, "source_url": row.source_url, "metadata": metadata,
    }


def _humanitarian_candidate(row: HumanitarianCondition) -> dict[str, Any]:
    details = row.details_json or {}
    return {
        "record_family": "humanitarian-condition", "record_id": row.id,
        "concept": details.get("canonical_concept") or f"{row.service_domain}.{row.condition_kind}",
        "source_id": row.source_id, "connector_id": row.connector_id, "publisher": row.publisher,
        "evidence_class": row.evidence_class, "semantic_role": row.semantic_role,
        "country_code": row.country_code, "geographic_scope": row.geographic_scope or row.country_code,
        "observed_at": row.observed_at, "published_at": row.published_at,
        "status_value": row.status_value, "value_number": row.value_number, "value_text": row.value_text,
        "unit": row.unit, "source_url": row.source_url, "metadata": details,
    }


def country_candidates(db: Session, country_code: str, concept: str | None = None, *, public_only: bool = False, limit: int = 1000) -> list[dict[str, Any]]:
    code = normalize_country(country_code)
    econ_q = select(EconomicDataRecord).where(EconomicDataRecord.geography_code == code)
    hum_q = select(HumanitarianCondition).where(HumanitarianCondition.country_code == code)
    if public_only:
        econ_q = econ_q.where(EconomicDataRecord.public.is_(True))
        hum_q = hum_q.where(HumanitarianCondition.public.is_(True))
    econ = list(db.scalars(econ_q.order_by(desc(EconomicDataRecord.period_start)).limit(limit)).all())
    hum = list(db.scalars(hum_q.order_by(desc(HumanitarianCondition.observed_at)).limit(limit)).all())
    items = [_economic_candidate(x) for x in econ] + [_humanitarian_candidate(x) for x in hum]
    if concept:
        target = _norm(concept)
        items = [x for x in items if _norm(x.get("concept")) == target]
    return items


def country_federation(db: Session, country_code: str, *, public_only: bool = False) -> dict[str, Any]:
    code = normalize_country(country_code)
    candidates = country_candidates(db, code, public_only=public_only, limit=5000)
    facilities_q = select(OperationalFacility).where(OperationalFacility.country_code == code)
    if public_only:
        facilities_q = facilities_q.where(OperationalFacility.public.is_(True))
    facilities = list(db.scalars(facilities_q.limit(5000)).all())
    facility_ids = [f.id for f in facilities]
    facility_observation_count = 0
    if facility_ids:
        obs_q = select(FacilityObservation).where(FacilityObservation.facility_id.in_(facility_ids))
        if public_only:
            obs_q = obs_q.where(FacilityObservation.public.is_(True))
        facility_observation_count = len(db.scalars(obs_q.limit(10000)).all())

    lanes = {"primary_official": 0, "operational": 0, "intergovernmental": 0, "harmonized_benchmark": 0, "published": 0, "context": 0}
    concepts: dict[str, int] = {}
    for c in candidates:
        role = authority_role(source_id=c.get("source_id"), publisher=c.get("publisher"), evidence_class=c.get("evidence_class"), semantic_role=c.get("semantic_role"), metadata=c.get("metadata") or {})
        c["authority_role"] = role
        concept = _norm(c.get("concept"))
        concepts[concept] = concepts.get(concept, 0) + 1
        if role in {"primary-official", "sector-official"}:
            lanes["primary_official"] += 1
        elif role == "operational-authority":
            lanes["operational"] += 1
        elif role == "intergovernmental":
            lanes["intergovernmental"] += 1
        elif role == "harmonized-benchmark":
            lanes["harmonized_benchmark"] += 1
        elif role == "knowledge-context":
            lanes["context"] += 1
        else:
            lanes["published"] += 1
    return {
        "country_code": code, "records": len(candidates), "lanes": lanes,
        "concepts": concepts, "facilities": len(facilities), "facility_observations": facility_observation_count,
        "automatic_blending": False, "zero_records_implication": "unknown-not-normal",
        "structural_and_operational_evidence_kept_separate": True,
        "subnational_and_national_scope_kept_separate": True,
    }


def persist_reconciliation(db: Session, result: dict[str, Any], *, public: bool = True) -> CountryEvidenceReconciliation:
    payload = {
        "country_code": result["country_code"], "concept": result["concept"],
        "candidates": result.get("candidates", []), "decision_state": result.get("decision_state"),
    }
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()
    existing = db.scalar(select(CountryEvidenceReconciliation).where(CountryEvidenceReconciliation.request_fingerprint == fingerprint))
    if existing:
        return existing
    selected = result.get("selected") or {}
    row = CountryEvidenceReconciliation(
        country_code=result["country_code"], concept=result["concept"], decision_state=result["decision_state"],
        selected_record_family=selected.get("record_family"), selected_record_id=selected.get("record_id"),
        selected_source=selected.get("publisher") or selected.get("source_id"), selected_authority_role=selected.get("authority_role"),
        request_fingerprint=fingerprint, candidates_json=result.get("candidates", []), rationale_json={
            "rationale": result.get("rationale", {}), "discrepancies": result.get("discrepancies", []),
            "do_not_blend": result.get("do_not_blend", True),
        }, public=public,
    )
    db.add(row); db.commit(); db.refresh(row); return row
