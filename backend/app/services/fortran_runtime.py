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

CORE_RELEASE = "3.50.0"
CONTRACT_VERSION = "sc.core.fortran-runtime.v1"
PROVIDER_VERSION = "1.0.0"
GFORTRAN_VERSION = "13.3.0"
GFORTRAN_PACKAGE_VERSION = "13.3.0-6ubuntu2~24.04.1"
RUNTIME_ID = "sc-runtime-fortran"
ADAPTER_ID = "adapter:sc-runtime-fortran"
SERVICE_NAME = "sc-fortran-runtime"
SERVICE_ENDPOINT = "http://127.0.0.1:18099"

FORTRAN_OPERATIONS = [
    "dot_product",
    "matrix_multiply",
    "trapezoidal_integral",
    "central_difference",
    "rk4_linear_step",
    "heat_step_1d",
]


class FortranOperation(str, Enum):
    dot_product = "dot_product"
    matrix_multiply = "matrix_multiply"
    trapezoidal_integral = "trapezoidal_integral"
    central_difference = "central_difference"
    rk4_linear_step = "rk4_linear_step"
    heat_step_1d = "heat_step_1d"


class FortranExecutionState(str, Enum):
    declared = "declared"
    prepared = "prepared"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


def _finite_vector(values: list[float], name: str, *, min_len: int = 1, max_len: int = 262144) -> None:
    if len(values) < min_len or len(values) > max_len:
        raise ValueError(f"{name} length must be between {min_len} and {max_len}")
    if any(not math.isfinite(float(x)) for x in values):
        raise ValueError(f"{name} values must be finite")


def _matrix_shape(matrix: list[list[float]], name: str) -> tuple[int, int]:
    if not matrix or not matrix[0]:
        raise ValueError(f"{name} must be a non-empty matrix")
    rows, cols = len(matrix), len(matrix[0])
    if rows > 256 or cols > 256:
        raise ValueError(f"{name} dimensions must not exceed 256x256")
    if any(len(row) != cols for row in matrix):
        raise ValueError(f"{name} must be rectangular")
    if any(not math.isfinite(float(v)) for row in matrix for v in row):
        raise ValueError(f"{name} values must be finite")
    return rows, cols


