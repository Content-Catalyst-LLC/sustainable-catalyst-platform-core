from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.44.0"
CONTRACT_VERSION = "sc.core.unified-runtime-api.v1"

RUNTIME_SECURITY_CONTRACT = "sc.core.runtime-security-governance.v1"
VERIFICATION_REPRODUCTION_CONTRACT = "sc.core.verification-reproduction-engine.v1"
ENVIRONMENT_PACKAGE_CONTRACT = "sc.core.reproducible-environment-package.v1"
CROSS_RUNTIME_WORKFLOW_CONTRACT = "sc.core.cross-runtime-research-workflow.v1"
RUNTIME_INTERCHANGE_CONTRACT = "sc.core.runtime-data-interchange.v1"
SCIENTIFIC_REGISTRY_CONTRACT = "sc.core.scientific-result-artifact-registry.v1"
COMPUTATIONAL_JOB_CONTRACT = "sc.core.computational-job.v1"
RUNTIME_ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"
RUNTIME_OBJECT_CONTRACT = "sc.core.computational-runtime-object.v1"

REFERENCE_R_RUNTIME = "sc-runtime-r"
REFERENCE_R_VERSION = "1.0.0"
REFERENCE_R_ADAPTER = "adapter:sc-runtime-r"
REFERENCE_JULIA_RUNTIME = "catalyst-julia-runtime"
REFERENCE_JULIA_VERSION = "0.3.0"
REFERENCE_JULIA_ADAPTER = "adapter:catalyst-julia-runtime"
REFERENCE_STAN_RUNTIME = "sc-runtime-stan"
REFERENCE_STAN_VERSION = "1.0.0"
REFERENCE_STAN_ADAPTER = "adapter:sc-runtime-stan"
REFERENCE_OCTAVE_RUNTIME = "sc-runtime-octave"
REFERENCE_OCTAVE_VERSION = "1.0.0"
REFERENCE_OCTAVE_ADAPTER = "adapter:sc-runtime-octave"
REFERENCE_GRETL_RUNTIME = "sc-runtime-gretl"
REFERENCE_GRETL_VERSION = "1.0.0"
REFERENCE_GRETL_ADAPTER = "adapter:sc-runtime-gretl"
REFERENCE_HASKELL_RUNTIME = "sc-runtime-haskell"
REFERENCE_HASKELL_VERSION = "1.0.0"
REFERENCE_HASKELL_ADAPTER = "adapter:sc-runtime-haskell"
REFERENCE_FORTRAN_RUNTIME = "sc-runtime-fortran"
REFERENCE_FORTRAN_VERSION = "1.0.0"
REFERENCE_FORTRAN_ADAPTER = "adapter:sc-runtime-fortran"
REFERENCE_CPP_RUNTIME = "sc-runtime-cpp"
REFERENCE_CPP_VERSION = "1.0.0"
REFERENCE_CPP_ADAPTER = "adapter:sc-runtime-cpp"
REFERENCE_RUST_RUNTIME = "sc-runtime-rust"
REFERENCE_RUST_VERSION = "1.0.0"
REFERENCE_RUST_ADAPTER = "adapter:sc-runtime-rust"


class ProductId(str, Enum):
    workspace = "workspace"
    research_lab = "research-lab"
    workbench = "workbench"
    knowledge_library = "knowledge-library"
    research_librarian = "research-librarian"
    decision_studio = "decision-studio"
    site_intelligence = "site-intelligence"
    catalyst_data = "catalyst-data"


class ProductIntegrationState(str, Enum):
    declared = "declared"
    contract_ready = "contract-ready"
    active = "active"
    suspended = "suspended"


class RuntimeAction(str, Enum):
    execute = "execute"
    statistical_analysis = "statistical-analysis"
    workflow = "workflow"
    interchange = "interchange"
    reproduce = "reproduce"
    verify = "verify"
    inspect = "inspect"


class RuntimeCapability(str, Enum):
    numerical_compute = "numerical-compute"
    matrix_compute = "matrix-compute"
    descriptive_statistics = "descriptive-statistics"
    regression = "regression"
    hypothesis_test = "hypothesis-test"
    statistical_analysis = "statistical-analysis"
    cross_runtime_interchange = "cross-runtime-interchange"
    workflow_execution = "workflow-execution"
    reproduction = "reproduction"
    verification = "verification"
    probabilistic_modeling = "probabilistic-modeling"
    bayesian_inference = "bayesian-inference"
    posterior_sampling = "posterior-sampling"
    linear_algebra = "linear-algebra"
    signal_processing = "signal-processing"
    econometrics = "econometrics"
    exact_arithmetic = "exact-arithmetic"
    discrete_mathematics = "discrete-mathematics"
    functional_computation = "functional-computation"
    graph_reasoning = "graph-reasoning"
    scientific_hpc = "scientific-hpc"
    numerical_integration = "numerical-integration"
    finite_difference = "finite-difference"
    differential_equations = "differential-equations"
    native_engineering = "native-engineering"
    safe_native_systems = "safe-native-systems"
    graph_processing = "graph-processing"
    text_algorithms = "text-algorithms"
    deterministic_hashing = "deterministic-hashing"


class RuntimeAvailability(str, Enum):
    active = "active"
    degraded = "degraded"
    unavailable = "unavailable"


class ResolutionMode(str, Enum):
    candidate_discovery = "candidate-discovery"
    explicit_binding_validated = "explicit-binding-validated"
    unresolved = "unresolved"


class ReceiptStatus(str, Enum):
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class UnifiedRuntimeCatalogEntry(BaseModel):
    catalog_entry_id: str = Field(min_length=2, max_length=500)
    runtime_ref: str = Field(min_length=2, max_length=500)
    runtime_version: str = Field(min_length=1, max_length=200)
    runtime_adapter_ref: str = Field(min_length=2, max_length=500)
    language: str = Field(min_length=1, max_length=200)
    capabilities: list[RuntimeCapability] = Field(default_factory=list)
    operations: list[str] = Field(default_factory=list)
    readable_formats: list[str] = Field(default_factory=list)
    writable_formats: list[str] = Field(default_factory=list)
    environment_package_ref: str | None = Field(default=None, max_length=1000)
    security_policy_ref: str | None = Field(default=None, max_length=1000)
    isolation_profile_ref: str | None = Field(default=None, max_length=1000)
    availability: RuntimeAvailability = RuntimeAvailability.active
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_entry(self):
        if len(self.capabilities) != len(set(self.capabilities)):
            raise ValueError("runtime capabilities must be unique")
        if len(self.operations) != len(set(self.operations)):
            raise ValueError("runtime operations must be unique")
        if len(self.readable_formats) != len(set(self.readable_formats)):
            raise ValueError("readable formats must be unique")
        if len(self.writable_formats) != len(set(self.writable_formats)):
            raise ValueError("writable formats must be unique")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("availability", None)
        return canonical_sha256(payload)


