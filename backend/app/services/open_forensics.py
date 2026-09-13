from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Entity, EvidenceRecord, SourceSnapshot,
    ForensicInvestigationRecord, ForensicObjectRecord, ForensicEvidenceItemRecord,
    ForensicEvidenceSourceBindingRecord, ForensicProvenanceActivityRecord,
    ForensicObjectRelationRecord, ForensicSnapshotRecord,
)

OBJECT_KINDS = {
    "artifact", "document", "media", "dataset", "device", "location", "event",
    "statement", "observation", "record", "measurement", "digital-object", "other",
}
EVIDENCE_KINDS = {
    "documentary", "digital", "media", "sensor", "measurement", "dataset",
    "observation", "record", "physical-reference", "derived-record", "other",
}
SOURCE_KINDS = {"core-source-snapshot", "core-evidence-record", "external", "product-reference"}
PROVENANCE_ACTIVITY_KINDS = {
    "observed", "acquired", "retrieved", "imported", "normalized", "extracted",
    "transformed", "derived", "annotated", "hash-recorded", "linked", "reviewed",
}
RELATION_KINDS = {
    "derived-from", "extracted-from", "depicts", "references", "same-source-as",
    "located-with", "temporally-related", "associated-with", "part-of", "version-of",
    "corresponds-to", "duplicates", "related-to",
}
FORBIDDEN_ACTIVITY_TERMS = {"custody", "transfer", "sealed", "seal", "unseal", "possession", "released-to", "received-by"}
FORBIDDEN_RELATION_KINDS = {"causes", "authored-by", "committed-by", "guilty-of", "responsible-for", "proves"}


def _ser(row):
    out = {}
    for c in row.__table__.columns:
        value = getattr(row, c.name)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        out[c.name] = value
    return out


def _dt(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip().replace("Z", "+00:00")
    result = datetime.fromisoformat(text)
    return result if result.tzinfo else result.replace(tzinfo=timezone.utc)


def _validate_hash(value: str | None, algorithm: str | None):
    if not value:
        return
    algo = (algorithm or "sha256").lower()
    if algo == "sha256":
        if len(value) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in value):
            raise ValueError("sha256 content_hash must contain exactly 64 hexadecimal characters.")


