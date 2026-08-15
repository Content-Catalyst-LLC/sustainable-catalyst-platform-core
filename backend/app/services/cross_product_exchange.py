from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session

from ..models import (
    ClaimRecord,
    CountryEvidenceReconciliation,
    CrossProductExchangeItem,
    CrossProductExchangePackage,
    CrossProductExchangeReceipt,
    EconomicDataRecord,
    Entity,
    EvidenceRecord,
    FacilityObservation,
    GeospatialFeature,
    HumanitarianCondition,
    InternationalLawRecord,
    LiveDataObservation,
    MapLayer,
    OperationalFacility,
    ScientificDataAsset,
    ScientificDataRecord,
    ScientificDomainBinding,
    SourceSnapshot,
    TimeSeriesDefinition,
)
from .reliability import emit_event

PRODUCTS = (
    "site-intelligence",
    "workspace",
    "lab",
    "knowledge-library",
    "decision-studio",
    "research-librarian",
    "workbench",
    "advisory",
    "catalyst-data",
    "finance",
    "narrative-risk",
)

SUBJECT_MODELS = {
    "entity": Entity,
    "claim": ClaimRecord,
    "evidence-record": EvidenceRecord,
    "source-snapshot": SourceSnapshot,
    "live-observation": LiveDataObservation,
    "scientific-record": ScientificDataRecord,
    "economic-record": EconomicDataRecord,
    "international-law-record": InternationalLawRecord,
    "geospatial-feature": GeospatialFeature,
    "time-series": TimeSeriesDefinition,
    "scientific-asset": ScientificDataAsset,
    "map-layer": MapLayer,
    "facility": OperationalFacility,
    "facility-observation": FacilityObservation,
    "humanitarian-condition": HumanitarianCondition,
    "country-reconciliation": CountryEvidenceReconciliation,
    "scientific-domain-binding": ScientificDomainBinding,
}

CANONICAL_URI_PREFIX = {
    "entity": "/v1/entities/",
    "claim": "/v1/evidence/claims/",
    "evidence-record": "/v1/evidence/records/",
    "source-snapshot": "/v1/evidence/snapshots/",
    "live-observation": "/v1/live/observations/",
    "scientific-record": "/v1/science/records/",
    "economic-record": "/v1/economics/records/",
    "international-law-record": "/v1/international-law/records/",
    "geospatial-feature": "/v1/data-fabric/features/",
    "time-series": "/v1/data-fabric/timeseries/",
    "scientific-asset": "/v1/data-fabric/assets/",
    "map-layer": "/v1/data-fabric/map-layers/",
    "facility": "/v1/facilities/",
    "facility-observation": "/v1/facilities/observations/",
    "humanitarian-condition": "/v1/humanitarian/conditions/",
    "country-reconciliation": "/v1/country-evidence/reconciliations/",
    "scientific-domain-binding": "/v1/scientific-fabric/bindings/",
}

ARTIFACT_TYPES = (
    "evidence",
    "dataset",
    "observation",
    "facility",
    "scientific-object",
    "map-layer",
    "time-series",
    "country-evidence",
    "document-reference",
    "derived-artifact",
)

RECEIPT_STATES = ("acknowledged", "accepted", "rejected", "derived")
SENSITIVE_PARTS = ("password", "secret", "token", "authorization", "api_key", "apikey", "credential")
MAX_ITEM_SNAPSHOT_BYTES = 128 * 1024
MAX_PACKAGE_SNAPSHOT_BYTES = 512 * 1024


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _assert_no_sensitive_keys(value: Any, path: str = "payload") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in SENSITIVE_PARTS):
                raise ValueError(f"Sensitive field is not exchangeable: {path}.{key}")
            _assert_no_sensitive_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_sensitive_keys(item, f"{path}[{index}]")


