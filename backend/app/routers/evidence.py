from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..models import (
    CalculationTrace,
    ClaimRecord,
    EvidenceRecord,
    EvidenceReview,
    EvidenceReviewAssignment,
    LedgerEntry,
    ProvenanceActivity,
    ProvenanceLink,
    SourceSnapshot,
)
from ..schemas import (
    CalculationTraceCreate,
    CalculationTraceRead,
    ClaimCreate,
    ClaimList,
    ClaimRead,
    ClaimUpdate,
    EvidenceAssignmentComplete,
    EvidenceAssignmentCreate,
    EvidenceAssignmentRead,
    EvidenceLedgerStats,
    EvidenceManifest,
    EvidenceRecordCreate,
    EvidenceRecordList,
    EvidenceRecordRead,
    EvidenceReviewCreate,
    EvidenceReviewRead,
    ProvenanceActivityCreate,
    ProvenanceActivityRead,
    ProvenanceLinkCreate,
    ProvenanceLinkRead,
    SnapshotVerificationRequest,
    SnapshotVerificationResult,
    SourceSnapshotCreate,
    SourceSnapshotRead,
)
from ..services.evidence import (
    assign_evidence_review,
    build_evidence_manifest,
    complete_assignment,
    create_activity,
    create_calculation_trace,
    create_claim,
    create_evidence,
    create_provenance_link,
    create_snapshot,
    get_activity_or_404,
    get_claim_or_404,
    get_evidence_or_404,
    get_snapshot_or_404,
    get_trace_or_404,
    list_claims,
    list_evidence,
    review_evidence,
    update_claim,
    verify_snapshot_content,
)

router = APIRouter(prefix="/v1", tags=["Evidence Ledger and Provenance"])


