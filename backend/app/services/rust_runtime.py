from __future__ import annotations

import math
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .reproducible_environment_packages import (
    EnvironmentAsset,
    EnvironmentAssetKind,
    EnvironmentBuildInstruction,
    EnvironmentPackageState,
    EnvironmentVariableDeclaration,
    EnvironmentVariableKind,
    PackageManager,
    PlatformArchitecture,
    PlatformDescriptor,
    ReproducibleEnvironmentPackage,
    RequirementSource,
    RuntimeEnvironmentRequirement,
    SystemPackageRequirement,
)
from .runtime_security_governance import (
    FilesystemAccessMode,
    IsolationMechanism,
    NetworkAccessMode,
    PackageInstallMode,
    RuntimeIsolationProfile,
    RuntimeSecurityPolicy,
)

CORE_RELEASE = "3.52.0"
CONTRACT_VERSION = "sc.core.rust-runtime.v1"
PROVIDER_VERSION = "1.0.0"
RUSTC_VERSION = "1.75.0"
RUST_PACKAGE_VERSION = "1.75.0+dfsg0ubuntu1-0ubuntu7.4"
CARGO_VERSION = "1.75.0"
CARGO_PACKAGE_VERSION = "1.75.0+dfsg0ubuntu1-0ubuntu7.4"
RUNTIME_ID = "sc-runtime-rust"
ADAPTER_ID = "adapter:sc-runtime-rust"
SERVICE_NAME = "sc-rust-runtime"
SERVICE_ENDPOINT = "http://127.0.0.1:18101"

RUST_OPERATIONS = [
    "prefix_sum",
    "moving_average",
    "connected_components",
    "topological_sort",
    "levenshtein_distance",
    "fnv1a_64",
]


class RustOperation(str, Enum):
    prefix_sum = "prefix_sum"
    moving_average = "moving_average"
    connected_components = "connected_components"
    topological_sort = "topological_sort"
    levenshtein_distance = "levenshtein_distance"
    fnv1a_64 = "fnv1a_64"


class RustExecutionState(str, Enum):
    declared = "declared"
    prepared = "prepared"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


def _finite_vector(values: list[float], name: str, min_len: int = 1, max_len: int = 262144) -> None:
    if len(values) < min_len or len(values) > max_len:
        raise ValueError(f"{name} length must be between {min_len} and {max_len}")
    if any(not math.isfinite(float(x)) for x in values):
        raise ValueError(f"{name} values must be finite")


def _validate_adjacency(matrix: list[list[int]]) -> int:
    if not matrix or not matrix[0]:
        raise ValueError("adjacency_matrix must be non-empty")
    n = len(matrix)
    if n > 512 or any(len(row) != n for row in matrix):
        raise ValueError("adjacency_matrix must be square and <= 512 vertices")
    if any(value not in {0, 1} for row in matrix for value in row):
        raise ValueError("adjacency_matrix values must be 0 or 1")
    if any(matrix[i][i] != 0 for i in range(n)):
        raise ValueError("adjacency_matrix diagonal must be zero")
    if any(matrix[i][j] != matrix[j][i] for i in range(n) for j in range(n)):
        raise ValueError("connected_components adjacency_matrix must be symmetric")
    return n


def _validate_ascii(value: str, name: str) -> None:
    if len(value) > 4096:
        raise ValueError(f"{name} must not exceed 4096 characters")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} must be ASCII in Rust runtime v1") from exc


