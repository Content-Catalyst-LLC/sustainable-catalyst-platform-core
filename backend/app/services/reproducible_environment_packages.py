from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.41.0"
CONTRACT_VERSION = "sc.core.reproducible-environment-package.v1"

EXECUTION_ENVIRONMENT_CONTRACT = "sc.core.execution-environment-provenance.v1"
RUNTIME_OBJECT_CONTRACT = "sc.core.computational-runtime-object.v1"
RUNTIME_ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"
COMPUTATIONAL_JOB_CONTRACT = "sc.core.computational-job.v1"
RUNTIME_INTERCHANGE_CONTRACT = "sc.core.runtime-data-interchange.v1"
CROSS_RUNTIME_WORKFLOW_CONTRACT = "sc.core.cross-runtime-research-workflow.v1"
SCIENTIFIC_REGISTRY_CONTRACT = "sc.core.scientific-result-artifact-registry.v1"

REFERENCE_R_RUNTIME = "sc-runtime-r"
REFERENCE_R_VERSION = "1.0.0"
REFERENCE_JULIA_RUNTIME = "catalyst-julia-runtime"
REFERENCE_JULIA_VERSION = "0.3.0"


class EnvironmentPackageState(str, Enum):
    declared = "declared"
    frozen = "frozen"
    verified = "verified"
    superseded = "superseded"
    archived = "archived"


class PackageManager(str, Enum):
    apt = "apt"
    apk = "apk"
    brew = "brew"
    pip = "pip"
    uv = "uv"
    conda = "conda"
    renv = "renv"
    cran = "cran"
    julia_pkg = "julia-pkg"
    cargo = "cargo"
    npm = "npm"
    other = "other"


class RequirementScope(str, Enum):
    system = "system"
    runtime = "runtime"
    analysis = "analysis"
    development = "development"
    optional = "optional"


class RequirementSource(str, Enum):
    registry = "registry"
    lockfile = "lockfile"
    local_artifact = "local-artifact"
    operating_system = "operating-system"
    runtime_distribution = "runtime-distribution"
    other = "other"


class EnvironmentAssetKind(str, Enum):
    lockfile = "lockfile"
    manifest = "manifest"
    containerfile = "containerfile"
    script = "script"
    configuration = "configuration"
    certificate = "certificate"
    dataset_schema = "dataset-schema"
    package_archive = "package-archive"
    other = "other"


class EnvironmentVerificationStatus(str, Enum):
    not_run = "not-run"
    passed = "passed"
    warning = "warning"
    failed = "failed"


class EnvironmentCompatibilityStatus(str, Enum):
    compatible = "compatible"
    compatible_with_warnings = "compatible-with-warnings"
    incompatible = "incompatible"
    unknown = "unknown"


class EnvironmentVariableKind(str, Enum):
    plain = "plain"
    path = "path"
    locale = "locale"
    timezone = "timezone"
    feature_flag = "feature-flag"
    secret_reference = "secret-reference"


class PlatformArchitecture(str, Enum):
    amd64 = "amd64"
    arm64 = "arm64"
    x86 = "x86"
    other = "other"


