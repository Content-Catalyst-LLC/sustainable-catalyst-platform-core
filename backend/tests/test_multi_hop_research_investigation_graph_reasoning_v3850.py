import copy
import pytest
from pydantic import ValidationError

from app.services.multi_hop_research_investigation_graph_reasoning import (
    CONTRACT_VERSION,
    MultiHopReasoningPolicy,
    MultiHopReasoningQuery,
    ReasoningBranch,
    ReasoningHop,
    ReasoningNodeType,
    ReasoningStopReason,
    ReasoningSupportState,
    SourceIndependenceAssessment,
    contract_document,
    reference_multi_hop_research_investigation_graph_reasoning_bundle,
)


def ref():
    return reference_multi_hop_research_investigation_graph_reasoning_bundle()


def test_contract_identity():
    c = contract_document()
    assert c["release"] == "3.85.0"
    assert c["contract"] == CONTRACT_VERSION
    assert c["database_migration"] == "none"


def test_reference_counts():
    b = ref()
    assert len(b.queries) == 1
    assert len(b.hops) == 7
    assert len(b.branches) == 2
    assert len(b.inference_steps) == 2
    assert len(b.contradiction_propagations) == 1
    assert len(b.source_independence_assessments) == 1
    assert len(b.stopping_decisions) == 2
    assert len(b.traces) == 1
    assert len(b.snapshots) == 1


@pytest.mark.parametrize("field", [
    "multi_hop_reachability_is_not_relationship_truth",
    "reasoning_chain_is_not_proof",
    "analytical_confidence_is_not_probability_of_truth",
    "repeated_paths_are_not_independent_corroboration",
    "contradiction_propagation_is_non_dispositive",
    "algorithmic_reasoning_is_not_investigator_conclusion",
])
def test_bundle_boundaries_true(field):
    assert getattr(ref(), field) is True


@pytest.mark.parametrize("field", [
    "relationship_graph_mutation_performed",
    "evidence_graph_mutation_performed",
    "identity_graph_mutation_performed",
])
def test_bundle_mutations_false(field):
    assert getattr(ref(), field) is False


@pytest.mark.parametrize("field", [
    "multi_hop_reachability_is_not_relationship_truth",
    "reasoning_chain_is_not_proof",
    "analytical_confidence_is_not_probability_of_truth",
    "repeated_paths_are_not_independent_corroboration",
    "contradiction_propagation_is_non_dispositive",
    "target_reached_is_not_relationship_fact",
    "algorithmic_reasoning_is_not_investigator_conclusion",
    "epistemic_state_is_preserved_across_hops",
    "explicit_stopping_rules_are_required",
])
def test_contract_principles(field):
    assert contract_document()["principles"][field] is True


@pytest.mark.parametrize("field", [
    "runtime_may_mutate_relationship_graph",
    "runtime_may_mutate_evidence_graph",
    "runtime_may_mutate_identity_graph",
    "runtime_may_promote_candidate_or_hypothesis",
    "v385_creates_evidence_edge",
    "v385_creates_endpoint_relationship_fact",
])
def test_contract_boundaries_false(field):
    assert contract_document()["boundaries"][field] is False


def test_primary_branch_reaches_target_but_is_qualified():
    b = ref()
    branch = b.branches[0]
    query = b.queries[0]
    assert branch.endpoint_ref in query.target_refs
    assert branch.support_state == ReasoningSupportState.qualified
    assert branch.completed is True
    assert branch.endpoint_reached_does_not_establish_relationship is True


def test_alternative_branch_stops_before_target():
    b = ref()
    branch = b.branches[1]
    query = b.queries[0]
    assert branch.endpoint_ref not in query.target_refs
    assert branch.support_state == ReasoningSupportState.unresolved
    assert branch.completed is False
    stop = [x for x in b.stopping_decisions if x.branch_ref == branch.reasoning_branch_id][0]
    assert stop.stop_reason == ReasoningStopReason.unvalidated_hypothesis
    assert stop.reached_target is False


def test_primary_stop_target_reached_is_not_fact():
    b = ref()
    stop = [x for x in b.stopping_decisions if x.stop_reason == ReasoningStopReason.target_reached][0]
    assert stop.reached_target is True
    assert stop.target_reached_is_not_relationship_fact is True
    assert stop.stopping_decision_is_not_truth_verdict is True


def test_contradiction_propagates_as_qualification():
    p = ref().contradiction_propagations[0]
    assert p.propagated_state == ReasoningSupportState.qualified
    assert p.contradiction_must_remain_visible is True
    assert p.contradiction_does_not_auto_invalidate_reasoning is True
    assert p.contradiction_does_not_auto_prove_opposite is True


