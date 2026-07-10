from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_session
from ..hashing import sha256_payload
from ..models import (
    EvidenceReview,
    EvidenceReviewAssignment,
    LedgerEntry,
    WebhookDelivery,
    WebhookSubscription,
)
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import (
    PublicEnvelope,
    WebhookSubscriptionCreate,
    WebhookSubscriptionIssued,
    WebhookSubscriptionRead,
    WebhookSubscriptionUpdate,
)
from ..services.developers import (
    create_webhook_subscription,
    get_subscription_or_404,
    update_webhook_subscription,
    usage_summary,
)
from ..services.entities import get_entity_or_404, list_entities
from ..services.evidence import (
    build_evidence_manifest,
    get_claim_or_404,
    get_evidence_or_404,
    list_claims,
    list_evidence,
)
from ..services.jsonld import entity_jsonld
from ..services.ledger import list_ledger_entries, verify_ledger
from ..services.predicates import list_predicates
from ..services.relationships import (
    find_paths,
    neighborhood,
    recommendations,
    traverse_graph,
)

router = APIRouter(prefix="/api/v1", tags=["Unified Public API"])


def envelope(
    request: Request,
    data,
    *,
    meta: dict | None = None,
) -> PublicEnvelope:
    payload_meta = {
        "api_version": "v1",
        "request_id": request.state.request_id,
        "documentation": "/developers",
    }
    if meta:
        payload_meta.update(meta)
    return PublicEnvelope(data=jsonable_encoder(data), meta=payload_meta)


@router.get(
    "/status",
    response_model=PublicEnvelope,
)
def public_status(
    request: Request,
    context: PublicApiContext = Depends(require_public_scope("public:status")),
):
    return envelope(
        request,
        {
            "service": request.app.state.settings.app_name,
            "version": request.app.state.settings.version,
            "status": "operational",
            "application": context.application.name,
            "plan": context.plan.name,
        },
    )


@router.get(
    "/entities",
    response_model=PublicEnvelope,
)
def public_entities(
    request: Request,
    q: str | None = None,
    entity_type: str | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    visibility: str | None = "public",
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    context: PublicApiContext = Depends(require_public_scope("registry:read")),
    db: Session = Depends(get_session),
):
    limit = min(
        limit,
        context.plan.max_page_size,
        request.app.state.settings.page_size_max,
    )
    items, total = list_entities(
        db,
        query=q,
        entity_type=entity_type,
        status_value=status_value,
        visibility=visibility,
        limit=limit,
        offset=offset,
    )
    return envelope(
        request,
        [item for item in items],
        meta={
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        },
    )


@router.get(
    "/entities/{entity_id:path}/jsonld",
    response_model=PublicEnvelope,
)
def public_entity_jsonld(
    request: Request,
    entity_id: str,
    _context: PublicApiContext = Depends(require_public_scope("registry:read")),
    db: Session = Depends(get_session),
):
    return envelope(request, entity_jsonld(db, entity_id))


@router.get(
    "/entities/{entity_id:path}",
    response_model=PublicEnvelope,
)
def public_entity(
    request: Request,
    entity_id: str,
    _context: PublicApiContext = Depends(require_public_scope("registry:read")),
    db: Session = Depends(get_session),
):
    return envelope(request, get_entity_or_404(db, entity_id))


@router.get(
    "/predicates",
    response_model=PublicEnvelope,
)
def public_predicates(
    request: Request,
    status_value: str | None = Query(default="active", alias="status"),
    visibility: str | None = "public",
    _context: PublicApiContext = Depends(require_public_scope("registry:read")),
    db: Session = Depends(get_session),
):
    items, total = list_predicates(
        db,
        status_value=status_value,
        visibility=visibility,
    )
    return envelope(request, items, meta={"total": total})


