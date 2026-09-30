from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .explainable_connection_paths_evidence_chains import (
    ExplainableConnectionPathsEvidenceChainsBundle,
    reference_explainable_connection_paths_evidence_chains_bundle,
)

CORE_RELEASE = "3.85.0"
CONTRACT_VERSION = "sc.core.multi-hop-research-investigation-graph-reasoning.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class ReasoningNodeType(str, Enum):
    entity = "entity"
    connection_path = "connection-path"
    evidence_chain = "evidence-chain"
    evidence_position = "evidence-position"
    documentary_interpretation = "documentary-interpretation"
    document_segment = "document-segment"
    connection_candidate = "connection-candidate"
    connection_hypothesis = "connection-hypothesis"
    contradiction_marker = "contradiction-marker"
    source = "source"


class ReasoningHopRelation(str, Enum):
    starts_from = "starts-from"
    explained_by = "explained-by"
    supported_by = "supported-by"
    contextualized_by = "contextualized-by"
    references = "references"
    mentions = "mentions"
    proposed_by = "proposed-by"
    qualifies = "qualifies"
    contradicts = "contradicts"
    alternative_to = "alternative-to"


class ReasoningSupportState(str, Enum):
    supported = "supported"
    qualified = "qualified"
    contradicted = "contradicted"
    unresolved = "unresolved"
    mixed = "mixed"


class ReasoningStopReason(str, Enum):
    target_reached = "target-reached"
    max_hops_reached = "max-hops-reached"
    provenance_gap = "provenance-gap"
    unresolved_contradiction = "unresolved-contradiction"
    unvalidated_hypothesis = "unvalidated-hypothesis"
    policy_boundary = "policy-boundary"
    manual_stop = "manual-stop"


