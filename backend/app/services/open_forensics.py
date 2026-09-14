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
    ForensicPlaceRecord, ForensicEvidenceSpatialBindingRecord, ForensicEventPlaceBindingRecord, ForensicSpatialUncertaintyEnvelopeRecord,
    ForensicTrajectoryEvidenceRecord, ForensicSpatialTemporalIntersectionRecord, ForensicSpatialTemporalViewRecord, ForensicSpatialTemporalSnapshotRecord,
    ForensicMediaArtifactRecord, ForensicMediaDerivativeRecord, ForensicMediaMetadataRecord, ForensicMediaFingerprintRecord,
    ForensicMediaSegmentRecord, ForensicMediaComparisonRecord, ForensicMediaProvenanceSnapshotRecord,
    ForensicQuantitativeReconstructionRecord, ForensicQuantitativeMeasurementRecord, ForensicQuantitativeAssumptionRecord,
    ForensicQuantitativeParameterRecord, ForensicQuantitativeScenarioRecord, ForensicQuantitativeHandoffRecord,
    ForensicQuantitativeResultBindingRecord, ForensicQuantitativeReproductionPackageRecord,
    ForensicStatementRecord, ForensicStatementSourceContextRecord, ForensicDocumentRecord, ForensicDocumentAssertionRecord,
    ForensicStatementClaimBindingRecord, ForensicStatementRelationRecord, ForensicTemporalConsistencyRecord, ForensicDocumentarySnapshotRecord,
    ForensicResearchGraphRecord, ForensicResearchGraphNodeRecord, ForensicResearchGraphEdgeRecord, ForensicResearchGraphViewRecord,
    ForensicResearchGraphHandoffRecord, ForensicResearchGraphSnapshotRecord, ForensicResearchGraphPackageRecord,
    ResearchModelRecord, ResearchResultRecord,
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

FORENSIC_GEOMETRY_TYPES = {"Point","MultiPoint","LineString","MultiLineString","Polygon","MultiPolygon","GeometryCollection"}
SPATIAL_BINDING_ROLES = {"supports-location","depicts-location","derived-location","context","contradicts-location","qualifies-location"}
EVENT_PLACE_ROLES = {"occurred-at","origin","destination","passed-through","near","associated","asserted-location"}
SPATIAL_SUBJECT_KINDS = {"event","evidence","place","trajectory","forensic-object"}
SPATIAL_TEMPORAL_RELATIONS = {"co-located","intersects-window","passes-through","near","overlaps-region","within-region","asserted"}
FORBIDDEN_SPATIAL_FIELDS = {"probability","posterior","rank","winner","verdict","confirmed_location","confirmed_path","truth_value"}

MEDIA_KINDS = {"image", "video", "audio", "multimedia", "document-media", "other"}
MEDIA_PROVENANCE_ROLES = {"original", "derivative", "reference", "unknown"}
MEDIA_TRANSFORMATION_KINDS = {"transcode", "crop", "resize", "frame-extract", "audio-extract", "normalize", "color-adjust", "metadata-copy", "metadata-strip", "re-encode", "container-remux", "trim", "concat", "composite", "annotate", "other"}
MEDIA_METADATA_NAMESPACES = {"exif", "xmp", "iptc", "quicktime", "id3", "container", "codec", "filesystem", "custom"}
MEDIA_FINGERPRINT_KINDS = {"cryptographic", "perceptual-image", "perceptual-audio", "frame-hash", "segment-hash", "external"}
MEDIA_SEGMENT_KINDS = {"frame", "time-range", "audio-range", "region", "page", "chapter", "other"}
MEDIA_COMPARISON_KINDS = {"exact-hash", "perceptual-similarity", "metadata-difference", "visual-difference", "audio-difference", "segment-alignment", "external-analysis", "other"}

QUANT_RECONSTRUCTION_KINDS = {"kinematic", "energetic", "statistical", "physical", "financial", "engineering", "environmental", "other"}
QUANT_RUNTIME_TARGETS = {"workbench", "lab", "external"}
QUANT_PARAMETER_ROLES = {"observed", "assumed", "calibrated", "derived-external", "declared"}
FORBIDDEN_QUANT_FIELDS = {"execute_by_core", "core_execute", "computed_by_core", "solved_by_core", "probability", "posterior", "rank", "winner", "verdict", "truth_value", "guilt", "responsibility"}

FORBIDDEN_MEDIA_DETERMINATION_FIELDS = {"authentic", "authenticity", "inauthentic", "fake", "deepfake", "manipulated", "manipulation_intent", "author", "author_identity", "creator_identity", "originality_determination", "probability", "posterior", "rank", "winner", "verdict", "truth_value", "guilt", "responsibility"}

STATEMENT_KINDS = {"testimony", "interview", "declaration", "statement", "communication", "transcript", "documentary-statement", "other"}
DOCUMENT_KINDS = {"report", "letter", "memo", "record", "filing", "publication", "transcript", "correspondence", "form", "document", "other"}
STATEMENT_CLAIM_BINDING_KINDS = {"reports", "supports", "inconsistent", "qualifies", "denies", "context", "unknown"}
STATEMENT_RELATION_KINDS = {"corroborates", "contradicts", "qualifies", "repeats", "derived-from", "same-source-as", "contextualizes", "related-to"}
TEMPORAL_CONSISTENCY_ASSESSMENTS = {"consistent", "inconsistent", "uncertain", "not-comparable", "unknown"}
DOCUMENTARY_SUBJECT_KINDS = {"statement", "document-assertion", "event", "claim"}
FORBIDDEN_DOCUMENTARY_FIELDS = {"credibility_score", "reliability_score", "truth_value", "truth", "verdict", "probability", "posterior", "rank", "winner", "verified_speaker", "verified_author", "authorship_determined", "speaker_identity_verified", "guilt", "responsibility"}

RESEARCH_GRAPH_NODE_KINDS = {"forensic-object", "evidence", "custodian", "custody-event", "claim", "contradiction", "hypothesis", "event", "place", "trajectory", "media-artifact", "quantitative-reconstruction", "statement", "document", "document-assertion", "research-model", "research-result", "core-entity", "person-reference", "organization-reference", "external-reference"}
RESEARCH_GRAPH_RELATION_KINDS = {"references", "supports", "inconsistent-with", "qualifies", "corroborates", "contradicts", "derived-from", "associated-with", "occurred-at", "located-at", "part-of", "version-of", "depicts", "contains", "relates-to", "custody-of", "evidence-for", "statement-of", "hypothesis-about", "analysis-of", "result-of", "temporal-relation", "spatial-relation", "same-source-as"}
RESEARCH_GRAPH_TARGET_PRODUCTS = {"research-librarian", "site-intelligence", "lab", "workbench", "decision-studio", "catalyst-data", "core", "external"}
FORBIDDEN_GRAPH_RELATIONS = {"causes", "proves", "authored-by", "same-person-as", "verified-identity-of", "authenticates", "guilty-of", "responsible-for"}
FORBIDDEN_GRAPH_DETERMINATION_FIELDS = {"truth_value", "truth", "verdict", "probability", "posterior", "rank", "winner", "identity_verified", "same_person_confirmed", "causation_confirmed", "proof_confirmed", "authenticity_confirmed", "guilt", "responsibility"}


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
        "forensic_place_registry_by_core": True,
        "evidence_spatial_binding_by_core": True,
        "event_place_binding_by_core": True,
        "spatial_uncertainty_envelopes_by_core": True,
        "trajectory_evidence_registry_by_core": True,
        "explicit_spatial_temporal_intersections_by_core": True,
        "linked_map_timeline_specification_by_core": True,
        "site_intelligence_handoffs_by_core": True,
        "immutable_spatial_temporal_snapshots_by_core": True,
        "media_artifact_registry_by_core": True,
        "declared_derivative_lineage_by_core": True,
        "media_metadata_preservation_by_core": True,
        "cryptographic_fingerprint_recording_by_core": True,
        "perceptual_fingerprint_recording_by_core": True,
        "frame_segment_reference_registry_by_core": True,
        "provenance_aware_media_comparisons_by_core": True,
        "immutable_media_provenance_snapshots_by_core": True,
        "quantitative_reconstruction_registry_by_core": True,
        "measurement_and_uncertainty_capture_by_core": True,
        "assumption_parameter_registry_by_core": True,
        "scenario_manifest_registry_by_core": True,
        "workbench_lab_handoff_contracts_by_core": True,
        "external_result_binding_by_core": True,
        "reproducible_quantitative_packages_by_core": True,
        "statement_testimony_registry_by_core": True,
        "documentary_evidence_registry_by_core": True,
        "speaker_author_reference_binding_by_core": True,
        "source_context_preservation_by_core": True,
        "statement_claim_binding_by_core": True,
        "explicit_corroboration_contradiction_relations_by_core": True,
        "temporal_consistency_recording_by_core": True,
        "immutable_documentary_snapshots_by_core": True,
        "forensic_research_graph_registry_by_core": True,
        "cross_forensics_node_binding_by_core": True,
        "explicit_graph_edge_registry_by_core": True,
        "renderer_neutral_forensic_graph_specification_by_core": True,
        "cross_product_graph_handoffs_by_core": True,
        "immutable_forensic_graph_snapshots_by_core": True,
        "portable_forensic_graph_packages_by_core": True,
        "automatic_graph_edge_inference_by_core": False,
        "automatic_entity_resolution_by_core": False,
        "automatic_identity_resolution_by_core": False,
        "automatic_causal_inference_by_core": False,
        "relationship_truth_determination_by_core": False,
        "graph_analytics_execution_by_core": False,
        "remote_product_fetch_by_core": False,
        "automatic_claim_extraction_by_core": False,
        "automatic_speaker_identity_resolution_by_core": False,
        "automatic_authorship_attribution_by_core": False,
        "automatic_corroboration_detection_by_core": False,
        "credibility_scoring_by_core": False,
        "quantitative_model_execution_by_core": False,
        "numerical_solution_by_core": False,
        "statistical_inference_execution_by_core": False,
        "uncertainty_propagation_execution_by_core": False,
        "sensitivity_execution_by_core": False,
        "parameter_optimization_by_core": False,
        "media_decoding_by_core": False,
        "perceptual_fingerprint_computation_by_core": False,
        "media_similarity_execution_by_core": False,
        "derivative_detection_by_core": False,
        "authenticity_determination_from_media_by_core": False,
        "manipulation_intent_determination_by_core": False,
        "media_authorship_attribution_by_core": False,
        "automatic_event_inference_by_core": False,
        "automatic_timestamp_inference_by_core": False,
        "automatic_sequence_truth_determination_by_core": False,
        "automatic_participant_identity_resolution_by_core": False,
        "crs_reprojection_by_core": False,
        "spatial_join_by_core": False,
        "routing_by_core": False,
        "remote_sensing_by_core": False,
        "trajectory_interpolation_execution_by_core": False,
        "automatic_location_truth_determination_by_core": False,
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
        "migration_0050_applied": True,
        "migration_0051_applied": True,
        "migration_0052_applied": True,
        "migration_0053_applied": True,
        "migration_0054_applied": True,
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
            "places": count(ForensicPlaceRecord),
            "evidence_spatial_bindings": count(ForensicEvidenceSpatialBindingRecord),
            "event_place_bindings": count(ForensicEventPlaceBindingRecord),
            "spatial_uncertainty_envelopes": count(ForensicSpatialUncertaintyEnvelopeRecord),
            "trajectory_evidence": count(ForensicTrajectoryEvidenceRecord),
            "spatial_temporal_intersections": count(ForensicSpatialTemporalIntersectionRecord),
            "spatial_temporal_views": count(ForensicSpatialTemporalViewRecord),
            "spatial_temporal_snapshots": count(ForensicSpatialTemporalSnapshotRecord),
            "media_artifacts": count(ForensicMediaArtifactRecord),
            "media_derivations": count(ForensicMediaDerivativeRecord),
            "media_metadata_records": count(ForensicMediaMetadataRecord),
            "media_fingerprints": count(ForensicMediaFingerprintRecord),
            "media_segments": count(ForensicMediaSegmentRecord),
            "media_comparisons": count(ForensicMediaComparisonRecord),
            "media_provenance_snapshots": count(ForensicMediaProvenanceSnapshotRecord),
            "quantitative_reconstructions": count(ForensicQuantitativeReconstructionRecord),
            "quantitative_measurements": count(ForensicQuantitativeMeasurementRecord),
            "quantitative_assumptions": count(ForensicQuantitativeAssumptionRecord),
            "quantitative_parameters": count(ForensicQuantitativeParameterRecord),
            "quantitative_scenarios": count(ForensicQuantitativeScenarioRecord),
            "quantitative_handoffs": count(ForensicQuantitativeHandoffRecord),
            "quantitative_result_bindings": count(ForensicQuantitativeResultBindingRecord),
            "quantitative_reproduction_packages": count(ForensicQuantitativeReproductionPackageRecord),
            "statements": count(ForensicStatementRecord),
            "statement_source_contexts": count(ForensicStatementSourceContextRecord),
            "documents": count(ForensicDocumentRecord),
            "document_assertions": count(ForensicDocumentAssertionRecord),
            "statement_claim_bindings": count(ForensicStatementClaimBindingRecord),
            "statement_relations": count(ForensicStatementRelationRecord),
            "temporal_consistency_assessments": count(ForensicTemporalConsistencyRecord),
            "documentary_snapshots": count(ForensicDocumentarySnapshotRecord),
            "research_graphs": count(ForensicResearchGraphRecord),
            "research_graph_nodes": count(ForensicResearchGraphNodeRecord),
            "research_graph_edges": count(ForensicResearchGraphEdgeRecord),
            "research_graph_views": count(ForensicResearchGraphViewRecord),
            "research_graph_handoffs": count(ForensicResearchGraphHandoffRecord),
            "research_graph_snapshots": count(ForensicResearchGraphSnapshotRecord),
            "research_graph_packages": count(ForensicResearchGraphPackageRecord),
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



