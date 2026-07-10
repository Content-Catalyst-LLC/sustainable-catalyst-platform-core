from __future__ import annotations

from datetime import datetime, timezone
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..hashing import sha256_payload, sha256_text
from ..models import (
    CalculationTrace,
    ClaimRecord,
    Entity,
    EvidenceRecord,
    EvidenceReview,
    EvidenceReviewAssignment,
    LedgerEntry,
    ProvenanceActivity,
    ProvenanceLink,
    Relationship,
    SourceSnapshot,
)
from ..schemas import (
    CalculationTraceCreate,
    CalculationTraceRead,
    ClaimCreate,
    ClaimRead,
    ClaimUpdate,
    EvidenceAssignmentCreate,
    EvidenceAssignmentRead,
    EvidenceManifest,
    EvidenceRecordCreate,
    EvidenceRecordRead,
    EvidenceReviewCreate,
    EvidenceReviewRead,
    LedgerEntryRead,
    ProvenanceActivityCreate,
    ProvenanceActivityRead,
    ProvenanceLinkCreate,
    ProvenanceLinkRead,
    SourceSnapshotCreate,
    SourceSnapshotRead,
)
from .developers import emit_webhook_event
from .entities import get_entity_or_404
from .ledger import append_ledger_entry


EVIDENCE_REVIEW_STATUS_MAP = {
    "approve": "verified",
    "reject": "rejected",
    "needs_changes": "needs_changes",
    "restore_unreviewed": "unreviewed",
}


def _not_found(label: str, record_id: str):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{label} not found: {record_id}",
    )


def get_claim_or_404(db: Session, claim_id: str) -> ClaimRecord:
    record = db.get(ClaimRecord, claim_id)
    return record if record else _not_found("Claim", claim_id)


def get_snapshot_or_404(db: Session, snapshot_id: str) -> SourceSnapshot:
    record = db.get(SourceSnapshot, snapshot_id)
    return record if record else _not_found("Source snapshot", snapshot_id)


def get_activity_or_404(db: Session, activity_id: str) -> ProvenanceActivity:
    record = db.get(ProvenanceActivity, activity_id)
    return record if record else _not_found("Provenance activity", activity_id)


def get_trace_or_404(db: Session, trace_id: str) -> CalculationTrace:
    record = db.get(CalculationTrace, trace_id)
    return record if record else _not_found("Calculation trace", trace_id)


def get_evidence_or_404(db: Session, evidence_id: str) -> EvidenceRecord:
    record = db.get(EvidenceRecord, evidence_id)
    return record if record else _not_found("Evidence record", evidence_id)


def create_claim(db: Session, payload: ClaimCreate) -> ClaimRecord:
    if payload.subject_entity_id:
        get_entity_or_404(db, payload.subject_entity_id)
    claim = ClaimRecord(
        id=payload.id or f"sc:claim:{uuid.uuid4()}",
        claim_text=payload.claim_text,
        claim_type=payload.claim_type,
        subject_entity_id=payload.subject_entity_id,
        status=payload.status,
        visibility=payload.visibility,
        language=payload.language,
        metadata_json=payload.metadata,
    )
    db.add(claim)
    db.flush()
    append_ledger_entry(
        db,
        record_type="claim",
        record_id=claim.id,
        action="created",
        actor=payload.actor,
        payload={
            "claim_text": claim.claim_text,
            "claim_type": claim.claim_type,
            "subject_entity_id": claim.subject_entity_id,
            "status": claim.status,
            "visibility": claim.visibility,
            "language": claim.language,
            "metadata": claim.metadata_json,
        },
    )
    emit_webhook_event(
        db,
        event_type="claim.created",
        resource_type="claim",
        resource_id=claim.id,
        payload={
            "id": claim.id,
            "claim_type": claim.claim_type,
            "subject_entity_id": claim.subject_entity_id,
            "status": claim.status,
            "visibility": claim.visibility,
        },
    )
    db.commit()
    db.refresh(claim)
    return claim


