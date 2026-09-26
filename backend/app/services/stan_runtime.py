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
    LanguagePackageRequirement,
    PackageManager,
    PlatformArchitecture,
    PlatformDescriptor,
    ReproducibleEnvironmentPackage,
    RequirementScope,
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

CORE_RELEASE = "3.46.0"
CONTRACT_VERSION = "sc.core.stan-runtime.v1"
PROVIDER_VERSION = "1.0.0"
CMDSTAN_VERSION = "2.36.0"
RUNTIME_ID = "sc-runtime-stan"
ADAPTER_ID = "adapter:sc-runtime-stan"
SERVICE_NAME = "sc-stan-runtime"
SERVICE_ENDPOINT = "http://127.0.0.1:18095"

RUNTIME_ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"
RUNTIME_OBJECT_CONTRACT = "sc.core.computational-runtime-object.v1"
ENVIRONMENT_PACKAGE_CONTRACT = "sc.core.reproducible-environment-package.v1"
RUNTIME_SECURITY_CONTRACT = "sc.core.runtime-security-governance.v1"
UNIFIED_RUNTIME_CONTRACT = "sc.core.unified-runtime-api.v1"
SCIENTIFIC_REGISTRY_CONTRACT = "sc.core.scientific-result-artifact-registry.v1"

STAN_OPERATIONS = [
    "compile_model",
    "sample",
    "optimize",
    "variational",
    "diagnose",
]


class StanOperation(str, Enum):
    compile_model = "compile_model"
    sample = "sample"
    optimize = "optimize"
    variational = "variational"
    diagnose = "diagnose"


class StanExecutionState(str, Enum):
    declared = "declared"
    prepared = "prepared"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class StanModelSpec(BaseModel):
    model_id: str = Field(min_length=2, max_length=500)
    name: str = Field(min_length=1, max_length=300)
    source: str = Field(min_length=8, max_length=200_000)
    source_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_model(self):
        lowered = self.source.lower()
        if "#include" in lowered:
            raise ValueError("Stan #include directives are not allowed by the v1 runtime contract")
        expected = canonical_sha256({"source": self.source})
        if self.source_sha256 is not None and self.source_sha256 != expected:
            raise ValueError("Stan model source_sha256 mismatch")
        self.source_sha256 = expected
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "model_id": self.model_id,
            "name": self.name,
            "source_sha256": self.source_sha256,
            "metadata": self.metadata,
        })


class StanDataBinding(BaseModel):
    data_binding_id: str = Field(min_length=2, max_length=500)
    data: dict[str, Any] = Field(default_factory=dict)
    schema_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class StanInferenceSettings(BaseModel):
    seed: int = Field(default=12345, ge=1, le=2_147_483_647)
    chains: int = Field(default=1, ge=1, le=1)
    num_warmup: int = Field(default=500, ge=0, le=10_000)
    num_samples: int = Field(default=1000, ge=1, le=50_000)
    thin: int = Field(default=1, ge=1, le=100)
    refresh: int = Field(default=0, ge=0, le=10_000)
    max_execution_seconds: int = Field(default=300, ge=1, le=3600)
    extra_options: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_options(self):
        allowed = {
            "adapt_delta",
            "max_treedepth",
            "stepsize",
            "iter",
            "output_samples",
            "algorithm",
        }
        unknown = set(self.extra_options) - allowed
        if unknown:
            raise ValueError("unsupported Stan option(s): " + ", ".join(sorted(unknown)))
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class StanExecutionRequest(BaseModel):
    stan_request_id: str = Field(min_length=2, max_length=500)
    operation: StanOperation
    model: StanModelSpec
    data_binding: StanDataBinding | None = None
    settings: StanInferenceSettings = Field(default_factory=StanInferenceSettings)
    computational_job_ref: str = Field(min_length=2, max_length=500)
    environment_package_ref: str = Field(
        default="environment-package:stan-runtime:v1",
        min_length=2,
        max_length=1000,
    )
    security_policy_ref: str = Field(
        default="runtime-security-policy:stan-runtime-standard:v1",
        min_length=2,
        max_length=1000,
    )
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self):
        if self.operation != StanOperation.compile_model and self.data_binding is None:
            raise ValueError("Stan execution operation requires data_binding")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class StanExecutionResultContract(BaseModel):
    result_contract_id: str = Field(min_length=2, max_length=500)
    stan_request_ref: str = Field(min_length=2, max_length=500)
    operation: StanOperation
    expected_artifact_kinds: list[str] = Field(default_factory=list)
    expected_result_kinds: list[str] = Field(default_factory=list)
    state: StanExecutionState = StanExecutionState.declared
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_contract(self):
        if not self.expected_artifact_kinds and not self.expected_result_kinds:
            raise ValueError("Stan result contract requires artifact or result kinds")
        if len(self.expected_artifact_kinds) != len(set(self.expected_artifact_kinds)):
            raise ValueError("Stan expected artifact kinds must be unique")
        if len(self.expected_result_kinds) != len(set(self.expected_result_kinds)):
            raise ValueError("Stan expected result kinds must be unique")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        return canonical_sha256(payload)


