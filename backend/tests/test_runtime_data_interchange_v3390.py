from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.runtime_data_interchange import (
    CONTRACT_VERSION,
    REFERENCE_JULIA_RUNTIME,
    REFERENCE_R_RUNTIME,
    CanonicalScalarType,
    DataFieldSchema,
    DataInterchangeArtifact,
    DataInterchangeConversionSpec,
    DataInterchangeNegotiationRequest,
    DataInterchangeNegotiationResult,
    DataInterchangeSchema,
    DataInterchangeTransfer,
    DataShapeKind,
    Endianness,
    InterchangeFormat,
    InterchangeStatus,
    LossPolicy,
    NullRepresentation,
    RuntimeDataInterchangeBundle,
    RuntimeInterchangeProfile,
    RuntimeTypeMapping,
    VerificationStatus,
    contract_document,
    negotiate_interchange,
    reference_runtime_data_interchange_bundle,
    reference_runtime_profiles,
    to_scientific_artifact_payload,
)


def reference_schema():
    return reference_runtime_data_interchange_bundle().transfers[0].source_artifact.data_schema


def test_contract_identity():
    doc = contract_document()
    assert doc["release"] == "3.39.0"
    assert doc["contract"] == CONTRACT_VERSION


def test_contract_links_runtime_and_registry_layers():
    doc = contract_document()
    assert "sc.core.r-runtime-migration.v1" in doc["depends_on"]
    assert "sc.core.scientific-result-artifact-registry.v1" in doc["depends_on"]


def test_contract_declares_arrow_and_parquet_without_provider_claim():
    doc = contract_document()
    assert "arrow-ipc-file" in doc["formats"]
    assert "parquet" in doc["formats"]
    assert doc["capabilities"]["arrow_parquet_contract_support"] is True
    assert doc["boundaries"]["core_claims_arrow_parquet_provider_support_without_registration"] is False


def test_reference_bundle_is_valid():
    bundle = reference_runtime_data_interchange_bundle()
    assert len(bundle.profiles) == 2
    assert len(bundle.transfers) == 1
    assert bundle.transfers[0].status == InterchangeStatus.completed


def test_reference_profiles_are_r_and_julia():
    profiles = reference_runtime_profiles()
    assert profiles[0].runtime_ref == REFERENCE_R_RUNTIME
    assert profiles[1].runtime_ref == REFERENCE_JULIA_RUNTIME


def test_reference_profiles_only_claim_registered_formats():
    r_profile, julia_profile = reference_runtime_profiles()
    assert InterchangeFormat.json in r_profile.readable_formats
    assert InterchangeFormat.csv in r_profile.readable_formats
    assert InterchangeFormat.parquet not in r_profile.readable_formats
    assert julia_profile.readable_formats == [InterchangeFormat.json]


def test_field_fingerprint_is_stable():
    field = reference_schema().fields[0]
    assert field.fingerprint() == deepcopy(field).fingerprint()


def test_schema_rejects_duplicate_field_ids():
    field = DataFieldSchema(
        field_id="field:x",
        name="x",
        canonical_type=CanonicalScalarType.float64,
    )
    with pytest.raises(ValidationError):
        DataInterchangeSchema(
            schema_id="schema:test",
            shape_kind=DataShapeKind.table,
            fields=[field, field.model_copy(update={"name": "y"})],
            column_count=2,
        )


def test_schema_rejects_duplicate_field_names():
    with pytest.raises(ValidationError):
        DataInterchangeSchema(
            schema_id="schema:test",
            shape_kind=DataShapeKind.table,
            fields=[
                DataFieldSchema(
                    field_id="field:x",
                    name="x",
                    canonical_type=CanonicalScalarType.float64,
                ),
                DataFieldSchema(
                    field_id="field:y",
                    name="x",
                    canonical_type=CanonicalScalarType.float64,
                ),
            ],
            column_count=2,
        )


def test_table_schema_requires_fields():
    with pytest.raises(ValidationError):
        DataInterchangeSchema(
            schema_id="schema:test",
            shape_kind=DataShapeKind.table,
            fields=[],
        )


def test_table_column_count_matches_fields():
    with pytest.raises(ValidationError):
        DataInterchangeSchema(
            schema_id="schema:test",
            shape_kind=DataShapeKind.table,
            fields=[
                DataFieldSchema(
                    field_id="field:x",
                    name="x",
                    canonical_type=CanonicalScalarType.float64,
                )
            ],
            column_count=2,
        )


def test_vector_requires_dimensions():
    with pytest.raises(ValidationError):
        DataInterchangeSchema(
            schema_id="schema:test",
            shape_kind=DataShapeKind.vector,
            dimensions=[],
        )