def _serialize_model(row: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    mapper = sa_inspect(row).mapper
    for attr in mapper.column_attrs:
        value = getattr(row, attr.key)
        if isinstance(value, datetime):
            value = value.isoformat()
        result[attr.key] = value
    _assert_no_sensitive_keys(result, "snapshot")
    return result


def _row_is_public(row: Any) -> bool:
    if hasattr(row, "public"):
        return bool(getattr(row, "public"))
    if hasattr(row, "visibility"):
        return str(getattr(row, "visibility")) == "public"
    return True


def resolve_subject(db: Session, subject_type: str, subject_id: str) -> Any:
    model = SUBJECT_MODELS.get(subject_type)
    if model is None:
        raise ValueError("Unsupported canonical subject type.")
    row = db.get(model, subject_id)
    if row is None:
        raise ValueError("Canonical subject does not exist.")
    return row


def readiness() -> dict[str, Any]:
    return {
        "products": list(PRODUCTS),
        "subject_types": sorted(SUBJECT_MODELS),
        "artifact_types": list(ARTIFACT_TYPES),
        "receipt_states": list(RECEIPT_STATES),
        "reference_first": True,
        "non_destructive": True,
        "automatic_truth_promotion": False,
        "automatic_ownership_transfer": False,
        "automatic_cross_product_delivery": False,
        "delivery_mode": "pull",
        "private_package_public_api_exposure": False,
        "secret_bearing_snapshots_allowed": False,
    }


def create_package(
    db: Session,
    *,
    origin_product: str,
    target_product: str,
    title: str,
    purpose: str | None,
    visibility: str,
    idempotency_key: str | None,
    items: list[dict[str, Any]],
    provenance: dict[str, Any] | None = None,
) -> CrossProductExchangePackage:
    origin_product = origin_product.strip().lower()
    target_product = target_product.strip().lower()
    if origin_product not in PRODUCTS or target_product not in PRODUCTS:
        raise ValueError("Unknown Sustainable Catalyst product.")
    if origin_product == target_product:
        raise ValueError("Origin and target products must differ.")
    if visibility not in {"public", "internal", "private"}:
        raise ValueError("Unsupported exchange visibility.")
    if not items:
        raise ValueError("An exchange package requires at least one item.")
    if len(items) > 100:
        raise ValueError("An exchange package is limited to 100 items.")
    _assert_no_sensitive_keys(provenance or {}, "provenance")

    normalized_items: list[dict[str, Any]] = []
    total_snapshot_bytes = 0
    for ordinal, item in enumerate(items):
        artifact_type = str(item.get("artifact_type", "evidence")).strip().lower()
        if artifact_type not in ARTIFACT_TYPES:
            raise ValueError("Unsupported exchange artifact type.")
        subject_type = str(item.get("subject_type", "")).strip().lower()
        subject_id = str(item.get("subject_id", "")).strip()
        if not subject_id:
            raise ValueError("subject_id is required.")
        row = resolve_subject(db, subject_type, subject_id)
        if visibility == "public" and not _row_is_public(row):
            raise ValueError("A non-public canonical subject cannot be placed in a public exchange package.")
        snapshot_mode = str(item.get("snapshot_mode", "reference")).strip().lower()
        if snapshot_mode not in {"reference", "reference+snapshot"}:
            raise ValueError("snapshot_mode must be reference or reference+snapshot.")
        snapshot = _serialize_model(row) if snapshot_mode == "reference+snapshot" else {}
        snapshot_bytes = len(json.dumps(snapshot, default=str).encode("utf-8"))
        if snapshot_bytes > MAX_ITEM_SNAPSHOT_BYTES:
            raise ValueError("Item snapshot exceeds the governed snapshot size limit.")
        total_snapshot_bytes += snapshot_bytes
        item_provenance = dict(item.get("provenance") or {})
        _assert_no_sensitive_keys(item_provenance, "item.provenance")
        canonical_uri = f"{CANONICAL_URI_PREFIX[subject_type]}{subject_id}"
        normalized_items.append(
            {
                "ordinal": ordinal,
                "artifact_type": artifact_type,
                "subject_type": subject_type,
                "subject_id": subject_id,
                "canonical_uri": canonical_uri,
                "snapshot_mode": snapshot_mode,
                "snapshot": snapshot,
                "provenance": item_provenance,
                "evidence_role": str(item.get("evidence_role", "inherited")),
                "truth_precedence": "inherit-from-subject",
                "transformation_state": "unaltered-reference",
            }
        )
    if total_snapshot_bytes > MAX_PACKAGE_SNAPSHOT_BYTES:
        raise ValueError("Package snapshots exceed the governed package size limit.")

    fingerprint_payload = {
        "origin_product": origin_product,
        "target_product": target_product,
        "title": title,
        "purpose": purpose,
        "visibility": visibility,
        "items": normalized_items,
    }
    package_hash = _stable_hash(fingerprint_payload)
    key = (idempotency_key or package_hash)[:128]
    existing = db.scalar(
        select(CrossProductExchangePackage).where(
            CrossProductExchangePackage.origin_product == origin_product,
            CrossProductExchangePackage.target_product == target_product,
            CrossProductExchangePackage.idempotency_key == key,
        )
    )
    if existing is not None:
        return existing

    package = CrossProductExchangePackage(
        origin_product=origin_product,
        target_product=target_product,
        idempotency_key=key,
        title=title.strip()[:400],
        purpose=purpose,
        visibility=visibility,
        state="ready",
        delivery_mode="pull",
        governance_json={
            "reference_first": True,
            "non_destructive": True,
            "automatic_truth_promotion": False,
            "automatic_ownership_transfer": False,
            "source_artifacts_retained": True,
        },
        provenance_json=dict(provenance or {}),
        package_hash=package_hash,
    )
    db.add(package)
    db.flush()
    for item in normalized_items:
        row = CrossProductExchangeItem(
            package_id=package.id,
            ordinal=item["ordinal"],
            artifact_type=item["artifact_type"],
            subject_type=item["subject_type"],
            subject_id=item["subject_id"],
            canonical_uri=item["canonical_uri"],
            snapshot_mode=item["snapshot_mode"],
            snapshot_json=item["snapshot"],
            provenance_json=item["provenance"],
            evidence_role=item["evidence_role"],
            truth_precedence=item["truth_precedence"],
            transformation_state=item["transformation_state"],
            item_hash=_stable_hash(item),
        )
        db.add(row)
    db.commit()
    db.refresh(package)
    emit_event(
        db,
        "exchange.package.created",
        "cross_product_exchange_package",
        package.id,
        {"origin_product": origin_product, "target_product": target_product, "item_count": len(normalized_items)},
        public=False,
    )
    return package


def package_detail(db: Session, package_id: str) -> dict[str, Any]:
    package = db.get(CrossProductExchangePackage, package_id)
    if package is None:
        raise ValueError("Exchange package not found.")
    items = db.scalars(
        select(CrossProductExchangeItem)
        .where(CrossProductExchangeItem.package_id == package_id)
        .order_by(CrossProductExchangeItem.ordinal)
    ).all()
    receipts = db.scalars(
        select(CrossProductExchangeReceipt)
        .where(CrossProductExchangeReceipt.package_id == package_id)
        .order_by(CrossProductExchangeReceipt.created_at)
    ).all()
    return {
        "id": package.id,
        "origin_product": package.origin_product,
        "target_product": package.target_product,
        "title": package.title,
        "purpose": package.purpose,
        "visibility": package.visibility,
        "state": package.state,
        "delivery_mode": package.delivery_mode,
        "governance": package.governance_json,
        "provenance": package.provenance_json,
        "package_hash": package.package_hash,
        "created_at": package.created_at,
        "updated_at": package.updated_at,
        "items": [
            {
                "id": item.id,
                "ordinal": item.ordinal,
                "artifact_type": item.artifact_type,
                "subject_type": item.subject_type,
                "subject_id": item.subject_id,
                "canonical_uri": item.canonical_uri,
                "snapshot_mode": item.snapshot_mode,
                "snapshot": item.snapshot_json,
                "provenance": item.provenance_json,
                "evidence_role": item.evidence_role,
                "truth_precedence": item.truth_precedence,
                "transformation_state": item.transformation_state,
                "item_hash": item.item_hash,
            }
            for item in items
        ],
        "receipts": [
            {
                "id": receipt.id,
                "target_product": receipt.target_product,
                "state": receipt.state,
                "derived_object_id": receipt.derived_object_id,
                "note": receipt.note,
                "metadata": receipt.metadata_json,
                "created_at": receipt.created_at,
            }
            for receipt in receipts
        ],
    }


def list_packages(
    db: Session,
    *,
    origin_product: str | None = None,
    target_product: str | None = None,
    state: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    stmt = select(CrossProductExchangePackage)
    if origin_product:
        stmt = stmt.where(CrossProductExchangePackage.origin_product == origin_product)
    if target_product:
        stmt = stmt.where(CrossProductExchangePackage.target_product == target_product)
    if state:
        stmt = stmt.where(CrossProductExchangePackage.state == state)
    rows = db.scalars(stmt.order_by(desc(CrossProductExchangePackage.created_at)).limit(max(1, min(limit, 500)))).all()
    return [
        {
            "id": row.id,
            "origin_product": row.origin_product,
            "target_product": row.target_product,
            "title": row.title,
            "visibility": row.visibility,
            "state": row.state,
            "delivery_mode": row.delivery_mode,
            "package_hash": row.package_hash,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def create_receipt(
    db: Session,
    package_id: str,
    *,
    target_product: str,
    state: str,
    derived_object_id: str | None = None,
    note: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> CrossProductExchangeReceipt:
    package = db.get(CrossProductExchangePackage, package_id)
    if package is None:
        raise ValueError("Exchange package not found.")
    if target_product != package.target_product:
        raise ValueError("Receipt target must match the package target product.")
    if state not in RECEIPT_STATES:
        raise ValueError("Unsupported receipt state.")
    _assert_no_sensitive_keys(metadata or {}, "receipt.metadata")
    receipt = CrossProductExchangeReceipt(
        package_id=package_id,
        target_product=target_product,
        state=state,
        derived_object_id=derived_object_id,
        note=note,
        metadata_json=dict(metadata or {}),
    )
    db.add(receipt)
    if state == "accepted":
        package.state = "accepted"
    elif state == "rejected":
        package.state = "rejected"
    elif state == "derived":
        package.state = "derived"
    package.updated_at = _now()
    db.add(package)
    db.commit()
    db.refresh(receipt)
    emit_event(
        db,
        "exchange.package.receipt",
        "cross_product_exchange_package",
        package.id,
        {"target_product": target_product, "state": state},
        public=False,
    )
    return receipt
