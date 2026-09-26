from __future__ import annotations

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

CORE_RELEASE = "3.49.0"
CONTRACT_VERSION = "sc.core.haskell-runtime.v1"
PROVIDER_VERSION = "1.0.0"
GHC_VERSION = "9.4.7"
GHC_PACKAGE_VERSION = "9.4.7-3"
RUNTIME_ID = "sc-runtime-haskell"
ADAPTER_ID = "adapter:sc-runtime-haskell"
SERVICE_NAME = "sc-haskell-runtime"
SERVICE_ENDPOINT = "http://127.0.0.1:18098"

HASKELL_OPERATIONS = [
    "gcd",
    "lcm",
    "rational_reduce",
    "factorial",
    "fibonacci",
    "binomial_coefficient",
    "integer_power",
    "graph_reachable",
]


class HaskellOperation(str, Enum):
    gcd = "gcd"
    lcm = "lcm"
    rational_reduce = "rational_reduce"
    factorial = "factorial"
    fibonacci = "fibonacci"
    binomial_coefficient = "binomial_coefficient"
    integer_power = "integer_power"
    graph_reachable = "graph_reachable"


class HaskellExecutionState(str, Enum):
    declared = "declared"
    prepared = "prepared"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class HaskellTypedInput(BaseModel):
    integers: list[int] = Field(default_factory=list)
    numerator: int | None = None
    denominator: int | None = None
    base: int | None = None
    exponent: int | None = None
    n: int | None = None
    k: int | None = None
    graph_edges: list[tuple[int, int]] = Field(default_factory=list)
    graph_source: int | None = None
    graph_target: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class HaskellExecutionSettings(BaseModel):
    max_execution_seconds: int = Field(default=60, ge=1, le=600)
    max_integer_digits: int = Field(default=20000, ge=64, le=100000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class HaskellExecutionRequest(BaseModel):
    haskell_request_id: str = Field(min_length=2, max_length=500)
    operation: HaskellOperation
    inputs: HaskellTypedInput
    settings: HaskellExecutionSettings = Field(default_factory=HaskellExecutionSettings)
    computational_job_ref: str = Field(min_length=2, max_length=500)
    environment_package_ref: str = "environment-package:haskell-runtime:v1"
    security_policy_ref: str = "runtime-security-policy:haskell-runtime-standard:v1"
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self):
        i = self.inputs
        op = self.operation
        if op in {HaskellOperation.gcd, HaskellOperation.lcm}:
            if len(i.integers) != 2:
                raise ValueError(f"{op.value} requires exactly two integers")
        elif op == HaskellOperation.rational_reduce:
            if i.numerator is None or i.denominator is None:
                raise ValueError("rational_reduce requires numerator and denominator")
            if i.denominator == 0:
                raise ValueError("rational denominator cannot be zero")
        elif op in {HaskellOperation.factorial, HaskellOperation.fibonacci}:
            if i.n is None:
                raise ValueError(f"{op.value} requires n")
            if i.n < 0 or i.n > 10000:
                raise ValueError("n must be between 0 and 10000")
        elif op == HaskellOperation.binomial_coefficient:
            if i.n is None or i.k is None:
                raise ValueError("binomial_coefficient requires n and k")
            if i.n < 0 or i.k < 0 or i.k > i.n or i.n > 10000:
                raise ValueError("binomial coefficient requires 0 <= k <= n <= 10000")
        elif op == HaskellOperation.integer_power:
            if i.base is None or i.exponent is None:
                raise ValueError("integer_power requires base and exponent")
            if i.exponent < 0 or i.exponent > 10000:
                raise ValueError("integer exponent must be between 0 and 10000")
        elif op == HaskellOperation.graph_reachable:
            if i.graph_source is None or i.graph_target is None:
                raise ValueError("graph_reachable requires graph_source and graph_target")
            if len(i.graph_edges) > 10000:
                raise ValueError("graph_reachable supports at most 10000 edges")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class HaskellExecutionResultContract(BaseModel):
    result_contract_id: str = Field(min_length=2, max_length=500)
    haskell_request_ref: str = Field(min_length=2, max_length=500)
    operation: HaskellOperation
    expected_artifact_kinds: list[str] = Field(default_factory=list)
    expected_result_kinds: list[str] = Field(default_factory=list)
    state: HaskellExecutionState = HaskellExecutionState.declared
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_contract(self):
        if not self.expected_artifact_kinds and not self.expected_result_kinds:
            raise ValueError("Haskell result contract requires artifact or result kinds")
        if len(self.expected_artifact_kinds) != len(set(self.expected_artifact_kinds)):
            raise ValueError("duplicate Haskell artifact kinds")
        if len(self.expected_result_kinds) != len(set(self.expected_result_kinds)):
            raise ValueError("duplicate Haskell result kinds")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        return canonical_sha256(payload)


