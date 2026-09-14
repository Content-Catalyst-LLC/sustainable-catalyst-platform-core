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
    ForensicCustodianRecord, ForensicCustodyEventRecord, ForensicEvidenceSealRecord,
    ForensicIntegrityCheckRecord, ForensicCustodyContinuityAssessmentRecord, ForensicCustodySnapshotRecord,
    ForensicClaimRecord, ForensicClaimEvidenceAssessmentRecord, ForensicContradictionRecord,
    ForensicHypothesisRecord, ForensicHypothesisEvidenceAssessmentRecord, ForensicHypothesisRelationRecord, ForensicReasoningSnapshotRecord,
    ForensicEventRecord, ForensicEventEvidenceBindingRecord, ForensicEventParticipantRecord, ForensicEventRelationRecord,
    ForensicEventReconstructionRecord, ForensicTimelineViewRecord, ForensicTimelineSnapshotRecord,
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
FORBIDDEN_ACTIVITY_TERMS = set()
FORBIDDEN_RELATION_KINDS = {"causes", "authored-by", "committed-by", "guilty-of", "responsible-for", "proves"}

CLAIM_KINDS = {"factual", "interpretive", "temporal", "quantitative", "identity", "attribution", "causal", "procedural", "other"}
CLAIM_EVIDENCE_STANCES = {"supports", "inconsistent", "qualifies", "neutral", "unknown"}
CONTRADICTION_KINDS = {"direct", "temporal", "quantitative", "source", "definition", "contextual", "other"}
HYPOTHESIS_EVIDENCE_CONSISTENCY = {"supports", "inconsistent", "neutral", "unknown"}
HYPOTHESIS_RELATION_KINDS = {"competes-with", "compatible-with", "subsumes", "distinct-from", "depends-on"}
FORBIDDEN_REASONING_FIELDS = {"truth_value", "truth", "verdict", "guilt", "responsibility", "probability", "posterior", "rank", "winner"}

EVENT_KINDS = {"event", "observation", "communication", "transaction", "movement", "measurement", "system-event", "decision", "publication", "incident", "other"}
TEMPORAL_BASES = {"observed", "asserted", "derived", "reconstructed", "unknown"}
TIME_PRECISIONS = {"exact", "second", "minute", "hour", "day", "month", "year", "bounded", "approximate", "unknown"}
EVENT_EVIDENCE_ROLES = {"supports-occurrence", "supports-time", "supports-location", "supports-participant", "contradicts", "qualifies", "context"}
EVENT_RELATION_KINDS = {"before", "after", "overlaps", "contains", "contained-by", "simultaneous", "possibly-before", "possibly-after", "related-to"}
FORBIDDEN_RECONSTRUCTION_FIELDS = {"truth_value", "truth", "verdict", "guilt", "responsibility", "probability", "posterior", "rank", "winner", "confirmed_sequence"}


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
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
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
        "chain_of_custody_by_core": True,
        "chain_of_custody_recording_by_core": True,
        "tamper_evident_custody_event_chain_by_core": True,
        "evidence_integrity_verification_by_core": True,
        "seal_state_recording_by_core": True,
        "custody_continuity_analysis_by_core": True,
        "external_custody_attestation_binding_by_core": True,
        "structured_claim_registry_by_core": True,
        "claim_evidence_position_mapping_by_core": True,
        "explicit_contradiction_registry_by_core": True,
        "competing_hypothesis_registry_by_core": True,
        "descriptive_hypothesis_comparison_matrix_by_core": True,
        "immutable_reasoning_snapshots_by_core": True,
        "forensic_event_registry_by_core": True,
        "bounded_temporal_assertion_capture_by_core": True,
        "event_evidence_binding_by_core": True,
        "explicit_event_relation_registry_by_core": True,
        "reconstruction_hypothesis_registry_by_core": True,
        "renderer_neutral_timeline_specification_by_core": True,
        "immutable_timeline_snapshots_by_core": True,
        "automatic_event_inference_by_core": False,
        "automatic_timestamp_inference_by_core": False,
        "automatic_sequence_truth_determination_by_core": False,
        "automatic_participant_identity_resolution_by_core": False,
        "automatic_contradiction_detection_by_core": False,
        "claim_truth_determination_by_core": False,
        "contradiction_resolution_by_core": False,
        "hypothesis_probability_assignment_by_core": False,
        "hypothesis_ranking_by_core": False,
        "verdict_generation_by_core": False,
        "custody_transfer_attestation_by_core": False,
        "physical_transfer_verification_by_core": False,
        "identity_verification_by_core": False,
        "legal_admissibility_determination_by_core": False,
        "ownership_determination_by_core": False,
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
        "migration_0047_applied": True,
        "migration_0048_applied": True,
        "migration_0049_applied": True,
        "forensic_contract": "sc.open-forensics.investigation.v1",
        "counts": {
            "investigations": count(ForensicInvestigationRecord),
            "objects": count(ForensicObjectRecord),
            "evidence_items": count(ForensicEvidenceItemRecord),
            "source_bindings": count(ForensicEvidenceSourceBindingRecord),
            "provenance_activities": count(ForensicProvenanceActivityRecord),
            "relations": count(ForensicObjectRelationRecord),
            "snapshots": count(ForensicSnapshotRecord),
            "custodians": count(ForensicCustodianRecord),
            "custody_events": count(ForensicCustodyEventRecord),
            "evidence_seals": count(ForensicEvidenceSealRecord),
            "integrity_checks": count(ForensicIntegrityCheckRecord),
            "custody_continuity_assessments": count(ForensicCustodyContinuityAssessmentRecord),
            "custody_snapshots": count(ForensicCustodySnapshotRecord),
            "claims": count(ForensicClaimRecord),
            "claim_evidence_assessments": count(ForensicClaimEvidenceAssessmentRecord),
            "contradictions": count(ForensicContradictionRecord),
            "hypotheses": count(ForensicHypothesisRecord),
            "hypothesis_evidence_assessments": count(ForensicHypothesisEvidenceAssessmentRecord),
            "hypothesis_relations": count(ForensicHypothesisRelationRecord),
            "reasoning_snapshots": count(ForensicReasoningSnapshotRecord),
            "events": count(ForensicEventRecord),
            "event_evidence_bindings": count(ForensicEventEvidenceBindingRecord),
            "event_participants": count(ForensicEventParticipantRecord),
            "event_relations": count(ForensicEventRelationRecord),
            "event_reconstructions": count(ForensicEventReconstructionRecord),
            "timeline_views": count(ForensicTimelineViewRecord),
            "timeline_snapshots": count(ForensicTimelineSnapshotRecord),
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
        raise ValueError("Unsupported provenance activity_kind; custody events must use the dedicated chain-of-custody API.")
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
        "release_boundary": "v2.43-evidence-integrity-and-chain-of-custody",
        "content_hash": hashlib.sha256(canonical).hexdigest(),
        "hash_algorithm": "sha256", "state": state,
        "custody": custody_bundle(db, investigation_id),
        "chain_of_custody_recorded": True,
        "not_chain_of_custody": False,
        "not_authenticity_determination": True,
        "not_legal_conclusion": True,
    }