def test_source_independence_counts_groups_not_paths():
    a = ref().source_independence_assessments[0]
    assert len(a.branch_refs) == 2
    assert a.independent_group_count == 2
    assert a.path_count_is_not_independence_count is True
    assert a.repeated_source_is_not_independent_corroboration is True


def test_inference_confidence_is_not_truth_probability():
    for x in ref().inference_steps:
        assert x.confidence_is_not_probability_of_truth is True
        assert x.conclusion_is_hypothesis_not_fact is True
        assert x.inference_does_not_create_graph_edge is True


def test_hops_preserve_nonpromotion_boundary():
    for x in ref().hops:
        assert x.hop_is_not_relationship_fact is True
        assert x.hop_is_not_causal_claim is True
        assert x.uncertainty_is_not_probability_of_truth is True
        assert x.traversal_does_not_promote_upstream_object is True


def test_trace_is_immutable_nonproof():
    t = ref().traces[0]
    assert t.immutable_trace is True
    assert t.trace_is_reproducible_analysis_not_proof is True
    assert t.trace_does_not_promote_candidates_or_hypotheses is True
    assert t.trace_does_not_mutate_graphs is True


def test_snapshot_is_immutable_nonverdict():
    s = ref().snapshots[0]
    assert s.immutable_snapshot is True
    assert s.snapshot_preserves_upstream_epistemic_states is True
    assert s.snapshot_is_not_endpoint_truth_verdict is True
    assert s.snapshot_does_not_mutate_graphs is True


def test_schema_generation():
    schema = type(ref()).model_json_schema()
    assert schema["title"] == "MultiHopResearchInvestigationGraphReasoningBundle"
    assert "$defs" in schema


@pytest.mark.parametrize("idx,expected", [
    (0, "source-observed-path"),
    (1, "evidence-chain-explanation"),
    (2, "documentary-support"),
    (3, "documentary-entity-reference"),
    (4, "hypothesis-path"),
    (5, "supported-for-validation-hypothesis"),
    (6, "contextualized-hypothesis"),
])
def test_reference_hop_epistemic_states(idx, expected):
    assert ref().hops[idx].epistemic_state == expected


@pytest.mark.parametrize("idx", range(7))
def test_reference_hop_uncertainty_in_range(idx):
    v = ref().hops[idx].uncertainty
    assert 0 <= v <= 1


@pytest.mark.parametrize("idx", range(7))
def test_reference_hop_has_provenance(idx):
    assert ref().hops[idx].provenance_refs


@pytest.mark.parametrize("idx", range(7))
def test_reference_hop_has_upstream_objects(idx):
    assert ref().hops[idx].upstream_object_refs


@pytest.mark.parametrize("idx", range(7))
def test_reference_hop_has_explanation(idx):
    assert len(ref().hops[idx].explanation) > 10


@pytest.mark.parametrize("idx", range(2))
def test_branch_score_semantics_present(idx):
    b = ref().branches[idx]
    assert b.branch_score is not None
    assert b.branch_score_semantics
    assert b.branch_score_is_not_evidence_strength is True


@pytest.mark.parametrize("idx", range(2))
def test_branch_has_source_groups(idx):
    assert ref().branches[idx].source_independence_groups


@pytest.mark.parametrize("idx", range(2))
def test_inference_has_provenance(idx):
    assert ref().inference_steps[idx].provenance_refs


@pytest.mark.parametrize("idx", range(2))
def test_stop_has_provenance(idx):
    assert ref().stopping_decisions[idx].provenance_refs


@pytest.mark.parametrize("type_value", [x.value for x in ReasoningNodeType])
def test_reasoning_node_type_round_trip(type_value):
    assert ReasoningNodeType(type_value).value == type_value


@pytest.mark.parametrize("max_hops", [1, 2, 3, 4, 5, 6, 12, 24])
def test_policy_valid_hop_limits(max_hops):
    p = MultiHopReasoningPolicy(reasoning_policy_id=f"policy:{max_hops}", max_hops=max_hops)
    assert p.max_hops == max_hops


@pytest.mark.parametrize("max_hops", [0, 25, -1, 100])
def test_policy_invalid_hop_limits(max_hops):
    with pytest.raises(ValidationError):
        MultiHopReasoningPolicy(reasoning_policy_id="policy:x", max_hops=max_hops)


def test_query_duplicate_start_refs_rejected():
    q = ref().queries[0].model_dump(mode="python")
    q["start_refs"] = q["start_refs"] * 2
    with pytest.raises(ValidationError):
        MultiHopReasoningQuery(**q)


def test_query_duplicate_target_refs_rejected():
    q = ref().queries[0].model_dump(mode="python")
    q["target_refs"] = q["target_refs"] * 2
    with pytest.raises(ValidationError):
        MultiHopReasoningQuery(**q)