class HaskellRuntimeRegistration(BaseModel):
    registration_id: str = Field(min_length=2, max_length=500)
    runtime_id: str = RUNTIME_ID
    provider_version: str = PROVIDER_VERSION
    ghc_version: str = GHC_VERSION
    ghc_package_version: str = GHC_PACKAGE_VERSION
    adapter_id: str = ADAPTER_ID
    service_name: str = SERVICE_NAME
    endpoint: str = SERVICE_ENDPOINT
    operations: list[str] = Field(default_factory=lambda: list(HASKELL_OPERATIONS))
    runtime_contract: str = CONTRACT_VERSION
    runtime_kind: str = "language"
    language: str = "haskell"
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_registration(self):
        if self.runtime_id != RUNTIME_ID or self.adapter_id != ADAPTER_ID:
            raise ValueError("Haskell runtime identity mismatch")
        if self.provider_version != PROVIDER_VERSION:
            raise ValueError("Haskell provider version mismatch")
        if set(self.operations) != set(HASKELL_OPERATIONS):
            raise ValueError("Haskell operation set mismatch")
        if len(self.operations) != len(set(self.operations)):
            raise ValueError("Haskell operations must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class HaskellRuntimeBundle(BaseModel):
    bundle_id: str = Field(min_length=2, max_length=500)
    registration: HaskellRuntimeRegistration
    environment_package: ReproducibleEnvironmentPackage
    security_policy: RuntimeSecurityPolicy
    reference_request: HaskellExecutionRequest
    result_contract: HaskellExecutionResultContract
    source_object_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.reference_request.environment_package_ref != self.environment_package.environment_package_id:
            raise ValueError("Haskell request/environment mismatch")
        if self.reference_request.security_policy_ref != self.security_policy.security_policy_id:
            raise ValueError("Haskell request/security mismatch")
        if self.result_contract.haskell_request_ref != self.reference_request.haskell_request_id:
            raise ValueError("Haskell result/request mismatch")
        if self.result_contract.operation != self.reference_request.operation:
            raise ValueError("Haskell operation mismatch")
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
        asset_id="environment-asset:haskell-runtime-manifest",
        kind=EnvironmentAssetKind.manifest,
        uri="core-ref://runtime-manifests/haskell-ghc-9.4.7-noble.json",
        content_sha256="e" * 64,
        media_type="application/json",
        size_bytes=512,
    )
    reqs = EnvironmentAsset(
        asset_id="environment-asset:haskell-provider-requirements",
        kind=EnvironmentAssetKind.lockfile,
        uri="core-ref://runtime-locks/haskell-provider-requirements.txt",
        content_sha256="f" * 64,
        media_type="text/plain",
        size_bytes=256,
    )
    return ReproducibleEnvironmentPackage(
        environment_package_id="environment-package:haskell-runtime:v1",
        name="Sustainable Catalyst Haskell Runtime Environment",
        package_version="1.0.0",
        platform=platform,
        runtimes=[
            RuntimeEnvironmentRequirement(
                runtime_requirement_id="runtime-requirement:haskell-provider",
                runtime_ref=RUNTIME_ID,
                runtime_version=PROVIDER_VERSION,
                runtime_adapter_ref=ADAPTER_ID,
            )
        ],
        system_packages=[
            SystemPackageRequirement(
                requirement_id="system-package:ghc",
                manager=PackageManager.apt,
                name="ghc",
                version=GHC_PACKAGE_VERSION,
                source=RequirementSource.operating_system,
            ),
        ],
        language_packages=[],
        environment_variables=[
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:haskell-artifact-root",
                name="SC_HASKELL_ARTIFACT_ROOT",
                kind=EnvironmentVariableKind.path,
                value="/var/lib/sc-haskell-runtime/artifacts",
            ),
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:haskell-work-root",
                name="SC_HASKELL_WORK_ROOT",
                kind=EnvironmentVariableKind.path,
                value="/var/lib/sc-haskell-runtime/work",
            ),
        ],
        assets=[manifest, reqs],
        build_instructions=[
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:haskell-system-package",
                ordinal=1,
                action="install-pinned-ghc",
                manager=PackageManager.apt,
                requirement_refs=["system-package:ghc"],
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:haskell-provider-python",
                ordinal=2,
                action="install-provider-python-dependencies",
                manager=PackageManager.pip,
                artifact_ref=reqs.asset_id,
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:haskell-smoke-test",
                ordinal=3,
                action="run-bounded-native-haskell-exact-arithmetic-smoke-test",
            ),
        ],
        source_environment_ref="runtime-environment:haskell-provider:v1",
        source_job_refs=[],
        source_workflow_refs=[],
        state=EnvironmentPackageState.verified,
        provenance={
            "source_release": CORE_RELEASE,
            "core_builds_environment": False,
            "execution_host_builds_environment": True,
        },
        metadata={
            "ghc_version": GHC_VERSION,
            "ghc_package_version": GHC_PACKAGE_VERSION,
            "provider_version": PROVIDER_VERSION,
            "arbitrary_haskell_source": False,
            "package_manager_api": False,
        },
    )