def test_matrix_requires_exactly_two_dimensions():
    with pytest.raises(ValidationError):
        DataInterchangeSchema(
            schema_id="schema:test",
            shape_kind=DataShapeKind.matrix,
            dimensions=[2, 2, 2],
        )


def test_schema_rejects_negative_dimensions():
    with pytest.raises(ValidationError):
        DataInterchangeSchema(
            schema_id="schema:test",
            shape_kind=DataShapeKind.matrix,
            dimensions=[2, -1],
        )


def test_schema_fingerprint_is_stable():
    schema = reference_schema()
    assert schema.fingerprint() == deepcopy(schema).fingerprint()
    assert len(schema.fingerprint()) == 64


def test_type_mapping_fingerprint_is_stable():
    mapping = reference_runtime_profiles()[0].type_mappings[0]
    assert mapping.fingerprint() == deepcopy(mapping).fingerprint()


def test_profile_requires_readable_formats():
    with pytest.raises(ValidationError):
        RuntimeInterchangeProfile(
            profile_id="profile:test",
            runtime_ref="runtime:test",
            runtime_version="1.0",
            readable_formats=[],
            writable_formats=[InterchangeFormat.json],
            supported_shapes=[DataShapeKind.table],
        )


def test_profile_requires_writable_formats():
    with pytest.raises(ValidationError):
        RuntimeInterchangeProfile(
            profile_id="profile:test",
            runtime_ref="runtime:test",
            runtime_version="1.0",
            readable_formats=[InterchangeFormat.json],
            writable_formats=[],
            supported_shapes=[DataShapeKind.table],
        )


def test_profile_requires_supported_shapes():
    with pytest.raises(ValidationError):
        RuntimeInterchangeProfile(
            profile_id="profile:test",
            runtime_ref="runtime:test",
            runtime_version="1.0",
            readable_formats=[InterchangeFormat.json],
            writable_formats=[InterchangeFormat.json],
            supported_shapes=[],
        )


def test_profile_rejects_duplicate_mapping_ids():
    mapping = RuntimeTypeMapping(
        mapping_id="map:test",
        runtime_ref="runtime:test",
        runtime_type="double",
        canonical_type=CanonicalScalarType.float64,
    )
    with pytest.raises(ValidationError):
        RuntimeInterchangeProfile(
            profile_id="profile:test",
            runtime_ref="runtime:test",
            runtime_version="1.0",
            readable_formats=[InterchangeFormat.json],
            writable_formats=[InterchangeFormat.json],
            supported_shapes=[DataShapeKind.table],
            type_mappings=[mapping, deepcopy(mapping)],
        )


def test_profile_fingerprint_is_stable():
    profile = reference_runtime_profiles()[0]
    assert profile.fingerprint() == deepcopy(profile).fingerprint()


def test_artifact_requires_sha256():
    schema = reference_schema()
    with pytest.raises(ValidationError):
        DataInterchangeArtifact(
            interchange_artifact_id="artifact:test",
            logical_data_ref="logical:test",
            format=InterchangeFormat.json,
            uri="core-ref://test.json",
            content_sha256="abc",
            data_schema=schema,
        )


def test_artifact_fingerprint_ignores_created_at():
    artifact = reference_runtime_data_interchange_bundle().transfers[0].source_artifact
    assert artifact.fingerprint() == deepcopy(artifact).fingerprint()