class RustInput(BaseModel):
    integers: list[int] = Field(default_factory=list)
    values: list[float] = Field(default_factory=list)
    window: int | None = None
    adjacency_matrix: list[list[int]] = Field(default_factory=list)
    edge_list: list[list[int]] = Field(default_factory=list)
    vertex_count: int | None = None
    text: str = ""
    text_a: str = ""
    text_b: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RustExecutionSettings(BaseModel):
    max_execution_seconds: int = Field(default=120, ge=1, le=1800)
    optimization_level: int = Field(default=2, ge=0, le=2)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RustExecutionRequest(BaseModel):
    rust_request_id: str = Field(min_length=2, max_length=500)
    operation: RustOperation
    inputs: RustInput
    settings: RustExecutionSettings = Field(default_factory=RustExecutionSettings)
    computational_job_ref: str = Field(min_length=2, max_length=500)
    environment_package_ref: str = "environment-package:rust-runtime:v1"
    security_policy_ref: str = "runtime-security-policy:rust-runtime-standard:v1"
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self):
        i, op = self.inputs, self.operation
        if op == RustOperation.prefix_sum:
            if not i.integers or len(i.integers) > 262144:
                raise ValueError("prefix_sum requires 1..262144 integers")
            if any(x < -(2**62) or x > 2**62 for x in i.integers):
                raise ValueError("prefix_sum integers exceed bounded i64 range")
        elif op == RustOperation.moving_average:
            _finite_vector(i.values, "values")
            if i.window is None or i.window < 1 or i.window > len(i.values):
                raise ValueError("moving_average window must be between 1 and len(values)")
        elif op == RustOperation.connected_components:
            _validate_adjacency(i.adjacency_matrix)
        elif op == RustOperation.topological_sort:
            if i.vertex_count is None or i.vertex_count < 1 or i.vertex_count > 10000:
                raise ValueError("topological_sort vertex_count must be 1..10000")
            if len(i.edge_list) > 100000:
                raise ValueError("topological_sort edge_list exceeds 100000 edges")
            for edge in i.edge_list:
                if len(edge) != 2:
                    raise ValueError("each topological_sort edge must contain [from,to]")
                if any(isinstance(x, bool) or not isinstance(x, int) for x in edge):
                    raise ValueError("topological_sort vertices must be integers")
                if not (0 <= edge[0] < i.vertex_count and 0 <= edge[1] < i.vertex_count):
                    raise ValueError("topological_sort edge references out-of-range vertex")
        elif op == RustOperation.levenshtein_distance:
            _validate_ascii(i.text_a, "text_a")
            _validate_ascii(i.text_b, "text_b")
        elif op == RustOperation.fnv1a_64:
            if len(i.text.encode("utf-8")) > 65536:
                raise ValueError("fnv1a_64 text must not exceed 65536 UTF-8 bytes")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RustExecutionResultContract(BaseModel):
    result_contract_id: str = Field(min_length=2, max_length=500)
    rust_request_ref: str = Field(min_length=2, max_length=500)
    operation: RustOperation
    expected_artifact_kinds: list[str] = Field(default_factory=list)
    expected_result_kinds: list[str] = Field(default_factory=list)
    state: RustExecutionState = RustExecutionState.declared
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_contract(self):
        if not self.expected_artifact_kinds and not self.expected_result_kinds:
            raise ValueError("Rust result contract requires artifact or result kinds")
        if len(self.expected_artifact_kinds) != len(set(self.expected_artifact_kinds)):
            raise ValueError("duplicate Rust artifact kinds")
        if len(self.expected_result_kinds) != len(set(self.expected_result_kinds)):
            raise ValueError("duplicate Rust result kinds")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        return canonical_sha256(payload)