class UnifiedRuntimeCatalog(BaseModel):
    catalog_id: str = Field(min_length=2, max_length=500)
    entries: list[UnifiedRuntimeCatalogEntry] = Field(default_factory=list)
    generated_from_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_catalog(self):
        if not self.entries:
            raise ValueError("unified runtime catalog requires entries")
        entry_ids = [item.catalog_entry_id for item in self.entries]
        runtime_refs = [item.runtime_ref for item in self.entries]
        adapter_refs = [item.runtime_adapter_ref for item in self.entries]
        if len(entry_ids) != len(set(entry_ids)):
            raise ValueError("catalog entry ids must be unique")
        if len(runtime_refs) != len(set(runtime_refs)):
            raise ValueError("runtime refs must be unique in catalog")
        if len(adapter_refs) != len(set(adapter_refs)):
            raise ValueError("runtime adapter refs must be unique in catalog")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "catalog_id": self.catalog_id,
            "entry_fingerprints": sorted(item.fingerprint() for item in self.entries),
            "generated_from_refs": sorted(self.generated_from_refs),
            "metadata": self.metadata,
        })


class ProductRuntimeIntegrationProfile(BaseModel):
    product_profile_id: str = Field(min_length=2, max_length=500)
    product_id: ProductId
    integration_version: str = Field(min_length=1, max_length=200)
    state: ProductIntegrationState = ProductIntegrationState.contract_ready
    allowed_actions: list[RuntimeAction] = Field(default_factory=list)
    allowed_runtime_refs: list[str] = Field(default_factory=list)
    allowed_operations: dict[str, list[str]] = Field(default_factory=dict)
    required_capabilities: list[RuntimeCapability] = Field(default_factory=list)
    default_execution_host_ref: str | None = Field(default=None, max_length=500)
    api_scopes: list[str] = Field(default_factory=list)
    source_product_contract_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_profile(self):
        if not self.allowed_actions:
            raise ValueError("product runtime integration profile requires actions")
        if len(self.allowed_actions) != len(set(self.allowed_actions)):
            raise ValueError("product allowed actions must be unique")
        if len(self.allowed_runtime_refs) != len(set(self.allowed_runtime_refs)):
            raise ValueError("product allowed runtime refs must be unique")
        if len(self.required_capabilities) != len(set(self.required_capabilities)):
            raise ValueError("product required capabilities must be unique")
        if len(self.api_scopes) != len(set(self.api_scopes)):
            raise ValueError("product API scopes must be unique")
        for runtime_ref, operations in self.allowed_operations.items():
            if runtime_ref not in self.allowed_runtime_refs:
                raise ValueError("product allowed operations reference unknown allowed runtime")
            if len(operations) != len(set(operations)):
                raise ValueError("product allowed operations must be unique per runtime")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        return canonical_sha256(payload)