# v2.46.0 — Forensic Spatial/Temporal Evidence Integration
def _forensic_geometry(value: Any, *, point_only: bool = False):
    if not isinstance(value, dict): raise ValueError("geometry must be a GeoJSON object.")
    typ=str(value.get("type") or "")
    if typ not in FORENSIC_GEOMETRY_TYPES: raise ValueError("Unsupported GeoJSON geometry type.")
    if point_only and typ != "Point": raise ValueError("Trajectory evidence points require GeoJSON Point geometry.")
    if typ == "GeometryCollection":
        if not isinstance(value.get("geometries"), list): raise ValueError("GeometryCollection requires geometries[].")
    elif "coordinates" not in value: raise ValueError("GeoJSON geometry requires coordinates.")
    return typ, dict(value)

def _reject_spatial_determination_fields(payload: dict[str, Any]):
    bad=sorted(FORBIDDEN_SPATIAL_FIELDS.intersection(payload))
    if bad: raise ValueError("Core records spatial evidence and uncertainty but does not determine location/path truth or probability: " + ", ".join(bad))

def _place(db: Session, investigation_id: str, place_id: str):
    row=db.get(ForensicPlaceRecord, place_id)
    if row is None or row.investigation_id != investigation_id: raise ValueError("place_id must belong to this investigation.")
    return row

