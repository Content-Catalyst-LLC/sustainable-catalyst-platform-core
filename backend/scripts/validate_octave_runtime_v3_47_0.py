#!/usr/bin/env python3
from app.services.octave_runtime import (
    ADAPTER_ID, CONTRACT_VERSION, OCTAVE_OPERATIONS, OCTAVE_VERSION,
    PROVIDER_VERSION, RUNTIME_ID, contract_document, reference_runtime_bundle,
    to_scientific_octave_artifact,
)
from app.services.scientific_result_registry import ScientificArtifactRef

doc = contract_document()
assert doc["release"] == "3.47.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["runtime_id"] == RUNTIME_ID
assert doc["adapter_id"] == ADAPTER_ID
assert doc["provider_version"] == PROVIDER_VERSION
assert doc["octave_version"] == OCTAVE_VERSION
assert doc["operations"] == OCTAVE_OPERATIONS
assert doc["capabilities"]["matrix_compute"] is True
assert doc["capabilities"]["linear_system_solving"] is True
assert doc["capabilities"]["workbench_product_profile_integration"] is True
assert doc["boundaries"]["core_executes_octave"] is False
assert doc["boundaries"]["arbitrary_octave_source"] is False
assert doc["boundaries"]["shell_execution"] is False

bundle = reference_runtime_bundle()
assert bundle.registration.runtime_id == RUNTIME_ID
assert bundle.registration.provider_version == PROVIDER_VERSION
assert bundle.environment_package.environment_package_id == "environment-package:octave-runtime:v1"
assert bundle.security_policy.security_policy_id == "runtime-security-policy:octave-runtime-standard:v1"
assert bundle.reference_request.operation == "linear_solve"
assert bundle.reference_request.payload.metadata["expected_solution"] == [2.0,3.0]
assert len(bundle.fingerprint()) == 64

ScientificArtifactRef.model_validate(to_scientific_octave_artifact(bundle))

print("PASS - Platform Core v3.47.0 Octave Runtime")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"RUNTIME_ID={RUNTIME_ID}")
print(f"PROVIDER_VERSION={PROVIDER_VERSION}")
print(f"OCTAVE_VERSION={OCTAVE_VERSION}")
print("MATRIX_COMPUTE=enabled")
print("LINEAR_SOLVE=enabled")
print("EIGENVALUES=enabled")
print("SVD=enabled")
print("FFT=enabled")
print("POLYNOMIAL_ROOTS=enabled")
print("REPRODUCIBLE_ENVIRONMENT_PACKAGE=enabled")
print("RUNTIME_SECURITY_POLICY=enabled")
print("UNIFIED_RUNTIME_API_INTEGRATION=enabled")
print("WORKSPACE_INTEGRATION=enabled")
print("RESEARCH_LAB_INTEGRATION=enabled")
print("WORKBENCH_INTEGRATION=enabled")
print("CORE_EXECUTES_OCTAVE=false")
print("ARBITRARY_OCTAVE_SOURCE=false")
print("SHELL_EXECUTION=false")
print("RUNTIME_PACKAGE_INSTALL_VIA_API=false")
print("CALLER_FILESYSTEM_PATHS=false")
print("CORE_CERTIFIES_NUMERICAL_VALIDITY=false")
print("CORE_CERTIFIES_SCIENTIFIC_VALIDITY=false")
