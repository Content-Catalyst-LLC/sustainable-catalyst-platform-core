from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.scientific_result_registry import (
    CONTRACT_VERSION,
    ScientificArtifactKind,
    ScientificArtifactRef,
    ScientificRegistryPackage,
    ScientificRegistryQuery,
    ScientificRegistryRelation,
    ScientificRegistrySnapshot,
    ScientificRegistryState,
    ScientificRelationType,
    ScientificResultArtifactRegistry,
    ScientificResultKind,
    ScientificResultRef,
    contract_document,
    query_registry,
    reference_scientific_registry_package,
    register_statistical_analysis_package,
)
from app.services.statistical_analysis_objects import reference_statistical_analysis_package


def test_contract_identity():
    doc = contract_document()
    assert doc["release"] == "3.38.0"
    assert doc["contract"] == CONTRACT_VERSION


def test_reference_package_is_valid():
    package = reference_scientific_registry_package()
    assert package.registry.results
    assert package.registry.artifacts
    assert package.registry.relations


def test_reference_registers_statistical_results():
    package = reference_scientific_registry_package()
    kinds = {item.result_kind for item in package.registry.results}
    assert ScientificResultKind.statistical_estimate in kinds
    assert ScientificResultKind.model_fit in kinds


def test_reference_contains_portable_statistical_package_artifact():
    package = reference_scientific_registry_package()
    packages = [
        item for item in package.registry.artifacts
        if item.artifact_kind == ScientificArtifactKind.package
    ]
    assert len(packages) == 1


def test_result_ref_sha256_validation():
    with pytest.raises(ValidationError):
        ScientificResultRef(
            result_id="result:test",
            result_kind=ScientificResultKind.finding,
            source_contract="contract:test",
            source_object_ref="object:test",
            fingerprint_sha256="bad",
        )


def test_result_ref_fingerprint_ignores_state():
    item = reference_scientific_registry_package().registry.results[0]
    other = deepcopy(item)
    other.state = ScientificRegistryState.archived
    assert item.fingerprint() == other.fingerprint()


def test_artifact_sha256_validation():
    with pytest.raises(ValidationError):
        ScientificArtifactRef(
            artifact_id="artifact:test",
            artifact_kind=ScientificArtifactKind.json,
            uri="core-ref://artifact:test",
            content_sha256="abc",
        )


def test_artifact_fingerprint_ignores_state():
    item = reference_scientific_registry_package().registry.artifacts[0]
    other = deepcopy(item)
    other.state = ScientificRegistryState.archived
    assert item.fingerprint() == other.fingerprint()


def test_relation_rejects_self_reference():
    with pytest.raises(ValidationError):
        ScientificRegistryRelation(
            relation_id="relation:test",
            source_ref="result:test",
            target_ref="result:test",
            relation_type=ScientificRelationType.supports,
        )


def test_relation_fingerprint_is_stable():
    relation = reference_scientific_registry_package().registry.relations[0]
    assert relation.fingerprint() == deepcopy(relation).fingerprint()


def test_registry_rejects_duplicate_result_ids():
    package = reference_scientific_registry_package()
    item = package.registry.results[0]
    with pytest.raises(ValidationError):
        ScientificResultArtifactRegistry(
            registry_id="registry:test",
            results=[item, deepcopy(item)],
            artifacts=package.registry.artifacts,
            relations=[],
        )


def test_registry_rejects_duplicate_artifact_ids():
    package = reference_scientific_registry_package()
    item = package.registry.artifacts[0]
    with pytest.raises(ValidationError):
        ScientificResultArtifactRegistry(
            registry_id="registry:test",
            results=package.registry.results,
            artifacts=[item, deepcopy(item)],
            relations=[],
        )


def test_registry_rejects_duplicate_relation_ids():
    package = reference_scientific_registry_package()
    relation = package.registry.relations[0]
    with pytest.raises(ValidationError):
        ScientificResultArtifactRegistry(
            registry_id="registry:test",
            results=package.registry.results,
            artifacts=package.registry.artifacts,
            relations=[relation, deepcopy(relation)],
        )


