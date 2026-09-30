from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .cross_source_entity_reconciliation import (
    CrossSourceEntityReconciliationBundle,
    reference_cross_source_entity_reconciliation_bundle,
)

CORE_RELEASE = "3.81.0"
CONTRACT_VERSION = "sc.core.public-record-documentary-source-object-model.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class DocumentarySourceKind(str, Enum):
    public_record = "public-record"
    filing = "filing"
    correspondence = "correspondence"
    transcript = "transcript"
    log = "log"
    report = "report"
    archival_item = "archival-item"
    docket = "docket"
    minutes = "minutes"
    contract = "contract"
    policy = "policy"
    dataset_extract = "dataset-extract"
    media_transcript = "media-transcript"
    other = "other"


class AcquisitionMethod(str, Enum):
    official_download = "official-download"
    api = "api"
    archive_export = "archive-export"
    scan = "scan"
    disclosure = "disclosure"
    manual_upload = "manual-upload"
    repository_fetch = "repository-fetch"
    other = "other"


class DocumentDerivativeKind(str, Enum):
    original = "original"
    normalized_copy = "normalized-copy"
    scan = "scan"
    ocr = "ocr"
    transcription = "transcription"
    redacted_copy = "redacted-copy"
    translated_copy = "translated-copy"
    excerpt = "excerpt"


class CustodyEventType(str, Enum):
    acquired = "acquired"
    checksum_verified = "checksum-verified"
    stored = "stored"
    transferred = "transferred"
    derivative_created = "derivative-created"
    redaction_recorded = "redaction-recorded"
    reviewed = "reviewed"


class AuthenticityState(str, Enum):
    unassessed = "unassessed"
    source_attested = "source-attested"
    checksum_verified = "checksum-verified"
    independently_corroborated = "independently-corroborated"
    disputed = "disputed"


class EvidenceInterpretationRelation(str, Enum):
    supports = "supports"
    contradicts = "contradicts"
    contextualizes = "contextualizes"
    mentions = "mentions"
    unresolved = "unresolved"