def update_claim(
    db: Session,
    claim_id: str,
    payload: ClaimUpdate,
) -> ClaimRecord:
    claim = get_claim_or_404(db, claim_id)
    changes = payload.model_dump(exclude={"actor"}, exclude_unset=True)
    if "metadata" in changes:
        changes["metadata_json"] = changes.pop("metadata")
    for key, value in changes.items():
        setattr(claim, key, value)
    db.add(claim)
    db.flush()
    append_ledger_entry(
        db,
        record_type="claim",
        record_id=claim.id,
        action="updated",
        actor=payload.actor,
        payload={
            "changes": changes,
            "current_status": claim.status,
            "updated_at": claim.updated_at,
        },
    )
    emit_webhook_event(
        db,
        event_type="claim.updated",
        resource_type="claim",
        resource_id=claim.id,
        payload={
            "id": claim.id,
            "changes": list(changes.keys()),
            "status": claim.status,
            "visibility": claim.visibility,
        },
    )
    db.commit()
    db.refresh(claim)
    return claim


def list_claims(
    db: Session,
    *,
    subject_entity_id: str | None,
    status_value: str | None,
    visibility: str | None,
    limit: int,
    offset: int,
) -> tuple[list[ClaimRecord], int]:
    filters = []
    if subject_entity_id:
        filters.append(ClaimRecord.subject_entity_id == subject_entity_id)
    if status_value:
        filters.append(ClaimRecord.status == status_value)
    if visibility:
        filters.append(ClaimRecord.visibility == visibility)
    stmt = select(ClaimRecord).where(*filters)
    total = int(
        db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    )
    records = db.scalars(
        stmt.order_by(ClaimRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(records), total


def create_snapshot(
    db: Session,
    payload: SourceSnapshotCreate,
    *,
    excerpt_max: int,
) -> SourceSnapshot:
    if payload.source_entity_id:
        get_entity_or_404(db, payload.source_entity_id)

    content_hash = (
        sha256_text(payload.content)
        if payload.content is not None
        else payload.content_hash
    )
    if content_hash is None:
        raise HTTPException(status_code=422, detail="Content hash is required.")

    snapshot = SourceSnapshot(
        id=payload.id or f"sc:snapshot:{uuid.uuid4()}",
        source_entity_id=payload.source_entity_id,
        canonical_url=str(payload.canonical_url) if payload.canonical_url else None,
        title=payload.title,
        publisher=payload.publisher,
        published_at=payload.published_at,
        retrieved_at=payload.retrieved_at or datetime.now(timezone.utc),
        media_type=payload.media_type,
        content_hash=content_hash,
        content_length=len(payload.content) if payload.content is not None else None,
        content_excerpt=(
            payload.content[:excerpt_max]
            if payload.content is not None and excerpt_max > 0
            else None
        ),
        storage_uri=payload.storage_uri,
        archived_url=str(payload.archived_url) if payload.archived_url else None,
        metadata_json=payload.metadata,
    )
    db.add(snapshot)
    db.flush()
    append_ledger_entry(
        db,
        record_type="source_snapshot",
        record_id=snapshot.id,
        action="captured",
        actor=payload.actor,
        payload={
            "source_entity_id": snapshot.source_entity_id,
            "canonical_url": snapshot.canonical_url,
            "title": snapshot.title,
            "publisher": snapshot.publisher,
            "published_at": snapshot.published_at,
            "retrieved_at": snapshot.retrieved_at,
            "media_type": snapshot.media_type,
            "content_hash": snapshot.content_hash,
            "content_length": snapshot.content_length,
            "storage_uri": snapshot.storage_uri,
            "archived_url": snapshot.archived_url,
            "metadata": snapshot.metadata_json,
        },
    )
    emit_webhook_event(
        db,
        event_type="source_snapshot.created",
        resource_type="source_snapshot",
        resource_id=snapshot.id,
        payload={
            "id": snapshot.id,
            "source_entity_id": snapshot.source_entity_id,
            "canonical_url": snapshot.canonical_url,
            "content_hash": snapshot.content_hash,
            "retrieved_at": snapshot.retrieved_at.isoformat(),
        },
    )
    db.commit()
    db.refresh(snapshot)
    return snapshot


def verify_snapshot_content(snapshot: SourceSnapshot, content: str) -> dict:
    observed_hash = sha256_text(content)
    return {
        "snapshot_id": snapshot.id,
        "expected_hash": snapshot.content_hash,
        "observed_hash": observed_hash,
        "matches": observed_hash == snapshot.content_hash,
        "observed_length": len(content),
    }


def create_activity(
    db: Session,
    payload: ProvenanceActivityCreate,
) -> ProvenanceActivity:
    if payload.software_entity_id:
        get_entity_or_404(db, payload.software_entity_id)
    activity = ProvenanceActivity(
        id=payload.id or f"sc:activity:{uuid.uuid4()}",
        activity_type=payload.activity_type,
        name=payload.name,
        description=payload.description,
        agent=payload.agent,
        software_entity_id=payload.software_entity_id,
        started_at=payload.started_at or datetime.now(timezone.utc),
        ended_at=payload.ended_at,
        parameters=payload.parameters,
        environment=payload.environment,
        status=payload.status,
        metadata_json=payload.metadata,
    )
    db.add(activity)
    db.flush()
    append_ledger_entry(
        db,
        record_type="provenance_activity",
        record_id=activity.id,
        action="recorded",
        actor=payload.agent,
        payload={
            "activity_type": activity.activity_type,
            "name": activity.name,
            "description": activity.description,
            "software_entity_id": activity.software_entity_id,
            "started_at": activity.started_at,
            "ended_at": activity.ended_at,
            "parameters": activity.parameters,
            "environment": activity.environment,
            "status": activity.status,
            "metadata": activity.metadata_json,
        },
    )
    emit_webhook_event(
        db,
        event_type="provenance_activity.created",
        resource_type="provenance_activity",
        resource_id=activity.id,
        payload={
            "id": activity.id,
            "activity_type": activity.activity_type,
            "name": activity.name,
            "agent": activity.agent,
            "status": activity.status,
        },
    )
    db.commit()
    db.refresh(activity)
    return activity


def _validate_provenance_object(
    db: Session,
    object_type: str,
    object_id: str,
) -> None:
    model_map = {
        "claim": ClaimRecord,
        "evidence": EvidenceRecord,
        "source_snapshot": SourceSnapshot,
        "calculation_trace": CalculationTrace,
        "entity": Entity,
        "relationship": Relationship,
        "provenance_activity": ProvenanceActivity,
    }
    model = model_map.get(object_type)
    if model is None:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported provenance object_type: {object_type}",
        )
    if db.get(model, object_id) is None:
        _not_found(object_type.replace("_", " ").title(), object_id)


def create_provenance_link(
    db: Session,
    activity_id: str,
    payload: ProvenanceLinkCreate,
) -> ProvenanceLink:
    get_activity_or_404(db, activity_id)
    _validate_provenance_object(db, payload.object_type, payload.object_id)
    link = ProvenanceLink(
        activity_id=activity_id,
        role=payload.role,
        object_type=payload.object_type,
        object_id=payload.object_id,
        metadata_json=payload.metadata,
    )
    db.add(link)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This provenance link already exists.",
        ) from exc
    append_ledger_entry(
        db,
        record_type="provenance_link",
        record_id=link.id,
        action="linked",
        actor=payload.actor,
        payload={
            "activity_id": activity_id,
            "role": link.role,
            "object_type": link.object_type,
            "object_id": link.object_id,
            "metadata": link.metadata_json,
        },
    )
    emit_webhook_event(
        db,
        event_type="provenance_link.created",
        resource_type="provenance_link",
        resource_id=link.id,
        payload={
            "id": link.id,
            "activity_id": activity_id,
            "role": link.role,
            "object_type": link.object_type,
            "object_id": link.object_id,
        },
    )
    db.commit()
    db.refresh(link)
    return link