def test_query_duplicate_allowed_types_rejected():
    q = ref().queries[0].model_dump(mode="python")
    q["allowed_node_types"] = q["allowed_node_types"] + [q["allowed_node_types"][0]]
    with pytest.raises(ValidationError):
        MultiHopReasoningQuery(**q)


def test_hop_same_endpoint_rejected():
    h = ref().hops[0].model_dump(mode="python")
    h["to_ref"] = h["from_ref"]
    h["to_type"] = h["from_type"]
    with pytest.raises(ValidationError):
        ReasoningHop(**h)


def test_branch_duplicate_hops_rejected():
    b = ref().branches[0].model_dump(mode="python")
    b["hop_refs"] = b["hop_refs"] + [b["hop_refs"][0]]
    with pytest.raises(ValidationError):
        ReasoningBranch(**b)


def test_independence_count_must_match_groups():
    a = ref().source_independence_assessments[0].model_dump(mode="python")
    a["independent_group_count"] = 99
    with pytest.raises(ValidationError):
        SourceIndependenceAssessment(**a)


@pytest.mark.parametrize("mutation", [
    "bad_query_policy",
    "bad_query_start",
    "bad_hop_query",
    "bad_hop_branch",
    "bad_hop_endpoint",
    "bad_branch_query",
    "bad_branch_hop",
    "bad_branch_endpoint",
    "bad_branch_contradiction",
    "bad_inference_query",
    "bad_inference_branch",
    "bad_inference_hop",
    "bad_inference_object",
    "bad_inference_contradiction",
    "bad_propagation_marker",
    "bad_propagation_branch",
    "bad_propagation_hop",
    "bad_propagation_inference",
    "bad_independence_query",
    "bad_independence_branch",
    "bad_stop_query",
    "bad_stop_branch",
    "bad_trace_query",
    "bad_trace_branch",
    "bad_trace_inference",
    "bad_trace_propagation",
    "bad_trace_independence",
    "bad_trace_stop",
    "bad_snapshot_upstream",
    "bad_snapshot_policy",
    "bad_snapshot_query",
    "bad_snapshot_trace",
])
def test_bundle_cross_reference_failures(mutation):
    data = ref().model_dump(mode="python")
    bad = "missing:ref"
    if mutation == "bad_query_policy": data["queries"][0]["reasoning_policy_ref"] = bad
    elif mutation == "bad_query_start": data["queries"][0]["start_refs"] = [bad]
    elif mutation == "bad_hop_query": data["hops"][0]["reasoning_query_ref"] = bad
    elif mutation == "bad_hop_branch": data["hops"][0]["branch_ref"] = bad
    elif mutation == "bad_hop_endpoint": data["hops"][0]["to_ref"] = bad
    elif mutation == "bad_branch_query": data["branches"][0]["reasoning_query_ref"] = bad
    elif mutation == "bad_branch_hop": data["branches"][0]["hop_refs"][0] = bad
    elif mutation == "bad_branch_endpoint": data["branches"][0]["endpoint_ref"] = bad
    elif mutation == "bad_branch_contradiction": data["branches"][0]["contradiction_marker_refs"] = [bad]
    elif mutation == "bad_inference_query": data["inference_steps"][0]["reasoning_query_ref"] = bad
    elif mutation == "bad_inference_branch": data["inference_steps"][0]["branch_ref"] = bad
    elif mutation == "bad_inference_hop": data["inference_steps"][0]["premise_hop_refs"][0] = bad
    elif mutation == "bad_inference_object": data["inference_steps"][0]["premise_object_refs"][0] = bad
    elif mutation == "bad_inference_contradiction": data["inference_steps"][0]["contradiction_marker_refs"] = [bad]
    elif mutation == "bad_propagation_marker": data["contradiction_propagations"][0]["source_contradiction_marker_ref"] = bad
    elif mutation == "bad_propagation_branch": data["contradiction_propagations"][0]["affected_branch_refs"] = [bad]
    elif mutation == "bad_propagation_hop": data["contradiction_propagations"][0]["affected_hop_refs"] = [bad]
    elif mutation == "bad_propagation_inference": data["contradiction_propagations"][0]["affected_inference_refs"] = [bad]
    elif mutation == "bad_independence_query": data["source_independence_assessments"][0]["reasoning_query_ref"] = bad
    elif mutation == "bad_independence_branch": data["source_independence_assessments"][0]["branch_refs"] = [bad]
    elif mutation == "bad_stop_query": data["stopping_decisions"][0]["reasoning_query_ref"] = bad
    elif mutation == "bad_stop_branch": data["stopping_decisions"][0]["branch_ref"] = bad
    elif mutation == "bad_trace_query": data["traces"][0]["reasoning_query_ref"] = bad
    elif mutation == "bad_trace_branch": data["traces"][0]["branch_refs"] = [bad]
    elif mutation == "bad_trace_inference": data["traces"][0]["inference_step_refs"] = [bad]
    elif mutation == "bad_trace_propagation": data["traces"][0]["contradiction_propagation_refs"] = [bad]
    elif mutation == "bad_trace_independence": data["traces"][0]["source_independence_assessment_refs"] = [bad]
    elif mutation == "bad_trace_stop": data["traces"][0]["stopping_decision_refs"] = [bad]
    elif mutation == "bad_snapshot_upstream": data["snapshots"][0]["connection_path_evidence_snapshot_ref"] = bad
    elif mutation == "bad_snapshot_policy": data["snapshots"][0]["policy_refs"] = [bad]
    elif mutation == "bad_snapshot_query": data["snapshots"][0]["query_refs"] = [bad]
    elif mutation == "bad_snapshot_trace": data["snapshots"][0]["trace_refs"] = [bad]
    with pytest.raises(ValidationError):
        type(ref())(**data)