class FortranNumericInput(BaseModel):
    vector_a: list[float] = Field(default_factory=list)
    vector_b: list[float] = Field(default_factory=list)
    matrix_a: list[list[float]] = Field(default_factory=list)
    matrix_b: list[list[float]] = Field(default_factory=list)
    x: list[float] = Field(default_factory=list)
    y: list[float] = Field(default_factory=list)
    index: int | None = None
    scalar_y: float | None = None
    step_size: float | None = None
    coefficient_a: float | None = None
    coefficient_b: float | None = None
    alpha_dt_dx2: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class FortranExecutionSettings(BaseModel):
    max_execution_seconds: int = Field(default=120, ge=1, le=1800)
    optimization_level: int = Field(default=2, ge=0, le=2)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class FortranExecutionRequest(BaseModel):
    fortran_request_id: str = Field(min_length=2, max_length=500)
    operation: FortranOperation
    inputs: FortranNumericInput
    settings: FortranExecutionSettings = Field(default_factory=FortranExecutionSettings)
    computational_job_ref: str = Field(min_length=2, max_length=500)
    environment_package_ref: str = "environment-package:fortran-runtime:v1"
    security_policy_ref: str = "runtime-security-policy:fortran-runtime-standard:v1"
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self):
        i, op = self.inputs, self.operation
        if op == FortranOperation.dot_product:
            _finite_vector(i.vector_a, "vector_a")
            _finite_vector(i.vector_b, "vector_b")
            if len(i.vector_a) != len(i.vector_b):
                raise ValueError("dot_product requires equal vector lengths")
        elif op == FortranOperation.matrix_multiply:
            ar, ac = _matrix_shape(i.matrix_a, "matrix_a")
            br, bc = _matrix_shape(i.matrix_b, "matrix_b")
            if ac != br:
                raise ValueError("matrix_multiply requires matrix_a columns == matrix_b rows")
            if ar * bc > 65536:
                raise ValueError("matrix_multiply output exceeds 65536 elements")
        elif op == FortranOperation.trapezoidal_integral:
            _finite_vector(i.x, "x", min_len=2)
            _finite_vector(i.y, "y", min_len=2)
            if len(i.x) != len(i.y):
                raise ValueError("trapezoidal_integral requires equal x/y lengths")
            if any(i.x[j+1] <= i.x[j] for j in range(len(i.x)-1)):
                raise ValueError("x must be strictly increasing")
        elif op == FortranOperation.central_difference:
            _finite_vector(i.x, "x", min_len=3)
            _finite_vector(i.y, "y", min_len=3)
            if len(i.x) != len(i.y):
                raise ValueError("central_difference requires equal x/y lengths")
            if i.index is None or i.index < 1 or i.index > len(i.x)-2:
                raise ValueError("central_difference index must be an interior zero-based index")
            if i.x[i.index+1] == i.x[i.index-1]:
                raise ValueError("central_difference denominator cannot be zero")
        elif op == FortranOperation.rk4_linear_step:
            vals = [i.scalar_y, i.step_size, i.coefficient_a, i.coefficient_b]
            if any(v is None for v in vals):
                raise ValueError("rk4_linear_step requires scalar_y, step_size, coefficient_a and coefficient_b")
            if any(not math.isfinite(float(v)) for v in vals if v is not None):
                raise ValueError("rk4_linear_step values must be finite")
            if i.step_size == 0:
                raise ValueError("rk4_linear_step step_size cannot be zero")
        elif op == FortranOperation.heat_step_1d:
            _finite_vector(i.vector_a, "vector_a", min_len=3)
            if i.alpha_dt_dx2 is None or not math.isfinite(float(i.alpha_dt_dx2)):
                raise ValueError("heat_step_1d requires finite alpha_dt_dx2")
            if i.alpha_dt_dx2 < 0 or i.alpha_dt_dx2 > 0.5:
                raise ValueError("heat_step_1d requires 0 <= alpha_dt_dx2 <= 0.5 for the explicit reference scheme")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class FortranExecutionResultContract(BaseModel):
    result_contract_id: str = Field(min_length=2, max_length=500)
    fortran_request_ref: str = Field(min_length=2, max_length=500)
    operation: FortranOperation
    expected_artifact_kinds: list[str] = Field(default_factory=list)
    expected_result_kinds: list[str] = Field(default_factory=list)
    state: FortranExecutionState = FortranExecutionState.declared
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_contract(self):
        if not self.expected_artifact_kinds and not self.expected_result_kinds:
            raise ValueError("Fortran result contract requires artifact or result kinds")
        if len(self.expected_artifact_kinds) != len(set(self.expected_artifact_kinds)):
            raise ValueError("duplicate Fortran artifact kinds")
        if len(self.expected_result_kinds) != len(set(self.expected_result_kinds)):
            raise ValueError("duplicate Fortran result kinds")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        return canonical_sha256(payload)


