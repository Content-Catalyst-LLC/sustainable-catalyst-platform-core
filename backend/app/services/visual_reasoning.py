from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session

from ..models import (
    Entity,
    Relationship,
    ResearchProjectRecord,
    ScientificStoredObject,
    VisualReasoningAnnotationRecord,
    VisualReasoningElementRecord,
    VisualReasoningLayerRecord,
    VisualReasoningObjectRecord,
    VisualReasoningRelationRecord,
    VisualReasoningSnapshotRecord,
)
from .developers import emit_webhook_event

VISUAL_KINDS = {
    "generic",
    "system-map",
    "flow-map",
    "scenario-landscape",
    "model-map",
    "model-canvas",
    "evidence-map",
    "causal-map",
    "spatial-temporal-map",
}
REASONING_PURPOSES = {"explore", "compare", "explain", "diagnose", "communicate"}
SEMANTIC_STATES = {"draft", "reviewed", "published", "archived"}
COORDINATE_SPACES = {"abstract", "geographic", "temporal", "cartesian", "none"}
ELEMENT_KINDS = {"node", "group", "metric", "axis", "region", "event", "state"}
SEMANTIC_ROLES = {
    "context", "actor", "input", "output", "stock", "flow", "variable", "parameter",
    "scenario", "model", "run", "result", "evidence", "assumption", "uncertainty", "constraint",
}
RELATION_KINDS = {
    "association", "dependency", "causal", "flow", "contrast", "containment", "temporal",
    "derived-from", "supports", "contradicts", "requires",
}
DIRECTIONS = {"directed", "undirected", "bidirectional"}
LAYER_KINDS = {"context", "data", "model", "scenario", "evidence", "uncertainty", "annotation"}
ANNOTATION_KINDS = {"note", "claim", "caveat", "uncertainty", "assumption", "provenance", "decision"}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:180] or "visual-reasoning-object"


