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



def _r_runtime_adapter() -> RuntimeAdapterDescriptor:
    capability = RuntimeCapability(
        capability_key="governed-statistical-analysis",
        category="statistics",
        operations=[
            "descriptive_summary",
            "quantile_summary",
            "correlation_matrix",
            "linear_regression",
            "t_test",
            "one_way_anova",
        ],
        input_types=["json", "array", "table", "scalar"],
        output_types=["json", "scalar", "table"],
        deterministic=True,
        arbitrary_code_execution=False,
        shell_execution=False,
        package_installation=False,
        metadata={
            "provider_contract": "sc.core.r-runtime-migration.v1",
            "environment_contract": "sc.environment.v1",
            "legacy_provider_alias": "catalyst-analytics-r",
        },
    )
    runtime = RuntimeDescriptor(
        runtime_id="sc-runtime-r",
        runtime_kind=RuntimeKind.language,
        language="r",
        implementation="R",
        runtime_version="system-managed",
        provider_version="1.0.0",
        service_name="sc-r-runtime",
        contract_versions=[
            OBJECT_CONTRACT_VERSION,
            ADAPTER_CONTRACT_VERSION,
            "sc.core.r-runtime-migration.v1",
            "sc.environment.v1",
        ],
        capabilities=[capability],
        execution_host="contabo-vps",
        status="active",
        metadata={
            "canonical_runtime": True,
            "provider_release": "Sustainable Catalyst R Runtime v1.0.0",
            "legacy_provider_id": "catalyst-analytics-r",
            "legacy_provider_version": "2.0.1",
            "legacy_alias_resolution": True,
            "arbitrary_r_source": False,
            "runtime_package_install": False,
        },
    )
    return RuntimeAdapterDescriptor(
        adapter_id="adapter:sc-runtime-r",
        runtime=runtime,
        provider_contracts=[
            "sc.core.r-runtime-migration.v1",
            "sc.core.analytical-runtime-provider.v1",
            "sc.environment.v1",
        ],
        transport="http",
        invocation_mode="governed-service",
        service_ref="sc-r-runtime",
        status="registered",
        metadata={
            "core_executes_runtime_directly": False,
            "migration_source": "catalyst-analytics-r@2.0.1",
            "endpoint": "http://127.0.0.1:18094",
        },
    )


def _stan_runtime_adapter() -> RuntimeAdapterDescriptor:
    capability = RuntimeCapability(
        capability_key="governed-bayesian-inference",
        category="probabilistic-modeling",
        operations=[
            "compile_model",
            "sample",
            "optimize",
            "variational",
            "diagnose",
        ],
        input_types=["json", "stan-model", "table", "scalar"],
        output_types=["json", "csv", "posterior-samples", "diagnostics"],
        deterministic=False,
        arbitrary_code_execution=False,
        shell_execution=False,
        package_installation=False,
        metadata={
            "provider_contract": "sc.core.stan-runtime.v1",
            "environment_contract": "sc.core.reproducible-environment-package.v1",
            "native_runtime": "CmdStan",
            "native_runtime_version": "2.36.0",
            "seeded_reproducibility": True,
        },
    )
    runtime = RuntimeDescriptor(
        runtime_id="sc-runtime-stan",
        runtime_kind=RuntimeKind.domain,
        language="stan",
        implementation="CmdStan",
        runtime_version="2.36.0",
        provider_version="1.0.0",
        service_name="sc-stan-runtime",
        contract_versions=[
            OBJECT_CONTRACT_VERSION,
            ADAPTER_CONTRACT_VERSION,
            "sc.core.stan-runtime.v1",
            "sc.core.reproducible-environment-package.v1",
            "sc.core.runtime-security-governance.v1",
        ],
        capabilities=[capability],
        execution_host="contabo-vps",
        status="active",
        metadata={
            "canonical_runtime": True,
            "provider_release": "Sustainable Catalyst Stan Runtime v1.0.0",
            "arbitrary_shell": False,
            "runtime_package_install": False,
            "stan_include_directives": False,
            "multi_chain_parallel_v1": False,
        },
    )
    return RuntimeAdapterDescriptor(
        adapter_id="adapter:sc-runtime-stan",
        runtime=runtime,
        provider_contracts=[
            "sc.core.stan-runtime.v1",
            "sc.core.reproducible-environment-package.v1",
            "sc.core.runtime-security-governance.v1",
        ],
        transport="http",
        invocation_mode="governed-service",
        service_ref="sc-stan-runtime",
        status="registered",
        metadata={
            "core_executes_runtime_directly": False,
            "endpoint": "http://127.0.0.1:18095",
            "native_runtime": "CmdStan",
            "native_runtime_version": "2.36.0",
        },
    )


