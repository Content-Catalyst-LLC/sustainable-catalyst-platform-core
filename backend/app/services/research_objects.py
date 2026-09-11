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
    CalculationTrace,
    Entity,
    ProvenanceActivity,
    Relationship,
    ResearchModelRecord,
    ResearchModelRunRecord,
    ResearchModelVersionRecord,
    ResearchParameterRecord,
    ResearchProjectRecord,
    ResearchResultRecord,
    ResearchScenarioRecord,
    ResearchVariableRecord,
    ScientificStoredObject,
)
from .developers import emit_webhook_event

OBJECT_TYPES = (
    "research-project",
    "model",
    "model-version",
    "variable",
    "parameter",
    "scenario",
    "model-run",
    "result",
)

PROFILE_MODELS = {
    "research-project": ResearchProjectRecord,
    "model": ResearchModelRecord,
    "model-version": ResearchModelVersionRecord,
    "variable": ResearchVariableRecord,
    "parameter": ResearchParameterRecord,
    "scenario": ResearchScenarioRecord,
    "model-run": ResearchModelRunRecord,
    "result": ResearchResultRecord,
}

MODEL_KINDS = {
    "conceptual", "mathematical", "statistical", "simulation", "causal",
    "optimization", "machine-learning", "hybrid",
}
EXECUTION_TARGETS = {"not-executable", "lab", "workbench", "external"}
VARIABLE_ROLES = {"input", "output", "state", "derived", "latent", "control"}
RUN_STATUSES = {"requested", "queued", "running", "completed", "failed", "cancelled"}
SCENARIO_STATES = {"draft", "ready", "active", "archived"}
QUALITY_STATUSES = {"unreviewed", "reviewed", "validated", "rejected"}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:180] or "research-object"


def _parse_datetime(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        text = value.strip().replace("Z", "+00:00")
        if not text:
            return None
        return datetime.fromisoformat(text)
    raise ValueError("Datetime values must be ISO-8601 strings or datetime objects.")


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


def _require_entity_type(db: Session, entity_id: str | None, expected: set[str], field: str) -> Entity | None:
    if entity_id is None:
        return None
    entity = db.get(Entity, entity_id)
    if entity is None:
        raise ValueError(f"{field} does not reference an existing Core entity.")
    if entity.entity_type not in expected:
        allowed = ", ".join(sorted(expected))
        raise ValueError(f"{field} must reference entity type: {allowed}.")
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
        provenance={"managed_by": "research-object-foundation", "core_release": release},
    ))