class StanRuntimeRegistration(BaseModel):
    registration_id: str = Field(min_length=2, max_length=500)
    runtime_id: str = RUNTIME_ID
    provider_version: str = PROVIDER_VERSION
    cmdstan_version: str = CMDSTAN_VERSION
    adapter_id: str = ADAPTER_ID
    service_name: str = SERVICE_NAME
    endpoint: str = SERVICE_ENDPOINT
    operations: list[str] = Field(default_factory=lambda: list(STAN_OPERATIONS))
    adapter_contract: str = RUNTIME_ADAPTER_CONTRACT
    runtime_contract: str = CONTRACT_VERSION
    runtime_kind: str = "domain"
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_registration(self):
        if self.runtime_id != RUNTIME_ID:
            raise ValueError(f"runtime_id must be {RUNTIME_ID}")
        if self.adapter_id != ADAPTER_ID:
            raise ValueError(f"adapter_id must be {ADAPTER_ID}")
        if self.provider_version != PROVIDER_VERSION:
            raise ValueError(f"provider_version must be {PROVIDER_VERSION}")
        if len(self.operations) != len(set(self.operations)):
            raise ValueError("Stan operations must be unique")
        if set(self.operations) != set(STAN_OPERATIONS):
            raise ValueError("Stan operation set does not match v1 contract")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class StanRuntimeBundle(BaseModel):
    bundle_id: str = Field(min_length=2, max_length=500)
    registration: StanRuntimeRegistration
    environment_package: ReproducibleEnvironmentPackage
    security_policy: RuntimeSecurityPolicy
    reference_request: StanExecutionRequest
    result_contract: StanExecutionResultContract
    source_object_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.reference_request.environment_package_ref != self.environment_package.environment_package_id:
            raise ValueError("Stan request/environment package mismatch")
        if self.reference_request.security_policy_ref != self.security_policy.security_policy_id:
            raise ValueError("Stan request/security policy mismatch")
        if self.result_contract.stan_request_ref != self.reference_request.stan_request_id:
            raise ValueError("Stan result contract/request mismatch")
        if self.result_contract.operation != self.reference_request.operation:
            raise ValueError("Stan result contract operation mismatch")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "bundle_id": self.bundle_id,
            "registration_fingerprint_sha256": self.registration.fingerprint(),
            "environment_fingerprint_sha256": self.environment_package.fingerprint(),
            "security_policy_fingerprint_sha256": self.security_policy.fingerprint(),
            "request_fingerprint_sha256": self.reference_request.fingerprint(),
            "result_contract_fingerprint_sha256": self.result_contract.fingerprint(),
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

    cmdstan_manifest = EnvironmentAsset(
        asset_id="environment-asset:stan-cmdstan-manifest",
        kind=EnvironmentAssetKind.manifest,
        uri="core-ref://runtime-manifests/stan-cmdstan-2.36.0.json",
        content_sha256="d" * 64,
        media_type="application/json",
        size_bytes=512,
    )

    provider_requirements = EnvironmentAsset(
        asset_id="environment-asset:stan-provider-requirements",
        kind=EnvironmentAssetKind.lockfile,
        uri="core-ref://runtime-locks/stan-provider-requirements.txt",
        content_sha256="e" * 64,
        media_type="text/plain",
        size_bytes=256,
    )

    return ReproducibleEnvironmentPackage(
        environment_package_id="environment-package:stan-runtime:v1",
        name="Sustainable Catalyst Stan Runtime Environment",
        package_version="1.0.0",
        platform=platform,
        runtimes=[
            RuntimeEnvironmentRequirement(
                runtime_requirement_id="runtime-requirement:stan-provider",
                runtime_ref=RUNTIME_ID,
                runtime_version=PROVIDER_VERSION,
                runtime_adapter_ref=ADAPTER_ID,
            )
        ],
        system_packages=[
            SystemPackageRequirement(
                requirement_id="system-package:build-essential",
                manager=PackageManager.apt,
                name="build-essential",
                version="ubuntu-24.04-repository",
                source=RequirementSource.operating_system,
            ),
            SystemPackageRequirement(
                requirement_id="system-package:git",
                manager=PackageManager.apt,
                name="git",
                version="ubuntu-24.04-repository",
                source=RequirementSource.operating_system,
            ),
        ],
        language_packages=[
            LanguagePackageRequirement(
                requirement_id="language-package:cmdstanpy",
                runtime_ref=RUNTIME_ID,
                manager=PackageManager.pip,
                name="cmdstanpy",
                version="1.2.x",
                scope=RequirementScope.runtime,
                source=RequirementSource.registry,
            )
        ],
        environment_variables=[
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:cmdstan-home",
                name="SC_STAN_CMDSTAN_HOME",
                kind=EnvironmentVariableKind.path,
                value="/opt/sustainable-catalyst/stan-runtime/.cmdstan/cmdstan-2.36.0",
            ),
            EnvironmentVariableDeclaration(
                variable_id="environment-variable:stan-artifact-root",
                name="SC_STAN_ARTIFACT_ROOT",
                kind=EnvironmentVariableKind.path,
                value="/var/lib/sc-stan-runtime/artifacts",
            ),
        ],
        assets=[cmdstan_manifest, provider_requirements],
        build_instructions=[
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:stan-system-packages",
                ordinal=1,
                action="install-system-packages",
                manager=PackageManager.apt,
                requirement_refs=[
                    "system-package:build-essential",
                    "system-package:git",
                ],
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:stan-provider-python",
                ordinal=2,
                action="install-provider-python-dependencies",
                manager=PackageManager.pip,
                artifact_ref=provider_requirements.asset_id,
                requirement_refs=["language-package:cmdstanpy"],
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:cmdstan",
                ordinal=3,
                action="install-pinned-cmdstan",
                artifact_ref=cmdstan_manifest.asset_id,
                arguments={"cmdstan_version": CMDSTAN_VERSION},
            ),
            EnvironmentBuildInstruction(
                instruction_id="build-instruction:stan-smoke-test",
                ordinal=4,
                action="compile-and-run-bounded-stan-smoke-test",
            ),
        ],
        source_environment_ref="runtime-environment:stan-provider:v1",
        source_job_refs=[],
        source_workflow_refs=[],
        state=EnvironmentPackageState.verified,
        provenance={
            "source_release": CORE_RELEASE,
            "core_builds_environment": False,
            "execution_host_builds_environment": True,
        },
        metadata={
            "cmdstan_version": CMDSTAN_VERSION,
            "provider_version": PROVIDER_VERSION,
            "arbitrary_shell": False,
            "runtime_package_install_via_api": False,
        },
    )