def test_registry_rejects_unknown_relation_source():
    package = reference_scientific_registry_package()
    relation = deepcopy(package.registry.relations[0])
    relation.source_ref = "result:missing"
    with pytest.raises(ValidationError):
        ScientificResultArtifactRegistry(
            registry_id="registry:test",
            results=package.registry.results,
            artifacts=package.registry.artifacts,
            relations=[relation],
        )


def test_registry_rejects_unknown_relation_target():
    package = reference_scientific_registry_package()
    relation = deepcopy(package.registry.relations[0])
    relation.target_ref = "artifact:missing"
    with pytest.raises(ValidationError):
        ScientificResultArtifactRegistry(
            registry_id="registry:test",
            results=package.registry.results,
            artifacts=package.registry.artifacts,
            relations=[relation],
        )


def test_registry_fingerprint_is_stable():
    registry = reference_scientific_registry_package().registry
    assert registry.fingerprint() == deepcopy(registry).fingerprint()
    assert len(registry.fingerprint()) == 64


def test_query_by_result_kind():
    registry = reference_scientific_registry_package().registry
    query = ScientificRegistryQuery(
        result_kinds=[ScientificResultKind.statistical_estimate]
    )
    result = query_registry(registry, query)
    assert result.result_refs
    assert all("scientific-result:" in ref for ref in result.result_refs)


def test_query_by_artifact_kind():
    registry = reference_scientific_registry_package().registry
    result = query_registry(
        registry,
        ScientificRegistryQuery(
            artifact_kinds=[ScientificArtifactKind.package]
        ),
    )
    assert len(result.artifact_refs) == 1


def test_query_by_source_contract():
    registry = reference_scientific_registry_package().registry
    result = query_registry(
        registry,
        ScientificRegistryQuery(
            source_contracts=["sc.core.statistical-analysis-object.v1"]
        ),
    )
    assert result.result_refs
    assert result.artifact_refs


def test_query_by_source_object():
    registry = reference_scientific_registry_package().registry
    source_ref = registry.results[0].source_object_ref
    result = query_registry(
        registry,
        ScientificRegistryQuery(source_object_refs=[source_ref]),
    )
    assert registry.results[0].result_id in result.result_refs


def test_query_by_state():
    registry = reference_scientific_registry_package().registry
    result = query_registry(
        registry,
        ScientificRegistryQuery(state=ScientificRegistryState.registered),
    )
    assert len(result.result_refs) == len(registry.results)


def test_query_fingerprint_is_stable():
    registry = reference_scientific_registry_package().registry
    result = query_registry(registry, ScientificRegistryQuery())
    assert result.fingerprint() == deepcopy(result).fingerprint()


def test_snapshot_fingerprint_is_stable():
    snapshot = reference_scientific_registry_package().snapshot
    assert snapshot.fingerprint() == deepcopy(snapshot).fingerprint()


def test_package_rejects_registry_ref_mismatch():
    package = reference_scientific_registry_package()
    snapshot = deepcopy(package.snapshot)
    snapshot.registry_ref = "registry:other"
    with pytest.raises(ValidationError):
        ScientificRegistryPackage(
            package_id="package:test",
            registry=package.registry,
            snapshot=snapshot,
        )


def test_package_rejects_registry_fingerprint_mismatch():
    package = reference_scientific_registry_package()
    snapshot = deepcopy(package.snapshot)
    snapshot.registry_fingerprint_sha256 = "f" * 64
    with pytest.raises(ValidationError):
        ScientificRegistryPackage(
            package_id="package:test",
            registry=package.registry,
            snapshot=snapshot,
        )


def test_package_rejects_unknown_selected_result():
    package = reference_scientific_registry_package()
    snapshot = deepcopy(package.snapshot)
    snapshot.selected_result_refs.append("result:missing")
    with pytest.raises(ValidationError):
        ScientificRegistryPackage(
            package_id="package:test",
            registry=package.registry,
            snapshot=snapshot,
        )