class DocumentarySourceDescriptor(BaseModel):
    documentary_source_id: str = Field(min_length=2, max_length=500)
    reconciliation_source_descriptor_ref: str | None = Field(default=None, max_length=500)
    source_kind: DocumentarySourceKind
    title: str = Field(min_length=1, max_length=2000)
    issuing_body: str | None = Field(default=None, max_length=1000)
    jurisdiction_or_context: str | None = Field(default=None, max_length=1000)
    source_record_key: str = Field(min_length=1, max_length=1000)
    publication_or_issue_date: str | None = Field(default=None, max_length=80)
    observed_at: str = Field(min_length=10, max_length=80)
    source_locator_ref: str = Field(min_length=1, max_length=2000)
    provenance_refs: list[str] = Field(min_length=1)
    source_description_is_not_authenticity_verdict: Literal[True] = True
    source_description_is_not_content_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DocumentAcquisitionRecord(BaseModel):
    acquisition_record_id: str = Field(min_length=2, max_length=500)
    documentary_source_ref: str = Field(min_length=2, max_length=500)
    acquisition_method: AcquisitionMethod
    acquired_at: str = Field(min_length=10, max_length=80)
    acquired_by_ref: str = Field(min_length=1, max_length=1000)
    acquisition_locator_ref: str = Field(min_length=1, max_length=2000)
    original_filename: str | None = Field(default=None, max_length=1000)
    media_type: str | None = Field(default=None, max_length=300)
    byte_length: int | None = Field(default=None, ge=0)
    content_sha256: str = Field(min_length=64, max_length=64)
    provenance_refs: list[str] = Field(min_length=1)
    acquisition_does_not_establish_authenticity: Literal[True] = True
    acquisition_does_not_establish_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.provenance_refs, "provenance_refs")
        if any(ch not in "0123456789abcdef" for ch in self.content_sha256.lower()):
            raise ValueError("content_sha256 must be lowercase/uppercase hexadecimal")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DocumentVersionRecord(BaseModel):
    document_version_id: str = Field(min_length=2, max_length=500)
    documentary_source_ref: str = Field(min_length=2, max_length=500)
    acquisition_record_ref: str = Field(min_length=2, max_length=500)
    derivative_kind: DocumentDerivativeKind
    parent_version_ref: str | None = Field(default=None, max_length=500)
    created_at: str = Field(min_length=10, max_length=80)
    content_sha256: str = Field(min_length=64, max_length=64)
    transformation_refs: list[str] = Field(default_factory=list)
    redaction_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(min_length=1)
    is_original_source_bytes: bool = False
    derivative_is_not_original: bool = True
    derived_text_is_not_source_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        for vals, label in ((self.transformation_refs, "transformation_refs"), (self.redaction_refs, "redaction_refs"), (self.provenance_refs, "provenance_refs")):
            _unique(vals, label)
        if self.derivative_kind == DocumentDerivativeKind.original:
            if self.parent_version_ref is not None:
                raise ValueError("original version cannot have parent_version_ref")
            if not self.is_original_source_bytes:
                raise ValueError("original version must mark is_original_source_bytes=true")
            if self.derivative_is_not_original:
                raise ValueError("original version cannot mark derivative_is_not_original=true")
        else:
            if not self.parent_version_ref:
                raise ValueError("derivative version requires parent_version_ref")
            if self.is_original_source_bytes:
                raise ValueError("derivative version cannot mark original source bytes")
            if not self.derivative_is_not_original:
                raise ValueError("derivative version must mark derivative_is_not_original=true")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DocumentCustodyEvent(BaseModel):
    custody_event_id: str = Field(min_length=2, max_length=500)
    document_version_ref: str = Field(min_length=2, max_length=500)
    event_type: CustodyEventType
    occurred_at: str = Field(min_length=10, max_length=80)
    actor_ref: str = Field(min_length=1, max_length=1000)
    previous_event_ref: str | None = Field(default=None, max_length=500)
    content_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    provenance_refs: list[str] = Field(min_length=1)
    append_only_event: Literal[True] = True
    custody_continuity_is_not_authenticity_proof: Literal[True] = True
    custody_continuity_is_not_content_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.provenance_refs, "provenance_refs")
        if self.previous_event_ref == self.custody_event_id:
            raise ValueError("custody event cannot reference itself")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DocumentRedactionRecord(BaseModel):
    redaction_record_id: str = Field(min_length=2, max_length=500)
    document_version_ref: str = Field(min_length=2, max_length=500)
    redaction_scope: str = Field(min_length=1, max_length=4000)
    redaction_reason: str | None = Field(default=None, max_length=4000)
    authority_ref: str | None = Field(default=None, max_length=1000)
    recorded_at: str = Field(min_length=10, max_length=80)
    provenance_refs: list[str] = Field(min_length=1)
    redaction_presence_is_not_evidence_of_wrongdoing: Literal[True] = True
    redacted_content_must_not_be_inferred: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DocumentSegmentAnchor(BaseModel):
    document_segment_id: str = Field(min_length=2, max_length=500)
    document_version_ref: str = Field(min_length=2, max_length=500)
    page_label: str | None = Field(default=None, max_length=200)
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    timestamp_start_seconds: float | None = Field(default=None, ge=0)
    timestamp_end_seconds: float | None = Field(default=None, ge=0)
    segment_sha256: str = Field(min_length=64, max_length=64)
    provenance_refs: list[str] = Field(min_length=1)
    segment_is_locator_not_interpretation: Literal[True] = True
    extracted_text_is_derived_representation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.provenance_refs, "provenance_refs")
        if self.line_start and self.line_end and self.line_end < self.line_start:
            raise ValueError("line_end must be >= line_start")
        if self.timestamp_start_seconds is not None and self.timestamp_end_seconds is not None and self.timestamp_end_seconds < self.timestamp_start_seconds:
            raise ValueError("timestamp_end_seconds must be >= timestamp_start_seconds")
        if self.page_label is None and self.line_start is None and self.timestamp_start_seconds is None:
            raise ValueError("segment requires page, line, or timestamp locator")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DocumentAuthenticityAssessment(BaseModel):
    authenticity_assessment_id: str = Field(min_length=2, max_length=500)
    document_version_ref: str = Field(min_length=2, max_length=500)
    authenticity_state: AuthenticityState
    assessment_method_refs: list[str] = Field(min_length=1)
    supporting_evidence_refs: list[str] = Field(default_factory=list)
    contradicting_evidence_refs: list[str] = Field(default_factory=list)
    reviewer_ref: str = Field(min_length=1, max_length=1000)
    assessed_at: str = Field(min_length=10, max_length=80)
    authenticity_is_not_content_truth: Literal[True] = True
    authenticity_is_not_claim_truth: Literal[True] = True
    authenticity_is_not_admissibility: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        for vals, label in ((self.assessment_method_refs, "assessment_method_refs"), (self.supporting_evidence_refs, "supporting_evidence_refs"), (self.contradicting_evidence_refs, "contradicting_evidence_refs")):
            _unique(vals, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PublicRecordDisclosureRecord(BaseModel):
    disclosure_record_id: str = Field(min_length=2, max_length=500)
    documentary_source_refs: list[str] = Field(min_length=1)
    request_or_case_ref: str = Field(min_length=1, max_length=1000)
    responding_authority_ref: str = Field(min_length=1, max_length=1000)
    response_date: str = Field(min_length=8, max_length=80)
    disclosed_item_count: int = Field(ge=0)
    withheld_item_count: int | None = Field(default=None, ge=0)
    redacted_item_count: int | None = Field(default=None, ge=0)
    provenance_refs: list[str] = Field(min_length=1)
    withheld_or_absent_material_is_not_proof: Literal[True] = True
    disclosure_scope_does_not_imply_completeness: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.documentary_source_refs, "documentary_source_refs")
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DocumentaryEvidenceInterpretation(BaseModel):
    documentary_interpretation_id: str = Field(min_length=2, max_length=500)
    document_version_ref: str = Field(min_length=2, max_length=500)
    segment_refs: list[str] = Field(default_factory=list)
    evidence_ref: str = Field(min_length=1, max_length=1000)
    relation: EvidenceInterpretationRelation
    interpretation_summary: str = Field(min_length=1, max_length=8000)
    entity_refs: list[str] = Field(default_factory=list)
    reviewer_ref: str = Field(min_length=1, max_length=1000)
    interpreted_at: str = Field(min_length=10, max_length=80)
    document_content_is_not_self_interpreting_evidence: Literal[True] = True
    interpretation_is_not_truth_verdict: Literal[True] = True
    provenance_refs: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        for vals, label in ((self.segment_refs, "segment_refs"), (self.entity_refs, "entity_refs"), (self.provenance_refs, "provenance_refs")):
            _unique(vals, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DocumentarySourceSnapshot(BaseModel):
    documentary_snapshot_id: str = Field(min_length=2, max_length=500)
    documentary_source_refs: list[str] = Field(min_length=1)
    document_version_refs: list[str] = Field(min_length=1)
    custody_event_refs: list[str] = Field(default_factory=list)
    authenticity_assessment_refs: list[str] = Field(default_factory=list)
    interpretation_refs: list[str] = Field(default_factory=list)
    unresolved_redaction_refs: list[str] = Field(default_factory=list)
    created_at: str = Field(min_length=10, max_length=80)
    immutable_snapshot: Literal[True] = True
    snapshot_preserves_source_and_derivative_lineage: Literal[True] = True
    snapshot_is_not_truth_verdict: Literal[True] = True
    snapshot_does_not_mutate_evidence_or_identity_graphs: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        for vals, label in (
            (self.documentary_source_refs, "documentary_source_refs"),
            (self.document_version_refs, "document_version_refs"),
            (self.custody_event_refs, "custody_event_refs"),
            (self.authenticity_assessment_refs, "authenticity_assessment_refs"),
            (self.interpretation_refs, "interpretation_refs"),
            (self.unresolved_redaction_refs, "unresolved_redaction_refs"),
        ):
            _unique(vals, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PublicRecordDocumentarySourceBundle(BaseModel):
    cross_source_entity_reconciliation_bundle: CrossSourceEntityReconciliationBundle
    documentary_sources: list[DocumentarySourceDescriptor] = Field(min_length=1)
    acquisition_records: list[DocumentAcquisitionRecord] = Field(min_length=1)
    document_versions: list[DocumentVersionRecord] = Field(min_length=1)
    custody_events: list[DocumentCustodyEvent] = Field(min_length=1)
    redactions: list[DocumentRedactionRecord] = Field(default_factory=list)
    segments: list[DocumentSegmentAnchor] = Field(min_length=1)
    authenticity_assessments: list[DocumentAuthenticityAssessment] = Field(min_length=1)
    disclosure_records: list[PublicRecordDisclosureRecord] = Field(default_factory=list)
    evidence_interpretations: list[DocumentaryEvidenceInterpretation] = Field(min_length=1)
    snapshots: list[DocumentarySourceSnapshot] = Field(min_length=1)
    document_existence_is_not_claim_truth: Literal[True] = True
    document_authenticity_is_not_content_truth: Literal[True] = True
    redaction_is_not_wrongdoing: Literal[True] = True
    hidden_or_missing_content_is_not_inferred: Literal[True] = True
    evidence_graph_mutation_performed: Literal[False] = False
    identity_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        upstream = self.cross_source_entity_reconciliation_bundle
        base = upstream.probabilistic_record_linkage_bundle.temporal_identity_bundle.entity_resolution_identity_graph_bundle

        def ids(items, attr, label):
            vals=[getattr(x, attr) for x in items]; _unique(vals, label); return set(vals)

        reconciliation_source_ids={x.source_descriptor_id for x in upstream.source_descriptors}
        entity_ids={x.entity_id for x in base.entities}
        evidence_ids={x.identity_evidence_id for x in base.identity_evidence_items}

        source_ids=ids(self.documentary_sources,"documentary_source_id","documentary_source_ids")
        acquisition_ids=ids(self.acquisition_records,"acquisition_record_id","acquisition_record_ids")
        version_ids=ids(self.document_versions,"document_version_id","document_version_ids")
        custody_ids=ids(self.custody_events,"custody_event_id","custody_event_ids")
        redaction_ids=ids(self.redactions,"redaction_record_id","redaction_ids")
        segment_ids=ids(self.segments,"document_segment_id","segment_ids")
        assessment_ids=ids(self.authenticity_assessments,"authenticity_assessment_id","assessment_ids")
        disclosure_ids=ids(self.disclosure_records,"disclosure_record_id","disclosure_ids")
        interpretation_ids=ids(self.evidence_interpretations,"documentary_interpretation_id","interpretation_ids")
        ids(self.snapshots,"documentary_snapshot_id","snapshot_ids")

        record_keys={x.source_record_key for x in self.documentary_sources}
        if len(record_keys)!=len(self.documentary_sources):
            raise ValueError("documentary source_record_key values must be unique")

        for src in self.documentary_sources:
            if src.reconciliation_source_descriptor_ref and src.reconciliation_source_descriptor_ref not in reconciliation_source_ids:
                raise ValueError("documentary source references unknown v3.80 reconciliation source")
        for acq in self.acquisition_records:
            if acq.documentary_source_ref not in source_ids:
                raise ValueError("acquisition references unknown documentary source")
        for ver in self.document_versions:
            if ver.documentary_source_ref not in source_ids:
                raise ValueError("document version references unknown documentary source")
            if ver.acquisition_record_ref not in acquisition_ids:
                raise ValueError("document version references unknown acquisition")
            if ver.parent_version_ref and ver.parent_version_ref not in version_ids:
                raise ValueError("document version references unknown parent version")
            if ver.parent_version_ref == ver.document_version_id:
                raise ValueError("document version cannot parent itself")
            if not set(ver.redaction_refs) <= redaction_ids:
                raise ValueError("document version references unknown redaction")
        # Parent lineage must be acyclic.
        parent={x.document_version_id:x.parent_version_ref for x in self.document_versions}
        for vid in version_ids:
            seen=set(); cur=vid
            while cur is not None:
                if cur in seen: raise ValueError("document version parent lineage contains cycle")
                seen.add(cur); cur=parent.get(cur)
        for event in self.custody_events:
            if event.document_version_ref not in version_ids:
                raise ValueError("custody event references unknown document version")
            if event.previous_event_ref and event.previous_event_ref not in custody_ids:
                raise ValueError("custody event references unknown previous event")
        for red in self.redactions:
            if red.document_version_ref not in version_ids:
                raise ValueError("redaction references unknown document version")
        for seg in self.segments:
            if seg.document_version_ref not in version_ids:
                raise ValueError("segment references unknown document version")
        for ass in self.authenticity_assessments:
            if ass.document_version_ref not in version_ids:
                raise ValueError("authenticity assessment references unknown document version")
            if not set(ass.supporting_evidence_refs + ass.contradicting_evidence_refs) <= evidence_ids:
                raise ValueError("authenticity assessment references unknown evidence")
        for d in self.disclosure_records:
            if not set(d.documentary_source_refs) <= source_ids:
                raise ValueError("disclosure references unknown documentary source")
        for interp in self.evidence_interpretations:
            if interp.document_version_ref not in version_ids:
                raise ValueError("interpretation references unknown document version")
            if not set(interp.segment_refs) <= segment_ids:
                raise ValueError("interpretation references unknown segment")
            if interp.evidence_ref not in evidence_ids:
                raise ValueError("interpretation references unknown evidence")
            if not set(interp.entity_refs) <= entity_ids:
                raise ValueError("interpretation references unknown entity")
        for snap in self.snapshots:
            if not set(snap.documentary_source_refs) <= source_ids: raise ValueError("snapshot references unknown documentary source")
            if not set(snap.document_version_refs) <= version_ids: raise ValueError("snapshot references unknown document version")
            if not set(snap.custody_event_refs) <= custody_ids: raise ValueError("snapshot references unknown custody event")
            if not set(snap.authenticity_assessment_refs) <= assessment_ids: raise ValueError("snapshot references unknown authenticity assessment")
            if not set(snap.interpretation_refs) <= interpretation_ids: raise ValueError("snapshot references unknown interpretation")
            if not set(snap.unresolved_redaction_refs) <= redaction_ids: raise ValueError("snapshot references unknown redaction")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _sha(label: str) -> str:
    return canonical_sha256({"synthetic": label})


def reference_public_record_documentary_source_bundle() -> PublicRecordDocumentarySourceBundle:
    upstream=reference_cross_source_entity_reconciliation_bundle()
    base=upstream.probabilistic_record_linkage_bundle.temporal_identity_bundle.entity_resolution_identity_graph_bundle
    evidence_refs=[x.identity_evidence_id for x in base.identity_evidence_items[:2]]
    entity_refs=[x.entity_id for x in base.entities[:2]]
    source_ref=upstream.source_descriptors[0].source_descriptor_id

    sources=[
        DocumentarySourceDescriptor(
            documentary_source_id="documentary-source:synthetic:agency-filing:v1",
            reconciliation_source_descriptor_ref=source_ref,
            source_kind=DocumentarySourceKind.filing,
            title="Synthetic Northstar annual filing",
            issuing_body="Synthetic Registry Authority",
            jurisdiction_or_context="Synthetic jurisdiction",
            source_record_key="synthetic-registry:annual-filing:2026",
            publication_or_issue_date="2026-03-31",
            observed_at="2026-09-30T03:10:00Z",
            source_locator_ref="source-locator:synthetic:registry-filing",
            provenance_refs=["provenance:synthetic:registry-filing:v1"],
            metadata={"synthetic_reference":True},
        ),
        DocumentarySourceDescriptor(
            documentary_source_id="documentary-source:synthetic:disclosure-letter:v1",
            reconciliation_source_descriptor_ref=None,
            source_kind=DocumentarySourceKind.correspondence,
            title="Synthetic disclosure response letter",
            issuing_body="Synthetic Records Office",
            jurisdiction_or_context="Synthetic public records process",
            source_record_key="synthetic-records:response:2026-091",
            publication_or_issue_date="2026-09-20",
            observed_at="2026-09-30T03:11:00Z",
            source_locator_ref="source-locator:synthetic:disclosure-letter",
            provenance_refs=["provenance:synthetic:disclosure-letter:v1"],
            metadata={"synthetic_reference":True},
        ),
    ]
    acquisitions=[
        DocumentAcquisitionRecord(
            acquisition_record_id="acquisition:synthetic:filing:v1", documentary_source_ref=sources[0].documentary_source_id,
            acquisition_method=AcquisitionMethod.official_download, acquired_at="2026-09-30T03:12:00Z", acquired_by_ref="actor:synthetic:researcher",
            acquisition_locator_ref="locator:synthetic:official-registry", original_filename="northstar-2026-filing.pdf", media_type="application/pdf", byte_length=10240,
            content_sha256=_sha("filing-original"), provenance_refs=["provenance:synthetic:acquisition:filing:v1"], metadata={"synthetic_reference":True},
        ),
        DocumentAcquisitionRecord(
            acquisition_record_id="acquisition:synthetic:letter:v1", documentary_source_ref=sources[1].documentary_source_id,
            acquisition_method=AcquisitionMethod.disclosure, acquired_at="2026-09-30T03:13:00Z", acquired_by_ref="actor:synthetic:researcher",
            acquisition_locator_ref="locator:synthetic:records-response", original_filename="response-091.pdf", media_type="application/pdf", byte_length=4096,
            content_sha256=_sha("letter-original"), provenance_refs=["provenance:synthetic:acquisition:letter:v1"], metadata={"synthetic_reference":True},
        ),
    ]
    versions=[
        DocumentVersionRecord(
            document_version_id="document-version:synthetic:filing:original:v1", documentary_source_ref=sources[0].documentary_source_id,
            acquisition_record_ref=acquisitions[0].acquisition_record_id, derivative_kind=DocumentDerivativeKind.original, parent_version_ref=None,
            created_at="2026-09-30T03:12:00Z", content_sha256=acquisitions[0].content_sha256, provenance_refs=["provenance:synthetic:version:filing-original:v1"],
            is_original_source_bytes=True, derivative_is_not_original=False, metadata={"synthetic_reference":True},
        ),
        DocumentVersionRecord(
            document_version_id="document-version:synthetic:filing:ocr:v1", documentary_source_ref=sources[0].documentary_source_id,
            acquisition_record_ref=acquisitions[0].acquisition_record_id, derivative_kind=DocumentDerivativeKind.ocr,
            parent_version_ref="document-version:synthetic:filing:original:v1", created_at="2026-09-30T03:14:00Z", content_sha256=_sha("filing-ocr"),
            transformation_refs=["transformation:synthetic:ocr:v1"], provenance_refs=["provenance:synthetic:version:filing-ocr:v1"],
            is_original_source_bytes=False, derivative_is_not_original=True, metadata={"synthetic_reference":True},
        ),
        DocumentVersionRecord(
            document_version_id="document-version:synthetic:letter:original:v1", documentary_source_ref=sources[1].documentary_source_id,
            acquisition_record_ref=acquisitions[1].acquisition_record_id, derivative_kind=DocumentDerivativeKind.original, parent_version_ref=None,
            created_at="2026-09-30T03:13:00Z", content_sha256=acquisitions[1].content_sha256, provenance_refs=["provenance:synthetic:version:letter-original:v1"],
            is_original_source_bytes=True, derivative_is_not_original=False, metadata={"synthetic_reference":True},
        ),
        DocumentVersionRecord(
            document_version_id="document-version:synthetic:letter:redacted:v1", documentary_source_ref=sources[1].documentary_source_id,
            acquisition_record_ref=acquisitions[1].acquisition_record_id, derivative_kind=DocumentDerivativeKind.redacted_copy,
            parent_version_ref="document-version:synthetic:letter:original:v1", created_at="2026-09-30T03:15:00Z", content_sha256=_sha("letter-redacted"),
            transformation_refs=["transformation:synthetic:redaction:v1"], redaction_refs=["redaction:synthetic:letter:1"], provenance_refs=["provenance:synthetic:version:letter-redacted:v1"],
            is_original_source_bytes=False, derivative_is_not_original=True, metadata={"synthetic_reference":True},
        ),
    ]
    redactions=[DocumentRedactionRecord(
        redaction_record_id="redaction:synthetic:letter:1", document_version_ref=versions[2].document_version_id,
        redaction_scope="Page 1, one bounded text region", redaction_reason="Synthetic statutory exemption marker", authority_ref="authority:synthetic:records-office",
        recorded_at="2026-09-30T03:15:00Z", provenance_refs=["provenance:synthetic:redaction:1"], metadata={"synthetic_reference":True},
    )]
    custody=[
        DocumentCustodyEvent(custody_event_id="custody:synthetic:filing:1",document_version_ref=versions[0].document_version_id,event_type=CustodyEventType.acquired,occurred_at="2026-09-30T03:12:00Z",actor_ref="actor:synthetic:researcher",content_sha256=versions[0].content_sha256,provenance_refs=["provenance:synthetic:custody:filing:1"]),
        DocumentCustodyEvent(custody_event_id="custody:synthetic:filing:2",document_version_ref=versions[0].document_version_id,event_type=CustodyEventType.checksum_verified,occurred_at="2026-09-30T03:12:30Z",actor_ref="runtime:synthetic:hash-verifier",previous_event_ref="custody:synthetic:filing:1",content_sha256=versions[0].content_sha256,provenance_refs=["provenance:synthetic:custody:filing:2"]),
        DocumentCustodyEvent(custody_event_id="custody:synthetic:letter:1",document_version_ref=versions[2].document_version_id,event_type=CustodyEventType.acquired,occurred_at="2026-09-30T03:13:00Z",actor_ref="actor:synthetic:researcher",content_sha256=versions[2].content_sha256,provenance_refs=["provenance:synthetic:custody:letter:1"]),
        DocumentCustodyEvent(custody_event_id="custody:synthetic:letter:2",document_version_ref=versions[3].document_version_id,event_type=CustodyEventType.redaction_recorded,occurred_at="2026-09-30T03:15:00Z",actor_ref="actor:synthetic:records-office",previous_event_ref="custody:synthetic:letter:1",content_sha256=versions[3].content_sha256,provenance_refs=["provenance:synthetic:custody:letter:2"]),
    ]
    segments=[
        DocumentSegmentAnchor(document_segment_id="segment:synthetic:filing:p1:v1",document_version_ref=versions[1].document_version_id,page_label="1",line_start=1,line_end=18,segment_sha256=_sha("filing-segment-1"),provenance_refs=["provenance:synthetic:segment:filing:1"]),
        DocumentSegmentAnchor(document_segment_id="segment:synthetic:filing:p2:v1",document_version_ref=versions[1].document_version_id,page_label="2",line_start=1,line_end=22,segment_sha256=_sha("filing-segment-2"),provenance_refs=["provenance:synthetic:segment:filing:2"]),
        DocumentSegmentAnchor(document_segment_id="segment:synthetic:letter:p1:v1",document_version_ref=versions[3].document_version_id,page_label="1",line_start=1,line_end=12,segment_sha256=_sha("letter-segment-1"),provenance_refs=["provenance:synthetic:segment:letter:1"]),
    ]
    assessments=[
        DocumentAuthenticityAssessment(authenticity_assessment_id="authenticity:synthetic:filing:v1",document_version_ref=versions[0].document_version_id,authenticity_state=AuthenticityState.checksum_verified,assessment_method_refs=["method:synthetic:source-checksum"],supporting_evidence_refs=[evidence_refs[0]],reviewer_ref="reviewer:synthetic:document-a",assessed_at="2026-09-30T03:20:00Z"),
        DocumentAuthenticityAssessment(authenticity_assessment_id="authenticity:synthetic:letter:v1",document_version_ref=versions[2].document_version_id,authenticity_state=AuthenticityState.source_attested,assessment_method_refs=["method:synthetic:disclosure-envelope"],supporting_evidence_refs=[evidence_refs[1]],reviewer_ref="reviewer:synthetic:document-b",assessed_at="2026-09-30T03:21:00Z"),
    ]
    disclosures=[PublicRecordDisclosureRecord(disclosure_record_id="disclosure:synthetic:2026-091:v1",documentary_source_refs=[sources[1].documentary_source_id],request_or_case_ref="records-request:synthetic:2026-091",responding_authority_ref="authority:synthetic:records-office",response_date="2026-09-20",disclosed_item_count=1,withheld_item_count=1,redacted_item_count=1,provenance_refs=["provenance:synthetic:disclosure:091"])]
    interpretations=[
        DocumentaryEvidenceInterpretation(documentary_interpretation_id="documentary-interpretation:synthetic:filing:v1",document_version_ref=versions[1].document_version_id,segment_refs=[segments[0].document_segment_id],evidence_ref=evidence_refs[0],relation=EvidenceInterpretationRelation.supports,interpretation_summary="The cited filing segment is treated as documentary support for the referenced identity evidence item, without elevating the whole document to truth.",entity_refs=entity_refs,reviewer_ref="reviewer:synthetic:document-a",interpreted_at="2026-09-30T03:25:00Z",provenance_refs=["provenance:synthetic:interpretation:filing"]),
        DocumentaryEvidenceInterpretation(documentary_interpretation_id="documentary-interpretation:synthetic:letter:v1",document_version_ref=versions[3].document_version_id,segment_refs=[segments[2].document_segment_id],evidence_ref=evidence_refs[1],relation=EvidenceInterpretationRelation.contextualizes,interpretation_summary="The disclosure letter establishes disclosure context and redaction state; it is not treated as proof of the redacted content.",entity_refs=[],reviewer_ref="reviewer:synthetic:document-b",interpreted_at="2026-09-30T03:26:00Z",provenance_refs=["provenance:synthetic:interpretation:letter"]),
    ]
    snapshot=DocumentarySourceSnapshot(documentary_snapshot_id="documentary-snapshot:synthetic:2026-09-30:v1",documentary_source_refs=[x.documentary_source_id for x in sources],document_version_refs=[x.document_version_id for x in versions],custody_event_refs=[x.custody_event_id for x in custody],authenticity_assessment_refs=[x.authenticity_assessment_id for x in assessments],interpretation_refs=[x.documentary_interpretation_id for x in interpretations],unresolved_redaction_refs=[redactions[0].redaction_record_id],created_at="2026-09-30T03:30:00Z",metadata={"synthetic_reference":True})
    return PublicRecordDocumentarySourceBundle(cross_source_entity_reconciliation_bundle=upstream,documentary_sources=sources,acquisition_records=acquisitions,document_versions=versions,custody_events=custody,redactions=redactions,segments=segments,authenticity_assessments=assessments,disclosure_records=disclosures,evidence_interpretations=interpretations,snapshots=[snapshot])


def contract_document() -> dict[str, Any]:
    b=reference_public_record_documentary_source_bundle()
    return {
        "ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
        "extends_contracts":[
            "sc.core.cross-source-entity-reconciliation-identity-provenance.v1",
            "sc.core.entity-resolution-identity-graph-foundation.v1",
            "sc.core.evidence-graph-neural-analysis-validation.v1",
        ],
        "object_types":[
            "DocumentarySourceDescriptor","DocumentAcquisitionRecord","DocumentVersionRecord","DocumentCustodyEvent","DocumentRedactionRecord","DocumentSegmentAnchor","DocumentAuthenticityAssessment","PublicRecordDisclosureRecord","DocumentaryEvidenceInterpretation","DocumentarySourceSnapshot","PublicRecordDocumentarySourceBundle"
        ],
        "principles":{
            "document_existence_is_not_claim_truth":True,
            "document_authenticity_is_not_content_truth":True,
            "document_content_is_not_self_interpreting_evidence":True,
            "derived_text_is_not_original_source":True,
            "redaction_is_not_evidence_of_wrongdoing":True,
            "withheld_or_absent_material_is_not_proof":True,
            "redacted_content_must_not_be_inferred":True,
            "source_and_derivative_lineage_must_be_preserved":True,
        },
        "capabilities":{
            "public_record_and_documentary_source_descriptors":True,
            "acquisition_provenance_and_content_hashes":True,
            "original_and_derivative_version_lineage":True,
            "append_only_document_custody_events":True,
            "redaction_provenance":True,
            "page_line_and_timestamp_segment_anchors":True,
            "authenticity_assessment_without_truth_promotion":True,
            "public_record_disclosure_lineage":True,
            "documentary_evidence_interpretation_layer":True,
            "immutable_documentary_snapshots":True,
            "deterministic_object_fingerprints":True,
        },
        "boundaries":{
            "core_fetches_or_scrapes_public_records":False,
            "core_performs_ocr_or_transcription":False,
            "core_infers_redacted_or_missing_content":False,
            "core_treats_authenticity_as_content_truth":False,
            "core_treats_document_existence_as_claim_truth":False,
            "core_treats_redaction_as_wrongdoing":False,
            "core_determines_legal_admissibility":False,
            "core_determines_authorship_or_credibility":False,
            "core_mutates_evidence_graph_during_document_ingest":False,
            "core_mutates_identity_graph_during_document_ingest":False,
        },
        "roadmap_integration":{
            "extends_v3800_cross_source_entity_reconciliation":True,
            "prepares_v3820_relationship_discovery_connection_hypotheses":True,
            "prepares_v3840_explainable_connection_paths_evidence_chains":True,
            "prepares_v3880_reproducible_graph_investigation_package":True,
            "preserves_v3760_evidence_validation_boundary":True,
        },
        "reference":{
            "documentary_source_count":len(b.documentary_sources),
            "acquisition_record_count":len(b.acquisition_records),
            "document_version_count":len(b.document_versions),
            "custody_event_count":len(b.custody_events),
            "redaction_count":len(b.redactions),
            "segment_count":len(b.segments),
            "authenticity_assessment_count":len(b.authenticity_assessments),
            "disclosure_record_count":len(b.disclosure_records),
            "evidence_interpretation_count":len(b.evidence_interpretations),
            "document_existence_is_claim_truth":False,
            "document_authenticity_is_content_truth":False,
            "redaction_is_wrongdoing":False,
            "hidden_or_missing_content_inferred":False,
            "evidence_graph_mutation_performed":False,
            "identity_graph_mutation_performed":False,
            "bundle_fingerprint_sha256":b.fingerprint(),
        },
        "database_migration":"none",
    }