@router.get(
    "/graph/path",
    response_model=PublicEnvelope,
)
def public_graph_path(
    request: Request,
    source_id: str,
    target_id: str,
    direction: str = Query(default="both", pattern="^(outbound|inbound|both)$"),
    depth: int = Query(default=4, ge=1),
    max_paths: int = Query(default=5, ge=1, le=20),
    predicates: list[str] | None = Query(default=None),
    statuses: list[str] | None = Query(default=["verified", "approved"]),
    min_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
    _context: PublicApiContext = Depends(require_public_scope("graph:read")),
    db: Session = Depends(get_session),
):
    depth = min(depth, request.app.state.settings.max_graph_depth)
    paths = find_paths(
        db,
        source_id=source_id,
        target_id=target_id,
        direction=direction,
        max_depth=depth,
        max_paths=max_paths,
        predicates=predicates,
        statuses=statuses,
        min_confidence=min_confidence,
    )
    data = [
        {
            "node_ids": node_ids,
            "relationships": relationships,
            "length": len(relationships),
            "score": score,
        }
        for node_ids, relationships, score in paths
    ]
    return envelope(
        request,
        data,
        meta={
            "source_id": source_id,
            "target_id": target_id,
            "direction": direction,
            "max_depth": depth,
        },
    )


@router.get(
    "/graph/{entity_id:path}/neighborhood",
    response_model=PublicEnvelope,
)
def public_neighborhood(
    request: Request,
    entity_id: str,
    statuses: list[str] | None = Query(default=["verified", "approved"]),
    min_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
    _context: PublicApiContext = Depends(require_public_scope("graph:read")),
    db: Session = Depends(get_session),
):
    root, groups, total = neighborhood(
        db,
        root_id=entity_id,
        statuses=statuses,
        min_confidence=min_confidence,
    )
    return envelope(
        request,
        {"root": root, "groups": groups},
        meta={"total_relationships": total},
    )


@router.get(
    "/graph/{entity_id:path}/recommendations",
    response_model=PublicEnvelope,
)
def public_recommendations(
    request: Request,
    entity_id: str,
    target_type: str | None = None,
    limit: int = Query(default=10, ge=1, le=50),
    statuses: list[str] | None = Query(default=["verified", "approved"]),
    min_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
    _context: PublicApiContext = Depends(require_public_scope("graph:read")),
    db: Session = Depends(get_session),
):
    items = recommendations(
        db,
        root_id=entity_id,
        target_type=target_type,
        limit=limit,
        statuses=statuses,
        min_confidence=min_confidence,
    )
    return envelope(request, items, meta={"root_id": entity_id})


@router.get(
    "/graph/{entity_id:path}",
    response_model=PublicEnvelope,
)
def public_graph(
    request: Request,
    entity_id: str,
    direction: str = Query(default="both", pattern="^(outbound|inbound|both)$"),
    depth: int = Query(default=1, ge=1),
    predicates: list[str] | None = Query(default=None),
    statuses: list[str] | None = Query(default=["verified", "approved"]),
    min_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
    _context: PublicApiContext = Depends(require_public_scope("graph:read")),
    db: Session = Depends(get_session),
):
    depth = min(depth, request.app.state.settings.max_graph_depth)
    nodes, edges = traverse_graph(
        db,
        root_id=entity_id,
        direction=direction,
        max_depth=depth,
        predicates=predicates,
        statuses=statuses,
        min_confidence=min_confidence,
    )
    return envelope(
        request,
        {
            "root_id": entity_id,
            "direction": direction,
            "max_depth": depth,
            "nodes": [
                {"entity": entity, "depth": node_depth}
                for entity, node_depth in nodes
            ],
            "edges": [
                {"relationship": relationship, "depth": edge_depth}
                for relationship, edge_depth in edges
            ],
        },
    )


@router.get(
    "/claims",
    response_model=PublicEnvelope,
)
def public_claims(
    request: Request,
    subject_entity_id: str | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    context: PublicApiContext = Depends(require_public_scope("evidence:read")),
    db: Session = Depends(get_session),
):
    limit = min(
        limit,
        context.plan.max_page_size,
        request.app.state.settings.page_size_max,
    )
    items, total = list_claims(
        db,
        subject_entity_id=subject_entity_id,
        status_value=status_value,
        visibility="public",
        limit=limit,
        offset=offset,
    )
    return envelope(
        request,
        items,
        meta={
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        },
    )


@router.get(
    "/claims/{claim_id:path}",
    response_model=PublicEnvelope,
)
def public_claim(
    request: Request,
    claim_id: str,
    _context: PublicApiContext = Depends(require_public_scope("evidence:read")),
    db: Session = Depends(get_session),
):
    claim = get_claim_or_404(db, claim_id)
    if claim.visibility != "public":
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Claim not found.")
    return envelope(request, claim)