def create_calculation_trace(
    db: Session,
    payload: CalculationTraceCreate,
) -> CalculationTrace:
    get_entity_or_404(db, payload.tool_entity_id)
    if payload.subject_entity_id:
        get_entity_or_404(db, payload.subject_entity_id)
    if payload.activity_id:
        get_activity_or_404(db, payload.activity_id)

    trace_payload = {
        "tool_entity_id": payload.tool_entity_id,
        "subject_entity_id": payload.subject_entity_id,
        "activity_id": payload.activity_id,
        "run_id": payload.run_id,
        "inputs": payload.inputs,
        "outputs": payload.outputs,
        "formula_version": payload.formula_version,
        "code_version": payload.code_version,
        "runtime": payload.runtime,
        "status": payload.status,
        "metadata": payload.metadata,
    }
    trace = CalculationTrace(
        id=payload.id or f"sc:trace:{uuid.uuid4()}",
        tool_entity_id=payload.tool_entity_id,
        subject_entity_id=payload.subject_entity_id,
        activity_id=payload.activity_id,
        run_id=payload.run_id,
        inputs=payload.inputs,
        outputs=payload.outputs,
        formula_version=payload.formula_version,
        code_version=payload.code_version,
        runtime=payload.runtime,
        status=payload.status,
        content_hash=sha256_payload(trace_payload),
        metadata_json=payload.metadata,
    )
    db.add(trace)
    db.flush()
    append_ledger_entry(
        db,
        record_type="calculation_trace",
        record_id=trace.id,
        action="recorded",
        actor=payload.actor,
        payload={**trace_payload, "content_hash": trace.content_hash},
    )
    emit_webhook_event(
        db,
        event_type="calculation_trace.created",
        resource_type="calculation_trace",
        resource_id=trace.id,
        payload={
            "id": trace.id,
            "tool_entity_id": trace.tool_entity_id,
            "subject_entity_id": trace.subject_entity_id,
            "activity_id": trace.activity_id,
            "status": trace.status,
            "content_hash": trace.content_hash,
        },
    )
    db.commit()
    db.refresh(trace)
    return trace