class FortranRuntimeRegistration(BaseModel):
    registration_id: str = Field(min_length=2, max_length=500)
    runtime_id: str = RUNTIME_ID
    provider_version: str = PROVIDER_VERSION
    gfortran_version: str = GFORTRAN_VERSION
    gfortran_package_version: str = GFORTRAN_PACKAGE_VERSION
    adapter_id: str = ADAPTER_ID
    service_name: str = SERVICE_NAME
    endpoint: str = SERVICE_ENDPOINT
    operations: list[str] = Field(default_factory=lambda: list(FORTRAN_OPERATIONS))
    runtime_contract: str = CONTRACT_VERSION
    runtime_kind: str = "language"
    language: str = "fortran"
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_registration(self):
        if self.runtime_id != RUNTIME_ID or self.adapter_id != ADAPTER_ID:
            raise ValueError("Fortran runtime identity mismatch")
        if self.provider_version != PROVIDER_VERSION:
            raise ValueError("Fortran provider version mismatch")
        if set(self.operations) != set(FORTRAN_OPERATIONS):
            raise ValueError("Fortran operation set mismatch")
        if len(self.operations) != len(set(self.operations)):
            raise ValueError("Fortran operations must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class FortranRuntimeBundle(BaseModel):
    bundle_id: str = Field(min_length=2, max_length=500)
    registration: FortranRuntimeRegistration
    environment_package: ReproducibleEnvironmentPackage
    security_policy: RuntimeSecurityPolicy
    reference_request: FortranExecutionRequest
    result_contract: FortranExecutionResultContract
    source_object_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.reference_request.environment_package_ref != self.environment_package.environment_package_id:
            raise ValueError("Fortran request/environment mismatch")
        if self.reference_request.security_policy_ref != self.security_policy.security_policy_id:
            raise ValueError("Fortran request/security mismatch")
        if self.result_contract.fortran_request_ref != self.reference_request.fortran_request_id:
            raise ValueError("Fortran result/request mismatch")
        if self.result_contract.operation != self.reference_request.operation:
            raise ValueError("Fortran operation mismatch")
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
        asset_id="environment-asset:fortran-runtime-manifest",
        kind=EnvironmentAssetKind.manifest,
        uri="core-ref://runtime-manifests/gfortran-13.3.0-noble.json",
        content_sha256="e" * 64,
        media_type="application/json",
        size_bytes=512,
    )
    reqs = EnvironmentAsset(
        asset_id="environment-asset:fortran-provider-requirements",
        kind=EnvironmentAssetKind.lockfile,
        uri="core-ref://runtime-locks/fortran-provider-requirements.txt",
        content_sha256="f" * 64,
        media_type="text/plain",
        size_bytes=256,
    )
    return ReproducibleEnvironmentPackage(
        environment_package_id="environment-package:fortran-runtime:v1",
        name="Sustainable Catalyst Fortran Runtime Environment",
        package_version="1.0.0",
        platform=platform,
        runtimes=[RuntimeEnvironmentRequirement(
            runtime_requirement_id="runtime-requirement:fortran-provider",
            runtime_ref=RUNTIME_ID,
            runtime_version=PROVIDER_VERSION,
            runtime_adapter_ref=ADAPTER_ID,
        )],
        system_packages=[SystemPackageRequirement(
            requirement_id="system-package:gfortran-13",
            manager=PackageManager.apt,
            name="gfortran-13",
            version=GFORTRAN_PACKAGE_VERSION,
            source=RequirementSource.operating_system,
        )],
        language_packages=[],
        environment_variables=[
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:fortran-artifact-root",
                name="SC_FORTRAN_ARTIFACT_ROOT",
                kind=EnvironmentVariableKind.path,
                value="/var/lib/sc-fortran-runtime/artifacts",
            ),
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:fortran-work-root",
                name="SC_FORTRAN_WORK_ROOT",
                kind=EnvironmentVariableKind.path,
                value="/var/lib/sc-fortran-runtime/work",
            ),
        ],
        assets=[manifest, reqs],
        build_instructions=[
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:fortran-system-package",
                ordinal=1,
                action="install-pinned-gfortran-13",
                manager=PackageManager.apt,
                requirement_refs=["system-package:gfortran-13"],
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:fortran-provider-python",
                ordinal=2,
                action="install-provider-python-dependencies",
                manager=PackageManager.pip,
                artifact_ref=reqs.asset_id,
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:fortran-smoke-test",
                ordinal=3,
                action="run-bounded-native-fortran-dot-product-smoke-test",
            ),
        ],
        source_environment_ref="runtime-environment:fortran-provider:v1",
        source_job_refs=[],
        source_workflow_refs=[],
        state=EnvironmentPackageState.verified,
        provenance={
            "source_release": CORE_RELEASE,
            "core_builds_environment": False,
            "execution_host_builds_environment": True,
        },
        metadata={
            "gfortran_version": GFORTRAN_VERSION,
            "gfortran_package_version": GFORTRAN_PACKAGE_VERSION,
            "provider_version": PROVIDER_VERSION,
            "arbitrary_fortran_source": False,
            "compiler_flags": ["-O2", "-std=f2008", "-fno-unsafe-math-optimizations"],
        },
    )


def reference_security_policy() -> RuntimeSecurityPolicy:
    isolation = RuntimeIsolationProfile(
        isolation_profile_id="isolation-profile:fortran-runtime-standard:v1",
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
        resource_budget_ref="resource-budget:fortran-runtime-standard:v1",
        syscall_policy_ref="syscall-policy:fortran-runtime-standard:v1",
    )
    return RuntimeSecurityPolicy(
        security_policy_id="runtime-security-policy:fortran-runtime-standard:v1",
        policy_version="1.0.0",
        name="Fortran Runtime Standard Policy",
        isolation_profile=isolation,
        allowed_runtime_refs=[RUNTIME_ID],
        allowed_adapter_refs=[ADAPTER_ID],
        allowed_operations={RUNTIME_ID: list(FORTRAN_OPERATIONS)},
        allowed_filesystem_prefixes=[
            "/workspace",
            "/tmp/sc-fortran-runtime",
            "/var/lib/sc-fortran-runtime/artifacts",
            "/var/lib/sc-fortran-runtime/work",
        ],
        allowed_artifact_egress_classes=[
            "research-artifact",
            "scientific-compute-result",
            "fortran-diagnostics",
        ],
        execution_policy_ref="execution-policy:fortran-runtime-standard:v1",
        provenance={"source_release": CORE_RELEASE, "policy_owner": "platform-governance"},
        metadata={
            "arbitrary_fortran_source_allowed": False,
            "runtime_package_install_allowed": False,
            "caller_filesystem_paths_allowed": False,
            "compiler_invocation_provider_managed": True,
        },
    )