class PlatformDescriptor(BaseModel):
    operating_system: str = Field(min_length=1, max_length=200)
    operating_system_version: str | None = Field(default=None, max_length=200)
    architecture: PlatformArchitecture
    libc: str | None = Field(default=None, max_length=200)
    kernel_family: str | None = Field(default=None, max_length=200)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeEnvironmentRequirement(BaseModel):
    runtime_requirement_id: str = Field(min_length=2, max_length=500)
    runtime_ref: str = Field(min_length=2, max_length=500)
    runtime_version: str = Field(min_length=1, max_length=200)
    runtime_adapter_ref: str | None = Field(default=None, max_length=500)
    exact_version_required: bool = True
    executable_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SystemPackageRequirement(BaseModel):
    requirement_id: str = Field(min_length=2, max_length=500)
    manager: PackageManager
    name: str = Field(min_length=1, max_length=500)
    version: str | None = Field(default=None, max_length=300)
    architecture: PlatformArchitecture | None = None
    scope: RequirementScope = RequirementScope.system
    source: RequirementSource = RequirementSource.operating_system
    checksum_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class LanguagePackageRequirement(BaseModel):
    requirement_id: str = Field(min_length=2, max_length=500)
    runtime_ref: str = Field(min_length=2, max_length=500)
    manager: PackageManager
    name: str = Field(min_length=1, max_length=500)
    version: str = Field(min_length=1, max_length=300)
    scope: RequirementScope = RequirementScope.analysis
    source: RequirementSource = RequirementSource.lockfile
    source_uri: str | None = Field(default=None, max_length=4000)
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EnvironmentVariableDeclaration(BaseModel):
    variable_id: str = Field(min_length=2, max_length=500)
    name: str = Field(min_length=1, max_length=300)
    kind: EnvironmentVariableKind = EnvironmentVariableKind.plain
    value: str | None = Field(default=None, max_length=5000)
    secret_ref: str | None = Field(default=None, max_length=1000)
    required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def protect_secrets(self):
        if self.kind == EnvironmentVariableKind.secret_reference:
            if not self.secret_ref:
                raise ValueError("secret-reference environment variable requires secret_ref")
            if self.value is not None:
                raise ValueError("secret-reference environment variable must not contain secret value")
        elif self.secret_ref is not None:
            raise ValueError("secret_ref is only valid for secret-reference variables")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EnvironmentAsset(BaseModel):
    asset_id: str = Field(min_length=2, max_length=500)
    kind: EnvironmentAssetKind
    uri: str = Field(min_length=2, max_length=4000)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    media_type: str | None = Field(default=None, max_length=300)
    size_bytes: int | None = Field(default=None, ge=0)
    required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EnvironmentBuildInstruction(BaseModel):
    instruction_id: str = Field(min_length=2, max_length=500)
    ordinal: int = Field(ge=1)
    action: str = Field(min_length=1, max_length=300)
    manager: PackageManager | None = None
    artifact_ref: str | None = Field(default=None, max_length=1000)
    requirement_refs: list[str] = Field(default_factory=list)
    arguments: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReproducibleEnvironmentPackage(BaseModel):
    environment_package_id: str = Field(min_length=2, max_length=500)
    name: str = Field(min_length=1, max_length=500)
    package_version: str = Field(min_length=1, max_length=200)
    platform: PlatformDescriptor
    runtimes: list[RuntimeEnvironmentRequirement] = Field(default_factory=list)
    system_packages: list[SystemPackageRequirement] = Field(default_factory=list)
    language_packages: list[LanguagePackageRequirement] = Field(default_factory=list)
    environment_variables: list[EnvironmentVariableDeclaration] = Field(default_factory=list)
    assets: list[EnvironmentAsset] = Field(default_factory=list)
    build_instructions: list[EnvironmentBuildInstruction] = Field(default_factory=list)
    source_environment_ref: str | None = Field(default=None, max_length=1000)
    source_job_refs: list[str] = Field(default_factory=list)
    source_workflow_refs: list[str] = Field(default_factory=list)
    state: EnvironmentPackageState = EnvironmentPackageState.frozen
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_package(self):
        def unique(items: list[Any], attr: str, label: str):
            values = [getattr(item, attr) for item in items]
            if len(values) != len(set(values)):
                raise ValueError(f"{label} ids must be unique")

        unique(self.runtimes, "runtime_requirement_id", "runtime requirement")
        unique(self.system_packages, "requirement_id", "system package requirement")
        unique(self.language_packages, "requirement_id", "language package requirement")
        unique(self.environment_variables, "variable_id", "environment variable")
        unique(self.assets, "asset_id", "environment asset")
        unique(self.build_instructions, "instruction_id", "build instruction")

        if not self.runtimes:
            raise ValueError("reproducible environment package requires at least one runtime")

        ordinals = [item.ordinal for item in self.build_instructions]
        if ordinals and sorted(ordinals) != list(range(1, len(ordinals) + 1)):
            raise ValueError("environment build instruction ordinals must be contiguous from 1")

        names = [item.name for item in self.environment_variables]
        if len(names) != len(set(names)):
            raise ValueError("environment variable names must be unique")

        known_requirements = {
            item.requirement_id for item in self.system_packages
        } | {
            item.requirement_id for item in self.language_packages
        }
        known_assets = {item.asset_id for item in self.assets}

        for instruction in self.build_instructions:
            missing_requirements = set(instruction.requirement_refs) - known_requirements
            if missing_requirements:
                raise ValueError("build instruction references unknown requirement")
            if instruction.artifact_ref and instruction.artifact_ref not in known_assets:
                raise ValueError("build instruction references unknown environment asset")

        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class EnvironmentReproductionRequest(BaseModel):
    reproduction_request_id: str = Field(min_length=2, max_length=500)
    environment_package_ref: str = Field(min_length=2, max_length=500)
    environment_package_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_platform: PlatformDescriptor
    requested_runtime_refs: list[str] = Field(default_factory=list)
    execution_host_ref: str | None = Field(default=None, max_length=500)
    workspace_ref: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EnvironmentCompatibilityReport(BaseModel):
    compatibility_report_id: str = Field(min_length=2, max_length=500)
    environment_package_ref: str = Field(min_length=2, max_length=500)
    source_platform_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_platform_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: EnvironmentCompatibilityStatus
    compatible_runtime_refs: list[str] = Field(default_factory=list)
    incompatible_runtime_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EnvironmentReproductionVerification(BaseModel):
    verification_id: str = Field(min_length=2, max_length=500)
    environment_package_ref: str = Field(min_length=2, max_length=500)
    package_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: EnvironmentVerificationStatus = EnvironmentVerificationStatus.not_run
    reproduced_environment_ref: str | None = Field(default=None, max_length=1000)
    runtime_version_matches: dict[str, bool] = Field(default_factory=dict)
    system_package_matches: dict[str, bool] = Field(default_factory=dict)
    language_package_matches: dict[str, bool] = Field(default_factory=dict)
    asset_hash_matches: dict[str, bool] = Field(default_factory=dict)
    environment_variable_declarations_match: bool | None = None
    smoke_test_refs: list[str] = Field(default_factory=list)
    verification_job_ref: str | None = Field(default=None, max_length=500)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_passed(self):
        if self.status == EnvironmentVerificationStatus.passed:
            checks = (
                list(self.runtime_version_matches.values())
                + list(self.system_package_matches.values())
                + list(self.language_package_matches.values())
                + list(self.asset_hash_matches.values())
            )
            if checks and not all(checks):
                raise ValueError("passed environment verification cannot contain failed checks")
            if self.environment_variable_declarations_match is False:
                raise ValueError("passed verification requires matching variable declarations")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReproducibleEnvironmentPackageBundle(BaseModel):
    bundle_id: str = Field(min_length=2, max_length=500)
    packages: list[ReproducibleEnvironmentPackage] = Field(default_factory=list)
    reproduction_requests: list[EnvironmentReproductionRequest] = Field(default_factory=list)
    compatibility_reports: list[EnvironmentCompatibilityReport] = Field(default_factory=list)
    verifications: list[EnvironmentReproductionVerification] = Field(default_factory=list)
    source_object_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        if not self.packages:
            raise ValueError("environment package bundle requires packages")

        ids = [item.environment_package_id for item in self.packages]
        if len(ids) != len(set(ids)):
            raise ValueError("environment package ids must be unique")

        package_map = {item.environment_package_id: item for item in self.packages}

        for request in self.reproduction_requests:
            package = package_map.get(request.environment_package_ref)
            if package is None:
                raise ValueError("reproduction request references unknown package")
            if request.environment_package_fingerprint_sha256 != package.fingerprint():
                raise ValueError("reproduction request package fingerprint mismatch")

        for report in self.compatibility_reports:
            if report.environment_package_ref not in package_map:
                raise ValueError("compatibility report references unknown package")

        for verification in self.verifications:
            package = package_map.get(verification.environment_package_ref)
            if package is None:
                raise ValueError("verification references unknown package")
            if verification.package_fingerprint_sha256 != package.fingerprint():
                raise ValueError("verification package fingerprint mismatch")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "bundle_id": self.bundle_id,
            "package_fingerprints": sorted(item.fingerprint() for item in self.packages),
            "request_fingerprints": sorted(item.fingerprint() for item in self.reproduction_requests),
            "compatibility_fingerprints": sorted(item.fingerprint() for item in self.compatibility_reports),
            "verification_fingerprints": sorted(item.fingerprint() for item in self.verifications),
            "source_object_refs": sorted(self.source_object_refs),
            "metadata": self.metadata,
        })