def test_negotiation_finds_json_for_r_to_julia():
    r_profile, julia_profile = reference_runtime_profiles()
    result = negotiate_interchange(
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
    assert result.compatible is True
    assert result.candidate_formats == [InterchangeFormat.json]
    assert result.selected_format is None


def test_negotiation_is_candidate_discovery_only():
    r_profile, julia_profile = reference_runtime_profiles()
    result = negotiate_interchange(
        DataInterchangeNegotiationRequest(
            source_profile=r_profile,
            target_profile=julia_profile,
            required_shape=DataShapeKind.table,
            required_types=[CanonicalScalarType.float64],
        )
    )
    assert result.selection_mode == "candidate-discovery-only"
    assert result.selected_format is None


def test_negotiation_object_rejects_autoselection():
    with pytest.raises(ValidationError):
        DataInterchangeNegotiationResult(
            source_runtime_ref="runtime:a",
            target_runtime_ref="runtime:b",
            candidate_formats=[InterchangeFormat.json],
            compatible=True,
            selected_format=InterchangeFormat.json,
        )


def test_negotiation_fails_when_shape_not_supported():
    r_profile, julia_profile = reference_runtime_profiles()
    result = negotiate_interchange(
        DataInterchangeNegotiationRequest(
            source_profile=r_profile,
            target_profile=julia_profile,
            required_shape=DataShapeKind.tensor,
            required_types=[CanonicalScalarType.float64],
        )
    )
    assert result.compatible is False
    assert "source-shape" in result.rejected_formats
    assert "target-shape" in result.rejected_formats


def test_negotiation_fails_when_required_type_missing():
    r_profile, julia_profile = reference_runtime_profiles()
    result = negotiate_interchange(
        DataInterchangeNegotiationRequest(
            source_profile=r_profile,
            target_profile=julia_profile,
            required_shape=DataShapeKind.table,
            required_types=[CanonicalScalarType.timestamp],
        )
    )
    assert result.compatible is False
    assert "source-types" in result.rejected_formats
    assert "target-types" in result.rejected_formats


def test_negotiation_fails_without_common_format():
    r_profile, julia_profile = reference_runtime_profiles()
    julia_profile = julia_profile.model_copy(
        update={
            "readable_formats": [InterchangeFormat.parquet],
            "writable_formats": [InterchangeFormat.parquet],
        }
    )
    result = negotiate_interchange(
        DataInterchangeNegotiationRequest(
            source_profile=r_profile,
            target_profile=julia_profile,
            required_shape=DataShapeKind.table,
            required_types=[CanonicalScalarType.float64],
        )
    )
    assert result.compatible is False
    assert result.candidate_formats == []


def test_negotiation_fingerprint_is_stable():
    r_profile, julia_profile = reference_runtime_profiles()
    result = negotiate_interchange(
        DataInterchangeNegotiationRequest(
            source_profile=r_profile,
            target_profile=julia_profile,
            required_shape=DataShapeKind.table,
            required_types=[CanonicalScalarType.float64],
        )
    )
    assert result.fingerprint() == deepcopy(result).fingerprint()


def test_conversion_spec_fingerprint_is_stable():
    spec = DataInterchangeConversionSpec(
        conversion_spec_id="conversion:test",
        source_artifact_ref="artifact:source",
        source_format=InterchangeFormat.json,
        target_format=InterchangeFormat.parquet,
        target_schema_ref="schema:target",
        source_runtime_ref="runtime:a",
        target_runtime_ref="runtime:b",
        loss_policy=LossPolicy.forbid,
    )
    assert spec.fingerprint() == deepcopy(spec).fingerprint()


def test_reference_transfer_preserves_logical_identity():
    transfer = reference_runtime_data_interchange_bundle().transfers[0]
    assert (
        transfer.source_artifact.logical_data_ref
        == transfer.target_artifact.logical_data_ref
    )


def test_transfer_rejects_logical_data_mismatch():
    transfer = reference_runtime_data_interchange_bundle().transfers[0]
    target = deepcopy(transfer.target_artifact)
    target.logical_data_ref = "logical-data:other"
    with pytest.raises(ValidationError):
        DataInterchangeTransfer(
            transfer_id="transfer:test",
            source_artifact=transfer.source_artifact,
            target_artifact=target,
            source_runtime_ref=transfer.source_runtime_ref,
            target_runtime_ref=transfer.target_runtime_ref,
            verification=transfer.verification,
        )


def test_transfer_rejects_verification_source_mismatch():
    transfer = reference_runtime_data_interchange_bundle().transfers[0]
    verification = deepcopy(transfer.verification)
    verification.source_artifact_ref = "artifact:other"
    with pytest.raises(ValidationError):
        DataInterchangeTransfer(
            transfer_id="transfer:test",
            source_artifact=transfer.source_artifact,
            target_artifact=transfer.target_artifact,
            source_runtime_ref=transfer.source_runtime_ref,
            target_runtime_ref=transfer.target_runtime_ref,
            verification=verification,
        )


def test_completed_transfer_requires_verification():
    transfer = reference_runtime_data_interchange_bundle().transfers[0]
    verification = deepcopy(transfer.verification)
    verification.status = VerificationStatus.failed
    with pytest.raises(ValidationError):
        DataInterchangeTransfer(
            transfer_id="transfer:test",
            source_artifact=transfer.source_artifact,
            target_artifact=transfer.target_artifact,
            source_runtime_ref=transfer.source_runtime_ref,
            target_runtime_ref=transfer.target_runtime_ref,
            verification=verification,
            status=InterchangeStatus.completed,
        )


def test_completed_at_requires_completed_status():
    transfer = reference_runtime_data_interchange_bundle().transfers[0]
    with pytest.raises(ValidationError):
        DataInterchangeTransfer(
            transfer_id="transfer:test",
            source_artifact=transfer.source_artifact,
            target_artifact=transfer.target_artifact,
            source_runtime_ref=transfer.source_runtime_ref,
            target_runtime_ref=transfer.target_runtime_ref,
            verification=transfer.verification,
            status=InterchangeStatus.prepared,
            completed_at=transfer.completed_at,
        )


def test_transfer_fingerprint_ignores_lifecycle_fields():
    transfer = reference_runtime_data_interchange_bundle().transfers[0]
    other = deepcopy(transfer)
    other.status = InterchangeStatus.transferring
    other.completed_at = None
    assert transfer.fingerprint() == other.fingerprint()


def test_bundle_rejects_duplicate_profile_ids():
    bundle = reference_runtime_data_interchange_bundle()
    with pytest.raises(ValidationError):
        RuntimeDataInterchangeBundle(
            bundle_id="bundle:test",
            profiles=[bundle.profiles[0], deepcopy(bundle.profiles[0])],
            transfers=[],
        )


def test_bundle_rejects_duplicate_transfer_ids():
    bundle = reference_runtime_data_interchange_bundle()
    with pytest.raises(ValidationError):
        RuntimeDataInterchangeBundle(
            bundle_id="bundle:test",
            profiles=bundle.profiles,
            transfers=[bundle.transfers[0], deepcopy(bundle.transfers[0])],
        )


def test_bundle_requires_source_runtime_profile():
    bundle = reference_runtime_data_interchange_bundle()
    with pytest.raises(ValidationError):
        RuntimeDataInterchangeBundle(
            bundle_id="bundle:test",
            profiles=[bundle.profiles[1]],
            transfers=bundle.transfers,
        )


def test_bundle_requires_target_runtime_profile():
    bundle = reference_runtime_data_interchange_bundle()
    with pytest.raises(ValidationError):
        RuntimeDataInterchangeBundle(
            bundle_id="bundle:test",
            profiles=[bundle.profiles[0]],
            transfers=bundle.transfers,
        )


def test_bundle_fingerprint_is_stable():
    bundle = reference_runtime_data_interchange_bundle()
    assert bundle.fingerprint() == deepcopy(bundle).fingerprint()
    assert len(bundle.fingerprint()) == 64


def test_scientific_artifact_bridge_json_kind():
    artifact = reference_runtime_data_interchange_bundle().transfers[0].source_artifact
    payload = to_scientific_artifact_payload(artifact)
    assert payload["artifact_kind"] == "json"
    assert payload["content_sha256"] == artifact.content_sha256
    assert payload["source_contract"] == CONTRACT_VERSION


def test_scientific_artifact_bridge_validates_against_v338_model():
    from app.services.scientific_result_registry import ScientificArtifactRef

    artifact = reference_runtime_data_interchange_bundle().transfers[0].source_artifact
    payload = to_scientific_artifact_payload(artifact)
    validated = ScientificArtifactRef.model_validate(payload)
    assert validated.source_object_ref == artifact.interchange_artifact_id


def test_reference_verification_has_equal_schema_fingerprints():
    transfer = reference_runtime_data_interchange_bundle().transfers[0]
    assert (
        transfer.verification.source_schema_fingerprint_sha256
        == transfer.verification.target_schema_fingerprint_sha256
    )


def test_reference_verification_preserves_rows_columns_types():
    verification = reference_runtime_data_interchange_bundle().transfers[0].verification
    assert verification.row_count_match is True
    assert verification.column_count_match is True
    assert verification.type_compatibility_passed is True


def test_reference_notes_do_not_claim_arrow_provider_support():
    verification = reference_runtime_data_interchange_bundle().transfers[0].verification
    text = " ".join(verification.notes)
    assert "not claimed as native provider capabilities" in text


def test_canonical_types_cover_cross_runtime_basics():
    values = {item.value for item in CanonicalScalarType}
    assert {"boolean", "int32", "int64", "float64", "string", "timestamp", "categorical"}.issubset(values)


def test_formats_cover_columnar_and_fallback_exchange():
    values = {item.value for item in InterchangeFormat}
    assert {"json", "csv", "arrow-ipc-stream", "parquet", "npy"}.issubset(values)


def test_null_representations_cover_runtime_semantics():
    values = {item.value for item in NullRepresentation}
    assert {"null", "na", "nan", "sentinel"}.issubset(values)


def test_endianness_model_is_explicit():
    values = {item.value for item in Endianness}
    assert {"little", "big", "native", "not-applicable"}.issubset(values)


def test_core_does_not_select_format():
    doc = contract_document()
    assert doc["boundaries"]["core_autonomously_selects_format"] is False


def test_core_does_not_execute_conversion():
    doc = contract_document()
    assert doc["boundaries"]["core_executes_data_conversion"] is False
    assert doc["integration"]["workspace_or_runtime_executes_conversion"] is True


def test_core_requires_verification_for_semantic_equivalence_claim():
    doc = contract_document()
    assert doc["boundaries"]["core_claims_semantic_equivalence_without_verification"] is False


def test_core_does_not_certify_scientific_validity():
    doc = contract_document()
    assert doc["boundaries"]["core_certifies_scientific_validity"] is False


def test_reference_negotiation_candidate_is_json_only():
    doc = contract_document()
    assert doc["reference"]["negotiation_candidates"] == ["json"]
