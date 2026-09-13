from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Entity,
    VisualReasoningObjectRecord,
    ResearchVisualExplanationRecord,
    CrossProductVisualResearchObjectRecord,
    CrossProductVisualResearchMemberRecord,
    CrossProductVisualResearchRelationRecord,
    CrossProductVisualResearchViewRecord,
    CrossProductVisualResearchSnapshotRecord,
)

OBJECT_KINDS = {"research-composite", "evidence-package", "model-study", "decision-package", "spatial-analysis", "mixed"}
MEMBER_KINDS = {
    "research-object", "visual-object", "visual-explanation", "evidence", "source", "model", "result",
    "scenario", "spatial-temporal", "decision-packet", "data-object", "external-artifact",
}
SOURCE_PRODUCTS = {
    "platform-core", "knowledge-library", "research-librarian", "lab", "workbench",
    "site-intelligence", "decision-studio", "catalyst-data", "external",
}
RELATION_KINDS = {
    "supports", "contradicts", "qualifies", "derived-from", "visualizes", "explains", "depends-on",
    "compares-with", "spatializes", "computes", "informs", "bundles", "references", "relates-to",
}
VIEW_KINDS = {"composite", "evidence", "analysis", "map-timeline", "decision", "model", "narrative", "custom"}
TARGET_PRODUCTS = SOURCE_PRODUCTS - {"platform-core", "knowledge-library", "catalyst-data"}


def _ser(row):
    out = {}
    for col in row.__table__.columns:
        value = getattr(row, col.name)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        out[col.name] = value
    return out


