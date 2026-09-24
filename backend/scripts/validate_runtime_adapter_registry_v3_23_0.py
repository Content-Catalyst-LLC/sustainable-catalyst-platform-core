#!/usr/bin/env python3
from app.services.runtime_adapter_registry import (
    ADAPTER_CONTRACT_VERSION,
    REGISTRY,
    REQUIRED_ADAPTER_METHODS,
    CapabilityRequirement,
    contract_document,
)

doc = contract_document()
assert doc["release"] == "3.23.0"
assert doc["contract"] == ADAPTER_CONTRACT_VERSION
assert tuple(doc["required_adapter_methods"]) == REQUIRED_ADAPTER_METHODS
assert doc["registry_semantics"]["autonomous_provider_selection"] is False

adapter = REGISTRY.get("adapter:catalyst-julia-runtime")
assert adapter is not None
assert adapter.runtime.provider_version == "0.2.0"
assert adapter.status == "contract-only"
assert len(adapter.fingerprint()) == 64

candidates = REGISTRY.resolve(
    CapabilityRequirement(operations=["matrix_multiply"], language="julia")
)
assert len(candidates) == 1
assert candidates[0].adapter_id == "adapter:catalyst-julia-runtime"

index = REGISTRY.capability_index()
assert "operation:sum" in index

print("PASS - Platform Core v3.23.0 Runtime Adapter Contract & Capability Registry")
print(f"CONTRACT={ADAPTER_CONTRACT_VERSION}")
print(f"METHODS={len(REQUIRED_ADAPTER_METHODS)}")
print("REFERENCE_ADAPTER=adapter:catalyst-julia-runtime@0.2.0")
print("SELECTION_MODE=candidate-discovery-only")
