from __future__ import annotations

from datetime import datetime, timezone
import hmac
import hashlib
import uuid

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..hashing import canonical_json, sha256_payload
from ..models import (
    CalculationTrace,
    ClaimRecord,
    DossierApproval,
    DossierRecord,
    Entity,
    EvaluationCheckResult,
    EvaluationRun,
    EvidenceRecord,
    KnownLimitation,
    LedgerEntry,
    ProvenanceActivity,
    Relationship,
    SignatureDossier,
    SourceSnapshot,
    TrustAttestation,
    TrustFinding,
    TrustIncident,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStep,
    WorkflowTransition,
)
from ..schemas import (
    DossierApprovalCreate,
    DossierApprovalRead,
    DossierCreate,
    DossierRead,
    DossierRecordCreate,
    DossierRecordRead,
    DossierVerificationResult,
    WorkflowRunCreate,
    WorkflowRunRead,
    WorkflowStepRead,
    WorkflowStepTransition,
    WorkflowTransitionRead,
)
from .developers import emit_webhook_event
from .evidence import build_evidence_manifest
from .ledger import append_ledger_entry
from .relationships import neighborhood
from .trust import build_trust_status


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _not_found(label: str, record_id: str):
    raise HTTPException(status_code=404, detail=f"{label} not found: {record_id}")


def get_workflow_definition_or_404(db: Session, definition_id: str) -> WorkflowDefinition:
    record = db.get(WorkflowDefinition, definition_id)
    return record if record else _not_found("Workflow definition", definition_id)


def get_workflow_run_or_404(db: Session, run_id: str) -> WorkflowRun:
    record = db.get(WorkflowRun, run_id)
    return record if record else _not_found("Workflow run", run_id)


def get_workflow_step_or_404(db: Session, run_id: str, step_key: str) -> WorkflowStep:
    record = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == run_id, WorkflowStep.step_key == step_key))
    return record if record else _not_found("Workflow step", f"{run_id}/{step_key}")


def get_dossier_or_404(db: Session, dossier_id: str) -> SignatureDossier:
    record = db.get(SignatureDossier, dossier_id)
    return record if record else _not_found("Signature dossier", dossier_id)


def _orm_dict(record) -> dict:
    mapper = inspect(record).mapper
    return jsonable_encoder({column.key: getattr(record, column.key) for column in mapper.columns})


def _transition(
    db: Session,
    *,
    run: WorkflowRun,
    step: WorkflowStep | None,
    from_status: str | None,
    to_status: str,
    actor: str,
    reason: str | None,
    payload: dict | None = None,
) -> WorkflowTransition:
    core = {
        "run_id": run.id,
        "step_id": step.id if step else None,
        "from_status": from_status,
        "to_status": to_status,
        "actor": actor,
        "reason": reason,
        "payload": payload or {},
        "created_at": utcnow(),
    }
    transition = WorkflowTransition(
        run_id=run.id,
        step_id=step.id if step else None,
        from_status=from_status,
        to_status=to_status,
        actor=actor,
        reason=reason,
        payload_json=payload or {},
        content_hash=sha256_payload(core),
        created_at=core["created_at"],
    )
    db.add(transition)
    db.flush()
    append_ledger_entry(
        db,
        record_type="workflow_transition",
        record_id=transition.id,
        action="transitioned",
        actor=actor,
        payload={**core, "content_hash": transition.content_hash},
    )
    emit_webhook_event(
        db,
        event_type="workflow.transitioned",
        resource_type="workflow_run",
        resource_id=run.id,
        payload={
            "run_id": run.id,
            "step_key": step.step_key if step else None,
            "from_status": from_status,
            "to_status": to_status,
            "actor": actor,
        },
    )
    return transition