@router.get(
    "/claims",
    response_model=ClaimList,
    dependencies=[Depends(require_read)],
)
def get_claims(
    request: Request,
    subject_entity_id: str | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    visibility: str | None = None,
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    limit = min(limit, request.app.state.settings.page_size_max)
    items, total = list_claims(
        db,
        subject_entity_id=subject_entity_id,
        status_value=status_value,
        visibility=visibility,
        limit=limit,
        offset=offset,
    )
    return ClaimList(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/claims",
    response_model=ClaimRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_claim(payload: ClaimCreate, db: Session = Depends(get_session)):
    return create_claim(db, payload)


@router.get(
    "/claims/{claim_id:path}",
    response_model=ClaimRead,
    dependencies=[Depends(require_read)],
)
def get_claim(claim_id: str, db: Session = Depends(get_session)):
    return get_claim_or_404(db, claim_id)


@router.patch(
    "/claims/{claim_id:path}",
    response_model=ClaimRead,
    dependencies=[Depends(require_write)],
)
def patch_claim(
    claim_id: str,
    payload: ClaimUpdate,
    db: Session = Depends(get_session),
):
    return update_claim(db, claim_id, payload)


@router.get(
    "/source-snapshots",
    response_model=list[SourceSnapshotRead],
    dependencies=[Depends(require_read)],
)
def get_source_snapshots(
    source_entity_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    filters = []
    if source_entity_id:
        filters.append(SourceSnapshot.source_entity_id == source_entity_id)
    return list(
        db.scalars(
            select(SourceSnapshot)
            .where(*filters)
            .order_by(SourceSnapshot.retrieved_at.desc())
            .limit(limit)
        ).all()
    )


@router.post(
    "/source-snapshots",
    response_model=SourceSnapshotRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_source_snapshot(
    request: Request,
    payload: SourceSnapshotCreate,
    db: Session = Depends(get_session),
):
    return create_snapshot(
        db,
        payload,
        excerpt_max=request.app.state.settings.snapshot_excerpt_max,
    )


@router.get(
    "/source-snapshots/{snapshot_id:path}",
    response_model=SourceSnapshotRead,
    dependencies=[Depends(require_read)],
)
def get_source_snapshot(
    snapshot_id: str,
    db: Session = Depends(get_session),
):
    return get_snapshot_or_404(db, snapshot_id)


@router.post(
    "/source-snapshots/{snapshot_id:path}/verify",
    response_model=SnapshotVerificationResult,
    dependencies=[Depends(require_read)],
)
def verify_source_snapshot(
    snapshot_id: str,
    payload: SnapshotVerificationRequest,
    db: Session = Depends(get_session),
):
    snapshot = get_snapshot_or_404(db, snapshot_id)
    return verify_snapshot_content(snapshot, payload.content)


@router.get(
    "/provenance/activities",
    response_model=list[ProvenanceActivityRead],
    dependencies=[Depends(require_read)],
)
def get_provenance_activities(
    activity_type: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    filters = []
    if activity_type:
        filters.append(ProvenanceActivity.activity_type == activity_type)
    return list(
        db.scalars(
            select(ProvenanceActivity)
            .where(*filters)
            .order_by(ProvenanceActivity.started_at.desc())
            .limit(limit)
        ).all()
    )


@router.post(
    "/provenance/activities",
    response_model=ProvenanceActivityRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_provenance_activity(
    payload: ProvenanceActivityCreate,
    db: Session = Depends(get_session),
):
    return create_activity(db, payload)


@router.get(
    "/provenance/activities/{activity_id:path}",
    response_model=ProvenanceActivityRead,
    dependencies=[Depends(require_read)],
)
def get_provenance_activity(
    activity_id: str,
    db: Session = Depends(get_session),
):
    return get_activity_or_404(db, activity_id)


@router.get(
    "/provenance/activities/{activity_id:path}/links",
    response_model=list[ProvenanceLinkRead],
    dependencies=[Depends(require_read)],
)
def get_provenance_links(
    activity_id: str,
    db: Session = Depends(get_session),
):
    get_activity_or_404(db, activity_id)
    return list(
        db.scalars(
            select(ProvenanceLink)
            .where(ProvenanceLink.activity_id == activity_id)
            .order_by(ProvenanceLink.created_at)
        ).all()
    )


@router.post(
    "/provenance/activities/{activity_id:path}/links",
    response_model=ProvenanceLinkRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_provenance_link(
    activity_id: str,
    payload: ProvenanceLinkCreate,
    db: Session = Depends(get_session),
):
    return create_provenance_link(db, activity_id, payload)


@router.get(
    "/calculation-traces",
    response_model=list[CalculationTraceRead],
    dependencies=[Depends(require_read)],
)
def get_calculation_traces(
    tool_entity_id: str | None = None,
    subject_entity_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    filters = []
    if tool_entity_id:
        filters.append(CalculationTrace.tool_entity_id == tool_entity_id)
    if subject_entity_id:
        filters.append(CalculationTrace.subject_entity_id == subject_entity_id)
    return list(
        db.scalars(
            select(CalculationTrace)
            .where(*filters)
            .order_by(CalculationTrace.created_at.desc())
            .limit(limit)
        ).all()
    )


@router.post(
    "/calculation-traces",
    response_model=CalculationTraceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_calculation_trace(
    payload: CalculationTraceCreate,
    db: Session = Depends(get_session),
):
    return create_calculation_trace(db, payload)


@router.get(
    "/calculation-traces/{trace_id:path}",
    response_model=CalculationTraceRead,
    dependencies=[Depends(require_read)],
)
def get_calculation_trace(
    trace_id: str,
    db: Session = Depends(get_session),
):
    return get_trace_or_404(db, trace_id)


@router.get(
    "/evidence-records",
    response_model=EvidenceRecordList,
    dependencies=[Depends(require_read)],
)
def get_evidence_records(
    request: Request,
    claim_id: str | None = None,
    subject_entity_id: str | None = None,
    source_entity_id: str | None = None,
    stance: str | None = None,
    review_status: str | None = None,
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    limit = min(limit, request.app.state.settings.page_size_max)
    items, total = list_evidence(
        db,
        claim_id=claim_id,
        subject_entity_id=subject_entity_id,
        source_entity_id=source_entity_id,
        stance=stance,
        review_status=review_status,
        limit=limit,
        offset=offset,
    )
    return EvidenceRecordList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/evidence-records",
    response_model=EvidenceRecordRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_evidence_record(
    payload: EvidenceRecordCreate,
    db: Session = Depends(get_session),
):
    return create_evidence(db, payload)


@router.get(
    "/evidence-records/{evidence_id:path}",
    response_model=EvidenceRecordRead,
    dependencies=[Depends(require_read)],
)
def get_evidence_record(
    evidence_id: str,
    db: Session = Depends(get_session),
):
    return get_evidence_or_404(db, evidence_id)


@router.post(
    "/evidence-records/{evidence_id:path}/reviews",
    response_model=EvidenceReviewRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_evidence_review(
    evidence_id: str,
    payload: EvidenceReviewCreate,
    db: Session = Depends(get_session),
):
    return review_evidence(db, evidence_id, payload)


@router.get(
    "/evidence-reviews",
    response_model=list[EvidenceReviewRead],
    dependencies=[Depends(require_read)],
)
def get_evidence_reviews(
    evidence_id: str | None = None,
    decision: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    filters = []
    if evidence_id:
        filters.append(EvidenceReview.evidence_id == evidence_id)
    if decision:
        filters.append(EvidenceReview.decision == decision)
    return list(
        db.scalars(
            select(EvidenceReview)
            .where(*filters)
            .order_by(EvidenceReview.created_at.desc())
            .limit(limit)
        ).all()
    )


@router.post(
    "/evidence-records/{evidence_id:path}/assignments",
    response_model=EvidenceAssignmentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_evidence_assignment(
    evidence_id: str,
    payload: EvidenceAssignmentCreate,
    db: Session = Depends(get_session),
):
    return assign_evidence_review(db, evidence_id, payload)


@router.get(
    "/evidence-assignments",
    response_model=list[EvidenceAssignmentRead],
    dependencies=[Depends(require_read)],
)
def get_evidence_assignments(
    evidence_id: str | None = None,
    assignee: str | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    filters = []
    if evidence_id:
        filters.append(EvidenceReviewAssignment.evidence_id == evidence_id)
    if assignee:
        filters.append(EvidenceReviewAssignment.assignee == assignee)
    if status_value:
        filters.append(EvidenceReviewAssignment.status == status_value)
    return list(
        db.scalars(
            select(EvidenceReviewAssignment)
            .where(*filters)
            .order_by(EvidenceReviewAssignment.created_at.desc())
            .limit(limit)
        ).all()
    )


@router.post(
    "/evidence-assignments/{assignment_id}/complete",
    response_model=EvidenceAssignmentRead,
    dependencies=[Depends(require_write)],
)
def post_complete_assignment(
    assignment_id: str,
    payload: EvidenceAssignmentComplete,
    db: Session = Depends(get_session),
):
    return complete_assignment(db, assignment_id, payload.completed_by)


@router.get(
    "/evidence/manifests/{claim_id:path}",
    response_model=EvidenceManifest,
    dependencies=[Depends(require_read)],
)
def get_evidence_manifest(
    claim_id: str,
    db: Session = Depends(get_session),
):
    return build_evidence_manifest(db, claim_id)


@router.get(
    "/evidence/stats",
    response_model=EvidenceLedgerStats,
    dependencies=[Depends(require_read)],
)
def get_evidence_stats(db: Session = Depends(get_session)):
    def count(model) -> int:
        return int(db.scalar(select(func.count()).select_from(model)) or 0)

    status_rows = db.execute(
        select(EvidenceRecord.review_status, func.count(EvidenceRecord.id))
        .group_by(EvidenceRecord.review_status)
        .order_by(EvidenceRecord.review_status)
    ).all()
    stance_rows = db.execute(
        select(EvidenceRecord.stance, func.count(EvidenceRecord.id))
        .group_by(EvidenceRecord.stance)
        .order_by(EvidenceRecord.stance)
    ).all()
    head = db.scalar(
        select(LedgerEntry)
        .order_by(LedgerEntry.sequence.desc())
        .limit(1)
    )
    return EvidenceLedgerStats(
        claims=count(ClaimRecord),
        source_snapshots=count(SourceSnapshot),
        evidence_records=count(EvidenceRecord),
        evidence_reviews=count(EvidenceReview),
        review_assignments=count(EvidenceReviewAssignment),
        provenance_activities=count(ProvenanceActivity),
        provenance_links=count(ProvenanceLink),
        calculation_traces=count(CalculationTrace),
        ledger_entries=count(LedgerEntry),
        ledger_head_hash=head.entry_hash if head else None,
        evidence_by_status={key: int(value) for key, value in status_rows},
        evidence_by_stance={key: int(value) for key, value in stance_rows},
    )
