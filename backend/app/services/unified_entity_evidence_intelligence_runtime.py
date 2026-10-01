from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .entity_resolution_identity_graph import (
    CONTRACT_VERSION as C377, reference_entity_resolution_identity_graph_bundle,
)
from .temporal_identity_intelligence import (
    CONTRACT_VERSION as C378, reference_temporal_identity_intelligence_bundle,
)
from .probabilistic_record_linkage import (
    CONTRACT_VERSION as C379, reference_probabilistic_record_linkage_bundle,
)
from .cross_source_entity_reconciliation import (
    CONTRACT_VERSION as C380, reference_cross_source_entity_reconciliation_bundle,
)
from .public_record_documentary_source import (
    CONTRACT_VERSION as C381, reference_public_record_documentary_source_bundle,
)
from .relationship_discovery_hypotheses import (
    CONTRACT_VERSION as C382, reference_relationship_discovery_hypothesis_bundle,
)
from .network_structure_community_motif import (
    CONTRACT_VERSION as C383, reference_network_structure_community_motif_bundle,
)
from .explainable_connection_paths_evidence_chains import (
    CONTRACT_VERSION as C384, reference_explainable_connection_paths_evidence_chains_bundle,
)
from .multi_hop_research_investigation_graph_reasoning import (
    CONTRACT_VERSION as C385, reference_multi_hop_research_investigation_graph_reasoning_bundle,
)
from .contradictory_identity_relationship_resolution import (
    CONTRACT_VERSION as C386, reference_contradictory_identity_relationship_resolution_bundle,
)
from .entity_centric_timeline_event_association import (
    CONTRACT_VERSION as C387, reference_entity_centric_timeline_event_association_bundle,
)
from .reproducible_graph_investigation_package import (
    CONTRACT_VERSION as C388, reference_reproducible_graph_investigation_package_bundle,
)
from .federated_evidence_graph_exchange import (
    CONTRACT_VERSION as C389, reference_federated_evidence_graph_exchange_bundle,
)

CORE_RELEASE = "3.90.0"
CONTRACT_VERSION = "sc.core.unified-entity-evidence-intelligence-runtime.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class RuntimeStageKind(str, Enum):
    identity_resolution = "identity-resolution"
    temporal_identity = "temporal-identity"
    record_linkage = "record-linkage"
    source_reconciliation = "source-reconciliation"
    documentary_source = "documentary-source"
    relationship_discovery = "relationship-discovery"
    network_intelligence = "network-intelligence"
    connection_paths = "connection-paths"
    multi_hop_reasoning = "multi-hop-reasoning"
    contradiction_resolution = "contradiction-resolution"
    timeline = "timeline"
    reproducible_package = "reproducible-package"
    federation = "federation"


class RuntimeStageStatus(str, Enum):
    completed = "completed"
    qualified = "qualified"
    handoff_required = "handoff-required"
    stopped = "stopped"


class RuntimeDisposition(str, Enum):
    qualified_analytical = "qualified-analytical"
    unresolved = "unresolved"
    validation_required = "validation-required"
    reference_only = "reference-only"