@router.get(
    "/evidence-records",
    response_model=PublicEnvelope,
)
def public_evidence_records(
    request: Request,
    claim_id: str | None = None,
    subject_entity_id: str | None = None,
    source_entity_id: str | None = None,
    stance: str | None = None,
    review_status: str | None = "verified",
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    context: PublicApiContext = Depends(require_public_scope("evidence:read")),
    db: Session = Depends(get_session),
):
    limit = min(
        limit,
        context.plan.max_page_size,
        request.app.state.settings.page_size_max,
    )
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
    return envelope(
        request,
        items,
        meta={
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        },
    )


@router.get(
    "/evidence-records/{evidence_id:path}",
    response_model=PublicEnvelope,
)
def public_evidence_record(
    request: Request,
    evidence_id: str,
    _context: PublicApiContext = Depends(require_public_scope("evidence:read")),
    db: Session = Depends(get_session),
):
    record = get_evidence_or_404(db, evidence_id)
    if record.review_status != "verified":
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Evidence record not found.")
    return envelope(request, record)


@router.get(
    "/evidence/manifests/{claim_id:path}",
    response_model=PublicEnvelope,
)
def public_evidence_manifest(
    request: Request,
    claim_id: str,
    _context: PublicApiContext = Depends(require_public_scope("evidence:read")),
    db: Session = Depends(get_session),
):
    claim = get_claim_or_404(db, claim_id)
    if claim.visibility != "public":
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Claim not found.")
    manifest = build_evidence_manifest(db, claim_id)
    manifest_data = manifest.model_dump(mode="json")

    verified_evidence = [
        record
        for record in manifest_data["evidence"]
        if record["review_status"] == "verified"
    ]
    verified_evidence_ids = {
        record["id"] for record in verified_evidence
    }
    snapshot_ids = {
        record["source_snapshot_id"]
        for record in verified_evidence
        if record.get("source_snapshot_id")
    }
    trace_ids = {
        record["calculation_trace_id"]
        for record in verified_evidence
        if record.get("calculation_trace_id")
    }
    snapshots = [
        record
        for record in manifest_data["snapshots"]
        if record["id"] in snapshot_ids
    ]
    traces = [
        record
        for record in manifest_data["calculation_traces"]
        if record["id"] in trace_ids
    ]
    allowed_object_ids = {
        claim_id,
        *verified_evidence_ids,
        *snapshot_ids,
        *trace_ids,
    }
    links = [
        record
        for record in manifest_data["provenance_links"]
        if record["object_id"] in allowed_object_ids
    ]
    activity_ids = {
        record["activity_id"] for record in links
    } | {
        record["activity_id"]
        for record in traces
        if record.get("activity_id")
    }
    activities = [
        record
        for record in manifest_data["provenance_activities"]
        if record["id"] in activity_ids
    ]
    reviews = [
        record
        for record in manifest_data["reviews"]
        if record["evidence_id"] in verified_evidence_ids
    ]
    relevant_ids = (
        allowed_object_ids
        | activity_ids
        | {record["id"] for record in links}
        | {record["id"] for record in reviews}
    )
    public_ledger_entries = [
        record
        for record in manifest_data["ledger_entries"]
        if record["record_id"] in relevant_ids
    ]
    public_manifest_core = {
        "claim": manifest_data["claim"],
        "evidence": verified_evidence,
        "snapshots": snapshots,
        "calculation_traces": traces,
        "provenance_activities": activities,
        "provenance_links": links,
        "reviews": reviews,
        "assignments": [],
        "ledger_entries": public_ledger_entries,
    }
    return envelope(
        request,
        {
            **public_manifest_core,
            "manifest_hash": sha256_payload(public_manifest_core),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get(
    "/ledger/verify",
    response_model=PublicEnvelope,
)
def public_ledger_verify(
    request: Request,
    _context: PublicApiContext = Depends(require_public_scope("ledger:read")),
    db: Session = Depends(get_session),
):
    return envelope(request, verify_ledger(db))


@router.get(
    "/ledger/entries",
    response_model=PublicEnvelope,
)
def public_ledger_entries(
    request: Request,
    record_type: str | None = None,
    record_id: str | None = None,
    limit: int = Query(default=100, ge=1),
    offset: int = Query(default=0, ge=0),
    context: PublicApiContext = Depends(require_public_scope("ledger:read")),
    db: Session = Depends(get_session),
):
    limit = min(limit, context.plan.max_page_size, 500)
    public_record_types = {
        "claim",
        "source_snapshot",
        "provenance_activity",
        "provenance_link",
        "calculation_trace",
        "evidence",
        "evidence_review",
        "evidence_review_assignment",
    }
    if record_type and record_type not in public_record_types:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="Public ledger record type not found.",
        )
    filters = [LedgerEntry.record_type.in_(public_record_types)]
    if record_type:
        filters.append(LedgerEntry.record_type == record_type)
    if record_id:
        filters.append(LedgerEntry.record_id == record_id)
    entries = list(
        db.scalars(
            select(LedgerEntry)
            .where(*filters)
            .order_by(LedgerEntry.sequence)
            .limit(limit)
            .offset(offset)
        ).all()
    )
    return envelope(
        request,
        entries,
        meta={"pagination": {"limit": limit, "offset": offset}},
    )


@router.get(
    "/developer/me",
    response_model=PublicEnvelope,
)
def public_developer_identity(
    request: Request,
    context: PublicApiContext = Depends(require_public_scope("developer:read")),
):
    return envelope(
        request,
        {
            "application_id": context.application.id,
            "application_name": context.application.name,
            "credential_id": context.credential.id,
            "credential_label": context.credential.label,
            "plan_id": context.plan.id,
            "plan_name": context.plan.name,
            "scopes": context.credential.scopes,
            "requests_per_minute": context.plan.requests_per_minute,
            "requests_per_day": context.plan.requests_per_day,
            "max_page_size": context.plan.max_page_size,
        },
    )


@router.get(
    "/developer/usage",
    response_model=PublicEnvelope,
)
def public_developer_usage(
    request: Request,
    days: int = Query(default=30, ge=1, le=366),
    context: PublicApiContext = Depends(require_public_scope("developer:read")),
    db: Session = Depends(get_session),
):
    return envelope(
        request,
        usage_summary(
            db,
            application_id=context.application.id,
            credential_id=context.credential.id,
            days=days,
        ),
    )


@router.get(
    "/developer/webhooks",
    response_model=PublicEnvelope,
)
def public_webhook_subscriptions(
    request: Request,
    context: PublicApiContext = Depends(require_public_scope("webhooks:manage")),
    db: Session = Depends(get_session),
):
    records = list(
        db.scalars(
            select(WebhookSubscription)
            .where(
                WebhookSubscription.application_id == context.application.id
            )
            .order_by(WebhookSubscription.created_at.desc())
        ).all()
    )
    return envelope(request, records)


@router.post(
    "/developer/webhooks",
    response_model=PublicEnvelope,
)
def public_create_webhook(
    request: Request,
    payload: WebhookSubscriptionCreate,
    response: Response,
    context: PublicApiContext = Depends(require_public_scope("webhooks:manage")),
    db: Session = Depends(get_session),
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    result = create_webhook_subscription(
        db,
        application_id=context.application.id,
        credential_id=context.credential.id,
        payload=payload,
        master_secret=request.app.state.settings.webhook_signing_secret,
        production=request.app.state.settings.environment == "production",
    )
    return envelope(request, result)


@router.patch(
    "/developer/webhooks/{subscription_id}",
    response_model=PublicEnvelope,
)
def public_update_webhook(
    request: Request,
    subscription_id: str,
    payload: WebhookSubscriptionUpdate,
    context: PublicApiContext = Depends(require_public_scope("webhooks:manage")),
    db: Session = Depends(get_session),
):
    record = update_webhook_subscription(
        db,
        subscription_id,
        context.application.id,
        payload,
        production=request.app.state.settings.environment == "production",
    )
    return envelope(request, record)


@router.get(
    "/developer/webhooks/{subscription_id}/deliveries",
    response_model=PublicEnvelope,
)
def public_webhook_deliveries(
    request: Request,
    subscription_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    context: PublicApiContext = Depends(require_public_scope("webhooks:manage")),
    db: Session = Depends(get_session),
):
    subscription = get_subscription_or_404(db, subscription_id)
    if subscription.application_id != context.application.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Webhook subscription does not belong to this application.")
    deliveries = list(
        db.scalars(
            select(WebhookDelivery)
            .where(WebhookDelivery.subscription_id == subscription_id)
            .order_by(WebhookDelivery.created_at.desc())
            .limit(limit)
        ).all()
    )
    return envelope(request, deliveries)
