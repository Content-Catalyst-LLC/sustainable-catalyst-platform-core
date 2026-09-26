from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .reproducible_environment_packages import (
    EnvironmentAsset, EnvironmentAssetKind, EnvironmentBuildInstruction,
    EnvironmentPackageState, EnvironmentVariableDeclaration,
    EnvironmentVariableKind, PlatformArchitecture, PlatformDescriptor,
    ReproducibleEnvironmentPackage, RequirementSource,
    RuntimeEnvironmentRequirement, SystemPackageRequirement, PackageManager,
)
from .runtime_security_governance import (
    FilesystemAccessMode, IsolationMechanism, NetworkAccessMode,
    PackageInstallMode, RuntimeIsolationProfile, RuntimeSecurityPolicy,
)

CORE_RELEASE = "3.47.0"
CONTRACT_VERSION = "sc.core.octave-runtime.v1"
PROVIDER_VERSION = "1.0.0"
OCTAVE_VERSION = "8.4.0"
RUNTIME_ID = "sc-runtime-octave"
ADAPTER_ID = "adapter:sc-runtime-octave"
SERVICE_NAME = "sc-octave-runtime"
SERVICE_ENDPOINT = "http://127.0.0.1:18096"

OCTAVE_OPERATIONS = [
    "matrix_multiply",
    "linear_solve",
    "eigenvalues",
    "svd",
    "fft",
    "polynomial_roots",
]


class OctaveOperation(str, Enum):
    matrix_multiply = "matrix_multiply"
    linear_solve = "linear_solve"
    eigenvalues = "eigenvalues"
    svd = "svd"
    fft = "fft"
    polynomial_roots = "polynomial_roots"


class OctaveExecutionState(str, Enum):
    declared = "declared"
    prepared = "prepared"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class OctaveNumericPayload(BaseModel):
    payload_id: str = Field(min_length=2, max_length=500)
    values: dict[str, Any] = Field(default_factory=dict)
    schema_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_values(self):
        if not self.values:
            raise ValueError("Octave numeric payload requires values")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class OctaveExecutionSettings(BaseModel):
    precision_digits: int = Field(default=15, ge=6, le=17)
    max_execution_seconds: int = Field(default=120, ge=1, le=1800)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class OctaveExecutionRequest(BaseModel):
    octave_request_id: str = Field(min_length=2, max_length=500)
    operation: OctaveOperation
    payload: OctaveNumericPayload
    settings: OctaveExecutionSettings = Field(default_factory=OctaveExecutionSettings)
    computational_job_ref: str = Field(min_length=2, max_length=500)
    environment_package_ref: str = "environment-package:octave-runtime:v1"
    security_policy_ref: str = "runtime-security-policy:octave-runtime-standard:v1"
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class OctaveExecutionResultContract(BaseModel):
    result_contract_id: str = Field(min_length=2, max_length=500)
    octave_request_ref: str = Field(min_length=2, max_length=500)
    operation: OctaveOperation
    expected_artifact_kinds: list[str] = Field(default_factory=list)
    expected_result_kinds: list[str] = Field(default_factory=list)
    state: OctaveExecutionState = OctaveExecutionState.declared
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_contract(self):
        if not self.expected_artifact_kinds and not self.expected_result_kinds:
            raise ValueError("Octave result contract requires artifact or result kinds")
        if len(self.expected_artifact_kinds) != len(set(self.expected_artifact_kinds)):
            raise ValueError("duplicate Octave artifact kinds")
        if len(self.expected_result_kinds) != len(set(self.expected_result_kinds)):
            raise ValueError("duplicate Octave result kinds")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        return canonical_sha256(payload)


