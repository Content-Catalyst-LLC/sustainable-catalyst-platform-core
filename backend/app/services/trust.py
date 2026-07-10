from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..hashing import sha256_payload
from ..models import (
    Entity,
    EvaluationCheckResult,
    EvaluationDefinition,
    EvaluationRun,
    KnownLimitation,
    TrustAttestation,
    TrustFinding,
    TrustIncident,
    ValidationEvent,
)
from ..schemas import (
    EvaluationDefinitionCreate,
    EvaluationDefinitionRead,
    EvaluationDefinitionUpdate,
    EvaluationRunCreate,
    EvaluationRunRead,
    EvaluationCheckRead,
    EvaluationSuiteRequest,
    EvaluationSuiteResult,
    KnownLimitationCreate,
    KnownLimitationRead,
    KnownLimitationUpdate,
    TrustAttestationCreate,
    TrustAttestationRead,
    TrustDomainStatus,
    TrustFindingCreate,
    TrustFindingRead,
    TrustFindingUpdate,
    TrustIncidentCreate,
    TrustIncidentRead,
    TrustIncidentUpdate,
    TrustStatusResponse,
)
from .developers import emit_webhook_event
from .evaluators import run_evaluator
from .ledger import append_ledger_entry, verify_ledger


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _not_found(label: str, record_id: str):
    raise HTTPException(status_code=404, detail=f"{label} not found: {record_id}")


def _validate_entity(db: Session, entity_id: str | None) -> None:
    if entity_id and db.get(Entity, entity_id) is None:
        _not_found("Entity", entity_id)


def get_definition_or_404(db: Session, definition_id: str) -> EvaluationDefinition:
    record = db.get(EvaluationDefinition, definition_id)
    return record if record else _not_found("Evaluation definition", definition_id)


def get_run_or_404(db: Session, run_id: str) -> EvaluationRun:
    record = db.get(EvaluationRun, run_id)
    return record if record else _not_found("Evaluation run", run_id)


def get_finding_or_404(db: Session, finding_id: str) -> TrustFinding:
    record = db.get(TrustFinding, finding_id)
    return record if record else _not_found("Trust finding", finding_id)


def get_incident_or_404(db: Session, incident_id: str) -> TrustIncident:
    record = db.get(TrustIncident, incident_id)
    return record if record else _not_found("Trust incident", incident_id)


def get_limitation_or_404(db: Session, limitation_id: str) -> KnownLimitation:
    record = db.get(KnownLimitation, limitation_id)
    return record if record else _not_found("Known limitation", limitation_id)


def get_attestation_or_404(db: Session, attestation_id: str) -> TrustAttestation:
    record = db.get(TrustAttestation, attestation_id)
    return record if record else _not_found("Trust attestation", attestation_id)


def create_definition(db: Session, payload: EvaluationDefinitionCreate) -> EvaluationDefinition:
    if db.get(EvaluationDefinition, payload.id):
        raise HTTPException(status_code=409, detail="Evaluation definition already exists.")
    data = payload.model_dump(exclude={"actor", "metadata"})
    definition = EvaluationDefinition(**data, metadata_json=payload.metadata)
    db.add(definition)
    db.flush()
    append_ledger_entry(db, record_type="evaluation_definition", record_id=definition.id, action="created", actor=payload.actor, payload={**data, "metadata": payload.metadata})
    emit_webhook_event(db, event_type="trust.evaluation_definition.created", resource_type="evaluation_definition", resource_id=definition.id, payload={"id": definition.id, "domain": definition.domain, "evaluator_kind": definition.evaluator_kind, "public": definition.public})
    db.commit(); db.refresh(definition)
    return definition


def update_definition(db: Session, definition_id: str, payload: EvaluationDefinitionUpdate) -> EvaluationDefinition:
    definition = get_definition_or_404(db, definition_id)
    changes = payload.model_dump(exclude={"actor"}, exclude_unset=True)
    if "metadata" in changes:
        changes["metadata_json"] = changes.pop("metadata")
    for key, value in changes.items(): setattr(definition, key, value)
    db.flush()
    append_ledger_entry(db, record_type="evaluation_definition", record_id=definition.id, action="updated", actor=payload.actor, payload={"changes": changes})
    emit_webhook_event(db, event_type="trust.evaluation_definition.updated", resource_type="evaluation_definition", resource_id=definition.id, payload={"id": definition.id, "changes": sorted(changes)})
    db.commit(); db.refresh(definition)
    return definition


