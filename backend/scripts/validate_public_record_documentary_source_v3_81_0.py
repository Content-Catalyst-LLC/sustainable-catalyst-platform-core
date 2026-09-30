from app.services.public_record_documentary_source import (
    CONTRACT_VERSION,
    contract_document,
    reference_public_record_documentary_source_bundle,
)

b = reference_public_record_documentary_source_bundle()
c = contract_document()
assert c["contract"] == CONTRACT_VERSION
assert c["release"] == "3.81.0"
assert len(b.documentary_sources) == 2
assert len(b.acquisition_records) == 2
assert len(b.document_versions) == 4
assert len(b.custody_events) == 4
assert len(b.redactions) == 1
assert len(b.segments) == 3
assert len(b.authenticity_assessments) == 2
assert len(b.disclosure_records) == 1
assert len(b.evidence_interpretations) == 2
assert b.document_existence_is_not_claim_truth is True
assert b.document_authenticity_is_not_content_truth is True
assert b.redaction_is_not_wrongdoing is True
assert b.hidden_or_missing_content_is_not_inferred is True
assert b.evidence_graph_mutation_performed is False
assert b.identity_graph_mutation_performed is False
assert c["boundaries"]["core_infers_redacted_or_missing_content"] is False
assert c["boundaries"]["core_treats_authenticity_as_content_truth"] is False
print("PASS - Platform Core v3.81.0 Public Record & Documentary Source Object Model")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"DOCUMENTARY_SOURCES={len(b.documentary_sources)}")
print(f"ACQUISITIONS={len(b.acquisition_records)}")
print(f"DOCUMENT_VERSIONS={len(b.document_versions)}")
print(f"CUSTODY_EVENTS={len(b.custody_events)}")
print(f"REDACTIONS={len(b.redactions)}")
print(f"SEGMENTS={len(b.segments)}")
print(f"AUTHENTICITY_ASSESSMENTS={len(b.authenticity_assessments)}")
print(f"EVIDENCE_INTERPRETATIONS={len(b.evidence_interpretations)}")
print("DOCUMENT_EXISTENCE_IS_CLAIM_TRUTH=false")
print("DOCUMENT_AUTHENTICITY_IS_CONTENT_TRUTH=false")
print("REDACTION_IS_WRONGDOING=false")
print("HIDDEN_OR_MISSING_CONTENT_INFERRED=false")
print("EVIDENCE_GRAPH_MUTATION_PERFORMED=false")
print("IDENTITY_GRAPH_MUTATION_PERFORMED=false")