def evaluate_platform_compatibility(
    package: ReproducibleEnvironmentPackage,
    target_platform: PlatformDescriptor,
) -> EnvironmentCompatibilityReport:
    warnings: list[str] = []
    incompatible_runtimes: list[str] = []
    compatible_runtimes: list[str] = []

    same_os = package.platform.operating_system.lower() == target_platform.operating_system.lower()
    same_arch = package.platform.architecture == target_platform.architecture

    if not same_os:
        warnings.append(
            f"operating system differs: source={package.platform.operating_system}, "
            f"target={target_platform.operating_system}"
        )
    if not same_arch:
        warnings.append(
            f"architecture differs: source={package.platform.architecture.value}, "
            f"target={target_platform.architecture.value}"
        )

    for runtime in package.runtimes:
        if same_os and same_arch:
            compatible_runtimes.append(runtime.runtime_ref)
        else:
            incompatible_runtimes.append(runtime.runtime_ref)

    if same_os and same_arch:
        status = (
            EnvironmentCompatibilityStatus.compatible_with_warnings
            if warnings
            else EnvironmentCompatibilityStatus.compatible
        )
    else:
        status = EnvironmentCompatibilityStatus.incompatible

    return EnvironmentCompatibilityReport(
        compatibility_report_id=(
            f"environment-compatibility:{package.environment_package_id}:"
            f"{target_platform.operating_system}:{target_platform.architecture.value}"
        ),
        environment_package_ref=package.environment_package_id,
        source_platform_fingerprint_sha256=package.platform.fingerprint(),
        target_platform_fingerprint_sha256=target_platform.fingerprint(),
        status=status,
        compatible_runtime_refs=sorted(compatible_runtimes),
        incompatible_runtime_refs=sorted(incompatible_runtimes),
        warnings=warnings,
        metadata={
            "core_claims_reproduction_success": False,
            "compatibility_is_preflight_only": True,
        },
    )