def add_place(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_spatial_determination_fields(payload)
    key=str(payload.get("place_key") or "").strip(); label=str(payload.get("label") or "").strip()
    if not key or not label: raise ValueError("place_key and label are required.")
    typ,geom=_forensic_geometry(payload.get("geometry"))
    srid=int(payload.get("srid") or 4326)
    row=ForensicPlaceRecord(investigation_id=investigation_id,place_key=key,label=label,place_kind=str(payload.get("place_kind") or "location"),geometry_type=typ,geometry_json=geom,srid=srid,crs=str(payload.get("crs") or f"EPSG:{srid}"),site_intelligence_ref=payload.get("site_intelligence_ref"),spatial_feature_ref=payload.get("spatial_feature_ref"),properties_json=dict(payload.get("properties") or {}),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Place key already exists in this investigation.") from exc
    return _ser(row)

def bind_evidence_spatial(db: Session, investigation_id: str, evidence_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _evidence(db,investigation_id,evidence_id); _reject_spatial_determination_fields(payload)
    key=str(payload.get("binding_key") or "").strip(); role=str(payload.get("spatial_role") or "supports-location")
    if not key: raise ValueError("binding_key is required.")
    if role not in SPATIAL_BINDING_ROLES: raise ValueError("Unsupported spatial_role.")
    place_id=payload.get("place_id"); geom={}; typ=None
    if place_id: _place(db,investigation_id,str(place_id))
    if payload.get("geometry") is not None: typ,geom=_forensic_geometry(payload.get("geometry"))
    if not place_id and not geom and not payload.get("site_intelligence_ref"): raise ValueError("A place_id, geometry, or site_intelligence_ref is required.")
    row=ForensicEvidenceSpatialBindingRecord(investigation_id=investigation_id,binding_key=key,evidence_item_id=evidence_id,place_id=str(place_id) if place_id else None,geometry_type=typ,geometry_json=geom,spatial_role=role,site_intelligence_ref=payload.get("site_intelligence_ref"),rationale=payload.get("rationale"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def bind_event_place(db: Session, investigation_id: str, event_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _event(db,investigation_id,event_id); _reject_spatial_determination_fields(payload)
    place_id=str(payload.get("place_id") or ""); _place(db,investigation_id,place_id)
    key=str(payload.get("binding_key") or "").strip(); role=str(payload.get("role") or "occurred-at")
    if not key: raise ValueError("binding_key is required.")
    if role not in EVENT_PLACE_ROLES: raise ValueError("Unsupported event-place role.")
    evidence_ids=[str(x) for x in (payload.get("basis_evidence_ids") or [])]
    for eid in evidence_ids: _evidence(db,investigation_id,eid)
    row=ForensicEventPlaceBindingRecord(event_id=event_id,place_id=place_id,binding_key=key,role=role,temporal_alignment_json=dict(payload.get("temporal_alignment") or {}),basis_evidence_ids_json=evidence_ids,rationale=payload.get("rationale"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_spatial_uncertainty_envelope(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_spatial_determination_fields(payload)
    key=str(payload.get("envelope_key") or "").strip(); subject_kind=str(payload.get("subject_kind") or ""); subject_ref=str(payload.get("subject_ref") or "").strip()
    if not key or subject_kind not in SPATIAL_SUBJECT_KINDS or not subject_ref: raise ValueError("envelope_key, supported subject_kind, and subject_ref are required.")
    typ,geom=_forensic_geometry(payload.get("geometry")); evidence_ids=[str(x) for x in (payload.get("basis_evidence_ids") or [])]
    for eid in evidence_ids: _evidence(db,investigation_id,eid)
    srid=int(payload.get("srid") or 4326)
    row=ForensicSpatialUncertaintyEnvelopeRecord(investigation_id=investigation_id,envelope_key=key,subject_kind=subject_kind,subject_ref=subject_ref,uncertainty_kind=str(payload.get("uncertainty_kind") or "bounded-region"),geometry_type=typ,geometry_json=geom,srid=srid,crs=str(payload.get("crs") or f"EPSG:{srid}"),basis_evidence_ids_json=evidence_ids,coverage_label=payload.get("coverage_label"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_trajectory_evidence(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_spatial_determination_fields(payload)
    key=str(payload.get("trajectory_key") or "").strip(); label=str(payload.get("label") or "").strip(); subject_ref=str(payload.get("subject_ref") or "").strip()
    if not key or not label or not subject_ref: raise ValueError("trajectory_key, label, and subject_ref are required.")
    points=list(payload.get("ordered_points") or [])
    prev=None; normalized=[]
    for i,pt in enumerate(points):
        if not isinstance(pt,dict): raise ValueError("ordered_points must contain objects.")
        _,geom=_forensic_geometry(pt.get("geometry"),point_only=True); at=_dt(pt.get("observed_at"))
        if at is None: raise ValueError("Each trajectory point requires observed_at.")
        if prev is not None and at < prev: raise ValueError("Trajectory evidence points must be time ordered.")
        prev=at; normalized.append({"sequence":i,"observed_at":at.isoformat(),"geometry":geom,"uncertainty":dict(pt.get("uncertainty") or {})})
    evidence_ids=[str(x) for x in (payload.get("basis_evidence_ids") or [])]
    for eid in evidence_ids: _evidence(db,investigation_id,eid)
    row=ForensicTrajectoryEvidenceRecord(investigation_id=investigation_id,trajectory_key=key,label=label,subject_ref=subject_ref,trajectory_kind=str(payload.get("trajectory_kind") or "observed-path"),ordered_points_json=normalized,basis_evidence_ids_json=evidence_ids,site_intelligence_ref=payload.get("site_intelligence_ref"),interpolation=str(payload.get("interpolation") or "none"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_spatial_temporal_intersection(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_spatial_determination_fields(payload)
    key=str(payload.get("intersection_key") or "").strip(); event_id=str(payload.get("event_id") or ""); relation=str(payload.get("relation_kind") or "")
    if not key or relation not in SPATIAL_TEMPORAL_RELATIONS: raise ValueError("intersection_key and supported relation_kind are required.")
    _event(db,investigation_id,event_id)
    place_id=payload.get("place_id"); trajectory_id=payload.get("trajectory_id")
    if place_id: _place(db,investigation_id,str(place_id))
    if trajectory_id:
        t=db.get(ForensicTrajectoryEvidenceRecord,str(trajectory_id))
        if t is None or t.investigation_id!=investigation_id: raise ValueError("trajectory_id must belong to this investigation.")
    if not place_id and not trajectory_id: raise ValueError("place_id or trajectory_id is required.")
    evidence_ids=[str(x) for x in (payload.get("basis_evidence_ids") or [])]
    for eid in evidence_ids: _evidence(db,investigation_id,eid)
    row=ForensicSpatialTemporalIntersectionRecord(investigation_id=investigation_id,intersection_key=key,event_id=event_id,place_id=str(place_id) if place_id else None,trajectory_id=str(trajectory_id) if trajectory_id else None,relation_kind=relation,temporal_window_json=dict(payload.get("temporal_window") or {}),basis_evidence_ids_json=evidence_ids,rationale=payload.get("rationale"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_spatial_temporal_view(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_spatial_determination_fields(payload)
    key=str(payload.get("view_key") or "").strip(); label=str(payload.get("label") or "").strip()
    if not key or not label: raise ValueError("view_key and label are required.")
    row=ForensicSpatialTemporalViewRecord(investigation_id=investigation_id,view_key=key,label=label,event_ids_json=[str(x) for x in payload.get("event_ids") or []],place_ids_json=[str(x) for x in payload.get("place_ids") or []],trajectory_ids_json=[str(x) for x in payload.get("trajectory_ids") or []],reconstruction_ids_json=[str(x) for x in payload.get("reconstruction_ids") or []],filters_json=dict(payload.get("filters") or {}),display_json=dict(payload.get("display") or {}),provenance_json=dict(payload.get("provenance") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def spatial_temporal_evidence_bundle(db: Session, investigation_id: str):
    _investigation(db,investigation_id)
    places=db.scalars(select(ForensicPlaceRecord).where(ForensicPlaceRecord.investigation_id==investigation_id).order_by(ForensicPlaceRecord.created_at)).all()
    evidence_bindings=db.scalars(select(ForensicEvidenceSpatialBindingRecord).where(ForensicEvidenceSpatialBindingRecord.investigation_id==investigation_id).order_by(ForensicEvidenceSpatialBindingRecord.created_at)).all()
    event_ids=[e.id for e in db.scalars(select(ForensicEventRecord).where(ForensicEventRecord.investigation_id==investigation_id)).all()]
    event_places=db.scalars(select(ForensicEventPlaceBindingRecord).where(ForensicEventPlaceBindingRecord.event_id.in_(event_ids)).order_by(ForensicEventPlaceBindingRecord.created_at)).all() if event_ids else []
    envelopes=db.scalars(select(ForensicSpatialUncertaintyEnvelopeRecord).where(ForensicSpatialUncertaintyEnvelopeRecord.investigation_id==investigation_id).order_by(ForensicSpatialUncertaintyEnvelopeRecord.created_at)).all()
    trajectories=db.scalars(select(ForensicTrajectoryEvidenceRecord).where(ForensicTrajectoryEvidenceRecord.investigation_id==investigation_id).order_by(ForensicTrajectoryEvidenceRecord.created_at)).all()
    intersections=db.scalars(select(ForensicSpatialTemporalIntersectionRecord).where(ForensicSpatialTemporalIntersectionRecord.investigation_id==investigation_id).order_by(ForensicSpatialTemporalIntersectionRecord.created_at)).all()
    views=db.scalars(select(ForensicSpatialTemporalViewRecord).where(ForensicSpatialTemporalViewRecord.investigation_id==investigation_id).order_by(ForensicSpatialTemporalViewRecord.created_at)).all()
    return {"contract":"sc.open-forensics.spatial-temporal-evidence.v1","investigation_id":investigation_id,"places":[_ser(x) for x in places],"evidence_spatial_bindings":[_ser(x) for x in evidence_bindings],"event_place_bindings":[_ser(x) for x in event_places],"uncertainty_envelopes":[_ser(x) for x in envelopes],"trajectory_evidence":[_ser(x) for x in trajectories],"intersections":[_ser(x) for x in intersections],"views":[_ser(x) for x in views],"spatial_relations_are_explicit_assertions_not_computed_truth":True,"boundaries":_boundaries()}

def forensic_scene_specification(db: Session, investigation_id: str):
    state=spatial_temporal_evidence_bundle(db,investigation_id); timeline=timeline_bundle(db,investigation_id)
    return {"contract":"sc.visual-spec.forensic-spatial-temporal.v1","visual_kind":"forensic-linked-map-timeline","renderer_neutral":True,"investigation_id":investigation_id,"map":{"places":state["places"],"evidence_bindings":state["evidence_spatial_bindings"],"uncertainty_envelopes":state["uncertainty_envelopes"],"trajectories":state["trajectory_evidence"]},"timeline":{"events":timeline["events"],"relations":timeline["relations"],"reconstructions":timeline["reconstructions"]},"links":{"event_place_bindings":state["event_place_bindings"],"intersections":state["intersections"]},"views":state["views"],"execution":{"layout_by_core":False,"rendering_by_core":False,"spatial_join_by_core":False,"crs_reprojection_by_core":False,"routing_by_core":False,"remote_sensing_by_core":False,"trajectory_interpolation_execution_by_core":False},"boundaries":_boundaries()}

def site_intelligence_handoff(db: Session, investigation_id: str):
    state=spatial_temporal_evidence_bundle(db,investigation_id)
    refs=sorted({x.get("site_intelligence_ref") for x in state["places"]+state["evidence_spatial_bindings"]+state["trajectory_evidence"] if x.get("site_intelligence_ref")})
    return {"contract":"sc.handoff.open-forensics.site-intelligence.v1","target_product":"site-intelligence","investigation_id":investigation_id,"reference_first":True,"site_intelligence_refs":refs,"forensic_scene":forensic_scene_specification(db,investigation_id),"requested_capabilities":["map-rendering","spatial-analysis","crs-reprojection","trajectory-analysis","remote-sensing-when-explicitly-requested"],"execution_by_core":False,"automatic_truth_promotion":False}

def create_spatial_temporal_snapshot(db: Session, investigation_id: str, payload: dict[str, Any]):
    state=spatial_temporal_evidence_bundle(db,investigation_id); canonical=json.dumps(state,sort_keys=True,separators=(",",":"),default=str).encode("utf-8"); digest=hashlib.sha256(canonical).hexdigest()
    last=db.scalar(select(ForensicSpatialTemporalSnapshotRecord).where(ForensicSpatialTemporalSnapshotRecord.investigation_id==investigation_id).order_by(ForensicSpatialTemporalSnapshotRecord.revision.desc()).limit(1)); revision=(last.revision+1) if last else 1
    row=ForensicSpatialTemporalSnapshotRecord(investigation_id=investigation_id,revision=revision,content_hash=digest,previous_snapshot_hash=last.content_hash if last else None,state_json=state,provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)

# v2.47.0 — Media Artifact & Derivative Provenance

def _reject_media_determination_fields(payload: dict[str, Any]):
    bad=sorted(FORBIDDEN_MEDIA_DETERMINATION_FIELDS.intersection(payload))
    if bad:
        raise ValueError("Core records media provenance and externally supplied analysis but does not determine authenticity, manipulation intent, authorship, probability, or verdict: " + ", ".join(bad))


def _media_artifact(db: Session, investigation_id: str, artifact_id: str) -> ForensicMediaArtifactRecord:
    row=db.get(ForensicMediaArtifactRecord, artifact_id)
    if row is None or row.investigation_id != investigation_id:
        raise ValueError("media artifact must belong to this investigation.")
    return row


def _media_segment(db: Session, investigation_id: str, segment_id: str | None) -> ForensicMediaSegmentRecord | None:
    if not segment_id: return None
    row=db.get(ForensicMediaSegmentRecord, segment_id)
    if row is None:
        raise ValueError("media segment not found.")
    artifact=db.get(ForensicMediaArtifactRecord,row.artifact_id)
    if artifact is None or artifact.investigation_id != investigation_id:
        raise ValueError("media segment must belong to this investigation.")
    return row


def add_media_artifact(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_media_determination_fields(payload)
    key=str(payload.get("artifact_key") or "").strip(); label=str(payload.get("label") or "").strip(); kind=str(payload.get("media_kind") or "other").lower(); role=str(payload.get("provenance_role") or "unknown").lower()
    if not key or not label: raise ValueError("artifact_key and label are required.")
    if kind not in MEDIA_KINDS: raise ValueError("unsupported media_kind.")
    if role not in MEDIA_PROVENANCE_ROLES: raise ValueError("unsupported provenance_role.")
    evidence_id=payload.get("evidence_item_id"); object_id=payload.get("forensic_object_id"); source_ref=str(payload.get("source_ref") or "").strip() or None
    if evidence_id: _evidence(db,investigation_id,str(evidence_id))
    if object_id: _object(db,investigation_id,str(object_id))
    if not evidence_id and not object_id and not source_ref: raise ValueError("media artifact requires evidence_item_id, forensic_object_id, or source_ref.")
    content_hash=str(payload.get("content_hash") or "").strip() or None; algo=str(payload.get("hash_algorithm") or "sha256").lower() if content_hash else None; _validate_hash(content_hash,algo)
    row=ForensicMediaArtifactRecord(investigation_id=investigation_id,artifact_key=key,label=label,media_kind=kind,provenance_role=role,evidence_item_id=str(evidence_id) if evidence_id else None,forensic_object_id=str(object_id) if object_id else None,source_ref=source_ref,mime_type=payload.get("mime_type"),byte_size=payload.get("byte_size"),content_hash=content_hash,hash_algorithm=algo,duration_seconds=payload.get("duration_seconds"),width=payload.get("width"),height=payload.get("height"),frame_rate=payload.get("frame_rate"),sample_rate_hz=payload.get("sample_rate_hz"),channels=payload.get("channels"),description=payload.get("description"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_media_derivation(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_media_determination_fields(payload)
    key=str(payload.get("derivation_key") or "").strip(); kind=str(payload.get("transformation_kind") or "other").lower(); parent=str(payload.get("parent_artifact_id") or ""); child=str(payload.get("child_artifact_id") or "")
    if not key or not parent or not child: raise ValueError("derivation_key, parent_artifact_id, and child_artifact_id are required.")
    if parent==child: raise ValueError("parent and child media artifacts must differ.")
    _media_artifact(db,investigation_id,parent); _media_artifact(db,investigation_id,child)
    if kind not in MEDIA_TRANSFORMATION_KINDS: raise ValueError("unsupported transformation_kind.")
    row=ForensicMediaDerivativeRecord(investigation_id=investigation_id,derivation_key=key,parent_artifact_id=parent,child_artifact_id=child,transformation_kind=kind,tool_ref=payload.get("tool_ref"),tool_version=payload.get("tool_version"),parameters_json=dict(payload.get("parameters") or {}),transformation_notes=payload.get("transformation_notes"),source_ref=payload.get("source_ref"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_media_metadata(db: Session, investigation_id: str, artifact_id: str, payload: dict[str, Any]):
    _reject_media_determination_fields(payload); _media_artifact(db,investigation_id,artifact_id)
    key=str(payload.get("record_key") or "").strip(); namespace=str(payload.get("namespace") or "custom").lower()
    if not key: raise ValueError("record_key is required.")
    if namespace not in MEDIA_METADATA_NAMESPACES: raise ValueError("unsupported metadata namespace.")
    row=ForensicMediaMetadataRecord(artifact_id=artifact_id,record_key=key,namespace=namespace,metadata_json=dict(payload.get("metadata") or {}),extraction_method=str(payload.get("extraction_method") or "external"),extraction_tool_ref=payload.get("extraction_tool_ref"),source_ref=payload.get("source_ref"),observed_at=_dt(payload.get("observed_at")),preserved=bool(payload.get("preserved",True)),provenance_json=dict(payload.get("provenance") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_media_fingerprint(db: Session, investigation_id: str, artifact_id: str, payload: dict[str, Any]):
    _reject_media_determination_fields(payload); _media_artifact(db,investigation_id,artifact_id)
    key=str(payload.get("fingerprint_key") or "").strip(); kind=str(payload.get("fingerprint_kind") or "external").lower(); algorithm=str(payload.get("algorithm") or "").strip(); value=str(payload.get("fingerprint_value") or "").strip()
    if not key or not algorithm or not value: raise ValueError("fingerprint_key, algorithm, and fingerprint_value are required.")
    if kind not in MEDIA_FINGERPRINT_KINDS: raise ValueError("unsupported fingerprint_kind.")
    if kind=="cryptographic" and algorithm.lower()=="sha256": _validate_hash(value,"sha256")
    row=ForensicMediaFingerprintRecord(artifact_id=artifact_id,fingerprint_key=key,fingerprint_kind=kind,algorithm=algorithm,algorithm_version=payload.get("algorithm_version"),fingerprint_value=value,scope_json=dict(payload.get("scope") or {}),producer_ref=payload.get("producer_ref"),source_ref=payload.get("source_ref"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_media_segment(db: Session, investigation_id: str, artifact_id: str, payload: dict[str, Any]):
    _reject_media_determination_fields(payload); _media_artifact(db,investigation_id,artifact_id)
    key=str(payload.get("segment_key") or "").strip(); kind=str(payload.get("segment_kind") or "other").lower(); label=str(payload.get("label") or "").strip()
    if not key or not label: raise ValueError("segment_key and label are required.")
    if kind not in MEDIA_SEGMENT_KINDS: raise ValueError("unsupported segment_kind.")
    evidence_id=payload.get("evidence_item_id")
    if evidence_id: _evidence(db,investigation_id,str(evidence_id))
    start=payload.get("start_time_ms"); end=payload.get("end_time_ms"); frame=payload.get("frame_index"); fend=payload.get("frame_end_index")
    if start is not None and end is not None and int(end)<int(start): raise ValueError("end_time_ms must be >= start_time_ms.")
    if frame is not None and fend is not None and int(fend)<int(frame): raise ValueError("frame_end_index must be >= frame_index.")
    content_hash=str(payload.get("content_hash") or "").strip() or None; algo=str(payload.get("hash_algorithm") or "sha256").lower() if content_hash else None; _validate_hash(content_hash,algo)
    row=ForensicMediaSegmentRecord(artifact_id=artifact_id,segment_key=key,segment_kind=kind,label=label,locator_json=dict(payload.get("locator") or {}),start_time_ms=int(start) if start is not None else None,end_time_ms=int(end) if end is not None else None,frame_index=int(frame) if frame is not None else None,frame_end_index=int(fend) if fend is not None else None,region_json=dict(payload.get("region") or {}),evidence_item_id=str(evidence_id) if evidence_id else None,content_hash=content_hash,hash_algorithm=algo,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_media_comparison(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_media_determination_fields(payload)
    key=str(payload.get("comparison_key") or "").strip(); kind=str(payload.get("comparison_kind") or "other").lower(); left=str(payload.get("left_artifact_id") or ""); right=str(payload.get("right_artifact_id") or "")
    if not key or not left or not right: raise ValueError("comparison_key, left_artifact_id, and right_artifact_id are required.")
    if kind not in MEDIA_COMPARISON_KINDS: raise ValueError("unsupported comparison_kind.")
    _media_artifact(db,investigation_id,left); _media_artifact(db,investigation_id,right)
    ls=_media_segment(db,investigation_id,payload.get("left_segment_id")); rs=_media_segment(db,investigation_id,payload.get("right_segment_id"))
    if ls and ls.artifact_id!=left: raise ValueError("left_segment_id must belong to left_artifact_id.")
    if rs and rs.artifact_id!=right: raise ValueError("right_segment_id must belong to right_artifact_id.")
    evidence_ids=[str(x) for x in payload.get("basis_evidence_ids") or []]
    for eid in evidence_ids: _evidence(db,investigation_id,eid)
    row=ForensicMediaComparisonRecord(investigation_id=investigation_id,comparison_key=key,comparison_kind=kind,left_artifact_id=left,right_artifact_id=right,left_segment_id=ls.id if ls else None,right_segment_id=rs.id if rs else None,method_ref=payload.get("method_ref"),findings_json=dict(payload.get("findings") or {}),metrics_json=dict(payload.get("metrics") or {}),basis_evidence_ids_json=evidence_ids,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def media_provenance_bundle(db: Session, investigation_id: str):
    _investigation(db,investigation_id)
    artifacts=db.scalars(select(ForensicMediaArtifactRecord).where(ForensicMediaArtifactRecord.investigation_id==investigation_id).order_by(ForensicMediaArtifactRecord.created_at)).all()
    ids=[x.id for x in artifacts]
    derivations=db.scalars(select(ForensicMediaDerivativeRecord).where(ForensicMediaDerivativeRecord.investigation_id==investigation_id).order_by(ForensicMediaDerivativeRecord.created_at)).all()
    metadata=db.scalars(select(ForensicMediaMetadataRecord).where(ForensicMediaMetadataRecord.artifact_id.in_(ids)).order_by(ForensicMediaMetadataRecord.created_at)).all() if ids else []
    fingerprints=db.scalars(select(ForensicMediaFingerprintRecord).where(ForensicMediaFingerprintRecord.artifact_id.in_(ids)).order_by(ForensicMediaFingerprintRecord.created_at)).all() if ids else []
    segments=db.scalars(select(ForensicMediaSegmentRecord).where(ForensicMediaSegmentRecord.artifact_id.in_(ids)).order_by(ForensicMediaSegmentRecord.created_at)).all() if ids else []
    comparisons=db.scalars(select(ForensicMediaComparisonRecord).where(ForensicMediaComparisonRecord.investigation_id==investigation_id).order_by(ForensicMediaComparisonRecord.created_at)).all()
    return {"contract":"sc.open-forensics.media-provenance.v1","investigation_id":investigation_id,"artifacts":[_ser(x) for x in artifacts],"derivations":[_ser(x) for x in derivations],"metadata_records":[_ser(x) for x in metadata],"fingerprints":[_ser(x) for x in fingerprints],"segments":[_ser(x) for x in segments],"comparisons":[_ser(x) for x in comparisons],"derivative_relations_are_declared_provenance_not_automated_detection":True,"comparisons_are_recorded_observations_not_authenticity_verdicts":True,"boundaries":_boundaries()}


def media_lineage_graph(db: Session, investigation_id: str):
    state=media_provenance_bundle(db,investigation_id)
    return {"contract":"sc.open-forensics.media-lineage-graph.v1","investigation_id":investigation_id,"nodes":state["artifacts"],"edges":state["derivations"],"directed":True,"derivative_detection_by_core":False,"authenticity_determination_by_core":False}


def media_comparison_bundle(db: Session, investigation_id: str):
    state=media_provenance_bundle(db,investigation_id)
    return {"contract":"sc.open-forensics.media-comparison-bundle.v1","investigation_id":investigation_id,"comparisons":state["comparisons"],"segments":state["segments"],"fingerprints":state["fingerprints"],"descriptive_only":True,"media_similarity_execution_by_core":False,"authenticity_determination_from_media_by_core":False,"media_authorship_attribution_by_core":False}


def create_media_provenance_snapshot(db: Session, investigation_id: str, payload: dict[str, Any]):
    state=media_provenance_bundle(db,investigation_id); canonical=json.dumps(state,sort_keys=True,separators=(",",":"),default=str).encode("utf-8"); digest=hashlib.sha256(canonical).hexdigest()
    last=db.scalar(select(ForensicMediaProvenanceSnapshotRecord).where(ForensicMediaProvenanceSnapshotRecord.investigation_id==investigation_id).order_by(ForensicMediaProvenanceSnapshotRecord.revision.desc()).limit(1)); revision=(last.revision+1) if last else 1
    row=ForensicMediaProvenanceSnapshotRecord(investigation_id=investigation_id,revision=revision,content_hash=digest,previous_snapshot_hash=last.content_hash if last else None,state_json=state,provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)


# v2.48.0 — Quantitative Reconstruction & Reproduction Handoffs
def _reject_quant_fields(payload: dict[str, Any]):
    bad=sorted(FORBIDDEN_QUANT_FIELDS.intersection(payload))
    if bad:
        raise ValueError("Core records quantitative reconstruction inputs and external-runtime handoffs but does not execute models, assign probabilities, rank hypotheses, or produce verdicts: " + ", ".join(bad))


def _quant_reconstruction(db: Session, investigation_id: str, reconstruction_id: str) -> ForensicQuantitativeReconstructionRecord:
    row=db.get(ForensicQuantitativeReconstructionRecord,reconstruction_id)
    if row is None or row.investigation_id!=investigation_id: raise ValueError("quantitative reconstruction must belong to this investigation.")
    return row


def add_quantitative_reconstruction(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_quant_fields(payload)
    key=str(payload.get("reconstruction_key") or "").strip(); label=str(payload.get("label") or "").strip(); kind=str(payload.get("reconstruction_kind") or "other").lower(); runtime=str(payload.get("preferred_runtime") or "workbench").lower()
    if not key or not label: raise ValueError("reconstruction_key and label are required.")
    if kind not in QUANT_RECONSTRUCTION_KINDS: raise ValueError("unsupported reconstruction_kind.")
    if runtime not in QUANT_RUNTIME_TARGETS: raise ValueError("unsupported preferred_runtime.")
    evidence_ids=[str(x) for x in payload.get("basis_evidence_ids") or []]
    for eid in evidence_ids: _evidence(db,investigation_id,eid)
    row=ForensicQuantitativeReconstructionRecord(investigation_id=investigation_id,reconstruction_key=key,label=label,reconstruction_kind=kind,question=payload.get("question"),model_ref=payload.get("model_ref"),model_version_ref=payload.get("model_version_ref"),method_ref=payload.get("method_ref"),preferred_runtime=runtime,unit_system=payload.get("unit_system"),status=str(payload.get("status") or "draft"),basis_evidence_ids_json=evidence_ids,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_quantitative_measurement(db: Session, investigation_id: str, reconstruction_id: str, payload: dict[str, Any]):
    _reject_quant_fields(payload); _quant_reconstruction(db,investigation_id,reconstruction_id)
    key=str(payload.get("measurement_key") or "").strip(); label=str(payload.get("label") or "").strip(); value=payload.get("value")
    if not key or not label or not isinstance(value,dict): raise ValueError("measurement_key, label, and object-valued value are required.")
    eid=payload.get("evidence_item_id"); source_ref=str(payload.get("source_ref") or "").strip() or None
    if eid: _evidence(db,investigation_id,str(eid))
    if not eid and not source_ref: raise ValueError("measurement requires evidence_item_id or source_ref.")
    row=ForensicQuantitativeMeasurementRecord(reconstruction_id=reconstruction_id,measurement_key=key,label=label,value_json=value,unit=payload.get("unit"),uncertainty_json=dict(payload.get("uncertainty") or {}),evidence_item_id=str(eid) if eid else None,source_ref=source_ref,observed_at=_dt(payload.get("observed_at")),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_quantitative_assumption(db: Session, investigation_id: str, reconstruction_id: str, payload: dict[str, Any]):
    _reject_quant_fields(payload); _quant_reconstruction(db,investigation_id,reconstruction_id)
    key=str(payload.get("assumption_key") or "").strip(); statement=str(payload.get("statement") or "").strip()
    if not key or not statement: raise ValueError("assumption_key and statement are required.")
    evidence_ids=[str(x) for x in payload.get("basis_evidence_ids") or []]
    for eid in evidence_ids: _evidence(db,investigation_id,eid)
    row=ForensicQuantitativeAssumptionRecord(reconstruction_id=reconstruction_id,assumption_key=key,statement=statement,assumption_kind=str(payload.get("assumption_kind") or "model"),status=str(payload.get("status") or "declared"),basis_evidence_ids_json=evidence_ids,source_ref=payload.get("source_ref"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_quantitative_parameter(db: Session, investigation_id: str, reconstruction_id: str, payload: dict[str, Any]):
    _reject_quant_fields(payload); _quant_reconstruction(db,investigation_id,reconstruction_id)
    key=str(payload.get("parameter_key") or "").strip(); label=str(payload.get("label") or "").strip(); value=payload.get("value"); role=str(payload.get("parameter_role") or "declared").lower()
    if not key or not label or not isinstance(value,dict): raise ValueError("parameter_key, label, and object-valued value are required.")
    if role not in QUANT_PARAMETER_ROLES: raise ValueError("unsupported parameter_role.")
    eid=payload.get("evidence_item_id");
    if eid: _evidence(db,investigation_id,str(eid))
    row=ForensicQuantitativeParameterRecord(reconstruction_id=reconstruction_id,parameter_key=key,label=label,symbol=payload.get("symbol"),value_json=value,unit=payload.get("unit"),bounds_json=dict(payload.get("bounds") or {}),uncertainty_json=dict(payload.get("uncertainty") or {}),parameter_role=role,evidence_item_id=str(eid) if eid else None,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_quantitative_scenario(db: Session, investigation_id: str, reconstruction_id: str, payload: dict[str, Any]):
    _reject_quant_fields(payload); _quant_reconstruction(db,investigation_id,reconstruction_id)
    key=str(payload.get("scenario_key") or "").strip(); label=str(payload.get("label") or "").strip()
    if not key or not label: raise ValueError("scenario_key and label are required.")
    aids=[str(x) for x in payload.get("assumption_ids") or []]; mids=[str(x) for x in payload.get("measurement_ids") or []]
    for aid in aids:
        r=db.get(ForensicQuantitativeAssumptionRecord,aid);
        if r is None or r.reconstruction_id!=reconstruction_id: raise ValueError("assumption_ids must belong to this reconstruction.")
    for mid in mids:
        r=db.get(ForensicQuantitativeMeasurementRecord,mid);
        if r is None or r.reconstruction_id!=reconstruction_id: raise ValueError("measurement_ids must belong to this reconstruction.")
    row=ForensicQuantitativeScenarioRecord(reconstruction_id=reconstruction_id,scenario_key=key,label=label,parameter_overrides_json=dict(payload.get("parameter_overrides") or {}),assumption_ids_json=aids,measurement_ids_json=mids,requested_analyses_json=list(payload.get("requested_analyses") or []),uncertainty_plan_json=dict(payload.get("uncertainty_plan") or {}),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def quantitative_reconstruction_bundle(db: Session, investigation_id: str, reconstruction_id: str | None=None):
    _investigation(db,investigation_id)
    q=select(ForensicQuantitativeReconstructionRecord).where(ForensicQuantitativeReconstructionRecord.investigation_id==investigation_id)
    if reconstruction_id: q=q.where(ForensicQuantitativeReconstructionRecord.id==reconstruction_id)
    recon=db.scalars(q.order_by(ForensicQuantitativeReconstructionRecord.created_at)).all(); ids=[x.id for x in recon]
    def rows(model,col): return db.scalars(select(model).where(col.in_(ids)).order_by(model.created_at)).all() if ids else []
    measurements=rows(ForensicQuantitativeMeasurementRecord,ForensicQuantitativeMeasurementRecord.reconstruction_id); assumptions=rows(ForensicQuantitativeAssumptionRecord,ForensicQuantitativeAssumptionRecord.reconstruction_id); parameters=rows(ForensicQuantitativeParameterRecord,ForensicQuantitativeParameterRecord.reconstruction_id); scenarios=rows(ForensicQuantitativeScenarioRecord,ForensicQuantitativeScenarioRecord.reconstruction_id); handoffs=rows(ForensicQuantitativeHandoffRecord,ForensicQuantitativeHandoffRecord.reconstruction_id)
    hids=[x.id for x in handoffs]; results=db.scalars(select(ForensicQuantitativeResultBindingRecord).where(ForensicQuantitativeResultBindingRecord.handoff_id.in_(hids)).order_by(ForensicQuantitativeResultBindingRecord.created_at)).all() if hids else []
    packages=db.scalars(select(ForensicQuantitativeReproductionPackageRecord).where(ForensicQuantitativeReproductionPackageRecord.reconstruction_id.in_(ids)).order_by(ForensicQuantitativeReproductionPackageRecord.created_at)).all() if ids else []
    return {"contract":"sc.open-forensics.quantitative-reconstruction.v1","investigation_id":investigation_id,"reconstructions":[_ser(x) for x in recon],"measurements":[_ser(x) for x in measurements],"assumptions":[_ser(x) for x in assumptions],"parameters":[_ser(x) for x in parameters],"scenarios":[_ser(x) for x in scenarios],"handoffs":[_ser(x) for x in handoffs],"result_bindings":[_ser(x) for x in results],"reproduction_packages":[_ser(x) for x in packages],"execution_by_core":False,"boundaries":_boundaries()}


def create_quantitative_handoff(db: Session, investigation_id: str, reconstruction_id: str, payload: dict[str, Any]):
    _reject_quant_fields(payload); rec=_quant_reconstruction(db,investigation_id,reconstruction_id)
    key=str(payload.get("handoff_key") or "").strip(); target=str(payload.get("target_product") or rec.preferred_runtime).lower()
    if not key: raise ValueError("handoff_key is required.")
    if target not in QUANT_RUNTIME_TARGETS: raise ValueError("target_product must be workbench, lab, or external.")
    sid=payload.get("scenario_id")
    if sid:
        sr=db.get(ForensicQuantitativeScenarioRecord,str(sid));
        if sr is None or sr.reconstruction_id!=reconstruction_id: raise ValueError("scenario_id must belong to this reconstruction.")
    manifest=quantitative_reconstruction_bundle(db,investigation_id,reconstruction_id)
    row=ForensicQuantitativeHandoffRecord(investigation_id=investigation_id,reconstruction_id=reconstruction_id,scenario_id=str(sid) if sid else None,handoff_key=key,target_product=target,contract_version="sc.forensic-quantitative-handoff.v1",input_manifest_json=manifest,execution_request_json=dict(payload.get("execution_request") or {}),external_run_ref=payload.get("external_run_ref"),status=str(payload.get("status") or "prepared"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_quantitative_result_binding(db: Session, investigation_id: str, handoff_id: str, payload: dict[str, Any]):
    _reject_quant_fields(payload); handoff=db.get(ForensicQuantitativeHandoffRecord,handoff_id)
    if handoff is None or handoff.investigation_id!=investigation_id: raise ValueError("handoff must belong to this investigation.")
    key=str(payload.get("result_key") or "").strip(); kind=str(payload.get("result_kind") or "result"); ref=str(payload.get("external_result_ref") or "").strip()
    if not key or not ref: raise ValueError("result_key and external_result_ref are required.")
    eid=payload.get("evidence_item_id");
    if eid: _evidence(db,investigation_id,str(eid))
    content_hash=str(payload.get("content_hash") or "").strip() or None; algo=str(payload.get("hash_algorithm") or "sha256").lower() if content_hash else None; _validate_hash(content_hash,algo)
    row=ForensicQuantitativeResultBindingRecord(handoff_id=handoff_id,result_key=key,result_kind=kind,external_result_ref=ref,output_manifest_json=dict(payload.get("output_manifest") or {}),metrics_json=dict(payload.get("metrics") or {}),content_hash=content_hash,hash_algorithm=algo,evidence_item_id=str(eid) if eid else None,produced_at=_dt(payload.get("produced_at")),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def quantitative_handoff_contract(db: Session, investigation_id: str, reconstruction_id: str, target_product: str):
    rec=_quant_reconstruction(db,investigation_id,reconstruction_id); target=str(target_product).lower()
    if target not in QUANT_RUNTIME_TARGETS: raise ValueError("target_product must be workbench, lab, or external.")
    return {"contract":"sc.forensic-quantitative-handoff.v1","investigation_id":investigation_id,"reconstruction_id":reconstruction_id,"target_product":target,"input_manifest":quantitative_reconstruction_bundle(db,investigation_id,reconstruction_id),"model_ref":rec.model_ref,"model_version_ref":rec.model_version_ref,"execute_by_core":False,"specialist_runtime_required":True,"automatic_truth_promotion":False}


def create_quantitative_reproduction_package(db: Session, investigation_id: str, reconstruction_id: str, payload: dict[str, Any]):
    _reject_quant_fields(payload); _quant_reconstruction(db,investigation_id,reconstruction_id)
    key=str(payload.get("package_key") or "").strip()
    if not key: raise ValueError("package_key is required.")
    state=quantitative_reconstruction_bundle(db,investigation_id,reconstruction_id); state["reproduction_packages"]=[]; canonical=json.dumps(state,sort_keys=True,separators=(",",":"),default=str).encode("utf-8"); digest=hashlib.sha256(canonical).hexdigest()
    last=db.scalar(select(ForensicQuantitativeReproductionPackageRecord).where(ForensicQuantitativeReproductionPackageRecord.investigation_id==investigation_id,ForensicQuantitativeReproductionPackageRecord.package_key==key).order_by(ForensicQuantitativeReproductionPackageRecord.revision.desc()).limit(1)); revision=(last.revision+1) if last else 1
    manifest={"contract":"sc.open-forensics.quantitative-reproduction-package.v1","manifest_hash":digest,"state":state,"specialist_execution_required":True,"quantitative_model_execution_by_core":False}
    row=ForensicQuantitativeReproductionPackageRecord(investigation_id=investigation_id,reconstruction_id=reconstruction_id,package_key=key,revision=revision,manifest_hash=digest,manifest_json=manifest,provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)


# v2.49.0 — Testimony, Statements & Documentary Evidence
def _reject_documentary_fields(payload: dict[str, Any]):
    bad=sorted(FORBIDDEN_DOCUMENTARY_FIELDS.intersection(payload))
    if bad:
        raise ValueError("Core preserves testimony/documentary source context and explicit analyst bindings but does not verify identity, determine authorship, score credibility, assign probability, or produce verdicts: " + ", ".join(bad))


def _statement(db: Session, investigation_id: str, statement_id: str) -> ForensicStatementRecord:
    row=db.get(ForensicStatementRecord,statement_id)
    if row is None or row.investigation_id!=investigation_id: raise ValueError("statement must belong to this investigation.")
    return row


def _document(db: Session, investigation_id: str, document_id: str) -> ForensicDocumentRecord:
    row=db.get(ForensicDocumentRecord,document_id)
    if row is None or row.investigation_id!=investigation_id: raise ValueError("document must belong to this investigation.")
    return row


def add_statement(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_documentary_fields(payload)
    key=str(payload.get("statement_key") or "").strip(); label=str(payload.get("label") or "").strip(); text=str(payload.get("statement_text") or "").strip(); kind=str(payload.get("statement_kind") or "statement")
    if not key or not label or not text: raise ValueError("statement_key, label, and statement_text are required.")
    if kind not in STATEMENT_KINDS: raise ValueError("unsupported statement_kind.")
    eid=payload.get("evidence_item_id"); event_id=payload.get("event_id")
    if eid: _evidence(db,investigation_id,str(eid))
    if event_id:
        event=db.get(ForensicEventRecord,str(event_id));
        if event is None or event.investigation_id!=investigation_id: raise ValueError("event_id must belong to this investigation.")
    row=ForensicStatementRecord(investigation_id=investigation_id,statement_key=key,statement_kind=kind,label=label,statement_text=text,speaker_ref=payload.get("speaker_ref"),speaker_label=payload.get("speaker_label"),author_ref=payload.get("author_ref"),author_label=payload.get("author_label"),evidence_item_id=str(eid) if eid else None,event_id=str(event_id) if event_id else None,stated_at=_dt(payload.get("stated_at")),temporal_basis=str(payload.get("temporal_basis") or "asserted"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_statement_source_context(db: Session, investigation_id: str, statement_id: str, payload: dict[str, Any]):
    _reject_documentary_fields(payload); _statement(db,investigation_id,statement_id)
    locator=dict(payload.get("locator") or {})
    if not locator: raise ValueError("source context requires an explicit locator such as page, section, timestamp, paragraph, or record identifier.")
    eid=payload.get("evidence_item_id")
    if eid: _evidence(db,investigation_id,str(eid))
    _validate_hash(payload.get("content_hash"),payload.get("hash_algorithm"))
    row=ForensicStatementSourceContextRecord(statement_id=statement_id,evidence_item_id=str(eid) if eid else None,source_ref=payload.get("source_ref"),locator_json=locator,surrounding_context=payload.get("surrounding_context"),transcription_status=str(payload.get("transcription_status") or "as-recorded"),content_hash=payload.get("content_hash"),hash_algorithm=payload.get("hash_algorithm") or "sha256",provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_document(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_documentary_fields(payload)
    key=str(payload.get("document_key") or "").strip(); title=str(payload.get("title") or "").strip(); kind=str(payload.get("document_kind") or "document")
    if not key or not title: raise ValueError("document_key and title are required.")
    if kind not in DOCUMENT_KINDS: raise ValueError("unsupported document_kind.")
    eid=payload.get("evidence_item_id"); oid=payload.get("forensic_object_id")
    if eid: _evidence(db,investigation_id,str(eid))
    if oid:
        obj=db.get(ForensicObjectRecord,str(oid));
        if obj is None or obj.investigation_id!=investigation_id: raise ValueError("forensic_object_id must belong to this investigation.")
    _validate_hash(payload.get("content_hash"),payload.get("hash_algorithm"))
    row=ForensicDocumentRecord(investigation_id=investigation_id,document_key=key,document_kind=kind,title=title,evidence_item_id=str(eid) if eid else None,forensic_object_id=str(oid) if oid else None,author_ref=payload.get("author_ref"),author_label=payload.get("author_label"),issuer_ref=payload.get("issuer_ref"),issued_at=_dt(payload.get("issued_at")),source_ref=payload.get("source_ref"),source_context_json=dict(payload.get("source_context") or {}),content_hash=payload.get("content_hash"),hash_algorithm=payload.get("hash_algorithm") or "sha256",provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_document_assertion(db: Session, investigation_id: str, document_id: str, payload: dict[str, Any]):
    _reject_documentary_fields(payload); _document(db,investigation_id,document_id)
    key=str(payload.get("assertion_key") or "").strip(); text=str(payload.get("assertion_text") or "").strip(); locator=dict(payload.get("locator") or {})
    if not key or not text or not locator: raise ValueError("assertion_key, assertion_text, and explicit locator are required.")
    claim_id=payload.get("claim_id"); eid=payload.get("evidence_item_id")
    if claim_id:
        claim=db.get(ForensicClaimRecord,str(claim_id));
        if claim is None or claim.investigation_id!=investigation_id: raise ValueError("claim_id must belong to this investigation.")
    if eid: _evidence(db,investigation_id,str(eid))
    row=ForensicDocumentAssertionRecord(document_id=document_id,assertion_key=key,assertion_text=text,assertion_kind=str(payload.get("assertion_kind") or "documentary"),locator_json=locator,claim_id=str(claim_id) if claim_id else None,evidence_item_id=str(eid) if eid else None,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def bind_statement_claim(db: Session, investigation_id: str, statement_id: str, payload: dict[str, Any]):
    _reject_documentary_fields(payload); _statement(db,investigation_id,statement_id)
    claim_id=str(payload.get("claim_id") or ""); kind=str(payload.get("binding_kind") or "unknown")
    claim=db.get(ForensicClaimRecord,claim_id)
    if claim is None or claim.investigation_id!=investigation_id: raise ValueError("claim_id must belong to this investigation.")
    if kind not in STATEMENT_CLAIM_BINDING_KINDS: raise ValueError("unsupported binding_kind.")
    eid=payload.get("evidence_item_id");
    if eid: _evidence(db,investigation_id,str(eid))
    row=ForensicStatementClaimBindingRecord(statement_id=statement_id,claim_id=claim_id,binding_kind=kind,rationale=payload.get("rationale"),evidence_item_id=str(eid) if eid else None,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_statement_relation(db: Session, investigation_id: str, payload: dict[str, Any]):
    _reject_documentary_fields(payload); _investigation(db,investigation_id)
    source=str(payload.get("source_statement_id") or ""); target=str(payload.get("target_statement_id") or ""); kind=str(payload.get("relation_kind") or "")
    _statement(db,investigation_id,source); _statement(db,investigation_id,target)
    if source==target: raise ValueError("statement relation endpoints must be distinct.")
    if kind not in STATEMENT_RELATION_KINDS: raise ValueError("unsupported relation_kind.")
    row=ForensicStatementRelationRecord(source_statement_id=source,target_statement_id=target,relation_kind=kind,rationale=payload.get("rationale"),evidence_basis_ids_json=list(payload.get("evidence_basis_ids") or []),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_temporal_consistency_assessment(db: Session, investigation_id: str, payload: dict[str, Any]):
    _reject_documentary_fields(payload); _investigation(db,investigation_id)
    ak=str(payload.get("subject_a_kind") or ""); bk=str(payload.get("subject_b_kind") or ""); aid=str(payload.get("subject_a_id") or ""); bid=str(payload.get("subject_b_id") or ""); assessment=str(payload.get("assessment") or "unknown")
    if ak not in DOCUMENTARY_SUBJECT_KINDS or bk not in DOCUMENTARY_SUBJECT_KINDS: raise ValueError("unsupported temporal consistency subject kind.")
    if not aid or not bid: raise ValueError("subject_a_id and subject_b_id are required.")
    if assessment not in TEMPORAL_CONSISTENCY_ASSESSMENTS: raise ValueError("unsupported temporal consistency assessment.")
    row=ForensicTemporalConsistencyRecord(investigation_id=investigation_id,subject_a_kind=ak,subject_a_id=aid,subject_b_kind=bk,subject_b_id=bid,assessment=assessment,rationale=payload.get("rationale"),evidence_basis_ids_json=list(payload.get("evidence_basis_ids") or []),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def documentary_evidence_bundle(db: Session, investigation_id: str):
    _investigation(db,investigation_id)
    statements=db.scalars(select(ForensicStatementRecord).where(ForensicStatementRecord.investigation_id==investigation_id).order_by(ForensicStatementRecord.created_at,ForensicStatementRecord.id)).all()
    statement_ids=[x.id for x in statements]
    documents=db.scalars(select(ForensicDocumentRecord).where(ForensicDocumentRecord.investigation_id==investigation_id).order_by(ForensicDocumentRecord.created_at,ForensicDocumentRecord.id)).all(); document_ids=[x.id for x in documents]
    contexts=db.scalars(select(ForensicStatementSourceContextRecord).where(ForensicStatementSourceContextRecord.statement_id.in_(statement_ids))).all() if statement_ids else []
    assertions=db.scalars(select(ForensicDocumentAssertionRecord).where(ForensicDocumentAssertionRecord.document_id.in_(document_ids))).all() if document_ids else []
    bindings=db.scalars(select(ForensicStatementClaimBindingRecord).where(ForensicStatementClaimBindingRecord.statement_id.in_(statement_ids))).all() if statement_ids else []
    relations=db.scalars(select(ForensicStatementRelationRecord).where(ForensicStatementRelationRecord.source_statement_id.in_(statement_ids))).all() if statement_ids else []
    temporal=db.scalars(select(ForensicTemporalConsistencyRecord).where(ForensicTemporalConsistencyRecord.investigation_id==investigation_id)).all()
    snapshots=db.scalars(select(ForensicDocumentarySnapshotRecord).where(ForensicDocumentarySnapshotRecord.investigation_id==investigation_id).order_by(ForensicDocumentarySnapshotRecord.revision)).all()
    return {"contract":"sc.open-forensics.testimony-documentary-evidence.v1","investigation_id":investigation_id,"statements":[_ser(x) for x in statements],"source_contexts":[_ser(x) for x in contexts],"documents":[_ser(x) for x in documents],"document_assertions":[_ser(x) for x in assertions],"statement_claim_bindings":[_ser(x) for x in bindings],"statement_relations":[_ser(x) for x in relations],"temporal_consistency_assessments":[_ser(x) for x in temporal],"snapshots":[_ser(x) for x in snapshots],"descriptive_only":True,"credibility_scoring_by_core":False,"identity_verification_by_core":False,"automatic_authorship_attribution_by_core":False,"automatic_truth_promotion":False,"boundaries":_boundaries()}


def create_documentary_snapshot(db: Session, investigation_id: str, payload: dict[str, Any]):
    _reject_documentary_fields(payload); state=documentary_evidence_bundle(db,investigation_id); state["snapshots"]=[]
    canonical=json.dumps(state,sort_keys=True,separators=(",",":"),default=str).encode("utf-8"); digest=hashlib.sha256(canonical).hexdigest()
    last=db.scalar(select(ForensicDocumentarySnapshotRecord).where(ForensicDocumentarySnapshotRecord.investigation_id==investigation_id).order_by(ForensicDocumentarySnapshotRecord.revision.desc()).limit(1)); revision=(last.revision+1) if last else 1
    row=ForensicDocumentarySnapshotRecord(investigation_id=investigation_id,revision=revision,content_hash=digest,previous_snapshot_hash=last.content_hash if last else None,state_json=state,provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)


# v2.50.0 — Forensic Research Graph
def _reject_graph_determination_fields(payload: dict[str, Any]):
    bad=sorted(FORBIDDEN_GRAPH_DETERMINATION_FIELDS.intersection(payload))
    if bad:
        raise ValueError("Core records explicit cross-forensics graph structure but does not determine identity, causation, proof, authenticity, probability, ranking, verdict, guilt, or responsibility: " + ", ".join(bad))


def _research_graph(db: Session, investigation_id: str, graph_id: str) -> ForensicResearchGraphRecord:
    row=db.get(ForensicResearchGraphRecord,graph_id)
    if row is None or row.investigation_id!=investigation_id: raise ValueError("research graph must belong to this investigation.")
    return row


def _research_graph_node(db: Session, graph_id: str, node_id: str) -> ForensicResearchGraphNodeRecord:
    row=db.get(ForensicResearchGraphNodeRecord,node_id)
    if row is None or row.graph_id!=graph_id: raise ValueError("graph node must belong to this graph.")
    return row


def _graph_internal_record(db: Session, investigation_id: str, kind: str, record_id: str):
    mapping={
        "forensic-object": ForensicObjectRecord, "evidence": ForensicEvidenceItemRecord, "custodian": ForensicCustodianRecord,
        "custody-event": ForensicCustodyEventRecord, "claim": ForensicClaimRecord, "contradiction": ForensicContradictionRecord,
        "hypothesis": ForensicHypothesisRecord, "event": ForensicEventRecord, "place": ForensicPlaceRecord,
        "trajectory": ForensicTrajectoryEvidenceRecord, "media-artifact": ForensicMediaArtifactRecord,
        "quantitative-reconstruction": ForensicQuantitativeReconstructionRecord, "statement": ForensicStatementRecord,
        "document": ForensicDocumentRecord, "document-assertion": ForensicDocumentAssertionRecord,
    }
    if kind in mapping:
        row=db.get(mapping[kind],record_id)
        if row is None: raise ValueError(f"record_id does not reference an existing {kind} record.")
        if kind=="document-assertion":
            doc=db.get(ForensicDocumentRecord,row.document_id)
            if doc is None or doc.investigation_id!=investigation_id: raise ValueError("document assertion must belong to this investigation.")
        elif kind=="custody-event":
            evidence=db.get(ForensicEvidenceItemRecord,row.evidence_item_id)
            if evidence is None or evidence.investigation_id!=investigation_id: raise ValueError("custody event must belong to this investigation.")
        elif getattr(row,"investigation_id",investigation_id)!=investigation_id:
            raise ValueError(f"{kind} must belong to this investigation.")
        return row
    if kind=="research-model":
        row=db.get(ResearchModelRecord,record_id)
        if row is None: raise ValueError("record_id does not reference an existing research model.")
        return row
    if kind=="research-result":
        row=db.get(ResearchResultRecord,record_id)
        if row is None: raise ValueError("record_id does not reference an existing research result.")
        return row
    return None


def create_research_graph(db: Session, investigation_id: str, payload: dict[str, Any]):
    _investigation(db,investigation_id); _reject_graph_determination_fields(payload)
    key=str(payload.get("graph_key") or "").strip(); label=str(payload.get("label") or "").strip()
    if not key or not label: raise ValueError("graph_key and label are required.")
    row=ForensicResearchGraphRecord(investigation_id=investigation_id,graph_key=key,label=label,description=payload.get("description"),status=str(payload.get("status") or "working"),visibility=str(payload.get("visibility") or "private"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}),created_by=str(payload.get("created_by") or "operator"))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail="Research graph key already exists in this investigation.") from exc
    return _ser(row)


def add_research_graph_node(db: Session, investigation_id: str, graph_id: str, payload: dict[str, Any]):
    _research_graph(db,investigation_id,graph_id); _reject_graph_determination_fields(payload)
    key=str(payload.get("node_key") or "").strip(); kind=str(payload.get("node_kind") or "").strip(); label=str(payload.get("label") or "").strip()
    if not key or not kind or not label: raise ValueError("node_key, node_kind, and label are required.")
    if kind not in RESEARCH_GRAPH_NODE_KINDS: raise ValueError("unsupported node_kind.")
    record_id=str(payload.get("record_id") or "").strip() or None; core_entity_id=str(payload.get("core_entity_id") or "").strip() or None; source_ref=str(payload.get("source_ref") or "").strip() or None
    internal_kinds=RESEARCH_GRAPH_NODE_KINDS-{"core-entity","person-reference","organization-reference","external-reference"}
    if kind in internal_kinds:
        if not record_id: raise ValueError("record_id is required for internal graph node kinds.")
        _graph_internal_record(db,investigation_id,kind,record_id)
    elif kind=="core-entity":
        if not core_entity_id or db.get(Entity,core_entity_id) is None: raise ValueError("core-entity nodes require an existing core_entity_id.")
    elif not source_ref:
        raise ValueError("reference nodes require an explicit source_ref.")
    evidence_ids=[str(x) for x in (payload.get("evidence_basis_ids") or [])]
    for eid in evidence_ids: _evidence(db,investigation_id,eid)
    row=ForensicResearchGraphNodeRecord(graph_id=graph_id,node_key=key,node_kind=kind,label=label,record_id=record_id,core_entity_id=core_entity_id,source_product=payload.get("source_product"),source_ref=source_ref,assertion_state=str(payload.get("assertion_state") or "referenced"),evidence_basis_ids_json=evidence_ids,properties_json=dict(payload.get("properties") or {}),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_research_graph_edge(db: Session, investigation_id: str, graph_id: str, payload: dict[str, Any]):
    _research_graph(db,investigation_id,graph_id); _reject_graph_determination_fields(payload)
    key=str(payload.get("edge_key") or "").strip(); source=str(payload.get("source_node_id") or ""); target=str(payload.get("target_node_id") or ""); relation=str(payload.get("relation_kind") or "").strip()
    if not key or not source or not target or not relation: raise ValueError("edge_key, source_node_id, target_node_id, and relation_kind are required.")
    if source==target: raise ValueError("graph edge endpoints must be distinct.")
    _research_graph_node(db,graph_id,source); _research_graph_node(db,graph_id,target)
    if relation in FORBIDDEN_GRAPH_RELATIONS: raise ValueError("relation_kind is determinative and is not permitted in the governed research graph.")
    if relation not in RESEARCH_GRAPH_RELATION_KINDS: raise ValueError("unsupported relation_kind.")
    evidence_ids=[str(x) for x in (payload.get("evidence_basis_ids") or [])]
    for eid in evidence_ids: _evidence(db,investigation_id,eid)
    row=ForensicResearchGraphEdgeRecord(graph_id=graph_id,edge_key=key,source_node_id=source,target_node_id=target,relation_kind=relation,assertion_state=str(payload.get("assertion_state") or "asserted"),rationale=payload.get("rationale"),evidence_basis_ids_json=evidence_ids,properties_json=dict(payload.get("properties") or {}),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_research_graph_view(db: Session, investigation_id: str, graph_id: str, payload: dict[str, Any]):
    _research_graph(db,investigation_id,graph_id); _reject_graph_determination_fields(payload)
    key=str(payload.get("view_key") or "").strip(); name=str(payload.get("name") or "").strip()
    if not key or not name: raise ValueError("view_key and name are required.")
    row=ForensicResearchGraphViewRecord(graph_id=graph_id,view_key=key,name=name,filters_json=dict(payload.get("filters") or {}),layout_hints_json=dict(payload.get("layout_hints") or {}),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def forensic_research_graph_bundle(db: Session, investigation_id: str, graph_id: str):
    graph=_research_graph(db,investigation_id,graph_id)
    nodes=db.scalars(select(ForensicResearchGraphNodeRecord).where(ForensicResearchGraphNodeRecord.graph_id==graph_id).order_by(ForensicResearchGraphNodeRecord.created_at,ForensicResearchGraphNodeRecord.node_key)).all()
    edges=db.scalars(select(ForensicResearchGraphEdgeRecord).where(ForensicResearchGraphEdgeRecord.graph_id==graph_id).order_by(ForensicResearchGraphEdgeRecord.created_at,ForensicResearchGraphEdgeRecord.edge_key)).all()
    views=db.scalars(select(ForensicResearchGraphViewRecord).where(ForensicResearchGraphViewRecord.graph_id==graph_id).order_by(ForensicResearchGraphViewRecord.created_at)).all()
    handoffs=db.scalars(select(ForensicResearchGraphHandoffRecord).where(ForensicResearchGraphHandoffRecord.graph_id==graph_id).order_by(ForensicResearchGraphHandoffRecord.created_at)).all()
    snapshots=db.scalars(select(ForensicResearchGraphSnapshotRecord).where(ForensicResearchGraphSnapshotRecord.graph_id==graph_id).order_by(ForensicResearchGraphSnapshotRecord.revision)).all()
    packages=db.scalars(select(ForensicResearchGraphPackageRecord).where(ForensicResearchGraphPackageRecord.graph_id==graph_id).order_by(ForensicResearchGraphPackageRecord.package_key,ForensicResearchGraphPackageRecord.revision)).all()
    return {"contract":"sc.open-forensics.research-graph.v1","investigation_id":investigation_id,"graph":_ser(graph),"nodes":[_ser(x) for x in nodes],"edges":[_ser(x) for x in edges],"views":[_ser(x) for x in views],"handoffs":[_ser(x) for x in handoffs],"snapshots":[_ser(x) for x in snapshots],"packages":[_ser(x) for x in packages],"edges_are_explicit_not_inferred":True,"descriptive_only":True,"boundaries":_boundaries()}


def forensic_research_graph_visual_spec(db: Session, investigation_id: str, graph_id: str):
    state=forensic_research_graph_bundle(db,investigation_id,graph_id)
    return {"contract":"sc.visual-spec.forensic-research-graph.v1","visual_kind":"forensic-research-graph","renderer_neutral":True,"investigation_id":investigation_id,"graph_id":graph_id,"nodes":state["nodes"],"edges":state["edges"],"views":state["views"],"execution":{"layout_by_core":False,"rendering_by_core":False,"graph_analytics_execution_by_core":False,"automatic_graph_edge_inference_by_core":False,"automatic_entity_resolution_by_core":False},"boundaries":_boundaries()}


def create_research_graph_handoff(db: Session, investigation_id: str, graph_id: str, payload: dict[str, Any]):
    _research_graph(db,investigation_id,graph_id); _reject_graph_determination_fields(payload)
    key=str(payload.get("handoff_key") or "").strip(); target=str(payload.get("target_product") or "").strip()
    if not key or not target: raise ValueError("handoff_key and target_product are required.")
    if target not in RESEARCH_GRAPH_TARGET_PRODUCTS: raise ValueError("unsupported target_product.")
    state=forensic_research_graph_bundle(db,investigation_id,graph_id); state["handoffs"]=[]; state["snapshots"]=[]; state["packages"]=[]
    manifest={"contract":"sc.open-forensics.research-graph-handoff.v1","target_product":target,"graph":state,"remote_product_fetch_by_core":False,"specialist_execution_required":target not in {"core","research-librarian"}}
    row=ForensicResearchGraphHandoffRecord(graph_id=graph_id,handoff_key=key,target_product=target,manifest_json=manifest,external_ref=payload.get("external_ref"),status=str(payload.get("status") or "prepared"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {})); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def create_research_graph_snapshot(db: Session, investigation_id: str, graph_id: str, payload: dict[str, Any]):
    _reject_graph_determination_fields(payload); state=forensic_research_graph_bundle(db,investigation_id,graph_id); state["snapshots"]=[]; state["packages"]=[]
    canonical=json.dumps(state,sort_keys=True,separators=(",",":"),default=str).encode("utf-8"); digest=hashlib.sha256(canonical).hexdigest()
    last=db.scalar(select(ForensicResearchGraphSnapshotRecord).where(ForensicResearchGraphSnapshotRecord.graph_id==graph_id).order_by(ForensicResearchGraphSnapshotRecord.revision.desc()).limit(1)); revision=(last.revision+1) if last else 1
    row=ForensicResearchGraphSnapshotRecord(graph_id=graph_id,revision=revision,content_hash=digest,previous_snapshot_hash=last.content_hash if last else None,state_json=state,provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def create_research_graph_package(db: Session, investigation_id: str, graph_id: str, payload: dict[str, Any]):
    _reject_graph_determination_fields(payload); _research_graph(db,investigation_id,graph_id)
    key=str(payload.get("package_key") or "").strip()
    if not key: raise ValueError("package_key is required.")
    state=forensic_research_graph_bundle(db,investigation_id,graph_id); state["packages"]=[]
    canonical=json.dumps(state,sort_keys=True,separators=(",",":"),default=str).encode("utf-8"); digest=hashlib.sha256(canonical).hexdigest()
    last=db.scalar(select(ForensicResearchGraphPackageRecord).where(ForensicResearchGraphPackageRecord.graph_id==graph_id,ForensicResearchGraphPackageRecord.package_key==key).order_by(ForensicResearchGraphPackageRecord.revision.desc()).limit(1)); revision=(last.revision+1) if last else 1
    manifest={"contract":"sc.open-forensics.research-graph-package.v1","manifest_hash":digest,"state":state,"descriptive_only":True,"automatic_truth_promotion":False}
    row=ForensicResearchGraphPackageRecord(graph_id=graph_id,package_key=key,revision=revision,manifest_hash=digest,manifest_json=manifest,provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def research_graph_source_inventory(db: Session, investigation_id: str):
    _investigation(db,investigation_id)
    def count(model):
        q=select(func.count()).select_from(model)
        if hasattr(model,"investigation_id"): q=q.where(model.investigation_id==investigation_id)
        return int(db.scalar(q) or 0)
    return {"contract":"sc.open-forensics.research-graph-source-inventory.v1","investigation_id":investigation_id,"eligible_node_kinds":sorted(RESEARCH_GRAPH_NODE_KINDS),"cross_product_targets":sorted(RESEARCH_GRAPH_TARGET_PRODUCTS),"counts":{"forensic_objects":count(ForensicObjectRecord),"evidence_items":count(ForensicEvidenceItemRecord),"custodians":count(ForensicCustodianRecord),"claims":count(ForensicClaimRecord),"hypotheses":count(ForensicHypothesisRecord),"events":count(ForensicEventRecord),"places":count(ForensicPlaceRecord),"trajectories":count(ForensicTrajectoryEvidenceRecord),"media_artifacts":count(ForensicMediaArtifactRecord),"quantitative_reconstructions":count(ForensicQuantitativeReconstructionRecord),"statements":count(ForensicStatementRecord),"documents":count(ForensicDocumentRecord)},"automatic_node_creation_by_core":False,"automatic_graph_edge_inference_by_core":False}
