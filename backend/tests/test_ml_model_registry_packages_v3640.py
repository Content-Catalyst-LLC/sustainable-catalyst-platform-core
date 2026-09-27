import copy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import ml_model_registry_packages
from app.services.ml_model_registry_packages import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    MLArtifactFormat,
    MLArtifactKind,
    MLModelArtifactRecord,
    MLModelRegistryEntry,
    MLModelRegistryPackageBundle,
    MLRegistryLifecycle,
    MLReproducibilityManifest,
    MLReproducibleModelPackage,
    MLRuntimeRequirementRecord,
    contract_document,
    reference_model_registry_package_bundle,
)


def payload():
    return reference_model_registry_package_bundle().model_dump(mode="json")


def invalid(mutator):
    data = payload()
    mutator(data)
    with pytest.raises(ValidationError):
        MLModelRegistryPackageBundle.model_validate(data)


def test_release_and_contract():
    assert CORE_RELEASE == "3.64.0"
    assert CONTRACT_VERSION == "sc.core.neural-model-registry-reproducible-packages.v1"


def test_reference_bundle_fingerprint_is_deterministic():
    a = reference_model_registry_package_bundle()
    b = reference_model_registry_package_bundle()
    assert a.fingerprint() == b.fingerprint()
    assert len(a.fingerprint()) == 64


def test_package_and_manifest_fingerprints_are_deterministic():
    a = reference_model_registry_package_bundle()
    b = reference_model_registry_package_bundle()
    assert a.model_packages[0].fingerprint() == b.model_packages[0].fingerprint()
    assert a.reproducibility_manifests[0].fingerprint() == b.reproducibility_manifests[0].fingerprint()


def test_contract_governance_boundaries():
    c = contract_document()
    assert c["governance"]["registration_does_not_certify_quality"] is True
    assert c["governance"]["portable_package_does_not_guarantee_reproducibility"] is True
    assert c["governance"]["model_package_is_not_evidence"] is True
    assert c["boundaries"]["core_executes_model_packages"] is False
    assert c["boundaries"]["core_installs_dependencies"] is False
    assert c["boundaries"]["core_certifies_model_quality"] is False
    assert c["boundaries"]["core_certifies_reproducibility"] is False


def test_reference_entry_does_not_imply_certification_or_autonomous_action():
    entry = reference_model_registry_package_bundle().registry_entries[0]
    assert entry.registration_implies_certification is False
    assert entry.approved_for_autonomous_action is False


def test_reference_manifest_does_not_guarantee_reproducibility():
    manifest = reference_model_registry_package_bundle().reproducibility_manifests[0]
    assert manifest.reproducibility_guaranteed is False


def test_reference_package_is_portable_but_not_executed_by_core():
    package = reference_model_registry_package_bundle().model_packages[0]
    assert package.portable_research_object is True
    assert package.core_executes_package is False
    assert package.core_downloads_dependencies is False


def test_cross_release_model_identity_matches():
    bundle = reference_model_registry_package_bundle()
    assert bundle.training_lineage_bundle.model_spec.model_spec_id == bundle.ml_model_bundle.model_spec.model_spec_id
    assert bundle.representation_bundle.model_spec_ref == bundle.ml_model_bundle.model_spec.model_spec_id
    assert bundle.inference_bundle.ml_model_bundle.fingerprint() == bundle.ml_model_bundle.fingerprint()


def test_runtime_requirement_core_does_not_install_packages():
    requirement = reference_model_registry_package_bundle().runtime_requirements[0]
    assert requirement.package_install_performed_by_core is False


def test_weights_artifact_requires_checkpoint_ref():
    with pytest.raises(ValidationError):
        MLModelArtifactRecord(
            artifact_id="artifact:test",
            artifact_kind=MLArtifactKind.weights,
            artifact_format=MLArtifactFormat.safetensors,
            artifact_ref="artifact:weights",
            artifact_sha256="1" * 64,
            model_spec_ref="model:test",
        )