def workflow_run_read(db: Session, run: WorkflowRun) -> WorkflowRunRead:
    steps = list(db.scalars(select(WorkflowStep).where(WorkflowStep.run_id == run.id).order_by(WorkflowStep.sequence)).all())
    transitions = list(db.scalars(select(WorkflowTransition).where(WorkflowTransition.run_id == run.id).order_by(WorkflowTransition.created_at, WorkflowTransition.id)).all())
    data = WorkflowRunRead.model_validate(run).model_dump(exclude={"steps", "transitions"})
    return WorkflowRunRead(
        **data,
        steps=[WorkflowStepRead.model_validate(step) for step in steps],
        transitions=[WorkflowTransitionRead.model_validate(item) for item in transitions],
    )


def create_workflow_run(db: Session, payload: WorkflowRunCreate) -> WorkflowRunRead:
    definition = get_workflow_definition_or_404(db, payload.definition_id)
    if not definition.active:
        raise HTTPException(status_code=422, detail="Workflow definition is inactive.")
    if payload.subject_entity_id and db.get(Entity, payload.subject_entity_id) is None:
        _not_found("Entity", payload.subject_entity_id)
    run = WorkflowRun(
        definition_id=definition.id,
        title=payload.title,
        subject_entity_id=payload.subject_entity_id,
        status="draft",
        requested_by=payload.requested_by,
        owner=payload.owner,
        context_json=payload.context,
        public=payload.public,
        metadata_json=payload.metadata,
    )
    db.add(run); db.flush()
    for sequence, stage in enumerate(definition.stages, start=1):
        db.add(WorkflowStep(
            run_id=run.id,
            step_key=stage["key"],
            name=stage.get("name", stage["key"]),
            sequence=sequence,
            product=stage.get("product", "platform-core"),
            action=stage.get("action", stage["key"]),
            required=bool(stage.get("required", True)),
            assigned_to=stage.get("assigned_to"),
            metadata_json=stage.get("metadata", {}),
        ))
    db.flush()
    _transition(db, run=run, step=None, from_status=None, to_status="draft", actor=payload.requested_by, reason="Workflow created.", payload={"definition_id": definition.id})
    emit_webhook_event(db, event_type="workflow.created", resource_type="workflow_run", resource_id=run.id, payload={"id":run.id,"definition_id":definition.id,"title":run.title,"subject_entity_id":run.subject_entity_id,"public":run.public})
    db.commit(); db.refresh(run)
    return workflow_run_read(db, run)


def start_workflow_run(db: Session, run_id: str, actor: str, reason: str | None) -> WorkflowRunRead:
    run = get_workflow_run_or_404(db, run_id)
    if run.status != "draft":
        raise HTTPException(status_code=422, detail="Only a draft workflow can be started.")
    first = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == run.id).order_by(WorkflowStep.sequence).limit(1))
    previous = run.status
    run.status = "in_progress"
    run.current_step_key = first.step_key if first else None
    run.started_at = utcnow()
    db.add(run); db.flush()
    _transition(db, run=run, step=None, from_status=previous, to_status=run.status, actor=actor, reason=reason or "Workflow started.", payload={"current_step_key":run.current_step_key})
    db.commit(); db.refresh(run)
    return workflow_run_read(db, run)


def _prior_required_incomplete(db: Session, step: WorkflowStep) -> list[WorkflowStep]:
    return list(db.scalars(select(WorkflowStep).where(
        WorkflowStep.run_id == step.run_id,
        WorkflowStep.sequence < step.sequence,
        WorkflowStep.required.is_(True),
        WorkflowStep.status.not_in(["completed", "skipped"]),
    ).order_by(WorkflowStep.sequence)).all())