def _overall_status(checks: list[dict]) -> str:
    statuses = {check["status"] for check in checks}
    if "error" in statuses or "failed" in statuses: return "failed"
    if "warning" in statuses: return "warning"
    if statuses and statuses <= {"not_applicable"}: return "not_applicable"
    return "passed"


def _score(checks: list[dict]) -> float | None:
    values = [float(check["score"]) for check in checks if check.get("score") is not None]
    return round(sum(values) / len(values), 3) if values else None


def _grade(score: float | None, status: str, thresholds: dict) -> str:
    if status == "not_applicable" or score is None: return "N/A"
    if status == "error": return "F"
    pass_score = float(thresholds.get("pass_score", 90.0))
    warning_score = float(thresholds.get("warning_score", 75.0))
    if score >= pass_score: return "A"
    if score >= warning_score: return "B"
    if score >= 60: return "C"
    if score >= 40: return "D"
    return "F"


def _summary(definition: EvaluationDefinition, status: str, score: float | None, checks: list[dict]) -> str:
    counts = {key: sum(1 for check in checks if check["status"] == key) for key in ("passed", "warning", "failed", "error", "not_applicable")}
    score_text = "not scored" if score is None else f"{score:.1f}/100"
    return f"{definition.name}: {status.replace('_', ' ')} ({score_text}); {counts['passed']} passed, {counts['warning']} warning, {counts['failed']} failed, {counts['error']} error, {counts['not_applicable']} not applicable."


def evaluation_run_read(db: Session, run: EvaluationRun) -> EvaluationRunRead:
    checks = list(db.scalars(select(EvaluationCheckResult).where(EvaluationCheckResult.run_id == run.id).order_by(EvaluationCheckResult.created_at, EvaluationCheckResult.check_key)).all())
    data = EvaluationRunRead.model_validate(run).model_dump(exclude={"checks"})
    return EvaluationRunRead(**data, checks=[EvaluationCheckRead.model_validate(check) for check in checks])