@pytest.mark.parametrize("idx", range(7))
def test_hop_fingerprint_stable(idx):
    h = ref().hops[idx]
    assert h.fingerprint() == h.fingerprint()
    assert len(h.fingerprint()) == 64


@pytest.mark.parametrize("idx", range(2))
def test_branch_fingerprint_stable(idx):
    b = ref().branches[idx]
    assert b.fingerprint() == b.fingerprint()
    assert len(b.fingerprint()) == 64


@pytest.mark.parametrize("idx", range(2))
def test_inference_fingerprint_stable(idx):
    x = ref().inference_steps[idx]
    assert x.fingerprint() == x.fingerprint()
    assert len(x.fingerprint()) == 64


def test_bundle_fingerprint_stable():
    b = ref()
    assert b.fingerprint() == b.fingerprint()
    assert len(b.fingerprint()) == 64


@pytest.mark.parametrize("idx", range(4))
def test_primary_branch_hops_are_contiguous(idx):
    b = ref()
    branch = b.branches[0]
    hop_by_id = {x.reasoning_hop_id: x for x in b.hops}
    h = hop_by_id[branch.hop_refs[idx]]
    assert h.sequence_index == idx


@pytest.mark.parametrize("idx", range(3))
def test_hypothesis_branch_hops_are_contiguous(idx):
    b = ref()
    branch = b.branches[1]
    hop_by_id = {x.reasoning_hop_id: x for x in b.hops}
    h = hop_by_id[branch.hop_refs[idx]]
    assert h.sequence_index == idx


def test_primary_branch_chain_contiguity():
    b = ref()
    hop_by_id = {x.reasoning_hop_id: x for x in b.hops}
    hs = [hop_by_id[x] for x in b.branches[0].hop_refs]
    assert all(a.to_ref == z.from_ref for a, z in zip(hs, hs[1:]))


def test_hypothesis_branch_chain_contiguity():
    b = ref()
    hop_by_id = {x.reasoning_hop_id: x for x in b.hops}
    hs = [hop_by_id[x] for x in b.branches[1].hop_refs]
    assert all(a.to_ref == z.from_ref for a, z in zip(hs, hs[1:]))


def test_reference_query_max_hops_within_policy():
    b = ref()
    assert b.queries[0].max_hops <= b.policies[0].max_hops


def test_contract_reference_fingerprint_matches_bundle():
    assert contract_document()["reference"]["bundle_fingerprint_sha256"] == ref().fingerprint()


@pytest.mark.parametrize("idx", range(2))
def test_stopping_hop_count_matches_branch(idx):
    b = ref()
    branch_by_id = {x.reasoning_branch_id: x for x in b.branches}
    stop = b.stopping_decisions[idx]
    assert stop.hop_count == len(branch_by_id[stop.branch_ref].hop_refs)


def test_primary_inference_preserves_contradiction():
    assert ref().inference_steps[0].contradiction_marker_refs


def test_alternative_inference_remains_unresolved():
    assert ref().inference_steps[1].support_state == ReasoningSupportState.unresolved


def test_reference_contains_two_independence_groups():
    assert ref().source_independence_assessments[0].independent_group_count == 2


def test_reference_does_not_create_third_independent_group_from_two_paths():
    a = ref().source_independence_assessments[0]
    assert len(a.branch_refs) == 2
    assert a.independent_group_count == 2


def test_query_allowed_node_types_include_hypothesis_and_entity():
    vals = set(ref().queries[0].allowed_node_types)
    assert ReasoningNodeType.entity in vals
    assert ReasoningNodeType.connection_hypothesis in vals


def test_policy_allows_hypothesis_but_does_not_promote_it():
    b = ref()
    assert b.policies[0].allow_hypothesis_traversal is True
    assert b.traces[0].trace_does_not_promote_candidates_or_hypotheses is True


@pytest.mark.parametrize("name", [
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
])
def test_contract_lists_object_type(name):
    assert name in contract_document()["object_types"]