class RuntimeCapabilityBinding(BaseModel):
    capability_id: str = Field(min_length=2, max_length=500)
    stage_kind: RuntimeStageKind
    release: str = Field(pattern=r"^3\.(?:7[7-9]|8[0-9])\.0$")
    contract: str = Field(min_length=3, max_length=500)
    service_module: str = Field(min_length=3, max_length=500)
    reference_bundle_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    preserves_upstream_contract: Literal[True] = True
    preserves_epistemic_state: Literal[True] = True
    preserves_provenance: Literal[True] = True
    may_mutate_identity_graph: Literal[False] = False
    may_mutate_relationship_graph: Literal[False] = False
    may_mutate_evidence_graph: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class UnifiedRuntimePolicy(BaseModel):
    runtime_policy_id: str = Field(min_length=2, max_length=500)
    require_capability_contract_identity: Literal[True] = True
    require_provenance_preservation: Literal[True] = True
    require_epistemic_state_preservation: Literal[True] = True
    require_contradiction_preservation: Literal[True] = True
    require_explicit_handoffs: Literal[True] = True
    require_explicit_stopping_decisions: Literal[True] = True
    require_local_validation_for_remote_references: Literal[True] = True
    require_human_review_for_promotion: Literal[True] = True
    runtime_may_create_global_truth_score: Literal[False] = False
    runtime_may_auto_promote_candidates: Literal[False] = False
    runtime_may_auto_resolve_contradictions: Literal[False] = False
    runtime_may_treat_remote_acceptance_as_evidence: Literal[False] = False
    runtime_may_mutate_governed_graphs: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class UnifiedRuntimeRequest(BaseModel):
    runtime_request_id: str = Field(min_length=2, max_length=500)
    objective: str = Field(min_length=3, max_length=8000)
    start_entity_refs: list[str] = Field(min_length=1)
    target_entity_refs: list[str] = Field(default_factory=list)
    requested_capability_refs: list[str] = Field(min_length=1)
    as_of: str = Field(min_length=10, max_length=80)
    max_hops: int = Field(ge=1, le=25)
    include_remote_references: bool = False
    no_graph_mutation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_request(self):
        _unique(self.start_entity_refs,"start_entity_refs")
        _unique(self.target_entity_refs,"target_entity_refs")
        _unique(self.requested_capability_refs,"requested_capability_refs")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class RuntimeStageExecution(BaseModel):
    runtime_stage_execution_id: str = Field(min_length=2, max_length=500)
    capability_ref: str = Field(min_length=2, max_length=500)
    sequence: int = Field(ge=1)
    input_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(min_length=1)
    input_epistemic_states: list[str] = Field(default_factory=list)
    output_epistemic_states: list[str] = Field(min_length=1)
    contradiction_refs: list[str] = Field(default_factory=list)
    status: RuntimeStageStatus
    qualification_note: str = Field(min_length=3, max_length=8000)
    stage_output_is_not_truth_verdict: Literal[True] = True
    stage_does_not_auto_promote_graph_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_stage(self):
        for vals,label in ((self.input_refs,"input_refs"),(self.output_refs,"output_refs"),(self.contradiction_refs,"contradiction_refs")):
            _unique(vals,label)
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class RuntimeHandoffDecision(BaseModel):
    runtime_handoff_decision_id: str = Field(min_length=2, max_length=500)
    from_stage_ref: str = Field(min_length=2, max_length=500)
    to_stage_ref: str = Field(min_length=2, max_length=500)
    reason: str = Field(min_length=3, max_length=8000)
    source_output_refs: list[str] = Field(min_length=1)
    handoff_required: Literal[True] = True
    auto_promotion_allowed: Literal[False] = False
    handoff_is_not_validation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_handoff(self):
        if self.from_stage_ref == self.to_stage_ref: raise ValueError("handoff stages must differ")
        _unique(self.source_output_refs,"source_output_refs")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class UnifiedRuntimeFinding(BaseModel):
    unified_runtime_finding_id: str = Field(min_length=2, max_length=500)
    statement: str = Field(min_length=3, max_length=12000)
    basis_refs: list[str] = Field(min_length=1)
    contradiction_refs: list[str] = Field(default_factory=list)
    disposition: RuntimeDisposition
    human_review_required: Literal[True] = True
    finding_is_not_truth_verdict: Literal[True] = True
    analytical_confidence_is_not_probability_of_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_finding(self):
        _unique(self.basis_refs,"basis_refs"); _unique(self.contradiction_refs,"contradiction_refs")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class UnifiedRuntimeExecutionTrace(BaseModel):
    unified_runtime_execution_trace_id: str = Field(min_length=2, max_length=500)
    runtime_request_ref: str = Field(min_length=2, max_length=500)
    stage_execution_refs: list[str] = Field(min_length=1)
    handoff_refs: list[str] = Field(default_factory=list)
    finding_refs: list[str] = Field(default_factory=list)
    started_at: str = Field(min_length=10, max_length=80)
    completed_at: str = Field(min_length=10, max_length=80)
    final_disposition: RuntimeDisposition
    deterministic_trace_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    trace_is_not_proof: Literal[True] = True
    completed_runtime_is_not_truth_certification: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_trace(self):
        for vals,label in ((self.stage_execution_refs,"stage_execution_refs"),(self.handoff_refs,"handoff_refs"),(self.finding_refs,"finding_refs")):
            _unique(vals,label)
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class UnifiedRuntimeSnapshot(BaseModel):
    unified_runtime_snapshot_id: str = Field(min_length=2, max_length=500)
    runtime_policy_ref: str = Field(min_length=2, max_length=500)
    runtime_request_ref: str = Field(min_length=2, max_length=500)
    execution_trace_ref: str = Field(min_length=2, max_length=500)
    capability_refs: list[str] = Field(min_length=1)
    as_of: str = Field(min_length=10, max_length=80)
    immutable: Literal[True] = True
    upstream_objects_remain_authoritative_for_their_own_state: Literal[True] = True
    later_evidence_may_supersede_snapshot: Literal[True] = True
    snapshot_is_not_truth_verdict: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_snapshot(self):
        _unique(self.capability_refs,"capability_refs")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class UnifiedEntityEvidenceIntelligenceRuntimeBundle(BaseModel):
    release: Literal["3.90.0"] = "3.90.0"
    contract: Literal["sc.core.unified-entity-evidence-intelligence-runtime.v1"] = CONTRACT_VERSION
    capabilities: list[RuntimeCapabilityBinding] = Field(min_length=13, max_length=13)
    policies: list[UnifiedRuntimePolicy] = Field(min_length=1)
    requests: list[UnifiedRuntimeRequest] = Field(min_length=1)
    stage_executions: list[RuntimeStageExecution] = Field(min_length=1)
    handoffs: list[RuntimeHandoffDecision] = Field(default_factory=list)
    findings: list[UnifiedRuntimeFinding] = Field(min_length=1)
    traces: list[UnifiedRuntimeExecutionTrace] = Field(min_length=1)
    snapshots: list[UnifiedRuntimeSnapshot] = Field(min_length=1)
    identity_graph_mutation_performed: Literal[False] = False
    relationship_graph_mutation_performed: Literal[False] = False
    evidence_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        groups={
            "capability":[x.capability_id for x in self.capabilities],
            "policy":[x.runtime_policy_id for x in self.policies],
            "request":[x.runtime_request_id for x in self.requests],
            "stage":[x.runtime_stage_execution_id for x in self.stage_executions],
            "handoff":[x.runtime_handoff_decision_id for x in self.handoffs],
            "finding":[x.unified_runtime_finding_id for x in self.findings],
            "trace":[x.unified_runtime_execution_trace_id for x in self.traces],
            "snapshot":[x.unified_runtime_snapshot_id for x in self.snapshots],
        }
        for label, vals in groups.items(): _unique(vals,f"{label} ids")
        capabilities, policies, requests, stages, handoffs, findings, traces = map(set,[groups["capability"],groups["policy"],groups["request"],groups["stage"],groups["handoff"],groups["finding"],groups["trace"]])
        expected_kinds=set(RuntimeStageKind)
        actual_kinds={x.stage_kind for x in self.capabilities}
        if actual_kinds != expected_kinds: raise ValueError("all 13 runtime stage kinds must be bound exactly once")
        for req in self.requests:
            if not set(req.requested_capability_refs) <= capabilities: raise ValueError("request capability reference unresolved")
        for st in self.stage_executions:
            if st.capability_ref not in capabilities: raise ValueError("stage capability reference unresolved")
        stage_by_id={x.runtime_stage_execution_id:x for x in self.stage_executions}
        seq=[x.sequence for x in sorted(self.stage_executions,key=lambda x:x.sequence)]
        if seq != list(range(1,len(seq)+1)): raise ValueError("stage sequence must be contiguous from 1")
        for h in self.handoffs:
            if h.from_stage_ref not in stages or h.to_stage_ref not in stages: raise ValueError("handoff stage reference unresolved")
            if stage_by_id[h.to_stage_ref].sequence <= stage_by_id[h.from_stage_ref].sequence: raise ValueError("handoff must move forward")
        for tr in self.traces:
            if tr.runtime_request_ref not in requests or not set(tr.stage_execution_refs) <= stages or not set(tr.handoff_refs) <= handoffs or not set(tr.finding_refs) <= findings: raise ValueError("trace reference unresolved")
        for sn in self.snapshots:
            if sn.runtime_policy_ref not in policies or sn.runtime_request_ref not in requests or sn.execution_trace_ref not in traces or not set(sn.capability_refs) <= capabilities: raise ValueError("snapshot reference unresolved")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