def _octave_runtime_adapter() -> RuntimeAdapterDescriptor:
    capability = RuntimeCapability(
        capability_key="bounded-numerical-computing",
        category="numerical-computing",
        operations=[
            "matrix_multiply",
            "linear_solve",
            "eigenvalues",
            "svd",
            "fft",
            "polynomial_roots",
        ],
        input_types=["json", "matrix", "vector", "scalar"],
        output_types=["json", "matrix", "vector", "complex-vector", "diagnostics"],
        deterministic=True,
        arbitrary_code_execution=False,
        shell_execution=False,
        package_installation=False,
        metadata={
            "provider_contract": "sc.core.octave-runtime.v1",
            "environment_contract": "sc.core.reproducible-environment-package.v1",
            "native_runtime": "GNU Octave",
            "native_runtime_version": "8.4.0",
        },
    )
    runtime = RuntimeDescriptor(
        runtime_id="sc-runtime-octave",
        runtime_kind=RuntimeKind.language,
        language="octave",
        implementation="GNU Octave",
        runtime_version="8.4.0",
        provider_version="1.0.0",
        service_name="sc-octave-runtime",
        contract_versions=[
            OBJECT_CONTRACT_VERSION,
            ADAPTER_CONTRACT_VERSION,
            "sc.core.octave-runtime.v1",
            "sc.core.reproducible-environment-package.v1",
            "sc.core.runtime-security-governance.v1",
        ],
        capabilities=[capability],
        execution_host="contabo-vps",
        status="active",
        metadata={
            "canonical_runtime": True,
            "provider_release": "Sustainable Catalyst Octave Runtime v1.0.0",
            "arbitrary_octave_source": False,
            "shell_execution": False,
            "runtime_package_install": False,
        },
    )
    return RuntimeAdapterDescriptor(
        adapter_id="adapter:sc-runtime-octave",
        runtime=runtime,
        provider_contracts=[
            "sc.core.octave-runtime.v1",
            "sc.core.reproducible-environment-package.v1",
            "sc.core.runtime-security-governance.v1",
        ],
        transport="http",
        invocation_mode="governed-service",
        service_ref="sc-octave-runtime",
        status="registered",
        metadata={
            "core_executes_runtime_directly": False,
            "endpoint": "http://127.0.0.1:18096",
            "native_runtime": "GNU Octave",
            "native_runtime_version": "8.4.0",
        },
    )