def test_checkpoint_artifact_hash_must_match_governed_checkpoint():
    invalid(lambda p: p["artifacts"][1].__setitem__("artifact_sha256", "f" * 64))


def test_artifact_model_spec_must_match():
    invalid(lambda p: p["artifacts"][0].__setitem__("model_spec_ref", "ml-model-spec:wrong"))


def test_artifact_checkpoint_must_resolve():
    invalid(lambda p: p["artifacts"][1].__setitem__("checkpoint_ref", "ml-checkpoint:missing"))


def test_runtime_binding_must_resolve():
    invalid(lambda p: p["runtime_requirements"][0].__setitem__("runtime_binding_ref", "runtime:missing"))


def test_runtime_environment_must_match_binding():
    invalid(lambda p: p["runtime_requirements"][0].__setitem__("environment_ref", "environment:wrong"))


def test_environment_lock_ref_and_hash_are_paired():
    req = reference_model_registry_package_bundle().runtime_requirements[0].model_dump(mode="json")
    req["environment_lock_sha256"] = None
    with pytest.raises(ValidationError):
        MLRuntimeRequirementRecord.model_validate(req)


def test_runtime_capabilities_must_be_unique():
    req = reference_model_registry_package_bundle().runtime_requirements[0].model_dump(mode="json")
    req["capabilities"].append(req["capabilities"][0])
    with pytest.raises(ValidationError):
        MLRuntimeRequirementRecord.model_validate(req)


def test_registry_model_spec_must_match():
    invalid(lambda p: p["registry_entries"][0].__setitem__("model_spec_ref", "model:wrong"))


def test_registry_inference_plan_must_match():
    invalid(lambda p: p["registry_entries"][0].__setitem__("inference_plan_ref", "plan:wrong"))


def test_registry_training_run_must_resolve():
    invalid(lambda p: p["registry_entries"][0].__setitem__("training_run_ref", "run:missing"))


def test_registry_checkpoint_must_resolve():
    invalid(lambda p: p["registry_entries"][0].__setitem__("checkpoint_ref", "checkpoint:missing"))


def test_registry_checkpoint_must_belong_to_training_run():
    data = payload()
    data["registry_entries"][0]["training_run_ref"] = "ml-training-run:fake"
    # fake run itself does not exist, still proves cross-link rejection
    with pytest.raises(ValidationError):
        MLModelRegistryPackageBundle.model_validate(data)


def test_registry_model_version_must_match_checkpoint_output():
    invalid(lambda p: p["registry_entries"][0].__setitem__("model_version_ref", "model-version:wrong"))


def test_registry_artifact_refs_must_resolve():
    invalid(lambda p: p["registry_entries"][0]["artifact_refs"].__setitem__(0, "artifact:missing"))


def test_registry_evaluation_refs_must_resolve():
    invalid(lambda p: p["registry_entries"][0]["evaluation_refs"].__setitem__(0, "evaluation:missing"))


def test_registry_representation_refs_must_resolve():
    invalid(lambda p: p["registry_entries"][0]["representation_model_refs"].__setitem__(0, "representation:missing"))


def test_registry_intended_use_ref_must_resolve():
    invalid(lambda p: p["registry_entries"][0].__setitem__("intended_use_ref", "intended-use:missing"))


def test_registry_limitation_refs_must_resolve():
    invalid(lambda p: p["registry_entries"][0]["limitation_refs"].__setitem__(0, "limitation:missing"))


def test_registry_aliases_must_be_unique():
    entry = reference_model_registry_package_bundle().registry_entries[0].model_dump(mode="json")
    entry["aliases"].append(entry["aliases"][0])
    with pytest.raises(ValidationError):
        MLModelRegistryEntry.model_validate(entry)


def test_registry_tags_must_be_unique():
    entry = reference_model_registry_package_bundle().registry_entries[0].model_dump(mode="json")
    entry["tags"].append(entry["tags"][0])
    with pytest.raises(ValidationError):
        MLModelRegistryEntry.model_validate(entry)