@lru_cache(maxsize=1)
def _upstream_reference_fingerprints() -> tuple[tuple[str,str,str,str,str], ...]:
    specs=[
        ("capability:v3770",RuntimeStageKind.identity_resolution,"3.77.0",C377,"entity_resolution_identity_graph",reference_entity_resolution_identity_graph_bundle),
        ("capability:v3780",RuntimeStageKind.temporal_identity,"3.78.0",C378,"temporal_identity_intelligence",reference_temporal_identity_intelligence_bundle),
        ("capability:v3790",RuntimeStageKind.record_linkage,"3.79.0",C379,"probabilistic_record_linkage",reference_probabilistic_record_linkage_bundle),
        ("capability:v3800",RuntimeStageKind.source_reconciliation,"3.80.0",C380,"cross_source_entity_reconciliation",reference_cross_source_entity_reconciliation_bundle),
        ("capability:v3810",RuntimeStageKind.documentary_source,"3.81.0",C381,"public_record_documentary_source",reference_public_record_documentary_source_bundle),
        ("capability:v3820",RuntimeStageKind.relationship_discovery,"3.82.0",C382,"relationship_discovery_hypotheses",reference_relationship_discovery_hypothesis_bundle),
        ("capability:v3830",RuntimeStageKind.network_intelligence,"3.83.0",C383,"network_structure_community_motif",reference_network_structure_community_motif_bundle),
        ("capability:v3840",RuntimeStageKind.connection_paths,"3.84.0",C384,"explainable_connection_paths_evidence_chains",reference_explainable_connection_paths_evidence_chains_bundle),
        ("capability:v3850",RuntimeStageKind.multi_hop_reasoning,"3.85.0",C385,"multi_hop_research_investigation_graph_reasoning",reference_multi_hop_research_investigation_graph_reasoning_bundle),
        ("capability:v3860",RuntimeStageKind.contradiction_resolution,"3.86.0",C386,"contradictory_identity_relationship_resolution",reference_contradictory_identity_relationship_resolution_bundle),
        ("capability:v3870",RuntimeStageKind.timeline,"3.87.0",C387,"entity_centric_timeline_event_association",reference_entity_centric_timeline_event_association_bundle),
        ("capability:v3880",RuntimeStageKind.reproducible_package,"3.88.0",C388,"reproducible_graph_investigation_package",reference_reproducible_graph_investigation_package_bundle),
        ("capability:v3890",RuntimeStageKind.federation,"3.89.0",C389,"federated_evidence_graph_exchange",reference_federated_evidence_graph_exchange_bundle),
    ]
    rows=[]
    for cid,kind,release,contract,module,fn in specs:
        rows.append((cid,kind.value,release,contract,module,fn().fingerprint()))
    return tuple(rows)