class UnifiedRuntimeInput(BaseModel):
    input_id: str = Field(min_length=2, max_length=500)
    logical_data_ref: str = Field(min_length=2, max_length=1000)
    artifact_ref: str | None = Field(default=None, max_length=1000)
    result_ref: str | None = Field(default=None, max_length=1000)
    schema_ref: str | None = Field(default=None, max_length=1000)
    required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_source(self):
        if not self.artifact_ref and not self.result_ref:
            raise ValueError("runtime input requires artifact_ref or result_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedRuntimeOutputContract(BaseModel):
    output_id: str = Field(min_length=2, max_length=500)
    logical_data_ref: str = Field(min_length=2, max_length=1000)
    expected_artifact_kind: str | None = Field(default=None, max_length=300)
    expected_result_kind: str | None = Field(default=None, max_length=300)
    schema_ref: str | None = Field(default=None, max_length=1000)
    required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_output_kind(self):
        if not self.expected_artifact_kind and not self.expected_result_kind:
            raise ValueError("runtime output contract requires artifact or result kind")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedRuntimeRequest(BaseModel):
    runtime_request_id: str = Field(min_length=2, max_length=500)
    product_id: ProductId
    action: RuntimeAction
    capability: RuntimeCapability
    operation: str | None = Field(default=None, max_length=500)
    explicit_runtime_ref: str | None = Field(default=None, max_length=500)
    computational_job_ref: str | None = Field(default=None, max_length=500)
    environment_package_ref: str | None = Field(default=None, max_length=1000)
    security_request_ref: str | None = Field(default=None, max_length=1000)
    workflow_ref: str | None = Field(default=None, max_length=1000)
    reproduction_plan_ref: str | None = Field(default=None, max_length=1000)
    inputs: list[UnifiedRuntimeInput] = Field(default_factory=list)
    outputs: list[UnifiedRuntimeOutputContract] = Field(default_factory=list)
    requested_formats: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self):
        input_ids = [item.input_id for item in self.inputs]
        output_ids = [item.output_id for item in self.outputs]
        if len(input_ids) != len(set(input_ids)):
            raise ValueError("runtime input ids must be unique")
        if len(output_ids) != len(set(output_ids)):
            raise ValueError("runtime output ids must be unique")
        if self.action in {RuntimeAction.execute, RuntimeAction.statistical_analysis} and not self.operation:
            raise ValueError("execution/statistical-analysis request requires operation")
        if self.action == RuntimeAction.workflow and not self.workflow_ref:
            raise ValueError("workflow request requires workflow_ref")
        if self.action in {RuntimeAction.reproduce, RuntimeAction.verify} and not self.reproduction_plan_ref:
            raise ValueError("reproduce/verify request requires reproduction_plan_ref")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class RuntimeResolutionCandidate(BaseModel):
    runtime_ref: str
    runtime_version: str
    runtime_adapter_ref: str
    catalog_entry_ref: str
    matched_capability: RuntimeCapability
    operation_supported: bool
    product_allowed: bool
    availability: RuntimeAvailability

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedRuntimeResolution(BaseModel):
    resolution_id: str = Field(min_length=2, max_length=500)
    runtime_request_ref: str = Field(min_length=2, max_length=500)
    runtime_request_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    product_profile_ref: str = Field(min_length=2, max_length=500)
    product_profile_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    catalog_ref: str = Field(min_length=2, max_length=500)
    catalog_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    mode: ResolutionMode
    candidates: list[RuntimeResolutionCandidate] = Field(default_factory=list)
    bound_runtime_ref: str | None = Field(default=None, max_length=500)
    rejection_reasons: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_resolution(self):
        refs = [item.runtime_ref for item in self.candidates]
        if len(refs) != len(set(refs)):
            raise ValueError("runtime resolution candidates must be unique")
        if self.mode == ResolutionMode.explicit_binding_validated:
            if not self.bound_runtime_ref:
                raise ValueError("validated explicit binding requires bound_runtime_ref")
            if self.bound_runtime_ref not in refs:
                raise ValueError("bound runtime must be present in candidates")
        if self.mode == ResolutionMode.candidate_discovery and self.bound_runtime_ref is not None:
            raise ValueError("candidate discovery cannot bind a runtime")
        if self.mode == ResolutionMode.unresolved and self.candidates:
            raise ValueError("unresolved resolution cannot contain candidates")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedRuntimeInvocation(BaseModel):
    invocation_id: str = Field(min_length=2, max_length=500)
    runtime_request_ref: str = Field(min_length=2, max_length=500)
    runtime_request_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    resolution_ref: str = Field(min_length=2, max_length=500)
    resolution_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    product_profile_ref: str = Field(min_length=2, max_length=500)
    product_profile_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    catalog_entry_ref: str = Field(min_length=2, max_length=500)
    catalog_entry_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    runtime_ref: str = Field(min_length=2, max_length=500)
    runtime_version: str = Field(min_length=1, max_length=200)
    runtime_adapter_ref: str = Field(min_length=2, max_length=500)
    computational_job_ref: str = Field(min_length=2, max_length=500)
    execution_host_ref: str = Field(min_length=2, max_length=500)
    environment_package_ref: str = Field(min_length=2, max_length=1000)
    security_policy_ref: str = Field(min_length=2, max_length=1000)
    security_decision_ref: str = Field(min_length=2, max_length=1000)
    input_refs: list[str] = Field(default_factory=list)
    output_contract_refs: list[str] = Field(default_factory=list)
    workflow_ref: str | None = Field(default=None, max_length=1000)
    reproduction_plan_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_invocation(self):
        if len(self.input_refs) != len(set(self.input_refs)):
            raise ValueError("invocation input refs must be unique")
        if len(self.output_contract_refs) != len(set(self.output_contract_refs)):
            raise ValueError("invocation output contract refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ProductRuntimeReceipt(BaseModel):
    receipt_id: str = Field(min_length=2, max_length=500)
    product_id: ProductId
    invocation_ref: str = Field(min_length=2, max_length=500)
    invocation_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: ReceiptStatus
    computational_job_ref: str = Field(min_length=2, max_length=500)
    runtime_ref: str = Field(min_length=2, max_length=500)
    execution_host_ref: str = Field(min_length=2, max_length=500)
    produced_artifact_refs: list[str] = Field(default_factory=list)
    produced_result_refs: list[str] = Field(default_factory=list)
    security_attestation_ref: str | None = Field(default=None, max_length=1000)
    reproduction_report_ref: str | None = Field(default=None, max_length=1000)
    error_ref: str | None = Field(default=None, max_length=1000)
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_receipt(self):
        if self.status == ReceiptStatus.failed and not self.error_ref:
            raise ValueError("failed product runtime receipt requires error_ref")
        if self.status == ReceiptStatus.completed and self.error_ref:
            raise ValueError("completed product runtime receipt cannot contain error_ref")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("completed_at", None)
        return canonical_sha256(payload)


class UnifiedRuntimeAPIBundle(BaseModel):
    bundle_id: str = Field(min_length=2, max_length=500)
    catalog: UnifiedRuntimeCatalog
    product_profiles: list[ProductRuntimeIntegrationProfile]
    request: UnifiedRuntimeRequest
    resolution: UnifiedRuntimeResolution
    invocation: UnifiedRuntimeInvocation | None = None
    receipts: list[ProductRuntimeReceipt] = Field(default_factory=list)
    source_object_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        profile_ids = [item.product_profile_id for item in self.product_profiles]
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError("product profile ids must be unique")
        matching_profiles = [item for item in self.product_profiles if item.product_id == self.request.product_id]
        if len(matching_profiles) != 1:
            raise ValueError("bundle must contain exactly one matching product profile")
        profile = matching_profiles[0]
        if self.resolution.runtime_request_ref != self.request.runtime_request_id:
            raise ValueError("resolution references wrong request")
        if self.resolution.runtime_request_fingerprint_sha256 != self.request.fingerprint():
            raise ValueError("resolution request fingerprint mismatch")
        if self.resolution.product_profile_ref != profile.product_profile_id:
            raise ValueError("resolution references wrong product profile")
        if self.resolution.product_profile_fingerprint_sha256 != profile.fingerprint():
            raise ValueError("resolution product profile fingerprint mismatch")
        if self.resolution.catalog_ref != self.catalog.catalog_id:
            raise ValueError("resolution references wrong catalog")
        if self.resolution.catalog_fingerprint_sha256 != self.catalog.fingerprint():
            raise ValueError("resolution catalog fingerprint mismatch")
        if self.invocation is not None:
            if self.resolution.mode != ResolutionMode.explicit_binding_validated:
                raise ValueError("invocation requires validated explicit runtime binding")
            if self.invocation.runtime_request_ref != self.request.runtime_request_id:
                raise ValueError("invocation references wrong request")
            if self.invocation.runtime_request_fingerprint_sha256 != self.request.fingerprint():
                raise ValueError("invocation request fingerprint mismatch")
            if self.invocation.resolution_ref != self.resolution.resolution_id:
                raise ValueError("invocation references wrong resolution")
            if self.invocation.resolution_fingerprint_sha256 != self.resolution.fingerprint():
                raise ValueError("invocation resolution fingerprint mismatch")
            if self.invocation.product_profile_ref != profile.product_profile_id:
                raise ValueError("invocation references wrong product profile")
            if self.invocation.product_profile_fingerprint_sha256 != profile.fingerprint():
                raise ValueError("invocation product profile fingerprint mismatch")
            if self.invocation.runtime_ref != self.resolution.bound_runtime_ref:
                raise ValueError("invocation runtime must match bound runtime")
            entry_map = {item.catalog_entry_id: item for item in self.catalog.entries}
            entry = entry_map.get(self.invocation.catalog_entry_ref)
            if entry is None:
                raise ValueError("invocation references unknown catalog entry")
            if self.invocation.catalog_entry_fingerprint_sha256 != entry.fingerprint():
                raise ValueError("invocation catalog entry fingerprint mismatch")
            if self.invocation.runtime_adapter_ref != entry.runtime_adapter_ref:
                raise ValueError("invocation adapter does not match catalog entry")
        invocation_map = {}
        if self.invocation is not None:
            invocation_map[self.invocation.invocation_id] = self.invocation
        receipt_ids = [item.receipt_id for item in self.receipts]
        if len(receipt_ids) != len(set(receipt_ids)):
            raise ValueError("receipt ids must be unique")
        for receipt in self.receipts:
            invocation = invocation_map.get(receipt.invocation_ref)
            if invocation is None:
                raise ValueError("receipt references unknown invocation")
            if receipt.invocation_fingerprint_sha256 != invocation.fingerprint():
                raise ValueError("receipt invocation fingerprint mismatch")
            if receipt.runtime_ref != invocation.runtime_ref:
                raise ValueError("receipt runtime mismatch")
            if receipt.execution_host_ref != invocation.execution_host_ref:
                raise ValueError("receipt execution host mismatch")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "bundle_id": self.bundle_id,
            "catalog_fingerprint_sha256": self.catalog.fingerprint(),
            "product_profile_fingerprints": sorted(item.fingerprint() for item in self.product_profiles),
            "request_fingerprint_sha256": self.request.fingerprint(),
            "resolution_fingerprint_sha256": self.resolution.fingerprint(),
            "invocation_fingerprint_sha256": self.invocation.fingerprint() if self.invocation else None,
            "receipt_fingerprints": sorted(item.fingerprint() for item in self.receipts),
            "source_object_refs": sorted(self.source_object_refs),
            "metadata": self.metadata,
        })