def to_scientific_environment_artifact(
    package: ReproducibleEnvironmentPackage,
) -> dict[str, Any]:
    return {
        "artifact_id": f"scientific-artifact:{package.environment_package_id}",
        "artifact_kind": "package",
        "uri": f"core-ref://{package.environment_package_id}",
        "content_sha256": package.fingerprint(),
        "media_type": "application/vnd.sustainable-catalyst.environment-package+json",
        "source_contract": CONTRACT_VERSION,
        "source_object_ref": package.environment_package_id,
        "metadata": {
            "package_version": package.package_version,
            "runtime_refs": sorted(item.runtime_ref for item in package.runtimes),
            "platform_fingerprint_sha256": package.platform.fingerprint(),
            "state": package.state.value,
        },
    }


def reference_environment_package_bundle() -> ReproducibleEnvironmentPackageBundle:
    platform = PlatformDescriptor(
        operating_system="Ubuntu",
        operating_system_version="24.04",
        architecture=PlatformArchitecture.amd64,
        libc="glibc",
        kernel_family="linux",
    )

    r_lock = EnvironmentAsset(
        asset_id="environment-asset:r-lockfile",
        kind=EnvironmentAssetKind.lockfile,
        uri="core-ref://environment-locks/r-runtime-renv.lock",
        content_sha256="a" * 64,
        media_type="application/json",
        size_bytes=2048,
    )
    julia_manifest = EnvironmentAsset(
        asset_id="environment-asset:julia-manifest",
        kind=EnvironmentAssetKind.lockfile,
        uri="core-ref://environment-locks/julia-Manifest.toml",
        content_sha256="b" * 64,
        media_type="text/plain",
        size_bytes=4096,
    )
    build_manifest = EnvironmentAsset(
        asset_id="environment-asset:build-manifest",
        kind=EnvironmentAssetKind.manifest,
        uri="core-ref://environment-manifests/reference-cross-runtime.json",
        content_sha256="c" * 64,
        media_type="application/json",
        size_bytes=1024,
    )

    package = ReproducibleEnvironmentPackage(
        environment_package_id="environment-package:reference-r-julia:v1",
        name="Reference R + Julia Cross-Runtime Environment",
        package_version="1.0.0",
        platform=platform,
        runtimes=[
            RuntimeEnvironmentRequirement(
                runtime_requirement_id="runtime-requirement:r",
                runtime_ref=REFERENCE_R_RUNTIME,
                runtime_version=REFERENCE_R_VERSION,
                runtime_adapter_ref="adapter:sc-runtime-r",
            ),
            RuntimeEnvironmentRequirement(
                runtime_requirement_id="runtime-requirement:julia",
                runtime_ref=REFERENCE_JULIA_RUNTIME,
                runtime_version=REFERENCE_JULIA_VERSION,
                runtime_adapter_ref="adapter:catalyst-julia-runtime",
            ),
        ],
        system_packages=[
            SystemPackageRequirement(
                requirement_id="system-package:r-base-core",
                manager=PackageManager.apt,
                name="r-base-core",
                version="system-pinned-by-snapshot",
            ),
            SystemPackageRequirement(
                requirement_id="system-package:ca-certificates",
                manager=PackageManager.apt,
                name="ca-certificates",
                version="system-pinned-by-snapshot",
            ),
        ],
        language_packages=[
            LanguagePackageRequirement(
                requirement_id="language-package:r:base-stats",
                runtime_ref=REFERENCE_R_RUNTIME,
                manager=PackageManager.renv,
                name="stats",
                version="runtime-bundled",
                scope=RequirementScope.runtime,
            ),
            LanguagePackageRequirement(
                requirement_id="language-package:julia:json3",
                runtime_ref=REFERENCE_JULIA_RUNTIME,
                manager=PackageManager.julia_pkg,
                name="JSON3",
                version="locked-by-manifest",
                scope=RequirementScope.runtime,
            ),
        ],
        environment_variables=[
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:lang",
                name="LANG",
                kind=EnvironmentVariableKind.locale,
                value="C.UTF-8",
            ),
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:tz",
                name="TZ",
                kind=EnvironmentVariableKind.timezone,
                value="UTC",
            ),
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:research-api-key",
                name="SC_RESEARCH_API_KEY",
                kind=EnvironmentVariableKind.secret_reference,
                secret_ref="secret-ref:sc-research-api-key",
                metadata={"secret_value_in_package": False},
            ),
        ],
        assets=[r_lock, julia_manifest, build_manifest],
        build_instructions=[
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:system-packages",
                ordinal=1,
                action="install-system-packages",
                manager=PackageManager.apt,
                requirement_refs=[
                    "system-package:r-base-core",
                    "system-package:ca-certificates",
                ],
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:r-packages",
                ordinal=2,
                action="restore-r-lockfile",
                manager=PackageManager.renv,
                artifact_ref=r_lock.asset_id,
                requirement_refs=["language-package:r:base-stats"],
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:julia-packages",
                ordinal=3,
                action="restore-julia-manifest",
                manager=PackageManager.julia_pkg,
                artifact_ref=julia_manifest.asset_id,
                requirement_refs=["language-package:julia:json3"],
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:verify",
                ordinal=4,
                action="run-environment-smoke-tests",
                artifact_ref=build_manifest.asset_id,
            ),
        ],
        source_environment_ref="environment:reference-cross-runtime",
        source_job_refs=[
            "job:reference-r-regression",
            "job:reference-julia-matrix",
        ],
        source_workflow_refs=[
            "cross-runtime-workflow:reference-r-julia:v1",
        ],
        state=EnvironmentPackageState.verified,
        provenance={
            "core_built_environment": False,
            "execution_host_builds_environment": True,
            "source_release": "v3.41.0",
        },
        metadata={
            "secret_values_embedded": False,
            "portable_manifest": True,
            "reproduction_requires_external_secret_resolution": True,
        },
    )

    request = EnvironmentReproductionRequest(
        reproduction_request_id="environment-reproduction-request:reference-r-julia:001",
        environment_package_ref=package.environment_package_id,
        environment_package_fingerprint_sha256=package.fingerprint(),
        target_platform=platform,
        requested_runtime_refs=[REFERENCE_R_RUNTIME, REFERENCE_JULIA_RUNTIME],
        execution_host_ref="workspace-execution-host:reference",
        workspace_ref="workspace:reference-cross-runtime",
    )

    compatibility = evaluate_platform_compatibility(package, platform)

    verification = EnvironmentReproductionVerification(
        verification_id="environment-verification:reference-r-julia:001",
        environment_package_ref=package.environment_package_id,
        package_fingerprint_sha256=package.fingerprint(),
        status=EnvironmentVerificationStatus.passed,
        reproduced_environment_ref="environment:reproduced-reference-r-julia:001",
        runtime_version_matches={
            REFERENCE_R_RUNTIME: True,
            REFERENCE_JULIA_RUNTIME: True,
        },
        system_package_matches={
            "system-package:r-base-core": True,
            "system-package:ca-certificates": True,
        },
        language_package_matches={
            "language-package:r:base-stats": True,
            "language-package:julia:json3": True,
        },
        asset_hash_matches={
            r_lock.asset_id: True,
            julia_manifest.asset_id: True,
            build_manifest.asset_id: True,
        },
        environment_variable_declarations_match=True,
        smoke_test_refs=[
            "smoke-test:r-runtime-health",
            "smoke-test:julia-runtime-health",
            "smoke-test:cross-runtime-json-roundtrip",
        ],
        verification_job_ref="job:reference-environment-reproduction-verification",
        notes=[
            "Reference verification is a contract proof, not evidence of a live reproduction during local packaging.",
            "Secret values are resolved externally and are never embedded in the environment package.",
        ],
    )

    return ReproducibleEnvironmentPackageBundle(
        bundle_id="environment-package-bundle:reference-r-julia:v1",
        packages=[package],
        reproduction_requests=[request],
        compatibility_reports=[compatibility],
        verifications=[verification],
        source_object_refs=[
            "cross-runtime-workflow-package:reference-r-julia:v1",
            "runtime-data-interchange-bundle:reference-r-julia:v1",
            "scientific-registry-package:reference-regression:v1",
        ],
        metadata={
            "reproducibility_scope": "runtime-plus-dependencies-plus-build-assets",
        },
    )