def reference_unified_entity_evidence_intelligence_runtime_bundle() -> UnifiedEntityEvidenceIntelligenceRuntimeBundle:
    now="2026-09-30T23:30:00Z"
    capabilities=[RuntimeCapabilityBinding(
        capability_id=cid, stage_kind=RuntimeStageKind(kind), release=release, contract=contract,
        service_module=module, reference_bundle_fingerprint_sha256=fp,
    ) for cid,kind,release,contract,module,fp in _upstream_reference_fingerprints()]
    policy=UnifiedRuntimePolicy(runtime_policy_id="runtime-policy:unified-entity-evidence:v1")
    request=UnifiedRuntimeRequest(
        runtime_request_id="runtime-request:synthetic:v1",
        objective="Trace a synthetic entity/evidence question through all governed identity, evidence, relationship, reasoning, packaging, and federation stages without promoting analytical outputs into graph facts.",
        start_entity_refs=["entity:synthetic:a"], target_entity_refs=["entity:synthetic:b"],
        requested_capability_refs=[x.capability_id for x in capabilities], as_of=now, max_hops=12, include_remote_references=True,
    )
    out_states=[
        "candidate-identity","temporally-qualified","candidate-supported","source-preserved",
        "documentary-interpretation","hypothesis","analytical-network","explained-path",
        "qualified-reasoning","partially-resolved","qualified-timeline","reproducible-snapshot","remote-reference",
    ]
    stages=[]
    for i,(cap,state) in enumerate(zip(capabilities,out_states),1):
        inp=[] if i==1 else [f"runtime-output:synthetic:{i-1}"]
        inpstates=[] if i==1 else [out_states[i-2]]
        status=RuntimeStageStatus.qualified if i in {2,6,8,9,10,11,13} else RuntimeStageStatus.completed
        stages.append(RuntimeStageExecution(
            runtime_stage_execution_id=f"runtime-stage:synthetic:{i}", capability_ref=cap.capability_id, sequence=i,
            input_refs=inp, output_refs=[f"runtime-output:synthetic:{i}"], input_epistemic_states=inpstates,
            output_epistemic_states=[state], contradiction_refs=["contradiction:synthetic:preserved"] if i>=10 else [],
            status=status, qualification_note=f"Stage {i} preserves {state} as a governed runtime state; it does not promote that state into truth or a graph fact.",
        ))
    handoffs=[]
    for i in range(1,len(stages)):
        handoffs.append(RuntimeHandoffDecision(
            runtime_handoff_decision_id=f"runtime-handoff:synthetic:{i}",
            from_stage_ref=stages[i-1].runtime_stage_execution_id, to_stage_ref=stages[i].runtime_stage_execution_id,
            reason="Explicit contract-preserving handoff between governed capability stages.",
            source_output_refs=stages[i-1].output_refs,
        ))
    findings=[
        UnifiedRuntimeFinding(
            unified_runtime_finding_id="runtime-finding:synthetic:1",
            statement="The synthetic records form a qualified analytical connection path whose underlying identity, relationship, contradiction, and documentary states remain governed by their originating contracts.",
            basis_refs=[stages[7].output_refs[0],stages[8].output_refs[0],stages[9].output_refs[0]],
            contradiction_refs=["contradiction:synthetic:preserved"], disposition=RuntimeDisposition.qualified_analytical,
        ),
        UnifiedRuntimeFinding(
            unified_runtime_finding_id="runtime-finding:synthetic:2",
            statement="The federated representation is reference-only pending local validation and cannot be used as an automatic local evidence promotion.",
            basis_refs=[stages[-1].output_refs[0]], disposition=RuntimeDisposition.reference_only,
        ),
    ]
    trace_seed={"request":request.runtime_request_id,"stages":[x.runtime_stage_execution_id for x in stages],"handoffs":[x.runtime_handoff_decision_id for x in handoffs],"findings":[x.unified_runtime_finding_id for x in findings],"as_of":now}
    trace=UnifiedRuntimeExecutionTrace(
        unified_runtime_execution_trace_id="runtime-trace:synthetic:v1", runtime_request_ref=request.runtime_request_id,
        stage_execution_refs=[x.runtime_stage_execution_id for x in stages], handoff_refs=[x.runtime_handoff_decision_id for x in handoffs],
        finding_refs=[x.unified_runtime_finding_id for x in findings], started_at=now, completed_at=now,
        final_disposition=RuntimeDisposition.qualified_analytical, deterministic_trace_fingerprint_sha256=canonical_sha256(trace_seed),
    )
    snapshot=UnifiedRuntimeSnapshot(
        unified_runtime_snapshot_id="runtime-snapshot:synthetic:v1", runtime_policy_ref=policy.runtime_policy_id,
        runtime_request_ref=request.runtime_request_id, execution_trace_ref=trace.unified_runtime_execution_trace_id,
        capability_refs=[x.capability_id for x in capabilities], as_of=now,
    )
    return UnifiedEntityEvidenceIntelligenceRuntimeBundle(
        capabilities=capabilities, policies=[policy], requests=[request], stage_executions=stages,
        handoffs=handoffs, findings=findings, traces=[trace], snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    b=reference_unified_entity_evidence_intelligence_runtime_bundle()
    return {
        "ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
        "principles":{
            "unified_runtime_over_v3770_through_v3890":True,
            "upstream_contract_identity_preserved":True,
            "epistemic_state_preserved_across_stages":True,
            "provenance_preserved_across_stages":True,
            "contradictions_preserved_across_stages":True,
            "explicit_handoffs_and_stopping_rules":True,
            "local_validation_required_for_remote_references":True,
            "human_review_required_for_promotion":True,
            "reproducible_runtime_trace":True,
        },
        "boundaries":{
            "runtime_creates_global_truth_score":False,
            "runtime_auto_promotes_candidates":False,
            "runtime_auto_resolves_contradictions":False,
            "analytical_confidence_is_probability_of_truth":False,
            "completed_runtime_is_truth_certification":False,
            "remote_acceptance_is_local_evidence":False,
            "identity_graph_mutation_performed":False,
            "relationship_graph_mutation_performed":False,
            "evidence_graph_mutation_performed":False,
        },
        "reference":{
            "capabilities":len(b.capabilities),"stage_executions":len(b.stage_executions),"handoffs":len(b.handoffs),
            "findings":len(b.findings),"traces":len(b.traces),"snapshots":len(b.snapshots),
            "final_disposition":b.traces[0].final_disposition.value,"bundle_fingerprint_sha256":b.fingerprint(),
        },
        "database_migration":"none",
    }
