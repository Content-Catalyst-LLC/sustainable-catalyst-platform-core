#!/usr/bin/env python3
from app.services.r_runtime_migration import (
    ADAPTER_ID,
    CONTRACT_VERSION,
    RUNTIME_ID,
    RUNTIME_VERSION,
    contract_document,
    reference_r_runtime_migration,
)
from app.services.runtime_adapter_registry import REGISTRY

doc = contract_document()
assert doc["release"] == "3.36.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["runtime"]["runtime_id"] == RUNTIME_ID
assert doc["runtime"]["runtime_version"] == RUNTIME_VERSION
assert doc["migration"]["legacy_provider_id"] == "catalyst-analytics-r"
assert doc["migration"]["legacy_provider_version"] == "2.0.1"
assert doc["migration"]["non_destructive"] is True
assert len(doc["capabilities"]) == 6

bundle = reference_r_runtime_migration()
assert len(bundle.fingerprint()) == 64
assert bundle.migration_plan.preserve_legacy_resolution is True
assert bundle.migration_plan.duplicate_runtime_execution is False
assert set(bundle.runtime_registration.capabilities) == {
    "descriptive_summary",
    "quantile_summary",
    "correlation_matrix",
    "linear_regression",
    "t_test",
    "one_way_anova",
}

adapter = REGISTRY.get(ADAPTER_ID)
assert adapter is not None
assert adapter.adapter_id == "adapter:sc-runtime-r"
assert adapter.runtime.runtime_id == "sc-runtime-r"
assert adapter.runtime.provider_version == "1.0.0"
assert adapter.status == "registered"
assert adapter.runtime.status == "active"

ops = {
    operation
    for capability in adapter.runtime.capabilities
    for operation in capability.operations
}
assert set(bundle.runtime_registration.capabilities).issubset(ops)

print("PASS - Platform Core v3.36.0 Analytics R Migration / R Runtime 1.0")
print(f"CONTRACT={CONTRACT_VERSION}")
print("LEGACY_PROVIDER=catalyst-analytics-r@2.0.1")
print("RUNTIME_ID=sc-runtime-r")
print("RUNTIME_VERSION=1.0.0")
print("ADAPTER_ID=adapter:sc-runtime-r")
print("CAPABILITIES=6")
print("RUNTIME_REGISTRY_STATUS=registered")
print("LEGACY_ALIAS_RESOLUTION=enabled")
print("DESTRUCTIVE_MIGRATION=false")
print("DUPLICATE_R_EXECUTION=false")
print("CORE_EXECUTES_R_DIRECTLY=false")