def run_evaluation(db: Session, definition_id: str, payload: EvaluationRunCreate, settings) -> EvaluationRunRead:
    definition = get_definition_or_404(db, definition_id)
    if not definition.active:
        raise HTTPException(status_code=422, detail="Evaluation definition is inactive.")
    _validate_entity(db, payload.target_entity_id)
    started = utcnow()
    checks_data = run_evaluator(definition.evaluator_kind, db, payload.observations, settings)
    status = _overall_status(checks_data)
    score = _score(checks_data)
    grade = _grade(score, status, definition.thresholds)
    completed = utcnow()
    public = definition.public if payload.public is None else payload.public
    run_id = f"sc:evaluation-run:{uuid.uuid4()}"
    core = {
        "id": run_id,
        "definition_id": definition.id,
        "target_entity_id": payload.target_entity_id,
        "status": status,
        "score": score,
        "grade": grade,
        "summary": _summary(definition, status, score, checks_data),
        "triggered_by": payload.triggered_by,
        "evaluator_version": definition.version,
        "observations": payload.observations,
        "environment": payload.environment,
        "evidence_references": payload.evidence_references,
        "public": public,
        "started_at": started,
        "completed_at": completed,
        "checks": checks_data,
    }
    run = EvaluationRun(id=run_id, definition_id=definition.id, target_entity_id=payload.target_entity_id, status=status, score=score, grade=grade, summary=core["summary"], triggered_by=payload.triggered_by, evaluator_version=definition.version, observations=payload.observations, environment=payload.environment, evidence_references=payload.evidence_references, content_hash=sha256_payload(core), public=public, started_at=started, completed_at=completed)
    db.add(run); db.flush()
    created_checks = []
    for check_data in checks_data:
        check = EvaluationCheckResult(run_id=run.id, **check_data)
        db.add(check); db.flush(); created_checks.append(check)
        db.add(ValidationEvent(entity_id=payload.target_entity_id, component=f"trust:{definition.domain}", check_name=check.check_key, status="passed" if check.status == "passed" else "warning" if check.status in {"warning", "not_applicable"} else "failed", severity=check.severity, details={"evaluation_run_id": run.id, "score": check.score, "observed": check.observed, "expected": check.expected}, observed_at=completed))
        if check.status in {"failed", "error"}:
            finding = TrustFinding(evaluation_run_id=run.id, check_result_id=check.id, target_entity_id=payload.target_entity_id, finding_type="evaluation", severity=check.severity if check.severity != "info" else definition.severity_on_failure, status="open", title=f"{definition.name}: {check.name}", description=check.details.get("reason") or f"The check {check.name} returned {check.status}.", remediation=check.details.get("remediation"), public=public, metadata_json={"definition_id": definition.id, "check_key": check.check_key})
            db.add(finding); db.flush()
            append_ledger_entry(db, record_type="trust_finding", record_id=finding.id, action="created_from_evaluation", actor=payload.triggered_by, payload={"evaluation_run_id": run.id, "check_result_id": check.id, "severity": finding.severity, "status": finding.status, "title": finding.title, "public": finding.public})
            emit_webhook_event(db, event_type="trust.finding.created", resource_type="trust_finding", resource_id=finding.id, payload={"id": finding.id, "evaluation_run_id": run.id, "severity": finding.severity, "status": finding.status, "public": finding.public})
    append_ledger_entry(db, record_type="evaluation_run", record_id=run.id, action="completed", actor=payload.triggered_by, payload={**core, "content_hash": run.content_hash})
    emit_webhook_event(db, event_type="trust.evaluation.completed", resource_type="evaluation_run", resource_id=run.id, payload={"id": run.id, "definition_id": definition.id, "domain": definition.domain, "target_entity_id": run.target_entity_id, "status": run.status, "score": run.score, "grade": run.grade, "public": run.public})
    db.commit(); db.refresh(run)
    return evaluation_run_read(db, run)


def run_suite(db: Session, payload: EvaluationSuiteRequest, settings) -> EvaluationSuiteResult:
    filters = [EvaluationDefinition.active.is_(True)]
    if payload.definition_ids:
        filters.append(EvaluationDefinition.id.in_(payload.definition_ids))
    else:
        filters.append(
            EvaluationDefinition.evaluator_kind.in_(
                [
                    "ledger_integrity",
                    "public_api_readiness",
                    "evidence_review_coverage",
                    "webhook_delivery_reliability",
                ]
            )
        )
    definitions = list(db.scalars(select(EvaluationDefinition).where(*filters).order_by(EvaluationDefinition.sort_order, EvaluationDefinition.id)).all())
    if payload.definition_ids:
        found = {definition.id for definition in definitions}
        missing = sorted(set(payload.definition_ids) - found)
        if missing: raise HTTPException(status_code=404, detail={"missing_evaluation_definitions": missing})
    runs = []
    for definition in definitions:
        runs.append(run_evaluation(db, definition.id, EvaluationRunCreate(target_entity_id=payload.target_entity_id, triggered_by=payload.triggered_by, observations=payload.contexts.get(definition.id, {}), environment=payload.environment, evidence_references=[], public=payload.public), settings))
    return EvaluationSuiteResult(runs=runs, total=len(runs), passed=sum(run.status == "passed" for run in runs), warnings=sum(run.status == "warning" for run in runs), failed=sum(run.status in {"failed", "error"} for run in runs), not_applicable=sum(run.status == "not_applicable" for run in runs))


def create_finding(db: Session, payload: TrustFindingCreate) -> TrustFinding:
    if payload.evaluation_run_id: get_run_or_404(db, payload.evaluation_run_id)
    if payload.check_result_id and db.get(EvaluationCheckResult, payload.check_result_id) is None: _not_found("Evaluation check result", payload.check_result_id)
    _validate_entity(db, payload.target_entity_id)
    finding = TrustFinding(**payload.model_dump(exclude={"actor", "metadata"}), metadata_json=payload.metadata)
    db.add(finding); db.flush()
    append_ledger_entry(db, record_type="trust_finding", record_id=finding.id, action="created", actor=payload.actor, payload={**payload.model_dump(exclude={"actor"}), "metadata": payload.metadata})
    emit_webhook_event(db, event_type="trust.finding.created", resource_type="trust_finding", resource_id=finding.id, payload={"id": finding.id, "severity": finding.severity, "status": finding.status, "public": finding.public})
    db.commit(); db.refresh(finding); return finding