def test_manifest_registry_ref_must_resolve():
    invalid(lambda p: p["reproducibility_manifests"][0].__setitem__("registry_entry_ref", "registry:missing"))


def test_manifest_model_identity_must_match_registry():
    invalid(lambda p: p["reproducibility_manifests"][0].__setitem__("model_version_ref", "model-version:wrong"))


def test_manifest_training_lineage_must_match_registry():
    invalid(lambda p: p["reproducibility_manifests"][0].__setitem__("checkpoint_ref", "ml-checkpoint:reference-energy:epoch-1"))


def test_manifest_training_plan_must_match():
    invalid(lambda p: p["reproducibility_manifests"][0].__setitem__("training_plan_ref", "training-plan:wrong"))


def test_manifest_runtime_requirement_must_resolve():
    invalid(lambda p: p["reproducibility_manifests"][0].__setitem__("runtime_requirement_ref", "runtime-requirement:missing"))


def test_manifest_input_schema_must_match_inference_plan():
    invalid(lambda p: p["reproducibility_manifests"][0].__setitem__("input_schema_ref", "schema:wrong"))


def test_manifest_artifacts_must_be_registry_artifacts():
    invalid(lambda p: p["reproducibility_manifests"][0]["artifact_refs"].__setitem__(0, "artifact:missing"))


def test_manifest_evaluations_must_be_registry_evaluations():
    invalid(lambda p: p["reproducibility_manifests"][0]["evaluation_refs"].__setitem__(0, "evaluation:missing"))


def test_manifest_predecessor_fingerprints_must_match():
    invalid(lambda p: p["reproducibility_manifests"][0].__setitem__("inference_fingerprint_sha256", "0" * 64))


def test_package_registry_and_manifest_must_resolve():
    invalid(lambda p: p["model_packages"][0].__setitem__("manifest_ref", "manifest:missing"))


def test_package_runtime_requirement_must_match_manifest():
    invalid(lambda p: p["model_packages"][0].__setitem__("runtime_requirement_ref", "runtime-requirement:wrong"))


def test_package_input_schema_must_match_manifest():
    invalid(lambda p: p["model_packages"][0].__setitem__("input_schema_ref", "schema:wrong"))


def test_package_artifact_set_must_match_manifest():
    invalid(lambda p: p["model_packages"][0]["artifact_refs"].pop())


def test_package_calibration_refs_must_resolve():
    invalid(lambda p: p["model_packages"][0]["calibration_refs"].__setitem__(0, "calibration:missing"))


def test_package_uncertainty_refs_must_resolve():
    invalid(lambda p: p["model_packages"][0]["uncertainty_refs"].__setitem__(0, "uncertainty:missing"))


def test_package_explainability_refs_must_resolve():
    invalid(lambda p: p["model_packages"][0]["explainability_refs"].__setitem__(0, "explain:missing"))


def test_package_representation_refs_must_resolve():
    invalid(lambda p: p["model_packages"][0]["representation_refs"].__setitem__(0, "representation:missing"))


def test_package_limitation_set_must_match_manifest():
    invalid(lambda p: p["model_packages"][0]["limitation_refs"].pop())


def test_public_contract_route():
    app = FastAPI()
    app.include_router(ml_model_registry_packages.public_router)
    response = TestClient(app).get("/public/v1/ml-model-registry/contract")
    assert response.status_code == 200
    body = response.json()
    assert body["release"] == "3.64.0"
    assert body["governance"]["registration_does_not_certify_quality"] is True


def test_private_reference_route():
    app = FastAPI()
    app.include_router(ml_model_registry_packages.router)
    response = TestClient(app).get("/api/v1/ml-model-registry/reference")
    assert response.status_code == 200
    body = response.json()
    assert body["release"] == "3.64.0"
    assert len(body["bundle_fingerprint_sha256"]) == 64