def _gretl_runtime_adapter() -> RuntimeAdapterDescriptor:
    capability = RuntimeCapability(
        capability_key="bounded-econometrics",
        category="econometrics",
        operations=[
            "ols",
            "robust_ols",
            "logit",
            "probit",
            "descriptive_summary",
            "correlation_matrix",
        ],
        input_types=["json", "table", "series", "scalar"],
        output_types=["json", "econometric-result", "transcript", "diagnostics"],
        deterministic=False,
        arbitrary_code_execution=False,
        shell_execution=False,
        package_installation=False,
        metadata={
            "provider_contract": "sc.core.gretl-hansl-runtime.v1",
            "environment_contract": "sc.core.reproducible-environment-package.v1",
            "native_runtime": "gretl",
            "native_runtime_version": "2023c",
            "native_package_version": "2023c-2.1build3",
            "language": "hansl",
        },
    )
    runtime = RuntimeDescriptor(
        runtime_id="sc-runtime-gretl",
        runtime_kind=RuntimeKind.domain,
        language="hansl",
        implementation="gretl",
        runtime_version="2023c",
        provider_version="1.0.0",
        service_name="sc-gretl-runtime",
        contract_versions=[
            OBJECT_CONTRACT_VERSION,
            ADAPTER_CONTRACT_VERSION,
            "sc.core.gretl-hansl-runtime.v1",
            "sc.core.reproducible-environment-package.v1",
            "sc.core.runtime-security-governance.v1",
        ],
        capabilities=[capability],
        execution_host="contabo-vps",
        status="active",
        metadata={
            "canonical_runtime": True,
            "provider_release": "Sustainable Catalyst gretl/hansl Runtime v1.0.0",
            "arbitrary_hansl_source": False,
            "shell_execution": False,
            "runtime_package_install": False,
        },
    )
    return RuntimeAdapterDescriptor(
        adapter_id="adapter:sc-runtime-gretl",
        runtime=runtime,
        provider_contracts=[
            "sc.core.gretl-hansl-runtime.v1",
            "sc.core.reproducible-environment-package.v1",
            "sc.core.runtime-security-governance.v1",
        ],
        transport="http",
        invocation_mode="governed-service",
        service_ref="sc-gretl-runtime",
        status="registered",
        metadata={
            "core_executes_runtime_directly": False,
            "endpoint": "http://127.0.0.1:18097",
            "native_runtime": "gretl",
            "native_runtime_version": "2023c",
            "language": "hansl",
        },
    )


def _haskell_runtime_adapter() -> RuntimeAdapterDescriptor:
    capability = RuntimeCapability(
        capability_key="bounded-typed-functional-compute",
        category="functional-computing",
        operations=[
            "gcd", "lcm", "rational_reduce", "factorial", "fibonacci",
            "binomial_coefficient", "integer_power", "graph_reachable",
        ],
        input_types=["json", "integer", "integer-pair", "graph-edge-list"],
        output_types=["json", "exact-integer", "exact-rational", "boolean", "diagnostics"],
        deterministic=True,
        arbitrary_code_execution=False,
        shell_execution=False,
        package_installation=False,
        metadata={
            "provider_contract": "sc.core.haskell-runtime.v1",
            "environment_contract": "sc.core.reproducible-environment-package.v1",
            "native_runtime": "GHC",
            "native_runtime_version": "9.4.7",
            "native_package_version": "9.4.7-3",
            "language": "haskell",
        },
    )
    runtime = RuntimeDescriptor(
        runtime_id="sc-runtime-haskell",
        runtime_kind=RuntimeKind.language,
        language="haskell",
        implementation="GHC",
        runtime_version="9.4.7",
        provider_version="1.0.0",
        service_name="sc-haskell-runtime",
        contract_versions=[
            OBJECT_CONTRACT_VERSION, ADAPTER_CONTRACT_VERSION,
            "sc.core.haskell-runtime.v1",
            "sc.core.reproducible-environment-package.v1",
            "sc.core.runtime-security-governance.v1",
        ],
        capabilities=[capability],
        execution_host="contabo-vps",
        status="active",
        metadata={
            "canonical_runtime": True,
            "provider_release": "Sustainable Catalyst Haskell Runtime v1.0.0",
            "arbitrary_haskell_source": False,
            "shell_execution": False,
            "runtime_package_install": False,
        },
    )
    return RuntimeAdapterDescriptor(
        adapter_id="adapter:sc-runtime-haskell",
        runtime=runtime,
        provider_contracts=[
            "sc.core.haskell-runtime.v1",
            "sc.core.reproducible-environment-package.v1",
            "sc.core.runtime-security-governance.v1",
        ],
        transport="http",
        invocation_mode="governed-service",
        service_ref="sc-haskell-runtime",
        status="registered",
        metadata={
            "core_executes_runtime_directly": False,
            "endpoint": "http://127.0.0.1:18098",
            "native_runtime": "GHC",
            "native_runtime_version": "9.4.7",
            "language": "haskell",
        },
    )


