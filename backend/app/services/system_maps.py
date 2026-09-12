from __future__ import annotations

from typing import Any
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Entity, SystemMapRecord, SystemMapBoundaryRecord, SystemMapDomainRecord,
    SystemMapMembershipRecord, SystemMapViewRecord, VisualReasoningObjectRecord,
    VisualReasoningElementRecord, VisualReasoningRelationRecord, VisualizationSpecificationRecord,
)
from . import visual_reasoning, visualization_registry

BOUNDARY_KINDS = {"included", "excluded", "context", "interface"}
MAP_STATES = {"draft", "review", "published", "archived"}
MEMBERSHIP_ROLES = {"member", "primary", "interface", "context"}


def _serialize(row) -> dict[str, Any]:
    out = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        out[column.name] = value
    return out


def _require_map(db: Session, visual_entity_id: str) -> SystemMapRecord:
    row = db.get(SystemMapRecord, visual_entity_id)
    if row is None:
        raise HTTPException(status_code=404, detail="System map not found.")
    return row


def _require_public(db: Session, visual_entity_id: str) -> None:
    entity = db.get(Entity, visual_entity_id)
    if entity is None or entity.visibility != "public":
        raise HTTPException(status_code=404, detail="System map not found.")


def readiness(db: Session) -> dict[str, Any]:
    return {
        "counts": {
            "system_maps": db.scalar(select(func.count()).select_from(SystemMapRecord)) or 0,
            "boundaries": db.scalar(select(func.count()).select_from(SystemMapBoundaryRecord)) or 0,
            "domains": db.scalar(select(func.count()).select_from(SystemMapDomainRecord)) or 0,
            "memberships": db.scalar(select(func.count()).select_from(SystemMapMembershipRecord)) or 0,
            "views": db.scalar(select(func.count()).select_from(SystemMapViewRecord)) or 0,
        },
        "boundary_kinds": sorted(BOUNDARY_KINDS),
        "map_states": sorted(MAP_STATES),
        "membership_roles": sorted(MEMBERSHIP_ROLES),
        "visual_kind": "system-map",
        "graph_native": True,
        "visual_reasoning_integrated": True,
        "visualization_registry_integrated": True,
        "renderer_neutral": True,
        "layout_engine_in_core": False,
        "causal_inference_by_core": False,
        "automatic_truth_promotion": False,
    }


def create_map(db: Session, payload: dict[str, Any], *, release: str) -> dict[str, Any]:
    state = str(payload.get("map_state") or "draft")
    if state not in MAP_STATES:
        raise ValueError("Unsupported map_state.")
    visual = visual_reasoning.create_object(
        db,
        name=str(payload.get("name") or "System map"),
        slug=payload.get("slug"),
        description=payload.get("description"),
        entity_id=payload.get("entity_id"),
        visibility=str(payload.get("visibility") or "public"),
        entity_status=str(payload.get("status") or "active"),
        visual_kind="system-map",
        reasoning_purpose=str(payload.get("reasoning_purpose") or "explore"),
        semantic_state=state,
        coordinate_space="abstract",
        project_entity_id=payload.get("project_entity_id"),
        primary_subject_entity_id=payload.get("primary_subject_entity_id"),
        lens=dict(payload.get("lens") or {}),
        filters=dict(payload.get("filters") or {}),
        assumptions=list(payload.get("assumptions") or []),
        metadata={**dict(payload.get("metadata") or {}), "system_map_release": release},
        release=release,
    )
    row = SystemMapRecord(
        visual_entity_id=visual["id"],
        system_purpose=str(payload.get("system_purpose") or payload.get("reasoning_purpose") or "explore"),
        perspective=payload.get("perspective"),
        map_state=state,
        boundary_statement=payload.get("boundary_statement"),
        assumptions_json=list(payload.get("assumptions") or []),
        metadata_json=dict(payload.get("metadata") or {}),
        created_by=str(payload.get("created_by") or "operator"),
    )
    db.add(row); db.commit(); db.refresh(row)
    return read_map(db, row.visual_entity_id)


def read_map(db: Session, visual_entity_id: str, *, public_only: bool = False) -> dict[str, Any]:
    row = _require_map(db, visual_entity_id)
    if public_only: _require_public(db, visual_entity_id)
    item = _serialize(row)
    entity = db.get(Entity, visual_entity_id)
    visual = db.get(VisualReasoningObjectRecord, visual_entity_id)
    item["entity"] = {
        "id": entity.id, "name": entity.name, "description": entity.description,
        "visibility": entity.visibility, "status": entity.status,
    } if entity else None
    item["visual_reasoning"] = _serialize(visual) if visual else None
    return item