class RustRuntimeRegistration(BaseModel):
    registration_id: str = Field(min_length=2, max_length=500)
    runtime_id: str = RUNTIME_ID
    provider_version: str = PROVIDER_VERSION
    rustc_version: str = RUSTC_VERSION
    rustc_package_version: str = RUST_PACKAGE_VERSION
    cargo_version: str = CARGO_VERSION
    cargo_package_version: str = CARGO_PACKAGE_VERSION
    adapter_id: str = ADAPTER_ID
    service_name: str = SERVICE_NAME
    endpoint: str = SERVICE_ENDPOINT
    operations: list[str] = Field(default_factory=lambda: list(RUST_OPERATIONS))
    runtime_contract: str = CONTRACT_VERSION
    runtime_kind: str = "language"
    language: str = "rust"
    edition: str = "2021"
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_registration(self):
        if self.runtime_id != RUNTIME_ID or self.adapter_id != ADAPTER_ID:
            raise ValueError("Rust runtime identity mismatch")
        if self.provider_version != PROVIDER_VERSION:
            raise ValueError("Rust provider version mismatch")
        if set(self.operations) != set(RUST_OPERATIONS) or len(self.operations) != len(set(self.operations)):
            raise ValueError("Rust operation set mismatch")
        if self.edition != "2021":
            raise ValueError("Rust runtime v1 requires edition 2021")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RustRuntimeBundle(BaseModel):
    bundle_id: str = Field(min_length=2, max_length=500)
    registration: RustRuntimeRegistration
    environment_package: ReproducibleEnvironmentPackage
    security_policy: RuntimeSecurityPolicy
    reference_request: RustExecutionRequest
    result_contract: RustExecutionResultContract
    source_object_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.reference_request.environment_package_ref != self.environment_package.environment_package_id:
            raise ValueError("Rust request/environment mismatch")
        if self.reference_request.security_policy_ref != self.security_policy.security_policy_id:
            raise ValueError("Rust request/security mismatch")
        if self.result_contract.rust_request_ref != self.reference_request.rust_request_id:
            raise ValueError("Rust result/request mismatch")
        if self.result_contract.operation != self.reference_request.operation:
            raise ValueError("Rust operation mismatch")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "bundle_id": self.bundle_id,
            "registration": self.registration.fingerprint(),
            "environment": self.environment_package.fingerprint(),
            "security": self.security_policy.fingerprint(),
            "request": self.reference_request.fingerprint(),
            "result_contract": self.result_contract.fingerprint(),
            "source_object_refs": sorted(self.source_object_refs),
            "metadata": self.metadata,
        })


def reference_environment_package() -> ReproducibleEnvironmentPackage:
    platform = PlatformDescriptor(
        operating_system="Ubuntu",
        operating_system_version="24.04",
        architecture=PlatformArchitecture.amd64,
        libc="glibc",
        kernel_family="linux",
    )
    manifest = EnvironmentAsset(
        asset_id="environment-asset:rust-runtime-manifest",
        kind=EnvironmentAssetKind.manifest,
        uri="core-ref://runtime-manifests/rust-1.75.0-noble.json",
        content_sha256="1" * 64,
        media_type="application/json",
        size_bytes=512,
    )
    reqs = EnvironmentAsset(
        asset_id="environment-asset:rust-provider-requirements",
        kind=EnvironmentAssetKind.lockfile,
        uri="core-ref://runtime-locks/rust-provider-requirements.txt",
        content_sha256="2" * 64,
        media_type="text/plain",
        size_bytes=256,
    )
    return ReproducibleEnvironmentPackage(
        environment_package_id="environment-package:rust-runtime:v1",
        name="Sustainable Catalyst Rust Runtime Environment",
        package_version="1.0.0",
        platform=platform,
        runtimes=[RuntimeEnvironmentRequirement(
            runtime_requirement_id="runtime-requirement:rust-provider",
            runtime_ref=RUNTIME_ID,
            runtime_version=PROVIDER_VERSION,
            runtime_adapter_ref=ADAPTER_ID,
        )],
        system_packages=[
            SystemPackageRequirement(
                requirement_id="system-package:rustc",
                manager=PackageManager.apt,
                name="rustc",
                version=RUST_PACKAGE_VERSION,
                source=RequirementSource.operating_system,
            ),
            SystemPackageRequirement(
                requirement_id="system-package:cargo",
                manager=PackageManager.apt,
                name="cargo",
                version=CARGO_PACKAGE_VERSION,
                source=RequirementSource.operating_system,
            ),
        ],
        language_packages=[],
        environment_variables=[
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:rust-artifact-root",
                name="SC_RUST_ARTIFACT_ROOT",
                kind=EnvironmentVariableKind.path,
                value="/var/lib/sc-rust-runtime/artifacts",
            ),
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:rust-work-root",
                name="SC_RUST_WORK_ROOT",
                kind=EnvironmentVariableKind.path,
                value="/var/lib/sc-rust-runtime/work",
            ),
        ],
        assets=[manifest, reqs],
        build_instructions=[
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:rust-system-packages",
                ordinal=1,
                action="install-pinned-rustc-cargo",
                manager=PackageManager.apt,
                requirement_refs=["system-package:rustc", "system-package:cargo"],
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:rust-provider-python",
                ordinal=2,
                action="install-provider-python-dependencies",
                manager=PackageManager.pip,
                artifact_ref=reqs.asset_id,
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:rust-smoke-test",
                ordinal=3,
                action="compile-and-run-bounded-rust-prefix-sum-smoke-test",
            ),
        ],
        source_environment_ref="runtime-environment:rust-provider:v1",
        source_job_refs=[],
        source_workflow_refs=[],
        state=EnvironmentPackageState.verified,
        provenance={
            "source_release": CORE_RELEASE,
            "core_builds_environment": False,
            "execution_host_builds_environment": True,
        },
        metadata={
            "rustc_version": RUSTC_VERSION,
            "rustc_package_version": RUST_PACKAGE_VERSION,
            "cargo_version": CARGO_VERSION,
            "cargo_package_version": CARGO_PACKAGE_VERSION,
            "edition": "2021",
            "provider_version": PROVIDER_VERSION,
            "arbitrary_rust_code": False,
            "provider_managed_compilation": True,
            "unsafe_code_forbidden": True,
        },
    )


