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

CORE_RELEASE = "3.48.0"
CONTRACT_VERSION = "sc.core.gretl-hansl-runtime.v1"
PROVIDER_VERSION = "1.0.0"
GRETL_VERSION = "2023c"
GRETL_PACKAGE_VERSION = "2023c-2.1build3"
RUNTIME_ID = "sc-runtime-gretl"
ADAPTER_ID = "adapter:sc-runtime-gretl"
SERVICE_NAME = "sc-gretl-runtime"
SERVICE_ENDPOINT = "http://127.0.0.1:18097"

GRETL_OPERATIONS = [
    "ols",
    "robust_ols",
    "logit",
    "probit",
    "descriptive_summary",
    "correlation_matrix",
]


class GretlOperation(str, Enum):
    ols = "ols"
    robust_ols = "robust_ols"
    logit = "logit"
    probit = "probit"
    descriptive_summary = "descriptive_summary"
    correlation_matrix = "correlation_matrix"


class GretlExecutionState(str, Enum):
    declared = "declared"
    prepared = "prepared"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class GretlDataset(BaseModel):
    dataset_id: str = Field(min_length=2, max_length=500)
    columns: dict[str, list[float | int]] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dataset(self):
        if not self.columns:
            raise ValueError("gretl dataset requires columns")
        lengths = {len(v) for v in self.columns.values()}
        if len(lengths) != 1:
            raise ValueError("gretl dataset columns must have equal lengths")
        if next(iter(lengths)) < 2:
            raise ValueError("gretl dataset requires at least two observations")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GretlModelSpecification(BaseModel):
    dependent_variable: str | None = Field(default=None, max_length=100)
    predictors: list[str] = Field(default_factory=list)
    include_constant: bool = True
    variables: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_specification(self):
        if len(self.predictors) != len(set(self.predictors)):
            raise ValueError("predictors must be unique")
        if len(self.variables) != len(set(self.variables)):
            raise ValueError("variables must be unique")
        if self.dependent_variable and self.dependent_variable in self.predictors:
            raise ValueError("dependent variable cannot also be a predictor")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GretlExecutionSettings(BaseModel):
    max_execution_seconds: int = Field(default=120, ge=1, le=1800)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GretlExecutionRequest(BaseModel):
    gretl_request_id: str = Field(min_length=2, max_length=500)
    operation: GretlOperation
    dataset: GretlDataset
    specification: GretlModelSpecification
    settings: GretlExecutionSettings = Field(default_factory=GretlExecutionSettings)
    computational_job_ref: str = Field(min_length=2, max_length=500)
    environment_package_ref: str = "environment-package:gretl-hansl-runtime:v1"
    security_policy_ref: str = "runtime-security-policy:gretl-hansl-runtime-standard:v1"
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self):
        names = set(self.dataset.columns)
        if self.operation in {
            GretlOperation.ols,
            GretlOperation.robust_ols,
            GretlOperation.logit,
            GretlOperation.probit,
        }:
            if not self.specification.dependent_variable:
                raise ValueError("model operation requires dependent_variable")
            if not self.specification.predictors:
                raise ValueError("model operation requires predictors")
            needed = {self.specification.dependent_variable, *self.specification.predictors}
        else:
            if not self.specification.variables:
                raise ValueError("summary/correlation operation requires variables")
            needed = set(self.specification.variables)
        missing = needed - names
        if missing:
            raise ValueError("specification references missing dataset columns: " + ", ".join(sorted(missing)))
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GretlExecutionResultContract(BaseModel):
    result_contract_id: str = Field(min_length=2, max_length=500)
    gretl_request_ref: str = Field(min_length=2, max_length=500)
    operation: GretlOperation
    expected_artifact_kinds: list[str] = Field(default_factory=list)
    expected_result_kinds: list[str] = Field(default_factory=list)
    state: GretlExecutionState = GretlExecutionState.declared
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_contract(self):
        if not self.expected_artifact_kinds and not self.expected_result_kinds:
            raise ValueError("gretl result contract requires artifact or result kinds")
        if len(self.expected_artifact_kinds) != len(set(self.expected_artifact_kinds)):
            raise ValueError("duplicate gretl artifact kinds")
        if len(self.expected_result_kinds) != len(set(self.expected_result_kinds)):
            raise ValueError("duplicate gretl result kinds")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        return canonical_sha256(payload)