def transition_workflow_step(db: Session, run_id: str, step_key: str, payload: WorkflowStepTransition) -> WorkflowRunRead:
    run = get_workflow_run_or_404(db, run_id)
    if run.status in {"completed", "cancelled"}:
        raise HTTPException(status_code=422, detail="The workflow is already closed.")
    if run.status == "draft":
        raise HTTPException(status_code=422, detail="Start the workflow before transitioning a step.")
    step = get_workflow_step_or_404(db, run_id, step_key)
    allowed = {
        "pending": {"in_progress", "blocked", "skipped"},
        "in_progress": {"completed", "blocked", "failed"},
        "blocked": {"in_progress", "skipped", "failed"},
        "failed": {"in_progress", "skipped"},
        "completed": set(),
        "skipped": set(),
    }
    if payload.status not in allowed.get(step.status, set()):
        raise HTTPException(status_code=422, detail=f"Invalid step transition: {step.status} -> {payload.status}")
    if payload.status == "in_progress":
        blockers = _prior_required_incomplete(db, step)
        if blockers:
            raise HTTPException(status_code=409, detail={"message":"Earlier required workflow steps are incomplete.","blocking_steps":[item.step_key for item in blockers]})
    previous = step.status
    step.status = payload.status
    if payload.assigned_to is not None: step.assigned_to = payload.assigned_to
    if payload.input_references is not None: step.input_references = payload.input_references
    if payload.output_references is not None: step.output_references = payload.output_references
    if payload.notes is not None: step.notes = payload.notes
    if payload.status == "in_progress" and step.started_at is None: step.started_at = utcnow()
    if payload.status in {"completed", "skipped", "failed"}: step.completed_at = utcnow()
    db.add(step); db.flush()
    _transition(db, run=run, step=step, from_status=previous, to_status=step.status, actor=payload.actor, reason=payload.reason, payload={"input_references":step.input_references,"output_references":step.output_references,**payload.payload})

    steps = list(db.scalars(select(WorkflowStep).where(WorkflowStep.run_id == run.id).order_by(WorkflowStep.sequence)).all())
    if step.status in {"blocked", "failed"}:
        if run.status != "blocked":
            old_run_status = run.status; run.status = "blocked"
            _transition(db, run=run, step=None, from_status=old_run_status, to_status="blocked", actor=payload.actor, reason=f"Step {step.step_key} is {step.status}.", payload={"step_key":step.step_key})
    else:
        incomplete_required = [item for item in steps if item.required and item.status not in {"completed", "skipped"}]
        if not incomplete_required:
            old_run_status = run.status
            run.status = "completed"
            run.current_step_key = None
            run.completed_at = utcnow()
            run.content_hash = sha256_payload({"run":_orm_dict(run),"steps":[_orm_dict(item) for item in steps]})
            _transition(db, run=run, step=None, from_status=old_run_status, to_status="completed", actor=payload.actor, reason="All required workflow steps are complete.", payload={"content_hash":run.content_hash})
            emit_webhook_event(db, event_type="workflow.completed", resource_type="workflow_run", resource_id=run.id, payload={"id":run.id,"definition_id":run.definition_id,"content_hash":run.content_hash})
        else:
            next_step = incomplete_required[0]
            old_run_status = run.status
            run.status = "in_progress"
            run.current_step_key = next_step.step_key
            if old_run_status == "blocked":
                _transition(db, run=run, step=None, from_status=old_run_status, to_status="in_progress", actor=payload.actor, reason="Workflow resumed.", payload={"current_step_key":next_step.step_key})
    db.add(run); db.commit(); db.refresh(run)
    return workflow_run_read(db, run)


def cancel_workflow_run(db: Session, run_id: str, actor: str, reason: str) -> WorkflowRunRead:
    run = get_workflow_run_or_404(db, run_id)
    if run.status in {"completed", "cancelled"}:
        raise HTTPException(status_code=422, detail="The workflow is already closed.")
    previous = run.status; run.status = "cancelled"; run.completed_at = utcnow(); run.current_step_key = None
    _transition(db, run=run, step=None, from_status=previous, to_status="cancelled", actor=actor, reason=reason)
    db.commit(); db.refresh(run)
    return workflow_run_read(db, run)


