from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.reproducible_environment_packages import (
    CONTRACT_VERSION,
    REFERENCE_JULIA_RUNTIME,
    REFERENCE_R_RUNTIME,
    EnvironmentAsset,
    EnvironmentAssetKind,
    EnvironmentBuildInstruction,
    EnvironmentCompatibilityStatus,
    EnvironmentPackageState,
    EnvironmentReproductionVerification,
    EnvironmentVariableDeclaration,
    EnvironmentVariableKind,
    EnvironmentVerificationStatus,
    LanguagePackageRequirement,
    PackageManager,
    PlatformArchitecture,
    PlatformDescriptor,
    ReproducibleEnvironmentPackage,
    ReproducibleEnvironmentPackageBundle,
    RequirementScope,
    RuntimeEnvironmentRequirement,
    SystemPackageRequirement,
    contract_document,
    evaluate_platform_compatibility,
    reference_environment_package_bundle,
    to_scientific_environment_artifact,
)


def ref_bundle():
    return reference_environment_package_bundle()


def ref_package():
    return ref_bundle().packages[0]


def test_contract_identity():
    doc = contract_document()
    assert doc["release"] == "3.41.0"
    assert doc["contract"] == CONTRACT_VERSION


def test_contract_links_v340_workflow():
    assert "sc.core.cross-runtime-research-workflow.v1" in contract_document()["depends_on"]


def test_contract_links_v324_environment_provenance():
    assert "sc.core.execution-environment-provenance.v1" in contract_document()["depends_on"]


def test_reference_bundle_valid():
    bundle = ref_bundle()
    assert bundle.packages
    assert bundle.verifications


def test_reference_package_contains_r_and_julia():
    package = ref_package()
    refs = {item.runtime_ref for item in package.runtimes}
    assert refs == {REFERENCE_R_RUNTIME, REFERENCE_JULIA_RUNTIME}


def test_reference_package_verified_state():
    assert ref_package().state == EnvironmentPackageState.verified


def test_platform_fingerprint_stable():
    platform = ref_package().platform
    assert platform.fingerprint() == deepcopy(platform).fingerprint()