def reference_runtime_catalog() -> UnifiedRuntimeCatalog:
    return UnifiedRuntimeCatalog(
        catalog_id="unified-runtime-catalog:platform-core:v1",
        entries=[
            UnifiedRuntimeCatalogEntry(catalog_entry_id="runtime-catalog-entry:sc-runtime-r:1.0.0",runtime_ref=REFERENCE_R_RUNTIME,runtime_version=REFERENCE_R_VERSION,runtime_adapter_ref=REFERENCE_R_ADAPTER,language="R",capabilities=[RuntimeCapability.descriptive_statistics,RuntimeCapability.regression,RuntimeCapability.hypothesis_test,RuntimeCapability.statistical_analysis,RuntimeCapability.cross_runtime_interchange,RuntimeCapability.workflow_execution,RuntimeCapability.reproduction,RuntimeCapability.verification],operations=["descriptive_summary","quantile_summary","correlation_matrix","linear_regression","t_test","one_way_anova"],readable_formats=["json","csv"],writable_formats=["json","csv"],environment_package_ref="environment-package:reference-r-julia:v1",security_policy_ref="runtime-security-policy:research-standard:v1",isolation_profile_ref="isolation-profile:research-runtime-standard:v1",metadata={"provider_contract":"sc.core.r-runtime-migration.v1"}),
            UnifiedRuntimeCatalogEntry(catalog_entry_id="runtime-catalog-entry:catalyst-julia-runtime:0.3.0",runtime_ref=REFERENCE_JULIA_RUNTIME,runtime_version=REFERENCE_JULIA_VERSION,runtime_adapter_ref=REFERENCE_JULIA_ADAPTER,language="Julia",capabilities=[RuntimeCapability.numerical_compute,RuntimeCapability.matrix_compute,RuntimeCapability.cross_runtime_interchange,RuntimeCapability.workflow_execution,RuntimeCapability.reproduction,RuntimeCapability.verification],operations=["identity","sum","mean","matrix_multiply"],readable_formats=["json"],writable_formats=["json"],environment_package_ref="environment-package:reference-r-julia:v1",security_policy_ref="runtime-security-policy:research-standard:v1",isolation_profile_ref="isolation-profile:research-runtime-standard:v1",metadata={"provider_contract":"sc.core.julia-runtime-integration.v1"}),
            UnifiedRuntimeCatalogEntry(catalog_entry_id="runtime-catalog-entry:sc-runtime-stan:1.0.0",runtime_ref=REFERENCE_STAN_RUNTIME,runtime_version=REFERENCE_STAN_VERSION,runtime_adapter_ref=REFERENCE_STAN_ADAPTER,language="Stan",capabilities=[RuntimeCapability.probabilistic_modeling,RuntimeCapability.bayesian_inference,RuntimeCapability.posterior_sampling,RuntimeCapability.workflow_execution,RuntimeCapability.reproduction,RuntimeCapability.verification],operations=["compile_model","sample","optimize","variational","diagnose"],readable_formats=["json","stan"],writable_formats=["json","csv"],environment_package_ref="environment-package:stan-runtime:v1",security_policy_ref="runtime-security-policy:stan-runtime-standard:v1",isolation_profile_ref="isolation-profile:stan-runtime-standard:v1",metadata={"provider_contract":"sc.core.stan-runtime.v1"}),
            UnifiedRuntimeCatalogEntry(catalog_entry_id="runtime-catalog-entry:sc-runtime-octave:1.0.0",runtime_ref=REFERENCE_OCTAVE_RUNTIME,runtime_version=REFERENCE_OCTAVE_VERSION,runtime_adapter_ref=REFERENCE_OCTAVE_ADAPTER,language="Octave",capabilities=[RuntimeCapability.numerical_compute,RuntimeCapability.matrix_compute,RuntimeCapability.linear_algebra,RuntimeCapability.signal_processing,RuntimeCapability.workflow_execution,RuntimeCapability.reproduction,RuntimeCapability.verification],operations=["matrix_multiply","linear_solve","eigenvalues","svd","fft","polynomial_roots"],readable_formats=["json"],writable_formats=["json"],environment_package_ref="environment-package:octave-runtime:v1",security_policy_ref="runtime-security-policy:octave-runtime-standard:v1",isolation_profile_ref="isolation-profile:octave-runtime-standard:v1",metadata={"provider_contract":"sc.core.octave-runtime.v1"}),
            UnifiedRuntimeCatalogEntry(catalog_entry_id="runtime-catalog-entry:sc-runtime-gretl:1.0.0",runtime_ref=REFERENCE_GRETL_RUNTIME,runtime_version=REFERENCE_GRETL_VERSION,runtime_adapter_ref=REFERENCE_GRETL_ADAPTER,language="hansl",capabilities=[RuntimeCapability.statistical_analysis,RuntimeCapability.regression,RuntimeCapability.econometrics,RuntimeCapability.workflow_execution,RuntimeCapability.reproduction,RuntimeCapability.verification],operations=["ols","robust_ols","logit","probit","descriptive_summary","correlation_matrix"],readable_formats=["json","csv"],writable_formats=["json","txt"],environment_package_ref="environment-package:gretl-hansl-runtime:v1",security_policy_ref="runtime-security-policy:gretl-hansl-runtime-standard:v1",isolation_profile_ref="isolation-profile:gretl-hansl-runtime-standard:v1",metadata={"provider_contract":"sc.core.gretl-hansl-runtime.v1"}),
            UnifiedRuntimeCatalogEntry(catalog_entry_id="runtime-catalog-entry:sc-runtime-haskell:1.0.0",runtime_ref=REFERENCE_HASKELL_RUNTIME,runtime_version=REFERENCE_HASKELL_VERSION,runtime_adapter_ref=REFERENCE_HASKELL_ADAPTER,language="Haskell",capabilities=[RuntimeCapability.exact_arithmetic,RuntimeCapability.discrete_mathematics,RuntimeCapability.functional_computation,RuntimeCapability.graph_reasoning,RuntimeCapability.workflow_execution,RuntimeCapability.reproduction,RuntimeCapability.verification],operations=["gcd","lcm","rational_reduce","factorial","fibonacci","binomial_coefficient","integer_power","graph_reachable"],readable_formats=["json"],writable_formats=["json","txt"],environment_package_ref="environment-package:haskell-runtime:v1",security_policy_ref="runtime-security-policy:haskell-runtime-standard:v1",isolation_profile_ref="isolation-profile:haskell-runtime-standard:v1",metadata={"provider_contract":"sc.core.haskell-runtime.v1"}),
            UnifiedRuntimeCatalogEntry(catalog_entry_id="runtime-catalog-entry:sc-runtime-fortran:1.0.0",runtime_ref=REFERENCE_FORTRAN_RUNTIME,runtime_version=REFERENCE_FORTRAN_VERSION,runtime_adapter_ref=REFERENCE_FORTRAN_ADAPTER,language="Fortran",capabilities=[RuntimeCapability.scientific_hpc,RuntimeCapability.numerical_compute,RuntimeCapability.matrix_compute,RuntimeCapability.numerical_integration,RuntimeCapability.finite_difference,RuntimeCapability.differential_equations,RuntimeCapability.workflow_execution,RuntimeCapability.reproduction,RuntimeCapability.verification],operations=["dot_product","matrix_multiply","trapezoidal_integral","central_difference","rk4_linear_step","heat_step_1d"],readable_formats=["json"],writable_formats=["json","txt"],environment_package_ref="environment-package:fortran-runtime:v1",security_policy_ref="runtime-security-policy:fortran-runtime-standard:v1",isolation_profile_ref="isolation-profile:fortran-runtime-standard:v1",metadata={"provider_contract":"sc.core.fortran-runtime.v1","native_runtime":"GNU Fortran","native_runtime_version":"13.3.0","native_package_version":"13.3.0-6ubuntu2~24.04.1"}),
            UnifiedRuntimeCatalogEntry(catalog_entry_id="runtime-catalog-entry:sc-runtime-cpp:1.0.0",runtime_ref=REFERENCE_CPP_RUNTIME,runtime_version=REFERENCE_CPP_VERSION,runtime_adapter_ref=REFERENCE_CPP_ADAPTER,language="C/C++",capabilities=[RuntimeCapability.native_engineering,RuntimeCapability.numerical_compute,RuntimeCapability.matrix_compute,RuntimeCapability.signal_processing,RuntimeCapability.graph_reasoning,RuntimeCapability.workflow_execution,RuntimeCapability.reproduction,RuntimeCapability.verification],operations=["dot_product","matrix_multiply","linear_interpolation","polynomial_evaluate","fir_filter","dijkstra_shortest_path"],readable_formats=["json"],writable_formats=["json","txt"],environment_package_ref="environment-package:c-cpp-runtime:v1",security_policy_ref="runtime-security-policy:c-cpp-runtime-standard:v1",isolation_profile_ref="isolation-profile:c-cpp-runtime-standard:v1",metadata={"provider_contract":"sc.core.c-cpp-runtime.v1","native_runtime":"GCC/G++","native_runtime_version":"13.3.0","native_package_version":"13.3.0-6ubuntu2~24.04.1","language_profiles":["c11","cpp17"]}),
            UnifiedRuntimeCatalogEntry(catalog_entry_id="runtime-catalog-entry:sc-runtime-rust:1.0.0",runtime_ref=REFERENCE_RUST_RUNTIME,runtime_version=REFERENCE_RUST_VERSION,runtime_adapter_ref=REFERENCE_RUST_ADAPTER,language="Rust",capabilities=[RuntimeCapability.safe_native_systems,RuntimeCapability.graph_processing,RuntimeCapability.text_algorithms,RuntimeCapability.deterministic_hashing,RuntimeCapability.numerical_compute,RuntimeCapability.workflow_execution,RuntimeCapability.reproduction,RuntimeCapability.verification],operations=["prefix_sum","moving_average","connected_components","topological_sort","levenshtein_distance","fnv1a_64"],readable_formats=["json"],writable_formats=["json","txt"],environment_package_ref="environment-package:rust-runtime:v1",security_policy_ref="runtime-security-policy:rust-runtime-standard:v1",isolation_profile_ref="isolation-profile:rust-runtime-standard:v1",metadata={"provider_contract":"sc.core.rust-runtime.v1","native_runtime":"rustc","native_runtime_version":"1.75.0","native_package_version":"1.75.0+dfsg0ubuntu1-0ubuntu7.4","edition":"2021","unsafe_code":False}),
        ],
        generated_from_refs=["runtime-adapter-registry:platform-core","runtime-data-interchange-bundle:reference-r-julia:v1","runtime-security-governance-bundle:reference:v1","stan-runtime-bundle:reference:v1","octave-runtime-bundle:reference:v1","gretl-hansl-runtime-bundle:reference:v1","haskell-runtime-bundle:reference:v1","fortran-runtime-bundle:reference:v1","c-cpp-runtime-bundle:reference:v1","rust-runtime-bundle:reference:v1"],
        metadata={"selection_owner":"calling-product-or-workspace","core_autonomously_selects_runtime":False},
    )