class GretlRuntimeRegistration(BaseModel):
    registration_id: str = Field(min_length=2, max_length=500)
    runtime_id: str = RUNTIME_ID
    provider_version: str = PROVIDER_VERSION
    gretl_version: str = GRETL_VERSION
    gretl_package_version: str = GRETL_PACKAGE_VERSION
    adapter_id: str = ADAPTER_ID
    service_name: str = SERVICE_NAME
    endpoint: str = SERVICE_ENDPOINT
    operations: list[str] = Field(default_factory=lambda: list(GRETL_OPERATIONS))
    runtime_contract: str = CONTRACT_VERSION
    runtime_kind: str = "domain"
    language: str = "hansl"
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_registration(self):
        if self.runtime_id != RUNTIME_ID or self.adapter_id != ADAPTER_ID:
            raise ValueError("gretl runtime identity mismatch")
        if self.provider_version != PROVIDER_VERSION:
            raise ValueError("gretl provider version mismatch")
        if set(self.operations) != set(GRETL_OPERATIONS):
            raise ValueError("gretl operation set mismatch")
        if len(self.operations) != len(set(self.operations)):
            raise ValueError("gretl operations must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GretlRuntimeBundle(BaseModel):
    bundle_id: str = Field(min_length=2, max_length=500)
    registration: GretlRuntimeRegistration
    environment_package: ReproducibleEnvironmentPackage
    security_policy: RuntimeSecurityPolicy
    reference_request: GretlExecutionRequest
    result_contract: GretlExecutionResultContract
    source_object_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.reference_request.environment_package_ref != self.environment_package.environment_package_id:
            raise ValueError("gretl request/environment mismatch")
        if self.reference_request.security_policy_ref != self.security_policy.security_policy_id:
            raise ValueError("gretl request/security mismatch")
        if self.result_contract.gretl_request_ref != self.reference_request.gretl_request_id:
            raise ValueError("gretl result/request mismatch")
        if self.result_contract.operation != self.reference_request.operation:
            raise ValueError("gretl operation mismatch")
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
        asset_id="environment-asset:gretl-hansl-runtime-manifest",
        kind=EnvironmentAssetKind.manifest,
        uri="core-ref://runtime-manifests/gretl-2023c-noble.json",
        content_sha256="c" * 64,
        media_type="application/json",
        size_bytes=512,
    )
    reqs = EnvironmentAsset(
        asset_id="environment-asset:gretl-provider-requirements",
        kind=EnvironmentAssetKind.lockfile,
        uri="core-ref://runtime-locks/gretl-provider-requirements.txt",
        content_sha256="d" * 64,
        media_type="text/plain",
        size_bytes=256,
    )
    return ReproducibleEnvironmentPackage(
        environment_package_id="environment-package:gretl-hansl-runtime:v1",
        name="Sustainable Catalyst gretl/hansl Runtime Environment",
        package_version="1.0.0",
        platform=platform,
        runtimes=[
            RuntimeEnvironmentRequirement(
                runtime_requirement_id="runtime-requirement:gretl-provider",
                runtime_ref=RUNTIME_ID,
                runtime_version=PROVIDER_VERSION,
                runtime_adapter_ref=ADAPTER_ID,
            )
        ],
        system_packages=[
            SystemPackageRequirement(
                requirement_id="system-package:gretl",
                manager=PackageManager.apt,
                name="gretl",
                version=GRETL_PACKAGE_VERSION,
                source=RequirementSource.operating_system,
            ),
            SystemPackageRequirement(
                requirement_id="system-package:gretl-common",
                manager=PackageManager.apt,
                name="gretl-common",
                version=GRETL_PACKAGE_VERSION,
                source=RequirementSource.operating_system,
            ),
        ],
        language_packages=[],
        environment_variables=[
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:gretl-artifact-root",
                name="SC_GRETL_ARTIFACT_ROOT",
                kind=EnvironmentVariableKind.path,
                value="/var/lib/sc-gretl-runtime/artifacts",
            ),
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:gretl-work-root",
                name="SC_GRETL_WORK_ROOT",
                kind=EnvironmentVariableKind.path,
                value="/var/lib/sc-gretl-runtime/work",
            ),
        ],
        assets=[manifest, reqs],
        build_instructions=[
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:gretl-system-packages",
                ordinal=1,
                action="install-pinned-gretl",
                manager=PackageManager.apt,
                requirement_refs=["system-package:gretl", "system-package:gretl-common"],
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:gretl-provider-python",
                ordinal=2,
                action="install-provider-python-dependencies",
                manager=PackageManager.pip,
                artifact_ref=reqs.asset_id,
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:gretl-smoke-test",
                ordinal=3,
                action="run-bounded-gretl-ols-smoke-test",
            ),
        ],
        source_environment_ref="runtime-environment:gretl-provider:v1",
        source_job_refs=[],
        source_workflow_refs=[],
        state=EnvironmentPackageState.verified,
        provenance={
            "source_release": CORE_RELEASE,
            "core_builds_environment": False,
            "execution_host_builds_environment": True,
        },
        metadata={
            "gretl_version": GRETL_VERSION,
            "gretl_package_version": GRETL_PACKAGE_VERSION,
            "provider_version": PROVIDER_VERSION,
            "arbitrary_hansl_code": False,
        },
    )


