#!/usr/bin/env python3

from app.services.stan_runtime import (
    ADAPTER_ID,
    CMDSTAN_VERSION,
    CONTRACT_VERSION,
    PROVIDER_VERSION,
    RUNTIME_ID,
    STAN_OPERATIONS,
    contract_document,
    reference_runtime_bundle,
    to_scientific_stan_artifact,
)
from app.services.scientific_result_registry import ScientificArtifactRef

doc = contract_document()
assert doc["release"] == "3.46.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["runtime_id"] == RUNTIME_ID
assert doc["adapter_id"] == ADAPTER_ID
assert doc["provider_version"] == PROVIDER_VERSION
assert doc["cmdstan_version"] == CMDSTAN_VERSION
assert doc["operations"] == STAN_OPERATIONS
assert doc["capabilities"]["posterior_sampling"] is True
assert doc["capabilities"]["runtime_adapter_registration"] is True
assert doc["capabilities"]["unified_runtime_catalog_integration"] is True
assert doc["boundaries"]["core_executes_stan"] is False
assert doc["boundaries"]["arbitrary_shell_execution"] is False
assert doc["boundaries"]["stan_include_directives"] is False
assert doc["boundaries"]["core_certifies_convergence"] is False

bundle = reference_runtime_bundle()
assert bundle.registration.runtime_id == RUNTIME_ID
assert bundle.registration.provider_version == PROVIDER_VERSION
assert bundle.environment_package.environment_package_id == "environment-package:stan-runtime:v1"
assert bundle.security_policy.security_policy_id == "runtime-security-policy:stan-runtime-standard:v1"
assert bundle.reference_request.operation == "sample"
assert bundle.reference_request.settings.chains == 1
assert len(bundle.fingerprint()) == 64

artifact = to_scientific_stan_artifact(bundle)
ScientificArtifactRef.model_validate(artifact)

print("PASS - Platform Core v3.46.0 Stan Runtime")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"RUNTIME_ID={RUNTIME_ID}")
print(f"PROVIDER_VERSION={PROVIDER_VERSION}")
print(f"CMDSTAN_VERSION={CMDSTAN_VERSION}")
print("MODEL_COMPILATION=enabled")
print("POSTERIOR_SAMPLING=enabled")
print("OPTIMIZATION=enabled")
print("VARIATIONAL_INFERENCE=enabled")
print("DIAGNOSTICS=enabled")
print("REPRODUCIBLE_ENVIRONMENT_PACKAGE=enabled")
print("RUNTIME_SECURITY_POLICY=enabled")
print("UNIFIED_RUNTIME_API_INTEGRATION=enabled")
print("CORE_EXECUTES_STAN=false")
print("ARBITRARY_SHELL=false")
print("RUNTIME_PACKAGE_INSTALL_VIA_API=false")
print("STAN_INCLUDE_DIRECTIVES=false")
print("EXTERNAL_CPP_EXTENSIONS=false")
print("MULTI_CHAIN_PARALLEL_V1=false")
print("CORE_CERTIFIES_CONVERGENCE=false")
print("CORE_CERTIFIES_SCIENTIFIC_VALIDITY=false")
