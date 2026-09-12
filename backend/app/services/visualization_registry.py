from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Entity,
    RendererCompatibilityRuleRecord,
    RendererDefinitionRecord,
    RendererResolutionRecord,
    RendererVersionRecord,
    VisualizationSpecificationRecord,
    VisualReasoningObjectRecord,
)

SPEC_KINDS = {"generic", "chart", "network", "diagram", "map", "table", "composite"}
RENDERER_POLICIES = {"compatible", "preferred-only", "registry-priority"}


def _serialize(row) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        out[column.name] = value
    return out


def _canonical_spec(payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
    canonical = {
        "visual_entity_id": payload["visual_entity_id"],
        "spec_key": payload["spec_key"],
        "revision": int(payload.get("revision", 1)),
        "spec_version": payload.get("spec_version", "1.0"),
        "spec_kind": payload.get("spec_kind", "generic"),
        "title": payload.get("title"),
        "preferred_renderer_key": payload.get("preferred_renderer_key"),
        "renderer_policy": payload.get("renderer_policy", "compatible"),
        "encoding": dict(payload.get("encoding") or {}),
        "interaction": dict(payload.get("interaction") or {}),
        "accessibility": dict(payload.get("accessibility") or {}),
        "layout_constraints": dict(payload.get("layout_constraints") or {}),
        "export": dict(payload.get("export") or {}),
        "metadata": dict(payload.get("metadata") or {}),
    }
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return canonical, hashlib.sha256(raw).hexdigest()


def readiness(db: Session) -> dict[str, Any]:
    counts = {
        "specifications": db.scalar(select(func.count()).select_from(VisualizationSpecificationRecord)) or 0,
        "renderers": db.scalar(select(func.count()).select_from(RendererDefinitionRecord)) or 0,
        "renderer_versions": db.scalar(select(func.count()).select_from(RendererVersionRecord)) or 0,
        "compatibility_rules": db.scalar(select(func.count()).select_from(RendererCompatibilityRuleRecord)) or 0,
        "resolutions": db.scalar(select(func.count()).select_from(RendererResolutionRecord)) or 0,
    }
    return {
        "counts": counts,
        "spec_kinds": sorted(SPEC_KINDS),
        "renderer_policies": sorted(RENDERER_POLICIES),
        "specification_hashing": "sha256",
        "renderer_registry": True,
        "compatibility_resolution": True,
        "renderer_execution_by_core": False,
        "layout_execution_by_core": False,
        "render_output_storage_by_core": False,
        "selection_is_advisory": True,
    }


def create_specification(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    visual_id = str(payload.get("visual_entity_id") or "")
    if not visual_id or db.get(VisualReasoningObjectRecord, visual_id) is None:
        raise ValueError("visual_entity_id must reference a visual-reasoning-object.")
    spec_kind = str(payload.get("spec_kind", "generic"))
    if spec_kind not in SPEC_KINDS:
        raise ValueError("Unsupported spec_kind.")
    policy = str(payload.get("renderer_policy", "compatible"))
    if policy not in RENDERER_POLICIES:
        raise ValueError("Unsupported renderer_policy.")
    preferred = payload.get("preferred_renderer_key")
    if preferred and db.get(RendererDefinitionRecord, preferred) is None:
        raise ValueError("preferred_renderer_key is not registered.")
    canonical, state_hash = _canonical_spec(payload)
    row = VisualizationSpecificationRecord(
        visual_entity_id=visual_id,
        spec_key=str(payload.get("spec_key") or "default"),
        revision=int(payload.get("revision", 1)),
        spec_version=str(payload.get("spec_version", "1.0")),
        spec_kind=spec_kind,
        title=payload.get("title"),
        preferred_renderer_key=preferred,
        renderer_policy=policy,
        encoding_json=canonical["encoding"],
        interaction_json=canonical["interaction"],
        accessibility_json=canonical["accessibility"],
        layout_constraints_json=canonical["layout_constraints"],
        export_json=canonical["export"],
        metadata_json=canonical["metadata"],
        state_hash=state_hash,
        created_by=str(payload.get("created_by", "operator")),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Visualization specification revision already exists.") from exc
    return specification_read(db, row.id)


def specification_read(db: Session, specification_id: str, *, public_only: bool = False) -> dict[str, Any]:
    row = db.get(VisualizationSpecificationRecord, specification_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Visualization specification not found.")
    entity = db.get(Entity, row.visual_entity_id)
    if public_only and (entity is None or entity.visibility != "public"):
        raise HTTPException(status_code=404, detail="Visualization specification not found.")
    return _serialize(row)


def list_specifications(db: Session, *, visual_entity_id: str | None = None, public_only: bool = False, limit: int = 100, offset: int = 0):
    stmt = select(VisualizationSpecificationRecord).join(Entity, Entity.id == VisualizationSpecificationRecord.visual_entity_id)
    count_stmt = select(func.count()).select_from(VisualizationSpecificationRecord).join(Entity, Entity.id == VisualizationSpecificationRecord.visual_entity_id)
    conditions = []
    if visual_entity_id:
        conditions.append(VisualizationSpecificationRecord.visual_entity_id == visual_entity_id)
    if public_only:
        conditions.append(Entity.visibility == "public")
    if conditions:
        stmt = stmt.where(*conditions); count_stmt = count_stmt.where(*conditions)
    total = int(db.scalar(count_stmt) or 0)
    rows = db.scalars(stmt.order_by(VisualizationSpecificationRecord.created_at.desc()).limit(limit).offset(offset)).all()
    return [_serialize(row) for row in rows], total


def list_renderers(db: Session, *, public_only: bool = False) -> list[dict[str, Any]]:
    stmt = select(RendererDefinitionRecord)
    if public_only:
        stmt = stmt.where(RendererDefinitionRecord.public_summary.is_(True))
    rows = db.scalars(stmt.order_by(RendererDefinitionRecord.renderer_key)).all()
    result = []
    for row in rows:
        item = _serialize(row)
        versions = db.scalars(select(RendererVersionRecord).where(RendererVersionRecord.renderer_key == row.renderer_key).order_by(RendererVersionRecord.created_at.desc())).all()
        item["versions"] = [_serialize(v) for v in versions]
        result.append(item)
    return result


def renderer_read(db: Session, renderer_key: str, *, public_only: bool = False) -> dict[str, Any]:
    row = db.get(RendererDefinitionRecord, renderer_key)
    if row is None or (public_only and not row.public_summary):
        raise HTTPException(status_code=404, detail="Renderer contract not found.")
    item = _serialize(row)
    item["versions"] = [_serialize(v) for v in db.scalars(select(RendererVersionRecord).where(RendererVersionRecord.renderer_key == renderer_key)).all()]
    item["compatibility_rules"] = [_serialize(v) for v in db.scalars(select(RendererCompatibilityRuleRecord).where(RendererCompatibilityRuleRecord.renderer_key == renderer_key)).all()]
    return item


def resolve_renderer(db: Session, specification_id: str, *, requested_renderer_key: str | None = None, created_by: str = "operator") -> dict[str, Any]:
    spec = db.get(VisualizationSpecificationRecord, specification_id)
    if spec is None:
        raise HTTPException(status_code=404, detail="Visualization specification not found.")
    visual = db.get(VisualReasoningObjectRecord, spec.visual_entity_id)
    if visual is None:
        raise ValueError("Visualization specification has no visual reasoning object.")
    candidate_key = requested_renderer_key or spec.preferred_renderer_key
    rules = db.scalars(
        select(RendererCompatibilityRuleRecord)
        .where(RendererCompatibilityRuleRecord.enabled.is_(True))
        .where(RendererCompatibilityRuleRecord.visual_kind.in_([visual.visual_kind, "*"]))
        .where(RendererCompatibilityRuleRecord.spec_kind.in_([spec.spec_kind, "*"]))
        .order_by(RendererCompatibilityRuleRecord.priority.desc(), RendererCompatibilityRuleRecord.renderer_key.asc())
    ).all()
    compatible = []
    for rule in rules:
        renderer = db.get(RendererDefinitionRecord, rule.renderer_key)
        if renderer is None or not renderer.enabled:
            continue
        if spec.spec_version not in (renderer.supported_spec_versions_json or []):
            continue
        required = rule.required_capabilities_json or []
        capabilities = renderer.capabilities_json or {}
        if any(not capabilities.get(name, False) for name in required):
            continue
        compatible.append(rule)
    selected = None
    mode = "registry-priority"
    if candidate_key:
        match = next((rule for rule in compatible if rule.renderer_key == candidate_key), None)
        if match:
            selected = match
            mode = "requested" if requested_renderer_key else "preferred"
        elif spec.renderer_policy == "preferred-only" or requested_renderer_key:
            compatible = []
    elif spec.renderer_policy == "preferred-only":
        compatible = []
    if selected is None and compatible:
        selected = compatible[0]
    renderer = db.get(RendererDefinitionRecord, selected.renderer_key) if selected else None
    version = None
    if renderer:
        version = db.scalar(select(RendererVersionRecord).where(RendererVersionRecord.renderer_key == renderer.renderer_key, RendererVersionRecord.status == "active").order_by(RendererVersionRecord.created_at.desc()))
    resolution_state = "resolved" if renderer else "unresolved"
    row = RendererResolutionRecord(
        specification_id=specification_id,
        requested_renderer_key=requested_renderer_key,
        resolved_renderer_key=renderer.renderer_key if renderer else None,
        resolved_renderer_version=version.version if version else None,
        resolution_state=resolution_state,
        selection_mode=mode if renderer else "unresolved",
        rationale_json={
            "visual_kind": visual.visual_kind,
            "spec_kind": spec.spec_kind,
            "compatible_renderer_keys": [rule.renderer_key for rule in compatible],
            "renderer_policy": spec.renderer_policy,
            "execution_performed": False,
        },
        execution_performed=False,
        created_by=created_by,
    )
    db.add(row); db.commit(); db.refresh(row)
    return _serialize(row)


def register_renderer(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    key = str(payload.get("renderer_key") or "").strip()
    if not key:
        raise ValueError("renderer_key is required.")
    if payload.get("executable_by_core") is True:
        raise ValueError("Platform Core cannot register a renderer as executable_by_core.")
    if db.get(RendererDefinitionRecord, key) is not None:
        raise HTTPException(status_code=409, detail="Renderer contract already exists.")
    versions = list(payload.get("supported_spec_versions") or ["1.0"])
    if not versions:
        raise ValueError("supported_spec_versions must not be empty.")
    row = RendererDefinitionRecord(
        renderer_key=key,
        name=str(payload.get("name") or key),
        description=payload.get("description"),
        renderer_family=str(payload.get("renderer_family") or "custom"),
        runtime=str(payload.get("runtime") or "external-runtime"),
        execution_mode=str(payload.get("execution_mode") or "external-runtime"),
        enabled=bool(payload.get("enabled", True)),
        executable_by_core=False,
        public_summary=bool(payload.get("public_summary", True)),
        supported_spec_versions_json=versions,
        capabilities_json=dict(payload.get("capabilities") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row); db.commit(); db.refresh(row)
    return renderer_read(db, key)


def register_renderer_version(db: Session, renderer_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    if db.get(RendererDefinitionRecord, renderer_key) is None:
        raise HTTPException(status_code=404, detail="Renderer contract not found.")
    row = RendererVersionRecord(
        renderer_key=renderer_key,
        version=str(payload.get("version") or "contract-v1"),
        status=str(payload.get("status") or "active"),
        contract_version=str(payload.get("contract_version") or "1.0"),
        capabilities_json=dict(payload.get("capabilities") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Renderer version already exists.") from exc
    return _serialize(row)


def register_compatibility_rule(db: Session, renderer_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    if db.get(RendererDefinitionRecord, renderer_key) is None:
        raise HTTPException(status_code=404, detail="Renderer contract not found.")
    spec_kind = str(payload.get("spec_kind") or "generic")
    if spec_kind != "*" and spec_kind not in SPEC_KINDS:
        raise ValueError("Unsupported spec_kind.")
    row = RendererCompatibilityRuleRecord(
        renderer_key=renderer_key,
        visual_kind=str(payload.get("visual_kind") or "*"),
        spec_kind=spec_kind,
        priority=int(payload.get("priority", 100)),
        required_capabilities_json=list(payload.get("required_capabilities") or []),
        constraints_json=dict(payload.get("constraints") or {}),
        enabled=bool(payload.get("enabled", True)),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Renderer compatibility rule already exists.") from exc
    return _serialize(row)


def list_resolutions(db: Session, specification_id: str) -> list[dict[str, Any]]:
    if db.get(VisualizationSpecificationRecord, specification_id) is None:
        raise HTTPException(status_code=404, detail="Visualization specification not found.")
    rows = db.scalars(select(RendererResolutionRecord).where(RendererResolutionRecord.specification_id == specification_id).order_by(RendererResolutionRecord.created_at.asc())).all()
    return [_serialize(row) for row in rows]
