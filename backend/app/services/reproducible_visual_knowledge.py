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
    CrossProductVisualResearchObjectRecord,
    CrossProductVisualResearchSnapshotRecord,
    ReproducibleVisualKnowledgePackageRecord,
    ReproducibleVisualKnowledgeInputRecord,
    ReproducibleVisualKnowledgeEnvironmentRecord,
    ReproducibleVisualKnowledgeReplayPlanRecord,
    ReproducibleVisualKnowledgeVerificationRecord,
    ReproducibleVisualKnowledgeSnapshotRecord,
)
from . import cross_product_visual_research as cpvr

SOURCE_PRODUCTS = {
    "platform-core", "knowledge-library", "research-librarian", "lab", "workbench",
    "site-intelligence", "decision-studio", "catalyst-data", "external",
}
INPUT_ROLES = {"source", "dataset", "evidence", "model", "parameter-set", "scenario", "code", "configuration", "visual-spec", "artifact"}
REPRO_LEVELS = {"documented", "reference-locked", "environment-locked", "replay-ready", "externally-verified"}
VERIFICATION_KINDS = {"integrity", "semantic", "replay", "output", "external-certification"}


def _ser(row):
    out = {}
    for col in row.__table__.columns:
        value = getattr(row, col.name)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        out[col.name] = value
    return out