def _hash_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _serialize_row(row: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for attr in sa_inspect(row).mapper.column_attrs:
        value = getattr(row, attr.key)
        if isinstance(value, datetime):
            value = value.isoformat()
        result[attr.key] = value
    if "metadata_json" in result:
        result["metadata"] = result.pop("metadata_json")
    for key in list(result):
        if key.endswith("_json"):
            result[key[:-5]] = result.pop(key)
    return result


def _require_entity(db: Session, entity_id: str | None, field: str) -> Entity | None:
    if entity_id is None:
        return None
    entity = db.get(Entity, entity_id)
    if entity is None:
        raise ValueError(f"{field} does not reference an existing Core entity.")
    return entity


def _ensure_relationship(db: Session, subject_id: str, predicate: str, object_id: str, *, release: str) -> None:
    existing = db.scalar(select(Relationship).where(
        Relationship.subject_id == subject_id,
        Relationship.predicate == predicate,
        Relationship.object_id == object_id,
    ))
    if existing is not None:
        return
    db.add(Relationship(
        subject_id=subject_id,
        predicate=predicate,
        object_id=object_id,
        confidence=1.0,
        status="verified",
        provenance={"managed_by": "visual-reasoning-object-model", "core_release": release},
    ))


def _visual_or_404(db: Session, visual_entity_id: str, *, public_only: bool = False) -> tuple[Entity, VisualReasoningObjectRecord]:
    entity = db.get(Entity, visual_entity_id)
    if entity is None or entity.entity_type != "visual-reasoning-object" or (public_only and entity.visibility != "public"):
        raise HTTPException(status_code=404, detail="Visual reasoning object not found.")
    profile = db.get(VisualReasoningObjectRecord, visual_entity_id)
    if profile is None:
        raise HTTPException(status_code=500, detail="Visual reasoning typed profile is missing.")
    return entity, profile


def readiness(db: Session) -> dict[str, Any]:
    counts = {
        "objects": db.scalar(select(func.count()).select_from(VisualReasoningObjectRecord)) or 0,
        "elements": db.scalar(select(func.count()).select_from(VisualReasoningElementRecord)) or 0,
        "relations": db.scalar(select(func.count()).select_from(VisualReasoningRelationRecord)) or 0,
        "layers": db.scalar(select(func.count()).select_from(VisualReasoningLayerRecord)) or 0,
        "annotations": db.scalar(select(func.count()).select_from(VisualReasoningAnnotationRecord)) or 0,
        "snapshots": db.scalar(select(func.count()).select_from(VisualReasoningSnapshotRecord)) or 0,
    }
    return {
        "visual_kinds": sorted(VISUAL_KINDS),
        "reasoning_purposes": sorted(REASONING_PURPOSES),
        "semantic_roles": sorted(SEMANTIC_ROLES),
        "relation_kinds": sorted(RELATION_KINDS),
        "counts": counts,
        "graph_native": True,
        "renderer_neutral": True,
        "renderer_registry_in_core": True,
        "layout_engine_in_core": False,
        "semantic_snapshot_hashing": "sha256",
        "automatic_truth_promotion": False,
    }


def create_object(
    db: Session,
    *,
    name: str,
    slug: str | None,
    description: str | None,
    entity_id: str | None,
    visibility: str,
    entity_status: str,
    visual_kind: str,
    reasoning_purpose: str,
    semantic_state: str,
    coordinate_space: str,
    project_entity_id: str | None,
    primary_subject_entity_id: str | None,
    lens: dict[str, Any],
    filters: dict[str, Any],
    assumptions: list[Any],
    metadata: dict[str, Any],
    release: str,
) -> dict[str, Any]:
    if visibility not in {"public", "internal", "private"}:
        raise ValueError("visibility must be public, internal, or private.")
    if visual_kind not in VISUAL_KINDS:
        raise ValueError("Unsupported visual_kind.")
    if reasoning_purpose not in REASONING_PURPOSES:
        raise ValueError("Unsupported reasoning_purpose.")
    if semantic_state not in SEMANTIC_STATES:
        raise ValueError("Unsupported semantic_state.")
    if coordinate_space not in COORDINATE_SPACES:
        raise ValueError("Unsupported coordinate_space.")

    project = _require_entity(db, project_entity_id, "project_entity_id")
    if project is not None and project.entity_type != "research-project":
        raise ValueError("project_entity_id must reference a research-project.")
    subject = _require_entity(db, primary_subject_entity_id, "primary_subject_entity_id")

    entity_id = entity_id or f"sc:visual-reasoning-object:{uuid.uuid4()}"
    entity = Entity(
        id=entity_id,
        entity_type="visual-reasoning-object",
        slug=_slugify(slug or name),
        name=name.strip(),
        description=description,
        status=entity_status,
        visibility=visibility,
        schema_version="1.0",
        metadata_json={**dict(metadata or {}), "visual_reasoning_object_model": "v2.29.0"},
    )
    profile = VisualReasoningObjectRecord(
        entity_id=entity_id,
        project_entity_id=project_entity_id,
        primary_subject_entity_id=primary_subject_entity_id,
        visual_kind=visual_kind,
        reasoning_purpose=reasoning_purpose,
        semantic_state=semantic_state,
        coordinate_space=coordinate_space,
        lens_json=dict(lens or {}),
        filters_json=dict(filters or {}),
        assumptions_json=list(assumptions or []),
        metadata_json=dict(metadata or {}),
    )
    db.add(entity)
    try:
        db.flush()
        db.add(profile)
        if project_entity_id:
            _ensure_relationship(db, entity_id, "part_of", project_entity_id, release=release)
        if subject is not None:
            _ensure_relationship(db, entity_id, "about", subject.id, release=release)
        emit_webhook_event(
            db,
            event_type="visual-reasoning-object.created",
            resource_type="visual-reasoning-object",
            resource_id=entity_id,
            payload={"id": entity_id, "visual_kind": visual_kind, "visibility": visibility},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Visual reasoning object conflicts with an existing identity or constraint.") from exc
    except Exception:
        db.rollback()
        raise
    return object_read(db, entity_id)


def object_read(db: Session, visual_entity_id: str, *, public_only: bool = False) -> dict[str, Any]:
    entity, profile = _visual_or_404(db, visual_entity_id, public_only=public_only)
    return {
        "id": entity.id,
        "object_type": entity.entity_type,
        "slug": entity.slug,
        "name": entity.name,
        "description": entity.description,
        "status": entity.status,
        "visibility": entity.visibility,
        "schema_version": entity.schema_version,
        "metadata": entity.metadata_json,
        "created_at": entity.created_at.isoformat(),
        "updated_at": entity.updated_at.isoformat(),
        "attributes": _serialize_row(profile),
    }


def list_objects(
    db: Session,
    *,
    visual_kind: str | None = None,
    project_entity_id: str | None = None,
    public_only: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    stmt = select(VisualReasoningObjectRecord.entity_id).join(Entity, Entity.id == VisualReasoningObjectRecord.entity_id)
    count_stmt = select(func.count()).select_from(VisualReasoningObjectRecord).join(Entity, Entity.id == VisualReasoningObjectRecord.entity_id)
    conditions = []
    if visual_kind:
        if visual_kind not in VISUAL_KINDS:
            raise ValueError("Unsupported visual_kind.")
        conditions.append(VisualReasoningObjectRecord.visual_kind == visual_kind)
    if project_entity_id:
        conditions.append(VisualReasoningObjectRecord.project_entity_id == project_entity_id)
    if public_only:
        conditions.append(Entity.visibility == "public")
    if conditions:
        stmt = stmt.where(*conditions)
        count_stmt = count_stmt.where(*conditions)
    total = int(db.scalar(count_stmt) or 0)
    ids = db.scalars(stmt.order_by(Entity.created_at.desc()).limit(limit).offset(offset)).all()
    return [object_read(db, entity_id, public_only=public_only) for entity_id in ids], total


def add_element(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _visual_or_404(db, visual_entity_id)
    kind = str(payload.get("element_kind", "node"))
    role = str(payload.get("semantic_role", "context"))
    if kind not in ELEMENT_KINDS:
        raise ValueError("Unsupported element_kind.")
    if role not in SEMANTIC_ROLES:
        raise ValueError("Unsupported semantic_role.")
    source_entity_id = payload.get("source_entity_id")
    if source_entity_id:
        _require_entity(db, source_entity_id, "source_entity_id")
    source_scientific_object_id = payload.get("source_scientific_object_id")
    if source_scientific_object_id and db.get(ScientificStoredObject, source_scientific_object_id) is None:
        raise ValueError("source_scientific_object_id does not exist.")
    row = VisualReasoningElementRecord(
        visual_entity_id=visual_entity_id,
        element_key=str(payload["element_key"]),
        element_kind=kind,
        semantic_role=role,
        label=str(payload.get("label") or payload["element_key"]),
        source_entity_id=source_entity_id,
        source_scientific_object_id=source_scientific_object_id,
        value_json=payload.get("value"),
        uncertainty_json=dict(payload.get("uncertainty") or {}),
        provenance_json=dict(payload.get("provenance") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Visual element key already exists for this visual object.") from exc
    return _serialize_row(row)


def add_relation(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _visual_or_404(db, visual_entity_id)
    kind = str(payload.get("relation_kind", "association"))
    direction = str(payload.get("direction", "directed"))
    if kind not in RELATION_KINDS:
        raise ValueError("Unsupported relation_kind.")
    if direction not in DIRECTIONS:
        raise ValueError("Unsupported direction.")
    source = db.get(VisualReasoningElementRecord, str(payload["source_element_id"]))
    target = db.get(VisualReasoningElementRecord, str(payload["target_element_id"]))
    if source is None or target is None or source.visual_entity_id != visual_entity_id or target.visual_entity_id != visual_entity_id:
        raise ValueError("source_element_id and target_element_id must belong to the same visual reasoning object.")
    confidence = payload.get("confidence")
    if confidence is not None and not 0 <= float(confidence) <= 1:
        raise ValueError("confidence must be between 0 and 1.")
    row = VisualReasoningRelationRecord(
        visual_entity_id=visual_entity_id,
        source_element_id=source.id,
        target_element_id=target.id,
        relation_kind=kind,
        direction=direction,
        magnitude=payload.get("magnitude"),
        confidence=confidence,
        uncertainty_json=dict(payload.get("uncertainty") or {}),
        provenance_json=dict(payload.get("provenance") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Visual relation already exists.") from exc
    return _serialize_row(row)


def add_layer(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _visual_or_404(db, visual_entity_id)
    kind = str(payload.get("layer_kind", "context"))
    if kind not in LAYER_KINDS:
        raise ValueError("Unsupported layer_kind.")
    row = VisualReasoningLayerRecord(
        visual_entity_id=visual_entity_id,
        layer_key=str(payload["layer_key"]),
        name=str(payload.get("name") or payload["layer_key"]),
        layer_kind=kind,
        order_index=int(payload.get("order_index", 0)),
        visible_by_default=bool(payload.get("visible_by_default", True)),
        filter_json=dict(payload.get("filter") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Visual layer key already exists for this visual object.") from exc
    return _serialize_row(row)


def add_annotation(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _visual_or_404(db, visual_entity_id)
    kind = str(payload.get("annotation_kind", "note"))
    if kind not in ANNOTATION_KINDS:
        raise ValueError("Unsupported annotation_kind.")
    element_id = payload.get("element_id")
    relation_id = payload.get("relation_id")
    if element_id:
        element = db.get(VisualReasoningElementRecord, element_id)
        if element is None or element.visual_entity_id != visual_entity_id:
            raise ValueError("element_id must belong to the visual reasoning object.")
    if relation_id:
        relation = db.get(VisualReasoningRelationRecord, relation_id)
        if relation is None or relation.visual_entity_id != visual_entity_id:
            raise ValueError("relation_id must belong to the visual reasoning object.")
    evidence_entity_id = payload.get("evidence_entity_id")
    if evidence_entity_id:
        _require_entity(db, evidence_entity_id, "evidence_entity_id")
    row = VisualReasoningAnnotationRecord(
        visual_entity_id=visual_entity_id,
        element_id=element_id,
        relation_id=relation_id,
        annotation_kind=kind,
        text=str(payload["text"]),
        evidence_entity_id=evidence_entity_id,
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row); db.commit(); db.refresh(row)
    return _serialize_row(row)


def _semantic_state(db: Session, visual_entity_id: str) -> dict[str, Any]:
    obj = object_read(db, visual_entity_id)
    elements = db.scalars(select(VisualReasoningElementRecord).where(VisualReasoningElementRecord.visual_entity_id == visual_entity_id).order_by(VisualReasoningElementRecord.element_key)).all()
    relations = db.scalars(select(VisualReasoningRelationRecord).where(VisualReasoningRelationRecord.visual_entity_id == visual_entity_id).order_by(VisualReasoningRelationRecord.id)).all()
    layers = db.scalars(select(VisualReasoningLayerRecord).where(VisualReasoningLayerRecord.visual_entity_id == visual_entity_id).order_by(VisualReasoningLayerRecord.order_index, VisualReasoningLayerRecord.layer_key)).all()
    annotations = db.scalars(select(VisualReasoningAnnotationRecord).where(VisualReasoningAnnotationRecord.visual_entity_id == visual_entity_id).order_by(VisualReasoningAnnotationRecord.created_at, VisualReasoningAnnotationRecord.id)).all()
    return {
        "object": obj,
        "elements": [_serialize_row(row) for row in elements],
        "relations": [_serialize_row(row) for row in relations],
        "layers": [_serialize_row(row) for row in layers],
        "annotations": [_serialize_row(row) for row in annotations],
    }


def create_snapshot(db: Session, visual_entity_id: str, *, snapshot_key: str, created_by: str, provenance: dict[str, Any]) -> dict[str, Any]:
    _visual_or_404(db, visual_entity_id)
    state = _semantic_state(db, visual_entity_id)
    row = VisualReasoningSnapshotRecord(
        visual_entity_id=visual_entity_id,
        snapshot_key=snapshot_key,
        state_hash=_hash_json(state),
        semantic_state_json=state,
        provenance_json=dict(provenance or {}),
        created_by=created_by,
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="snapshot_key already exists for this visual reasoning object.") from exc
    return _serialize_row(row)


def bundle(db: Session, visual_entity_id: str, *, public_only: bool = False) -> dict[str, Any]:
    obj = object_read(db, visual_entity_id, public_only=public_only)
    state = _semantic_state(db, visual_entity_id)
    snapshots = db.scalars(select(VisualReasoningSnapshotRecord).where(VisualReasoningSnapshotRecord.visual_entity_id == visual_entity_id).order_by(VisualReasoningSnapshotRecord.created_at)).all()
    if public_only:
        # The parent object's public visibility governs child semantic metadata.
        pass
    return {
        **state,
        "object": obj,
        "snapshots": [_serialize_row(row) for row in snapshots],
        "renderer_contract": {
            "renderer_neutral": True,
            "layout_engine_in_core": False,
            "style_specification_in_core": False,
            "visualization_specification_layer": "v2.36.0 System Maps + Flow Maps + Scenario Landscapes + Interactive Model Canvas + Scenario Compute Engine + Uncertainty/Sensitivity/Ensemble Reasoning on v2.30 Visualization Specification & Renderer Registry",
            "renderer_execution_by_core": False,
        },
    }