def reference_security_policy() -> RuntimeSecurityPolicy:
    isolation = RuntimeIsolationProfile(
        isolation_profile_id="isolation-profile:rust-runtime-standard:v1",
        mechanism=IsolationMechanism.process,
        network_mode=NetworkAccessMode.none,
        filesystem_mode=FilesystemAccessMode.allowlist,
        package_install_mode=PackageInstallMode.denied,
        process_namespace_isolated=True,
        user_namespace_isolated=True,
        privilege_escalation_allowed=False,
        host_filesystem_mounted=False,
        shell_allowed=False,
        arbitrary_code_allowed=False,
        outbound_artifact_egress_allowed=True,
        resource_budget_ref="resource-budget:rust-runtime-standard:v1",
        syscall_policy_ref="syscall-policy:rust-runtime-standard:v1",
    )
    return RuntimeSecurityPolicy(
        security_policy_id="runtime-security-policy:rust-runtime-standard:v1",
        policy_version="1.0.0",
        name="Rust Runtime Standard Policy",
        isolation_profile=isolation,
        allowed_runtime_refs=[RUNTIME_ID],
        allowed_adapter_refs=[ADAPTER_ID],
        allowed_operations={RUNTIME_ID: list(RUST_OPERATIONS)},
        allowed_filesystem_prefixes=[
            "/workspace",
            "/tmp/sc-rust-runtime",
            "/var/lib/sc-rust-runtime/artifacts",
            "/var/lib/sc-rust-runtime/work",
        ],
        allowed_artifact_egress_classes=[
            "research-artifact",
            "safe-native-result",
            "rust-diagnostics",
        ],
        execution_policy_ref="execution-policy:rust-runtime-standard:v1",
        provenance={"source_release": CORE_RELEASE, "policy_owner": "platform-governance"},
        metadata={
            "arbitrary_rust_source_allowed": False,
            "cargo_dependency_install_allowed": False,
            "caller_filesystem_paths_allowed": False,
            "unsafe_code_allowed": False,
        },
    )