def _create_profile(db: Session, object_type: str, entity_id: str, attrs: dict[str, Any], *, release: str) -> Any:
    if object_type == "research-project":
        return ResearchProjectRecord(
            entity_id=entity_id,
            research_question=attrs.get("research_question"),
            objective=attrs.get("objective"),
            methodology=attrs.get("methodology"),
            owner_product=str(attrs.get("owner_product", "workspace")),
            lifecycle_state=str(attrs.get("lifecycle_state", "draft")),
            reproducibility_target=str(attrs.get("reproducibility_target", "reproducible")),
            metadata_json=dict(attrs.get("metadata") or {}),
        )

    if object_type == "model":
        project_id = attrs.get("project_entity_id")
        _require_entity_type(db, project_id, {"research-project"}, "project_entity_id")
        model_kind = str(attrs.get("model_kind", "conceptual"))
        if model_kind not in MODEL_KINDS:
            raise ValueError("Unsupported model_kind.")
        execution_target = str(attrs.get("execution_target", "not-executable"))
        if execution_target not in EXECUTION_TARGETS:
            raise ValueError("Unsupported execution_target.")
        row = ResearchModelRecord(
            entity_id=entity_id,
            project_entity_id=project_id,
            model_kind=model_kind,
            execution_target=execution_target,
            specification_json=dict(attrs.get("specification") or {}),
            assumptions_json=list(attrs.get("assumptions") or []),
            equations_json=list(attrs.get("equations") or []),
            reproducibility_status=str(attrs.get("reproducibility_status", "declared")),
            metadata_json=dict(attrs.get("metadata") or {}),
        )
        if project_id:
            _ensure_relationship(db, entity_id, "part_of", project_id, release=release)
        return row

    if object_type == "model-version":
        model_id = str(attrs.get("model_entity_id") or "")
        _require_entity_type(db, model_id, {"model"}, "model_entity_id")
        version_label = str(attrs.get("version_label") or "").strip()
        if not version_label:
            raise ValueError("version_label is required.")
        specification = dict(attrs.get("specification") or {})
        specification_hash = str(attrs.get("specification_hash") or _hash_json(specification)).lower()
        if not re.fullmatch(r"[0-9a-f]{64}", specification_hash):
            raise ValueError("specification_hash must be a 64-character lowercase hexadecimal SHA-256 digest.")
        row = ResearchModelVersionRecord(
            entity_id=entity_id,
            model_entity_id=model_id,
            version_label=version_label,
            code_version=attrs.get("code_version"),
            specification_hash=specification_hash,
            specification_json=specification,
            immutable=bool(attrs.get("immutable", True)),
            metadata_json=dict(attrs.get("metadata") or {}),
        )
        _ensure_relationship(db, entity_id, "version_of", model_id, release=release)
        return row

    if object_type == "variable":
        model_id = str(attrs.get("model_entity_id") or "")
        _require_entity_type(db, model_id, {"model"}, "model_entity_id")
        symbol = str(attrs.get("symbol") or "").strip()
        if not symbol:
            raise ValueError("symbol is required.")
        role = str(attrs.get("role", "input"))
        if role not in VARIABLE_ROLES:
            raise ValueError("Unsupported variable role.")
        row = ResearchVariableRecord(
            entity_id=entity_id,
            model_entity_id=model_id,
            symbol=symbol,
            role=role,
            data_type=str(attrs.get("data_type", "number")),
            unit=attrs.get("unit"),
            definition=attrs.get("definition"),
            domain_json=dict(attrs.get("domain") or {}),
            uncertainty_json=dict(attrs.get("uncertainty") or {}),
            metadata_json=dict(attrs.get("metadata") or {}),
        )
        _ensure_relationship(db, entity_id, "part_of", model_id, release=release)
        return row

    if object_type == "parameter":
        model_id = str(attrs.get("model_entity_id") or "")
        _require_entity_type(db, model_id, {"model"}, "model_entity_id")
        variable_id = attrs.get("variable_entity_id")
        if variable_id:
            variable = _require_entity_type(db, variable_id, {"variable"}, "variable_entity_id")
            profile = db.get(ResearchVariableRecord, variable_id)
            if profile is None or profile.model_entity_id != model_id:
                raise ValueError("variable_entity_id must belong to the same model.")
        name = str(attrs.get("name") or "").strip()
        if not name:
            raise ValueError("name is required.")
        default_value = attrs.get("default_value", {})
        row = ResearchParameterRecord(
            entity_id=entity_id,
            model_entity_id=model_id,
            variable_entity_id=variable_id,
            name=name,
            data_type=str(attrs.get("data_type", "number")),
            unit=attrs.get("unit"),
            default_value_json=default_value,
            bounds_json=dict(attrs.get("bounds") or {}),
            prior_json=dict(attrs.get("prior") or {}),
            sensitivity_enabled=bool(attrs.get("sensitivity_enabled", True)),
            metadata_json=dict(attrs.get("metadata") or {}),
        )
        _ensure_relationship(db, entity_id, "part_of", model_id, release=release)
        if variable_id:
            _ensure_relationship(db, entity_id, "uses", variable_id, release=release)
        return row

    if object_type == "scenario":
        project_id = str(attrs.get("project_entity_id") or "")
        _require_entity_type(db, project_id, {"research-project"}, "project_entity_id")
        base_id = attrs.get("base_scenario_entity_id")
        if base_id:
            _require_entity_type(db, base_id, {"scenario"}, "base_scenario_entity_id")
            base_profile = db.get(ResearchScenarioRecord, base_id)
            if base_profile is None or base_profile.project_entity_id != project_id:
                raise ValueError("base_scenario_entity_id must belong to the same research project.")
        state = str(attrs.get("scenario_state", "draft"))
        if state not in SCENARIO_STATES:
            raise ValueError("Unsupported scenario_state.")
        row = ResearchScenarioRecord(
            entity_id=entity_id,
            project_entity_id=project_id,
            base_scenario_entity_id=base_id,
            scenario_state=state,
            parameter_values_json=dict(attrs.get("parameter_values") or {}),
            assumptions_json=list(attrs.get("assumptions") or []),
            metadata_json=dict(attrs.get("metadata") or {}),
        )
        _ensure_relationship(db, entity_id, "part_of", project_id, release=release)
        if base_id:
            _ensure_relationship(db, entity_id, "derived_from", base_id, release=release)
        return row

    if object_type == "model-run":
        version_id = str(attrs.get("model_version_entity_id") or "")
        _require_entity_type(db, version_id, {"model-version"}, "model_version_entity_id")
        scenario_id = attrs.get("scenario_entity_id")
        if scenario_id:
            _require_entity_type(db, scenario_id, {"scenario"}, "scenario_entity_id")
            version_profile = db.get(ResearchModelVersionRecord, version_id)
            model_profile = db.get(ResearchModelRecord, version_profile.model_entity_id) if version_profile else None
            scenario_profile = db.get(ResearchScenarioRecord, scenario_id)
            if model_profile and model_profile.project_entity_id and (scenario_profile is None or scenario_profile.project_entity_id != model_profile.project_entity_id):
                raise ValueError("scenario_entity_id must belong to the model's research project.")
        activity_id = attrs.get("provenance_activity_id")
        if activity_id and db.get(ProvenanceActivity, activity_id) is None:
            raise ValueError("provenance_activity_id does not exist.")
        trace_id = attrs.get("calculation_trace_id")
        if trace_id and db.get(CalculationTrace, trace_id) is None:
            raise ValueError("calculation_trace_id does not exist.")
        run_status = str(attrs.get("run_status", "requested"))
        if run_status not in RUN_STATUSES:
            raise ValueError("Unsupported run_status.")
        executor_product = str(attrs.get("executor_product", "lab"))
        if executor_product not in {"lab", "workbench", "external"}:
            raise ValueError("executor_product must be lab, workbench, or external.")
        row = ResearchModelRunRecord(
            entity_id=entity_id,
            model_version_entity_id=version_id,
            scenario_entity_id=scenario_id,
            executor_product=executor_product,
            external_run_id=attrs.get("external_run_id"),
            run_status=run_status,
            parameter_values_json=dict(attrs.get("parameter_values") or {}),
            runtime_json=dict(attrs.get("runtime") or {}),
            provenance_activity_id=activity_id,
            calculation_trace_id=trace_id,
            started_at=_parse_datetime(attrs.get("started_at")),
            completed_at=_parse_datetime(attrs.get("completed_at")),
            metadata_json=dict(attrs.get("metadata") or {}),
        )
        _ensure_relationship(db, entity_id, "uses", version_id, release=release)
        if scenario_id:
            _ensure_relationship(db, entity_id, "uses", scenario_id, release=release)
        return row

    if object_type == "result":
        run_id = str(attrs.get("model_run_entity_id") or "")
        _require_entity_type(db, run_id, {"model-run"}, "model_run_entity_id")
        object_id = attrs.get("scientific_object_id")
        if object_id and db.get(ScientificStoredObject, object_id) is None:
            raise ValueError("scientific_object_id does not exist.")
        quality = str(attrs.get("quality_status", "unreviewed"))
        if quality not in QUALITY_STATUSES:
            raise ValueError("Unsupported quality_status.")
        row = ResearchResultRecord(
            entity_id=entity_id,
            model_run_entity_id=run_id,
            result_kind=str(attrs.get("result_kind", "summary")),
            value_json=attrs.get("value", {}),
            summary=attrs.get("summary"),
            scientific_object_id=object_id,
            quality_status=quality,
            uncertainty_json=dict(attrs.get("uncertainty") or {}),
            metadata_json=dict(attrs.get("metadata") or {}),
        )
        _ensure_relationship(db, entity_id, "derived_from", run_id, release=release)
        if object_id:
            # Scientific stored objects are not universal entities, so the durable
            # linkage remains in the typed result profile rather than a graph edge.
            pass
        return row

    raise ValueError("Unsupported research object type.")