def update_finding(db: Session, finding_id: str, payload: TrustFindingUpdate) -> TrustFinding:
    finding = get_finding_or_404(db, finding_id); changes = payload.model_dump(exclude={"actor"}, exclude_unset=True)
    if "metadata" in changes: changes["metadata_json"] = changes.pop("metadata")
    if changes.get("status") == "resolved" and finding.status != "resolved": changes["resolved_at"] = utcnow()
    for key, value in changes.items(): setattr(finding, key, value)
    db.flush(); append_ledger_entry(db, record_type="trust_finding", record_id=finding.id, action="updated", actor=payload.actor, payload={"changes": changes})
    emit_webhook_event(db, event_type="trust.finding.updated", resource_type="trust_finding", resource_id=finding.id, payload={"id": finding.id, "status": finding.status, "severity": finding.severity})
    db.commit(); db.refresh(finding); return finding


def create_incident(db: Session, payload: TrustIncidentCreate) -> TrustIncident:
    for entity_id in payload.affected_entity_ids: _validate_entity(db, entity_id)
    data = payload.model_dump(exclude={"actor", "metadata", "started_at", "detected_at"})
    incident = TrustIncident(**data, started_at=payload.started_at or utcnow(), detected_at=payload.detected_at or utcnow(), metadata_json=payload.metadata)
    db.add(incident); db.flush(); append_ledger_entry(db, record_type="trust_incident", record_id=incident.id, action="created", actor=payload.actor, payload={**payload.model_dump(exclude={"actor"}), "metadata": payload.metadata})
    emit_webhook_event(db, event_type="trust.incident.created", resource_type="trust_incident", resource_id=incident.id, payload={"id": incident.id, "title": incident.title, "severity": incident.severity, "status": incident.status, "public": incident.public})
    db.commit(); db.refresh(incident); return incident


def update_incident(db: Session, incident_id: str, payload: TrustIncidentUpdate) -> TrustIncident:
    incident = get_incident_or_404(db, incident_id); changes = payload.model_dump(exclude={"actor"}, exclude_unset=True)
    if "metadata" in changes: changes["metadata_json"] = changes.pop("metadata")
    if changes.get("status") == "resolved" and not changes.get("resolved_at"): changes["resolved_at"] = utcnow()
    for entity_id in changes.get("affected_entity_ids", []): _validate_entity(db, entity_id)
    for key, value in changes.items(): setattr(incident, key, value)
    db.flush(); append_ledger_entry(db, record_type="trust_incident", record_id=incident.id, action="updated", actor=payload.actor, payload={"changes": changes})
    emit_webhook_event(db, event_type="trust.incident.updated", resource_type="trust_incident", resource_id=incident.id, payload={"id": incident.id, "severity": incident.severity, "status": incident.status, "public": incident.public})
    db.commit(); db.refresh(incident); return incident


def create_limitation(db: Session, payload: KnownLimitationCreate) -> KnownLimitation:
    for entity_id in payload.affected_entity_ids: _validate_entity(db, entity_id)
    limitation = KnownLimitation(**payload.model_dump(exclude={"actor", "metadata"}), metadata_json=payload.metadata)
    db.add(limitation); db.flush(); append_ledger_entry(db, record_type="known_limitation", record_id=limitation.id, action="created", actor=payload.actor, payload={**payload.model_dump(exclude={"actor"}), "metadata": payload.metadata})
    emit_webhook_event(db, event_type="trust.limitation.created", resource_type="known_limitation", resource_id=limitation.id, payload={"id": limitation.id, "domain": limitation.domain, "status": limitation.status, "public": limitation.public})
    db.commit(); db.refresh(limitation); return limitation