def _snapshot_record(db: Session, record_type: str, record_id: str, settings) -> dict:
    model_map = {
        "entity": Entity,
        "relationship": Relationship,
        "claim": ClaimRecord,
        "source_snapshot": SourceSnapshot,
        "calculation_trace": CalculationTrace,
        "provenance_activity": ProvenanceActivity,
        "evidence": EvidenceRecord,
        "trust_finding": TrustFinding,
        "trust_incident": TrustIncident,
        "known_limitation": KnownLimitation,
        "trust_attestation": TrustAttestation,
    }
    if record_type in model_map:
        record = db.get(model_map[record_type], record_id)
        if record is None: _not_found(record_type.replace("_", " ").title(), record_id)
        return {"record_type":record_type,"record_id":record_id,"record":_orm_dict(record)}
    if record_type == "evaluation_run":
        run = db.get(EvaluationRun, record_id)
        if run is None: _not_found("Evaluation run", record_id)
        checks = list(db.scalars(select(EvaluationCheckResult).where(EvaluationCheckResult.run_id == run.id).order_by(EvaluationCheckResult.check_key)).all())
        return {"record_type":record_type,"record_id":record_id,"record":_orm_dict(run),"checks":[_orm_dict(item) for item in checks]}
    if record_type == "workflow_run":
        return {"record_type":record_type,"record_id":record_id,"record":workflow_run_read(db, get_workflow_run_or_404(db, record_id)).model_dump(mode="json")}
    if record_type == "evidence_manifest":
        return {"record_type":record_type,"record_id":record_id,"record":build_evidence_manifest(db, record_id).model_dump(mode="json")}
    if record_type == "trust_status":
        if record_id != "platform": raise HTTPException(status_code=422, detail="The trust_status record ID must be 'platform'.")
        return {"record_type":record_type,"record_id":record_id,"record":build_trust_status(db, settings, public_only=False).model_dump(mode="json")}
    if record_type == "graph_neighborhood":
        root, groups, total = neighborhood(db, root_id=record_id, statuses=["verified","approved"], min_confidence=0.0)
        return {"record_type":record_type,"record_id":record_id,"record":{"root":jsonable_encoder(root),"groups":jsonable_encoder(groups),"total_relationships":total}}
    if record_type == "ledger_entry":
        record = db.scalar(select(LedgerEntry).where(LedgerEntry.id == record_id))
        if record is None: _not_found("Ledger entry", record_id)
        return {"record_type":record_type,"record_id":record_id,"record":_orm_dict(record)}
    raise HTTPException(status_code=422, detail=f"Unsupported dossier record type: {record_type}")


def dossier_read(db: Session, dossier: SignatureDossier, *, include_private_records: bool = True) -> DossierRead:
    filters = [DossierRecord.dossier_id == dossier.id]
    if not include_private_records: filters.append(DossierRecord.public.is_(True))
    records = list(db.scalars(select(DossierRecord).where(*filters).order_by(DossierRecord.section, DossierRecord.sort_order, DossierRecord.created_at)).all())
    approvals = list(db.scalars(select(DossierApproval).where(DossierApproval.dossier_id == dossier.id).order_by(DossierApproval.created_at)).all())
    workflow = workflow_run_read(db, get_workflow_run_or_404(db, dossier.workflow_run_id)) if dossier.workflow_run_id else None
    data = DossierRead.model_validate(dossier).model_dump(exclude={"records","approvals","workflow"})
    return DossierRead(**data, records=[DossierRecordRead.model_validate(item) for item in records], approvals=[DossierApprovalRead.model_validate(item) for item in approvals], workflow=workflow)