def _fortran_runtime_adapter() -> RuntimeAdapterDescriptor:
    capability = RuntimeCapability(
        capability_key="bounded-scientific-hpc",
        category="scientific-hpc",
        operations=["dot_product","matrix_multiply","trapezoidal_integral","central_difference","rk4_linear_step","heat_step_1d"],
        input_types=["json","vector","matrix","scalar"],
        output_types=["json","scalar","vector","matrix","diagnostics"],
        deterministic=True,
        arbitrary_code_execution=False,
        shell_execution=False,
        package_installation=False,
        metadata={"provider_contract":"sc.core.fortran-runtime.v1","environment_contract":"sc.core.reproducible-environment-package.v1","native_runtime":"GNU Fortran","native_runtime_version":"13.3.0","native_package_version":"13.3.0-6ubuntu2~24.04.1","language":"fortran"},
    )
    runtime = RuntimeDescriptor(
        runtime_id="sc-runtime-fortran", runtime_kind=RuntimeKind.language, language="fortran", implementation="GNU Fortran", runtime_version="13.3.0", provider_version="1.0.0", service_name="sc-fortran-runtime",
        contract_versions=[OBJECT_CONTRACT_VERSION,ADAPTER_CONTRACT_VERSION,"sc.core.fortran-runtime.v1","sc.core.reproducible-environment-package.v1","sc.core.runtime-security-governance.v1"],
        capabilities=[capability], execution_host="contabo-vps", status="active",
        metadata={"canonical_runtime":True,"provider_release":"Sustainable Catalyst Fortran Runtime v1.0.0","arbitrary_fortran_source":False,"shell_execution":False,"runtime_package_install":False,"provider_managed_compilation":True},
    )
    return RuntimeAdapterDescriptor(
        adapter_id="adapter:sc-runtime-fortran", runtime=runtime,
        provider_contracts=["sc.core.fortran-runtime.v1","sc.core.reproducible-environment-package.v1","sc.core.runtime-security-governance.v1"],
        transport="http", invocation_mode="governed-service", service_ref="sc-fortran-runtime", status="registered",
        metadata={"core_executes_runtime_directly":False,"endpoint":"http://127.0.0.1:18099","native_runtime":"GNU Fortran","native_runtime_version":"13.3.0","language":"fortran"},
    )

def _cpp_runtime_adapter() -> RuntimeAdapterDescriptor:
    capability = RuntimeCapability(
        capability_key="bounded-native-engineering",
        category="native-engineering",
        operations=["dot_product","matrix_multiply","linear_interpolation","polynomial_evaluate","fir_filter","dijkstra_shortest_path"],
        input_types=["json","vector","matrix","scalar","graph"],
        output_types=["json","scalar","vector","matrix","diagnostics"],
        deterministic=True,
        arbitrary_code_execution=False,
        shell_execution=False,
        package_installation=False,
        metadata={"provider_contract":"sc.core.c-cpp-runtime.v1","environment_contract":"sc.core.reproducible-environment-package.v1","native_runtime":"GCC/G++","native_runtime_version":"13.3.0","native_package_version":"13.3.0-6ubuntu2~24.04.1","language_profiles":["c11","cpp17"]},
    )
    runtime = RuntimeDescriptor(
        runtime_id="sc-runtime-cpp", runtime_kind=RuntimeKind.language, language="c-cpp", implementation="GCC/G++", runtime_version="13.3.0", provider_version="1.0.0", service_name="sc-cpp-runtime",
        contract_versions=[OBJECT_CONTRACT_VERSION,ADAPTER_CONTRACT_VERSION,"sc.core.c-cpp-runtime.v1","sc.core.reproducible-environment-package.v1","sc.core.runtime-security-governance.v1"],
        capabilities=[capability], execution_host="contabo-vps", status="active",
        metadata={"canonical_runtime":True,"provider_release":"Sustainable Catalyst C/C++ Runtime v1.0.0","arbitrary_c_cpp_source":False,"shell_execution":False,"runtime_package_install":False,"provider_managed_compilation":True},
    )
    return RuntimeAdapterDescriptor(
        adapter_id="adapter:sc-runtime-cpp", runtime=runtime,
        provider_contracts=["sc.core.c-cpp-runtime.v1","sc.core.reproducible-environment-package.v1","sc.core.runtime-security-governance.v1"],
        transport="http", invocation_mode="governed-service", service_ref="sc-cpp-runtime", status="registered",
        metadata={"core_executes_runtime_directly":False,"endpoint":"http://127.0.0.1:18100","native_runtime":"GCC/G++","native_runtime_version":"13.3.0","language":"c-cpp","language_profiles":["c11","cpp17"]},
    )