def update_limitation(db: Session, limitation_id: str, payload: KnownLimitationUpdate) -> KnownLimitation:
    limitation = get_limitation_or_404(db, limitation_id); changes = payload.model_dump(exclude={"actor"}, exclude_unset=True)
    if "metadata" in changes: changes["metadata_json"] = changes.pop("metadata")
    for entity_id in changes.get("affected_entity_ids", []): _validate_entity(db, entity_id)
    for key, value in changes.items(): setattr(limitation, key, value)
    db.flush(); append_ledger_entry(db, record_type="known_limitation", record_id=limitation.id, action="updated", actor=payload.actor, payload={"changes": changes})
    emit_webhook_event(db, event_type="trust.limitation.updated", resource_type="known_limitation", resource_id=limitation.id, payload={"id": limitation.id, "domain": limitation.domain, "status": limitation.status, "public": limitation.public})
    db.commit(); db.refresh(limitation); return limitation


def create_attestation(db: Session, payload: TrustAttestationCreate) -> TrustAttestation:
    _validate_entity(db, payload.subject_entity_id)
    valid_from = payload.valid_from or utcnow()
    valid_from = aware(valid_from)
    valid_until = aware(payload.valid_until)
    if valid_until and valid_until <= valid_from: raise HTTPException(status_code=422, detail="valid_until must be later than valid_from.")
    core = payload.model_dump(exclude={"actor", "metadata", "valid_from", "valid_until"}); core["valid_from"] = valid_from; core["valid_until"] = valid_until
    attestation = TrustAttestation(**core, content_hash=sha256_payload({**core, "metadata": payload.metadata}), metadata_json=payload.metadata)
    db.add(attestation); db.flush(); append_ledger_entry(db, record_type="trust_attestation", record_id=attestation.id, action="issued", actor=payload.actor, payload={**core, "content_hash": attestation.content_hash, "metadata": payload.metadata})
    emit_webhook_event(db, event_type="trust.attestation.issued", resource_type="trust_attestation", resource_id=attestation.id, payload={"id": attestation.id, "subject_entity_id": attestation.subject_entity_id, "scope": attestation.scope, "issuer": attestation.issuer, "public": attestation.public})
    db.commit(); db.refresh(attestation); return attestation


def revoke_attestation(db: Session, attestation_id: str, reason: str, revoked_by: str) -> TrustAttestation:
    attestation = get_attestation_or_404(db, attestation_id); attestation.status = "revoked"; attestation.revoked_at = utcnow(); attestation.revocation_reason = reason
    db.flush(); append_ledger_entry(db, record_type="trust_attestation", record_id=attestation.id, action="revoked", actor=revoked_by, payload={"reason": reason, "revoked_at": attestation.revoked_at})
    emit_webhook_event(db, event_type="trust.attestation.revoked", resource_type="trust_attestation", resource_id=attestation.id, payload={"id": attestation.id, "subject_entity_id": attestation.subject_entity_id, "scope": attestation.scope})
    db.commit(); db.refresh(attestation); return attestation