def contract_document() -> dict[str, Any]:
    reference = reference_environment_package_bundle()
    package = reference.packages[0]
    compatibility = reference.compatibility_reports[0]
    verification = reference.verifications[0]

    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            EXECUTION_ENVIRONMENT_CONTRACT,
            RUNTIME_OBJECT_CONTRACT,
            RUNTIME_ADAPTER_CONTRACT,
            COMPUTATIONAL_JOB_CONTRACT,
            RUNTIME_INTERCHANGE_CONTRACT,
            CROSS_RUNTIME_WORKFLOW_CONTRACT,
            SCIENTIFIC_REGISTRY_CONTRACT,
        ],
        "object_types": [
            "PlatformDescriptor",
            "RuntimeEnvironmentRequirement",
            "SystemPackageRequirement",
            "LanguagePackageRequirement",
            "EnvironmentVariableDeclaration",
            "EnvironmentAsset",
            "EnvironmentBuildInstruction",
            "ReproducibleEnvironmentPackage",
            "EnvironmentReproductionRequest",
            "EnvironmentCompatibilityReport",
            "EnvironmentReproductionVerification",
            "ReproducibleEnvironmentPackageBundle",
        ],
        "capabilities": {
            "platform_fingerprints": True,
            "exact_runtime_requirements": True,
            "system_package_requirements": True,
            "language_package_requirements": True,
            "lockfile_and_manifest_assets": True,
            "secret_reference_only_variables": True,
            "ordered_build_instructions": True,
            "reproduction_requests": True,
            "compatibility_preflight": True,
            "reproduction_verification": True,
            "workflow_environment_packaging": True,
            "scientific_registry_bridge": True,
            "portable_environment_packages": True,
        },
        "integration": {
            "execution_environment_provenance": True,
            "cross_runtime_workflows": True,
            "runtime_data_interchange": True,
            "scientific_result_registry": True,
            "workspace_or_execution_host_builds_environment": True,
            "core_builds_environment": False,
        },
        "boundaries": {
            "core_installs_packages": False,
            "core_executes_environment_builds": False,
            "core_resolves_secret_values": False,
            "secret_values_embedded_in_packages": False,
            "compatibility_report_is_reproduction_proof": False,
            "core_certifies_reproduction_without_verification": False,
            "core_certifies_scientific_validity": False,
            "core_owns_environment_identity_recipe_lineage_and_verification_objects": True,
        },
        "reference": {
            "bundle_id": reference.bundle_id,
            "environment_package_id": package.environment_package_id,
            "runtime_refs": [item.runtime_ref for item in package.runtimes],
            "compatibility_status": compatibility.status.value,
            "verification_status": verification.status.value,
            "package_fingerprint_sha256": package.fingerprint(),
            "bundle_fingerprint_sha256": reference.fingerprint(),
        },
    }
