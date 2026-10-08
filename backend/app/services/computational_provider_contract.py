from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "4.20.2"
CONTRACT_VERSION = "sc.core.computational-provider-contract.v1"
PREDECESSOR_CONTRACT = "sc.core.external-provider-registry.v1"
LEGACY_ANALYTICAL_CONTRACT = "sc.core.analytical-runtime-provider.v1"


class ComputationalEngineKind(str, Enum):
    general = "general"
    symbolic = "symbolic"
    numerical = "numerical"
    statistical = "statistical"
    simulation = "simulation"
    optimization = "optimization"
    functional = "functional"


class ComputationalExecutionHost(str, Enum):
    external_service = "external-service"
    workbench = "workbench"
    workspace = "workspace"
    lab = "lab"
    provider_managed = "provider-managed"
    caller_managed = "caller-managed"


class ComputationalImplementationState(str, Enum):
    reference_only = "reference-only"
    internal_runtime_reference = "internal-runtime-reference"
    proposed = "proposed"


class DeterminismClass(str, Enum):
    deterministic = "deterministic"
    seeded = "seeded"
    environment_dependent = "environment-dependent"
    provider_dependent = "provider-dependent"
    unknown = "unknown"


class ComputationalResultState(str, Enum):
    declared = "declared"
    completed = "completed"
    partial = "partial"
    failed = "failed"
    cancelled = "cancelled"


class ComputationalComparisonDisposition(str, Enum):
    exact_agreement = "exact-agreement"
    tolerance_agreement = "tolerance-agreement"
    symbolic_equivalence = "symbolic-equivalence"
    discrepancy = "discrepancy"
    incomparable = "incomparable"
    unresolved = "unresolved"


class ComputationalCapabilityDeclaration(BaseModel):
    capability_id: str = Field(min_length=3)
    operation: str = Field(min_length=2, max_length=160)
    engine_kind: ComputationalEngineKind
    input_types: list[str] = Field(min_length=1)
    output_types: list[str] = Field(min_length=1)
    supports_units: bool = False
    supports_exact_arithmetic: bool = False
    supports_seed_control: bool = False
    supports_assumptions: bool = True
    output_requires_provenance: Literal[True] = True
    output_is_not_automatically_evidence: Literal[True] = True

    @model_validator(mode="after")
    def validate_types(self):
        if len(self.input_types) != len(set(self.input_types)):
            raise ValueError("input_types must be unique")
        if len(self.output_types) != len(set(self.output_types)):
            raise ValueError("output_types must be unique")
        return self


class ComputationalProviderProfile(BaseModel):
    profile_id: str = Field(min_length=3)
    display_name: str = Field(min_length=2, max_length=200)
    provider_registry_ref: str | None = None
    registry_binding_state: Literal["registered-reference", "internal-runtime-reference", "proposed"]
    implementation_state: ComputationalImplementationState
    engine_kinds: list[ComputationalEngineKind] = Field(min_length=1)
    execution_host: ComputationalExecutionHost
    capabilities: list[ComputationalCapabilityDeclaration] = Field(min_length=1)
    runtime_or_service_version: str = Field(min_length=1, max_length=120)
    reference_profile_only: Literal[True] = True
    connectivity_verified: Literal[False] = False
    execution_authorized_by_core: Literal[False] = False
    provider_output_establishes_truth: Literal[False] = False
    provider_output_auto_promotes_evidence: Literal[False] = False

    @model_validator(mode="after")
    def validate_profile(self):
        if len(self.engine_kinds) != len(set(self.engine_kinds)):
            raise ValueError("engine_kinds must be unique")
        ids=[c.capability_id for c in self.capabilities]
        if len(ids) != len(set(ids)):
            raise ValueError("capability ids must be unique per profile")
        if any(c.engine_kind not in self.engine_kinds for c in self.capabilities):
            raise ValueError("capability engine_kind must be declared by provider profile")
        if self.registry_binding_state == "registered-reference" and not self.provider_registry_ref:
            raise ValueError("registered-reference profile requires provider_registry_ref")
        if self.provider_registry_ref and not self.provider_registry_ref.startswith("provider:"):
            raise ValueError("provider_registry_ref must use provider: identity")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ComputationalInputBinding(BaseModel):
    input_id: str = Field(min_length=3)
    object_ref: str = Field(min_length=3)
    role: str = Field(min_length=2, max_length=100)
    unit: str | None = None
    content_hash: str | None = None
    source_provenance_ref: str | None = None