def _obj(db: Session, object_id: str) -> CrossProductVisualResearchObjectRecord:
    row = db.get(CrossProductVisualResearchObjectRecord, object_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Cross-product visual research object not found.")
    return row


def _member(db: Session, object_id: str, member_id: str) -> CrossProductVisualResearchMemberRecord:
    row = db.get(CrossProductVisualResearchMemberRecord, member_id)
    if row is None or row.object_id != object_id:
        raise ValueError("member_id must belong to this cross-product visual research object.")
    return row


def _boundaries() -> dict[str, bool]:
    return {
        "reference_first_cross_product": True,
        "remote_product_fetch_by_core": False,
        "model_execution_by_core": False,
        "analysis_execution_by_core": False,
        "cross_product_truth_merging_by_core": False,
        "layout_execution_by_core": False,
        "renderer_execution_by_core": False,
        "automatic_truth_promotion": False,
    }


def readiness(db: Session) -> dict[str, Any]:
    counts = {
        "objects": int(db.scalar(select(func.count()).select_from(CrossProductVisualResearchObjectRecord)) or 0),
        "members": int(db.scalar(select(func.count()).select_from(CrossProductVisualResearchMemberRecord)) or 0),
        "relations": int(db.scalar(select(func.count()).select_from(CrossProductVisualResearchRelationRecord)) or 0),
        "views": int(db.scalar(select(func.count()).select_from(CrossProductVisualResearchViewRecord)) or 0),
        "snapshots": int(db.scalar(select(func.count()).select_from(CrossProductVisualResearchSnapshotRecord)) or 0),
    }
    return {
        "migration_0044_applied": True,
        "counts": counts,
        "object_kinds": sorted(OBJECT_KINDS),
        "member_kinds": sorted(MEMBER_KINDS),
        "source_products": sorted(SOURCE_PRODUCTS),
        "renderer_neutral": True,
        "portable_semantic_package": True,
        **_boundaries(),
    }


def create_object(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    project_id = str(payload.get("project_entity_id") or "").strip()
    if not project_id or db.get(Entity, project_id) is None:
        raise ValueError("project_entity_id must reference an existing Core entity.")
    kind = str(payload.get("object_kind") or "research-composite")
    if kind not in OBJECT_KINDS:
        raise ValueError(f"object_kind must be one of {sorted(OBJECT_KINDS)}")
    visibility = str(payload.get("visibility") or "private")
    if visibility not in {"private", "public"}:
        raise ValueError("visibility must be private or public.")
    root_visual = payload.get("root_visual_entity_id")
    if root_visual and db.get(VisualReasoningObjectRecord, root_visual) is None:
        raise ValueError("root_visual_entity_id must reference an existing visual reasoning object.")
    root_explanation = payload.get("root_explanation_id")
    if root_explanation and db.get(ResearchVisualExplanationRecord, root_explanation) is None:
        raise ValueError("root_explanation_id must reference an existing research visual explanation.")
    source_products = sorted({str(v) for v in payload.get("source_products", [])})
    if any(v not in SOURCE_PRODUCTS for v in source_products):
        raise ValueError(f"source_products must be drawn from {sorted(SOURCE_PRODUCTS)}")
    row = CrossProductVisualResearchObjectRecord(
        object_key=str(payload.get("object_key") or "").strip(),
        name=str(payload.get("name") or "").strip(),
        description=payload.get("description"), object_kind=kind,
        lifecycle_state=str(payload.get("lifecycle_state") or "draft"), visibility=visibility,
        project_entity_id=project_id, root_visual_entity_id=root_visual, root_explanation_id=root_explanation,
        source_products_json=source_products, provenance_json=dict(payload.get("provenance") or {}),
        metadata_json=dict(payload.get("metadata") or {}), created_by=str(payload.get("created_by") or "operator"),
    )
    if not row.object_key or not row.name:
        raise ValueError("object_key and name are required.")
    db.add(row)
    try: db.commit()
    except IntegrityError as exc:
        db.rollback(); raise ValueError("object_key must be unique within the project.") from exc
    db.refresh(row); return _ser(row)


def list_objects(db: Session, *, project_entity_id: str | None = None, object_kind: str | None = None, public_only: bool = False, limit: int = 100, offset: int = 0):
    stmt = select(CrossProductVisualResearchObjectRecord)
    count = select(func.count()).select_from(CrossProductVisualResearchObjectRecord)
    if project_entity_id:
        stmt = stmt.where(CrossProductVisualResearchObjectRecord.project_entity_id == project_entity_id); count = count.where(CrossProductVisualResearchObjectRecord.project_entity_id == project_entity_id)
    if object_kind:
        stmt = stmt.where(CrossProductVisualResearchObjectRecord.object_kind == object_kind); count = count.where(CrossProductVisualResearchObjectRecord.object_kind == object_kind)
    if public_only:
        stmt = stmt.where(CrossProductVisualResearchObjectRecord.visibility == "public"); count = count.where(CrossProductVisualResearchObjectRecord.visibility == "public")
    items = db.scalars(stmt.order_by(CrossProductVisualResearchObjectRecord.created_at.desc()).limit(limit).offset(offset)).all()
    return [_ser(x) for x in items], int(db.scalar(count) or 0)


def add_member(db: Session, object_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    obj = _obj(db, object_id)
    product = str(payload.get("source_product") or "").strip()
    kind = str(payload.get("member_kind") or "research-object")
    if product not in SOURCE_PRODUCTS: raise ValueError(f"source_product must be one of {sorted(SOURCE_PRODUCTS)}")
    if kind not in MEMBER_KINDS: raise ValueError(f"member_kind must be one of {sorted(MEMBER_KINDS)}")
    local_entity = payload.get("local_entity_id"); visual_entity = payload.get("visual_entity_id"); explanation = payload.get("explanation_id")
    external_ref = payload.get("external_ref"); source_ref = dict(payload.get("source_ref") or {})
    if local_entity and db.get(Entity, local_entity) is None: raise ValueError("local_entity_id must reference an existing Core entity.")
    if visual_entity and db.get(VisualReasoningObjectRecord, visual_entity) is None: raise ValueError("visual_entity_id must reference an existing visual reasoning object.")
    if explanation and db.get(ResearchVisualExplanationRecord, explanation) is None: raise ValueError("explanation_id must reference an existing research visual explanation.")
    if not any([local_entity, visual_entity, explanation, external_ref, source_ref]):
        raise ValueError("A member requires at least one explicit local or external source reference.")
    if product != "platform-core" and not (external_ref or source_ref):
        raise ValueError("Non-Core product members require external_ref or source_ref metadata; Core does not infer remote identity.")
    row = CrossProductVisualResearchMemberRecord(
        object_id=object_id, member_key=str(payload.get("member_key") or "").strip(), member_kind=kind,
        source_product=product, semantic_role=str(payload.get("semantic_role") or "context"),
        label=str(payload.get("label") or "").strip(), local_entity_id=local_entity, visual_entity_id=visual_entity,
        explanation_id=explanation, external_ref=external_ref, source_ref_json=source_ref,
        display_json=dict(payload.get("display") or {}), provenance_json=dict(payload.get("provenance") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    if not row.member_key or not row.label: raise ValueError("member_key and label are required.")
    db.add(row)
    try: db.commit()
    except IntegrityError as exc:
        db.rollback(); raise ValueError("member_key must be unique within the object.") from exc
    if product not in obj.source_products_json:
        obj.source_products_json = sorted(set(obj.source_products_json or []) | {product}); db.add(obj); db.commit()
    db.refresh(row); return _ser(row)


def add_relation(db: Session, object_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _obj(db, object_id)
    source_id = str(payload.get("source_member_id") or ""); target_id = str(payload.get("target_member_id") or "")
    if source_id == target_id: raise ValueError("Cross-product relations cannot self-reference.")
    _member(db, object_id, source_id); _member(db, object_id, target_id)
    kind = str(payload.get("relation_kind") or "relates-to")
    if kind not in RELATION_KINDS: raise ValueError(f"relation_kind must be one of {sorted(RELATION_KINDS)}")
    row = CrossProductVisualResearchRelationRecord(
        object_id=object_id, relation_key=str(payload.get("relation_key") or "").strip(), source_member_id=source_id,
        target_member_id=target_id, relation_kind=kind, directed=bool(payload.get("directed", True)), label=payload.get("label"),
        rationale=payload.get("rationale"), provenance_json=dict(payload.get("provenance") or {}), metadata_json=dict(payload.get("metadata") or {}),
    )
    if not row.relation_key: raise ValueError("relation_key is required.")
    db.add(row)
    try: db.commit()
    except IntegrityError as exc:
        db.rollback(); raise ValueError("relation_key must be unique within the object.") from exc
    db.refresh(row); return _ser(row)


def add_view(db: Session, object_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _obj(db, object_id); kind = str(payload.get("view_kind") or "composite")
    if kind not in VIEW_KINDS: raise ValueError(f"view_kind must be one of {sorted(VIEW_KINDS)}")
    order = list(payload.get("member_order") or [])
    for member_id in order: _member(db, object_id, str(member_id))
    row = CrossProductVisualResearchViewRecord(
        object_id=object_id, view_key=str(payload.get("view_key") or "").strip(), name=str(payload.get("name") or "").strip(),
        view_kind=kind, renderer_contract=str(payload.get("renderer_contract") or "contract.d3"), member_order_json=order,
        layer_config_json=list(payload.get("layer_config") or []), layout_hints_json=dict(payload.get("layout_hints") or {}),
        interaction_json=dict(payload.get("interaction") or {}), metadata_json=dict(payload.get("metadata") or {}),
    )
    if not row.view_key or not row.name: raise ValueError("view_key and name are required.")
    db.add(row)
    try: db.commit()
    except IntegrityError as exc:
        db.rollback(); raise ValueError("view_key must be unique within the object.") from exc
    db.refresh(row); return _ser(row)


def bundle(db: Session, object_id: str, *, public_only: bool = False) -> dict[str, Any]:
    obj = _obj(db, object_id)
    if public_only and obj.visibility != "public": raise HTTPException(status_code=404, detail="Cross-product visual research object not found.")
    members = db.scalars(select(CrossProductVisualResearchMemberRecord).where(CrossProductVisualResearchMemberRecord.object_id == object_id).order_by(CrossProductVisualResearchMemberRecord.created_at)).all()
    relations = db.scalars(select(CrossProductVisualResearchRelationRecord).where(CrossProductVisualResearchRelationRecord.object_id == object_id).order_by(CrossProductVisualResearchRelationRecord.created_at)).all()
    views = db.scalars(select(CrossProductVisualResearchViewRecord).where(CrossProductVisualResearchViewRecord.object_id == object_id).order_by(CrossProductVisualResearchViewRecord.created_at)).all()
    products = sorted({m.source_product for m in members})
    return {
        "contract": "sc.cross-product-visual-research-object.v1",
        "object": _ser(obj), "members": [_ser(x) for x in members], "relations": [_ser(x) for x in relations], "views": [_ser(x) for x in views],
        "source_products": products, "cross_product": len(products) > 1,
        "boundaries": _boundaries(),
    }


def validate_object(db: Session, object_id: str) -> dict[str, Any]:
    data = bundle(db, object_id); members = data["members"]; relations = data["relations"]
    ids = {m["id"] for m in members}; relation_ok = all(r["source_member_id"] in ids and r["target_member_id"] in ids for r in relations)
    explicit_refs = all(any([m["local_entity_id"], m["visual_entity_id"], m["explanation_id"], m["external_ref"], m["source_ref_json"]]) for m in members)
    products = data["source_products"]
    return {
        "valid": relation_ok and explicit_refs and bool(members), "member_count": len(members), "relation_count": len(relations),
        "source_products": products, "cross_product": len(products) > 1, "relations_resolve": relation_ok,
        "all_members_reference_explicit_sources": explicit_refs, **_boundaries(),
    }


def visualization_spec(db: Session, object_id: str, view_id: str | None = None) -> dict[str, Any]:
    data = bundle(db, object_id); validation = validate_object(db, object_id)
    view = None
    if view_id:
        row = db.get(CrossProductVisualResearchViewRecord, view_id)
        if row is None or row.object_id != object_id: raise ValueError("view_id must belong to this object.")
        view = _ser(row)
    return {
        "contract": "sc.cross-product-visual-research-object.v1", "object": data["object"], "members": data["members"],
        "relations": data["relations"], "view": view, "validation": validation, "renderer_neutral": True,
        "composition": {"source_products": data["source_products"], "preserve_source_product_identity": True, "reference_first": True},
        "layout_execution_by_core": False, "renderer_execution_by_core": False,
    }


def create_snapshot(db: Session, object_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    state = bundle(db, object_id)
    canonical = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    revision = int(db.scalar(select(func.max(CrossProductVisualResearchSnapshotRecord.revision)).where(CrossProductVisualResearchSnapshotRecord.object_id == object_id)) or 0) + 1
    row = CrossProductVisualResearchSnapshotRecord(object_id=object_id, revision=revision, content_hash=digest, state_json=state,
        provenance_json=dict(payload.get("provenance") or {}), created_by=str(payload.get("created_by") or "operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def portability_package(db: Session, object_id: str) -> dict[str, Any]:
    state = bundle(db, object_id); validation = validate_object(db, object_id)
    return {
        "package_contract": "sc.cross-product-visual-research-portable-package.v1", "object_id": object_id,
        "semantic_bundle": state, "validation": validation,
        "portable": True, "reference_first": True, "embedded_remote_content": False,
        "required_consumer_behavior": {"preserve_product_identity": True, "preserve_provenance": True, "resolve_remote_refs_explicitly": True},
    }


def runtime_handoff(db: Session, object_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    state = bundle(db, object_id)
    if payload.get("execute_by_core") is True: raise ValueError("Core cannot execute cross-product runtime work.")
    target = str(payload.get("target_product") or "external")
    if target not in TARGET_PRODUCTS: raise ValueError(f"target_product must be one of {sorted(TARGET_PRODUCTS)}")
    return {
        "contract": "sc.cross-product-visual-research-handoff.v1", "object_id": object_id, "target_product": target,
        "operation": str(payload.get("operation") or "inspect"), "portable_package": portability_package(db, object_id),
        "source_products": state["source_products"], **_boundaries(),
    }
