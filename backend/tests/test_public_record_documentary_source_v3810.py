import pytest
from pydantic import ValidationError

from app.services.public_record_documentary_source import (
    CONTRACT_VERSION,
    AcquisitionMethod,
    AuthenticityState,
    DocumentAcquisitionRecord,
    DocumentAuthenticityAssessment,
    DocumentCustodyEvent,
    DocumentDerivativeKind,
    DocumentRedactionRecord,
    DocumentSegmentAnchor,
    DocumentVersionRecord,
    DocumentaryEvidenceInterpretation,
    DocumentarySourceDescriptor,
    PublicRecordDisclosureRecord,
    PublicRecordDocumentarySourceBundle,
    contract_document,
    reference_public_record_documentary_source_bundle,
)


def ref(): return reference_public_record_documentary_source_bundle()

def test_release(): assert contract_document()["release"] == "3.81.0"
def test_contract(): assert contract_document()["contract"] == CONTRACT_VERSION
def test_two_sources(): assert len(ref().documentary_sources) == 2
def test_two_acquisitions(): assert len(ref().acquisition_records) == 2
def test_four_versions(): assert len(ref().document_versions) == 4
def test_four_custody_events(): assert len(ref().custody_events) == 4
def test_one_redaction(): assert len(ref().redactions) == 1
def test_three_segments(): assert len(ref().segments) == 3
def test_two_auth_assessments(): assert len(ref().authenticity_assessments) == 2
def test_one_disclosure(): assert len(ref().disclosure_records) == 1
def test_two_interpretations(): assert len(ref().evidence_interpretations) == 2
def test_one_snapshot(): assert len(ref().snapshots) == 1
def test_source_kind_filing(): assert ref().documentary_sources[0].source_kind.value == "filing"
def test_source_kind_correspondence(): assert ref().documentary_sources[1].source_kind.value == "correspondence"
def test_acquisition_official_download(): assert ref().acquisition_records[0].acquisition_method == AcquisitionMethod.official_download
def test_acquisition_disclosure(): assert ref().acquisition_records[1].acquisition_method == AcquisitionMethod.disclosure
def test_original_version_1(): assert ref().document_versions[0].derivative_kind == DocumentDerivativeKind.original
def test_ocr_version(): assert ref().document_versions[1].derivative_kind == DocumentDerivativeKind.ocr
def test_original_version_2(): assert ref().document_versions[2].derivative_kind == DocumentDerivativeKind.original
def test_redacted_version(): assert ref().document_versions[3].derivative_kind == DocumentDerivativeKind.redacted_copy
def test_redaction_boundary(): assert ref().redactions[0].redaction_presence_is_not_evidence_of_wrongdoing is True
def test_hidden_content_boundary(): assert ref().redactions[0].redacted_content_must_not_be_inferred is True
def test_auth_content_truth_boundary(): assert ref().authenticity_assessments[0].authenticity_is_not_content_truth is True
def test_auth_claim_truth_boundary(): assert ref().authenticity_assessments[0].authenticity_is_not_claim_truth is True
def test_auth_admissibility_boundary(): assert ref().authenticity_assessments[0].authenticity_is_not_admissibility is True
def test_disclosure_absence_boundary(): assert ref().disclosure_records[0].withheld_or_absent_material_is_not_proof is True
def test_disclosure_completeness_boundary(): assert ref().disclosure_records[0].disclosure_scope_does_not_imply_completeness is True
def test_interpretation_boundary(): assert ref().evidence_interpretations[0].document_content_is_not_self_interpreting_evidence is True
def test_interpretation_not_truth(): assert ref().evidence_interpretations[0].interpretation_is_not_truth_verdict is True
def test_snapshot_immutable(): assert ref().snapshots[0].immutable_snapshot is True
def test_snapshot_lineage(): assert ref().snapshots[0].snapshot_preserves_source_and_derivative_lineage is True
def test_snapshot_not_truth(): assert ref().snapshots[0].snapshot_is_not_truth_verdict is True
def test_snapshot_no_mutation(): assert ref().snapshots[0].snapshot_does_not_mutate_evidence_or_identity_graphs is True
def test_bundle_document_existence_not_truth(): assert ref().document_existence_is_not_claim_truth is True
def test_bundle_authenticity_not_truth(): assert ref().document_authenticity_is_not_content_truth is True
def test_bundle_redaction_not_wrongdoing(): assert ref().redaction_is_not_wrongdoing is True
def test_bundle_hidden_content_not_inferred(): assert ref().hidden_or_missing_content_is_not_inferred is True
def test_bundle_no_evidence_mutation(): assert ref().evidence_graph_mutation_performed is False
def test_bundle_no_identity_mutation(): assert ref().identity_graph_mutation_performed is False
def test_fingerprint_stable(): assert ref().fingerprint() == ref().fingerprint()
def test_fingerprint_length(): assert len(ref().fingerprint()) == 64
def test_contract_fingerprint_length(): assert len(contract_document()["reference"]["bundle_fingerprint_sha256"]) == 64