def reference_security_policy() -> RuntimeSecurityPolicy:
    isolation = RuntimeIsolationProfile(
        isolation_profile_id="isolation-profile:stan-runtime-standard:v1",
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
        resource_budget_ref="resource-budget:stan-runtime-standard:v1",
        syscall_policy_ref="syscall-policy:stan-runtime-standard:v1",
    )
    return RuntimeSecurityPolicy(
        security_policy_id="runtime-security-policy:stan-runtime-standard:v1",
        policy_version="1.0.0",
        name="Stan Runtime Standard Policy",
        isolation_profile=isolation,
        allowed_runtime_refs=[RUNTIME_ID],
        allowed_adapter_refs=[ADAPTER_ID],
        allowed_operations={RUNTIME_ID: list(STAN_OPERATIONS)},
        allowed_filesystem_prefixes=[
            "/workspace",
            "/tmp/sc-stan-runtime",
            "/var/lib/sc-stan-runtime/artifacts",
        ],
        allowed_artifact_egress_classes=[
            "research-artifact",
            "posterior-samples",
            "stan-diagnostics",
        ],
        execution_policy_ref="execution-policy:stan-runtime-standard:v1",
        provenance={
            "source_release": CORE_RELEASE,
            "policy_owner": "platform-governance",
        },
        metadata={
            "stan_source_is_governed_domain_model": True,
            "stan_include_directives_allowed": False,
            "external_cpp_extensions_allowed": False,
        },
    )


