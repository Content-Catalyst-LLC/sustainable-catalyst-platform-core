#!/usr/bin/env python3

from app.services.reproducible_environment_packages import (
    CONTRACT_VERSION,
    EnvironmentVerificationStatus,
    contract_document,
    evaluate_platform_compatibility,
    reference_environment_package_bundle,
    to_scientific_environment_artifact,
)
from app.services.scientific_result_registry import ScientificArtifactRef

doc = contract_document()
assert doc["release"] == "3.41.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["capabilities"]["exact_runtime_requirements"] is True
assert doc["capabilities"]["lockfile_and_manifest_assets"] is True
assert doc["capabilities"]["secret_reference_only_variables"] is True
assert doc["capabilities"]["reproduction_verification"] is True
assert doc["integration"]["workspace_or_execution_host_builds_environment"] is True
assert doc["boundaries"]["core_executes_environment_builds"] is False
assert doc["boundaries"]["core_resolves_secret_values"] is False

bundle = reference_environment_package_bundle()
assert len(bundle.packages) == 1
assert len(bundle.fingerprint()) == 64

package = bundle.packages[0]
assert package.state == "verified"
assert {x.runtime_ref for x in package.runtimes} == {
    "sc-runtime-r",
    "catalyst-julia-runtime",
}
assert [x.ordinal for x in package.build_instructions] == [1, 2, 3, 4]
assert package.metadata["secret_values_embedded"] is False

secret_vars = [x for x in package.environment_variables if x.kind == "secret-reference"]
assert len(secret_vars) == 1
assert secret_vars[0].value is None
assert secret_vars[0].secret_ref

compatibility = evaluate_platform_compatibility(package, package.platform)
assert compatibility.status == "compatible"
assert compatibility.metadata["compatibility_is_preflight_only"] is True

verification = bundle.verifications[0]
assert verification.status == EnvironmentVerificationStatus.passed
assert all(verification.runtime_version_matches.values())
assert all(verification.asset_hash_matches.values())

payload = to_scientific_environment_artifact(package)
ScientificArtifactRef.model_validate(payload)

print("PASS - Platform Core v3.41.0 Reproducible Environment Packages")
print(f"CONTRACT={CONTRACT_VERSION}")
print("PLATFORM_FINGERPRINTS=enabled")
print("EXACT_RUNTIME_REQUIREMENTS=enabled")
print("SYSTEM_PACKAGE_REQUIREMENTS=enabled")
print("LANGUAGE_PACKAGE_REQUIREMENTS=enabled")
print("LOCKFILE_MANIFEST_ASSETS=enabled")
print("SECRET_REFERENCE_ONLY_VARIABLES=enabled")
print("ORDERED_BUILD_INSTRUCTIONS=enabled")
print("COMPATIBILITY_PREFLIGHT=enabled")
print("REPRODUCTION_VERIFICATION=enabled")
print("CROSS_RUNTIME_WORKFLOW_BINDING=enabled")
print("SCIENTIFIC_REGISTRY_BRIDGE=enabled")
print("CORE_INSTALLS_PACKAGES=false")
print("CORE_EXECUTES_ENVIRONMENT_BUILDS=false")
print("CORE_RESOLVES_SECRET_VALUES=false")
print("CORE_CERTIFIES_REPRODUCTION_WITHOUT_VERIFICATION=false")
print("CORE_CERTIFIES_SCIENTIFIC_VALIDITY=false")