CUSTODY_EVENT_KINDS = {"intake", "receipt", "transfer", "release", "storage-in", "storage-out", "inspection", "seal", "unseal", "integrity-check", "duplicate-created", "other"}


def _custodian(db: Session, investigation_id: str, custodian_id: str | None):
    if not custodian_id:
        return None
    row = db.get(ForensicCustodianRecord, custodian_id)
    if row is None or row.investigation_id != investigation_id:
        raise ValueError("custodian must belong to this investigation.")
    return row


def _custody_event_payload(*, investigation_id: str, evidence_item_id: str, sequence: int, event_kind: str,
                           from_custodian_id: str | None, to_custodian_id: str | None,
                           location_ref: str | None, occurred_at: datetime, previous_event_hash: str | None,
                           external_attestation_ref: str | None, notes: str | None,
                           provenance: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "investigation_id": investigation_id, "evidence_item_id": evidence_item_id, "sequence": sequence,
        "event_kind": event_kind, "from_custodian_id": from_custodian_id, "to_custodian_id": to_custodian_id,
        "location_ref": location_ref, "occurred_at": _dt(occurred_at).isoformat(), "previous_event_hash": previous_event_hash,
        "external_attestation_ref": external_attestation_ref, "notes": notes,
        "provenance": provenance, "metadata": metadata,
    }