def reference_product_profiles() -> list[ProductRuntimeIntegrationProfile]:
    all_r_ops=["descriptive_summary","quantile_summary","correlation_matrix","linear_regression","t_test","one_way_anova"]
    all_julia_ops=["identity","sum","mean","matrix_multiply"]
    all_stan_ops=["compile_model","sample","optimize","variational","diagnose"]
    all_octave_ops=["matrix_multiply","linear_solve","eigenvalues","svd","fft","polynomial_roots"]
    all_gretl_ops=["ols","robust_ols","logit","probit","descriptive_summary","correlation_matrix"]
    all_haskell_ops=["gcd","lcm","rational_reduce","factorial","fibonacci","binomial_coefficient","integer_power","graph_reachable"]
    all_fortran_ops=["dot_product","matrix_multiply","trapezoidal_integral","central_difference","rk4_linear_step","heat_step_1d"]
    all_cpp_ops=["dot_product","matrix_multiply","linear_interpolation","polynomial_evaluate","fir_filter","dijkstra_shortest_path"]
    all_rust_ops=["prefix_sum","moving_average","connected_components","topological_sort","levenshtein_distance","fnv1a_64"]
    return [
        ProductRuntimeIntegrationProfile(product_profile_id="product-runtime-profile:workspace:v1",product_id=ProductId.workspace,integration_version="1.7.0",allowed_actions=[RuntimeAction.execute,RuntimeAction.statistical_analysis,RuntimeAction.workflow,RuntimeAction.interchange,RuntimeAction.reproduce,RuntimeAction.verify,RuntimeAction.inspect],allowed_runtime_refs=[REFERENCE_R_RUNTIME,REFERENCE_JULIA_RUNTIME,REFERENCE_STAN_RUNTIME,REFERENCE_OCTAVE_RUNTIME,REFERENCE_GRETL_RUNTIME,REFERENCE_HASKELL_RUNTIME,REFERENCE_FORTRAN_RUNTIME,REFERENCE_CPP_RUNTIME,REFERENCE_RUST_RUNTIME],allowed_operations={REFERENCE_R_RUNTIME:all_r_ops,REFERENCE_JULIA_RUNTIME:all_julia_ops,REFERENCE_STAN_RUNTIME:all_stan_ops,REFERENCE_OCTAVE_RUNTIME:all_octave_ops,REFERENCE_GRETL_RUNTIME:all_gretl_ops,REFERENCE_HASKELL_RUNTIME:all_haskell_ops,REFERENCE_FORTRAN_RUNTIME:all_fortran_ops,REFERENCE_CPP_RUNTIME:all_cpp_ops,REFERENCE_RUST_RUNTIME:all_rust_ops},required_capabilities=[RuntimeCapability.workflow_execution],default_execution_host_ref="workspace-execution-host:primary",api_scopes=["runtime:catalog","runtime:resolve","runtime:invoke","runtime:receipt","runtime:reproduce"],source_product_contract_refs=["workspace-runtime-orchestration","sc.core.stan-runtime.v1","sc.core.octave-runtime.v1","sc.core.gretl-hansl-runtime.v1","sc.core.haskell-runtime.v1","sc.core.fortran-runtime.v1","sc.core.c-cpp-runtime.v1","sc.core.rust-runtime.v1"],metadata={"role":"primary-runtime-orchestrator","rust_runtime_enabled":True}),
        ProductRuntimeIntegrationProfile(product_profile_id="product-runtime-profile:research-lab:v1",product_id=ProductId.research_lab,integration_version="1.7.0",allowed_actions=[RuntimeAction.execute,RuntimeAction.statistical_analysis,RuntimeAction.interchange,RuntimeAction.verify,RuntimeAction.inspect],allowed_runtime_refs=[REFERENCE_R_RUNTIME,REFERENCE_JULIA_RUNTIME,REFERENCE_STAN_RUNTIME,REFERENCE_OCTAVE_RUNTIME,REFERENCE_GRETL_RUNTIME,REFERENCE_HASKELL_RUNTIME,REFERENCE_FORTRAN_RUNTIME,REFERENCE_CPP_RUNTIME,REFERENCE_RUST_RUNTIME],allowed_operations={REFERENCE_R_RUNTIME:all_r_ops,REFERENCE_JULIA_RUNTIME:all_julia_ops,REFERENCE_STAN_RUNTIME:all_stan_ops,REFERENCE_OCTAVE_RUNTIME:all_octave_ops,REFERENCE_GRETL_RUNTIME:all_gretl_ops,REFERENCE_HASKELL_RUNTIME:all_haskell_ops,REFERENCE_FORTRAN_RUNTIME:all_fortran_ops,REFERENCE_CPP_RUNTIME:all_cpp_ops,REFERENCE_RUST_RUNTIME:all_rust_ops},required_capabilities=[RuntimeCapability.statistical_analysis,RuntimeCapability.numerical_compute,RuntimeCapability.bayesian_inference,RuntimeCapability.linear_algebra,RuntimeCapability.econometrics,RuntimeCapability.exact_arithmetic,RuntimeCapability.scientific_hpc,RuntimeCapability.native_engineering,RuntimeCapability.safe_native_systems],default_execution_host_ref="workspace-execution-host:primary",api_scopes=["runtime:catalog","runtime:resolve","runtime:invoke","runtime:receipt"],source_product_contract_refs=["research-lab-computational-analysis","sc.core.stan-runtime.v1","sc.core.octave-runtime.v1","sc.core.gretl-hansl-runtime.v1","sc.core.haskell-runtime.v1","sc.core.fortran-runtime.v1","sc.core.c-cpp-runtime.v1","sc.core.rust-runtime.v1"],metadata={"role":"scientific-analysis-client","fortran_runtime_enabled":True,"cpp_runtime_enabled":True,"rust_runtime_enabled":True}),
        ProductRuntimeIntegrationProfile(product_profile_id="product-runtime-profile:workbench:v1",product_id=ProductId.workbench,integration_version="1.5.0",allowed_actions=[RuntimeAction.execute,RuntimeAction.interchange,RuntimeAction.inspect],allowed_runtime_refs=[REFERENCE_R_RUNTIME,REFERENCE_JULIA_RUNTIME,REFERENCE_OCTAVE_RUNTIME,REFERENCE_HASKELL_RUNTIME,REFERENCE_FORTRAN_RUNTIME,REFERENCE_CPP_RUNTIME,REFERENCE_RUST_RUNTIME],allowed_operations={REFERENCE_R_RUNTIME:["descriptive_summary","correlation_matrix","linear_regression"],REFERENCE_JULIA_RUNTIME:all_julia_ops,REFERENCE_OCTAVE_RUNTIME:all_octave_ops,REFERENCE_HASKELL_RUNTIME:all_haskell_ops,REFERENCE_FORTRAN_RUNTIME:all_fortran_ops,REFERENCE_CPP_RUNTIME:all_cpp_ops,REFERENCE_RUST_RUNTIME:all_rust_ops},required_capabilities=[RuntimeCapability.numerical_compute,RuntimeCapability.linear_algebra,RuntimeCapability.exact_arithmetic,RuntimeCapability.scientific_hpc,RuntimeCapability.native_engineering,RuntimeCapability.safe_native_systems],default_execution_host_ref="workspace-execution-host:primary",api_scopes=["runtime:catalog","runtime:resolve","runtime:invoke","runtime:receipt"],source_product_contract_refs=["workbench-computational-prototyping","sc.core.octave-runtime.v1","sc.core.haskell-runtime.v1","sc.core.fortran-runtime.v1","sc.core.c-cpp-runtime.v1","sc.core.rust-runtime.v1"],metadata={"role":"engineering-compute-client","fortran_runtime_enabled":True,"cpp_runtime_enabled":True,"rust_runtime_enabled":True}),
    ]

