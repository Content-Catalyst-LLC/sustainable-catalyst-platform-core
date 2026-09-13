from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Entity,
    FlowMapRecord,
    FlowMapChannelRecord,
    FlowMapFlowRecord,
    FlowMapNodeStateRecord,
    FlowMapViewRecord,
    VisualReasoningObjectRecord,
    VisualReasoningElementRecord,
    VisualReasoningRelationRecord,
    VisualizationSpecificationRecord,
)
from . import visual_reasoning, visualization_registry

MAP_STATES = {"draft", "review", "published", "archived"}
QUANTITY_MODES = {"qualitative", "quantitative", "mixed"}
TIME_BASES = {"unspecified", "snapshot", "interval", "series"}
CONSERVATION_POLICIES = {"none", "advisory"}
FLOW_KINDS = {"generic", "material", "energy", "money", "information", "people", "emissions", "resource", "service"}
QUANTITY_KINDS = {"qualitative", "amount", "rate", "count", "index"}
FLOW_STATUSES = {"observed", "estimated", "planned", "scenario", "unknown"}
NODE_STATE_KINDS = {"stock", "capacity", "supply", "demand", "balance", "inventory", "reserve"}
SPEC_KINDS = {"network", "map"}


def _serialize(row) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        out[column.name] = value
    return out