def reference_runtime_bundle() -> RustRuntimeBundle:
    request = RustExecutionRequest(
        rust_request_id="rust-request:reference-prefix-sum:001",
        operation=RustOperation.prefix_sum,
        inputs=RustInput(integers=[1, 2, 3, 4, 5]),
        computational_job_ref="job:rust-reference-prefix-sum:001",
        provenance={
            "originating_product": "workbench",
            "execution_owner": "workspace-or-execution-host",
        },
    )
    contract = RustExecutionResultContract(
        result_contract_id="rust-result-contract:reference-prefix-sum:001",
        rust_request_ref=request.rust_request_id,
        operation=request.operation,
        expected_artifact_kinds=[
            "rust-generated-source",
            "rust-result-json",
            "rust-compile-log",
            "rust-run-log",
        ],
        expected_result_kinds=["integer-vector", "rust-diagnostics"],
        metadata={
            "scientific_validity_certified": False,
            "algorithm_selection_owned_by_product": True,
        },
    )
    return RustRuntimeBundle(
        bundle_id="rust-runtime-bundle:reference:v1",
        registration=RustRuntimeRegistration(
            registration_id="rust-runtime-registration:v1",
            metadata={
                "compiler": "rustc",
                "edition": "2021",
                "arbitrary_rust_code": False,
                "unsafe_code": False,
                "shell_execution": False,
                "cargo_dependency_installation": False,
                "provider_managed_compilation": True,
            },
        ),
        environment_package=reference_environment_package(),
        security_policy=reference_security_policy(),
        reference_request=request,
        result_contract=contract,
        source_object_refs=[
            "unified-runtime-catalog:platform-core:v1",
            "c-cpp-runtime-bundle:reference:v1",
        ],
        metadata={
            "reference_is_contract_proof": True,
            "live_provider_execution_occurs_outside_core": True,
        },
    )


def to_scientific_rust_artifact(bundle: RustRuntimeBundle) -> dict[str, Any]:
    return {
        "artifact_id": f"scientific-artifact:{bundle.bundle_id}",
        "artifact_kind": "package",
        "uri": f"core-ref://{bundle.bundle_id}",
        "content_sha256": bundle.fingerprint(),
        "media_type": "application/vnd.sustainable-catalyst.rust-runtime+json",
        "source_contract": CONTRACT_VERSION,
        "source_object_ref": bundle.bundle_id,
        "metadata": {
            "runtime_id": bundle.registration.runtime_id,
            "provider_version": bundle.registration.provider_version,
            "rustc_version": bundle.registration.rustc_version,
            "edition": bundle.registration.edition,
            "reference_operation": bundle.reference_request.operation.value,
        },
    }


def contract_document() -> dict[str, Any]:
    bundle = reference_runtime_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "provider_version": PROVIDER_VERSION,
        "rustc_version": RUSTC_VERSION,
        "rustc_package_version": RUST_PACKAGE_VERSION,
        "cargo_version": CARGO_VERSION,
        "cargo_package_version": CARGO_PACKAGE_VERSION,
        "runtime_id": RUNTIME_ID,
        "adapter_id": ADAPTER_ID,
        "language": "rust",
        "edition": "2021",
        "operations": list(RUST_OPERATIONS),
        "capabilities": {
            "safe_native_systems": True,
            "graph_processing": True,
            "text_algorithms": True,
            "streaming_numeric_transform": True,
            "deterministic_hashing": True,
            "provider_managed_compilation": True,
            "unsafe_code_forbidden": True,
            "reproducible_environment_package": True,
            "runtime_security_policy": True,
            "runtime_adapter_registration": True,
            "unified_runtime_catalog_integration": True,
            "workspace_product_profile_integration": True,
            "research_lab_product_profile_integration": True,
            "workbench_product_profile_integration": True,
            "scientific_registry_bridge": True,
        },
        "boundaries": {
            "core_executes_rust": False,
            "provider_executes_rust": True,
            "arbitrary_rust_source": False,
            "unsafe_rust_code": False,
            "shell_execution": False,
            "runtime_package_install_via_api": False,
            "caller_filesystem_paths": False,
            "core_selects_algorithm": False,
            "core_certifies_numerical_validity": False,
            "core_certifies_scientific_validity": False,
        },
        "reference": {
            "bundle_id": bundle.bundle_id,
            "environment_package_id": bundle.environment_package.environment_package_id,
            "security_policy_id": bundle.security_policy.security_policy_id,
            "reference_request_id": bundle.reference_request.rust_request_id,
            "reference_operation": bundle.reference_request.operation.value,
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
    }