def _event_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def add_custodian(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db, investigation_id)
    key=str(payload.get("custodian_key") or "").strip(); name=str(payload.get("display_name") or "").strip()
    if not key or not name: raise ValueError("custodian_key and display_name are required.")
    # Core may bind an external identity attestation but never upgrades identity state on its own.
    attestation=payload.get("external_identity_attestation_ref")
    state="externally-attested" if attestation else "unverified"
    row=ForensicCustodianRecord(
        investigation_id=investigation_id,custodian_key=key,display_name=name,actor_ref=payload.get("actor_ref"),
        organization_ref=payload.get("organization_ref"),role=payload.get("role"),identity_verification_state=state,
        external_identity_attestation_ref=attestation,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Custodian key already exists in this investigation.") from exc
    return _ser(row)


def record_custody_event(db: Session, investigation_id: str, evidence_id: str, payload: dict[str, Any]):
    _investigation(db, investigation_id); _evidence(db, investigation_id, evidence_id)
    kind=str(payload.get("event_kind") or "").strip().lower()
    if kind not in CUSTODY_EVENT_KINDS: raise ValueError("Unsupported custody event_kind.")
    from_id=payload.get("from_custodian_id"); to_id=payload.get("to_custodian_id")
    _custodian(db, investigation_id, from_id); _custodian(db, investigation_id, to_id)
    if kind == "transfer":
        if not from_id or not to_id or from_id == to_id: raise ValueError("transfer requires distinct from_custodian_id and to_custodian_id.")
    if kind in {"intake","receipt","storage-in"} and not to_id: raise ValueError(f"{kind} requires to_custodian_id.")
    if kind in {"release","storage-out"} and not from_id: raise ValueError(f"{kind} requires from_custodian_id.")
    last=db.scalar(select(ForensicCustodyEventRecord).where(ForensicCustodyEventRecord.evidence_item_id==evidence_id).order_by(ForensicCustodyEventRecord.sequence.desc()).limit(1))
    sequence=(last.sequence+1) if last else 1; prev=last.event_hash if last else None
    occurred=_dt(payload.get("occurred_at")) or datetime.now(timezone.utc)
    provenance=dict(payload.get("provenance") or {}); metadata=dict(payload.get("metadata") or {})
    event_payload=_custody_event_payload(investigation_id=investigation_id,evidence_item_id=evidence_id,sequence=sequence,event_kind=kind,from_custodian_id=from_id,to_custodian_id=to_id,location_ref=payload.get("location_ref"),occurred_at=occurred,previous_event_hash=prev,external_attestation_ref=payload.get("external_attestation_ref"),notes=payload.get("notes"),provenance=provenance,metadata=metadata)
    row=ForensicCustodyEventRecord(investigation_id=investigation_id,evidence_item_id=evidence_id,sequence=sequence,event_kind=kind,from_custodian_id=from_id,to_custodian_id=to_id,location_ref=payload.get("location_ref"),occurred_at=occurred,previous_event_hash=prev,event_hash=_event_hash(event_payload),external_attestation_ref=payload.get("external_attestation_ref"),notes=payload.get("notes"),provenance_json=provenance,metadata_json=metadata)
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def custody_chain(db: Session, investigation_id: str, evidence_id: str):
    _evidence(db, investigation_id, evidence_id)
    events=db.scalars(select(ForensicCustodyEventRecord).where(ForensicCustodyEventRecord.evidence_item_id==evidence_id).order_by(ForensicCustodyEventRecord.sequence)).all()
    findings=[]; prev_hash=None; expected_seq=1; current=None; hash_valid=True
    for e in events:
        if e.sequence != expected_seq: findings.append({"kind":"sequence-gap","expected":expected_seq,"observed":e.sequence})
        if e.previous_event_hash != prev_hash: findings.append({"kind":"previous-hash-mismatch","sequence":e.sequence}); hash_valid=False
        payload=_custody_event_payload(investigation_id=e.investigation_id,evidence_item_id=e.evidence_item_id,sequence=e.sequence,event_kind=e.event_kind,from_custodian_id=e.from_custodian_id,to_custodian_id=e.to_custodian_id,location_ref=e.location_ref,occurred_at=e.occurred_at,previous_event_hash=e.previous_event_hash,external_attestation_ref=e.external_attestation_ref,notes=e.notes,provenance=e.provenance_json or {},metadata=e.metadata_json or {})
        if _event_hash(payload) != e.event_hash: findings.append({"kind":"event-hash-mismatch","sequence":e.sequence}); hash_valid=False
        if e.event_kind == "transfer":
            if current is not None and e.from_custodian_id != current: findings.append({"kind":"custodian-discontinuity","sequence":e.sequence,"expected_from":current,"observed_from":e.from_custodian_id})
            current=e.to_custodian_id
        elif e.event_kind in {"intake","receipt","storage-in"}:
            if current is not None and e.to_custodian_id != current: findings.append({"kind":"overlapping-custody","sequence":e.sequence,"current":current,"received_by":e.to_custodian_id})
            current=e.to_custodian_id
        elif e.event_kind in {"release","storage-out"}:
            if current is not None and e.from_custodian_id != current: findings.append({"kind":"custodian-discontinuity","sequence":e.sequence,"expected_from":current,"observed_from":e.from_custodian_id})
            current=None
        prev_hash=e.event_hash; expected_seq=e.sequence+1
    gap_count=len([f for f in findings if f["kind"] in {"sequence-gap","previous-hash-mismatch","event-hash-mismatch","custodian-discontinuity","overlapping-custody"}])
    return {"contract":"sc.open-forensics.custody-chain.v1","investigation_id":investigation_id,"evidence_item_id":evidence_id,"events":[_ser(e) for e in events],"hash_chain_valid":hash_valid,"gap_count":gap_count,"continuity_status":"continuous" if events and gap_count==0 else ("no-events" if not events else "review-required"),"current_custodian_id":current,"findings":findings,"boundaries":_boundaries()}


def record_seal(db: Session, investigation_id: str, evidence_id: str, payload: dict[str, Any]):
    evidence=_evidence(db, investigation_id, evidence_id); action=str(payload.get("action") or "seal").lower(); identifier=str(payload.get("seal_identifier") or "").strip()
    if not identifier: raise ValueError("seal_identifier is required.")
    if action == "seal":
        custodian=payload.get("custodian_id"); _custodian(db,investigation_id,custodian)
        content_hash=payload.get("content_hash_at_seal") or evidence.content_hash; algorithm=str(payload.get("hash_algorithm") or evidence.hash_algorithm or "sha256") if content_hash else None; _validate_hash(content_hash,algorithm)
        row=ForensicEvidenceSealRecord(evidence_item_id=evidence_id,seal_identifier=identifier,status="sealed",sealed_by_custodian_id=custodian,sealed_at=_dt(payload.get("occurred_at")) or datetime.now(timezone.utc),content_hash_at_seal=content_hash,hash_algorithm=algorithm,external_attestation_ref=payload.get("external_attestation_ref"),reason=payload.get("reason"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
        db.add(row)
        try: db.commit(); db.refresh(row)
        except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Seal identifier already exists for this evidence item.") from exc
        return _ser(row)
    if action == "unseal":
        row=db.scalar(select(ForensicEvidenceSealRecord).where(ForensicEvidenceSealRecord.evidence_item_id==evidence_id,ForensicEvidenceSealRecord.seal_identifier==identifier))
        if row is None: raise ValueError("seal_identifier was not previously recorded for this evidence item.")
        if row.status != "sealed": raise ValueError("seal is not currently sealed.")
        custodian=payload.get("custodian_id"); _custodian(db,investigation_id,custodian); row.status="unsealed"; row.unsealed_by_custodian_id=custodian; row.unsealed_at=_dt(payload.get("occurred_at")) or datetime.now(timezone.utc); row.reason=payload.get("reason") or row.reason; row.external_attestation_ref=payload.get("external_attestation_ref") or row.external_attestation_ref; db.add(row); db.commit(); db.refresh(row); return _ser(row)
    raise ValueError("action must be seal or unseal.")


def record_integrity_check(db: Session, investigation_id: str, evidence_id: str, payload: dict[str, Any]):
    evidence=_evidence(db, investigation_id, evidence_id); key=str(payload.get("check_key") or "").strip()
    if not key: raise ValueError("check_key is required.")
    algo=str(payload.get("hash_algorithm") or evidence.hash_algorithm or "sha256"); expected=payload.get("expected_hash") or evidence.content_hash; observed=payload.get("observed_hash")
    _validate_hash(expected,algo); _validate_hash(observed,algo)
    status="indeterminate" if not expected or not observed else ("match" if expected.lower()==observed.lower() else "mismatch")
    row=ForensicIntegrityCheckRecord(evidence_item_id=evidence_id,check_key=key,check_kind=str(payload.get("check_kind") or "content-hash"),hash_algorithm=algo,expected_hash=expected,observed_hash=observed,status=status,checker_ref=payload.get("checker_ref"),tool_ref=payload.get("tool_ref"),checked_at=_dt(payload.get("checked_at")) or datetime.now(timezone.utc),external_attestation_ref=payload.get("external_attestation_ref"),evidence_json=dict(payload.get("evidence") or {}),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    evidence.integrity_state="verified-hash-match" if status=="match" else ("hash-mismatch" if status=="mismatch" else evidence.integrity_state)
    db.add(row); db.add(evidence)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Integrity check key already exists for this evidence item.") from exc
    return _ser(row)


def create_continuity_assessment(db: Session, investigation_id: str, evidence_id: str, payload: dict[str, Any]):
    chain=custody_chain(db,investigation_id,evidence_id); key=str(payload.get("assessment_key") or "").strip()
    if not key: raise ValueError("assessment_key is required.")
    status="continuous" if chain["continuity_status"]=="continuous" and chain["hash_chain_valid"] else ("no-events" if chain["continuity_status"]=="no-events" else "review-required")
    row=ForensicCustodyContinuityAssessmentRecord(evidence_item_id=evidence_id,assessment_key=key,status=status,event_count=len(chain["events"]),gap_count=chain["gap_count"],hash_chain_valid=chain["hash_chain_valid"],findings_json=chain["findings"],assessed_at=datetime.now(timezone.utc),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Continuity assessment key already exists for this evidence item.") from exc
    return _ser(row)


def custody_bundle(db: Session, investigation_id: str):
    _investigation(db, investigation_id)
    evidence=db.scalars(select(ForensicEvidenceItemRecord).where(ForensicEvidenceItemRecord.investigation_id==investigation_id).order_by(ForensicEvidenceItemRecord.created_at)).all(); eids=[e.id for e in evidence]
    custodians=db.scalars(select(ForensicCustodianRecord).where(ForensicCustodianRecord.investigation_id==investigation_id).order_by(ForensicCustodianRecord.created_at)).all()
    events=db.scalars(select(ForensicCustodyEventRecord).where(ForensicCustodyEventRecord.investigation_id==investigation_id).order_by(ForensicCustodyEventRecord.evidence_item_id,ForensicCustodyEventRecord.sequence)).all()
    seals=db.scalars(select(ForensicEvidenceSealRecord).where(ForensicEvidenceSealRecord.evidence_item_id.in_(eids)).order_by(ForensicEvidenceSealRecord.created_at)).all() if eids else []
    checks=db.scalars(select(ForensicIntegrityCheckRecord).where(ForensicIntegrityCheckRecord.evidence_item_id.in_(eids)).order_by(ForensicIntegrityCheckRecord.checked_at)).all() if eids else []
    assessments=db.scalars(select(ForensicCustodyContinuityAssessmentRecord).where(ForensicCustodyContinuityAssessmentRecord.evidence_item_id.in_(eids)).order_by(ForensicCustodyContinuityAssessmentRecord.assessed_at)).all() if eids else []
    return {"contract":"sc.open-forensics.custody-bundle.v1","investigation_id":investigation_id,"custodians":[_ser(x) for x in custodians],"custody_events":[_ser(x) for x in events],"evidence_seals":[_ser(x) for x in seals],"integrity_checks":[_ser(x) for x in checks],"continuity_assessments":[_ser(x) for x in assessments],"boundaries":_boundaries()}


def create_custody_snapshot(db: Session, investigation_id: str, payload: dict[str, Any]):
    state=custody_bundle(db,investigation_id); canonical=json.dumps(state,sort_keys=True,separators=(",",":"),default=str).encode("utf-8"); digest=hashlib.sha256(canonical).hexdigest()
    last=db.scalar(select(ForensicCustodySnapshotRecord).where(ForensicCustodySnapshotRecord.investigation_id==investigation_id).order_by(ForensicCustodySnapshotRecord.revision.desc()).limit(1)); revision=(last.revision+1) if last else 1
    row=ForensicCustodySnapshotRecord(investigation_id=investigation_id,revision=revision,content_hash=digest,previous_snapshot_hash=last.content_hash if last else None,state_json=state,provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)


# v2.44.0 — Claims, Contradictions & Competing Hypotheses

def _reject_forbidden_reasoning_fields(payload: dict[str, Any]):
    found = sorted(k for k in FORBIDDEN_REASONING_FIELDS if k in payload)
    if found:
        raise ValueError("Core does not accept verdict/ranking/probability fields in v2.44 reasoning records: " + ", ".join(found))


def _claim(db: Session, investigation_id: str, claim_id: str) -> ForensicClaimRecord:
    row = db.get(ForensicClaimRecord, claim_id)
    if row is None or row.investigation_id != investigation_id:
        raise ValueError("forensic claim must belong to this investigation.")
    return row


def _hypothesis(db: Session, investigation_id: str, hypothesis_id: str) -> ForensicHypothesisRecord:
    row = db.get(ForensicHypothesisRecord, hypothesis_id)
    if row is None or row.investigation_id != investigation_id:
        raise ValueError("forensic hypothesis must belong to this investigation.")
    return row


def _bounded_score(value, field):
    if value is None:
        return None
    score=float(value)
    if score < 0 or score > 1:
        raise ValueError(f"{field} must be between 0 and 1.")
    return score


def add_claim(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db, investigation_id); _reject_forbidden_reasoning_fields(payload)
    key=str(payload.get("claim_key") or "").strip(); statement=str(payload.get("statement") or "").strip(); kind=str(payload.get("claim_kind") or "factual").lower()
    if not key or not statement: raise ValueError("claim_key and statement are required.")
    if kind not in CLAIM_KINDS: raise ValueError("unsupported claim_kind.")
    confidence=_bounded_score(payload.get("asserted_confidence"),"asserted_confidence")
    row=ForensicClaimRecord(investigation_id=investigation_id,claim_key=key,claim_kind=kind,statement=statement,subject_ref=payload.get("subject_ref"),asserted_by_ref=payload.get("asserted_by_ref"),source_ref=payload.get("source_ref"),asserted_at=_dt(payload.get("asserted_at")),asserted_confidence=confidence,review_state=str(payload.get("review_state") or "unassessed"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Claim key already exists in this investigation.") from exc
    return _ser(row)


def assess_claim_evidence(db: Session, investigation_id: str, claim_id: str, payload: dict[str, Any]):
    _claim(db,investigation_id,claim_id); _reject_forbidden_reasoning_fields(payload)
    evidence_id=str(payload.get("evidence_item_id") or ""); _evidence(db,investigation_id,evidence_id)
    key=str(payload.get("assessment_key") or "").strip(); stance=str(payload.get("stance") or "").lower()
    if not key: raise ValueError("assessment_key is required.")
    if stance not in CLAIM_EVIDENCE_STANCES: raise ValueError("stance must be supports, inconsistent, qualifies, neutral, or unknown.")
    row=ForensicClaimEvidenceAssessmentRecord(claim_id=claim_id,evidence_item_id=evidence_id,assessment_key=key,stance=stance,diagnosticity=_bounded_score(payload.get("diagnosticity"),"diagnosticity"),rationale=payload.get("rationale"),reliability_note=payload.get("reliability_note"),analyst_ref=payload.get("analyst_ref"),external_assessment_ref=payload.get("external_assessment_ref"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Claim evidence assessment key already exists for this claim.") from exc
    return _ser(row)


def add_contradiction(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_forbidden_reasoning_fields(payload)
    key=str(payload.get("contradiction_key") or "").strip(); left=str(payload.get("left_claim_id") or ""); right=str(payload.get("right_claim_id") or ""); kind=str(payload.get("contradiction_kind") or "direct").lower()
    if not key: raise ValueError("contradiction_key is required.")
    if left == right: raise ValueError("a contradiction must reference two distinct claims.")
    _claim(db,investigation_id,left); _claim(db,investigation_id,right)
    if kind not in CONTRADICTION_KINDS: raise ValueError("unsupported contradiction_kind.")
    basis=[str(x) for x in (payload.get("basis_evidence_ids") or [])]
    for eid in basis: _evidence(db,investigation_id,eid)
    row=ForensicContradictionRecord(investigation_id=investigation_id,contradiction_key=key,left_claim_id=left,right_claim_id=right,contradiction_kind=kind,severity=str(payload.get("severity") or "unspecified"),status=str(payload.get("status") or "open"),rationale=payload.get("rationale"),basis_evidence_ids_json=basis,external_assessment_ref=payload.get("external_assessment_ref"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Contradiction key already exists in this investigation.") from exc
    return _ser(row)


def add_hypothesis(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_forbidden_reasoning_fields(payload)
    key=str(payload.get("hypothesis_key") or "").strip(); label=str(payload.get("label") or "").strip(); statement=str(payload.get("statement") or "").strip(); focal=payload.get("focal_claim_id")
    if not key or not label or not statement: raise ValueError("hypothesis_key, label, and statement are required.")
    if focal: _claim(db,investigation_id,str(focal))
    row=ForensicHypothesisRecord(investigation_id=investigation_id,hypothesis_key=key,label=label,statement=statement,focal_claim_id=str(focal) if focal else None,status=str(payload.get("status") or "active"),assumptions_json=list(payload.get("assumptions") or []),predicted_observations_json=list(payload.get("predicted_observations") or []),disconfirming_conditions_json=list(payload.get("disconfirming_conditions") or []),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Hypothesis key already exists in this investigation.") from exc
    return _ser(row)


def assess_hypothesis_evidence(db: Session, investigation_id: str, hypothesis_id: str, payload: dict[str, Any]):
    _hypothesis(db,investigation_id,hypothesis_id); _reject_forbidden_reasoning_fields(payload)
    evidence_id=str(payload.get("evidence_item_id") or ""); _evidence(db,investigation_id,evidence_id)
    key=str(payload.get("assessment_key") or "").strip(); consistency=str(payload.get("consistency") or "").lower()
    if not key: raise ValueError("assessment_key is required.")
    if consistency not in HYPOTHESIS_EVIDENCE_CONSISTENCY: raise ValueError("consistency must be supports, inconsistent, neutral, or unknown.")
    row=ForensicHypothesisEvidenceAssessmentRecord(hypothesis_id=hypothesis_id,evidence_item_id=evidence_id,assessment_key=key,consistency=consistency,diagnosticity=_bounded_score(payload.get("diagnosticity"),"diagnosticity"),rationale=payload.get("rationale"),reliability_note=payload.get("reliability_note"),analyst_ref=payload.get("analyst_ref"),external_assessment_ref=payload.get("external_assessment_ref"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Hypothesis evidence assessment key already exists for this hypothesis.") from exc
    return _ser(row)


def add_hypothesis_relation(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_forbidden_reasoning_fields(payload)
    key=str(payload.get("relation_key") or "").strip(); source=str(payload.get("source_hypothesis_id") or ""); target=str(payload.get("target_hypothesis_id") or ""); kind=str(payload.get("relation_kind") or "competes-with").lower()
    if not key: raise ValueError("relation_key is required.")
    if source == target: raise ValueError("hypothesis relation requires two distinct hypotheses.")
    _hypothesis(db,investigation_id,source); _hypothesis(db,investigation_id,target)
    if kind not in HYPOTHESIS_RELATION_KINDS: raise ValueError("unsupported hypothesis relation_kind.")
    row=ForensicHypothesisRelationRecord(investigation_id=investigation_id,relation_key=key,source_hypothesis_id=source,target_hypothesis_id=target,relation_kind=kind,rationale=payload.get("rationale"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Hypothesis relation key already exists in this investigation.") from exc
    return _ser(row)


def claim_map(db: Session, investigation_id: str):
    _investigation(db,investigation_id)
    claims=db.scalars(select(ForensicClaimRecord).where(ForensicClaimRecord.investigation_id==investigation_id).order_by(ForensicClaimRecord.created_at)).all(); ids=[x.id for x in claims]
    assessments=db.scalars(select(ForensicClaimEvidenceAssessmentRecord).where(ForensicClaimEvidenceAssessmentRecord.claim_id.in_(ids)).order_by(ForensicClaimEvidenceAssessmentRecord.created_at)).all() if ids else []
    contradictions=db.scalars(select(ForensicContradictionRecord).where(ForensicContradictionRecord.investigation_id==investigation_id).order_by(ForensicContradictionRecord.created_at)).all()
    return {"contract":"sc.open-forensics.claim-map.v1","investigation_id":investigation_id,"claims":[_ser(x) for x in claims],"evidence_assessments":[_ser(x) for x in assessments],"contradictions":[_ser(x) for x in contradictions],"automatic_contradiction_detection":False,"truth_determination":False,"boundaries":_boundaries()}


def hypothesis_matrix(db: Session, investigation_id: str):
    _investigation(db,investigation_id)
    hypotheses=db.scalars(select(ForensicHypothesisRecord).where(ForensicHypothesisRecord.investigation_id==investigation_id).order_by(ForensicHypothesisRecord.created_at)).all(); hids=[h.id for h in hypotheses]
    assessments=db.scalars(select(ForensicHypothesisEvidenceAssessmentRecord).where(ForensicHypothesisEvidenceAssessmentRecord.hypothesis_id.in_(hids)).order_by(ForensicHypothesisEvidenceAssessmentRecord.created_at)).all() if hids else []
    relations=db.scalars(select(ForensicHypothesisRelationRecord).where(ForensicHypothesisRelationRecord.investigation_id==investigation_id).order_by(ForensicHypothesisRelationRecord.created_at)).all()
    evidence_ids=sorted({a.evidence_item_id for a in assessments})
    by_pair={(a.evidence_item_id,a.hypothesis_id):a for a in assessments}
    rows=[]
    for eid in evidence_ids:
        rows.append({"evidence_item_id":eid,"cells":[{"hypothesis_id":h.id,"consistency":(by_pair[(eid,h.id)].consistency if (eid,h.id) in by_pair else "unassessed"),"diagnosticity":(by_pair[(eid,h.id)].diagnosticity if (eid,h.id) in by_pair else None),"assessment_id":(by_pair[(eid,h.id)].id if (eid,h.id) in by_pair else None)} for h in hypotheses]})
    summaries=[]
    for h in hypotheses:
        vals=[a for a in assessments if a.hypothesis_id==h.id]
        counts={k:len([a for a in vals if a.consistency==k]) for k in sorted(HYPOTHESIS_EVIDENCE_CONSISTENCY)}
        summaries.append({"hypothesis_id":h.id,"counts":counts,"assessed_evidence_count":len(vals)})
    return {"contract":"sc.open-forensics.competing-hypothesis-matrix.v1","investigation_id":investigation_id,"hypotheses":[_ser(x) for x in hypotheses],"rows":rows,"relations":[_ser(x) for x in relations],"summaries":summaries,"descriptive_only":True,"ranked":False,"probabilities_assigned":False,"verdict":None,"boundaries":_boundaries()}


def reasoning_bundle(db: Session, investigation_id: str):
    return {"contract":"sc.open-forensics.reasoning-bundle.v1","investigation_id":investigation_id,"claim_map":claim_map(db,investigation_id),"hypothesis_matrix":hypothesis_matrix(db,investigation_id),"boundaries":_boundaries()}


def create_reasoning_snapshot(db: Session, investigation_id: str, payload: dict[str, Any]):
    state=reasoning_bundle(db,investigation_id); canonical=json.dumps(state,sort_keys=True,separators=(",",":"),default=str).encode("utf-8"); digest=hashlib.sha256(canonical).hexdigest()
    last=db.scalar(select(ForensicReasoningSnapshotRecord).where(ForensicReasoningSnapshotRecord.investigation_id==investigation_id).order_by(ForensicReasoningSnapshotRecord.revision.desc()).limit(1)); revision=(last.revision+1) if last else 1
    row=ForensicReasoningSnapshotRecord(investigation_id=investigation_id,revision=revision,content_hash=digest,previous_snapshot_hash=last.content_hash if last else None,state_json=state,provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)

# v2.45.0 — Forensic Timeline & Event Reconstruction

def _event(db: Session, investigation_id: str, event_id: str) -> ForensicEventRecord:
    row=db.get(ForensicEventRecord,event_id)
    if row is None or row.investigation_id != investigation_id:
        raise ValueError("forensic event must belong to this investigation.")
    return row


def _reject_reconstruction_fields(payload: dict[str, Any]):
    present=sorted(k for k in FORBIDDEN_RECONSTRUCTION_FIELDS if k in payload)
    if present:
        raise ValueError("Core does not determine event-sequence truth, probabilities, rankings, verdicts, guilt, or responsibility: " + ", ".join(present))


def add_event(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_reconstruction_fields(payload)
    key=str(payload.get("event_key") or "").strip(); label=str(payload.get("label") or "").strip()
    kind=str(payload.get("event_kind") or "event").lower(); basis=str(payload.get("temporal_basis") or "asserted").lower(); precision=str(payload.get("time_precision") or "unknown").lower()
    if not key or not label: raise ValueError("event_key and label are required.")
    if kind not in EVENT_KINDS: raise ValueError("unsupported event_kind.")
    if basis not in TEMPORAL_BASES: raise ValueError("unsupported temporal_basis.")
    if precision not in TIME_PRECISIONS: raise ValueError("unsupported time_precision.")
    start,end,earliest,latest=(_dt(payload.get(k)) for k in ("start_time","end_time","earliest_time","latest_time"))
    if start and end and start>end: raise ValueError("start_time must not be after end_time.")
    if earliest and latest and earliest>latest: raise ValueError("earliest_time must not be after latest_time.")
    if start and earliest and start<earliest: raise ValueError("start_time cannot precede earliest_time.")
    if start and latest and start>latest: raise ValueError("start_time cannot follow latest_time.")
    row=ForensicEventRecord(investigation_id=investigation_id,event_key=key,label=label,description=payload.get("description"),event_kind=kind,temporal_basis=basis,time_precision=precision,start_time=start,end_time=end,earliest_time=earliest,latest_time=latest,location_ref=payload.get("location_ref"),status=str(payload.get("status") or "working"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Event key already exists in this investigation.") from exc
    return _ser(row)


def bind_event_evidence(db: Session, investigation_id: str, event_id: str, payload: dict[str, Any]):
    _event(db,investigation_id,event_id); _reject_reconstruction_fields(payload)
    evidence_id=str(payload.get("evidence_item_id") or ""); _evidence(db,investigation_id,evidence_id)
    key=str(payload.get("binding_key") or "").strip(); role=str(payload.get("role") or "context").lower()
    if not key: raise ValueError("binding_key is required.")
    if role not in EVENT_EVIDENCE_ROLES: raise ValueError("unsupported event evidence role.")
    row=ForensicEventEvidenceBindingRecord(event_id=event_id,evidence_item_id=evidence_id,binding_key=key,role=role,temporal_assertion_json=dict(payload.get("temporal_assertion") or {}),rationale=payload.get("rationale"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Event evidence binding key already exists for this event.") from exc
    return _ser(row)


def add_event_participant(db: Session, investigation_id: str, event_id: str, payload: dict[str, Any]):
    _event(db,investigation_id,event_id); _reject_reconstruction_fields(payload)
    key=str(payload.get("participant_key") or "").strip(); object_id=payload.get("forensic_object_id"); external_ref=payload.get("external_ref"); evidence_id=payload.get("basis_evidence_item_id")
    if not key: raise ValueError("participant_key is required.")
    if not object_id and not external_ref: raise ValueError("forensic_object_id or external_ref is required.")
    if object_id: _object(db,investigation_id,str(object_id))
    if evidence_id: _evidence(db,investigation_id,str(evidence_id))
    row=ForensicEventParticipantRecord(event_id=event_id,participant_key=key,forensic_object_id=str(object_id) if object_id else None,external_ref=str(external_ref) if external_ref else None,role=str(payload.get("role") or "associated"),basis_evidence_item_id=str(evidence_id) if evidence_id else None,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Participant key already exists for this event.") from exc
    return _ser(row)


def add_event_relation(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_reconstruction_fields(payload)
    key=str(payload.get("relation_key") or "").strip(); source=str(payload.get("source_event_id") or ""); target=str(payload.get("target_event_id") or ""); kind=str(payload.get("relation_kind") or "related-to").lower()
    if not key: raise ValueError("relation_key is required.")
    if source==target: raise ValueError("event relation requires two distinct events.")
    _event(db,investigation_id,source); _event(db,investigation_id,target)
    if kind not in EVENT_RELATION_KINDS: raise ValueError("unsupported event relation_kind.")
    evidence_ids=[str(x) for x in (payload.get("basis_evidence_ids") or [])]
    for eid in evidence_ids: _evidence(db,investigation_id,eid)
    row=ForensicEventRelationRecord(investigation_id=investigation_id,relation_key=key,source_event_id=source,target_event_id=target,relation_kind=kind,basis_evidence_ids_json=evidence_ids,rationale=payload.get("rationale"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Event relation key already exists in this investigation.") from exc
    return _ser(row)


def add_event_reconstruction(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_reconstruction_fields(payload)
    key=str(payload.get("reconstruction_key") or "").strip(); label=str(payload.get("label") or "").strip(); hypothesis_id=payload.get("hypothesis_id")
    if not key or not label: raise ValueError("reconstruction_key and label are required.")
    if hypothesis_id: _hypothesis(db,investigation_id,str(hypothesis_id))
    event_ids=[str(x) for x in (payload.get("ordered_event_ids") or [])]
    if len(event_ids)!=len(set(event_ids)): raise ValueError("ordered_event_ids cannot contain duplicates.")
    for eid in event_ids: _event(db,investigation_id,eid)
    relation_ids=[str(x) for x in (payload.get("event_relation_ids") or [])]
    for rid in relation_ids:
        r=db.get(ForensicEventRelationRecord,rid)
        if r is None or r.investigation_id!=investigation_id: raise ValueError("event_relation_ids must belong to this investigation.")
    row=ForensicEventReconstructionRecord(investigation_id=investigation_id,reconstruction_key=key,label=label,description=payload.get("description"),hypothesis_id=str(hypothesis_id) if hypothesis_id else None,ordered_event_ids_json=event_ids,event_relation_ids_json=relation_ids,assumptions_json=list(payload.get("assumptions") or []),unresolved_conflicts_json=list(payload.get("unresolved_conflicts") or []),status=str(payload.get("status") or "working"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Reconstruction key already exists in this investigation.") from exc
    return _ser(row)


def add_timeline_view(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_reconstruction_fields(payload)
    key=str(payload.get("view_key") or "").strip(); label=str(payload.get("label") or "").strip(); event_ids=[str(x) for x in (payload.get("event_ids") or [])]; reconstruction_ids=[str(x) for x in (payload.get("reconstruction_ids") or [])]
    if not key or not label: raise ValueError("view_key and label are required.")
    for eid in event_ids: _event(db,investigation_id,eid)
    for rid in reconstruction_ids:
        r=db.get(ForensicEventReconstructionRecord,rid)
        if r is None or r.investigation_id!=investigation_id: raise ValueError("reconstruction_ids must belong to this investigation.")
    row=ForensicTimelineViewRecord(investigation_id=investigation_id,view_key=key,label=label,event_ids_json=event_ids,reconstruction_ids_json=reconstruction_ids,filters_json=dict(payload.get("filters") or {}),display_json=dict(payload.get("display") or {}),provenance_json=dict(payload.get("provenance") or {})); db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Timeline view key already exists in this investigation.") from exc
    return _ser(row)


def timeline_bundle(db: Session, investigation_id: str):
    _investigation(db,investigation_id)
    events=db.scalars(select(ForensicEventRecord).where(ForensicEventRecord.investigation_id==investigation_id).order_by(ForensicEventRecord.start_time,ForensicEventRecord.created_at)).all(); event_ids=[e.id for e in events]
    bindings=db.scalars(select(ForensicEventEvidenceBindingRecord).where(ForensicEventEvidenceBindingRecord.event_id.in_(event_ids)).order_by(ForensicEventEvidenceBindingRecord.created_at)).all() if event_ids else []
    participants=db.scalars(select(ForensicEventParticipantRecord).where(ForensicEventParticipantRecord.event_id.in_(event_ids)).order_by(ForensicEventParticipantRecord.created_at)).all() if event_ids else []
    relations=db.scalars(select(ForensicEventRelationRecord).where(ForensicEventRelationRecord.investigation_id==investigation_id).order_by(ForensicEventRelationRecord.created_at)).all()
    reconstructions=db.scalars(select(ForensicEventReconstructionRecord).where(ForensicEventReconstructionRecord.investigation_id==investigation_id).order_by(ForensicEventReconstructionRecord.created_at)).all()
    views=db.scalars(select(ForensicTimelineViewRecord).where(ForensicTimelineViewRecord.investigation_id==investigation_id).order_by(ForensicTimelineViewRecord.created_at)).all()
    return {"contract":"sc.open-forensics.forensic-timeline.v1","investigation_id":investigation_id,"events":[_ser(x) for x in events],"evidence_bindings":[_ser(x) for x in bindings],"participants":[_ser(x) for x in participants],"relations":[_ser(x) for x in relations],"reconstructions":[_ser(x) for x in reconstructions],"views":[_ser(x) for x in views],"ordering_method":"explicit-timestamps-and-recorded-relations-not-sequence-truth","reconstructed_sequence_is_hypothesis":True,"boundaries":_boundaries()}


def timeline_specification(db: Session, investigation_id: str):
    state=timeline_bundle(db,investigation_id)
    return {"contract":"sc.visual-spec.forensic-timeline.v1","visual_kind":"forensic-timeline","renderer_neutral":True,"investigation_id":investigation_id,"events":state["events"],"relations":state["relations"],"reconstructions":state["reconstructions"],"views":state["views"],"execution":{"layout_by_core":False,"rendering_by_core":False,"automatic_event_inference":False,"automatic_sequence_truth_determination":False},"boundaries":_boundaries()}


def create_timeline_snapshot(db: Session, investigation_id: str, payload: dict[str, Any]):
    state=timeline_bundle(db,investigation_id); canonical=json.dumps(state,sort_keys=True,separators=(",",":"),default=str).encode("utf-8"); digest=hashlib.sha256(canonical).hexdigest()
    last=db.scalar(select(ForensicTimelineSnapshotRecord).where(ForensicTimelineSnapshotRecord.investigation_id==investigation_id).order_by(ForensicTimelineSnapshotRecord.revision.desc()).limit(1)); revision=(last.revision+1) if last else 1
    row=ForensicTimelineSnapshotRecord(investigation_id=investigation_id,revision=revision,content_hash=digest,previous_snapshot_hash=last.content_hash if last else None,state_json=state,provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)