def _parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip().replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _require_map(db: Session, visual_entity_id: str) -> FlowMapRecord:
    row = db.get(FlowMapRecord, visual_entity_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Flow map not found.")
    return row


def _require_public(db: Session, visual_entity_id: str) -> None:
    entity = db.get(Entity, visual_entity_id)
    if entity is None or entity.visibility != "public":
        raise HTTPException(status_code=404, detail="Flow map not found.")


def readiness(db: Session) -> dict[str, Any]:
    return {
        "counts": {
            "flow_maps": db.scalar(select(func.count()).select_from(FlowMapRecord)) or 0,
            "channels": db.scalar(select(func.count()).select_from(FlowMapChannelRecord)) or 0,
            "flows": db.scalar(select(func.count()).select_from(FlowMapFlowRecord)) or 0,
            "node_states": db.scalar(select(func.count()).select_from(FlowMapNodeStateRecord)) or 0,
            "views": db.scalar(select(func.count()).select_from(FlowMapViewRecord)) or 0,
        },
        "flow_kinds": sorted(FLOW_KINDS),
        "quantity_kinds": sorted(QUANTITY_KINDS),
        "flow_statuses": sorted(FLOW_STATUSES),
        "node_state_kinds": sorted(NODE_STATE_KINDS),
        "visual_kind": "flow-map",
        "graph_native": True,
        "visual_reasoning_integrated": True,
        "visualization_registry_integrated": True,
        "flow_relations_reused": True,
        "renderer_neutral": True,
        "layout_engine_in_core": False,
        "unit_conversion_by_core": False,
        "simulation_by_core": False,
        "automatic_conservation_claim": False,
        "automatic_truth_promotion": False,
    }


def create_map(db: Session, payload: dict[str, Any], *, release: str) -> dict[str, Any]:
    state = str(payload.get("map_state") or "draft")
    quantity_mode = str(payload.get("quantity_mode") or "mixed")
    time_basis = str(payload.get("time_basis") or "unspecified")
    conservation_policy = str(payload.get("conservation_policy") or "advisory")
    if state not in MAP_STATES:
        raise ValueError("Unsupported map_state.")
    if quantity_mode not in QUANTITY_MODES:
        raise ValueError("Unsupported quantity_mode.")
    if time_basis not in TIME_BASES:
        raise ValueError("Unsupported time_basis.")
    if conservation_policy not in CONSERVATION_POLICIES:
        raise ValueError("Unsupported conservation_policy.")
    visual = visual_reasoning.create_object(
        db,
        name=str(payload.get("name") or "Flow map"),
        slug=payload.get("slug"),
        description=payload.get("description"),
        entity_id=payload.get("entity_id"),
        visibility=str(payload.get("visibility") or "public"),
        entity_status=str(payload.get("status") or "active"),
        visual_kind="flow-map",
        reasoning_purpose=str(payload.get("reasoning_purpose") or "explain"),
        semantic_state=state,
        coordinate_space=str(payload.get("coordinate_space") or "abstract"),
        project_entity_id=payload.get("project_entity_id"),
        primary_subject_entity_id=payload.get("primary_subject_entity_id"),
        lens=dict(payload.get("lens") or {}),
        filters=dict(payload.get("filters") or {}),
        assumptions=list(payload.get("assumptions") or []),
        metadata={**dict(payload.get("metadata") or {}), "flow_map_release": release},
        release=release,
    )
    row = FlowMapRecord(
        visual_entity_id=visual["id"],
        flow_purpose=str(payload.get("flow_purpose") or "trace"),
        flow_domain=str(payload.get("flow_domain") or "generic"),
        map_state=state,
        quantity_mode=quantity_mode,
        default_unit=payload.get("default_unit"),
        time_basis=time_basis,
        conservation_policy=conservation_policy,
        assumptions_json=list(payload.get("assumptions") or []),
        metadata_json=dict(payload.get("metadata") or {}),
        created_by=str(payload.get("created_by") or "operator"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return read_map(db, row.visual_entity_id)


def read_map(db: Session, visual_entity_id: str, *, public_only: bool = False) -> dict[str, Any]:
    row = _require_map(db, visual_entity_id)
    if public_only:
        _require_public(db, visual_entity_id)
    item = _serialize(row)
    entity = db.get(Entity, visual_entity_id)
    visual = db.get(VisualReasoningObjectRecord, visual_entity_id)
    item["entity"] = {
        "id": entity.id,
        "name": entity.name,
        "description": entity.description,
        "visibility": entity.visibility,
        "status": entity.status,
    } if entity else None
    item["visual_reasoning"] = _serialize(visual) if visual else None
    return item


def list_maps(db: Session, *, public_only: bool = False, limit: int = 100, offset: int = 0):
    stmt = select(FlowMapRecord).join(Entity, Entity.id == FlowMapRecord.visual_entity_id)
    count_stmt = select(func.count()).select_from(FlowMapRecord).join(Entity, Entity.id == FlowMapRecord.visual_entity_id)
    if public_only:
        stmt = stmt.where(Entity.visibility == "public")
        count_stmt = count_stmt.where(Entity.visibility == "public")
    total = int(db.scalar(count_stmt) or 0)
    rows = db.scalars(stmt.order_by(FlowMapRecord.created_at.desc()).limit(limit).offset(offset)).all()
    return [read_map(db, row.visual_entity_id, public_only=public_only) for row in rows], total


def add_channel(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _require_map(db, visual_entity_id)
    flow_kind = str(payload.get("flow_kind") or "generic")
    if flow_kind not in FLOW_KINDS:
        raise ValueError("Unsupported flow_kind.")
    row = FlowMapChannelRecord(
        visual_entity_id=visual_entity_id,
        channel_key=str(payload.get("channel_key") or "channel"),
        name=str(payload.get("name") or payload.get("channel_key") or "Flow channel"),
        flow_kind=flow_kind,
        unit=payload.get("unit"),
        order_index=int(payload.get("order_index", 0)),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Flow-map channel key already exists.") from exc
    return _serialize(row)


def _flow_relation(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> VisualReasoningRelationRecord:
    relation_id = payload.get("relation_id")
    if relation_id:
        relation = db.get(VisualReasoningRelationRecord, str(relation_id))
        if relation is None or relation.visual_entity_id != visual_entity_id:
            raise ValueError("relation_id must belong to this flow map.")
        if relation.relation_kind != "flow":
            raise ValueError("relation_id must reference relation_kind=flow.")
        if relation.direction != "directed":
            raise ValueError("Flow-map relations must be directed.")
        return relation
    source_id = str(payload.get("source_element_id") or "")
    target_id = str(payload.get("target_element_id") or "")
    if not source_id or not target_id:
        raise ValueError("Provide relation_id or source_element_id and target_element_id.")
    source = db.get(VisualReasoningElementRecord, source_id)
    target = db.get(VisualReasoningElementRecord, target_id)
    if source is None or target is None or source.visual_entity_id != visual_entity_id or target.visual_entity_id != visual_entity_id:
        raise ValueError("Flow source and target elements must belong to this flow map.")
    existing = db.scalar(select(VisualReasoningRelationRecord).where(
        VisualReasoningRelationRecord.visual_entity_id == visual_entity_id,
        VisualReasoningRelationRecord.source_element_id == source_id,
        VisualReasoningRelationRecord.target_element_id == target_id,
        VisualReasoningRelationRecord.relation_kind == "flow",
    ))
    if existing is not None:
        return existing
    created = visual_reasoning.add_relation(db, visual_entity_id, {
        "source_element_id": source_id,
        "target_element_id": target_id,
        "relation_kind": "flow",
        "direction": "directed",
        "magnitude": payload.get("quantity_value"),
        "confidence": payload.get("confidence"),
        "uncertainty": dict(payload.get("uncertainty") or {}),
        "provenance": dict(payload.get("provenance") or {}),
        "metadata": {"flow_map_v232": True, **dict(payload.get("relation_metadata") or {})},
    })
    return db.get(VisualReasoningRelationRecord, created["id"])


def add_flow(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    fmap = _require_map(db, visual_entity_id)
    quantity_kind = str(payload.get("quantity_kind") or "qualitative")
    flow_status = str(payload.get("flow_status") or "observed")
    if quantity_kind not in QUANTITY_KINDS:
        raise ValueError("Unsupported quantity_kind.")
    if flow_status not in FLOW_STATUSES:
        raise ValueError("Unsupported flow_status.")
    channel = None
    channel_id = payload.get("channel_id")
    if channel_id:
        channel = db.get(FlowMapChannelRecord, str(channel_id))
        if channel is None or channel.visual_entity_id != visual_entity_id:
            raise ValueError("channel_id must belong to this flow map.")
    relation = _flow_relation(db, visual_entity_id, payload)
    value = payload.get("quantity_value")
    value = None if value is None else float(value)
    lower = payload.get("lower_bound")
    upper = payload.get("upper_bound")
    lower = None if lower is None else float(lower)
    upper = None if upper is None else float(upper)
    if lower is not None and upper is not None and lower > upper:
        raise ValueError("lower_bound cannot exceed upper_bound.")
    start = _parse_dt(payload.get("period_start"))
    end = _parse_dt(payload.get("period_end"))
    if start and end and start > end:
        raise ValueError("period_start cannot be after period_end.")
    unit = payload.get("unit") or (channel.unit if channel else None) or fmap.default_unit
    row = FlowMapFlowRecord(
        visual_entity_id=visual_entity_id,
        flow_key=str(payload.get("flow_key") or "flow"),
        relation_id=relation.id,
        channel_id=channel.id if channel else None,
        quantity_kind=quantity_kind,
        quantity_value=value,
        unit=unit,
        lower_bound=lower,
        upper_bound=upper,
        period_start=start,
        period_end=end,
        flow_status=flow_status,
        uncertainty_json=dict(payload.get("uncertainty") or {}),
        provenance_json=dict(payload.get("provenance") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Flow-map flow key already exists.") from exc
    out = _serialize(row)
    out["source_element_id"] = relation.source_element_id
    out["target_element_id"] = relation.target_element_id
    return out


def add_node_state(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    fmap = _require_map(db, visual_entity_id)
    element = db.get(VisualReasoningElementRecord, str(payload.get("element_id") or ""))
    if element is None or element.visual_entity_id != visual_entity_id:
        raise ValueError("element_id must belong to this flow map.")
    kind = str(payload.get("state_kind") or "stock")
    if kind not in NODE_STATE_KINDS:
        raise ValueError("Unsupported state_kind.")
    value = payload.get("quantity_value")
    row = FlowMapNodeStateRecord(
        visual_entity_id=visual_entity_id,
        element_id=element.id,
        state_key=str(payload.get("state_key") or kind),
        state_kind=kind,
        quantity_value=None if value is None else float(value),
        unit=payload.get("unit") or fmap.default_unit,
        observed_at=_parse_dt(payload.get("observed_at")),
        uncertainty_json=dict(payload.get("uncertainty") or {}),
        provenance_json=dict(payload.get("provenance") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row); db.commit(); db.refresh(row)
    return _serialize(row)


def add_view(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _require_map(db, visual_entity_id)
    channel_ids = [str(x) for x in (payload.get("channel_ids") or [])]
    for channel_id in channel_ids:
        channel = db.get(FlowMapChannelRecord, channel_id)
        if channel is None or channel.visual_entity_id != visual_entity_id:
            raise ValueError("Every channel_id must belong to this flow map.")
    spec_id = payload.get("specification_id")
    if spec_id:
        spec = db.get(VisualizationSpecificationRecord, spec_id)
        if spec is None or spec.visual_entity_id != visual_entity_id:
            raise ValueError("specification_id must belong to this flow map.")
    row = FlowMapViewRecord(
        visual_entity_id=visual_entity_id,
        view_key=str(payload.get("view_key") or "default"),
        name=str(payload.get("name") or payload.get("view_key") or "Flow map view"),
        channel_ids_json=channel_ids,
        filters_json=dict(payload.get("filters") or {}),
        time_window_json=dict(payload.get("time_window") or {}),
        layout_intent_json=dict(payload.get("layout_intent") or {}),
        specification_id=spec_id,
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Flow-map view key already exists.") from exc
    return _serialize(row)


def balance_summary(db: Session, visual_entity_id: str, *, public_only: bool = False) -> dict[str, Any]:
    _require_map(db, visual_entity_id)
    if public_only:
        _require_public(db, visual_entity_id)
    rows = db.scalars(select(FlowMapFlowRecord).where(FlowMapFlowRecord.visual_entity_id == visual_entity_id)).all()
    balances: dict[str, dict[str, dict[str, float]]] = {}
    included = 0
    excluded = 0
    for row in rows:
        if row.quantity_value is None or not row.unit:
            excluded += 1
            continue
        relation = db.get(VisualReasoningRelationRecord, row.relation_id)
        if relation is None:
            excluded += 1
            continue
        unit = row.unit
        balances.setdefault(unit, {})
        src = balances[unit].setdefault(relation.source_element_id, {"incoming": 0.0, "outgoing": 0.0, "net": 0.0})
        dst = balances[unit].setdefault(relation.target_element_id, {"incoming": 0.0, "outgoing": 0.0, "net": 0.0})
        src["outgoing"] += float(row.quantity_value)
        dst["incoming"] += float(row.quantity_value)
        included += 1
    for by_node in balances.values():
        for item in by_node.values():
            item["net"] = item["incoming"] - item["outgoing"]
    return {
        "visual_entity_id": visual_entity_id,
        "balances_by_unit": balances,
        "flows_included": included,
        "flows_excluded": excluded,
        "comparable_within_unit_only": True,
        "unit_conversion_performed": False,
        "conservation_claim": False,
        "simulation_performed": False,
    }


def validate_structure(db: Session, visual_entity_id: str, *, public_only: bool = False) -> dict[str, Any]:
    fmap = _require_map(db, visual_entity_id)
    if public_only:
        _require_public(db, visual_entity_id)
    elements = db.scalars(select(VisualReasoningElementRecord).where(VisualReasoningElementRecord.visual_entity_id == visual_entity_id)).all()
    flows = db.scalars(select(FlowMapFlowRecord).where(FlowMapFlowRecord.visual_entity_id == visual_entity_id)).all()
    channels = db.scalars(select(FlowMapChannelRecord).where(FlowMapChannelRecord.visual_entity_id == visual_entity_id)).all()
    states = db.scalars(select(FlowMapNodeStateRecord).where(FlowMapNodeStateRecord.visual_entity_id == visual_entity_id)).all()
    channel_by_id = {x.id: x for x in channels}
    errors: list[str] = []
    warnings: list[str] = []
    if not elements:
        warnings.append("flow_map_has_no_elements")
    if not flows:
        warnings.append("flow_map_has_no_flows")
    for flow in flows:
        relation = db.get(VisualReasoningRelationRecord, flow.relation_id)
        if relation is None or relation.visual_entity_id != visual_entity_id or relation.relation_kind != "flow" or relation.direction != "directed":
            errors.append(f"invalid_flow_relation:{flow.flow_key}")
        if fmap.quantity_mode == "quantitative" and (flow.quantity_value is None or not flow.unit):
            warnings.append(f"quantitative_flow_incomplete:{flow.flow_key}")
        if flow.channel_id and flow.channel_id in channel_by_id:
            channel = channel_by_id[flow.channel_id]
            if channel.unit and flow.unit and channel.unit != flow.unit:
                warnings.append(f"channel_unit_mismatch:{flow.flow_key}")
    units = sorted({f.unit for f in flows if f.unit})
    if len(units) > 1:
        warnings.append("multiple_units_present_no_automatic_conversion")
    return {
        "valid": not errors,
        "counts": {"elements": len(elements), "channels": len(channels), "flows": len(flows), "node_states": len(states)},
        "errors": errors,
        "warnings": sorted(set(warnings)),
        "structural_only": True,
        "unit_conversion_performed": False,
        "simulation_performed": False,
        "conservation_claim_performed": False,
        "truth_promotion_performed": False,
    }


def compile_specification(db: Session, visual_entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    fmap = _require_map(db, visual_entity_id)
    spec_kind = str(payload.get("spec_kind") or "network")
    if spec_kind not in SPEC_KINDS:
        raise ValueError("Flow-map spec_kind must be network or map.")
    spec_key = str(payload.get("spec_key") or "flow-map-default")
    existing = db.scalars(select(VisualizationSpecificationRecord).where(
        VisualizationSpecificationRecord.visual_entity_id == visual_entity_id,
        VisualizationSpecificationRecord.spec_key == spec_key,
    )).all()
    revision = int(payload.get("revision") or (max([x.revision for x in existing], default=0) + 1))
    channels = db.scalars(select(FlowMapChannelRecord).where(FlowMapChannelRecord.visual_entity_id == visual_entity_id).order_by(FlowMapChannelRecord.order_index)).all()
    spec = visualization_registry.create_specification(db, {
        "visual_entity_id": visual_entity_id,
        "spec_key": spec_key,
        "revision": revision,
        "spec_version": "1.0",
        "spec_kind": spec_kind,
        "title": payload.get("title") or "Flow map",
        "preferred_renderer_key": payload.get("preferred_renderer_key"),
        "renderer_policy": str(payload.get("renderer_policy") or "compatible"),
        "encoding": {
            "node": {"source": "visual_reasoning_elements", "label": "label", "role": "semantic_role"},
            "flow": {
                "source": "flow_map_flows",
                "relation_source": "visual_reasoning_relations",
                "relation_kind": "flow",
                "direction": "directed",
                "magnitude": "quantity_value",
                "unit": "unit",
                "channel": "channel_id",
            },
            "channels": [{"id": c.id, "key": c.channel_key, "name": c.name, "flow_kind": c.flow_kind, "unit": c.unit} for c in channels],
        },
        "interaction": {"pan": True, "zoom": True, "inspect": True, "filter_channels": True, "filter_time": True},
        "accessibility": {"text_summary_required": True, "keyboard_navigation_required": True, "flow_direction_text_required": True},
        "layout_constraints": {
            "runtime_owns_layout": True,
            "core_coordinates_required": False,
            "flow_layout_family": "runtime-selectable",
            **dict(payload.get("layout_constraints") or {}),
        },
        "export": {"semantic_bundle": True, "snapshot_compatible": True, "balance_summary_available": True},
        "metadata": {
            "flow_map_v232": True,
            "flow_purpose": fmap.flow_purpose,
            "flow_domain": fmap.flow_domain,
            "quantity_mode": fmap.quantity_mode,
            "unit_conversion_by_core": False,
            "simulation_by_core": False,
            **dict(payload.get("metadata") or {}),
        },
        "created_by": str(payload.get("created_by") or "operator"),
    })
    return spec


def bundle(db: Session, visual_entity_id: str, *, public_only: bool = False) -> dict[str, Any]:
    base = read_map(db, visual_entity_id, public_only=public_only)
    flows = db.scalars(select(FlowMapFlowRecord).where(FlowMapFlowRecord.visual_entity_id == visual_entity_id).order_by(FlowMapFlowRecord.created_at)).all()
    flow_items = []
    for row in flows:
        item = _serialize(row)
        relation = db.get(VisualReasoningRelationRecord, row.relation_id)
        if relation:
            item["source_element_id"] = relation.source_element_id
            item["target_element_id"] = relation.target_element_id
        flow_items.append(item)
    return {
        "flow_map": base,
        "visual_reasoning": visual_reasoning.bundle(db, visual_entity_id, public_only=public_only),
        "channels": [_serialize(x) for x in db.scalars(select(FlowMapChannelRecord).where(FlowMapChannelRecord.visual_entity_id == visual_entity_id).order_by(FlowMapChannelRecord.order_index, FlowMapChannelRecord.created_at)).all()],
        "flows": flow_items,
        "node_states": [_serialize(x) for x in db.scalars(select(FlowMapNodeStateRecord).where(FlowMapNodeStateRecord.visual_entity_id == visual_entity_id).order_by(FlowMapNodeStateRecord.created_at)).all()],
        "views": [_serialize(x) for x in db.scalars(select(FlowMapViewRecord).where(FlowMapViewRecord.visual_entity_id == visual_entity_id).order_by(FlowMapViewRecord.created_at)).all()],
        "specifications": visualization_registry.list_specifications(db, visual_entity_id=visual_entity_id, public_only=public_only, limit=1000, offset=0)[0],
        "balance_summary": balance_summary(db, visual_entity_id, public_only=public_only),
        "validation": validate_structure(db, visual_entity_id, public_only=public_only),
    }