def test_package_rejects_unknown_selected_artifact():
    package = reference_scientific_registry_package()
    snapshot = deepcopy(package.snapshot)
    snapshot.selected_artifact_refs.append("artifact:missing")
    with pytest.raises(ValidationError):
        ScientificRegistryPackage(
            package_id="package:test",
            registry=package.registry,
            snapshot=snapshot,
        )


def test_package_rejects_unknown_selected_relation():
    package = reference_scientific_registry_package()
    snapshot = deepcopy(package.snapshot)
    snapshot.selected_relation_refs.append("relation:missing")
    with pytest.raises(ValidationError):
        ScientificRegistryPackage(
            package_id="package:test",
            registry=package.registry,
            snapshot=snapshot,
        )


def test_package_fingerprint_is_stable():
    package = reference_scientific_registry_package()
    assert package.fingerprint() == deepcopy(package).fingerprint()
    assert len(package.fingerprint()) == 64


def test_statistical_registration_is_reference_only():
    package = reference_scientific_registry_package()
    assert package.registry.metadata["source_payload_duplicated"] is False
    assert package.registry.metadata["registry_mode"] == "reference-and-fingerprint"


def test_statistical_registration_preserves_source_contract():
    package = reference_scientific_registry_package()
    assert all(
        item.source_contract == "sc.core.statistical-analysis-object.v1"
        for item in package.registry.results
    )


def test_statistical_registration_relates_results_to_package():
    package = reference_scientific_registry_package()
    package_artifact_ids = {
        item.artifact_id
        for item in package.registry.artifacts
        if item.artifact_kind == ScientificArtifactKind.package
    }
    assert package_artifact_ids
    assert all(
        relation.target_ref in package_artifact_ids
        for relation in package.registry.relations
    )


def test_registration_from_reference_statistical_package():
    statistical = reference_statistical_analysis_package()
    registry = register_statistical_analysis_package(
        analysis_package=statistical.model_dump(mode="json", exclude_none=True)
    )
    assert len(registry.results) == 6
    assert len(registry.artifacts) == 1
    assert len(registry.relations) == 6


def test_registration_estimate_fingerprints_match_source_payload():
    statistical = reference_statistical_analysis_package()
    payload = statistical.model_dump(mode="json", exclude_none=True)
    registry = register_statistical_analysis_package(analysis_package=payload)
    estimate = payload["results"][0]["estimates"][0]
    result = [
        item for item in registry.results
        if item.source_object_ref == estimate["estimate_id"]
    ][0]
    from app.services.computational_runtime_objects import canonical_sha256
    assert result.fingerprint_sha256 == canonical_sha256(estimate)


def test_result_kinds_cover_future_scientific_domains():
    values = {item.value for item in ScientificResultKind}
    assert {"forecast", "causal-estimate", "simulation", "calibration", "robustness"}.issubset(values)


def test_artifact_kinds_cover_research_outputs():
    values = {item.value for item in ScientificArtifactKind}
    assert {"table", "figure", "dataset", "model", "notebook", "publication", "parquet"}.issubset(values)


def test_contract_supports_cross_domain_registry():
    doc = contract_document()
    assert doc["capabilities"]["cross_domain_result_identity"] is True
    assert doc["capabilities"]["content_addressed_artifacts"] is True


def test_core_does_not_duplicate_source_payloads():
    doc = contract_document()
    assert doc["integration"]["core_duplicates_source_payloads"] is False
    assert doc["capabilities"]["source_payload_reference_mode"] is True


def test_core_does_not_execute_science():
    doc = contract_document()
    assert doc["boundaries"]["core_executes_scientific_methods"] is False


def test_core_does_not_modify_source_artifacts():
    doc = contract_document()
    assert doc["boundaries"]["core_modifies_source_artifacts"] is False


def test_core_does_not_certify_validity_or_truth():
    doc = contract_document()
    assert doc["boundaries"]["core_certifies_scientific_validity"] is False
    assert doc["boundaries"]["core_interprets_results_as_truth"] is False