def create_object(
    db: Session,
    *,
    object_type: str,
    name: str,
    slug: str | None,
    description: str | None,
    entity_id: str | None,
    visibility: str,
    entity_status: str,
    attributes: dict[str, Any],
    metadata: dict[str, Any],
    release: str,
) -> dict[str, Any]:
    object_type = object_type.strip().lower()
    if object_type not in OBJECT_TYPES:
        raise ValueError("Unsupported research object type.")
    if visibility not in {"public", "internal", "private"}:
        raise ValueError("visibility must be public, internal, or private.")
    entity_id = entity_id or f"sc:{object_type}:{uuid.uuid4()}"
    entity = Entity(
        id=entity_id,
        entity_type=object_type,
        slug=_slugify(slug or name),
        name=name.strip(),
        description=description,
        status=entity_status,
        visibility=visibility,
        schema_version="1.0",
        metadata_json={**dict(metadata or {}), "research_object_foundation": "v2.28.0"},
    )
    db.add(entity)
    try:
        db.flush()
        profile = _create_profile(db, object_type, entity_id, dict(attributes or {}), release=release)
        db.add(profile)
        db.flush()
        emit_webhook_event(
            db,
            event_type="research-object.created",
            resource_type=object_type,
            resource_id=entity_id,
            payload={"id": entity_id, "object_type": object_type, "visibility": visibility},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Research object identity or typed constraints conflict with an existing object.") from exc
    except Exception:
        db.rollback()
        raise
    return object_read(db, entity_id)


def object_or_404(db: Session, entity_id: str, *, public_only: bool = False) -> Entity:
    entity = db.get(Entity, entity_id)
    if entity is None or entity.entity_type not in OBJECT_TYPES or (public_only and entity.visibility != "public"):
        raise HTTPException(status_code=404, detail="Research object not found.")
    return entity


def object_read(db: Session, entity_id: str, *, public_only: bool = False) -> dict[str, Any]:
    entity = object_or_404(db, entity_id, public_only=public_only)
    profile_model = PROFILE_MODELS[entity.entity_type]
    profile = db.get(profile_model, entity.id)
    if profile is None:
        raise HTTPException(status_code=500, detail="Research object typed profile is missing.")
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
    object_type: str | None = None,
    project_entity_id: str | None = None,
    public_only: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    filters = [Entity.entity_type.in_(OBJECT_TYPES)]
    if object_type:
        if object_type not in OBJECT_TYPES:
            raise ValueError("Unsupported research object type.")
        filters.append(Entity.entity_type == object_type)
    if public_only:
        filters.append(Entity.visibility == "public")

    ids: list[str] | None = None
    if project_entity_id:
        related: set[str] = {project_entity_id}
        related.update(db.scalars(select(ResearchModelRecord.entity_id).where(ResearchModelRecord.project_entity_id == project_entity_id)).all())
        related.update(db.scalars(select(ResearchScenarioRecord.entity_id).where(ResearchScenarioRecord.project_entity_id == project_entity_id)).all())
        model_ids = db.scalars(select(ResearchModelRecord.entity_id).where(ResearchModelRecord.project_entity_id == project_entity_id)).all()
        if model_ids:
            related.update(db.scalars(select(ResearchModelVersionRecord.entity_id).where(ResearchModelVersionRecord.model_entity_id.in_(model_ids))).all())
            related.update(db.scalars(select(ResearchVariableRecord.entity_id).where(ResearchVariableRecord.model_entity_id.in_(model_ids))).all())
            related.update(db.scalars(select(ResearchParameterRecord.entity_id).where(ResearchParameterRecord.model_entity_id.in_(model_ids))).all())
        version_ids = [rid for rid in related if (db.get(Entity, rid) and db.get(Entity, rid).entity_type == "model-version")]
        if version_ids:
            run_ids = db.scalars(select(ResearchModelRunRecord.entity_id).where(ResearchModelRunRecord.model_version_entity_id.in_(version_ids))).all()
            related.update(run_ids)
            if run_ids:
                related.update(db.scalars(select(ResearchResultRecord.entity_id).where(ResearchResultRecord.model_run_entity_id.in_(run_ids))).all())
        ids = list(related)
        filters.append(Entity.id.in_(ids))

    total = db.scalar(select(func.count()).select_from(Entity).where(*filters)) or 0
    rows = db.scalars(select(Entity).where(*filters).order_by(Entity.created_at.desc()).offset(offset).limit(limit)).all()
    return [object_read(db, row.id, public_only=public_only) for row in rows], int(total)


def project_bundle(db: Session, project_entity_id: str, *, public_only: bool = False) -> dict[str, Any]:
    project = object_read(db, project_entity_id, public_only=public_only)
    if project["object_type"] != "research-project":
        raise ValueError("project_entity_id must reference a research-project.")
    items, total = list_objects(db, project_entity_id=project_entity_id, public_only=public_only, limit=1000, offset=0)
    by_type = {kind: [] for kind in OBJECT_TYPES}
    for item in items:
        by_type[item["object_type"]].append(item)
    return {"project": project, "objects": by_type, "total_objects": total}


def readiness(db: Session) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for object_type, model in PROFILE_MODELS.items():
        counts[object_type] = int(db.scalar(select(func.count()).select_from(model)) or 0)
    return {
        "object_types": list(OBJECT_TYPES),
        "counts": counts,
        "graph_native": True,
        "provenance_linkable": True,
        "calculation_trace_linkable": True,
        "scientific_object_result_linkable": True,
        "model_execution_by_core": False,
        "model_execution_targets": ["lab", "workbench", "external"],
        "automatic_truth_promotion": False,
        "visual_renderer_in_core": False,
    }
