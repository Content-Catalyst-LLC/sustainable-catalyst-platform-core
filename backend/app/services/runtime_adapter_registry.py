from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import (
    RuntimeCapability,
    RuntimeDescriptor,
    RuntimeKind,
    canonical_sha256,
)

CORE_RELEASE = "3.23.0"
ADAPTER_CONTRACT_VERSION = "sc.core.runtime-adapter.v1"
OBJECT_CONTRACT_VERSION = "sc.core.computational-runtime-object.v1"

REQUIRED_ADAPTER_METHODS = (
    "health",
    "version",
    "capabilities",
    "prepare",
    "execute",
    "cancel",
    "inspect",
    "collect_results",
    "collect_artifacts",
    "diagnose",
)


class AdapterMethodSpec(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    required: bool = True
    asynchronous: bool = False
    idempotent: bool | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuntimeAdapterDescriptor(BaseModel):
    adapter_id: str = Field(min_length=2, max_length=180)
    runtime: RuntimeDescriptor
    adapter_contract: str = ADAPTER_CONTRACT_VERSION
    provider_contracts: list[str] = Field(default_factory=list)
    transport: Literal[
        "http",
        "local-process",
        "container",
        "workspace-managed",
        "library",
        "contract-only",
    ] = "contract-only"
    invocation_mode: str = Field(default="governed", min_length=1, max_length=180)
    service_ref: str | None = Field(default=None, max_length=1000)
    methods: list[AdapterMethodSpec] = Field(
        default_factory=lambda: [
            AdapterMethodSpec(
                name=name,
                asynchronous=name in {"execute", "cancel"},
                idempotent=(name not in {"execute", "cancel"}),
            )
            for name in REQUIRED_ADAPTER_METHODS
        ]
    )
    status: Literal["registered", "contract-only", "degraded", "offline", "retired"] = "registered"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_contract(self):
        if self.adapter_contract != ADAPTER_CONTRACT_VERSION:
            raise ValueError(f"adapter_contract must be {ADAPTER_CONTRACT_VERSION}")
        method_names = [method.name for method in self.methods]
        missing = [name for name in REQUIRED_ADAPTER_METHODS if name not in method_names]
        if missing:
            raise ValueError("adapter is missing required methods: " + ", ".join(missing))
        if len(method_names) != len(set(method_names)):
            raise ValueError("adapter method names must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CapabilityRequirement(BaseModel):
    capability_keys: list[str] = Field(default_factory=list)
    operations: list[str] = Field(default_factory=list)
    input_types: list[str] = Field(default_factory=list)
    output_types: list[str] = Field(default_factory=list)
    runtime_kinds: list[RuntimeKind] = Field(default_factory=list)
    language: str | None = Field(default=None, max_length=100)
    deterministic_only: bool = False
    arbitrary_code_execution_allowed: bool = False
    include_contract_only: bool = True


class CapabilityCandidate(BaseModel):
    adapter_id: str
    runtime_id: str
    runtime_kind: RuntimeKind
    language: str | None = None
    provider_version: str | None = None
    status: str
    matched_capability_keys: list[str] = Field(default_factory=list)
    matched_operations: list[str] = Field(default_factory=list)
    matched_input_types: list[str] = Field(default_factory=list)
    matched_output_types: list[str] = Field(default_factory=list)


def _julia_reference_adapter() -> RuntimeAdapterDescriptor:
    capability = RuntimeCapability(
        capability_key="governed-numeric-compute",
        category="compute",
        operations=["identity", "sum", "mean", "matrix_multiply"],
        input_types=["json", "array", "matrix", "scalar"],
        output_types=["json", "array", "matrix", "scalar"],
        deterministic=True,
        arbitrary_code_execution=False,
        shell_execution=False,
        package_installation=False,
        metadata={
            "execution_contract": "sc.execution.v1",
            "environment_contract": "sc.environment.v1",
        },
    )
    runtime = RuntimeDescriptor(
        runtime_id="catalyst-julia-runtime",
        runtime_kind=RuntimeKind.language,
        language="julia",
        implementation="Julia",
        runtime_version="1.13.0",
        provider_version="0.3.0",
        service_name="catalyst-julia-runtime",
        contract_versions=[
            OBJECT_CONTRACT_VERSION,
            "sc.execution.v1",
            "sc.environment.v1",
        ],
        capabilities=[capability],
        execution_host="contabo-vps",
        status="active",
        metadata={
            "reference_runtime": True,
            "provider_release": "Catalyst Julia Runtime v0.3.0",
            "adapter_integration_state": "native-v0.3-core-adapter",
        },
    )
    return RuntimeAdapterDescriptor(
        adapter_id="adapter:catalyst-julia-runtime",
        runtime=runtime,
        provider_contracts=["sc.execution.v1", "sc.environment.v1"],
        transport="http",
        invocation_mode="governed-service",
        service_ref="catalyst-julia-runtime",
        status="registered",
        metadata={
            "reference_adapter": True,
            "core_executes_runtime_directly": False,
        },
    )


def legacy_analytical_provider_to_adapter(
    provider: dict[str, Any],
    capabilities: list[dict[str, Any]] | None = None,
) -> RuntimeAdapterDescriptor:
    runtime_name = str(provider.get("runtime") or "unknown").lower()
    provider_key = str(provider.get("provider_key") or provider.get("name") or "legacy-provider")
    provider_version = str(provider.get("provider_version") or "unknown")
    mapped_caps: list[RuntimeCapability] = []

    for cap in capabilities or []:
        mapped_caps.append(
            RuntimeCapability(
                capability_key=str(cap.get("capability_key") or "legacy-capability"),
                category=str(cap.get("category") or "analysis"),
                operations=list(cap.get("method_refs") or []),
                input_types=list(cap.get("input_types") or []),
                output_types=list(cap.get("output_types") or []),
                metadata={
                    "legacy_provider_capability": True,
                    "legacy_status": cap.get("status"),
                },
            )
        )

    runtime = RuntimeDescriptor(
        runtime_id=f"legacy:{provider_key}".lower().replace("_", "-"),
        runtime_kind=RuntimeKind.language,
        language=runtime_name,
        implementation=str(provider.get("name") or provider_key),
        runtime_version=provider_version,
        provider_version=provider_version,
        contract_versions=[
            OBJECT_CONTRACT_VERSION,
            str(provider.get("contract_ref") or "sc.core.analytical-runtime-provider.v1"),
        ],
        capabilities=mapped_caps,
        execution_host=str(provider.get("execution_host") or "workspace"),
        status="contract-only",
        metadata={
            "legacy_provider_key": provider_key,
            "legacy_transport_mode": provider.get("transport_mode"),
            "legacy_invocation_mode": provider.get("invocation_mode"),
        },
    )
    return RuntimeAdapterDescriptor(
        adapter_id=f"adapter:legacy:{provider_key}".lower().replace("_", "-"),
        runtime=runtime,
        provider_contracts=[
            str(provider.get("contract_ref") or "sc.core.analytical-runtime-provider.v1")
        ],
        transport="workspace-managed",
        invocation_mode=str(provider.get("invocation_mode") or "workspace-managed"),
        service_ref=provider_key,
        status="contract-only",
        metadata={
            "compatibility_bridge": "sc.core.analytical-runtime-provider.v1",
            "requires_native_adapter_upgrade": True,
        },
    )


class RuntimeAdapterRegistry:
    def __init__(self):
        self._adapters: dict[str, RuntimeAdapterDescriptor] = {}
        self.register(_julia_reference_adapter())

    def register(self, adapter: RuntimeAdapterDescriptor) -> RuntimeAdapterDescriptor:
        self._adapters[adapter.adapter_id] = adapter
        return adapter

    def get(self, adapter_id: str) -> RuntimeAdapterDescriptor | None:
        return self._adapters.get(adapter_id)

    def list(self) -> list[RuntimeAdapterDescriptor]:
        return [self._adapters[key] for key in sorted(self._adapters)]

    def capability_index(self) -> dict[str, list[str]]:
        index: dict[str, list[str]] = {}
        for adapter in self.list():
            for capability in adapter.runtime.capabilities:
                index.setdefault(capability.capability_key, []).append(adapter.adapter_id)
                for operation in capability.operations:
                    index.setdefault(f"operation:{operation}", []).append(adapter.adapter_id)
        return {key: sorted(set(value)) for key, value in sorted(index.items())}

    def resolve(self, requirement: CapabilityRequirement) -> list[CapabilityCandidate]:
        candidates: list[CapabilityCandidate] = []
        for adapter in self.list():
            if adapter.status == "retired":
                continue
            if adapter.status == "contract-only" and not requirement.include_contract_only:
                continue

            runtime = adapter.runtime
            if requirement.runtime_kinds and runtime.runtime_kind not in requirement.runtime_kinds:
                continue
            if requirement.language and (runtime.language or "").lower() != requirement.language.lower():
                continue

            caps = runtime.capabilities
            cap_keys = {cap.capability_key for cap in caps}
            operations = {item for cap in caps for item in cap.operations}
            input_types = {item for cap in caps for item in cap.input_types}
            output_types = {item for cap in caps for item in cap.output_types}

            if any(key not in cap_keys for key in requirement.capability_keys):
                continue
            if any(op not in operations for op in requirement.operations):
                continue
            if any(item not in input_types for item in requirement.input_types):
                continue
            if any(item not in output_types for item in requirement.output_types):
                continue
            if requirement.deterministic_only and not any(cap.deterministic is True for cap in caps):
                continue
            if not requirement.arbitrary_code_execution_allowed and any(
                cap.arbitrary_code_execution for cap in caps
            ):
                continue

            candidates.append(
                CapabilityCandidate(
                    adapter_id=adapter.adapter_id,
                    runtime_id=runtime.runtime_id,
                    runtime_kind=runtime.runtime_kind,
                    language=runtime.language,
                    provider_version=runtime.provider_version,
                    status=adapter.status,
                    matched_capability_keys=sorted(
                        set(requirement.capability_keys).intersection(cap_keys)
                    ),
                    matched_operations=sorted(
                        set(requirement.operations).intersection(operations)
                    ),
                    matched_input_types=sorted(
                        set(requirement.input_types).intersection(input_types)
                    ),
                    matched_output_types=sorted(
                        set(requirement.output_types).intersection(output_types)
                    ),
                )
            )
        return candidates


REGISTRY = RuntimeAdapterRegistry()


def contract_document() -> dict[str, Any]:
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": ADAPTER_CONTRACT_VERSION,
        "depends_on": OBJECT_CONTRACT_VERSION,
        "required_adapter_methods": list(REQUIRED_ADAPTER_METHODS),
        "registry_semantics": {
            "registration": "explicit",
            "capability_matching": "candidate-discovery-only",
            "autonomous_provider_selection": False,
            "execution_by_core": False,
            "capability_index_by_core": True,
        },
        "reference_adapter": {
            "adapter_id": "adapter:catalyst-julia-runtime",
            "runtime_id": "catalyst-julia-runtime",
            "provider_version": "0.2.0",
            "status": "contract-only",
            "provider_release": "Catalyst Julia Runtime v0.3.0",
        },
        "legacy_bridge": {
            "contract": "sc.core.analytical-runtime-provider.v1",
            "purpose": "translate existing analytical provider metadata without replacing it",
        },
        "boundaries": {
            "core_invokes_runtime_directly": False,
            "core_selects_runtime_autonomously": False,
            "core_installs_packages": False,
            "core_executes_arbitrary_source": False,
            "core_certifies_scientific_validity": False,
        },
    }