class ComputationalAssumptionSet(BaseModel):
    assumption_set_id: str = Field(min_length=3)
    assumptions: list[str] = Field(default_factory=list)
    unit_system: str | None = None
    precision_policy: str | None = None
    tolerance: float | None = Field(default=None, ge=0)
    random_seed: int | None = None
    assumptions_are_declared_not_inferred: Literal[True] = True


class ComputationalExecutionEnvironment(BaseModel):
    environment_id: str = Field(min_length=3)
    provider_profile_id: str = Field(min_length=3)
    runtime_or_service_version: str = Field(min_length=1)
    package_or_model_versions: dict[str, str] = Field(default_factory=dict)
    container_or_endpoint_ref: str | None = None
    locale: str | None = None
    timezone: str | None = None
    determinism_class: DeterminismClass
    environment_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ComputationalRequestEnvelope(BaseModel):
    request_id: str = Field(min_length=3)
    provider_profile_id: str = Field(min_length=3)
    capability_id: str = Field(min_length=3)
    operation: str = Field(min_length=2)
    inputs: list[ComputationalInputBinding] = Field(min_length=1)
    assumption_set_id: str
    environment_id: str
    requested_by_product: str = Field(min_length=2)
    external_execution_ref: str | None = None
    reference_fixture_only: Literal[True] = True
    core_executes_request: Literal[False] = False
    request_is_not_evidence: Literal[True] = True


class ComputationalResultEnvelope(BaseModel):
    result_id: str = Field(min_length=3)
    request_id: str = Field(min_length=3)
    provider_profile_id: str = Field(min_length=3)
    state: ComputationalResultState
    result_payload: dict[str, Any]
    diagnostics: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    external_execution_ref: str | None = None
    external_execution_performed: Literal[False] = False
    reference_fixture_only: Literal[True] = True
    provenance_complete: Literal[True] = True
    result_establishes_truth: Literal[False] = False
    result_auto_promotes_evidence: Literal[False] = False


class ComputationalResultComparison(BaseModel):
    comparison_id: str = Field(min_length=3)
    left_result_id: str = Field(min_length=3)
    right_result_id: str = Field(min_length=3)
    disposition: ComputationalComparisonDisposition
    basis: list[str] = Field(min_length=1)
    tolerance: float | None = Field(default=None, ge=0)
    comparison_is_reference_fixture: Literal[True] = True
    agreement_establishes_truth: Literal[False] = False
    discrepancy_establishes_error: Literal[False] = False
    comparison_auto_selects_winner: Literal[False] = False


class ComputationalProviderPolicy(BaseModel):
    policy_id: str = Field(min_length=3)
    provider_registry_binding_required_for_external_services: Literal[True] = True
    execution_occurs_outside_core: Literal[True] = True
    explicit_capability_match_required: Literal[True] = True
    explicit_assumptions_required: Literal[True] = True
    explicit_environment_required: Literal[True] = True
    units_and_precision_must_be_preserved: Literal[True] = True
    provenance_required: Literal[True] = True
    failures_and_partial_results_must_be_preserved: Literal[True] = True
    legacy_analytical_runtime_lineage_preserved: Literal[True] = True
    computational_output_establishes_truth: Literal[False] = False
    computational_output_auto_promotes_evidence: Literal[False] = False
    multi_engine_agreement_establishes_truth: Literal[False] = False
    discrepancy_auto_identifies_faulty_engine: Literal[False] = False
    core_selects_provider_autonomously: Literal[False] = False
    core_executes_provider: Literal[False] = False
    contract_authorizes_graph_mutation: Literal[False] = False


class ComputationalProviderSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3)
    provider_fingerprints: dict[str, str]
    request_result_pairs: dict[str, str]
    deterministic_contract_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    supersedable: Literal[True] = True
    snapshot_is_not_connectivity_execution_or_truth_certification: Literal[True] = True


class ComputationalProviderContractBundle(BaseModel):
    release: Literal["4.20.2"] = "4.20.2"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    legacy_analytical_contract: Literal[LEGACY_ANALYTICAL_CONTRACT] = LEGACY_ANALYTICAL_CONTRACT
    policy: ComputationalProviderPolicy
    providers: list[ComputationalProviderProfile] = Field(min_length=1)
    assumption_sets: list[ComputationalAssumptionSet] = Field(min_length=1)
    environments: list[ComputationalExecutionEnvironment] = Field(min_length=1)
    requests: list[ComputationalRequestEnvelope] = Field(min_length=1)
    results: list[ComputationalResultEnvelope] = Field(min_length=1)
    comparisons: list[ComputationalResultComparison] = Field(min_length=1)
    snapshots: list[ComputationalProviderSnapshot] = Field(min_length=1, max_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        def unique(items, attr, label):
            vals=[getattr(x,attr) for x in items]
            if len(vals) != len(set(vals)):
                raise ValueError(f"{label} must be unique")
            return set(vals)
        pids=unique(self.providers,"profile_id","provider profile ids")
        aids=unique(self.assumption_sets,"assumption_set_id","assumption set ids")
        eids=unique(self.environments,"environment_id","environment ids")
        rids=unique(self.requests,"request_id","request ids")
        result_ids=unique(self.results,"result_id","result ids")
        unique(self.comparisons,"comparison_id","comparison ids")
        provider_map={p.profile_id:p for p in self.providers}
        env_map={e.environment_id:e for e in self.environments}
        req_map={r.request_id:r for r in self.requests}
        result_map={r.result_id:r for r in self.results}
        for env in self.environments:
            if env.provider_profile_id not in pids: raise ValueError("environment provider profile missing")
        for req in self.requests:
            if req.provider_profile_id not in pids: raise ValueError("request provider profile missing")
            if req.assumption_set_id not in aids: raise ValueError("request assumption set missing")
            if req.environment_id not in eids: raise ValueError("request environment missing")
            if env_map[req.environment_id].provider_profile_id != req.provider_profile_id: raise ValueError("request environment provider mismatch")
            profile=provider_map[req.provider_profile_id]
            caps={c.capability_id:c for c in profile.capabilities}
            if req.capability_id not in caps: raise ValueError("request capability not declared by provider")
            if caps[req.capability_id].operation != req.operation: raise ValueError("request operation does not match declared capability")
        for result in self.results:
            if result.request_id not in rids: raise ValueError("result request missing")
            if result.provider_profile_id not in pids: raise ValueError("result provider profile missing")
            if req_map[result.request_id].provider_profile_id != result.provider_profile_id: raise ValueError("result provider does not match request")
        for comp in self.comparisons:
            if comp.left_result_id not in result_ids or comp.right_result_id not in result_ids: raise ValueError("comparison result missing")
            if comp.left_result_id == comp.right_result_id: raise ValueError("comparison requires distinct results")
        pf={p.profile_id:p.fingerprint() for p in self.providers}
        pairs={r.request_id: next(x.result_id for x in self.results if x.request_id==r.request_id) for r in self.requests}
        snap=self.snapshots[0]
        expected=canonical_sha256({"contract":self.contract,"providers":pf,"pairs":pairs})
        if snap.provider_fingerprints != pf: raise ValueError("snapshot provider fingerprint mismatch")
        if snap.request_result_pairs != pairs: raise ValueError("snapshot request/result pair mismatch")
        if snap.deterministic_contract_fingerprint_sha256 != expected: raise ValueError("snapshot deterministic fingerprint mismatch")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _cap(pid: str, op: str, kind: ComputationalEngineKind, *, units=False, exact=False, seed=False) -> ComputationalCapabilityDeclaration:
    return ComputationalCapabilityDeclaration(
        capability_id=f"capability:{pid}:{op}", operation=op, engine_kind=kind,
        input_types=["computational-expression"], output_types=["computational-result"],
        supports_units=units, supports_exact_arithmetic=exact, supports_seed_control=seed,
    )


def _profile(pid: str, name: str, kinds: list[ComputationalEngineKind], host: ComputationalExecutionHost,
             state: ComputationalImplementationState, binding: str, registry_ref: str | None,
             caps: list[ComputationalCapabilityDeclaration]) -> ComputationalProviderProfile:
    return ComputationalProviderProfile(
        profile_id=pid, display_name=name, provider_registry_ref=registry_ref,
        registry_binding_state=binding, implementation_state=state, engine_kinds=kinds,
        execution_host=host, capabilities=caps, runtime_or_service_version="reference-v1",
    )


def _env(pid: str, determinism: DeterminismClass) -> ComputationalExecutionEnvironment:
    raw={"profile":pid,"runtime":"reference-v1","determinism":determinism.value}
    return ComputationalExecutionEnvironment(
        environment_id=f"environment:{pid}:reference-v1", provider_profile_id=pid,
        runtime_or_service_version="reference-v1", package_or_model_versions={},
        determinism_class=determinism, environment_fingerprint_sha256=canonical_sha256(raw),
    )


@lru_cache(maxsize=1)
def reference_computational_provider_contract_bundle() -> ComputationalProviderContractBundle:
    providers=[
        _profile("compute:wolfram","Wolfram",[ComputationalEngineKind.general,ComputationalEngineKind.symbolic,ComputationalEngineKind.numerical],ComputationalExecutionHost.external_service,ComputationalImplementationState.reference_only,"registered-reference","provider:wolfram",[_cap("compute:wolfram","evaluate",ComputationalEngineKind.general,units=True),_cap("compute:wolfram","solve-symbolically",ComputationalEngineKind.symbolic,units=True,exact=True)]),
        _profile("compute:python","Python",[ComputationalEngineKind.general,ComputationalEngineKind.numerical,ComputationalEngineKind.statistical],ComputationalExecutionHost.workbench,ComputationalImplementationState.internal_runtime_reference,"internal-runtime-reference",None,[_cap("compute:python","evaluate",ComputationalEngineKind.general,units=True),_cap("compute:python","statistical-analysis",ComputationalEngineKind.statistical,seed=True)]),
        _profile("compute:r","R Runtime",[ComputationalEngineKind.statistical],ComputationalExecutionHost.workbench,ComputationalImplementationState.internal_runtime_reference,"internal-runtime-reference",None,[_cap("compute:r","statistical-analysis",ComputationalEngineKind.statistical,seed=True),_cap("compute:r","model-diagnostics",ComputationalEngineKind.statistical,seed=True)]),
        _profile("compute:julia","Julia",[ComputationalEngineKind.numerical,ComputationalEngineKind.simulation,ComputationalEngineKind.optimization],ComputationalExecutionHost.workbench,ComputationalImplementationState.internal_runtime_reference,"internal-runtime-reference",None,[_cap("compute:julia","numerical-solve",ComputationalEngineKind.numerical),_cap("compute:julia","simulate",ComputationalEngineKind.simulation,seed=True)]),
        _profile("compute:sympy","SymPy",[ComputationalEngineKind.symbolic],ComputationalExecutionHost.workbench,ComputationalImplementationState.internal_runtime_reference,"internal-runtime-reference",None,[_cap("compute:sympy","solve-symbolically",ComputationalEngineKind.symbolic,exact=True),_cap("compute:sympy","simplify",ComputationalEngineKind.symbolic,exact=True)]),
        _profile("compute:haskell","Haskell",[ComputationalEngineKind.functional,ComputationalEngineKind.general],ComputationalExecutionHost.workbench,ComputationalImplementationState.proposed,"proposed",None,[_cap("compute:haskell","evaluate",ComputationalEngineKind.general),_cap("compute:haskell","transform",ComputationalEngineKind.functional)]),
        _profile("compute:workbench-native","Workbench Native",[ComputationalEngineKind.general,ComputationalEngineKind.numerical,ComputationalEngineKind.optimization],ComputationalExecutionHost.workbench,ComputationalImplementationState.internal_runtime_reference,"internal-runtime-reference",None,[_cap("compute:workbench-native","evaluate",ComputationalEngineKind.general,units=True),_cap("compute:workbench-native","optimize",ComputationalEngineKind.optimization,units=True)]),
    ]
    assumptions=[
        ComputationalAssumptionSet(assumption_set_id="assumptions:symbolic-reference",assumptions=["real-domain fixture"],unit_system="dimensionless",precision_policy="exact"),
        ComputationalAssumptionSet(assumption_set_id="assumptions:statistical-reference",assumptions=["reference dataset fixture"],precision_policy="float64",random_seed=42),
    ]
    envs=[_env(p.profile_id, DeterminismClass.provider_dependent if p.profile_id=="compute:wolfram" else (DeterminismClass.seeded if p.profile_id in {"compute:python","compute:r","compute:julia"} else DeterminismClass.deterministic)) for p in providers]
    requests=[
        ComputationalRequestEnvelope(request_id="request:wolfram:symbolic",provider_profile_id="compute:wolfram",capability_id="capability:compute:wolfram:solve-symbolically",operation="solve-symbolically",inputs=[ComputationalInputBinding(input_id="input:wolfram:expr",object_ref="fixture:equation:x2-minus-4",role="expression")],assumption_set_id="assumptions:symbolic-reference",environment_id="environment:compute:wolfram:reference-v1",requested_by_product="Workbench"),
        ComputationalRequestEnvelope(request_id="request:sympy:symbolic",provider_profile_id="compute:sympy",capability_id="capability:compute:sympy:solve-symbolically",operation="solve-symbolically",inputs=[ComputationalInputBinding(input_id="input:sympy:expr",object_ref="fixture:equation:x2-minus-4",role="expression")],assumption_set_id="assumptions:symbolic-reference",environment_id="environment:compute:sympy:reference-v1",requested_by_product="Workbench"),
        ComputationalRequestEnvelope(request_id="request:python:statistics",provider_profile_id="compute:python",capability_id="capability:compute:python:statistical-analysis",operation="statistical-analysis",inputs=[ComputationalInputBinding(input_id="input:python:data",object_ref="fixture:dataset:statistics-1",role="dataset")],assumption_set_id="assumptions:statistical-reference",environment_id="environment:compute:python:reference-v1",requested_by_product="Lab"),
        ComputationalRequestEnvelope(request_id="request:r:statistics",provider_profile_id="compute:r",capability_id="capability:compute:r:statistical-analysis",operation="statistical-analysis",inputs=[ComputationalInputBinding(input_id="input:r:data",object_ref="fixture:dataset:statistics-1",role="dataset")],assumption_set_id="assumptions:statistical-reference",environment_id="environment:compute:r:reference-v1",requested_by_product="Lab"),
    ]
    results=[
        ComputationalResultEnvelope(result_id="result:wolfram:symbolic",request_id="request:wolfram:symbolic",provider_profile_id="compute:wolfram",state=ComputationalResultState.declared,result_payload={"normalized_fixture":"roots:-2,2"},diagnostics=["reference fixture only; no Wolfram execution performed"]),
        ComputationalResultEnvelope(result_id="result:sympy:symbolic",request_id="request:sympy:symbolic",provider_profile_id="compute:sympy",state=ComputationalResultState.declared,result_payload={"normalized_fixture":"roots:-2,2"},diagnostics=["reference fixture only; no SymPy execution performed"]),
        ComputationalResultEnvelope(result_id="result:python:statistics",request_id="request:python:statistics",provider_profile_id="compute:python",state=ComputationalResultState.declared,result_payload={"normalized_fixture":"mean:10.0"},diagnostics=["reference fixture only; no Python execution performed"]),
        ComputationalResultEnvelope(result_id="result:r:statistics",request_id="request:r:statistics",provider_profile_id="compute:r",state=ComputationalResultState.declared,result_payload={"normalized_fixture":"mean:10.0"},diagnostics=["reference fixture only; no R execution performed"]),
    ]
    comparisons=[
        ComputationalResultComparison(comparison_id="comparison:symbolic-reference",left_result_id="result:wolfram:symbolic",right_result_id="result:sympy:symbolic",disposition=ComputationalComparisonDisposition.symbolic_equivalence,basis=["normalized reference fixture equality"]),
        ComputationalResultComparison(comparison_id="comparison:statistics-reference",left_result_id="result:python:statistics",right_result_id="result:r:statistics",disposition=ComputationalComparisonDisposition.exact_agreement,basis=["normalized reference fixture equality"]),
    ]
    pf={p.profile_id:p.fingerprint() for p in providers}
    pairs={q.request_id:next(r.result_id for r in results if r.request_id==q.request_id) for q in requests}
    deterministic=canonical_sha256({"contract":CONTRACT_VERSION,"providers":pf,"pairs":pairs})
    return ComputationalProviderContractBundle(
        policy=ComputationalProviderPolicy(policy_id="computational-provider-policy:v1"),providers=providers,
        assumption_sets=assumptions,environments=envs,requests=requests,results=results,comparisons=comparisons,
        snapshots=[ComputationalProviderSnapshot(snapshot_id="computational-provider-snapshot:reference-v1",provider_fingerprints=pf,request_result_pairs=pairs,deterministic_contract_fingerprint_sha256=deterministic)],
    )


def contract_document() -> dict:
    b=reference_computational_provider_contract_bundle()
    registered=sum(p.registry_binding_state=="registered-reference" for p in b.providers)
    internal=sum(p.registry_binding_state=="internal-runtime-reference" for p in b.providers)
    proposed=sum(p.registry_binding_state=="proposed" for p in b.providers)
    return {
        "ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"predecessor_contract":PREDECESSOR_CONTRACT,
        "legacy_analytical_contract":LEGACY_ANALYTICAL_CONTRACT,
        "identity":{"product":"Sustainable Catalyst Platform Core","build":"Computational Provider Contract","major_api":"v4"},
        "principles":{
            "external_computational_services_bind_to_provider_registry":True,
            "capability_match_is_explicit":True,"assumptions_are_explicit":True,"environment_is_explicit":True,
            "units_precision_and_seed_are_preserved":True,"provenance_is_required":True,
            "legacy_analytical_runtime_lineage_is_preserved":True,"execution_occurs_outside_core":True,
        },
        "boundaries":{
            "computational_output_establishes_truth":False,"computational_output_auto_promotes_evidence":False,
            "multi_engine_agreement_establishes_truth":False,"discrepancy_auto_identifies_faulty_engine":False,
            "core_selects_provider_autonomously":False,"core_executes_provider":False,"contract_authorizes_graph_mutation":False,
            "reference_fixture_establishes_live_connectivity":False,
        },
        "reference":{
            "provider_profiles":len(b.providers),"registered_external_provider_profiles":registered,"internal_runtime_profiles":internal,
            "proposed_profiles":proposed,"capabilities":sum(len(p.capabilities) for p in b.providers),
            "assumption_sets":len(b.assumption_sets),"environments":len(b.environments),"requests":len(b.requests),
            "results":len(b.results),"comparisons":len(b.comparisons),"snapshots":len(b.snapshots),
            "bundle_fingerprint_sha256":b.fingerprint(),"contract_snapshot_fingerprint_sha256":b.snapshots[0].deterministic_contract_fingerprint_sha256,
        },
        "roadmap_integration":{
            "extends_v4201_provider_registry":True,"preserves_v4200_reasoning_consolidation":True,
            "prepares_workbench_wolfram_provider":True,"prepares_multi_engine_verification":True,
            "prepares_dataset_observation_vintage_contract":True,"prepares_library_provider_runtime":True,
        },
        "database_migration":"none",
    }
