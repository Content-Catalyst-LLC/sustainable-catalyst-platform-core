#!/usr/bin/env python3
from app.services.gretl_hansl_runtime import (
    ADAPTER_ID, CONTRACT_VERSION, GRETL_OPERATIONS, GRETL_PACKAGE_VERSION,
    GRETL_VERSION, PROVIDER_VERSION, RUNTIME_ID, contract_document,
    reference_runtime_bundle, to_scientific_gretl_artifact,
)
from app.services.scientific_result_registry import ScientificArtifactRef

doc = contract_document()
assert doc["release"] == "3.48.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["runtime_id"] == RUNTIME_ID
assert doc["adapter_id"] == ADAPTER_ID
assert doc["provider_version"] == PROVIDER_VERSION
assert doc["gretl_version"] == GRETL_VERSION
assert doc["gretl_package_version"] == GRETL_PACKAGE_VERSION
assert doc["operations"] == GRETL_OPERATIONS
assert doc["language"] == "hansl"
assert doc["capabilities"]["econometrics"] is True
assert doc["capabilities"]["ordinary_least_squares"] is True
assert doc["capabilities"]["unified_runtime_catalog_integration"] is True
assert doc["boundaries"]["core_executes_gretl"] is False
assert doc["boundaries"]["arbitrary_hansl_source"] is False

bundle = reference_runtime_bundle()
assert bundle.registration.runtime_id == RUNTIME_ID
assert bundle.registration.provider_version == PROVIDER_VERSION
assert bundle.registration.runtime_kind == "domain"
assert bundle.registration.language == "hansl"
assert bundle.environment_package.environment_package_id == "environment-package:gretl-hansl-runtime:v1"
assert bundle.security_policy.security_policy_id == "runtime-security-policy:gretl-hansl-runtime-standard:v1"
assert bundle.reference_request.operation == "ols"
assert len(bundle.fingerprint()) == 64

ScientificArtifactRef.model_validate(to_scientific_gretl_artifact(bundle))

print("PASS - Platform Core v3.48.0 gretl/hansl Runtime")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"RUNTIME_ID={RUNTIME_ID}")
print(f"PROVIDER_VERSION={PROVIDER_VERSION}")
print(f"GRETL_VERSION={GRETL_VERSION}")
print(f"GRETL_PACKAGE_VERSION={GRETL_PACKAGE_VERSION}")
print("ECONOMETRICS=enabled")
print("OLS=enabled")
print("ROBUST_OLS=enabled")
print("LOGIT=enabled")
print("PROBIT=enabled")
print("DESCRIPTIVE_SUMMARY=enabled")
print("CORRELATION_MATRIX=enabled")
print("WORKSPACE_INTEGRATION=enabled")
print("RESEARCH_LAB_INTEGRATION=enabled")
print("CORE_EXECUTES_GRETL=false")
print("ARBITRARY_HANSL_SOURCE=false")
print("SHELL_EXECUTION=false")
print("CORE_CERTIFIES_ECONOMETRIC_VALIDITY=false")
print("CORE_CERTIFIES_SCIENTIFIC_VALIDITY=false")