def _rust_runtime_adapter() -> RuntimeAdapterDescriptor:
    capability = RuntimeCapability(
        capability_key="bounded-safe-native-systems",
        category="safe-native-systems",
        operations=["prefix_sum","moving_average","connected_components","topological_sort","levenshtein_distance","fnv1a_64"],
        input_types=["json","integer-vector","numeric-vector","graph","text"],
        output_types=["json","integer-vector","numeric-vector","integer-scalar","hex64","diagnostics"],
        deterministic=True,
        arbitrary_code_execution=False,
        shell_execution=False,
        package_installation=False,
        metadata={"provider_contract":"sc.core.rust-runtime.v1","environment_contract":"sc.core.reproducible-environment-package.v1","native_runtime":"rustc","native_runtime_version":"1.75.0","native_package_version":"1.75.0+dfsg0ubuntu1-0ubuntu7.4","edition":"2021","unsafe_code":False},
    )
    runtime = RuntimeDescriptor(
        runtime_id="sc-runtime-rust", runtime_kind=RuntimeKind.language, language="rust", implementation="rustc", runtime_version="1.75.0", provider_version="1.0.0", service_name="sc-rust-runtime",
        contract_versions=[OBJECT_CONTRACT_VERSION,ADAPTER_CONTRACT_VERSION,"sc.core.rust-runtime.v1","sc.core.reproducible-environment-package.v1","sc.core.runtime-security-governance.v1"],
        capabilities=[capability], execution_host="contabo-vps", status="active",
        metadata={"canonical_runtime":True,"provider_release":"Sustainable Catalyst Rust Runtime v1.0.0","arbitrary_rust_source":False,"unsafe_code":False,"shell_execution":False,"runtime_package_install":False,"provider_managed_compilation":True},
    )
    return RuntimeAdapterDescriptor(
        adapter_id="adapter:sc-runtime-rust", runtime=runtime,
        provider_contracts=["sc.core.rust-runtime.v1","sc.core.reproducible-environment-package.v1","sc.core.runtime-security-governance.v1"],
        transport="http", invocation_mode="governed-service", service_ref="sc-rust-runtime", status="registered",
        metadata={"core_executes_runtime_directly":False,"endpoint":"http://127.0.0.1:18101","native_runtime":"rustc","native_runtime_version":"1.75.0","language":"rust","edition":"2021","unsafe_code":False},
    )

def _go_runtime_adapter() -> RuntimeAdapterDescriptor:
    capability = RuntimeCapability(capability_key="bounded-concurrent-distributed",category="concurrent-distributed",operations=["parallel_sum","parallel_map_affine","concurrent_histogram","parallel_matrix_row_sums","parallel_graph_degrees","batch_sha256"],input_types=["json","numeric-vector","matrix","graph","text-batch"],output_types=["json","scalar","numeric-vector","integer-vector","hash-batch","diagnostics"],deterministic=True,arbitrary_code_execution=False,shell_execution=False,package_installation=False,metadata={"provider_contract":"sc.core.go-runtime.v1","environment_contract":"sc.core.reproducible-environment-package.v1","native_runtime":"Go","native_runtime_version":"1.22.2","native_package_version":"1.22.2-2ubuntu0.4","external_module_downloads":False,"cgo":False})
    runtime = RuntimeDescriptor(runtime_id="sc-runtime-go",runtime_kind=RuntimeKind.language,language="go",implementation="Go",runtime_version="1.22.2",provider_version="1.0.0",service_name="sc-go-runtime",contract_versions=[OBJECT_CONTRACT_VERSION,ADAPTER_CONTRACT_VERSION,"sc.core.go-runtime.v1","sc.core.reproducible-environment-package.v1","sc.core.runtime-security-governance.v1"],capabilities=[capability],execution_host="contabo-vps",status="active",metadata={"canonical_runtime":True,"provider_release":"Sustainable Catalyst Go Runtime v1.0.0","arbitrary_go_source":False,"external_module_downloads":False,"shell_execution":False,"runtime_package_install":False,"provider_managed_compilation":True})
    return RuntimeAdapterDescriptor(adapter_id="adapter:sc-runtime-go",runtime=runtime,provider_contracts=["sc.core.go-runtime.v1","sc.core.reproducible-environment-package.v1","sc.core.runtime-security-governance.v1"],transport="http",invocation_mode="governed-service",service_ref="sc-go-runtime",status="registered",metadata={"core_executes_runtime_directly":False,"endpoint":"http://127.0.0.1:18102","native_runtime":"Go","native_runtime_version":"1.22.2","language":"go"})