class OctaveRuntimeRegistration(BaseModel):
    registration_id: str = Field(min_length=2, max_length=500)
    runtime_id: str = RUNTIME_ID
    provider_version: str = PROVIDER_VERSION
    octave_version: str = OCTAVE_VERSION
    adapter_id: str = ADAPTER_ID
    service_name: str = SERVICE_NAME
    endpoint: str = SERVICE_ENDPOINT
    operations: list[str] = Field(default_factory=lambda: list(OCTAVE_OPERATIONS))
    runtime_contract: str = CONTRACT_VERSION
    runtime_kind: str = "language"
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_registration(self):
        if self.runtime_id != RUNTIME_ID or self.adapter_id != ADAPTER_ID:
            raise ValueError("Octave runtime identity mismatch")
        if self.provider_version != PROVIDER_VERSION:
            raise ValueError("Octave provider version mismatch")
        if len(self.operations) != len(set(self.operations)):
            raise ValueError("Octave operations must be unique")
        if set(self.operations) != set(OCTAVE_OPERATIONS):
            raise ValueError("Octave operation set mismatch")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class OctaveRuntimeBundle(BaseModel):
    bundle_id: str = Field(min_length=2, max_length=500)
    registration: OctaveRuntimeRegistration
    environment_package: ReproducibleEnvironmentPackage
    security_policy: RuntimeSecurityPolicy
    reference_request: OctaveExecutionRequest
    result_contract: OctaveExecutionResultContract
    source_object_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.reference_request.environment_package_ref != self.environment_package.environment_package_id:
            raise ValueError("Octave request/environment mismatch")
        if self.reference_request.security_policy_ref != self.security_policy.security_policy_id:
            raise ValueError("Octave request/security mismatch")
        if self.result_contract.octave_request_ref != self.reference_request.octave_request_id:
            raise ValueError("Octave result/request mismatch")
        if self.result_contract.operation != self.reference_request.operation:
            raise ValueError("Octave operation mismatch")
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
        asset_id="environment-asset:octave-runtime-manifest",
        kind=EnvironmentAssetKind.manifest,
        uri="core-ref://runtime-manifests/octave-8.4.0.json",
        content_sha256="a" * 64,
        media_type="application/json",
        size_bytes=512,
    )
    reqs = EnvironmentAsset(
        asset_id="environment-asset:octave-provider-requirements",
        kind=EnvironmentAssetKind.lockfile,
        uri="core-ref://runtime-locks/octave-provider-requirements.txt",
        content_sha256="b" * 64,
        media_type="text/plain",
        size_bytes=256,
    )
    return ReproducibleEnvironmentPackage(
        environment_package_id="environment-package:octave-runtime:v1",
        name="Sustainable Catalyst Octave Runtime Environment",
        package_version="1.0.0",
        platform=platform,
        runtimes=[
            RuntimeEnvironmentRequirement(
                runtime_requirement_id="runtime-requirement:octave-provider",
                runtime_ref=RUNTIME_ID,
                runtime_version=PROVIDER_VERSION,
                runtime_adapter_ref=ADAPTER_ID,
            )
        ],
        system_packages=[
            SystemPackageRequirement(
                requirement_id="system-package:octave",
                manager=PackageManager.apt,
                name="octave",
                version=OCTAVE_VERSION,
                source=RequirementSource.operating_system,
            )
        ],
        language_packages=[],
        environment_variables=[
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:octave-artifact-root",
                name="SC_OCTAVE_ARTIFACT_ROOT",
                kind=EnvironmentVariableKind.path,
                value="/var/lib/sc-octave-runtime/artifacts",
            ),
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:octave-work-root",
                name="SC_OCTAVE_WORK_ROOT",
                kind=EnvironmentVariableKind.path,
                value="/var/lib/sc-octave-runtime/work",
            ),
        ],
        assets=[manifest, reqs],
        build_instructions=[
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:octave-system-package",
                ordinal=1,
                action="install-pinned-octave",
                manager=PackageManager.apt,
                requirement_refs=["system-package:octave"],
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:octave-provider-python",
                ordinal=2,
                action="install-provider-python-dependencies",
                manager=PackageManager.pip,
                artifact_ref=reqs.asset_id,
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:octave-smoke-test",
                ordinal=3,
                action="run-bounded-octave-linear-solve-smoke-test",
            ),
        ],
        source_environment_ref="runtime-environment:octave-provider:v1",
        source_job_refs=[],
        source_workflow_refs=[],
        state=EnvironmentPackageState.verified,
        provenance={
            "source_release": CORE_RELEASE,
            "core_builds_environment": False,
            "execution_host_builds_environment": True,
        },
        metadata={
            "octave_version": OCTAVE_VERSION,
            "provider_version": PROVIDER_VERSION,
            "arbitrary_octave_code": False,
        },
    )