def create_evidence(
    db: Session,
    payload: EvidenceRecordCreate,
) -> EvidenceRecord:
    if payload.claim_id:
        get_claim_or_404(db, payload.claim_id)
    if payload.subject_entity_id:
        get_entity_or_404(db, payload.subject_entity_id)
    if payload.source_entity_id:
        get_entity_or_404(db, payload.source_entity_id)
    if payload.source_snapshot_id:
        get_snapshot_or_404(db, payload.source_snapshot_id)
    if payload.relationship_id and db.get(Relationship, payload.relationship_id) is None:
        _not_found("Relationship", payload.relationship_id)
    if payload.calculation_trace_id:
        get_trace_or_404(db, payload.calculation_trace_id)

    evidence = EvidenceRecord(
        id=payload.id or f"sc:evidence:{uuid.uuid4()}",
        evidence_type=payload.evidence_type,
        stance=payload.stance,
        claim_id=payload.claim_id,
        subject_entity_id=payload.subject_entity_id,
        source_entity_id=payload.source_entity_id,
        source_snapshot_id=payload.source_snapshot_id,
        relationship_id=payload.relationship_id,
        calculation_trace_id=payload.calculation_trace_id,
        statement=payload.statement,
        methodology=payload.methodology,
        confidence=payload.confidence,
        review_status=payload.review_status,
        provenance=payload.provenance,
        metadata_json=payload.metadata,
    )
    db.add(evidence)
    db.flush()
    append_ledger_entry(
        db,
        record_type="evidence",
        record_id=evidence.id,
        action="created",
        actor=payload.actor,
        payload={
            "evidence_type": evidence.evidence_type,
            "stance": evidence.stance,
            "claim_id": evidence.claim_id,
            "subject_entity_id": evidence.subject_entity_id,
            "source_entity_id": evidence.source_entity_id,
            "source_snapshot_id": evidence.source_snapshot_id,
            "relationship_id": evidence.relationship_id,
            "calculation_trace_id": evidence.calculation_trace_id,
            "statement": evidence.statement,
            "methodology": evidence.methodology,
            "confidence": evidence.confidence,
            "review_status": evidence.review_status,
            "provenance": evidence.provenance,
            "metadata": evidence.metadata_json,
        },
    )
    emit_webhook_event(
        db,
        event_type="evidence.created",
        resource_type="evidence",
        resource_id=evidence.id,
        payload={
            "id": evidence.id,
            "evidence_type": evidence.evidence_type,
            "stance": evidence.stance,
            "claim_id": evidence.claim_id,
            "subject_entity_id": evidence.subject_entity_id,
            "review_status": evidence.review_status,
        },
    )
    db.commit()
    db.refresh(evidence)
    return evidence