def list_maps(db: Session, *, public_only: bool = False, limit: int = 100, offset: int = 0):
    stmt = select(SystemMapRecord).join(Entity, Entity.id == SystemMapRecord.visual_entity_id)
    count_stmt = select(func.count()).select_from(SystemMapRecord).join(Entity, Entity.id == SystemMapRecord.visual_entity_id)
    if public_only:
        stmt = stmt.where(Entity.visibility == "public"); count_stmt = count_stmt.where(Entity.visibility == "public")
    total = int(db.scalar(count_stmt) or 0)
    rows = db.scalars(stmt.order_by(SystemMapRecord.created_at.desc()).limit(limit).offset(offset)).all()
    return [read_map(db, row.visual_entity_id, public_only=public_only) for row in rows], total


def add_boundary(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _require_map(db, visual_entity_id)
    kind = str(payload.get("boundary_kind") or "included")
    if kind not in BOUNDARY_KINDS: raise ValueError("Unsupported boundary_kind.")
    row = SystemMapBoundaryRecord(
        visual_entity_id=visual_entity_id,
        boundary_key=str(payload.get("boundary_key") or "boundary"),
        boundary_kind=kind,
        name=str(payload.get("name") or payload.get("boundary_key") or "Boundary"),
        description=payload.get("description"), criteria_json=dict(payload.get("criteria") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="System-map boundary key already exists.") from exc
    return _serialize(row)


def add_domain(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _require_map(db, visual_entity_id)
    parent = payload.get("parent_domain_id")
    if parent:
        prow = db.get(SystemMapDomainRecord, parent)
        if prow is None or prow.visual_entity_id != visual_entity_id: raise ValueError("parent_domain_id must belong to this system map.")
    row = SystemMapDomainRecord(
        visual_entity_id=visual_entity_id, domain_key=str(payload.get("domain_key") or "domain"),
        name=str(payload.get("name") or payload.get("domain_key") or "Domain"), description=payload.get("description"),
        parent_domain_id=parent, order_index=int(payload.get("order_index", 0)), metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="System-map domain key already exists.") from exc
    return _serialize(row)


def add_membership(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _require_map(db, visual_entity_id)
    domain = db.get(SystemMapDomainRecord, str(payload.get("domain_id") or ""))
    if domain is None or domain.visual_entity_id != visual_entity_id: raise ValueError("domain_id must belong to this system map.")
    element = db.get(VisualReasoningElementRecord, str(payload.get("element_id") or ""))
    if element is None or element.visual_entity_id != visual_entity_id: raise ValueError("element_id must belong to this system map.")
    role = str(payload.get("membership_role") or "member")
    if role not in MEMBERSHIP_ROLES: raise ValueError("Unsupported membership_role.")
    row = SystemMapMembershipRecord(visual_entity_id=visual_entity_id, domain_id=domain.id, element_id=element.id, membership_role=role, metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="System-map membership already exists.") from exc
    return _serialize(row)


def add_view(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _require_map(db, visual_entity_id)
    spec_id = payload.get("specification_id")
    if spec_id:
        spec = db.get(VisualizationSpecificationRecord, spec_id)
        if spec is None or spec.visual_entity_id != visual_entity_id: raise ValueError("specification_id must belong to this system map.")
    row = SystemMapViewRecord(
        visual_entity_id=visual_entity_id, view_key=str(payload.get("view_key") or "default"),
        name=str(payload.get("name") or payload.get("view_key") or "System map view"),
        lens_json=dict(payload.get("lens") or {}), filters_json=dict(payload.get("filters") or {}),
        highlights_json=list(payload.get("highlights") or []), layout_intent_json=dict(payload.get("layout_intent") or {}),
        specification_id=spec_id, metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="System-map view key already exists.") from exc
    return _serialize(row)


def validate_structure(db: Session, visual_entity_id: str, *, public_only: bool = False) -> dict[str, Any]:
    _require_map(db, visual_entity_id)
    if public_only: _require_public(db, visual_entity_id)
    elements = db.scalars(select(VisualReasoningElementRecord).where(VisualReasoningElementRecord.visual_entity_id == visual_entity_id)).all()
    relations = db.scalars(select(VisualReasoningRelationRecord).where(VisualReasoningRelationRecord.visual_entity_id == visual_entity_id)).all()
    domains = db.scalars(select(SystemMapDomainRecord).where(SystemMapDomainRecord.visual_entity_id == visual_entity_id)).all()
    memberships = db.scalars(select(SystemMapMembershipRecord).where(SystemMapMembershipRecord.visual_entity_id == visual_entity_id)).all()
    boundaries = db.scalars(select(SystemMapBoundaryRecord).where(SystemMapBoundaryRecord.visual_entity_id == visual_entity_id)).all()
    member_ids = {m.element_id for m in memberships}
    warnings = []
    if not elements: warnings.append("system_map_has_no_elements")
    if elements and not relations: warnings.append("system_map_has_no_relations")
    if not boundaries: warnings.append("system_boundary_not_explicit")
    if domains and any(e.id not in member_ids for e in elements): warnings.append("elements_without_domain_membership")
    return {
        "valid": True,
        "counts": {"elements":len(elements), "relations":len(relations), "domains":len(domains), "memberships":len(memberships), "boundaries":len(boundaries)},
        "warnings": warnings,
        "structural_only": True,
        "causal_inference_performed": False,
        "truth_promotion_performed": False,
    }


def compile_specification(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    smap = _require_map(db, visual_entity_id)
    existing = db.scalars(select(VisualizationSpecificationRecord).where(
        VisualizationSpecificationRecord.visual_entity_id == visual_entity_id,
        VisualizationSpecificationRecord.spec_key == str(payload.get("spec_key") or "system-map-default")
    )).all()
    revision = int(payload.get("revision") or (max([x.revision for x in existing], default=0) + 1))
    domains = db.scalars(select(SystemMapDomainRecord).where(SystemMapDomainRecord.visual_entity_id == visual_entity_id).order_by(SystemMapDomainRecord.order_index)).all()
    boundaries = db.scalars(select(SystemMapBoundaryRecord).where(SystemMapBoundaryRecord.visual_entity_id == visual_entity_id)).all()
    spec = visualization_registry.create_specification(db, {
        "visual_entity_id": visual_entity_id,
        "spec_key": str(payload.get("spec_key") or "system-map-default"),
        "revision": revision,
        "spec_version": "1.0",
        "spec_kind": "diagram",
        "title": payload.get("title") or "System map",
        "preferred_renderer_key": payload.get("preferred_renderer_key"),
        "renderer_policy": str(payload.get("renderer_policy") or "compatible"),
        "encoding": {
            "node": {"source": "visual_reasoning_elements", "label": "label", "role": "semantic_role"},
            "edge": {"source": "visual_reasoning_relations", "type": "relation_kind", "direction": "direction"},
            "domains": [{"id":d.id,"key":d.domain_key,"name":d.name,"order_index":d.order_index} for d in domains],
            "boundaries": [{"id":b.id,"key":b.boundary_key,"kind":b.boundary_kind,"name":b.name} for b in boundaries],
        },
        "interaction": {"pan": True, "zoom": True, "inspect": True, "filter_domains": True},
        "accessibility": {"text_summary_required": True, "keyboard_navigation_required": True},
        "layout_constraints": {"runtime_owns_layout": True, "core_coordinates_required": False, **dict(payload.get("layout_constraints") or {})},
        "export": {"semantic_bundle": True, "snapshot_compatible": True},
        "metadata": {"system_map_v231": True, "system_purpose": smap.system_purpose, "causal_inference_by_core": False, **dict(payload.get("metadata") or {})},
        "created_by": str(payload.get("created_by") or "operator"),
    })
    return spec


def bundle(db: Session, visual_entity_id: str, *, public_only: bool = False) -> dict[str, Any]:
    base = read_map(db, visual_entity_id, public_only=public_only)
    return {
        "system_map": base,
        "visual_reasoning": visual_reasoning.bundle(db, visual_entity_id, public_only=public_only),
        "boundaries": [_serialize(x) for x in db.scalars(select(SystemMapBoundaryRecord).where(SystemMapBoundaryRecord.visual_entity_id == visual_entity_id).order_by(SystemMapBoundaryRecord.created_at)).all()],
        "domains": [_serialize(x) for x in db.scalars(select(SystemMapDomainRecord).where(SystemMapDomainRecord.visual_entity_id == visual_entity_id).order_by(SystemMapDomainRecord.order_index, SystemMapDomainRecord.created_at)).all()],
        "memberships": [_serialize(x) for x in db.scalars(select(SystemMapMembershipRecord).where(SystemMapMembershipRecord.visual_entity_id == visual_entity_id)).all()],
        "views": [_serialize(x) for x in db.scalars(select(SystemMapViewRecord).where(SystemMapViewRecord.visual_entity_id == visual_entity_id).order_by(SystemMapViewRecord.created_at)).all()],
        "specifications": visualization_registry.list_specifications(db, visual_entity_id=visual_entity_id, public_only=public_only, limit=1000, offset=0)[0],
        "validation": validate_structure(db, visual_entity_id, public_only=public_only),
    }
