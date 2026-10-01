from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .unified_runtime_policy_capability_negotiation import (
    CONTRACT_VERSION as V391_CONTRACT,
    reference_unified_runtime_policy_capability_negotiation_bundle,
)

CORE_RELEASE = "3.92.0"
CONTRACT_VERSION = "sc.core.unified-entity-evidence-query-api.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class QueryMode(str, Enum):
    exact = "exact"
    exploratory = "exploratory"
    provenance = "provenance"
    graph_context = "graph-context"
    timeline = "timeline"
    federation_reference = "federation-reference"


class QueryTargetKind(str, Enum):
    entity = "entity"
    temporal_identity = "temporal-identity"
    record_linkage = "record-linkage"
    source_reconciliation = "source-reconciliation"
    documentary_source = "documentary-source"
    relationship = "relationship"
    network_structure = "network-structure"
    connection_path = "connection-path"
    evidence_chain = "evidence-chain"
    multi_hop_reasoning = "multi-hop-reasoning"
    contradiction = "contradiction"
    timeline = "timeline"
    investigation_package = "investigation-package"
    federation_reference = "federation-reference"
    runtime_metadata = "runtime-metadata"


class EpistemicState(str, Enum):
    governed_record = "governed-record"
    source_asserted = "source-asserted"
    candidate = "candidate"
    hypothesis = "hypothesis"
    analytical = "analytical"
    qualified = "qualified"
    unresolved = "unresolved"
    remote_reference = "remote-reference"
    runtime_metadata = "runtime-metadata"


class ResultValidationState(str, Enum):
    governed_reference = "governed-reference"
    review_required = "review-required"
    local_validation_required = "local-validation-required"
    analytical_only = "analytical-only"
    unresolved = "unresolved"
    metadata_only = "metadata-only"


class QueryExecutionDisposition(str, Enum):
    complete_with_qualifications = "complete-with-qualifications"
    partial = "partial"
    blocked = "blocked"


class UnifiedQueryPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    require_capability_negotiation: Literal[True] = True
    preserve_source_contract_identity: Literal[True] = True
    preserve_epistemic_state: Literal[True] = True
    preserve_provenance: Literal[True] = True
    preserve_validation_state: Literal[True] = True
    preserve_contradictions: Literal[True] = True
    preserve_remote_reference_state: Literal[True] = True
    enforce_consumer_scope: Literal[True] = True
    label_retrieval_scores_as_relevance_only: Literal[True] = True
    allow_cross_state_flattening: Literal[False] = False
    allow_candidate_promotion: Literal[False] = False
    allow_hypothesis_promotion: Literal[False] = False
    allow_remote_reference_promotion: Literal[False] = False
    allow_local_validation_bypass: Literal[False] = False
    allow_truth_score: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedQueryScope(BaseModel):
    scope_id: str = Field(min_length=3, max_length=500)
    target_kinds: list[QueryTargetKind] = Field(min_length=1)
    capability_refs: list[str] = Field(min_length=1)
    allowed_epistemic_states: list[EpistemicState] = Field(min_length=1)
    include_remote_references: bool = False
    include_contradictions: bool = True
    max_results: int = Field(default=100, ge=1, le=1000)
    valid_time_start: str | None = Field(default=None, max_length=80)
    valid_time_end: str | None = Field(default=None, max_length=80)
    scope_is_not_truth_filter: Literal[True] = True
    omitted_results_do_not_imply_nonexistence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_scope(self):
        _unique([x.value for x in self.target_kinds], "target_kinds")
        _unique(self.capability_refs, "capability_refs")
        _unique([x.value for x in self.allowed_epistemic_states], "allowed_epistemic_states")
        if self.valid_time_start and self.valid_time_end and self.valid_time_start > self.valid_time_end:
            raise ValueError("valid_time_start must not follow valid_time_end")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedEntityEvidenceQuery(BaseModel):
    query_id: str = Field(min_length=3, max_length=500)
    policy_ref: str = Field(min_length=3, max_length=500)
    scope_ref: str = Field(min_length=3, max_length=500)
    consumer_ref: str = Field(min_length=3, max_length=500)
    query_text: str = Field(min_length=3, max_length=8000)
    mode: QueryMode
    requested_fields: list[str] = Field(min_length=1)
    include_provenance: Literal[True] = True
    include_epistemic_state: Literal[True] = True
    include_validation_state: Literal[True] = True
    include_source_contract: Literal[True] = True
    requested_at: str = Field(min_length=10, max_length=80)
    query_is_not_truth_instruction: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_query(self):
        _unique(self.requested_fields, "requested_fields")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class QueryPlanStep(BaseModel):
    step_id: str = Field(min_length=3, max_length=500)
    query_ref: str = Field(min_length=3, max_length=500)
    ordinal: int = Field(ge=1)
    capability_ref: str = Field(min_length=3, max_length=500)
    target_kind: QueryTargetKind
    operation: str = Field(min_length=3, max_length=500)
    dependency_step_refs: list[str] = Field(default_factory=list)
    output_contract: str = Field(min_length=3, max_length=500)
    allowed_epistemic_states: list[EpistemicState] = Field(min_length=1)
    may_promote_epistemic_state: Literal[False] = False
    may_mutate_governed_graphs: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_step(self):
        _unique(self.dependency_step_refs, "dependency_step_refs")
        _unique([x.value for x in self.allowed_epistemic_states], "allowed_epistemic_states")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedQueryPlan(BaseModel):
    plan_id: str = Field(min_length=3, max_length=500)
    query_ref: str = Field(min_length=3, max_length=500)
    policy_ref: str = Field(min_length=3, max_length=500)
    step_refs: list[str] = Field(min_length=1)
    selected_capability_refs: list[str] = Field(min_length=1)
    deterministic_plan_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    preserves_contract_identity: Literal[True] = True
    preserves_epistemic_state: Literal[True] = True
    preserves_provenance: Literal[True] = True
    plan_is_not_truth_assessment: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_plan(self):
        _unique(self.step_refs, "step_refs")
        _unique(self.selected_capability_refs, "selected_capability_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class QueryProvenanceReference(BaseModel):
    provenance_ref_id: str = Field(min_length=3, max_length=500)
    source_contract: str = Field(min_length=3, max_length=500)
    source_object_ref: str = Field(min_length=3, max_length=1000)
    source_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_kind: str = Field(min_length=3, max_length=500)
    provenance_is_not_truth_certification: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedQueryResultItem(BaseModel):
    result_id: str = Field(min_length=3, max_length=500)
    query_ref: str = Field(min_length=3, max_length=500)
    plan_step_ref: str = Field(min_length=3, max_length=500)
    source_capability_ref: str = Field(min_length=3, max_length=500)
    target_kind: QueryTargetKind
    source_contract: str = Field(min_length=3, max_length=500)
    source_object_ref: str = Field(min_length=3, max_length=1000)
    title: str = Field(min_length=1, max_length=1000)
    summary: str = Field(min_length=1, max_length=8000)
    epistemic_state: EpistemicState
    validation_state: ResultValidationState
    provenance_refs: list[str] = Field(min_length=1)
    retrieval_score: float = Field(ge=0.0, le=1.0)
    retrieval_score_is_relevance_only: Literal[True] = True
    retrieval_score_is_not_evidence_strength: Literal[True] = True
    retrieval_score_is_not_probability_of_truth: Literal[True] = True
    result_does_not_promote_source_state: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_result(self):
        _unique(self.provenance_refs, "provenance_refs")
        if self.epistemic_state == EpistemicState.remote_reference and self.validation_state != ResultValidationState.local_validation_required:
            raise ValueError("remote references require local-validation-required state")
        if self.epistemic_state in {EpistemicState.candidate, EpistemicState.hypothesis} and self.validation_state == ResultValidationState.governed_reference:
            raise ValueError("candidate/hypothesis result may not be presented as governed-reference validation")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedQueryResultSet(BaseModel):
    result_set_id: str = Field(min_length=3, max_length=500)
    query_ref: str = Field(min_length=3, max_length=500)
    plan_ref: str = Field(min_length=3, max_length=500)
    result_refs: list[str] = Field(min_length=1)
    returned_results: int = Field(ge=1)
    result_limit: int = Field(ge=1)
    disposition: QueryExecutionDisposition
    qualification_notes: list[str] = Field(default_factory=list)
    result_set_is_not_truth_verdict: Literal[True] = True
    query_completeness_is_not_evidence_completeness: Literal[True] = True
    absence_from_results_is_not_nonexistence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_result_set(self):
        _unique(self.result_refs, "result_refs")
        if self.returned_results != len(self.result_refs):
            raise ValueError("returned_results must equal number of result_refs")
        if self.returned_results > self.result_limit:
            raise ValueError("returned_results exceeds result_limit")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedQueryExecutionTrace(BaseModel):
    trace_id: str = Field(min_length=3, max_length=500)
    query_ref: str = Field(min_length=3, max_length=500)
    plan_ref: str = Field(min_length=3, max_length=500)
    step_refs: list[str] = Field(min_length=1)
    result_set_ref: str = Field(min_length=3, max_length=500)
    executed_at: str = Field(min_length=10, max_length=80)
    warnings: list[str] = Field(default_factory=list)
    final_disposition: QueryExecutionDisposition
    deterministic_trace_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    trace_preserves_epistemic_state: Literal[True] = True
    trace_preserves_provenance: Literal[True] = True
    trace_is_not_truth_assessment: Literal[True] = True
    graph_mutation_performed: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_trace(self):
        _unique(self.step_refs, "step_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedQuerySnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    query_ref: str = Field(min_length=3, max_length=500)
    plan_ref: str = Field(min_length=3, max_length=500)
    result_set_ref: str = Field(min_length=3, max_length=500)
    trace_ref: str = Field(min_length=3, max_length=500)
    as_of: str = Field(min_length=10, max_length=80)
    immutable: Literal[True] = True
    later_source_state_may_supersede_snapshot: Literal[True] = True
    snapshot_is_not_truth_certification: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedEntityEvidenceQueryBundle(BaseModel):
    release: Literal["3.92.0"] = "3.92.0"
    contract: Literal["sc.core.unified-entity-evidence-query-api.v1"] = CONTRACT_VERSION
    negotiation_contract: Literal["sc.core.unified-runtime-policy-capability-negotiation.v1"] = V391_CONTRACT
    policies: list[UnifiedQueryPolicy] = Field(min_length=1)
    scopes: list[UnifiedQueryScope] = Field(min_length=1)
    queries: list[UnifiedEntityEvidenceQuery] = Field(min_length=1)
    plan_steps: list[QueryPlanStep] = Field(min_length=1)
    plans: list[UnifiedQueryPlan] = Field(min_length=1)
    provenance_refs: list[QueryProvenanceReference] = Field(min_length=1)
    results: list[UnifiedQueryResultItem] = Field(min_length=1)
    result_sets: list[UnifiedQueryResultSet] = Field(min_length=1)
    traces: list[UnifiedQueryExecutionTrace] = Field(min_length=1)
    snapshots: list[UnifiedQuerySnapshot] = Field(min_length=1)
    identity_graph_mutation_performed: Literal[False] = False
    relationship_graph_mutation_performed: Literal[False] = False
    evidence_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        groups = {
            "policy": [x.policy_id for x in self.policies],
            "scope": [x.scope_id for x in self.scopes],
            "query": [x.query_id for x in self.queries],
            "step": [x.step_id for x in self.plan_steps],
            "plan": [x.plan_id for x in self.plans],
            "provenance": [x.provenance_ref_id for x in self.provenance_refs],
            "result": [x.result_id for x in self.results],
            "result_set": [x.result_set_id for x in self.result_sets],
            "trace": [x.trace_id for x in self.traces],
            "snapshot": [x.snapshot_id for x in self.snapshots],
        }
        for label, vals in groups.items():
            _unique(vals, f"{label} ids")
        ids={k:set(v) for k,v in groups.items()}
        upstream=reference_unified_runtime_policy_capability_negotiation_bundle()
        capability_by_id={x.capability_id:x for x in upstream.capabilities}
        consumer_ids={x.consumer_id for x in upstream.consumers}
        policy_by_id={x.policy_id:x for x in self.policies}
        scope_by_id={x.scope_id:x for x in self.scopes}
        query_by_id={x.query_id:x for x in self.queries}
        step_by_id={x.step_id:x for x in self.plan_steps}
        plan_by_id={x.plan_id:x for x in self.plans}
        result_by_id={x.result_id:x for x in self.results}
        rs_by_id={x.result_set_id:x for x in self.result_sets}
        trace_by_id={x.trace_id:x for x in self.traces}
        for scope in self.scopes:
            if not set(scope.capability_refs) <= set(capability_by_id):
                raise ValueError("query scope capability reference unresolved")
        for q in self.queries:
            if q.policy_ref not in ids["policy"] or q.scope_ref not in ids["scope"] or q.consumer_ref not in consumer_ids:
                raise ValueError("query reference unresolved")
        seen_ordinals: dict[str,set[int]]={}
        for step in self.plan_steps:
            if step.query_ref not in ids["query"] or step.capability_ref not in capability_by_id:
                raise ValueError("query plan step reference unresolved")
            cap=capability_by_id[step.capability_ref]
            if step.output_contract != cap.contract:
                raise ValueError("query plan step output contract must match capability contract")
            if step.capability_ref not in scope_by_id[query_by_id[step.query_ref].scope_ref].capability_refs:
                raise ValueError("query plan step capability outside query scope")
            if not set(step.allowed_epistemic_states) <= set(scope_by_id[query_by_id[step.query_ref].scope_ref].allowed_epistemic_states):
                raise ValueError("query plan step epistemic states outside query scope")
            if not set(step.dependency_step_refs) <= ids["step"]:
                raise ValueError("query plan dependency unresolved")
            ords=seen_ordinals.setdefault(step.query_ref,set())
            if step.ordinal in ords: raise ValueError("query plan ordinals must be unique per query")
            ords.add(step.ordinal)
        for plan in self.plans:
            if plan.query_ref not in ids["query"] or plan.policy_ref not in ids["policy"] or not set(plan.step_refs) <= ids["step"]:
                raise ValueError("query plan reference unresolved")
            if any(step_by_id[x].query_ref != plan.query_ref for x in plan.step_refs):
                raise ValueError("query plan contains step from another query")
            selected={step_by_id[x].capability_ref for x in plan.step_refs}
            if set(plan.selected_capability_refs) != selected:
                raise ValueError("selected_capability_refs must equal capabilities used by plan steps")
        for result in self.results:
            if result.query_ref not in ids["query"] or result.plan_step_ref not in ids["step"] or result.source_capability_ref not in capability_by_id:
                raise ValueError("query result reference unresolved")
            step=step_by_id[result.plan_step_ref]
            if step.query_ref != result.query_ref or step.capability_ref != result.source_capability_ref:
                raise ValueError("query result does not match plan step")
            if result.source_contract != step.output_contract:
                raise ValueError("query result source contract mismatch")
            if result.target_kind != step.target_kind:
                raise ValueError("query result target kind mismatch")
            if result.epistemic_state not in step.allowed_epistemic_states:
                raise ValueError("query result epistemic state not allowed by plan step")
            if not set(result.provenance_refs) <= ids["provenance"]:
                raise ValueError("query result provenance reference unresolved")
            scope=scope_by_id[query_by_id[result.query_ref].scope_ref]
            if result.epistemic_state == EpistemicState.remote_reference and not scope.include_remote_references:
                raise ValueError("remote reference returned outside remote-enabled query scope")
        for rs in self.result_sets:
            if rs.query_ref not in ids["query"] or rs.plan_ref not in ids["plan"] or not set(rs.result_refs) <= ids["result"]:
                raise ValueError("result set reference unresolved")
            if plan_by_id[rs.plan_ref].query_ref != rs.query_ref or any(result_by_id[x].query_ref != rs.query_ref for x in rs.result_refs):
                raise ValueError("result set mixes query identities")
            if rs.result_limit != scope_by_id[query_by_id[rs.query_ref].scope_ref].max_results:
                raise ValueError("result set limit must equal query scope max_results")
        for tr in self.traces:
            if tr.query_ref not in ids["query"] or tr.plan_ref not in ids["plan"] or tr.result_set_ref not in ids["result_set"] or not set(tr.step_refs) <= ids["step"]:
                raise ValueError("query trace reference unresolved")
            if plan_by_id[tr.plan_ref].query_ref != tr.query_ref or rs_by_id[tr.result_set_ref].query_ref != tr.query_ref:
                raise ValueError("query trace mixes query identities")
        for sn in self.snapshots:
            if sn.query_ref not in ids["query"] or sn.plan_ref not in ids["plan"] or sn.result_set_ref not in ids["result_set"] or sn.trace_ref not in ids["trace"]:
                raise ValueError("query snapshot reference unresolved")
            if any(x != sn.query_ref for x in [plan_by_id[sn.plan_ref].query_ref,rs_by_id[sn.result_set_ref].query_ref,trace_by_id[sn.trace_ref].query_ref]):
                raise ValueError("query snapshot mixes query identities")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


_TARGETS = [
    ("runtime-capability:3770", QueryTargetKind.entity, EpistemicState.governed_record, ResultValidationState.governed_reference, "Canonical entity record", "Governed entity identity record with aliases and source-specific identity assertions."),
    ("runtime-capability:3780", QueryTargetKind.temporal_identity, EpistemicState.qualified, ResultValidationState.review_required, "Temporal identity history", "Historical names, identifiers, roles, and temporal qualifications remain explicitly time-bounded."),
    ("runtime-capability:3790", QueryTargetKind.record_linkage, EpistemicState.candidate, ResultValidationState.review_required, "Probabilistic linkage candidate", "High-probability record linkage candidate remains a candidate pending identity-resolution review."),
    ("runtime-capability:3800", QueryTargetKind.source_reconciliation, EpistemicState.unresolved, ResultValidationState.unresolved, "Cross-source reconciliation conflict", "Source-specific identity observations remain reconciled without erasing an unresolved source/temporal disagreement."),
    ("runtime-capability:3810", QueryTargetKind.documentary_source, EpistemicState.source_asserted, ResultValidationState.governed_reference, "Documentary source anchor", "Source record preserves acquisition, content hash, derivative lineage, redaction, and citation anchors."),
    ("runtime-capability:3820", QueryTargetKind.relationship, EpistemicState.hypothesis, ResultValidationState.review_required, "Connection hypothesis", "Candidate relationship is retained as a hypothesis with supporting and contradicting evidence positions."),
    ("runtime-capability:3830", QueryTargetKind.network_structure, EpistemicState.analytical, ResultValidationState.analytical_only, "Network structure analysis", "Community, centrality, motif, and bridge outputs remain descriptive analytical results."),
    ("runtime-capability:3840", QueryTargetKind.connection_path, EpistemicState.qualified, ResultValidationState.analytical_only, "Explainable connection path", "Connection path preserves edge epistemic state, documentary anchors, contradictions, and alternative-path qualifications."),
    ("runtime-capability:3840", QueryTargetKind.evidence_chain, EpistemicState.qualified, ResultValidationState.review_required, "Evidence chain", "Evidence chain preserves source-independence groups, contradictions, and provenance without becoming a truth verdict."),
    ("runtime-capability:3850", QueryTargetKind.multi_hop_reasoning, EpistemicState.qualified, ResultValidationState.analytical_only, "Multi-hop reasoning trace", "Reasoning trace records branch structure, stopping rules, contradiction propagation, and qualified inference state."),
    ("runtime-capability:3860", QueryTargetKind.contradiction, EpistemicState.unresolved, ResultValidationState.unresolved, "Contradiction resolution state", "Identity conflict remains partially resolved and preserves competing assertions and supersession lineage."),
    ("runtime-capability:3870", QueryTargetKind.timeline, EpistemicState.qualified, ResultValidationState.review_required, "Entity-centric timeline", "Timeline preserves event assertion state, temporal uncertainty, participation roles, and contradiction context."),
    ("runtime-capability:3880", QueryTargetKind.investigation_package, EpistemicState.governed_record, ResultValidationState.governed_reference, "Reproducible investigation package", "Content-addressed package preserves upstream epistemic states, environment, policy, and reproduction plan."),
    ("runtime-capability:3890", QueryTargetKind.federation_reference, EpistemicState.remote_reference, ResultValidationState.local_validation_required, "Federated evidence reference", "Signed remote object reference remains remote and requires local validation before any promotion."),
    ("runtime-capability:3900", QueryTargetKind.runtime_metadata, EpistemicState.runtime_metadata, ResultValidationState.metadata_only, "Unified runtime trace", "Unified runtime execution metadata preserves contract identities, handoffs, stopping rules, and final qualified disposition."),
]


@lru_cache(maxsize=1)
def reference_unified_entity_evidence_query_bundle() -> UnifiedEntityEvidenceQueryBundle:
    upstream=reference_unified_runtime_policy_capability_negotiation_bundle()
    caps={x.capability_id:x for x in upstream.capabilities}
    policy=UnifiedQueryPolicy(policy_id="unified-query-policy:default:v1")
    scope=UnifiedQueryScope(
        scope_id="query-scope:entity-evidence:synthetic:v1",
        target_kinds=[x[1] for x in _TARGETS],
        capability_refs=sorted({x[0] for x in _TARGETS}),
        allowed_epistemic_states=list(EpistemicState),
        include_remote_references=True,
        include_contradictions=True,
        max_results=50,
        valid_time_start="1985-01-01T00:00:00Z",
        valid_time_end="2026-09-30T23:59:59Z",
    )
    q=UnifiedEntityEvidenceQuery(
        query_id="query:synthetic:entity-evidence:v1",
        policy_ref=policy.policy_id,
        scope_ref=scope.scope_id,
        consumer_ref="consumer:research-librarian",
        query_text="Show the entity's identity history, documentary sources, relationship hypotheses, network/path context, contradictions, timeline, reproducible package, and federated references while preserving uncertainty and provenance.",
        mode=QueryMode.exploratory,
        requested_fields=["source-contract","source-object-ref","epistemic-state","validation-state","provenance","summary"],
        requested_at="2026-09-30T23:58:00Z",
    )
    steps=[]; provenance=[]; results=[]; previous=None
    for i,(capref,target,state,validation,title,summary) in enumerate(_TARGETS,1):
        cap=caps[capref]
        sid=f"query-step:{i:02d}"
        steps.append(QueryPlanStep(
            step_id=sid, query_ref=q.query_id, ordinal=i, capability_ref=capref,
            target_kind=target, operation=f"retrieve-{target.value}",
            dependency_step_refs=[] if previous is None else [previous],
            output_contract=cap.contract, allowed_epistemic_states=[state],
        ))
        pref=f"query-provenance:{i:02d}"
        objref=f"reference-object:{target.value}:synthetic:v1"
        provenance.append(QueryProvenanceReference(
            provenance_ref_id=pref, source_contract=cap.contract, source_object_ref=objref,
            source_fingerprint_sha256=canonical_sha256({"contract":cap.contract,"object_ref":objref,"target":target.value}),
            source_kind=target.value,
        ))
        results.append(UnifiedQueryResultItem(
            result_id=f"query-result:{i:02d}", query_ref=q.query_id, plan_step_ref=sid,
            source_capability_ref=capref, target_kind=target, source_contract=cap.contract,
            source_object_ref=objref, title=title, summary=summary, epistemic_state=state,
            validation_state=validation, provenance_refs=[pref], retrieval_score=max(0.50, 0.99-(i-1)*0.025),
        ))
        previous=sid
    seed={"query":q.query_id,"steps":[x.step_id for x in steps],"caps":sorted({x.capability_ref for x in steps})}
    plan=UnifiedQueryPlan(
        plan_id="query-plan:synthetic:v1", query_ref=q.query_id, policy_ref=policy.policy_id,
        step_refs=[x.step_id for x in steps], selected_capability_refs=sorted({x.capability_ref for x in steps}),
        deterministic_plan_fingerprint_sha256=canonical_sha256(seed),
    )
    result_set=UnifiedQueryResultSet(
        result_set_id="query-result-set:synthetic:v1", query_ref=q.query_id, plan_ref=plan.plan_id,
        result_refs=[x.result_id for x in results], returned_results=len(results), result_limit=scope.max_results,
        disposition=QueryExecutionDisposition.complete_with_qualifications,
        qualification_notes=[
            "Candidate, hypothesis, analytical, unresolved, and remote-reference states are preserved.",
            "Retrieval scores rank relevance only and are not evidence strength or probability of truth.",
            "Remote federation references remain subject to local validation.",
        ],
    )
    trace_seed={"query":q.query_id,"plan":plan.plan_id,"steps":plan.step_refs,"result_set":result_set.result_set_id,"at":"2026-09-30T23:58:01Z"}
    trace=UnifiedQueryExecutionTrace(
        trace_id="query-trace:synthetic:v1", query_ref=q.query_id, plan_ref=plan.plan_id,
        step_refs=plan.step_refs, result_set_ref=result_set.result_set_id, executed_at="2026-09-30T23:58:01Z",
        warnings=["Federated evidence capability is degraded and returned reference-only output pending local validation."],
        final_disposition=QueryExecutionDisposition.complete_with_qualifications,
        deterministic_trace_fingerprint_sha256=canonical_sha256(trace_seed),
    )
    snapshot=UnifiedQuerySnapshot(
        snapshot_id="query-snapshot:synthetic:v1", query_ref=q.query_id, plan_ref=plan.plan_id,
        result_set_ref=result_set.result_set_id, trace_ref=trace.trace_id, as_of="2026-09-30T23:58:01Z",
    )
    return UnifiedEntityEvidenceQueryBundle(
        policies=[policy], scopes=[scope], queries=[q], plan_steps=steps, plans=[plan],
        provenance_refs=provenance, results=results, result_sets=[result_set], traces=[trace], snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    b=reference_unified_entity_evidence_query_bundle()
    return {
        "ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"negotiation_contract":V391_CONTRACT,
        "principles":{
            "single_governed_query_surface":True,
            "capability_negotiation_required":True,
            "source_contract_identity_preserved":True,
            "epistemic_state_preserved":True,
            "provenance_preserved":True,
            "validation_state_preserved":True,
            "contradictions_preserved":True,
            "remote_references_remain_remote":True,
            "consumer_scope_enforced":True,
            "retrieval_scores_are_relevance_only":True,
            "query_plans_are_reproducible":True,
            "result_sets_are_explicitly_qualified":True,
        },
        "boundaries":{
            "query_flattens_epistemic_states":False,
            "query_promotes_candidate_to_fact":False,
            "query_promotes_hypothesis_to_evidence":False,
            "query_promotes_remote_reference_to_local_evidence":False,
            "retrieval_score_is_evidence_strength":False,
            "retrieval_score_is_probability_of_truth":False,
            "absence_from_results_proves_nonexistence":False,
            "query_completeness_is_evidence_completeness":False,
            "query_result_is_truth_verdict":False,
            "query_bypasses_local_validation":False,
            "identity_graph_mutation_performed":False,
            "relationship_graph_mutation_performed":False,
            "evidence_graph_mutation_performed":False,
        },
        "reference":{
            "policies":len(b.policies),"scopes":len(b.scopes),"queries":len(b.queries),
            "plan_steps":len(b.plan_steps),"plans":len(b.plans),"provenance_refs":len(b.provenance_refs),
            "results":len(b.results),"result_sets":len(b.result_sets),"traces":len(b.traces),"snapshots":len(b.snapshots),
            "final_disposition":b.traces[0].final_disposition.value,
            "bundle_fingerprint_sha256":b.fingerprint(),
        },
        "database_migration":"none",
    }