def list_evidence(
    db: Session,
    *,
    claim_id: str | None,
    subject_entity_id: str | None,
    source_entity_id: str | None,
    stance: str | None,
    review_status: str | None,
    limit: int,
    offset: int,
) -> tuple[list[EvidenceRecord], int]:
    filters = []
    if claim_id:
        filters.append(EvidenceRecord.claim_id == claim_id)
    if subject_entity_id:
        filters.append(EvidenceRecord.subject_entity_id == subject_entity_id)
    if source_entity_id:
        filters.append(EvidenceRecord.source_entity_id == source_entity_id)
    if stance:
        filters.append(EvidenceRecord.stance == stance)
    if review_status:
        filters.append(EvidenceRecord.review_status == review_status)
    stmt = select(EvidenceRecord).where(*filters)
    total = int(
        db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    )
    records = db.scalars(
        stmt.order_by(EvidenceRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(records), total


def review_evidence(
    db: Session,
    evidence_id: str,
    payload: EvidenceReviewCreate,
) -> EvidenceReview:
    evidence = get_evidence_or_404(db, evidence_id)
    resulting_status = EVIDENCE_REVIEW_STATUS_MAP[payload.decision]
    review = EvidenceReview(
        evidence_id=evidence_id,
        decision=payload.decision,
        reviewer=payload.reviewer,
        note=payload.note,
        previous_status=evidence.review_status,
        resulting_status=resulting_status,
        metadata_json=payload.metadata,
    )
    evidence.review_status = resulting_status
    db.add(review)
    db.add(evidence)
    db.flush()
    append_ledger_entry(
        db,
        record_type="evidence_review",
        record_id=review.id,
        action=payload.decision,
        actor=payload.reviewer,
        payload={
            "evidence_id": evidence_id,
            "note": payload.note,
            "previous_status": review.previous_status,
            "resulting_status": review.resulting_status,
            "metadata": review.metadata_json,
        },
    )
    emit_webhook_event(
        db,
        event_type="evidence.reviewed",
        resource_type="evidence",
        resource_id=evidence_id,
        payload={
            "evidence_id": evidence_id,
            "decision": payload.decision,
            "reviewer": payload.reviewer,
            "previous_status": review.previous_status,
            "resulting_status": review.resulting_status,
        },
    )
    db.commit()
    db.refresh(review)
    return review


def assign_evidence_review(
    db: Session,
    evidence_id: str,
    payload: EvidenceAssignmentCreate,
) -> EvidenceReviewAssignment:
    get_evidence_or_404(db, evidence_id)
    assignment = EvidenceReviewAssignment(
        evidence_id=evidence_id,
        assignee=payload.assignee,
        assigned_by=payload.assigned_by,
        instructions=payload.instructions,
        due_at=payload.due_at,
        metadata_json=payload.metadata,
    )
    db.add(assignment)
    db.flush()
    append_ledger_entry(
        db,
        record_type="evidence_review_assignment",
        record_id=assignment.id,
        action="assigned",
        actor=payload.assigned_by,
        payload={
            "evidence_id": evidence_id,
            "assignee": assignment.assignee,
            "instructions": assignment.instructions,
            "due_at": assignment.due_at,
            "status": assignment.status,
            "metadata": assignment.metadata_json,
        },
    )
    emit_webhook_event(
        db,
        event_type="evidence_review.assigned",
        resource_type="evidence_review_assignment",
        resource_id=assignment.id,
        payload={
            "assignment_id": assignment.id,
            "evidence_id": evidence_id,
            "assignee": assignment.assignee,
            "status": assignment.status,
        },
    )
    db.commit()
    db.refresh(assignment)
    return assignment


def complete_assignment(
    db: Session,
    assignment_id: str,
    completed_by: str,
) -> EvidenceReviewAssignment:
    assignment = db.get(EvidenceReviewAssignment, assignment_id)
    if assignment is None:
        _not_found("Evidence review assignment", assignment_id)
    assignment.status = "completed"
    assignment.completed_at = datetime.now(timezone.utc)
    db.add(assignment)
    db.flush()
    append_ledger_entry(
        db,
        record_type="evidence_review_assignment",
        record_id=assignment.id,
        action="completed",
        actor=completed_by,
        payload={
            "evidence_id": assignment.evidence_id,
            "assignee": assignment.assignee,
            "completed_at": assignment.completed_at,
        },
    )
    emit_webhook_event(
        db,
        event_type="evidence_review.completed",
        resource_type="evidence_review_assignment",
        resource_id=assignment.id,
        payload={
            "assignment_id": assignment.id,
            "evidence_id": assignment.evidence_id,
            "assignee": assignment.assignee,
            "completed_at": assignment.completed_at.isoformat(),
        },
    )
    db.commit()
    db.refresh(assignment)
    return assignment


def build_evidence_manifest(
    db: Session,
    claim_id: str,
) -> EvidenceManifest:
    claim = get_claim_or_404(db, claim_id)
    evidence_records = list(
        db.scalars(
            select(EvidenceRecord)
            .where(EvidenceRecord.claim_id == claim_id)
            .order_by(EvidenceRecord.created_at)
        ).all()
    )
    evidence_ids = [record.id for record in evidence_records]
    snapshot_ids = {
        record.source_snapshot_id
        for record in evidence_records
        if record.source_snapshot_id
    }
    trace_ids = {
        record.calculation_trace_id
        for record in evidence_records
        if record.calculation_trace_id
    }

    snapshots = list(
        db.scalars(
            select(SourceSnapshot)
            .where(SourceSnapshot.id.in_(snapshot_ids))
            .order_by(SourceSnapshot.created_at)
        ).all()
    ) if snapshot_ids else []

    traces = list(
        db.scalars(
            select(CalculationTrace)
            .where(CalculationTrace.id.in_(trace_ids))
            .order_by(CalculationTrace.created_at)
        ).all()
    ) if trace_ids else []

    object_ids = {claim_id, *evidence_ids, *snapshot_ids, *trace_ids}
    links = list(
        db.scalars(
            select(ProvenanceLink)
            .where(ProvenanceLink.object_id.in_(object_ids))
            .order_by(ProvenanceLink.created_at)
        ).all()
    ) if object_ids else []

    activity_ids = {
        link.activity_id for link in links
    } | {
        trace.activity_id for trace in traces if trace.activity_id
    }
    activities = list(
        db.scalars(
            select(ProvenanceActivity)
            .where(ProvenanceActivity.id.in_(activity_ids))
            .order_by(ProvenanceActivity.started_at)
        ).all()
    ) if activity_ids else []

    reviews = list(
        db.scalars(
            select(EvidenceReview)
            .where(EvidenceReview.evidence_id.in_(evidence_ids))
            .order_by(EvidenceReview.created_at)
        ).all()
    ) if evidence_ids else []

    assignments = list(
        db.scalars(
            select(EvidenceReviewAssignment)
            .where(EvidenceReviewAssignment.evidence_id.in_(evidence_ids))
            .order_by(EvidenceReviewAssignment.created_at)
        ).all()
    ) if evidence_ids else []

    relevant_record_ids = (
        {claim_id}
        | set(evidence_ids)
        | snapshot_ids
        | trace_ids
        | {activity.id for activity in activities}
        | {link.id for link in links}
        | {review.id for review in reviews}
        | {assignment.id for assignment in assignments}
    )
    ledger_entries = list(
        db.scalars(
            select(LedgerEntry)
            .where(LedgerEntry.record_id.in_(relevant_record_ids))
            .order_by(LedgerEntry.sequence)
        ).all()
    ) if relevant_record_ids else []

    claim_read = ClaimRead.model_validate(claim)
    evidence_read = [EvidenceRecordRead.model_validate(item) for item in evidence_records]
    snapshot_read = [SourceSnapshotRead.model_validate(item) for item in snapshots]
    trace_read = [CalculationTraceRead.model_validate(item) for item in traces]
    activity_read = [ProvenanceActivityRead.model_validate(item) for item in activities]
    link_read = [ProvenanceLinkRead.model_validate(item) for item in links]
    review_read = [EvidenceReviewRead.model_validate(item) for item in reviews]
    assignment_read = [EvidenceAssignmentRead.model_validate(item) for item in assignments]
    ledger_read = [LedgerEntryRead.model_validate(item) for item in ledger_entries]

    manifest_core = {
        "claim": claim_read.model_dump(mode="json"),
        "evidence": [item.model_dump(mode="json") for item in evidence_read],
        "snapshots": [item.model_dump(mode="json") for item in snapshot_read],
        "calculation_traces": [item.model_dump(mode="json") for item in trace_read],
        "provenance_activities": [item.model_dump(mode="json") for item in activity_read],
        "provenance_links": [item.model_dump(mode="json") for item in link_read],
        "reviews": [item.model_dump(mode="json") for item in review_read],
        "assignments": [item.model_dump(mode="json") for item in assignment_read],
        "ledger_entries": [item.model_dump(mode="json") for item in ledger_read],
    }
    generated_at = datetime.now(timezone.utc)
    return EvidenceManifest(
        claim=claim_read,
        evidence=evidence_read,
        snapshots=snapshot_read,
        calculation_traces=trace_read,
        provenance_activities=activity_read,
        provenance_links=link_read,
        reviews=review_read,
        assignments=assignment_read,
        ledger_entries=ledger_read,
        manifest_hash=sha256_payload(manifest_core),
        generated_at=generated_at,
    )
