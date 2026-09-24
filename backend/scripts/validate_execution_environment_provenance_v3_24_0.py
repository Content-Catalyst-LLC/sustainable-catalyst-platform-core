#!/usr/bin/env python3
from app.services.execution_environment_provenance import (
    CONTRACT_VERSION,
    EnvironmentRequirement,
    compare_environments,
    contract_document,
    julia_v030_reference_provenance,
    verify_requirement,
)

doc = contract_document()
assert doc["release"] == "3.24.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["reference_runtime"]["provider_version"] == "0.3.0"
assert doc["reference_runtime"]["adapter_status"] == "registered"

julia = julia_v030_reference_provenance()
assert julia.environment.runtime_id == "catalyst-julia-runtime"
assert julia.environment.metadata["provider_version"] == "0.3.0"
assert julia.reproducibility_status.value == "locked"
assert len(julia.fingerprint()) == 64

comparison = compare_environments(julia, julia)
assert comparison.exact_match is True
assert comparison.differences == []

verification = verify_requirement(
    julia,
    EnvironmentRequirement(
        runtime_id="catalyst-julia-runtime",
        runtime_version="1.13.0",
        reproducibility_status="locked",
    ),
)
assert verification.ok is True

print("PASS - Platform Core v3.24.0 Execution Environment & Dependency Provenance")
print(f"CONTRACT={CONTRACT_VERSION}")
print("REFERENCE_RUNTIME=catalyst-julia-runtime@0.3.0")
print("REFERENCE_ADAPTER_STATUS=registered")
print("ENVIRONMENT_FINGERPRINTING=enabled")
print("DEPENDENCY_DRIFT_DETECTION=enabled")