def reference_runtime_bundle() -> FortranRuntimeBundle:
    request = FortranExecutionRequest(
        fortran_request_id="fortran-request:reference-dot-product:001",
        operation=FortranOperation.dot_product,
        inputs=FortranNumericInput(vector_a=[1.0, 2.0, 3.0], vector_b=[4.0, 5.0, 6.0]),
        computational_job_ref="job:fortran-reference-dot-product:001",
        provenance={
            "originating_product": "workbench",
            "execution_owner": "workspace-or-execution-host",
        },
    )
    contract = FortranExecutionResultContract(
        result_contract_id="fortran-result-contract:reference-dot-product:001",
        fortran_request_ref=request.fortran_request_id,
        operation=request.operation,
        expected_artifact_kinds=["fortran-generated-source", "fortran-result-json", "fortran-compile-log", "fortran-run-log"],
        expected_result_kinds=["scientific-numeric-result", "fortran-diagnostics"],
        metadata={
            "scientific_validity_certified": False,
            "source_is_provider_generated": True,
        },
    )
    return FortranRuntimeBundle(
        bundle_id="fortran-runtime-bundle:reference:v1",
        registration=FortranRuntimeRegistration(
            registration_id="fortran-runtime-registration:v1",
            metadata={
                "native_compiler": "gfortran-13",
                "fortran_standard": "Fortran 2008",
                "arbitrary_fortran_code": False,
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
            "haskell-runtime-bundle:reference:v1",
        ],
        metadata={
            "reference_is_contract_proof": True,
            "live_provider_execution_occurs_outside_core": True,
        },
    )


def to_scientific_fortran_artifact(bundle: FortranRuntimeBundle) -> dict[str, Any]:
    return {
        "artifact_id": f"scientific-artifact:{bundle.bundle_id}",
        "artifact_kind": "package",
        "uri": f"core-ref://{bundle.bundle_id}",
        "content_sha256": bundle.fingerprint(),
        "media_type": "application/vnd.sustainable-catalyst.fortran-runtime+json",
        "source_contract": CONTRACT_VERSION,
        "source_object_ref": bundle.bundle_id,
        "metadata": {
            "runtime_id": bundle.registration.runtime_id,
            "provider_version": bundle.registration.provider_version,
            "gfortran_version": bundle.registration.gfortran_version,
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
        "gfortran_version": GFORTRAN_VERSION,
        "gfortran_package_version": GFORTRAN_PACKAGE_VERSION,
        "runtime_id": RUNTIME_ID,
        "adapter_id": ADAPTER_ID,
        "language": "fortran",
        "operations": list(FORTRAN_OPERATIONS),
        "capabilities": {
            "scientific_hpc": True,
            "numerical_compute": True,
            "matrix_compute": True,
            "numerical_integration": True,
            "finite_difference_methods": True,
            "differential_equation_methods": True,
            "provider_managed_compilation": True,
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
            "core_executes_fortran": False,
            "provider_compiles_and_executes_fortran": True,
            "arbitrary_fortran_source": False,
            "shell_execution": False,
            "runtime_package_install_via_api": False,
            "caller_filesystem_paths": False,
            "core_selects_numerical_method": False,
            "core_certifies_numerical_validity": False,
            "core_certifies_scientific_validity": False,
        },
        "reference": {
            "bundle_id": bundle.bundle_id,
            "environment_package_id": bundle.environment_package.environment_package_id,
            "security_policy_id": bundle.security_policy.security_policy_id,
            "reference_request_id": bundle.reference_request.fortran_request_id,
            "reference_operation": bundle.reference_request.operation.value,
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
    }