def _investigation(db: Session, investigation_id: str) -> ForensicInvestigationRecord:
    row = db.get(ForensicInvestigationRecord, investigation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Forensic investigation not found.")
    return row


def _object(db: Session, investigation_id: str, object_id: str) -> ForensicObjectRecord:
    row = db.get(ForensicObjectRecord, object_id)
    if row is None or row.investigation_id != investigation_id:
        raise ValueError("forensic object must belong to this investigation.")
    return row


def _evidence(db: Session, investigation_id: str, evidence_id: str) -> ForensicEvidenceItemRecord:
    row = db.get(ForensicEvidenceItemRecord, evidence_id)
    if row is None or row.investigation_id != investigation_id:
        raise ValueError("forensic evidence item must belong to this investigation.")
    return row


def _boundaries():
    return {
        "evidence_provenance_capture_by_core": True,
        "content_hash_recording_by_core": True,
        "evidence_ledger_binding_by_core": True,
        "source_snapshot_binding_by_core": True,
        "immutable_forensic_snapshots_by_core": True,
        "chain_of_custody_by_core": False,
        "custody_transfer_attestation_by_core": False,
        "authenticity_determination_by_core": False,
        "identity_attribution_by_core": False,
        "causal_conclusion_by_core": False,
        "legal_conclusion_by_core": False,
        "automatic_truth_promotion": False,
    }


def readiness(db: Session) -> dict[str, Any]:
    def count(model):
        return int(db.scalar(select(func.count()).select_from(model)) or 0)
    return {
        "migration_0046_applied": True,
        "forensic_contract": "sc.open-forensics.investigation.v1",
        "counts": {
            "investigations": count(ForensicInvestigationRecord),
            "objects": count(ForensicObjectRecord),
            "evidence_items": count(ForensicEvidenceItemRecord),
            "source_bindings": count(ForensicEvidenceSourceBindingRecord),
            "provenance_activities": count(ForensicProvenanceActivityRecord),
            "relations": count(ForensicObjectRelationRecord),
            "snapshots": count(ForensicSnapshotRecord),
        },
        **_boundaries(),
    }


def create_investigation(db: Session, payload: dict[str, Any]):
    project_id = str(payload.get("project_entity_id") or "").strip()
    project = db.get(Entity, project_id)
    if project is None or project.entity_type != "research-project":
        raise ValueError("project_entity_id must reference a research-project.")
    key = str(payload.get("investigation_key") or "").strip()
    name = str(payload.get("name") or "").strip()
    if not key or not name:
        raise ValueError("investigation_key and name are required.")
    row = ForensicInvestigationRecord(
        investigation_key=key,
        name=name,
        description=payload.get("description"),
        research_question=payload.get("research_question"),
        project_entity_id=project_id,
        status=str(payload.get("status") or "open"),
        visibility=str(payload.get("visibility") or "private"),
        scope_json=dict(payload.get("scope") or {}),
        provenance_json=dict(payload.get("provenance") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
        created_by=str(payload.get("created_by") or "operator"),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Investigation key already exists in this project.") from exc
    return _ser(row)


def list_investigations(db: Session, *, project_entity_id=None, public_only=False, limit=100, offset=0):
    q = select(ForensicInvestigationRecord)
    cq = select(func.count()).select_from(ForensicInvestigationRecord)
    filters = []
    if project_entity_id:
        filters.append(ForensicInvestigationRecord.project_entity_id == project_entity_id)
    if public_only:
        filters.append(ForensicInvestigationRecord.visibility == "public")
    for condition in filters:
        q = q.where(condition); cq = cq.where(condition)
    total = int(db.scalar(cq) or 0)
    rows = db.scalars(q.order_by(ForensicInvestigationRecord.created_at.desc()).limit(limit).offset(offset)).all()
    return [_ser(x) for x in rows], total


def add_object(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db, investigation_id)
    kind = str(payload.get("object_kind") or "artifact")
    if kind not in OBJECT_KINDS:
        raise ValueError("Unsupported object_kind.")
    bound_entity_id = payload.get("bound_entity_id")
    if bound_entity_id and db.get(Entity, bound_entity_id) is None:
        raise ValueError("bound_entity_id must reference an existing Core entity.")
    source_product = payload.get("source_product")
    source_ref = payload.get("source_ref")
    if source_product and source_product != "core" and not source_ref:
        raise ValueError("Non-Core forensic objects require an explicit source_ref.")
    row = ForensicObjectRecord(
        investigation_id=investigation_id,
        object_key=str(payload.get("object_key") or "").strip(),
        object_kind=kind,
        label=str(payload.get("label") or "").strip(),
        description=payload.get("description"), bound_entity_id=bound_entity_id,
        source_product=source_product, source_ref=source_ref,
        observed_context_json=dict(payload.get("observed_context") or {}),
        status=str(payload.get("status") or "observed"),
        provenance_json=dict(payload.get("provenance") or {}), metadata_json=dict(payload.get("metadata") or {}),
    )
    if not row.object_key or not row.label:
        raise ValueError("object_key and label are required.")
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Forensic object key already exists.") from exc
    return _ser(row)


def add_evidence(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db, investigation_id)
    object_id = payload.get("forensic_object_id")
    if object_id:
        _object(db, investigation_id, object_id)
    kind = str(payload.get("evidence_kind") or "record")
    if kind not in EVIDENCE_KINDS:
        raise ValueError("Unsupported evidence_kind.")
    snapshot_id = payload.get("source_snapshot_id")
    evidence_record_id = payload.get("evidence_record_id")
    if snapshot_id and db.get(SourceSnapshot, snapshot_id) is None:
        raise ValueError("source_snapshot_id must reference an existing Source Snapshot.")
    if evidence_record_id and db.get(EvidenceRecord, evidence_record_id) is None:
        raise ValueError("evidence_record_id must reference an existing Evidence Ledger record.")
    content_hash = payload.get("content_hash")
    algorithm = str(payload.get("hash_algorithm") or "sha256") if content_hash else None
    _validate_hash(content_hash, algorithm)
    row = ForensicEvidenceItemRecord(
        investigation_id=investigation_id, forensic_object_id=object_id,
        evidence_key=str(payload.get("evidence_key") or "").strip(), evidence_kind=kind,
        label=str(payload.get("label") or "").strip(), description=payload.get("description"),
        mime_type=payload.get("mime_type"), byte_size=payload.get("byte_size"),
        content_hash=content_hash, hash_algorithm=algorithm,
        source_snapshot_id=snapshot_id, evidence_record_id=evidence_record_id,
        integrity_state="hash-recorded" if content_hash else "unverified",
        provenance_json=dict(payload.get("provenance") or {}), metadata_json=dict(payload.get("metadata") or {}),
    )
    if not row.evidence_key or not row.label:
        raise ValueError("evidence_key and label are required.")
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Forensic evidence key already exists.") from exc
    return _ser(row)


def add_source_binding(db: Session, investigation_id: str, evidence_id: str, payload: dict[str, Any]):
    _evidence(db, investigation_id, evidence_id)
    kind = str(payload.get("source_kind") or "external")
    if kind not in SOURCE_KINDS:
        raise ValueError("Unsupported source_kind.")
    source_ref = str(payload.get("source_ref") or "").strip()
    if not source_ref:
        raise ValueError("source_ref is required.")
    snapshot_id = payload.get("source_snapshot_id")
    evidence_record_id = payload.get("evidence_record_id")
    if kind == "core-source-snapshot":
        snapshot_id = snapshot_id or source_ref
        if db.get(SourceSnapshot, snapshot_id) is None:
            raise ValueError("Core source snapshot binding must reference an existing Source Snapshot.")
    if kind == "core-evidence-record":
        evidence_record_id = evidence_record_id or source_ref
        if db.get(EvidenceRecord, evidence_record_id) is None:
            raise ValueError("Core evidence binding must reference an existing Evidence Ledger record.")
    if snapshot_id and db.get(SourceSnapshot, snapshot_id) is None:
        raise ValueError("source_snapshot_id must reference an existing Source Snapshot.")
    if evidence_record_id and db.get(EvidenceRecord, evidence_record_id) is None:
        raise ValueError("evidence_record_id must reference an existing Evidence Ledger record.")
    content_hash = payload.get("content_hash")
    algorithm = str(payload.get("hash_algorithm") or "sha256") if content_hash else None
    _validate_hash(content_hash, algorithm)
    row = ForensicEvidenceSourceBindingRecord(
        evidence_item_id=evidence_id, binding_key=str(payload.get("binding_key") or "").strip(),
        source_kind=kind, source_ref=source_ref, source_version=payload.get("source_version"), locator=payload.get("locator"),
        source_snapshot_id=snapshot_id, evidence_record_id=evidence_record_id,
        observed_at=_dt(payload.get("observed_at")), retrieved_at=_dt(payload.get("retrieved_at")),
        content_hash=content_hash, hash_algorithm=algorithm,
        provenance_json=dict(payload.get("provenance") or {}), metadata_json=dict(payload.get("metadata") or {}),
    )
    if not row.binding_key:
        raise ValueError("binding_key is required.")
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Source binding key already exists for this evidence item.") from exc
    return _ser(row)


def add_provenance_activity(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db, investigation_id)
    kind = str(payload.get("activity_kind") or "observed").strip().lower()
    if kind not in PROVENANCE_ACTIVITY_KINDS:
        if any(term in kind for term in FORBIDDEN_ACTIVITY_TERMS):
            raise ValueError("Custody, possession, sealing, and transfer events are reserved for the v2.43 chain-of-custody layer.")
        raise ValueError("Unsupported activity_kind.")
    evidence_id = payload.get("evidence_item_id")
    if evidence_id:
        _evidence(db, investigation_id, evidence_id)
    row = ForensicProvenanceActivityRecord(
        investigation_id=investigation_id, evidence_item_id=evidence_id, activity_kind=kind,
        description=payload.get("description"), actor_ref=payload.get("actor_ref"), tool_ref=payload.get("tool_ref"),
        occurred_at=_dt(payload.get("occurred_at")) or datetime.now(timezone.utc),
        inputs_json=list(payload.get("inputs") or []), outputs_json=list(payload.get("outputs") or []),
        provenance_json=dict(payload.get("provenance") or {}), metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_relation(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db, investigation_id)
    source = _object(db, investigation_id, str(payload.get("source_object_id") or ""))
    target = _object(db, investigation_id, str(payload.get("target_object_id") or ""))
    if source.id == target.id:
        raise ValueError("Self-relations are not permitted.")
    kind = str(payload.get("relation_kind") or "related-to").strip()
    if kind in FORBIDDEN_RELATION_KINDS or kind not in RELATION_KINDS:
        raise ValueError("Unsupported relation_kind; v2.42 does not infer authorship, responsibility, guilt, proof, or causation.")
    confidence = payload.get("confidence")
    if confidence is not None and not 0 <= float(confidence) <= 1:
        raise ValueError("confidence must be between 0 and 1.")
    row = ForensicObjectRelationRecord(
        investigation_id=investigation_id, relation_key=str(payload.get("relation_key") or "").strip(),
        source_object_id=source.id, target_object_id=target.id, relation_kind=kind,
        assertion_state=str(payload.get("assertion_state") or "observed"),
        confidence=float(confidence) if confidence is not None else None,
        basis_json=dict(payload.get("basis") or {}), provenance_json=dict(payload.get("provenance") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    if not row.relation_key:
        raise ValueError("relation_key is required.")
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Forensic relation key already exists.") from exc
    return _ser(row)


def bundle(db: Session, investigation_id: str, *, public_only=False):
    investigation = _investigation(db, investigation_id)
    if public_only and investigation.visibility != "public":
        raise HTTPException(status_code=404, detail="Forensic investigation not found.")
    objects = db.scalars(select(ForensicObjectRecord).where(ForensicObjectRecord.investigation_id == investigation_id).order_by(ForensicObjectRecord.created_at)).all()
    evidence = db.scalars(select(ForensicEvidenceItemRecord).where(ForensicEvidenceItemRecord.investigation_id == investigation_id).order_by(ForensicEvidenceItemRecord.created_at)).all()
    evidence_ids = [x.id for x in evidence]
    bindings = db.scalars(select(ForensicEvidenceSourceBindingRecord).where(ForensicEvidenceSourceBindingRecord.evidence_item_id.in_(evidence_ids)).order_by(ForensicEvidenceSourceBindingRecord.created_at)).all() if evidence_ids else []
    activities = db.scalars(select(ForensicProvenanceActivityRecord).where(ForensicProvenanceActivityRecord.investigation_id == investigation_id).order_by(ForensicProvenanceActivityRecord.occurred_at)).all()
    relations = db.scalars(select(ForensicObjectRelationRecord).where(ForensicObjectRelationRecord.investigation_id == investigation_id).order_by(ForensicObjectRelationRecord.created_at)).all()
    return {
        "contract": "sc.open-forensics.investigation.v1",
        "investigation": _ser(investigation),
        "objects": [_ser(x) for x in objects], "evidence_items": [_ser(x) for x in evidence],
        "source_bindings": [_ser(x) for x in bindings], "provenance_activities": [_ser(x) for x in activities],
        "relations": [_ser(x) for x in relations], "boundaries": _boundaries(),
    }


def provenance_graph(db: Session, investigation_id: str):
    state = bundle(db, investigation_id)
    nodes = []
    edges = []
    for obj in state["objects"]:
        nodes.append({"id": obj["id"], "kind": "forensic-object", "label": obj["label"], "object_kind": obj["object_kind"]})
    for item in state["evidence_items"]:
        nodes.append({"id": item["id"], "kind": "evidence-item", "label": item["label"], "evidence_kind": item["evidence_kind"], "content_hash": item["content_hash"]})
        if item["forensic_object_id"]:
            edges.append({"source": item["id"], "target": item["forensic_object_id"], "relation": "evidence-for"})
    for binding in state["source_bindings"]:
        source_id = f"source:{binding['id']}"
        nodes.append({"id": source_id, "kind": "source-binding", "label": binding["source_ref"], "source_kind": binding["source_kind"]})
        edges.append({"source": binding["evidence_item_id"], "target": source_id, "relation": "sourced-from"})
    for relation in state["relations"]:
        edges.append({"source": relation["source_object_id"], "target": relation["target_object_id"], "relation": relation["relation_kind"], "assertion_state": relation["assertion_state"]})
    return {"contract": "sc.open-forensics.provenance-graph.v1", "investigation_id": investigation_id, "nodes": nodes, "edges": edges, "boundaries": _boundaries()}


def create_snapshot(db: Session, investigation_id: str, payload: dict[str, Any]):
    state = bundle(db, investigation_id)
    canonical = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    revision = int(db.scalar(select(func.count()).select_from(ForensicSnapshotRecord).where(ForensicSnapshotRecord.investigation_id == investigation_id)) or 0) + 1
    row = ForensicSnapshotRecord(
        investigation_id=investigation_id, revision=revision, content_hash=digest, state_json=state,
        provenance_json=dict(payload.get("provenance") or {}), created_by=str(payload.get("created_by") or "operator"),
    )
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def portable_package(db: Session, investigation_id: str):
    state = bundle(db, investigation_id)
    canonical = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return {
        "contract": "sc.open-forensics.portable-investigation.v1",
        "release_boundary": "v2.42-object-model-and-evidence-provenance",
        "content_hash": hashlib.sha256(canonical).hexdigest(),
        "hash_algorithm": "sha256", "state": state,
        "not_chain_of_custody": True,
        "not_authenticity_determination": True,
        "not_legal_conclusion": True,
    }