def build_trust_status(db: Session, settings, *, public_only: bool = True) -> TrustStatusResponse:
    definitions = list(db.scalars(select(EvaluationDefinition).where(EvaluationDefinition.active.is_(True), *( [EvaluationDefinition.public.is_(True)] if public_only else [])).order_by(EvaluationDefinition.sort_order)).all())
    all_runs = list(db.scalars(select(EvaluationRun).where(*( [EvaluationRun.public.is_(True)] if public_only else [])).order_by(EvaluationRun.completed_at.desc())).all())
    latest_by_definition = {}
    for run in all_runs:
        latest_by_definition.setdefault(run.definition_id, run)
    finding_filters = [TrustFinding.status.in_(["open", "accepted"])]
    if public_only: finding_filters.append(TrustFinding.public.is_(True))
    findings = list(db.scalars(select(TrustFinding).where(*finding_filters)).all())
    domains = []
    grouped = {}
    for definition in definitions: grouped.setdefault(definition.domain, []).append(definition)
    stale_cutoff = utcnow() - timedelta(days=settings.trust_stale_after_days)
    for domain, domain_defs in sorted(grouped.items()):
        runs = [latest_by_definition.get(defn.id) for defn in domain_defs if latest_by_definition.get(defn.id)]
        domain_findings = [finding for finding in findings if finding.evaluation_run_id and any(run.id == finding.evaluation_run_id for run in runs)]
        scores = [run.score for run in runs if run.score is not None]
        score = round(sum(scores)/len(scores), 3) if scores else None
        latest = max((aware(run.completed_at) for run in runs), default=None)
        stale = bool(latest and latest < stale_cutoff)
        statuses = {run.status for run in runs}
        if not runs: status, grade, summary = "unknown", "N/A", "No public evaluation has been completed for this domain."
        elif "failed" in statuses or "error" in statuses: status, grade, summary = "degraded", "F" if score is None or score < 40 else "D", "One or more latest evaluations failed."
        elif stale: status, grade, summary = "attention", "C", f"The latest evaluation is older than {settings.trust_stale_after_days} days."
        elif "warning" in statuses or domain_findings: status, grade, summary = "attention", "B", "The domain has warnings or open findings."
        elif statuses <= {"not_applicable"}: status, grade, summary = "unknown", "N/A", "Latest evaluations were not applicable."
        else: status, grade, summary = "operational", "A", "Latest evaluations passed."
        domains.append(TrustDomainStatus(domain=domain, status=status, score=score, grade=grade, latest_run_id=max(runs, key=lambda run: aware(run.completed_at)).id if runs else None, latest_completed_at=latest, evaluation_count=len(runs), open_findings=len(domain_findings), summary=summary))
    incident_filters = [TrustIncident.status != "resolved"]
    limitation_filters = [KnownLimitation.status == "active"]
    attestation_filters = [TrustAttestation.status == "active"]
    if public_only:
        incident_filters.append(TrustIncident.public.is_(True)); limitation_filters.append(KnownLimitation.public.is_(True)); attestation_filters.append(TrustAttestation.public.is_(True))
    incidents = list(db.scalars(select(TrustIncident).where(*incident_filters).order_by(TrustIncident.started_at.desc())).all())
    limitations = list(db.scalars(select(KnownLimitation).where(*limitation_filters).order_by(KnownLimitation.domain, KnownLimitation.title)).all())
    now = utcnow(); attestations = list(db.scalars(select(TrustAttestation).where(*attestation_filters).order_by(TrustAttestation.valid_from.desc())).all())
    attestations = [a for a in attestations if not a.valid_until or aware(a.valid_until) > now]
    scores = [domain.score for domain in domains if domain.score is not None]
    overall_score = round(sum(scores)/len(scores), 3) if scores else None
    severity_set = {incident.severity for incident in incidents}
    domain_statuses = {domain.status for domain in domains}
    ledger = verify_ledger(db)
    if not ledger.valid: overall_status = "critical"
    elif "critical" in severity_set: overall_status = "critical"
    elif "high" in severity_set or "degraded" in domain_statuses: overall_status = "degraded"
    elif incidents or findings or "attention" in domain_statuses: overall_status = "attention"
    elif domains and domain_statuses <= {"operational", "unknown"} and "operational" in domain_statuses: overall_status = "operational"
    else: overall_status = "unknown"
    if overall_score is None: grade = "N/A"
    elif overall_score >= 90: grade = "A"
    elif overall_score >= 75: grade = "B"
    elif overall_score >= 60: grade = "C"
    elif overall_score >= 40: grade = "D"
    else: grade = "F"
    last_evaluated = max((aware(run.completed_at) for run in all_runs), default=None)
    return TrustStatusResponse(service=settings.app_name, platform_version=settings.version, overall_status=overall_status, overall_score=overall_score, grade=grade, generated_at=now, ledger_valid=ledger.valid, last_evaluated_at=last_evaluated, domains=domains, active_incidents=[TrustIncidentRead.model_validate(record) for record in incidents], known_limitations=[KnownLimitationRead.model_validate(record) for record in limitations], active_attestations=[TrustAttestationRead.model_validate(record) for record in attestations], open_findings=len(findings), public_evaluation_runs=len(all_runs), methodology="Overall status is derived from the latest public evaluation per active definition, active public incidents, open public findings, evaluation freshness, and ledger-chain verification. Scores never override disclosed incidents or limitations.")
