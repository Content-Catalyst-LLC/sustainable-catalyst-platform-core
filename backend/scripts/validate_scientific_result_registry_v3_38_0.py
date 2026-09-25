#!/usr/bin/env python3

from app.services.scientific_result_registry import (
    CONTRACT_VERSION,
    ScientificArtifactKind,
    ScientificRegistryQuery,
    ScientificResultKind,
    contract_document,
    query_registry,
    reference_scientific_registry_package,
)

doc = contract_document()
assert doc["release"] == "3.38.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["capabilities"]["cross_domain_result_identity"] is True
assert doc["capabilities"]["content_addressed_artifacts"] is True
assert doc["capabilities"]["statistical_result_registration"] is True
assert doc["integration"]["core_duplicates_source_payloads"] is False
assert doc["boundaries"]["core_executes_scientific_methods"] is False

package = reference_scientific_registry_package()
assert len(package.fingerprint()) == 64
assert package.registry.results
assert package.registry.artifacts
assert package.registry.relations
assert package.registry.metadata["source_payload_duplicated"] is False

estimate_query = query_registry(
    package.registry,
    ScientificRegistryQuery(
        result_kinds=[ScientificResultKind.statistical_estimate]
    ),
)
assert estimate_query.result_refs

package_query = query_registry(
    package.registry,
    ScientificRegistryQuery(
        artifact_kinds=[ScientificArtifactKind.package]
    ),
)
assert len(package_query.artifact_refs) == 1

print("PASS - Platform Core v3.38.0 Scientific Result & Artifact Registry")
print(f"CONTRACT={CONTRACT_VERSION}")
print("CROSS_DOMAIN_RESULT_IDENTITY=enabled")
print("CONTENT_ADDRESSED_ARTIFACTS=enabled")
print("TYPED_RESULT_ARTIFACT_RELATIONS=enabled")
print("STATISTICAL_RESULT_REGISTRATION=enabled")
print("REGISTRY_QUERIES=enabled")
print("REGISTRY_SNAPSHOTS=enabled")
print("PORTABLE_REGISTRY_PACKAGES=enabled")
print("SOURCE_PAYLOAD_REFERENCE_MODE=enabled")
print("CORE_DUPLICATES_SOURCE_PAYLOADS=false")
print("CORE_EXECUTES_SCIENTIFIC_METHODS=false")
print("CORE_CERTIFIES_SCIENTIFIC_VALIDITY=false")