def create_dossier(db: Session, payload: DossierCreate) -> DossierRead:
    if payload.workflow_run_id: get_workflow_run_or_404(db, payload.workflow_run_id)
    if payload.subject_entity_id and db.get(Entity, payload.subject_entity_id) is None: _not_found("Entity", payload.subject_entity_id)
    if payload.supersedes_dossier_id: get_dossier_or_404(db, payload.supersedes_dossier_id)
    dossier = SignatureDossier(workflow_run_id=payload.workflow_run_id, subject_entity_id=payload.subject_entity_id, title=payload.title, purpose=payload.purpose, version=payload.version, status="draft", visibility=payload.visibility, supersedes_dossier_id=payload.supersedes_dossier_id, metadata_json=payload.metadata)
    db.add(dossier); db.flush()
    append_ledger_entry(db, record_type="signature_dossier", record_id=dossier.id, action="created", actor=payload.actor, payload={"title":dossier.title,"workflow_run_id":dossier.workflow_run_id,"subject_entity_id":dossier.subject_entity_id,"visibility":dossier.visibility,"version":dossier.version})
    emit_webhook_event(db, event_type="dossier.created", resource_type="signature_dossier", resource_id=dossier.id, payload={"id":dossier.id,"title":dossier.title,"workflow_run_id":dossier.workflow_run_id,"visibility":dossier.visibility})
    db.commit(); db.refresh(dossier)
    return dossier_read(db, dossier)


def add_dossier_record(db: Session, dossier_id: str, payload: DossierRecordCreate, settings) -> DossierRecord:
    dossier = get_dossier_or_404(db, dossier_id)
    if dossier.status != "draft": raise HTTPException(status_code=422, detail="Records can only be added to a draft dossier.")
    count = int(db.scalar(select(func.count()).select_from(DossierRecord).where(DossierRecord.dossier_id == dossier.id)) or 0)
    if count >= settings.dossier_max_records: raise HTTPException(status_code=413, detail="Dossier record limit reached.")
    snapshot = _snapshot_record(db, payload.record_type, payload.record_id, settings)
    record = DossierRecord(dossier_id=dossier.id, section=payload.section, record_type=payload.record_type, record_id=payload.record_id, label=payload.label, sort_order=payload.sort_order, snapshot_hash=sha256_payload(snapshot), snapshot_json=snapshot, public=payload.public, metadata_json=payload.metadata)
    db.add(record)
    try: db.flush()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="This record is already included in the dossier.") from exc
    append_ledger_entry(db, record_type="dossier_record", record_id=record.id, action="snapshotted", actor=payload.actor, payload={"dossier_id":dossier.id,"section":record.section,"record_type":record.record_type,"record_id":record.record_id,"snapshot_hash":record.snapshot_hash,"public":record.public})
    db.commit(); db.refresh(record)
    return record


def add_dossier_approval(db: Session, dossier_id: str, payload: DossierApprovalCreate) -> DossierApproval:
    dossier = get_dossier_or_404(db, dossier_id)
    if dossier.status != "draft": raise HTTPException(status_code=422, detail="Approvals can only be added to a draft dossier.")
    core = {"dossier_id":dossier.id,"decision":payload.decision,"signer":payload.signer,"role":payload.role,"statement":payload.statement,"evidence_references":payload.evidence_references,"created_at":utcnow()}
    approval = DossierApproval(dossier_id=dossier.id, decision=payload.decision, signer=payload.signer, role=payload.role, statement=payload.statement, evidence_references=payload.evidence_references, content_hash=sha256_payload(core), created_at=core["created_at"])
    db.add(approval); db.flush()
    append_ledger_entry(db, record_type="dossier_approval", record_id=approval.id, action=payload.decision, actor=payload.signer, payload={**core,"content_hash":approval.content_hash})
    emit_webhook_event(db, event_type="dossier.approval_recorded", resource_type="signature_dossier", resource_id=dossier.id, payload={"dossier_id":dossier.id,"decision":approval.decision,"signer":approval.signer,"role":approval.role})
    db.commit(); db.refresh(approval)
    return approval


def _latest_approval_state(approvals: list[DossierApproval]) -> dict[str, DossierApproval]:
    latest: dict[str, DossierApproval] = {}
    for approval in approvals: latest[approval.signer] = approval
    return latest