def test_original_requires_no_parent():
    d=ref().document_versions[0].model_dump(); d["parent_version_ref"]="document-version:x"
    with pytest.raises(ValidationError): DocumentVersionRecord.model_validate(d)

def test_original_requires_original_bytes():
    d=ref().document_versions[0].model_dump(); d["is_original_source_bytes"]=False
    with pytest.raises(ValidationError): DocumentVersionRecord.model_validate(d)

def test_original_rejects_derivative_flag():
    d=ref().document_versions[0].model_dump(); d["derivative_is_not_original"]=True
    with pytest.raises(ValidationError): DocumentVersionRecord.model_validate(d)

def test_derivative_requires_parent():
    d=ref().document_versions[1].model_dump(); d["parent_version_ref"]=None
    with pytest.raises(ValidationError): DocumentVersionRecord.model_validate(d)

def test_derivative_rejects_original_bytes():
    d=ref().document_versions[1].model_dump(); d["is_original_source_bytes"]=True
    with pytest.raises(ValidationError): DocumentVersionRecord.model_validate(d)

def test_derivative_requires_derivative_flag():
    d=ref().document_versions[1].model_dump(); d["derivative_is_not_original"]=False
    with pytest.raises(ValidationError): DocumentVersionRecord.model_validate(d)

def test_custody_self_reference_rejected():
    d=ref().custody_events[0].model_dump(); d["previous_event_ref"]=d["custody_event_id"]
    with pytest.raises(ValidationError): DocumentCustodyEvent.model_validate(d)

def test_segment_line_order_enforced():
    d=ref().segments[0].model_dump(); d["line_start"]=10; d["line_end"]=2
    with pytest.raises(ValidationError): DocumentSegmentAnchor.model_validate(d)

def test_segment_timestamp_order_enforced():
    d=ref().segments[0].model_dump(); d["line_start"]=None; d["line_end"]=None; d["page_label"]=None; d["timestamp_start_seconds"]=10; d["timestamp_end_seconds"]=2
    with pytest.raises(ValidationError): DocumentSegmentAnchor.model_validate(d)

def test_segment_requires_locator():
    d=ref().segments[0].model_dump(); d["page_label"]=None; d["line_start"]=None; d["line_end"]=None; d["timestamp_start_seconds"]=None; d["timestamp_end_seconds"]=None
    with pytest.raises(ValidationError): DocumentSegmentAnchor.model_validate(d)

def test_bad_acquisition_hash_rejected():
    d=ref().acquisition_records[0].model_dump(); d["content_sha256"]="z"*64
    with pytest.raises(ValidationError): DocumentAcquisitionRecord.model_validate(d)


def _invalid(mutator):
    b=ref().model_copy(deep=True); mutator(b)
    with pytest.raises(ValidationError): PublicRecordDocumentarySourceBundle.model_validate(b.model_dump(mode="json"))

def test_unknown_v380_source_rejected(): _invalid(lambda b: setattr(b.documentary_sources[0],"reconciliation_source_descriptor_ref","source:missing"))
def test_unknown_acquisition_source_rejected(): _invalid(lambda b: setattr(b.acquisition_records[0],"documentary_source_ref","doc:missing"))
def test_unknown_version_source_rejected(): _invalid(lambda b: setattr(b.document_versions[0],"documentary_source_ref","doc:missing"))
def test_unknown_version_acquisition_rejected(): _invalid(lambda b: setattr(b.document_versions[0],"acquisition_record_ref","acq:missing"))
def test_unknown_parent_version_rejected(): _invalid(lambda b: setattr(b.document_versions[1],"parent_version_ref","version:missing"))
def test_self_parent_rejected(): _invalid(lambda b: setattr(b.document_versions[1],"parent_version_ref",b.document_versions[1].document_version_id))
def test_unknown_version_redaction_rejected(): _invalid(lambda b: setattr(b.document_versions[3],"redaction_refs",["redaction:missing"]))
def test_unknown_custody_version_rejected(): _invalid(lambda b: setattr(b.custody_events[0],"document_version_ref","version:missing"))
def test_unknown_previous_custody_rejected(): _invalid(lambda b: setattr(b.custody_events[1],"previous_event_ref","custody:missing"))
def test_unknown_redaction_version_rejected(): _invalid(lambda b: setattr(b.redactions[0],"document_version_ref","version:missing"))
def test_unknown_segment_version_rejected(): _invalid(lambda b: setattr(b.segments[0],"document_version_ref","version:missing"))
def test_unknown_assessment_version_rejected(): _invalid(lambda b: setattr(b.authenticity_assessments[0],"document_version_ref","version:missing"))
def test_unknown_assessment_evidence_rejected(): _invalid(lambda b: setattr(b.authenticity_assessments[0],"supporting_evidence_refs",["evidence:missing"]))
def test_unknown_disclosure_source_rejected(): _invalid(lambda b: setattr(b.disclosure_records[0],"documentary_source_refs",["doc:missing"]))
def test_unknown_interpretation_version_rejected(): _invalid(lambda b: setattr(b.evidence_interpretations[0],"document_version_ref","version:missing"))
def test_unknown_interpretation_segment_rejected(): _invalid(lambda b: setattr(b.evidence_interpretations[0],"segment_refs",["segment:missing"]))
def test_unknown_interpretation_evidence_rejected(): _invalid(lambda b: setattr(b.evidence_interpretations[0],"evidence_ref","evidence:missing"))
def test_unknown_interpretation_entity_rejected(): _invalid(lambda b: setattr(b.evidence_interpretations[0],"entity_refs",["entity:missing"]))
def test_unknown_snapshot_source_rejected(): _invalid(lambda b: setattr(b.snapshots[0],"documentary_source_refs",["doc:missing"]))
def test_unknown_snapshot_version_rejected(): _invalid(lambda b: setattr(b.snapshots[0],"document_version_refs",["version:missing"]))
def test_unknown_snapshot_custody_rejected(): _invalid(lambda b: setattr(b.snapshots[0],"custody_event_refs",["custody:missing"]))
def test_unknown_snapshot_assessment_rejected(): _invalid(lambda b: setattr(b.snapshots[0],"authenticity_assessment_refs",["auth:missing"]))
def test_unknown_snapshot_interpretation_rejected(): _invalid(lambda b: setattr(b.snapshots[0],"interpretation_refs",["interp:missing"]))
def test_unknown_snapshot_redaction_rejected(): _invalid(lambda b: setattr(b.snapshots[0],"unresolved_redaction_refs",["redaction:missing"]))
def test_duplicate_source_record_key_rejected(): _invalid(lambda b: setattr(b.documentary_sources[1],"source_record_key",b.documentary_sources[0].source_record_key))