class MultiHopReasoningPolicy(BaseModel):
    reasoning_policy_id: str = Field(min_length=2, max_length=500)
    max_hops: int = Field(ge=1, le=24)
    require_provenance_each_hop: Literal[True] = True
    require_epistemic_state_preservation: Literal[True] = True
    preserve_source_independence_groups: Literal[True] = True
    preserve_contradictions: Literal[True] = True
    preserve_alternative_branches: Literal[True] = True
    require_explicit_stopping_decision: Literal[True] = True
    allow_hypothesis_traversal: bool = True
    allow_candidate_traversal: bool = True
    hop_count_can_establish_truth: Literal[False] = False
    chain_completion_can_establish_endpoint_relationship: Literal[False] = False
    analytical_confidence_can_establish_claim_truth: Literal[False] = False
    repeated_sources_can_create_independence: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MultiHopReasoningQuery(BaseModel):
    reasoning_query_id: str = Field(min_length=2, max_length=500)
    reasoning_policy_ref: str = Field(min_length=2, max_length=500)
    start_refs: list[str] = Field(min_length=1)
    target_refs: list[str] = Field(min_length=1)
    question: str = Field(min_length=1, max_length=12000)
    allowed_node_types: list[ReasoningNodeType] = Field(min_length=1)
    max_hops: int = Field(ge=1, le=24)
    created_at: str = Field(min_length=10, max_length=80)
    query_is_analytical_not_factual_assertion: Literal[True] = True
    target_reachability_is_not_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_query(self):
        _unique(self.start_refs, "start_refs")
        _unique(self.target_refs, "target_refs")
        _unique([x.value for x in self.allowed_node_types], "allowed_node_types")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReasoningHop(BaseModel):
    reasoning_hop_id: str = Field(min_length=2, max_length=500)
    reasoning_query_ref: str = Field(min_length=2, max_length=500)
    branch_ref: str = Field(min_length=2, max_length=500)
    sequence_index: int = Field(ge=0)
    from_ref: str = Field(min_length=2, max_length=1000)
    from_type: ReasoningNodeType
    to_ref: str = Field(min_length=2, max_length=1000)
    to_type: ReasoningNodeType
    relation: ReasoningHopRelation
    upstream_object_refs: list[str] = Field(min_length=1)
    provenance_refs: list[str] = Field(min_length=1)
    source_independence_groups: list[str] = Field(default_factory=list)
    epistemic_state: str = Field(min_length=1, max_length=200)
    uncertainty: float = Field(ge=0.0, le=1.0)
    uncertainty_semantics: str = Field(min_length=1, max_length=2000)
    explanation: str = Field(min_length=1, max_length=8000)
    hop_is_not_relationship_fact: Literal[True] = True
    hop_is_not_causal_claim: Literal[True] = True
    uncertainty_is_not_probability_of_truth: Literal[True] = True
    traversal_does_not_promote_upstream_object: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_hop(self):
        if self.from_ref == self.to_ref:
            raise ValueError("reasoning hop requires distinct endpoints")
        _unique(self.upstream_object_refs, "upstream_object_refs")
        _unique(self.provenance_refs, "provenance_refs")
        _unique(self.source_independence_groups, "source_independence_groups")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReasoningInferenceStep(BaseModel):
    reasoning_inference_step_id: str = Field(min_length=2, max_length=500)
    reasoning_query_ref: str = Field(min_length=2, max_length=500)
    branch_ref: str = Field(min_length=2, max_length=500)
    premise_hop_refs: list[str] = Field(min_length=1)
    premise_object_refs: list[str] = Field(min_length=1)
    conclusion_statement: str = Field(min_length=1, max_length=12000)
    support_state: ReasoningSupportState
    analytical_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    analytical_confidence_semantics: str | None = Field(default=None, max_length=2000)
    contradiction_marker_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(min_length=1)
    conclusion_is_hypothesis_not_fact: Literal[True] = True
    confidence_is_not_probability_of_truth: Literal[True] = True
    inference_does_not_create_graph_edge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_inference(self):
        for values, label in (
            (self.premise_hop_refs, "premise_hop_refs"),
            (self.premise_object_refs, "premise_object_refs"),
            (self.contradiction_marker_refs, "contradiction_marker_refs"),
            (self.provenance_refs, "provenance_refs"),
        ):
            _unique(values, label)
        if self.analytical_confidence is not None and not self.analytical_confidence_semantics:
            raise ValueError("analytical confidence requires explicit semantics")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReasoningContradictionPropagation(BaseModel):
    contradiction_propagation_id: str = Field(min_length=2, max_length=500)
    source_contradiction_marker_ref: str = Field(min_length=2, max_length=500)
    affected_branch_refs: list[str] = Field(min_length=1)
    affected_hop_refs: list[str] = Field(min_length=1)
    affected_inference_refs: list[str] = Field(default_factory=list)
    propagated_state: ReasoningSupportState
    explanation: str = Field(min_length=1, max_length=8000)
    provenance_refs: list[str] = Field(min_length=1)
    contradiction_must_remain_visible: Literal[True] = True
    contradiction_does_not_auto_invalidate_reasoning: Literal[True] = True
    contradiction_does_not_auto_prove_opposite: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_propagation(self):
        for values, label in (
            (self.affected_branch_refs, "affected_branch_refs"),
            (self.affected_hop_refs, "affected_hop_refs"),
            (self.affected_inference_refs, "affected_inference_refs"),
            (self.provenance_refs, "provenance_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SourceIndependenceAssessment(BaseModel):
    source_independence_assessment_id: str = Field(min_length=2, max_length=500)
    reasoning_query_ref: str = Field(min_length=2, max_length=500)
    branch_refs: list[str] = Field(min_length=1)
    independence_groups: list[str] = Field(min_length=1)
    shared_provenance_refs: list[str] = Field(default_factory=list)
    independent_group_count: int = Field(ge=1)
    explanation: str = Field(min_length=1, max_length=8000)
    path_count_is_not_independence_count: Literal[True] = True
    repeated_source_is_not_independent_corroboration: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_assessment(self):
        _unique(self.branch_refs, "branch_refs")
        _unique(self.independence_groups, "independence_groups")
        _unique(self.shared_provenance_refs, "shared_provenance_refs")
        if self.independent_group_count != len(self.independence_groups):
            raise ValueError("independent_group_count must equal unique independence groups")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReasoningBranch(BaseModel):
    reasoning_branch_id: str = Field(min_length=2, max_length=500)
    reasoning_query_ref: str = Field(min_length=2, max_length=500)
    hop_refs: list[str] = Field(min_length=1)
    endpoint_ref: str = Field(min_length=2, max_length=1000)
    endpoint_type: ReasoningNodeType
    support_state: ReasoningSupportState
    contradiction_marker_refs: list[str] = Field(default_factory=list)
    source_independence_groups: list[str] = Field(min_length=1)
    branch_score: float | None = None
    branch_score_semantics: str | None = Field(default=None, max_length=2000)
    explanation: str = Field(min_length=1, max_length=12000)
    completed: bool
    branch_is_explanation_not_proof: Literal[True] = True
    endpoint_reached_does_not_establish_relationship: Literal[True] = True
    branch_score_is_not_evidence_strength: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_branch(self):
        _unique(self.hop_refs, "hop_refs")
        _unique(self.contradiction_marker_refs, "contradiction_marker_refs")
        _unique(self.source_independence_groups, "source_independence_groups")
        if self.branch_score is not None and not self.branch_score_semantics:
            raise ValueError("branch score requires explicit semantics")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReasoningStoppingDecision(BaseModel):
    reasoning_stopping_decision_id: str = Field(min_length=2, max_length=500)
    reasoning_query_ref: str = Field(min_length=2, max_length=500)
    branch_ref: str = Field(min_length=2, max_length=500)
    stop_reason: ReasoningStopReason
    hop_count: int = Field(ge=0)
    reached_target: bool
    unresolved_issue_refs: list[str] = Field(default_factory=list)
    explanation: str = Field(min_length=1, max_length=8000)
    provenance_refs: list[str] = Field(min_length=1)
    stopping_decision_is_not_truth_verdict: Literal[True] = True
    target_reached_is_not_relationship_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_stop(self):
        _unique(self.unresolved_issue_refs, "unresolved_issue_refs")
        _unique(self.provenance_refs, "provenance_refs")
        if self.stop_reason == ReasoningStopReason.target_reached and not self.reached_target:
            raise ValueError("target-reached stop reason requires reached_target=true")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MultiHopReasoningTrace(BaseModel):
    reasoning_trace_id: str = Field(min_length=2, max_length=500)
    reasoning_query_ref: str = Field(min_length=2, max_length=500)
    branch_refs: list[str] = Field(min_length=1)
    inference_step_refs: list[str] = Field(min_length=1)
    contradiction_propagation_refs: list[str] = Field(default_factory=list)
    source_independence_assessment_refs: list[str] = Field(min_length=1)
    stopping_decision_refs: list[str] = Field(min_length=1)
    created_at: str = Field(min_length=10, max_length=80)
    immutable_trace: Literal[True] = True
    trace_is_reproducible_analysis_not_proof: Literal[True] = True
    trace_does_not_promote_candidates_or_hypotheses: Literal[True] = True
    trace_does_not_mutate_graphs: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_trace(self):
        for field in (
            "branch_refs",
            "inference_step_refs",
            "contradiction_propagation_refs",
            "source_independence_assessment_refs",
            "stopping_decision_refs",
        ):
            _unique(getattr(self, field), field)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MultiHopReasoningSnapshot(BaseModel):
    reasoning_snapshot_id: str = Field(min_length=2, max_length=500)
    connection_path_evidence_snapshot_ref: str = Field(min_length=2, max_length=500)
    policy_refs: list[str] = Field(min_length=1)
    query_refs: list[str] = Field(min_length=1)
    trace_refs: list[str] = Field(min_length=1)
    created_at: str = Field(min_length=10, max_length=80)
    immutable_snapshot: Literal[True] = True
    snapshot_preserves_upstream_epistemic_states: Literal[True] = True
    snapshot_is_not_endpoint_truth_verdict: Literal[True] = True
    snapshot_does_not_mutate_graphs: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        _unique(self.policy_refs, "policy_refs")
        _unique(self.query_refs, "query_refs")
        _unique(self.trace_refs, "trace_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MultiHopResearchInvestigationGraphReasoningBundle(BaseModel):
    explainable_connection_paths_evidence_chains_bundle: ExplainableConnectionPathsEvidenceChainsBundle
    policies: list[MultiHopReasoningPolicy] = Field(min_length=1)
    queries: list[MultiHopReasoningQuery] = Field(min_length=1)
    hops: list[ReasoningHop] = Field(min_length=1)
    branches: list[ReasoningBranch] = Field(min_length=1)
    inference_steps: list[ReasoningInferenceStep] = Field(min_length=1)
    contradiction_propagations: list[ReasoningContradictionPropagation] = Field(default_factory=list)
    source_independence_assessments: list[SourceIndependenceAssessment] = Field(min_length=1)
    stopping_decisions: list[ReasoningStoppingDecision] = Field(min_length=1)
    traces: list[MultiHopReasoningTrace] = Field(min_length=1)
    snapshots: list[MultiHopReasoningSnapshot] = Field(min_length=1)
    multi_hop_reachability_is_not_relationship_truth: Literal[True] = True
    reasoning_chain_is_not_proof: Literal[True] = True
    analytical_confidence_is_not_probability_of_truth: Literal[True] = True
    repeated_paths_are_not_independent_corroboration: Literal[True] = True
    contradiction_propagation_is_non_dispositive: Literal[True] = True
    algorithmic_reasoning_is_not_investigator_conclusion: Literal[True] = True
    relationship_graph_mutation_performed: Literal[False] = False
    evidence_graph_mutation_performed: Literal[False] = False
    identity_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        upstream = self.explainable_connection_paths_evidence_chains_bundle
        rel = upstream.network_structure_community_motif_bundle.relationship_discovery_hypothesis_bundle
        documentary = rel.public_record_documentary_source_bundle
        base = documentary.cross_source_entity_reconciliation_bundle.probabilistic_record_linkage_bundle.temporal_identity_bundle.entity_resolution_identity_graph_bundle

        def ids(items, attr, label):
            vals = [getattr(x, attr) for x in items]
            _unique(vals, label)
            return set(vals)

        entity_ids = {x.entity_id for x in base.entities}
        path_ids = {x.connection_path_id for x in upstream.connection_paths}
        chain_ids = {x.evidence_chain_id for x in upstream.evidence_chains}
        evidence_position_ids = {x.evidence_position_id for x in rel.evidence_positions}
        interpretation_ids = {x.documentary_interpretation_id for x in documentary.evidence_interpretations}
        segment_ids = {x.document_segment_id for x in documentary.segments}
        candidate_ids = {x.connection_candidate_id for x in rel.connection_candidates}
        hypothesis_ids = {x.connection_hypothesis_id for x in rel.connection_hypotheses}
        contradiction_ids = {x.path_contradiction_marker_id for x in upstream.contradiction_markers}
        source_ids = {x.documentary_source_id for x in documentary.documentary_sources}
        path_snapshot_ids = {x.connection_path_evidence_snapshot_id for x in upstream.snapshots}

        resolvable_by_type = {
            ReasoningNodeType.entity: entity_ids,
            ReasoningNodeType.connection_path: path_ids,
            ReasoningNodeType.evidence_chain: chain_ids,
            ReasoningNodeType.evidence_position: evidence_position_ids,
            ReasoningNodeType.documentary_interpretation: interpretation_ids,
            ReasoningNodeType.document_segment: segment_ids,
            ReasoningNodeType.connection_candidate: candidate_ids,
            ReasoningNodeType.connection_hypothesis: hypothesis_ids,
            ReasoningNodeType.contradiction_marker: contradiction_ids,
            ReasoningNodeType.source: source_ids,
        }
        all_upstream_ids = set().union(*resolvable_by_type.values())

        policy_ids = ids(self.policies, "reasoning_policy_id", "reasoning_policy_ids")
        query_ids = ids(self.queries, "reasoning_query_id", "reasoning_query_ids")
        hop_ids = ids(self.hops, "reasoning_hop_id", "reasoning_hop_ids")
        branch_ids = ids(self.branches, "reasoning_branch_id", "reasoning_branch_ids")
        inference_ids = ids(self.inference_steps, "reasoning_inference_step_id", "reasoning_inference_step_ids")
        propagation_ids = ids(self.contradiction_propagations, "contradiction_propagation_id", "contradiction_propagation_ids")
        independence_ids = ids(self.source_independence_assessments, "source_independence_assessment_id", "source_independence_assessment_ids")
        stopping_ids = ids(self.stopping_decisions, "reasoning_stopping_decision_id", "reasoning_stopping_decision_ids")
        trace_ids = ids(self.traces, "reasoning_trace_id", "reasoning_trace_ids")
        ids(self.snapshots, "reasoning_snapshot_id", "reasoning_snapshot_ids")

        policy_by_id = {x.reasoning_policy_id: x for x in self.policies}
        query_by_id = {x.reasoning_query_id: x for x in self.queries}
        hop_by_id = {x.reasoning_hop_id: x for x in self.hops}
        branch_by_id = {x.reasoning_branch_id: x for x in self.branches}

        for query in self.queries:
            if query.reasoning_policy_ref not in policy_ids:
                raise ValueError("reasoning query policy ref must resolve")
            if not set(query.start_refs) <= all_upstream_ids or not set(query.target_refs) <= all_upstream_ids:
                raise ValueError("reasoning query start/target refs must resolve upstream")
            if query.max_hops > policy_by_id[query.reasoning_policy_ref].max_hops:
                raise ValueError("reasoning query max_hops cannot exceed policy max_hops")

        for hop in self.hops:
            if hop.reasoning_query_ref not in query_ids or hop.branch_ref not in branch_ids:
                raise ValueError("reasoning hop query/branch refs must resolve")
            if hop.from_ref not in resolvable_by_type[hop.from_type] or hop.to_ref not in resolvable_by_type[hop.to_type]:
                raise ValueError("reasoning hop endpoints must resolve for declared node types")
            if not set(hop.upstream_object_refs) <= all_upstream_ids:
                raise ValueError("reasoning hop upstream object refs must resolve")

        for branch in self.branches:
            if branch.reasoning_query_ref not in query_ids:
                raise ValueError("reasoning branch query ref must resolve")
            if not set(branch.hop_refs) <= hop_ids:
                raise ValueError("reasoning branch hop refs must resolve")
            if branch.endpoint_ref not in resolvable_by_type[branch.endpoint_type]:
                raise ValueError("reasoning branch endpoint must resolve")
            if not set(branch.contradiction_marker_refs) <= contradiction_ids:
                raise ValueError("reasoning branch contradiction refs must resolve")
            ordered = sorted((hop_by_id[x] for x in branch.hop_refs), key=lambda x: x.sequence_index)
            if [x.sequence_index for x in ordered] != list(range(len(ordered))):
                raise ValueError("reasoning branch hop indexes must be contiguous from zero")
            for left, right in zip(ordered, ordered[1:]):
                if left.to_ref != right.from_ref:
                    raise ValueError("reasoning branch hops must form a contiguous chain")
            if ordered[-1].to_ref != branch.endpoint_ref:
                raise ValueError("reasoning branch endpoint must match final hop")
            query = query_by_id[branch.reasoning_query_ref]
            if len(ordered) > query.max_hops:
                raise ValueError("reasoning branch exceeds query max_hops")

        for inference in self.inference_steps:
            if inference.reasoning_query_ref not in query_ids or inference.branch_ref not in branch_ids:
                raise ValueError("inference query/branch refs must resolve")
            if not set(inference.premise_hop_refs) <= hop_ids:
                raise ValueError("inference premise hop refs must resolve")
            if not set(inference.premise_object_refs) <= all_upstream_ids:
                raise ValueError("inference premise object refs must resolve")
            if not set(inference.contradiction_marker_refs) <= contradiction_ids:
                raise ValueError("inference contradiction marker refs must resolve")

        for propagation in self.contradiction_propagations:
            if propagation.source_contradiction_marker_ref not in contradiction_ids:
                raise ValueError("contradiction propagation source marker must resolve")
            if not set(propagation.affected_branch_refs) <= branch_ids:
                raise ValueError("contradiction propagation branch refs must resolve")
            if not set(propagation.affected_hop_refs) <= hop_ids:
                raise ValueError("contradiction propagation hop refs must resolve")
            if not set(propagation.affected_inference_refs) <= inference_ids:
                raise ValueError("contradiction propagation inference refs must resolve")

        for assessment in self.source_independence_assessments:
            if assessment.reasoning_query_ref not in query_ids or not set(assessment.branch_refs) <= branch_ids:
                raise ValueError("source independence assessment refs must resolve")

        for stop in self.stopping_decisions:
            if stop.reasoning_query_ref not in query_ids or stop.branch_ref not in branch_ids:
                raise ValueError("stopping decision refs must resolve")
            branch = branch_by_id[stop.branch_ref]
            if stop.hop_count != len(branch.hop_refs):
                raise ValueError("stopping decision hop count must equal branch hop count")
            if stop.reached_target and branch.endpoint_ref not in query_by_id[stop.reasoning_query_ref].target_refs:
                raise ValueError("reached-target stopping decision must end on a query target")

        for trace in self.traces:
            if trace.reasoning_query_ref not in query_ids:
                raise ValueError("reasoning trace query ref must resolve")
            if not set(trace.branch_refs) <= branch_ids:
                raise ValueError("reasoning trace branch refs must resolve")
            if not set(trace.inference_step_refs) <= inference_ids:
                raise ValueError("reasoning trace inference refs must resolve")
            if not set(trace.contradiction_propagation_refs) <= propagation_ids:
                raise ValueError("reasoning trace contradiction refs must resolve")
            if not set(trace.source_independence_assessment_refs) <= independence_ids:
                raise ValueError("reasoning trace independence refs must resolve")
            if not set(trace.stopping_decision_refs) <= stopping_ids:
                raise ValueError("reasoning trace stopping refs must resolve")

        for snapshot in self.snapshots:
            if snapshot.connection_path_evidence_snapshot_ref not in path_snapshot_ids:
                raise ValueError("reasoning snapshot upstream path snapshot ref must resolve")
            if not set(snapshot.policy_refs) <= policy_ids or not set(snapshot.query_refs) <= query_ids or not set(snapshot.trace_refs) <= trace_ids:
                raise ValueError("reasoning snapshot refs must resolve")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_multi_hop_research_investigation_graph_reasoning_bundle() -> MultiHopResearchInvestigationGraphReasoningBundle:
    upstream = reference_explainable_connection_paths_evidence_chains_bundle()
    rel = upstream.network_structure_community_motif_bundle.relationship_discovery_hypothesis_bundle
    documentary = rel.public_record_documentary_source_bundle
    base = documentary.cross_source_entity_reconciliation_bundle.probabilistic_record_linkage_bundle.temporal_identity_bundle.entity_resolution_identity_graph_bundle

    entity_a, entity_b = [x.entity_id for x in base.entities[:2]]
    primary_path, alternative_path = upstream.connection_paths[:2]
    chain = upstream.evidence_chains[0]
    contradiction = upstream.contradiction_markers[0]
    evidence_position_a, evidence_position_b = rel.evidence_positions[:2]
    interpretation_a, interpretation_b = documentary.evidence_interpretations[:2]
    hypothesis = rel.connection_hypotheses[0]
    candidate = rel.connection_candidates[0]
    upstream_snapshot = upstream.snapshots[0]

    policy = MultiHopReasoningPolicy(
        reasoning_policy_id="reasoning-policy:synthetic:bounded-investigation:v1",
        max_hops=6,
        metadata={"synthetic_reference": True},
    )
    query = MultiHopReasoningQuery(
        reasoning_query_id="reasoning-query:synthetic:entity-a-to-b:v1",
        reasoning_policy_ref=policy.reasoning_policy_id,
        start_refs=[entity_a],
        target_refs=[entity_b],
        question="What provenance-preserving analytical chains connect synthetic entity A to synthetic entity B, and what qualifications remain unresolved?",
        allowed_node_types=[
            ReasoningNodeType.entity,
            ReasoningNodeType.connection_path,
            ReasoningNodeType.evidence_chain,
            ReasoningNodeType.documentary_interpretation,
            ReasoningNodeType.connection_candidate,
            ReasoningNodeType.connection_hypothesis,
        ],
        max_hops=5,
        created_at="2026-09-30T20:00:00Z",
        metadata={"synthetic_reference": True},
    )

    primary_branch_id = "reasoning-branch:synthetic:evidence-chain:v1"
    hypothesis_branch_id = "reasoning-branch:synthetic:hypothesis:v1"
    primary_hops = [
        ReasoningHop(
            reasoning_hop_id="reasoning-hop:synthetic:primary:0",
            reasoning_query_ref=query.reasoning_query_id,
            branch_ref=primary_branch_id,
            sequence_index=0,
            from_ref=entity_a,
            from_type=ReasoningNodeType.entity,
            to_ref=primary_path.connection_path_id,
            to_type=ReasoningNodeType.connection_path,
            relation=ReasoningHopRelation.starts_from,
            upstream_object_refs=[primary_path.connection_path_id],
            provenance_refs=["provenance:synthetic:reasoning:primary:0"],
            source_independence_groups=["independence-group:synthetic:filing"],
            epistemic_state="source-observed-path",
            uncertainty=0.10,
            uncertainty_semantics="synthetic analytical uncertainty for traversal bookkeeping; not probability that a relationship is true",
            explanation="Begin from entity A and traverse the provenance-preserving source-observed connection path object.",
            metadata={"synthetic_reference": True},
        ),
        ReasoningHop(
            reasoning_hop_id="reasoning-hop:synthetic:primary:1",
            reasoning_query_ref=query.reasoning_query_id,
            branch_ref=primary_branch_id,
            sequence_index=1,
            from_ref=primary_path.connection_path_id,
            from_type=ReasoningNodeType.connection_path,
            to_ref=chain.evidence_chain_id,
            to_type=ReasoningNodeType.evidence_chain,
            relation=ReasoningHopRelation.explained_by,
            upstream_object_refs=[primary_path.connection_path_id, chain.evidence_chain_id],
            provenance_refs=["provenance:synthetic:reasoning:primary:1"],
            source_independence_groups=list(chain.independence_groups),
            epistemic_state="evidence-chain-explanation",
            uncertainty=0.18,
            uncertainty_semantics="synthetic analytical uncertainty reflecting unresolved qualification; not evidence strength",
            explanation="Traverse from the connection path into its explicit evidence-chain explanation while preserving source independence groups.",
            metadata={"synthetic_reference": True},
        ),
        ReasoningHop(
            reasoning_hop_id="reasoning-hop:synthetic:primary:2",
            reasoning_query_ref=query.reasoning_query_id,
            branch_ref=primary_branch_id,
            sequence_index=2,
            from_ref=chain.evidence_chain_id,
            from_type=ReasoningNodeType.evidence_chain,
            to_ref=interpretation_a.documentary_interpretation_id,
            to_type=ReasoningNodeType.documentary_interpretation,
            relation=ReasoningHopRelation.supported_by,
            upstream_object_refs=[chain.evidence_chain_id, interpretation_a.documentary_interpretation_id, evidence_position_a.evidence_position_id],
            provenance_refs=["provenance:synthetic:reasoning:primary:2"],
            source_independence_groups=[evidence_position_a.independence_group],
            epistemic_state="documentary-support",
            uncertainty=0.14,
            uncertainty_semantics="synthetic analytical uncertainty; documentary interpretation remains non-dispositive",
            explanation="Use the provenance-bearing filing interpretation as one supporting analytical premise, not as a truth verdict.",
            metadata={"synthetic_reference": True},
        ),
        ReasoningHop(
            reasoning_hop_id="reasoning-hop:synthetic:primary:3",
            reasoning_query_ref=query.reasoning_query_id,
            branch_ref=primary_branch_id,
            sequence_index=3,
            from_ref=interpretation_a.documentary_interpretation_id,
            from_type=ReasoningNodeType.documentary_interpretation,
            to_ref=entity_b,
            to_type=ReasoningNodeType.entity,
            relation=ReasoningHopRelation.mentions,
            upstream_object_refs=[interpretation_a.documentary_interpretation_id, entity_b],
            provenance_refs=["provenance:synthetic:reasoning:primary:3"],
            source_independence_groups=[evidence_position_a.independence_group],
            epistemic_state="documentary-entity-reference",
            uncertainty=0.16,
            uncertainty_semantics="synthetic analytical uncertainty; reaching entity B does not establish an endpoint relationship",
            explanation="Reach entity B through an explicit documentary interpretation that references both entities; reachability remains analytical only.",
            metadata={"synthetic_reference": True},
        ),
    ]

    hypothesis_hops = [
        ReasoningHop(
            reasoning_hop_id="reasoning-hop:synthetic:hypothesis:0",
            reasoning_query_ref=query.reasoning_query_id,
            branch_ref=hypothesis_branch_id,
            sequence_index=0,
            from_ref=entity_a,
            from_type=ReasoningNodeType.entity,
            to_ref=alternative_path.connection_path_id,
            to_type=ReasoningNodeType.connection_path,
            relation=ReasoningHopRelation.starts_from,
            upstream_object_refs=[alternative_path.connection_path_id],
            provenance_refs=["provenance:synthetic:reasoning:hypothesis:0"],
            source_independence_groups=[evidence_position_b.independence_group],
            epistemic_state="hypothesis-path",
            uncertainty=0.35,
            uncertainty_semantics="synthetic analytical uncertainty reflecting hypothesis-level epistemic state",
            explanation="Traverse the alternative path while preserving its hypothesis-level epistemic state.",
            metadata={"synthetic_reference": True},
        ),
        ReasoningHop(
            reasoning_hop_id="reasoning-hop:synthetic:hypothesis:1",
            reasoning_query_ref=query.reasoning_query_id,
            branch_ref=hypothesis_branch_id,
            sequence_index=1,
            from_ref=alternative_path.connection_path_id,
            from_type=ReasoningNodeType.connection_path,
            to_ref=hypothesis.connection_hypothesis_id,
            to_type=ReasoningNodeType.connection_hypothesis,
            relation=ReasoningHopRelation.proposed_by,
            upstream_object_refs=[alternative_path.connection_path_id, hypothesis.connection_hypothesis_id, candidate.connection_candidate_id],
            provenance_refs=["provenance:synthetic:reasoning:hypothesis:1"],
            source_independence_groups=[evidence_position_b.independence_group],
            epistemic_state="supported-for-validation-hypothesis",
            uncertainty=0.42,
            uncertainty_semantics="synthetic analytical uncertainty; candidate/hypothesis score is not relationship probability",
            explanation="Connect the alternative path to the explicit upstream relationship hypothesis without promoting it.",
            metadata={"synthetic_reference": True},
        ),
        ReasoningHop(
            reasoning_hop_id="reasoning-hop:synthetic:hypothesis:2",
            reasoning_query_ref=query.reasoning_query_id,
            branch_ref=hypothesis_branch_id,
            sequence_index=2,
            from_ref=hypothesis.connection_hypothesis_id,
            from_type=ReasoningNodeType.connection_hypothesis,
            to_ref=interpretation_b.documentary_interpretation_id,
            to_type=ReasoningNodeType.documentary_interpretation,
            relation=ReasoningHopRelation.contextualized_by,
            upstream_object_refs=[hypothesis.connection_hypothesis_id, evidence_position_b.evidence_position_id, interpretation_b.documentary_interpretation_id],
            provenance_refs=["provenance:synthetic:reasoning:hypothesis:2"],
            source_independence_groups=[evidence_position_b.independence_group],
            epistemic_state="contextualized-hypothesis",
            uncertainty=0.46,
            uncertainty_semantics="synthetic analytical uncertainty; contextual material is non-dispositive",
            explanation="Use the disclosure interpretation only as contextual material for the still-unvalidated hypothesis.",
            metadata={"synthetic_reference": True},
        ),
    ]

    primary_branch = ReasoningBranch(
        reasoning_branch_id=primary_branch_id,
        reasoning_query_ref=query.reasoning_query_id,
        hop_refs=[x.reasoning_hop_id for x in primary_hops],
        endpoint_ref=entity_b,
        endpoint_type=ReasoningNodeType.entity,
        support_state=ReasoningSupportState.qualified,
        contradiction_marker_refs=[contradiction.path_contradiction_marker_id],
        source_independence_groups=list(chain.independence_groups),
        branch_score=0.78,
        branch_score_semantics="synthetic reasoning coverage score; not evidence strength, relationship probability, or truth probability",
        explanation="A four-hop analytical chain reaches entity B through the source-observed path, evidence chain, and documentary interpretation, while retaining the upstream temporal/source contradiction.",
        completed=True,
        metadata={"synthetic_reference": True},
    )
    hypothesis_branch = ReasoningBranch(
        reasoning_branch_id=hypothesis_branch_id,
        reasoning_query_ref=query.reasoning_query_id,
        hop_refs=[x.reasoning_hop_id for x in hypothesis_hops],
        endpoint_ref=interpretation_b.documentary_interpretation_id,
        endpoint_type=ReasoningNodeType.documentary_interpretation,
        support_state=ReasoningSupportState.unresolved,
        source_independence_groups=[evidence_position_b.independence_group],
        branch_score=0.44,
        branch_score_semantics="synthetic branch exploration score only; not evidence strength or truth probability",
        explanation="A three-hop alternative branch reaches contextual documentary material but stops before asserting any endpoint relationship because the upstream relationship remains a hypothesis.",
        completed=False,
        metadata={"synthetic_reference": True},
    )

    primary_inference = ReasoningInferenceStep(
        reasoning_inference_step_id="reasoning-inference:synthetic:primary:v1",
        reasoning_query_ref=query.reasoning_query_id,
        branch_ref=primary_branch_id,
        premise_hop_refs=[x.reasoning_hop_id for x in primary_hops],
        premise_object_refs=[primary_path.connection_path_id, chain.evidence_chain_id, interpretation_a.documentary_interpretation_id],
        conclusion_statement="The available provenance-preserving objects provide an analytical route from entity A to entity B that is qualified by an unresolved temporal/source contradiction; this does not establish a new relationship fact.",
        support_state=ReasoningSupportState.qualified,
        analytical_confidence=0.72,
        analytical_confidence_semantics="synthetic confidence in the completeness of this reasoning trace, not probability that an endpoint relationship is true",
        contradiction_marker_refs=[contradiction.path_contradiction_marker_id],
        provenance_refs=["provenance:synthetic:reasoning-inference:primary:v1"],
        metadata={"synthetic_reference": True},
    )
    hypothesis_inference = ReasoningInferenceStep(
        reasoning_inference_step_id="reasoning-inference:synthetic:hypothesis:v1",
        reasoning_query_ref=query.reasoning_query_id,
        branch_ref=hypothesis_branch_id,
        premise_hop_refs=[x.reasoning_hop_id for x in hypothesis_hops],
        premise_object_refs=[alternative_path.connection_path_id, hypothesis.connection_hypothesis_id, interpretation_b.documentary_interpretation_id],
        conclusion_statement="The alternative analytical route remains an unvalidated hypothesis contextualized by documentary material and must not be treated as a factual relationship.",
        support_state=ReasoningSupportState.unresolved,
        analytical_confidence=0.48,
        analytical_confidence_semantics="synthetic confidence in branch characterization only; not probability that the hypothesis is true",
        provenance_refs=["provenance:synthetic:reasoning-inference:hypothesis:v1"],
        metadata={"synthetic_reference": True},
    )

    propagation = ReasoningContradictionPropagation(
        contradiction_propagation_id="reasoning-contradiction-propagation:synthetic:v1",
        source_contradiction_marker_ref=contradiction.path_contradiction_marker_id,
        affected_branch_refs=[primary_branch_id],
        affected_hop_refs=[primary_hops[1].reasoning_hop_id, primary_hops[2].reasoning_hop_id],
        affected_inference_refs=[primary_inference.reasoning_inference_step_id],
        propagated_state=ReasoningSupportState.qualified,
        explanation="The upstream temporal/source contradiction propagates into the primary reasoning branch as a qualification; it is neither erased nor treated as proof of the opposite conclusion.",
        provenance_refs=["provenance:synthetic:reasoning-contradiction-propagation:v1"],
        metadata={"synthetic_reference": True},
    )

    independence = SourceIndependenceAssessment(
        source_independence_assessment_id="source-independence-assessment:synthetic:v1",
        reasoning_query_ref=query.reasoning_query_id,
        branch_refs=[primary_branch_id, hypothesis_branch_id],
        independence_groups=list(chain.independence_groups),
        shared_provenance_refs=[primary_path.connection_path_id, alternative_path.connection_path_id],
        independent_group_count=len(chain.independence_groups),
        explanation="Two upstream independence groups are preserved. The existence of two analytical branches does not create a third independent source group.",
        metadata={"synthetic_reference": True},
    )

    stops = [
        ReasoningStoppingDecision(
            reasoning_stopping_decision_id="reasoning-stop:synthetic:primary:v1",
            reasoning_query_ref=query.reasoning_query_id,
            branch_ref=primary_branch_id,
            stop_reason=ReasoningStopReason.target_reached,
            hop_count=len(primary_hops),
            reached_target=True,
            unresolved_issue_refs=[contradiction.path_contradiction_marker_id],
            explanation="Stop because the requested target is analytically reachable; preserve the unresolved contradiction and do not convert reachability into a relationship fact.",
            provenance_refs=["provenance:synthetic:reasoning-stop:primary:v1"],
            metadata={"synthetic_reference": True},
        ),
        ReasoningStoppingDecision(
            reasoning_stopping_decision_id="reasoning-stop:synthetic:hypothesis:v1",
            reasoning_query_ref=query.reasoning_query_id,
            branch_ref=hypothesis_branch_id,
            stop_reason=ReasoningStopReason.unvalidated_hypothesis,
            hop_count=len(hypothesis_hops),
            reached_target=False,
            unresolved_issue_refs=[hypothesis.connection_hypothesis_id],
            explanation="Stop the alternative branch at the explicit unvalidated-hypothesis boundary instead of inferring a factual endpoint connection.",
            provenance_refs=["provenance:synthetic:reasoning-stop:hypothesis:v1"],
            metadata={"synthetic_reference": True},
        ),
    ]

    trace = MultiHopReasoningTrace(
        reasoning_trace_id="reasoning-trace:synthetic:entity-a-to-b:v1",
        reasoning_query_ref=query.reasoning_query_id,
        branch_refs=[primary_branch_id, hypothesis_branch_id],
        inference_step_refs=[primary_inference.reasoning_inference_step_id, hypothesis_inference.reasoning_inference_step_id],
        contradiction_propagation_refs=[propagation.contradiction_propagation_id],
        source_independence_assessment_refs=[independence.source_independence_assessment_id],
        stopping_decision_refs=[x.reasoning_stopping_decision_id for x in stops],
        created_at="2026-09-30T20:05:00Z",
        metadata={"synthetic_reference": True},
    )
    snapshot = MultiHopReasoningSnapshot(
        reasoning_snapshot_id="reasoning-snapshot:synthetic:2026-09-30:v1",
        connection_path_evidence_snapshot_ref=upstream_snapshot.connection_path_evidence_snapshot_id,
        policy_refs=[policy.reasoning_policy_id],
        query_refs=[query.reasoning_query_id],
        trace_refs=[trace.reasoning_trace_id],
        created_at="2026-09-30T20:06:00Z",
        metadata={"synthetic_reference": True},
    )

    return MultiHopResearchInvestigationGraphReasoningBundle(
        explainable_connection_paths_evidence_chains_bundle=upstream,
        policies=[policy],
        queries=[query],
        hops=primary_hops + hypothesis_hops,
        branches=[primary_branch, hypothesis_branch],
        inference_steps=[primary_inference, hypothesis_inference],
        contradiction_propagations=[propagation],
        source_independence_assessments=[independence],
        stopping_decisions=stops,
        traces=[trace],
        snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    b = reference_multi_hop_research_investigation_graph_reasoning_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": [
            "sc.core.explainable-connection-paths-evidence-chains.v1",
            "sc.core.network-structure-community-motif-intelligence.v1",
            "sc.core.relationship-discovery-connection-hypothesis.v1",
            "sc.core.public-record-documentary-source-object-model.v1",
            "sc.core.cross-source-entity-reconciliation-identity-provenance.v1",
            "sc.core.evidence-graph-neural-analysis-validation.v1",
        ],
        "object_types": [
            "MultiHopReasoningPolicy",
            "MultiHopReasoningQuery",
            "ReasoningHop",
            "ReasoningBranch",
            "ReasoningInferenceStep",
            "ReasoningContradictionPropagation",
            "SourceIndependenceAssessment",
            "ReasoningStoppingDecision",
            "MultiHopReasoningTrace",
            "MultiHopReasoningSnapshot",
            "MultiHopResearchInvestigationGraphReasoningBundle",
        ],
        "principles": {
            "multi_hop_reachability_is_not_relationship_truth": True,
            "reasoning_chain_is_not_proof": True,
            "analytical_confidence_is_not_probability_of_truth": True,
            "repeated_paths_are_not_independent_corroboration": True,
            "contradiction_propagation_is_non_dispositive": True,
            "target_reached_is_not_relationship_fact": True,
            "algorithmic_reasoning_is_not_investigator_conclusion": True,
            "epistemic_state_is_preserved_across_hops": True,
            "explicit_stopping_rules_are_required": True,
        },
        "boundaries": {
            "runtime_may_mutate_relationship_graph": False,
            "runtime_may_mutate_evidence_graph": False,
            "runtime_may_mutate_identity_graph": False,
            "runtime_may_promote_candidate_or_hypothesis": False,
            "v385_creates_evidence_edge": False,
            "v385_creates_endpoint_relationship_fact": False,
        },
        "reference": {
            "queries": len(b.queries),
            "hops": len(b.hops),
            "branches": len(b.branches),
            "inference_steps": len(b.inference_steps),
            "contradiction_propagations": len(b.contradiction_propagations),
            "source_independence_assessments": len(b.source_independence_assessments),
            "stopping_decisions": len(b.stopping_decisions),
            "primary_branch_hops": len(b.branches[0].hop_refs),
            "alternative_branch_hops": len(b.branches[1].hop_refs),
            "primary_branch_state": b.branches[0].support_state.value,
            "alternative_branch_state": b.branches[1].support_state.value,
            "relationship_graph_mutation_performed": b.relationship_graph_mutation_performed,
            "evidence_graph_mutation_performed": b.evidence_graph_mutation_performed,
            "identity_graph_mutation_performed": b.identity_graph_mutation_performed,
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