def _signature(secret: str, dossier_hash: str) -> str:
    return hmac.new(secret.encode("utf-8"), dossier_hash.encode("utf-8"), hashlib.sha256).hexdigest()


def finalize_dossier(db: Session, dossier_id: str, signed_by: str, actor: str, settings) -> DossierRead:
    dossier = get_dossier_or_404(db, dossier_id)
    if dossier.status != "draft": raise HTTPException(status_code=422, detail="Only a draft dossier can be finalized.")
    if settings.environment == "production" and not settings.dossier_signing_secret:
        raise HTTPException(status_code=503, detail="Dossier signing is unavailable because the production signing secret is not configured.")
    if not settings.dossier_signing_secret:
        raise HTTPException(status_code=503, detail="Dossier signing secret is not configured.")
    if dossier.workflow_run_id:
        workflow = get_workflow_run_or_404(db, dossier.workflow_run_id)
        if workflow.status != "completed": raise HTTPException(status_code=409, detail="The linked workflow must be completed before dossier finalization.")
    records = list(db.scalars(select(DossierRecord).where(DossierRecord.dossier_id == dossier.id).order_by(DossierRecord.section, DossierRecord.sort_order, DossierRecord.created_at)).all())
    if not records: raise HTTPException(status_code=422, detail="A dossier must contain at least one record.")
    approvals = list(db.scalars(select(DossierApproval).where(DossierApproval.dossier_id == dossier.id).order_by(DossierApproval.created_at)).all())
    latest = _latest_approval_state(approvals)
    blocking = [item for item in latest.values() if item.decision in {"reject","request_changes"}]
    approved = [item for item in latest.values() if item.decision == "approve"]
    if blocking: raise HTTPException(status_code=409, detail={"message":"Dossier has unresolved rejection or change requests.","blocking_signers":[item.signer for item in blocking]})
    if len(approved) < settings.dossier_required_approvals:
        raise HTTPException(status_code=409, detail=f"Dossier requires at least {settings.dossier_required_approvals} current approval(s).")
    signed_at = utcnow()
    workflow_snapshot = workflow_run_read(db, get_workflow_run_or_404(db, dossier.workflow_run_id)).model_dump(mode="json") if dossier.workflow_run_id else None
    snapshot = {
        "schema": "sustainable-catalyst-signature-dossier-v1",
        "dossier": {"id":dossier.id,"title":dossier.title,"purpose":dossier.purpose,"version":dossier.version,"visibility":dossier.visibility,"workflow_run_id":dossier.workflow_run_id,"subject_entity_id":dossier.subject_entity_id,"supersedes_dossier_id":dossier.supersedes_dossier_id,"metadata":dossier.metadata_json},
        "workflow": workflow_snapshot,
        "records": [{"id":item.id,"section":item.section,"record_type":item.record_type,"record_id":item.record_id,"label":item.label,"sort_order":item.sort_order,"snapshot_hash":item.snapshot_hash,"snapshot":item.snapshot_json,"public":item.public,"metadata":item.metadata_json} for item in records],
        "approvals": [{"id":item.id,"decision":item.decision,"signer":item.signer,"role":item.role,"statement":item.statement,"evidence_references":item.evidence_references,"content_hash":item.content_hash,"created_at":item.created_at} for item in approvals],
        "signature_context": {"signed_by":signed_by,"signed_at":signed_at,"algorithm":"HMAC-SHA256","signing_key_id":settings.dossier_signing_key_id},
    }
    dossier_hash = sha256_payload(snapshot)
    dossier.status = "finalized"; dossier.dossier_hash = dossier_hash; dossier.signature_algorithm = "HMAC-SHA256"; dossier.platform_signature = _signature(settings.dossier_signing_secret, dossier_hash); dossier.signing_key_id = settings.dossier_signing_key_id; dossier.signed_by = signed_by; dossier.signed_at = signed_at; dossier.snapshot_json = jsonable_encoder(snapshot)
    db.add(dossier); db.flush()
    append_ledger_entry(db, record_type="signature_dossier", record_id=dossier.id, action="finalized", actor=actor, payload={"dossier_hash":dossier.dossier_hash,"signature_algorithm":dossier.signature_algorithm,"signing_key_id":dossier.signing_key_id,"signed_by":dossier.signed_by,"signed_at":dossier.signed_at,"record_count":len(records),"approval_count":len(approvals)})
    emit_webhook_event(db, event_type="dossier.finalized", resource_type="signature_dossier", resource_id=dossier.id, payload={"id":dossier.id,"dossier_hash":dossier.dossier_hash,"signing_key_id":dossier.signing_key_id,"visibility":dossier.visibility,"record_count":len(records)})
    if dossier.supersedes_dossier_id:
        previous = get_dossier_or_404(db, dossier.supersedes_dossier_id)
        if previous.status == "finalized": previous.status = "superseded"; db.add(previous)
    db.commit(); db.refresh(dossier)
    return dossier_read(db, dossier)