def _python_runtime_adapter() -> RuntimeAdapterDescriptor:
    capability = RuntimeCapability(capability_key="bounded-general-scientific-python",category="general-scientific",operations=["descriptive_summary","linear_regression","matrix_multiply","standardize","bootstrap_mean_ci","token_frequency"],input_types=["json","numeric-vector","matrix","text"],output_types=["json","scalar","numeric-vector","matrix","table","diagnostics"],deterministic=True,arbitrary_code_execution=False,shell_execution=False,package_installation=False,metadata={"provider_contract":"sc.core.python-runtime.v1","environment_contract":"sc.core.reproducible-environment-package.v1","native_runtime":"CPython","native_runtime_version":"3.12.3","isolated_mode":True,"site_imports_disabled_for_jobs":True,"job_network_access":False})
    runtime = RuntimeDescriptor(runtime_id="sc-runtime-python",runtime_kind=RuntimeKind.language,language="python",implementation="CPython",runtime_version="3.12.3",provider_version="1.0.0",service_name="sc-python-runtime",contract_versions=[OBJECT_CONTRACT_VERSION,ADAPTER_CONTRACT_VERSION,"sc.core.python-runtime.v1","sc.core.reproducible-environment-package.v1","sc.core.runtime-security-governance.v1"],capabilities=[capability],execution_host="contabo-vps",status="active",metadata={"canonical_runtime":True,"provider_release":"Sustainable Catalyst Python Runtime v1.0.0","arbitrary_python_source":False,"shell_execution":False,"runtime_package_install":False,"job_network_access":False,"provider_managed_execution":True})
    return RuntimeAdapterDescriptor(adapter_id="adapter:sc-runtime-python",runtime=runtime,provider_contracts=["sc.core.python-runtime.v1","sc.core.reproducible-environment-package.v1","sc.core.runtime-security-governance.v1"],transport="http",invocation_mode="governed-service",service_ref="sc-python-runtime",status="registered",metadata={"core_executes_runtime_directly":False,"endpoint":"http://127.0.0.1:18103","native_runtime":"CPython","native_runtime_version":"3.12.3","language":"python"})