def reference_security_policy() -> RuntimeSecurityPolicy:
    isolation = RuntimeIsolationProfile(
        isolation_profile_id="isolation-profile:haskell-runtime-standard:v1",
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
        resource_budget_ref="resource-budget:haskell-runtime-standard:v1",
        syscall_policy_ref="syscall-policy:haskell-runtime-standard:v1",
    )
    return RuntimeSecurityPolicy(
        security_policy_id="runtime-security-policy:haskell-runtime-standard:v1",
        policy_version="1.0.0",
        name="Haskell Runtime Standard Policy",
        isolation_profile=isolation,
        allowed_runtime_refs=[RUNTIME_ID],
        allowed_adapter_refs=[ADAPTER_ID],
        allowed_operations={RUNTIME_ID: list(HASKELL_OPERATIONS)},
        allowed_filesystem_prefixes=[
            "/workspace",
            "/tmp/sc-haskell-runtime",
            "/var/lib/sc-haskell-runtime/artifacts",
            "/var/lib/sc-haskell-runtime/work",
        ],
        allowed_artifact_egress_classes=[
            "research-artifact",
            "exact-computation-result",
            "haskell-diagnostics",
        ],
        execution_policy_ref="execution-policy:haskell-runtime-standard:v1",
        provenance={"source_release": CORE_RELEASE, "policy_owner": "platform-governance"},
        metadata={
            "arbitrary_haskell_source_allowed": False,
            "package_install_allowed": False,
            "caller_filesystem_paths_allowed": False,
        },
    )


def reference_runtime_bundle() -> HaskellRuntimeBundle:
    request = HaskellExecutionRequest(
        haskell_request_id="haskell-request:reference-rational-reduce:001",
        operation=HaskellOperation.rational_reduce,
        inputs=HaskellTypedInput(numerator=42, denominator=56),
        computational_job_ref="job:haskell-reference-rational-reduce:001",
        provenance={
            "originating_product": "research-lab",
            "execution_owner": "workspace-or-execution-host",
        },
    )
    contract = HaskellExecutionResultContract(
        result_contract_id="haskell-result-contract:reference-rational-reduce:001",
        haskell_request_ref=request.haskell_request_id,
        operation=request.operation,
        expected_artifact_kinds=["haskell-generated-source", "haskell-result-json", "haskell-run-log"],
        expected_result_kinds=["exact-rational-result", "typed-computation-diagnostics"],
        metadata={
            "scientific_validity_certified": False,
            "source_is_provider_generated": True,
        },
    )
    return HaskellRuntimeBundle(
        bundle_id="haskell-runtime-bundle:reference:v1",
        registration=HaskellRuntimeRegistration(
            registration_id="haskell-runtime-registration:v1",
            metadata={
                "native_cli": "runghc",
                "compiler": "GHC",
                "arbitrary_haskell_code": False,
                "shell_execution": False,
                "runtime_package_installation": False,
            },
        ),
        environment_package=reference_environment_package(),
        security_policy=reference_security_policy(),
        reference_request=request,
        result_contract=contract,
        source_object_refs=[
            "unified-runtime-catalog:platform-core:v1",
            "gretl-hansl-runtime-bundle:reference:v1",
        ],
        metadata={
            "reference_is_contract_proof": True,
            "live_provider_execution_occurs_outside_core": True,
        },
    )


def to_scientific_haskell_artifact(bundle: HaskellRuntimeBundle) -> dict[str, Any]:
    return {
        "artifact_id": f"scientific-artifact:{bundle.bundle_id}",
        "artifact_kind": "package",
        "uri": f"core-ref://{bundle.bundle_id}",
        "content_sha256": bundle.fingerprint(),
        "media_type": "application/vnd.sustainable-catalyst.haskell-runtime+json",
        "source_contract": CONTRACT_VERSION,
        "source_object_ref": bundle.bundle_id,
        "metadata": {
            "runtime_id": bundle.registration.runtime_id,
            "provider_version": bundle.registration.provider_version,
            "ghc_version": bundle.registration.ghc_version,
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
        "ghc_version": GHC_VERSION,
        "ghc_package_version": GHC_PACKAGE_VERSION,
        "runtime_id": RUNTIME_ID,
        "adapter_id": ADAPTER_ID,
        "language": "haskell",
        "operations": list(HASKELL_OPERATIONS),
        "capabilities": {
            "typed_functional_computation": True,
            "exact_integer_arithmetic": True,
            "exact_rational_arithmetic": True,
            "discrete_mathematics": True,
            "combinatorics": True,
            "graph_reachability": True,
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
            "core_executes_haskell": False,
            "provider_executes_haskell": True,
            "arbitrary_haskell_source": False,
            "shell_execution": False,
            "runtime_package_install_via_api": False,
            "caller_filesystem_paths": False,
            "core_selects_method": False,
            "core_certifies_mathematical_validity": False,
            "core_certifies_scientific_validity": False,
        },
        "reference": {
            "bundle_id": bundle.bundle_id,
            "environment_package_id": bundle.environment_package.environment_package_id,
            "security_policy_id": bundle.security_policy.security_policy_id,
            "reference_request_id": bundle.reference_request.haskell_request_id,
            "reference_operation": bundle.reference_request.operation.value,
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
    }