def reference_runtime_bundle() -> StanRuntimeBundle:
    model = StanModelSpec(
        model_id="stan-model:reference-normal:v1",
        name="Reference Normal Model",
        source="""data {
  int<lower=1> N;
  array[N] real y;
}
parameters {
  real mu;
  real<lower=0> sigma;
}
model {
  mu ~ normal(0, 5);
  sigma ~ exponential(1);
  y ~ normal(mu, sigma);
}
""",
        metadata={"reference_model": True},
    )
    data = StanDataBinding(
        data_binding_id="stan-data:reference-normal:v1",
        data={
            "N": 5,
            "y": [1.1, 1.9, 2.2, 1.7, 2.0],
        },
    )
    request = StanExecutionRequest(
        stan_request_id="stan-request:reference-normal-sample:001",
        operation=StanOperation.sample,
        model=model,
        data_binding=data,
        settings=StanInferenceSettings(
            seed=12345,
            chains=1,
            num_warmup=100,
            num_samples=200,
            thin=1,
            refresh=0,
            max_execution_seconds=300,
            extra_options={"adapt_delta": 0.9},
        ),
        computational_job_ref="job:stan-reference-normal-sample:001",
        provenance={
            "originating_product": "research-lab",
            "execution_owner": "workspace-or-execution-host",
        },
    )
    result_contract = StanExecutionResultContract(
        result_contract_id="stan-result-contract:reference-normal-sample:001",
        stan_request_ref=request.stan_request_id,
        operation=request.operation,
        expected_artifact_kinds=[
            "stan-sample-csv",
            "stan-run-log",
        ],
        expected_result_kinds=[
            "posterior-sample-summary",
            "stan-diagnostics",
        ],
        state=StanExecutionState.declared,
        metadata={
            "scientific_validity_certified": False,
            "convergence_must_be_evaluated_by_research_method_layer": True,
        },
    )

    return StanRuntimeBundle(
        bundle_id="stan-runtime-bundle:reference:v1",
        registration=StanRuntimeRegistration(
            registration_id="stan-runtime-registration:v1",
            metadata={
                "cmdstan_distribution": "pinned",
                "arbitrary_stan_include": False,
                "shell_execution": False,
                "runtime_package_installation": False,
            },
        ),
        environment_package=reference_environment_package(),
        security_policy=reference_security_policy(),
        reference_request=request,
        result_contract=result_contract,
        source_object_refs=[
            "runtime-fabric-production-certificate:reference:v1",
            "unified-runtime-catalog:platform-core:v1",
        ],
        metadata={
            "reference_is_contract_proof": True,
            "live_provider_execution_occurs_outside_core": True,
        },
    )


def to_scientific_stan_artifact(bundle: StanRuntimeBundle) -> dict[str, Any]:
    return {
        "artifact_id": f"scientific-artifact:{bundle.bundle_id}",
        "artifact_kind": "package",
        "uri": f"core-ref://{bundle.bundle_id}",
        "content_sha256": bundle.fingerprint(),
        "media_type": "application/vnd.sustainable-catalyst.stan-runtime+json",
        "source_contract": CONTRACT_VERSION,
        "source_object_ref": bundle.bundle_id,
        "metadata": {
            "runtime_id": bundle.registration.runtime_id,
            "provider_version": bundle.registration.provider_version,
            "cmdstan_version": bundle.registration.cmdstan_version,
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
        "cmdstan_version": CMDSTAN_VERSION,
        "runtime_id": RUNTIME_ID,
        "adapter_id": ADAPTER_ID,
        "depends_on": [
            RUNTIME_ADAPTER_CONTRACT,
            RUNTIME_OBJECT_CONTRACT,
            ENVIRONMENT_PACKAGE_CONTRACT,
            RUNTIME_SECURITY_CONTRACT,
            UNIFIED_RUNTIME_CONTRACT,
            SCIENTIFIC_REGISTRY_CONTRACT,
        ],
        "operations": list(STAN_OPERATIONS),
        "capabilities": {
            "stan_model_compilation": True,
            "posterior_sampling": True,
            "optimization": True,
            "variational_inference": True,
            "stan_diagnostics": True,
            "pinned_cmdstan_environment": True,
            "reproducible_environment_package": True,
            "runtime_security_policy": True,
            "runtime_adapter_registration": True,
            "unified_runtime_catalog_integration": True,
            "workspace_product_profile_integration": True,
            "research_lab_product_profile_integration": True,
            "scientific_registry_bridge": True,
        },
        "boundaries": {
            "core_executes_stan": False,
            "provider_executes_stan": True,
            "arbitrary_shell_execution": False,
            "runtime_package_install_via_api": False,
            "stan_include_directives": False,
            "external_cpp_extensions": False,
            "multi_chain_parallel_execution_v1": False,
            "core_selects_model_or_method": False,
            "core_certifies_convergence": False,
            "core_certifies_scientific_validity": False,
        },
        "reference": {
            "bundle_id": bundle.bundle_id,
            "environment_package_id": bundle.environment_package.environment_package_id,
            "security_policy_id": bundle.security_policy.security_policy_id,
            "reference_request_id": bundle.reference_request.stan_request_id,
            "reference_operation": bundle.reference_request.operation.value,
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
    }