def test_parent_cycle_rejected():
    b=ref().model_copy(deep=True)
    b.document_versions[0].derivative_kind=DocumentDerivativeKind.normalized_copy
    b.document_versions[0].is_original_source_bytes=False
    b.document_versions[0].derivative_is_not_original=True
    b.document_versions[0].parent_version_ref=b.document_versions[1].document_version_id
    with pytest.raises(ValidationError): PublicRecordDocumentarySourceBundle.model_validate(b.model_dump(mode="json"))


def test_contract_no_fetch(): assert contract_document()["boundaries"]["core_fetches_or_scrapes_public_records"] is False
def test_contract_no_ocr(): assert contract_document()["boundaries"]["core_performs_ocr_or_transcription"] is False
def test_contract_no_hidden_inference(): assert contract_document()["boundaries"]["core_infers_redacted_or_missing_content"] is False
def test_contract_no_auth_truth(): assert contract_document()["boundaries"]["core_treats_authenticity_as_content_truth"] is False
def test_contract_no_existence_truth(): assert contract_document()["boundaries"]["core_treats_document_existence_as_claim_truth"] is False
def test_contract_no_redaction_wrongdoing(): assert contract_document()["boundaries"]["core_treats_redaction_as_wrongdoing"] is False
def test_contract_no_admissibility(): assert contract_document()["boundaries"]["core_determines_legal_admissibility"] is False
def test_contract_no_authorship(): assert contract_document()["boundaries"]["core_determines_authorship_or_credibility"] is False
def test_contract_no_evidence_mutation(): assert contract_document()["boundaries"]["core_mutates_evidence_graph_during_document_ingest"] is False
def test_contract_no_identity_mutation(): assert contract_document()["boundaries"]["core_mutates_identity_graph_during_document_ingest"] is False
def test_contract_prepares_v382(): assert contract_document()["roadmap_integration"]["prepares_v3820_relationship_discovery_connection_hypotheses"] is True
def test_contract_prepares_v384(): assert contract_document()["roadmap_integration"]["prepares_v3840_explainable_connection_paths_evidence_chains"] is True
def test_contract_prepares_v388(): assert contract_document()["roadmap_integration"]["prepares_v3880_reproducible_graph_investigation_package"] is True
def test_contract_preserves_evidence_boundary(): assert contract_document()["roadmap_integration"]["preserves_v3760_evidence_validation_boundary"] is True
def test_reference_existence_false(): assert contract_document()["reference"]["document_existence_is_claim_truth"] is False
def test_reference_auth_false(): assert contract_document()["reference"]["document_authenticity_is_content_truth"] is False
def test_reference_redaction_false(): assert contract_document()["reference"]["redaction_is_wrongdoing"] is False
def test_reference_hidden_false(): assert contract_document()["reference"]["hidden_or_missing_content_inferred"] is False
def test_reference_no_evidence_mutation(): assert contract_document()["reference"]["evidence_graph_mutation_performed"] is False
def test_reference_no_identity_mutation(): assert contract_document()["reference"]["identity_graph_mutation_performed"] is False