def verify_dossier(db: Session, dossier_id: str, settings) -> DossierVerificationResult:
    dossier = get_dossier_or_404(db, dossier_id)
    errors: list[str] = []
    finalized = dossier.status in {"finalized","superseded"} and bool(dossier.snapshot_json)
    if not finalized: errors.append("Dossier is not finalized.")
    observed_hash = sha256_payload(dossier.snapshot_json) if dossier.snapshot_json else None
    hash_matches = bool(dossier.dossier_hash and observed_hash == dossier.dossier_hash)
    if finalized and not hash_matches: errors.append("Canonical dossier snapshot hash does not match.")
    signature_matches = bool(dossier.platform_signature and dossier.dossier_hash and settings.dossier_signing_secret and hmac.compare_digest(dossier.platform_signature, _signature(settings.dossier_signing_secret, dossier.dossier_hash)))
    if finalized and not signature_matches: errors.append("Platform signature does not match.")
    records = list(db.scalars(select(DossierRecord).where(DossierRecord.dossier_id == dossier.id)).all())
    record_snapshots_match = all(item.snapshot_hash == sha256_payload(item.snapshot_json) for item in records)
    if not record_snapshots_match: errors.append("One or more dossier record snapshot hashes do not match.")
    if finalized:
        frozen_records = {item["id"]: item for item in dossier.snapshot_json.get("records", [])}
        for item in records:
            frozen = frozen_records.get(item.id)
            if not frozen or frozen.get("snapshot_hash") != item.snapshot_hash or frozen.get("snapshot") != item.snapshot_json:
                record_snapshots_match = False; errors.append(f"Frozen record mismatch: {item.id}")
    return DossierVerificationResult(dossier_id=dossier.id, valid=finalized and hash_matches and signature_matches and record_snapshots_match, finalized=finalized, hash_matches=hash_matches, signature_matches=signature_matches, record_snapshots_match=record_snapshots_match, expected_hash=dossier.dossier_hash, observed_hash=observed_hash, signing_key_id=dossier.signing_key_id, errors=errors)


def workflow_platform_stats(db: Session) -> dict:
    def count(model, *filters): return int(db.scalar(select(func.count()).select_from(model).where(*filters)) or 0)
    return {
        "workflow_definitions": count(WorkflowDefinition),
        "workflow_runs": count(WorkflowRun),
        "active_workflows": count(WorkflowRun, WorkflowRun.status.in_(["draft","in_progress","blocked"])),
        "completed_workflows": count(WorkflowRun, WorkflowRun.status == "completed"),
        "workflow_steps": count(WorkflowStep),
        "workflow_transitions": count(WorkflowTransition),
        "dossiers": count(SignatureDossier),
        "finalized_dossiers": count(SignatureDossier, SignatureDossier.status.in_(["finalized","superseded"])),
        "approvals": count(DossierApproval),
    }