def reference_security_policy() -> RuntimeSecurityPolicy:
    isolation = RuntimeIsolationProfile(
        isolation_profile_id="isolation-profile:gretl-hansl-runtime-standard:v1",
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
        resource_budget_ref="resource-budget:gretl-runtime-standard:v1",
        syscall_policy_ref="syscall-policy:gretl-runtime-standard:v1",
    )
    return RuntimeSecurityPolicy(
        security_policy_id="runtime-security-policy:gretl-hansl-runtime-standard:v1",
        policy_version="1.0.0",
        name="gretl/hansl Runtime Standard Policy",
        isolation_profile=isolation,
        allowed_runtime_refs=[RUNTIME_ID],
        allowed_adapter_refs=[ADAPTER_ID],
        allowed_operations={RUNTIME_ID: list(GRETL_OPERATIONS)},
        allowed_filesystem_prefixes=[
            "/workspace",
            "/tmp/sc-gretl-runtime",
            "/var/lib/sc-gretl-runtime/artifacts",
            "/var/lib/sc-gretl-runtime/work",
        ],
        allowed_artifact_egress_classes=[
            "research-artifact",
            "econometric-result",
            "gretl-transcript",
        ],
        execution_policy_ref="execution-policy:gretl-runtime-standard:v1",
        provenance={"source_release": CORE_RELEASE, "policy_owner": "platform-governance"},
        metadata={
            "arbitrary_hansl_source_allowed": False,
            "gretl_package_install_allowed": False,
            "caller_filesystem_paths_allowed": False,
        },
    )


def reference_runtime_bundle() -> GretlRuntimeBundle:
    dataset = GretlDataset(
        dataset_id="gretl-dataset:reference-ols:v1",
        columns={
            "y": [1.0, 2.0, 2.9, 4.1, 5.2],
            "x": [0.0, 1.0, 2.0, 3.0, 4.0],
        },
        metadata={"reference_dataset": True},
    )
    request = GretlExecutionRequest(
        gretl_request_id="gretl-request:reference-ols:001",
        operation=GretlOperation.ols,
        dataset=dataset,
        specification=GretlModelSpecification(
            dependent_variable="y",
            predictors=["x"],
            include_constant=True,
        ),
        computational_job_ref="job:gretl-reference-ols:001",
        provenance={
            "originating_product": "research-lab",
            "execution_owner": "workspace-or-execution-host",
        },
    )
    contract = GretlExecutionResultContract(
        result_contract_id="gretl-result-contract:reference-ols:001",
        gretl_request_ref=request.gretl_request_id,
        operation=request.operation,
        expected_artifact_kinds=["gretl-transcript", "econometric-result-json"],
        expected_result_kinds=["regression-coefficients", "econometric-diagnostics"],
        metadata={
            "scientific_validity_certified": False,
            "model_specification_owned_by_product": True,
        },
    )
    return GretlRuntimeBundle(
        bundle_id="gretl-hansl-runtime-bundle:reference:v1",
        registration=GretlRuntimeRegistration(
            registration_id="gretl-runtime-registration:v1",
            metadata={
                "native_cli": "gretlcli",
                "language": "hansl",
                "arbitrary_hansl_code": False,
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
            "octave-runtime-bundle:reference:v1",
        ],
        metadata={
            "reference_is_contract_proof": True,
            "live_provider_execution_occurs_outside_core": True,
        },
    )


def to_scientific_gretl_artifact(bundle: GretlRuntimeBundle) -> dict[str, Any]:
    return {
        "artifact_id": f"scientific-artifact:{bundle.bundle_id}",
        "artifact_kind": "package",
        "uri": f"core-ref://{bundle.bundle_id}",
        "content_sha256": bundle.fingerprint(),
        "media_type": "application/vnd.sustainable-catalyst.gretl-hansl-runtime+json",
        "source_contract": CONTRACT_VERSION,
        "source_object_ref": bundle.bundle_id,
        "metadata": {
            "runtime_id": bundle.registration.runtime_id,
            "provider_version": bundle.registration.provider_version,
            "gretl_version": bundle.registration.gretl_version,
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
        "gretl_version": GRETL_VERSION,
        "gretl_package_version": GRETL_PACKAGE_VERSION,
        "runtime_id": RUNTIME_ID,
        "adapter_id": ADAPTER_ID,
        "language": "hansl",
        "operations": list(GRETL_OPERATIONS),
        "capabilities": {
            "econometrics": True,
            "ordinary_least_squares": True,
            "robust_ols": True,
            "binary_logit": True,
            "binary_probit": True,
            "descriptive_statistics": True,
            "correlation_analysis": True,
            "reproducible_environment_package": True,
            "runtime_security_policy": True,
            "runtime_adapter_registration": True,
            "unified_runtime_catalog_integration": True,
            "workspace_product_profile_integration": True,
            "research_lab_product_profile_integration": True,
            "scientific_registry_bridge": True,
        },
        "boundaries": {
            "core_executes_gretl": False,
            "provider_executes_gretl": True,
            "arbitrary_hansl_source": False,
            "shell_execution": False,
            "runtime_package_install_via_api": False,
            "caller_filesystem_paths": False,
            "core_selects_model": False,
            "core_certifies_econometric_validity": False,
            "core_certifies_scientific_validity": False,
        },
        "reference": {
            "bundle_id": bundle.bundle_id,
            "environment_package_id": bundle.environment_package.environment_package_id,
            "security_policy_id": bundle.security_policy.security_policy_id,
            "reference_request_id": bundle.reference_request.gretl_request_id,
            "reference_operation": bundle.reference_request.operation.value,
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
    }