def resolve_runtime_request(*, catalog: UnifiedRuntimeCatalog, profile: ProductRuntimeIntegrationProfile, request: UnifiedRuntimeRequest, resolution_id: str | None = None) -> UnifiedRuntimeResolution:
    reasons: list[str] = []
    if request.product_id != profile.product_id:
        reasons.append("request product does not match product integration profile")
    if request.action not in profile.allowed_actions:
        reasons.append(f"action not allowed for product: {request.action.value}")
    candidates: list[RuntimeResolutionCandidate] = []
    for entry in catalog.entries:
        product_allowed = entry.runtime_ref in profile.allowed_runtime_refs
        capability_supported = request.capability in entry.capabilities
        operation_supported = request.operation is None or request.operation in entry.operations
        profile_operation_allowed = request.operation is None or request.operation in profile.allowed_operations.get(entry.runtime_ref, [])
        format_supported = all(
            fmt in entry.readable_formats or fmt in entry.writable_formats
            for fmt in request.requested_formats
        )
        if product_allowed and capability_supported and operation_supported and profile_operation_allowed and format_supported and entry.availability != RuntimeAvailability.unavailable:
            candidates.append(RuntimeResolutionCandidate(
                runtime_ref=entry.runtime_ref,
                runtime_version=entry.runtime_version,
                runtime_adapter_ref=entry.runtime_adapter_ref,
                catalog_entry_ref=entry.catalog_entry_id,
                matched_capability=request.capability,
                operation_supported=True,
                product_allowed=True,
                availability=entry.availability,
            ))
    if request.explicit_runtime_ref:
        explicit = [item for item in candidates if item.runtime_ref == request.explicit_runtime_ref]
        if explicit and not reasons:
            mode = ResolutionMode.explicit_binding_validated
            candidates = explicit
            bound_runtime_ref = request.explicit_runtime_ref
        else:
            mode = ResolutionMode.unresolved
            candidates = []
            bound_runtime_ref = None
            reasons.append("explicit runtime is not compatible with request/product profile")
    elif candidates and not reasons:
        mode = ResolutionMode.candidate_discovery
        bound_runtime_ref = None
    else:
        mode = ResolutionMode.unresolved
        candidates = []
        bound_runtime_ref = None
        if not reasons:
            reasons.append("no compatible runtime candidates")
    return UnifiedRuntimeResolution(
        resolution_id=resolution_id or f"runtime-resolution:{request.runtime_request_id}",
        runtime_request_ref=request.runtime_request_id,
        runtime_request_fingerprint_sha256=request.fingerprint(),
        product_profile_ref=profile.product_profile_id,
        product_profile_fingerprint_sha256=profile.fingerprint(),
        catalog_ref=catalog.catalog_id,
        catalog_fingerprint_sha256=catalog.fingerprint(),
        mode=mode,
        candidates=candidates,
        bound_runtime_ref=bound_runtime_ref,
        rejection_reasons=reasons,
        metadata={"core_autonomously_selected_runtime": False, "explicit_binding_present": request.explicit_runtime_ref is not None},
    )