def test_runtime_requirement_fingerprint_stable():
    item = ref_package().runtimes[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_system_package_checksum_requires_sha256():
    with pytest.raises(ValidationError):
        SystemPackageRequirement(
            requirement_id="system:test",
            manager=PackageManager.apt,
            name="test",
            checksum_sha256="abc",
        )


def test_system_package_fingerprint_stable():
    item = ref_package().system_packages[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_language_package_hash_requires_sha256():
    with pytest.raises(ValidationError):
        LanguagePackageRequirement(
            requirement_id="lang:test",
            runtime_ref="runtime:test",
            manager=PackageManager.pip,
            name="numpy",
            version="1.0",
            content_sha256="bad",
        )


def test_language_package_fingerprint_stable():
    item = ref_package().language_packages[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_secret_reference_requires_secret_ref():
    with pytest.raises(ValidationError):
        EnvironmentVariableDeclaration(
            variable_id="env:secret",
            name="API_KEY",
            kind=EnvironmentVariableKind.secret_reference,
        )


def test_secret_reference_forbids_value():
    with pytest.raises(ValidationError):
        EnvironmentVariableDeclaration(
            variable_id="env:secret",
            name="API_KEY",
            kind=EnvironmentVariableKind.secret_reference,
            value="secret-value",
            secret_ref="secret-ref:test",
        )


def test_plain_variable_forbids_secret_ref():
    with pytest.raises(ValidationError):
        EnvironmentVariableDeclaration(
            variable_id="env:plain",
            name="LANG",
            kind=EnvironmentVariableKind.plain,
            value="C.UTF-8",
            secret_ref="secret-ref:test",
        )


def test_reference_secret_has_no_value():
    item = [
        x for x in ref_package().environment_variables
        if x.kind == EnvironmentVariableKind.secret_reference
    ][0]
    assert item.value is None
    assert item.secret_ref == "secret-ref:sc-research-api-key"


def test_environment_variable_fingerprint_stable():
    item = ref_package().environment_variables[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_environment_asset_requires_sha256():
    with pytest.raises(ValidationError):
        EnvironmentAsset(
            asset_id="asset:test",
            kind=EnvironmentAssetKind.lockfile,
            uri="core-ref://lock",
            content_sha256="bad",
        )


def test_environment_asset_fingerprint_stable():
    item = ref_package().assets[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_build_instruction_fingerprint_stable():
    item = ref_package().build_instructions[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_package_requires_runtime():
    package = ref_package().model_dump(mode="python")
    package["runtimes"] = []
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackage.model_validate(package)


def test_package_rejects_duplicate_runtime_requirement_ids():
    package = ref_package().model_dump(mode="python")
    package["runtimes"] = [package["runtimes"][0], deepcopy(package["runtimes"][0])]
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackage.model_validate(package)


def test_package_rejects_duplicate_system_requirement_ids():
    package = ref_package().model_dump(mode="python")
    package["system_packages"] = [
        package["system_packages"][0],
        deepcopy(package["system_packages"][0]),
    ]
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackage.model_validate(package)


def test_package_rejects_duplicate_language_requirement_ids():
    package = ref_package().model_dump(mode="python")
    package["language_packages"] = [
        package["language_packages"][0],
        deepcopy(package["language_packages"][0]),
    ]
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackage.model_validate(package)


def test_package_rejects_duplicate_variable_ids():
    package = ref_package().model_dump(mode="python")
    package["environment_variables"] = [
        package["environment_variables"][0],
        deepcopy(package["environment_variables"][0]),
    ]
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackage.model_validate(package)


def test_package_rejects_duplicate_variable_names():
    package = ref_package().model_dump(mode="python")
    second = deepcopy(package["environment_variables"][1])
    second["name"] = package["environment_variables"][0]["name"]
    package["environment_variables"] = [
        package["environment_variables"][0], second
    ]
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackage.model_validate(package)


def test_package_rejects_duplicate_asset_ids():
    package = ref_package().model_dump(mode="python")
    package["assets"] = [package["assets"][0], deepcopy(package["assets"][0])]
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackage.model_validate(package)


def test_package_rejects_duplicate_instruction_ids():
    package = ref_package().model_dump(mode="python")
    package["build_instructions"] = [
        package["build_instructions"][0],
        deepcopy(package["build_instructions"][0]),
    ]
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackage.model_validate(package)


def test_build_instruction_ordinals_must_be_contiguous():
    package = ref_package().model_dump(mode="python")
    package["build_instructions"][1]["ordinal"] = 8
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackage.model_validate(package)


def test_build_instruction_rejects_unknown_requirement():
    package = ref_package().model_dump(mode="python")
    package["build_instructions"][0]["requirement_refs"] = ["requirement:missing"]
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackage.model_validate(package)


def test_build_instruction_rejects_unknown_asset():
    package = ref_package().model_dump(mode="python")
    package["build_instructions"][1]["artifact_ref"] = "asset:missing"
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackage.model_validate(package)


def test_package_fingerprint_ignores_state():
    package = ref_package()
    other = deepcopy(package)
    other.state = EnvironmentPackageState.archived
    assert package.fingerprint() == other.fingerprint()


def test_package_fingerprint_ignores_created_at():
    package = ref_package()
    assert package.fingerprint() == deepcopy(package).fingerprint()
    assert len(package.fingerprint()) == 64


def test_compatibility_same_platform_is_compatible():
    package = ref_package()
    report = evaluate_platform_compatibility(package, package.platform)
    assert report.status == EnvironmentCompatibilityStatus.compatible
    assert not report.incompatible_runtime_refs


def test_compatibility_different_os_is_incompatible():
    package = ref_package()
    target = package.platform.model_copy(update={"operating_system": "macOS"})
    report = evaluate_platform_compatibility(package, target)
    assert report.status == EnvironmentCompatibilityStatus.incompatible
    assert set(report.incompatible_runtime_refs) == {REFERENCE_R_RUNTIME, REFERENCE_JULIA_RUNTIME}


def test_compatibility_different_arch_is_incompatible():
    package = ref_package()
    target = package.platform.model_copy(update={"architecture": PlatformArchitecture.arm64})
    report = evaluate_platform_compatibility(package, target)
    assert report.status == EnvironmentCompatibilityStatus.incompatible


def test_compatibility_is_preflight_only():
    report = evaluate_platform_compatibility(ref_package(), ref_package().platform)
    assert report.metadata["compatibility_is_preflight_only"] is True
    assert report.metadata["core_claims_reproduction_success"] is False


def test_compatibility_report_fingerprint_stable():
    report = evaluate_platform_compatibility(ref_package(), ref_package().platform)
    assert report.fingerprint() == deepcopy(report).fingerprint()


def test_verification_passed_rejects_failed_runtime_check():
    package = ref_package()
    with pytest.raises(ValidationError):
        EnvironmentReproductionVerification(
            verification_id="verification:test",
            environment_package_ref=package.environment_package_id,
            package_fingerprint_sha256=package.fingerprint(),
            status=EnvironmentVerificationStatus.passed,
            runtime_version_matches={REFERENCE_R_RUNTIME: False},
        )


def test_verification_passed_rejects_failed_asset_check():
    package = ref_package()
    with pytest.raises(ValidationError):
        EnvironmentReproductionVerification(
            verification_id="verification:test",
            environment_package_ref=package.environment_package_id,
            package_fingerprint_sha256=package.fingerprint(),
            status=EnvironmentVerificationStatus.passed,
            asset_hash_matches={"asset:test": False},
        )


def test_verification_passed_rejects_variable_mismatch():
    package = ref_package()
    with pytest.raises(ValidationError):
        EnvironmentReproductionVerification(
            verification_id="verification:test",
            environment_package_ref=package.environment_package_id,
            package_fingerprint_sha256=package.fingerprint(),
            status=EnvironmentVerificationStatus.passed,
            environment_variable_declarations_match=False,
        )


def test_reference_verification_passed():
    verification = ref_bundle().verifications[0]
    assert verification.status == EnvironmentVerificationStatus.passed


def test_reference_verification_covers_both_runtimes():
    verification = ref_bundle().verifications[0]
    assert verification.runtime_version_matches == {
        REFERENCE_R_RUNTIME: True,
        REFERENCE_JULIA_RUNTIME: True,
    }


def test_reference_verification_covers_all_assets():
    package = ref_package()
    verification = ref_bundle().verifications[0]
    assert set(verification.asset_hash_matches) == {x.asset_id for x in package.assets}


def test_verification_fingerprint_stable():
    verification = ref_bundle().verifications[0]
    assert verification.fingerprint() == deepcopy(verification).fingerprint()


def test_bundle_requires_packages():
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackageBundle(
            bundle_id="bundle:test",
            packages=[],
        )


def test_bundle_rejects_duplicate_package_ids():
    package = ref_package()
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackageBundle(
            bundle_id="bundle:test",
            packages=[package, deepcopy(package)],
        )


def test_bundle_rejects_unknown_request_package():
    bundle = ref_bundle().model_dump(mode="python")
    bundle["reproduction_requests"][0]["environment_package_ref"] = "package:missing"
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackageBundle.model_validate(bundle)


def test_bundle_rejects_request_package_fingerprint_mismatch():
    bundle = ref_bundle().model_dump(mode="python")
    bundle["reproduction_requests"][0]["environment_package_fingerprint_sha256"] = "f" * 64
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackageBundle.model_validate(bundle)


def test_bundle_rejects_unknown_compatibility_package():
    bundle = ref_bundle().model_dump(mode="python")
    bundle["compatibility_reports"][0]["environment_package_ref"] = "package:missing"
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackageBundle.model_validate(bundle)


def test_bundle_rejects_unknown_verification_package():
    bundle = ref_bundle().model_dump(mode="python")
    bundle["verifications"][0]["environment_package_ref"] = "package:missing"
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackageBundle.model_validate(bundle)


def test_bundle_rejects_verification_fingerprint_mismatch():
    bundle = ref_bundle().model_dump(mode="python")
    bundle["verifications"][0]["package_fingerprint_sha256"] = "f" * 64
    with pytest.raises(ValidationError):
        ReproducibleEnvironmentPackageBundle.model_validate(bundle)


def test_bundle_fingerprint_stable():
    bundle = ref_bundle()
    assert bundle.fingerprint() == deepcopy(bundle).fingerprint()
    assert len(bundle.fingerprint()) == 64


def test_reference_build_instructions_are_contiguous():
    package = ref_package()
    assert [x.ordinal for x in package.build_instructions] == [1, 2, 3, 4]


def test_reference_has_r_lockfile():
    package = ref_package()
    assert any(x.asset_id == "environment-asset:r-lockfile" for x in package.assets)


def test_reference_has_julia_manifest():
    package = ref_package()
    assert any(x.asset_id == "environment-asset:julia-manifest" for x in package.assets)


def test_reference_links_cross_runtime_workflow():
    package = ref_package()
    assert package.source_workflow_refs == ["cross-runtime-workflow:reference-r-julia:v1"]


def test_reference_secret_values_not_embedded():
    package = ref_package()
    assert package.metadata["secret_values_embedded"] is False


def test_scientific_artifact_bridge():
    payload = to_scientific_environment_artifact(ref_package())
    assert payload["artifact_kind"] == "package"
    assert payload["source_contract"] == CONTRACT_VERSION
    assert payload["content_sha256"] == ref_package().fingerprint()


def test_scientific_artifact_bridge_validates_v338():
    from app.services.scientific_result_registry import ScientificArtifactRef
    payload = to_scientific_environment_artifact(ref_package())
    item = ScientificArtifactRef.model_validate(payload)
    assert item.source_object_ref == ref_package().environment_package_id


def test_scientific_artifact_lists_runtimes():
    payload = to_scientific_environment_artifact(ref_package())
    assert payload["metadata"]["runtime_refs"] == [
        REFERENCE_JULIA_RUNTIME,
        REFERENCE_R_RUNTIME,
    ]


def test_package_manager_enum_covers_research_runtimes():
    values = {x.value for x in PackageManager}
    assert {"apt", "pip", "conda", "renv", "julia-pkg", "cargo"}.issubset(values)


def test_asset_kinds_cover_reproducibility_material():
    values = {x.value for x in EnvironmentAssetKind}
    assert {"lockfile", "manifest", "containerfile", "script", "configuration"}.issubset(values)


def test_core_does_not_install_packages():
    assert contract_document()["boundaries"]["core_installs_packages"] is False


def test_core_does_not_execute_environment_build():
    doc = contract_document()
    assert doc["boundaries"]["core_executes_environment_builds"] is False
    assert doc["integration"]["workspace_or_execution_host_builds_environment"] is True


def test_core_does_not_resolve_secret_values():
    doc = contract_document()
    assert doc["boundaries"]["core_resolves_secret_values"] is False
    assert doc["boundaries"]["secret_values_embedded_in_packages"] is False


def test_compatibility_is_not_reproduction_proof():
    assert contract_document()["boundaries"]["compatibility_report_is_reproduction_proof"] is False


def test_core_requires_verification_for_reproduction_claim():
    assert contract_document()["boundaries"]["core_certifies_reproduction_without_verification"] is False


def test_core_does_not_certify_scientific_validity():
    assert contract_document()["boundaries"]["core_certifies_scientific_validity"] is False


def test_reference_contract_statuses():
    doc = contract_document()
    assert doc["reference"]["compatibility_status"] == "compatible"
    assert doc["reference"]["verification_status"] == "passed"


def test_reference_bundle_fingerprints_are_sha256():
    doc = contract_document()
    assert len(doc["reference"]["package_fingerprint_sha256"]) == 64
    assert len(doc["reference"]["bundle_fingerprint_sha256"]) == 64