def _prolog_runtime_adapter() -> RuntimeAdapterDescriptor:
    capability = RuntimeCapability(capability_key="bounded-logic-constraint-reasoning",category="logic-constraint",operations=["relation_reachable","relation_paths_bounded","transitive_closure","contradiction_scan","temporal_consistency","graph_coloring"],input_types=["json","relation-graph","claim-set","temporal-constraints","graph"],output_types=["json","boolean","path-set","relation-set","contradiction-set","constraint-solution","diagnostics"],deterministic=True,arbitrary_code_execution=False,shell_execution=False,package_installation=False,metadata={"provider_contract":"sc.core.prolog-runtime.v1","environment_contract":"sc.core.reproducible-environment-package.v1","native_runtime":"SWI-Prolog","native_runtime_version":"9.0.4","native_package_version":"9.0.4+dfsg-3.1ubuntu4","provider_generated_programs":True})
    runtime = RuntimeDescriptor(runtime_id="sc-runtime-prolog",runtime_kind=RuntimeKind.language,language="prolog",implementation="SWI-Prolog",runtime_version="9.0.4",provider_version="1.0.0",service_name="sc-prolog-runtime",contract_versions=[OBJECT_CONTRACT_VERSION,ADAPTER_CONTRACT_VERSION,"sc.core.prolog-runtime.v1","sc.core.reproducible-environment-package.v1","sc.core.runtime-security-governance.v1"],capabilities=[capability],execution_host="contabo-vps",status="active",metadata={"canonical_runtime":True,"provider_release":"Sustainable Catalyst Prolog Runtime v1.0.0","arbitrary_prolog_source":False,"shell_execution":False,"runtime_package_install":False,"provider_generated_programs":True})
    return RuntimeAdapterDescriptor(adapter_id="adapter:sc-runtime-prolog",runtime=runtime,provider_contracts=["sc.core.prolog-runtime.v1","sc.core.reproducible-environment-package.v1","sc.core.runtime-security-governance.v1"],transport="http",invocation_mode="governed-service",service_ref="sc-prolog-runtime",status="registered",metadata={"core_executes_runtime_directly":False,"endpoint":"http://127.0.0.1:18104","native_runtime":"SWI-Prolog","native_runtime_version":"9.0.4","language":"prolog"})

def _jvm_runtime_adapter() -> RuntimeAdapterDescriptor:
    capability = RuntimeCapability(capability_key="managed-jvm-execution",category="managed-vm",operations=["jvm_runtime_info","parallel_sum","parallel_map_affine","matrix_row_sums","graph_bfs","batch_sha256"],input_types=["json","numeric-vector","matrix","graph","string-batch"],output_types=["json","scalar","vector","distance-vector","hash-batch","diagnostics"],deterministic=True,arbitrary_code_execution=False,shell_execution=False,package_installation=False,metadata={"provider_contract":"sc.core.jvm-runtime.v1","environment_contract":"sc.core.reproducible-environment-package.v1","native_runtime":"OpenJDK JVM","native_runtime_version":"21","provider_generated_bootstrap_java":True,"language_profiles_deferred_to":"3.56.1"})
    runtime = RuntimeDescriptor(runtime_id="sc-runtime-jvm",runtime_kind=RuntimeKind.execution_target,language="jvm-bytecode",implementation="OpenJDK JVM",runtime_version="21",provider_version="1.0.0",service_name="sc-jvm-runtime",contract_versions=[OBJECT_CONTRACT_VERSION,ADAPTER_CONTRACT_VERSION,"sc.core.jvm-runtime.v1","sc.core.reproducible-environment-package.v1","sc.core.runtime-security-governance.v1"],capabilities=[capability],execution_host="contabo-vps",status="active",metadata={"canonical_runtime":True,"provider_release":"Sustainable Catalyst JVM Runtime v1.0.0","arbitrary_jvm_bytecode":False,"caller_classpath":False,"runtime_dependency_install":False,"language_profiles_deferred_to":"3.56.1"})
    return RuntimeAdapterDescriptor(adapter_id="adapter:sc-runtime-jvm",runtime=runtime,provider_contracts=["sc.core.jvm-runtime.v1","sc.core.reproducible-environment-package.v1","sc.core.runtime-security-governance.v1"],transport="http",invocation_mode="governed-service",service_ref="sc-jvm-runtime",status="registered",metadata={"core_executes_runtime_directly":False,"endpoint":"http://127.0.0.1:18105","native_runtime":"OpenJDK JVM","native_runtime_version":"21","language":"jvm-bytecode"})

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
        self.register(_r_runtime_adapter())
        self.register(_stan_runtime_adapter())
        self.register(_octave_runtime_adapter())
        self.register(_gretl_runtime_adapter())
        self.register(_haskell_runtime_adapter())
        self.register(_fortran_runtime_adapter())
        self.register(_cpp_runtime_adapter())
        self.register(_rust_runtime_adapter())
        self.register(_go_runtime_adapter())
        self.register(_python_runtime_adapter())
        self.register(_prolog_runtime_adapter())
        self.register(_jvm_runtime_adapter())

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