def build_invocation(*, request: UnifiedRuntimeRequest, resolution: UnifiedRuntimeResolution, profile: ProductRuntimeIntegrationProfile, catalog: UnifiedRuntimeCatalog, security_decision_ref: str, invocation_id: str | None = None) -> UnifiedRuntimeInvocation:
    if resolution.runtime_request_ref != request.runtime_request_id:
        raise ValueError("runtime resolution references a different request")
    if resolution.runtime_request_fingerprint_sha256 != request.fingerprint():
        raise ValueError("runtime resolution request fingerprint mismatch")
    if resolution.product_profile_ref != profile.product_profile_id:
        raise ValueError("runtime resolution references a different product profile")
    if resolution.product_profile_fingerprint_sha256 != profile.fingerprint():
        raise ValueError("runtime resolution product profile fingerprint mismatch")
    if resolution.catalog_ref != catalog.catalog_id:
        raise ValueError("runtime resolution references a different catalog")
    if resolution.catalog_fingerprint_sha256 != catalog.fingerprint():
        raise ValueError("runtime resolution catalog fingerprint mismatch")
    if resolution.mode != ResolutionMode.explicit_binding_validated:
        raise ValueError("unified runtime invocation requires validated explicit runtime binding")
    if not resolution.bound_runtime_ref:
        raise ValueError("runtime resolution is missing bound runtime")
    if request.explicit_runtime_ref != resolution.bound_runtime_ref:
        raise ValueError("request explicit runtime does not match validated binding")
    entry = next((item for item in catalog.entries if item.runtime_ref == resolution.bound_runtime_ref), None)
    if entry is None:
        raise ValueError("bound runtime missing from catalog")
    if not request.computational_job_ref:
        raise ValueError("runtime invocation requires computational_job_ref")
    if not request.environment_package_ref:
        raise ValueError("runtime invocation requires environment_package_ref")
    if not security_decision_ref:
        raise ValueError("runtime invocation requires security_decision_ref")
    execution_host = profile.default_execution_host_ref
    if not execution_host:
        raise ValueError("product profile does not define execution host")
    return UnifiedRuntimeInvocation(
        invocation_id=invocation_id or f"runtime-invocation:{request.runtime_request_id}",
        runtime_request_ref=request.runtime_request_id,
        runtime_request_fingerprint_sha256=request.fingerprint(),
        resolution_ref=resolution.resolution_id,
        resolution_fingerprint_sha256=resolution.fingerprint(),
        product_profile_ref=profile.product_profile_id,
        product_profile_fingerprint_sha256=profile.fingerprint(),
        catalog_entry_ref=entry.catalog_entry_id,
        catalog_entry_fingerprint_sha256=entry.fingerprint(),
        runtime_ref=entry.runtime_ref,
        runtime_version=entry.runtime_version,
        runtime_adapter_ref=entry.runtime_adapter_ref,
        computational_job_ref=request.computational_job_ref,
        execution_host_ref=execution_host,
        environment_package_ref=request.environment_package_ref,
        security_policy_ref=entry.security_policy_ref or "runtime-security-policy:unspecified",
        security_decision_ref=security_decision_ref,
        input_refs=[item.input_id for item in request.inputs],
        output_contract_refs=[item.output_id for item in request.outputs],
        workflow_ref=request.workflow_ref,
        reproduction_plan_ref=request.reproduction_plan_ref,
        metadata={"dispatch_owner": "workspace-or-execution-host", "core_dispatched_execution": False},
    )


def to_scientific_unified_runtime_artifact(bundle: UnifiedRuntimeAPIBundle) -> dict[str, Any]:
    return {
        "artifact_id": f"scientific-artifact:{bundle.bundle_id}",
        "artifact_kind": "package",
        "uri": f"core-ref://{bundle.bundle_id}",
        "content_sha256": bundle.fingerprint(),
        "media_type": "application/vnd.sustainable-catalyst.unified-runtime-api+json",
        "source_contract": CONTRACT_VERSION,
        "source_object_ref": bundle.bundle_id,
        "metadata": {
            "product_id": bundle.request.product_id.value,
            "resolution_mode": bundle.resolution.mode.value,
            "runtime_ref": bundle.invocation.runtime_ref if bundle.invocation else None,
            "receipt_count": len(bundle.receipts),
        },
    }


