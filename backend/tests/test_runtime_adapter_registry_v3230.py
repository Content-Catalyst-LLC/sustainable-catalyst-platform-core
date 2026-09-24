import pytest
from pydantic import ValidationError

from app.services.computational_runtime_objects import RuntimeDescriptor, RuntimeKind
from app.services.runtime_adapter_registry import (
    ADAPTER_CONTRACT_VERSION,
    REGISTRY,
    REQUIRED_ADAPTER_METHODS,
    AdapterMethodSpec,
    CapabilityRequirement,
    RuntimeAdapterDescriptor,
    RuntimeAdapterRegistry,
    contract_document,
    legacy_analytical_provider_to_adapter,
)


def test_contract_exposes_required_adapter_methods_and_boundaries():
    doc = contract_document()
    assert doc["release"] == "3.23.0"
    assert doc["contract"] == ADAPTER_CONTRACT_VERSION
    assert tuple(doc["required_adapter_methods"]) == REQUIRED_ADAPTER_METHODS
    assert doc["registry_semantics"]["autonomous_provider_selection"] is False
    assert doc["boundaries"]["core_invokes_runtime_directly"] is False


def test_julia_reference_adapter_is_registered():
    adapter = REGISTRY.get("adapter:catalyst-julia-runtime")
    assert adapter is not None
    assert adapter.runtime.runtime_id == "catalyst-julia-runtime"
    assert adapter.runtime.provider_version == "0.2.0"
    assert adapter.status == "contract-only"


def test_julia_capabilities_include_v020_allowlisted_operations():
    adapter = REGISTRY.get("adapter:catalyst-julia-runtime")
    operations = {
        operation
        for capability in adapter.runtime.capabilities
        for operation in capability.operations
    }
    assert {"identity", "sum", "mean", "matrix_multiply"} <= operations


def test_capability_resolution_discovers_candidate_without_selecting():
    candidates = REGISTRY.resolve(
        CapabilityRequirement(operations=["matrix_multiply"], language="julia")
    )
    assert len(candidates) == 1
    assert candidates[0].adapter_id == "adapter:catalyst-julia-runtime"


def test_unknown_operation_returns_no_candidate():
    candidates = REGISTRY.resolve(
        CapabilityRequirement(operations=["not-a-real-operation"])
    )
    assert candidates == []


def test_capability_index_is_deterministic():
    first = REGISTRY.capability_index()
    second = REGISTRY.capability_index()
    assert first == second
    assert first["operation:sum"] == ["adapter:catalyst-julia-runtime"]


def test_adapter_rejects_missing_required_method():
    runtime = RuntimeDescriptor(
        runtime_id="test-runtime",
        runtime_kind=RuntimeKind.language,
        language="python",
        implementation="Python",
        runtime_version="3.12",
    )
    with pytest.raises(ValidationError):
        RuntimeAdapterDescriptor(
            adapter_id="adapter:test-runtime",
            runtime=runtime,
            methods=[AdapterMethodSpec(name="health")],
        )


def test_adapter_fingerprint_is_stable():
    adapter = REGISTRY.get("adapter:catalyst-julia-runtime")
    assert adapter.fingerprint() == adapter.fingerprint()
    assert len(adapter.fingerprint()) == 64


def test_legacy_analytical_provider_bridge_preserves_capability_metadata():
    provider = {
        "provider_key": "catalystanalyticsr",
        "name": "Catalyst Analytics R",
        "provider_version": "2.0.1",
        "runtime": "r",
        "execution_host": "workspace",
        "contract_ref": "sc.core.analytical-runtime-provider.v1",
        "transport_mode": "hosted",
        "invocation_mode": "workspace-managed",
    }
    capabilities = [{
        "capability_key": "econometrics",
        "category": "statistics",
        "input_types": ["dataset", "model", "parameter_set"],
        "output_types": ["analytical_result"],
        "method_refs": [],
        "status": "active",
    }]
    adapter = legacy_analytical_provider_to_adapter(provider, capabilities)
    assert adapter.runtime.language == "r"
    assert adapter.runtime.provider_version == "2.0.1"
    assert adapter.runtime.capabilities[0].capability_key == "econometrics"
    assert adapter.metadata["requires_native_adapter_upgrade"] is True


def test_contract_only_adapters_can_be_excluded_from_resolution():
    candidates = REGISTRY.resolve(
        CapabilityRequirement(operations=["sum"], include_contract_only=False)
    )
    assert candidates == []