def _package(db: Session, package_id: str) -> ReproducibleVisualKnowledgePackageRecord:
    row = db.get(ReproducibleVisualKnowledgePackageRecord, package_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Reproducible visual knowledge package not found.")
    return row


def _boundaries() -> dict[str, bool]:
    return {
        "knowledge_state_capture_by_core": True,
        "manifest_hashing_by_core": True,
        "integrity_verification_by_core": True,
        "specialist_execution_by_core": False,
        "remote_product_fetch_by_core": False,
        "arbitrary_code_execution_by_core": False,
        "replay_execution_by_core": False,
        "output_equivalence_claim_by_core_without_external_evidence": False,
        "automatic_truth_promotion": False,
    }


def readiness(db: Session) -> dict[str, Any]:
    def count(model):
        return int(db.scalar(select(func.count()).select_from(model)) or 0)
    return {
        "migration_0045_applied": True,
        "counts": {
            "packages": count(ReproducibleVisualKnowledgePackageRecord),
            "inputs": count(ReproducibleVisualKnowledgeInputRecord),
            "environments": count(ReproducibleVisualKnowledgeEnvironmentRecord),
            "replay_plans": count(ReproducibleVisualKnowledgeReplayPlanRecord),
            "verifications": count(ReproducibleVisualKnowledgeVerificationRecord),
            "snapshots": count(ReproducibleVisualKnowledgeSnapshotRecord),
        },
        "contract": "sc.reproducible-visual-knowledge.v1",
        "portable_package_contract": "sc.reproducible-visual-knowledge-package.v1",
        "reproducibility_levels": sorted(REPRO_LEVELS),
        "input_roles": sorted(INPUT_ROLES),
        **_boundaries(),
    }


def create_package(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    project_id = str(payload.get("project_entity_id") or "").strip()
    source_object_id = str(payload.get("source_object_id") or "").strip()
    if not project_id or db.get(Entity, project_id) is None:
        raise ValueError("project_entity_id must reference an existing Core entity.")
    source = db.get(CrossProductVisualResearchObjectRecord, source_object_id)
    if source is None:
        raise ValueError("source_object_id must reference an existing cross-product visual research object.")
    if source.project_entity_id != project_id:
        raise ValueError("source_object_id must belong to the same project_entity_id.")
    source_snapshot_id = payload.get("source_snapshot_id")
    if source_snapshot_id:
        snap = db.get(CrossProductVisualResearchSnapshotRecord, source_snapshot_id)
        if snap is None or snap.object_id != source_object_id:
            raise ValueError("source_snapshot_id must belong to source_object_id.")
    level = str(payload.get("reproducibility_level") or "documented")
    if level not in REPRO_LEVELS:
        raise ValueError(f"reproducibility_level must be one of {sorted(REPRO_LEVELS)}")
    visibility = str(payload.get("visibility") or "private")
    if visibility not in {"private", "public"}:
        raise ValueError("visibility must be private or public.")
    row = ReproducibleVisualKnowledgePackageRecord(
        package_key=str(payload.get("package_key") or "").strip(),
        name=str(payload.get("name") or "").strip(), description=payload.get("description"),
        project_entity_id=project_id, source_object_id=source_object_id, source_snapshot_id=source_snapshot_id,
        lifecycle_state=str(payload.get("lifecycle_state") or "draft"), visibility=visibility,
        reproducibility_level=level, provenance_json=dict(payload.get("provenance") or {}),
        metadata_json=dict(payload.get("metadata") or {}), created_by=str(payload.get("created_by") or "operator"),
    )
    if not row.package_key or not row.name:
        raise ValueError("package_key and name are required.")
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback(); raise ValueError("package_key must be unique within the project.") from exc
    db.refresh(row); return _ser(row)


def list_packages(db: Session, *, project_entity_id: str | None = None, public_only: bool = False, limit: int = 100, offset: int = 0):
    stmt = select(ReproducibleVisualKnowledgePackageRecord)
    count = select(func.count()).select_from(ReproducibleVisualKnowledgePackageRecord)
    if project_entity_id:
        stmt = stmt.where(ReproducibleVisualKnowledgePackageRecord.project_entity_id == project_entity_id)
        count = count.where(ReproducibleVisualKnowledgePackageRecord.project_entity_id == project_entity_id)
    if public_only:
        stmt = stmt.where(ReproducibleVisualKnowledgePackageRecord.visibility == "public")
        count = count.where(ReproducibleVisualKnowledgePackageRecord.visibility == "public")
    rows = db.scalars(stmt.order_by(ReproducibleVisualKnowledgePackageRecord.created_at.desc()).limit(limit).offset(offset)).all()
    return [_ser(r) for r in rows], int(db.scalar(count) or 0)


def add_input(db: Session, package_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _package(db, package_id)
    role = str(payload.get("input_role") or "source")
    product = str(payload.get("source_product") or "").strip()
    source_ref = str(payload.get("source_ref") or "").strip()
    if role not in INPUT_ROLES:
        raise ValueError(f"input_role must be one of {sorted(INPUT_ROLES)}")
    if product not in SOURCE_PRODUCTS:
        raise ValueError(f"source_product must be one of {sorted(SOURCE_PRODUCTS)}")
    if not source_ref:
        raise ValueError("source_ref is required; reproducible inputs cannot rely on implicit remote identity.")
    digest = payload.get("content_hash")
    if digest is not None:
        digest = str(digest).lower().strip()
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("content_hash must be a 64-character SHA-256 hexadecimal digest.")
    row = ReproducibleVisualKnowledgeInputRecord(
        package_id=package_id, input_key=str(payload.get("input_key") or "").strip(),
        label=str(payload.get("label") or "").strip(), input_role=role, source_product=product,
        source_ref=source_ref, source_version=payload.get("source_version"), content_hash=digest,
        immutable=bool(payload.get("immutable", True)), provenance_json=dict(payload.get("provenance") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    if not row.input_key or not row.label:
        raise ValueError("input_key and label are required.")
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback(); raise ValueError("input_key must be unique within the package.") from exc
    db.refresh(row); return _ser(row)


def add_environment(db: Session, package_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _package(db, package_id)
    container_digest = payload.get("container_digest")
    if container_digest and not str(container_digest).startswith("sha256:"):
        raise ValueError("container_digest must use a sha256: prefix when supplied.")
    row = ReproducibleVisualKnowledgeEnvironmentRecord(
        package_id=package_id, environment_key=str(payload.get("environment_key") or "").strip(),
        name=str(payload.get("name") or "").strip(), runtime_versions_json=dict(payload.get("runtime_versions") or {}),
        dependencies_json=list(payload.get("dependencies") or []), container_ref=payload.get("container_ref"),
        container_digest=container_digest, code_ref=payload.get("code_ref"), random_seed=(None if payload.get("random_seed") is None else str(payload.get("random_seed"))),
        locale=payload.get("locale"), timezone=payload.get("timezone"), deterministic_claim=bool(payload.get("deterministic_claim", False)),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    if not row.environment_key or not row.name:
        raise ValueError("environment_key and name are required.")
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback(); raise ValueError("environment_key must be unique within the package.") from exc
    db.refresh(row); return _ser(row)


def add_replay_plan(db: Session, package_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _package(db, package_id)
    steps = list(payload.get("steps") or [])
    if not steps:
        raise ValueError("steps must contain at least one replay instruction.")
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise ValueError(f"replay step {index} must be an object.")
        target = str(step.get("target_product") or "").strip()
        if target not in SOURCE_PRODUCTS:
            raise ValueError(f"replay step {index} target_product must be one of {sorted(SOURCE_PRODUCTS)}")
        if step.get("execute_by_core") is True:
            raise ValueError("Replay plans cannot request Core-side specialist execution.")
        if not str(step.get("operation") or "").strip():
            raise ValueError(f"replay step {index} requires operation.")
    environment_id = payload.get("environment_id")
    if environment_id:
        env = db.get(ReproducibleVisualKnowledgeEnvironmentRecord, environment_id)
        if env is None or env.package_id != package_id:
            raise ValueError("environment_id must belong to this package.")
    row = ReproducibleVisualKnowledgeReplayPlanRecord(
        package_id=package_id, plan_key=str(payload.get("plan_key") or "").strip(),
        name=str(payload.get("name") or "").strip(), steps_json=steps,
        expected_outputs_json=list(payload.get("expected_outputs") or []), environment_id=environment_id,
        execution_policy="external-only", provenance_json=dict(payload.get("provenance") or {}),
    )
    if not row.plan_key or not row.name:
        raise ValueError("plan_key and name are required.")
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback(); raise ValueError("plan_key must be unique within the package.") from exc
    db.refresh(row); return _ser(row)


def bundle(db: Session, package_id: str, *, public_only: bool = False) -> dict[str, Any]:
    package = _package(db, package_id)
    if public_only and package.visibility != "public":
        raise HTTPException(status_code=404, detail="Reproducible visual knowledge package not found.")
    inputs = db.scalars(select(ReproducibleVisualKnowledgeInputRecord).where(ReproducibleVisualKnowledgeInputRecord.package_id == package_id).order_by(ReproducibleVisualKnowledgeInputRecord.created_at)).all()
    envs = db.scalars(select(ReproducibleVisualKnowledgeEnvironmentRecord).where(ReproducibleVisualKnowledgeEnvironmentRecord.package_id == package_id).order_by(ReproducibleVisualKnowledgeEnvironmentRecord.created_at)).all()
    plans = db.scalars(select(ReproducibleVisualKnowledgeReplayPlanRecord).where(ReproducibleVisualKnowledgeReplayPlanRecord.package_id == package_id).order_by(ReproducibleVisualKnowledgeReplayPlanRecord.created_at)).all()
    verifications = db.scalars(select(ReproducibleVisualKnowledgeVerificationRecord).where(ReproducibleVisualKnowledgeVerificationRecord.package_id == package_id).order_by(ReproducibleVisualKnowledgeVerificationRecord.created_at)).all()
    source = cpvr.bundle(db, package.source_object_id)
    return {
        "contract": "sc.reproducible-visual-knowledge.v1",
        "package": _ser(package), "source_visual_research_object": source,
        "inputs": [_ser(x) for x in inputs], "environments": [_ser(x) for x in envs],
        "replay_plans": [_ser(x) for x in plans], "verifications": [_ser(x) for x in verifications],
        "boundaries": _boundaries(),
    }


def manifest(db: Session, package_id: str) -> dict[str, Any]:
    state = bundle(db, package_id)
    canonical = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    fingerprint = hashlib.sha256(canonical).hexdigest()
    locked_inputs = all(bool(item["immutable"]) and bool(item["source_ref"]) for item in state["inputs"])
    hashed_inputs = all(bool(item["content_hash"]) for item in state["inputs"]) if state["inputs"] else False
    environments_documented = bool(state["environments"])
    replay_ready = bool(state["replay_plans"])
    return {
        "manifest_contract": "sc.reproducible-visual-knowledge-manifest.v1", "package_id": package_id,
        "fingerprint": fingerprint, "hash_algorithm": "sha256",
        "input_count": len(state["inputs"]), "environment_count": len(state["environments"]),
        "replay_plan_count": len(state["replay_plans"]), "locked_inputs": locked_inputs,
        "all_inputs_content_hashed": hashed_inputs, "environment_documented": environments_documented,
        "replay_ready": replay_ready, **_boundaries(),
    }


def validate_package(db: Session, package_id: str) -> dict[str, Any]:
    state = bundle(db, package_id); mf = manifest(db, package_id)
    input_keys = [x["input_key"] for x in state["inputs"]]
    plan_keys = [x["plan_key"] for x in state["replay_plans"]]
    environment_keys = [x["environment_key"] for x in state["environments"]]
    unique = len(input_keys) == len(set(input_keys)) and len(plan_keys) == len(set(plan_keys)) and len(environment_keys) == len(set(environment_keys))
    source_valid = cpvr.validate_object(db, state["package"]["source_object_id"])["valid"]
    valid = source_valid and unique and mf["input_count"] > 0 and mf["environment_documented"] and mf["replay_ready"]
    return {"valid": valid, "source_visual_research_valid": source_valid, "keys_unique": unique, **mf}


def record_verification(db: Session, package_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _package(db, package_id)
    kind = str(payload.get("verification_kind") or "integrity")
    if kind not in VERIFICATION_KINDS:
        raise ValueError(f"verification_kind must be one of {sorted(VERIFICATION_KINDS)}")
    current = manifest(db, package_id)["fingerprint"]
    expected = payload.get("expected_fingerprint")
    observed = payload.get("observed_fingerprint") or current
    verifier = str(payload.get("verifier_product") or "platform-core")
    external_run_ref = payload.get("external_run_ref")
    if kind in {"replay", "output", "external-certification"} and verifier == "platform-core":
        raise ValueError("Replay/output equivalence must be verified by an external specialist runtime or reviewer, not asserted by Core.")
    if kind in {"replay", "output", "external-certification"} and not external_run_ref:
        raise ValueError("External replay/output verification requires external_run_ref.")
    status = "match" if expected and observed == expected else ("integrity-recorded" if kind == "integrity" else str(payload.get("status") or "recorded"))
    row = ReproducibleVisualKnowledgeVerificationRecord(
        package_id=package_id, verification_kind=kind, status=status,
        expected_fingerprint=expected, observed_fingerprint=observed, verifier_product=verifier,
        external_run_ref=external_run_ref, assertions_json=list(payload.get("assertions") or []),
        evidence_json=dict(payload.get("evidence") or {}), created_by=str(payload.get("created_by") or "operator"),
    )
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def create_snapshot(db: Session, package_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    state = bundle(db, package_id); mf = manifest(db, package_id)
    canonical = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    revision = int(db.scalar(select(func.max(ReproducibleVisualKnowledgeSnapshotRecord.revision)).where(ReproducibleVisualKnowledgeSnapshotRecord.package_id == package_id)) or 0) + 1
    row = ReproducibleVisualKnowledgeSnapshotRecord(
        package_id=package_id, revision=revision, content_hash=digest, state_json=state,
        manifest_hash=mf["fingerprint"], provenance_json=dict(payload.get("provenance") or {}),
        created_by=str(payload.get("created_by") or "operator"),
    )
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def portable_package(db: Session, package_id: str) -> dict[str, Any]:
    state = bundle(db, package_id); mf = manifest(db, package_id); validation = validate_package(db, package_id)
    return {
        "package_contract": "sc.reproducible-visual-knowledge-package.v1", "package_id": package_id,
        "manifest": mf, "knowledge_bundle": state, "validation": validation,
        "portable": True, "reference_first": True, "execution_embedded": False,
        "required_consumer_behavior": {
            "preserve_product_identity": True, "preserve_provenance": True,
            "honor_input_versions_and_hashes": True, "resolve_replay_steps_in_declared_specialist_runtimes": True,
            "do_not_treat_reproduction_as_truth_promotion": True,
        },
    }