def reference_security_policy() -> RuntimeSecurityPolicy:
    isolation = RuntimeIsolationProfile(
        isolation_profile_id="isolation-profile:octave-runtime-standard:v1",
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
        resource_budget_ref="resource-budget:octave-runtime-standard:v1",
        syscall_policy_ref="syscall-policy:octave-runtime-standard:v1",
    )
    return RuntimeSecurityPolicy(
        security_policy_id="runtime-security-policy:octave-runtime-standard:v1",
        policy_version="1.0.0",
        name="Octave Runtime Standard Policy",
        isolation_profile=isolation,
        allowed_runtime_refs=[RUNTIME_ID],
        allowed_adapter_refs=[ADAPTER_ID],
        allowed_operations={RUNTIME_ID: list(OCTAVE_OPERATIONS)},
        allowed_filesystem_prefixes=[
            "/workspace",
            "/tmp/sc-octave-runtime",
            "/var/lib/sc-octave-runtime/artifacts",
            "/var/lib/sc-octave-runtime/work",
        ],
        allowed_artifact_egress_classes=[
            "research-artifact",
            "numerical-result",
            "octave-diagnostics",
        ],
        execution_policy_ref="execution-policy:octave-runtime-standard:v1",
        provenance={"source_release": CORE_RELEASE, "policy_owner": "platform-governance"},
        metadata={
            "arbitrary_octave_source_allowed": False,
            "octave_package_install_allowed": False,
            "caller_filesystem_paths_allowed": False,
        },
    )


def reference_runtime_bundle() -> OctaveRuntimeBundle:
    request = OctaveExecutionRequest(
        octave_request_id="octave-request:reference-linear-solve:001",
        operation=OctaveOperation.linear_solve,
        payload=OctaveNumericPayload(
            payload_id="octave-payload:reference-linear-solve:v1",
            values={"A": [[3.0, 1.0], [1.0, 2.0]], "b": [9.0, 8.0]},
            metadata={"expected_solution": [2.0, 3.0]},
        ),
        computational_job_ref="job:octave-reference-linear-solve:001",
        provenance={"originating_product": "workbench", "execution_owner": "workspace-or-execution-host"},
    )
    contract = OctaveExecutionResultContract(
        result_contract_id="octave-result-contract:reference-linear-solve:001",
        octave_request_ref=request.octave_request_id,
        operation=request.operation,
        expected_artifact_kinds=["octave-result-json", "octave-run-log"],
        expected_result_kinds=["numerical-vector", "octave-diagnostics"],
        metadata={"numerical_tolerance_required": True, "scientific_validity_certified": False},
    )
    return OctaveRuntimeBundle(
        bundle_id="octave-runtime-bundle:reference:v1",
        registration=OctaveRuntimeRegistration(
            registration_id="octave-runtime-registration:v1",
            metadata={
                "native_cli": "octave-cli",
                "arbitrary_octave_code": False,
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
            "stan-runtime-bundle:reference:v1",
        ],
        metadata={"reference_is_contract_proof": True, "live_provider_execution_occurs_outside_core": True},
    )


def to_scientific_octave_artifact(bundle: OctaveRuntimeBundle) -> dict[str, Any]:
    return {
        "artifact_id": f"scientific-artifact:{bundle.bundle_id}",
        "artifact_kind": "package",
        "uri": f"core-ref://{bundle.bundle_id}",
        "content_sha256": bundle.fingerprint(),
        "media_type": "application/vnd.sustainable-catalyst.octave-runtime+json",
        "source_contract": CONTRACT_VERSION,
        "source_object_ref": bundle.bundle_id,
        "metadata": {
            "runtime_id": bundle.registration.runtime_id,
            "provider_version": bundle.registration.provider_version,
            "octave_version": bundle.registration.octave_version,
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
        "octave_version": OCTAVE_VERSION,
        "runtime_id": RUNTIME_ID,
        "adapter_id": ADAPTER_ID,
        "operations": list(OCTAVE_OPERATIONS),
        "capabilities": {
            "matrix_compute": True,
            "linear_system_solving": True,
            "eigenvalue_analysis": True,
            "singular_value_decomposition": True,
            "fast_fourier_transform": True,
            "polynomial_root_solving": True,
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
            "core_executes_octave": False,
            "provider_executes_octave": True,
            "arbitrary_octave_source": False,
            "shell_execution": False,
            "runtime_package_install_via_api": False,
            "caller_filesystem_paths": False,
            "core_selects_method": False,
            "core_certifies_numerical_validity": False,
            "core_certifies_scientific_validity": False,
        },
        "reference": {
            "bundle_id": bundle.bundle_id,
            "environment_package_id": bundle.environment_package.environment_package_id,
            "security_policy_id": bundle.security_policy.security_policy_id,
            "reference_request_id": bundle.reference_request.octave_request_id,
            "reference_operation": bundle.reference_request.operation.value,
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
    }