def reference_unified_runtime_api_bundle() -> UnifiedRuntimeAPIBundle:
    catalog = reference_runtime_catalog()
    profiles = reference_product_profiles()
    lab_profile = next(item for item in profiles if item.product_id == ProductId.research_lab)
    request = UnifiedRuntimeRequest(
        runtime_request_id="unified-runtime-request:research-lab:r-regression:reference",
        product_id=ProductId.research_lab,
        action=RuntimeAction.statistical_analysis,
        capability=RuntimeCapability.regression,
        operation="linear_regression",
        explicit_runtime_ref=REFERENCE_R_RUNTIME,
        computational_job_ref="job:unified-runtime-reference-r-regression",
        environment_package_ref="environment-package:reference-r-julia:v1",
        security_request_ref="security-request:r-regression:reference",
        inputs=[UnifiedRuntimeInput(
            input_id="runtime-input:reference-regression-data",
            logical_data_ref="logical-data:reference-regression-table:v1",
            artifact_ref="scientific-artifact:reference-regression-input",
        )],
        outputs=[UnifiedRuntimeOutputContract(
            output_id="runtime-output:reference-regression-result",
            logical_data_ref="logical-result:reference-regression:v1",
            expected_result_kind="statistical-result",
        )],
        requested_formats=["json"],
        provenance={"originating_product": "research-lab", "request_contract": CONTRACT_VERSION},
    )
    resolution = resolve_runtime_request(catalog=catalog, profile=lab_profile, request=request, resolution_id="runtime-resolution:reference-r-regression")
    invocation = build_invocation(
        request=request,
        resolution=resolution,
        profile=lab_profile,
        catalog=catalog,
        security_decision_ref="security-decision:r-regression:reference",
        invocation_id="runtime-invocation:reference-r-regression",
    )
    receipt = ProductRuntimeReceipt(
        receipt_id="product-runtime-receipt:research-lab:r-regression:reference",
        product_id=ProductId.research_lab,
        invocation_ref=invocation.invocation_id,
        invocation_fingerprint_sha256=invocation.fingerprint(),
        status=ReceiptStatus.completed,
        computational_job_ref=invocation.computational_job_ref,
        runtime_ref=invocation.runtime_ref,
        execution_host_ref=invocation.execution_host_ref,
        produced_artifact_refs=["scientific-artifact:reference-regression-result"],
        produced_result_refs=["stat-result:reference-regression:001"],
        security_attestation_ref="isolation-attestation:r-regression:reference",
        provenance={"receipt_owner": "research-lab", "execution_owner": "workspace-or-execution-host"},
    )
    return UnifiedRuntimeAPIBundle(
        bundle_id="unified-runtime-api-bundle:research-lab:r-regression:v1",
        catalog=catalog,
        product_profiles=profiles,
        request=request,
        resolution=resolution,
        invocation=invocation,
        receipts=[receipt],
        source_object_refs=[
            "runtime-security-governance-bundle:reference:v1",
            "reproduction-package:reference-r-julia:v1",
            "environment-package:reference-r-julia:v1",
            "cross-runtime-workflow-package:reference-r-julia:v1",
            "runtime-data-interchange-bundle:reference-r-julia:v1",
        ],
        metadata={"reference_is_contract_proof": True, "core_dispatched_execution": False},
    )


def contract_document() -> dict[str, Any]:
    bundle = reference_unified_runtime_api_bundle()
    catalog = bundle.catalog
    profiles = bundle.product_profiles
    discovery_request = UnifiedRuntimeRequest(
        runtime_request_id="unified-runtime-request:contract:matrix-candidates",
        product_id=ProductId.workspace,
        action=RuntimeAction.execute,
        capability=RuntimeCapability.matrix_compute,
        operation="matrix_multiply",
        computational_job_ref="job:contract-matrix",
        environment_package_ref="environment-package:reference-r-julia:v1",
    )
    workspace_profile = next(item for item in profiles if item.product_id == ProductId.workspace)
    discovery = resolve_runtime_request(catalog=catalog, profile=workspace_profile, request=discovery_request)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            RUNTIME_SECURITY_CONTRACT, VERIFICATION_REPRODUCTION_CONTRACT,
            ENVIRONMENT_PACKAGE_CONTRACT, CROSS_RUNTIME_WORKFLOW_CONTRACT,
            RUNTIME_INTERCHANGE_CONTRACT, SCIENTIFIC_REGISTRY_CONTRACT,
            COMPUTATIONAL_JOB_CONTRACT, RUNTIME_ADAPTER_CONTRACT,
            RUNTIME_OBJECT_CONTRACT,
        ],
        "object_types": [
            "UnifiedRuntimeCatalogEntry", "UnifiedRuntimeCatalog",
            "ProductRuntimeIntegrationProfile", "UnifiedRuntimeInput",
            "UnifiedRuntimeOutputContract", "UnifiedRuntimeRequest",
            "RuntimeResolutionCandidate", "UnifiedRuntimeResolution",
            "UnifiedRuntimeInvocation", "ProductRuntimeReceipt",
            "UnifiedRuntimeAPIBundle",
        ],
        "capabilities": {
            "unified_runtime_catalog": True,
            "product_runtime_profiles": True,
            "product_scoped_runtime_resolution": True,
            "candidate_discovery": True,
            "explicit_runtime_binding_validation": True,
            "unified_invocation_envelopes": True,
            "environment_package_binding": True,
            "security_decision_binding": True,
            "computational_job_binding": True,
            "cross_runtime_workflow_binding": True,
            "reproduction_plan_binding": True,
            "product_completion_receipts": True,
            "scientific_registry_bridge": True,
        },
        "product_integration": {
            "workspace": "contract-ready",
            "research-lab": "contract-ready",
            "workbench": "contract-ready",
            "knowledge-library": "not-runtime-client-in-reference",
            "research-librarian": "not-runtime-client-in-reference",
            "decision-studio": "not-runtime-client-in-reference",
            "site-intelligence": "not-runtime-client-in-reference",
            "catalyst-data": "not-runtime-client-in-reference",
        },
        "integration": {
            "r_runtime": True,
            "julia_runtime": True,
            "runtime_security_governance": True,
            "verification_reproduction_engine": True,
            "reproducible_environment_packages": True,
            "cross_runtime_workflows": True,
            "runtime_data_interchange": True,
            "workspace_or_execution_host_dispatches": True,
            "core_dispatches_execution": False,
        },
        "boundaries": {
            "core_autonomously_selects_runtime": False,
            "core_dispatches_runtime_execution": False,
            "core_bypasses_runtime_security": False,
            "core_replaces_product_business_logic": False,
            "core_claims_product_side_integration_without_product_changes": False,
            "core_certifies_scientific_validity": False,
            "core_owns_unified_runtime_api_contract_resolution_and_exchange": True,
        },
        "reference": {
            "catalog_id": catalog.catalog_id,
            "runtime_refs": [item.runtime_ref for item in catalog.entries],
            "product_profile_ids": [item.product_profile_id for item in profiles],
            "reference_bundle_id": bundle.bundle_id,
            "reference_resolution_mode": bundle.resolution.mode.value,
            "reference_bound_runtime_ref": bundle.resolution.bound_runtime_ref,
            "reference_receipt_status": bundle.receipts[0].status.value,
            "matrix_candidate_runtime_refs": [item.runtime_ref for item in discovery.candidates],
            "matrix_candidate_resolution_mode": discovery.mode.value,
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
    }
