#!/usr/bin/env python3

from app.services.runtime_data_interchange import (
    CONTRACT_VERSION,
    CanonicalScalarType,
    DataInterchangeNegotiationRequest,
    DataShapeKind,
    InterchangeFormat,
    VerificationStatus,
    contract_document,
    negotiate_interchange,
    reference_runtime_data_interchange_bundle,
    to_scientific_artifact_payload,
)
from app.services.scientific_result_registry import ScientificArtifactRef

doc = contract_document()
assert doc["release"] == "3.39.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["capabilities"]["canonical_data_types"] is True
assert doc["capabilities"]["runtime_type_mappings"] is True
assert doc["capabilities"]["format_candidate_discovery"] is True
assert doc["capabilities"]["arrow_parquet_contract_support"] is True
assert doc["boundaries"]["core_autonomously_selects_format"] is False
assert doc["boundaries"]["core_executes_data_conversion"] is False

bundle = reference_runtime_data_interchange_bundle()
assert len(bundle.profiles) == 2
assert len(bundle.transfers) == 1
assert len(bundle.fingerprint()) == 64

r_profile, julia_profile = bundle.profiles
negotiation = negotiate_interchange(
    DataInterchangeNegotiationRequest(
        source_profile=r_profile,
        target_profile=julia_profile,
        required_shape=DataShapeKind.table,
        required_types=[CanonicalScalarType.float64],
        preferred_formats=[
            InterchangeFormat.arrow_ipc_stream,
            InterchangeFormat.parquet,
            InterchangeFormat.json,
        ],
    )
)
assert negotiation.compatible is True
assert negotiation.candidate_formats == [InterchangeFormat.json]
assert negotiation.selected_format is None
assert negotiation.selection_mode == "candidate-discovery-only"

transfer = bundle.transfers[0]
assert transfer.verification.status == VerificationStatus.passed
assert transfer.source_artifact.logical_data_ref == transfer.target_artifact.logical_data_ref
assert transfer.verification.row_count_match is True
assert transfer.verification.column_count_match is True
assert transfer.verification.type_compatibility_passed is True

scientific_payload = to_scientific_artifact_payload(transfer.source_artifact)
ScientificArtifactRef.model_validate(scientific_payload)

print("PASS - Platform Core v3.39.0 Runtime Data Interchange")
print(f"CONTRACT={CONTRACT_VERSION}")
print("CANONICAL_DATA_TYPES=enabled")
print("SHAPE_AWARE_SCHEMAS=enabled")
print("RUNTIME_TYPE_MAPPINGS=enabled")
print("FORMAT_CANDIDATE_DISCOVERY=enabled")
print("JSON_CSV_INTERCHANGE=enabled")
print("ARROW_PARQUET_CONTRACT_SUPPORT=enabled")
print("TRANSFER_VERIFICATION=enabled")
print("SCIENTIFIC_ARTIFACT_BRIDGE=enabled")
print("REFERENCE_R_TO_JULIA_FORMAT=json")
print("CORE_AUTONOMOUSLY_SELECTS_FORMAT=false")
print("CORE_EXECUTES_DATA_CONVERSION=false")
print("CORE_CERTIFIES_SCIENTIFIC_VALIDITY=false")
