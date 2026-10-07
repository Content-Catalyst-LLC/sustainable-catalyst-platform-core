from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.routers import context_retrieval_relevance as api
from app.services.context_retrieval_relevance import (
    ContextRetrievalRelevanceBundle,
    RelevanceSignalKind,
    RetrievalMethodKind,
    RetrievalQueryKind,
    RetrievalReviewState,
    contract_document,
    reference_context_retrieval_relevance_bundle,
)


def ref():
    return reference_context_retrieval_relevance_bundle()


def payload():
    return ref().model_dump(mode="json")


def invalid(mutator):
    p = deepcopy(payload())
    mutator(p)
    with pytest.raises((ValidationError, ValueError)):
        ContextRetrievalRelevanceBundle.model_validate(p)


def test_release_identity():
    assert Settings().version == "4.12.0"
    assert ref().release == "4.12.0"
    assert ref().contract == "sc.core.context-retrieval-relevance-intelligence.v1"
    assert ref().predecessor_contract == "sc.core.contextual-memory-semantic-state-foundation.v1"


def test_v411_predecessor_is_exact_and_preserved():
    assert ref().predecessor_memory.release == "4.11.0"
    assert ref().predecessor_memory.contract == ref().predecessor_contract
    assert ref().snapshots[0].predecessor_memory_fingerprint_sha256 == ref().predecessor_memory.fingerprint()


def test_reference_query_is_project_scoped_and_cross_language():
    q = ref().queries[0]
    assert q.kind == RetrievalQueryKind.research_project
    assert len(q.requested_scope_refs) == 2
    assert q.language_tags == ["zh", "en", "es"]
    assert q.preserve_unresolved is True
    assert q.include_superseded is False
    assert q.max_results == 5


def test_query_uses_hybrid_explainable_methods():
    methods = set(ref().queries[0].methods)
    assert RetrievalMethodKind.hybrid in methods
    assert RetrievalMethodKind.semantic_anchor in methods
    assert RetrievalMethodKind.contextual_link in methods
    assert RetrievalMethodKind.multilingual_alignment in methods


def test_all_six_v411_memories_become_candidates():
    assert len(ref().candidates) == 6
    assert {x.memory_ref for x in ref().candidates} == {x.memory_id for x in ref().predecessor_memory.memories}


def test_each_candidate_uses_current_revision_by_default():
    memories = {x.memory_id: x for x in ref().predecessor_memory.memories}
    for c in ref().candidates:
        assert c.current_revision is True
        assert c.revision_ref == memories[c.memory_ref].current_revision_ref


def test_every_candidate_has_seven_explainable_signals():
    by_candidate = {}
    for s in ref().signals:
        by_candidate.setdefault(s.candidate_ref, []).append(s)
    assert len(ref().signals) == 42
    assert all(len(by_candidate[x.candidate_id]) == 7 for x in ref().candidates)
    assert all({s.kind for s in xs} == set(RelevanceSignalKind) for xs in by_candidate.values())


def test_signal_contributions_sum_to_candidate_score():
    signals = {x.signal_id: x for x in ref().signals}
    for c in ref().candidates:
        expected = sum(signals[x].contribution for x in c.signal_refs)
        assert c.aggregate_relevance_score == pytest.approx(expected)


def test_top_result_is_actor_continuity_hypothesis():
    rs = ref().result_sets[0]
    candidates = {x.candidate_id: x for x in ref().candidates}
    top = candidates[rs.results[0].candidate_ref]
    assert top.memory_ref == "memory:continuity:actor-ministry-agency"
    assert rs.results[0].relevance_score == pytest.approx(0.99)
    assert "thread:actor-continuity:candidate" in rs.results[0].unresolved_refs


def test_multilingual_divergence_ranks_second():
    rs = ref().result_sets[0]
    candidates = {x.candidate_id: x for x in ref().candidates}
    second = candidates[rs.results[1].candidate_ref]
    assert second.memory_ref == "memory:multilingual-divergence:governance"


def test_source_uncertainty_ranks_third():
    rs = ref().result_sets[0]
    candidates = {x.candidate_id: x for x in ref().candidates}
    third = candidates[rs.results[2].candidate_ref]
    assert third.memory_ref == "memory:epistemic-state:ministry-uncertainty"


def test_results_are_sorted_non_increasing():
    scores = [x.relevance_score for x in ref().result_sets[0].results]
    assert scores == sorted(scores, reverse=True)


def test_result_limit_preserves_omitted_candidate_trace():
    rs = ref().result_sets[0]
    assert len(rs.results) == 5
    assert len(rs.omitted_candidate_refs) == 1
    omitted = next(x for x in ref().candidates if x.candidate_id == rs.omitted_candidate_refs[0])
    assert omitted.memory_ref == "memory:geographic-grounding:brussels"


def test_selected_results_preserve_qualifications():
    candidates = {x.candidate_id: x for x in ref().candidates}
    for r in ref().result_sets[0].results:
        assert r.qualification_refs == candidates[r.candidate_ref].qualification_refs
        assert r.qualification_refs


def test_selected_results_preserve_unresolved_context_when_present():
    candidates = {x.candidate_id: x for x in ref().candidates}
    for r in ref().result_sets[0].results:
        assert r.unresolved_refs == candidates[r.candidate_ref].unresolved_refs


def test_four_selected_results_have_unresolved_context():
    assert sum(1 for x in ref().result_sets[0].results if x.unresolved_refs) == 4


def test_reviewed_candidates_have_reviewer():
    assert all(x.review_state == RetrievalReviewState.reviewed for x in ref().candidates)
    assert all(x.reviewer_ref == "reviewer:context-retrieval-reference" for x in ref().candidates)


def test_policy_relevance_is_not_truth_evidence_or_authority():
    p = ref().policy
    assert p.retrieval_rank_establishes_truth is False
    assert p.relevance_score_is_evidence_weight is False
    assert p.semantic_similarity_establishes_equivalence is False
    assert p.scope_proximity_establishes_authority is False
    assert p.provenance_completeness_establishes_credibility is False
    assert p.retrieval_frequency_increases_truth_or_authority is False


def test_policy_does_not_authorize_graph_mutation():
    p = ref().policy
    assert p.retrieval_mutates_memory is False
    assert p.context_graph_mutation_authorized is False
    assert p.identity_graph_mutation_authorized is False
    assert p.evidence_graph_mutation_authorized is False
    assert p.knowledge_graph_mutation_authorized is False


def test_policy_requires_explainability_and_qualification_preservation():
    p = ref().policy
    assert p.ranking_must_be_explainable is True
    assert p.qualifications_must_travel_with_results is True
    assert p.unresolved_context_must_not_be_silently_dropped is True
    assert p.candidate_generation_and_ranking_are_distinct is True


def test_provenance_is_bound_to_predecessor_memory_fingerprint():
    p = ref().provenance_records[0]
    assert p.predecessor_memory_fingerprint_sha256 == ref().predecessor_memory.fingerprint()
    assert p.replayable is True


def test_snapshot_is_deterministic():
    a = ref().snapshots[0].deterministic_retrieval_fingerprint_sha256
    b = reference_context_retrieval_relevance_bundle().snapshots[0].deterministic_retrieval_fingerprint_sha256
    assert a == b


def test_bundle_fingerprint_is_deterministic():
    assert ref().fingerprint() == reference_context_retrieval_relevance_bundle().fingerprint()


def test_contract_reference_counts_and_top_result():
    r = contract_document()["reference"]
    assert r["predecessor_release"] == "4.11.0"
    assert r["queries"] == 1
    assert r["generated_candidates"] == 6
    assert r["relevance_signals"] == 42
    assert r["selected_results"] == 5
    assert r["omitted_candidates"] == 1
    assert r["top_result_rank"] == 1
    assert r["top_result_memory_ref"] == "memory:continuity:actor-ministry-agency"
    assert r["top_result_relevance_score"] == pytest.approx(0.99)
    assert r["results_with_qualifications"] == 5
    assert r["results_with_unresolved_context"] == 4
    assert r["deterministic_reference_ranking_is_model_performance_claim"] is False


def test_contract_boundaries_are_explicit():
    b = contract_document()["boundaries"]
    assert b["retrieval_rank_establishes_truth"] is False
    assert b["relevance_score_is_evidence_weight"] is False
    assert b["semantic_similarity_establishes_equivalence"] is False
    assert b["scope_proximity_establishes_authority"] is False
    assert b["provenance_completeness_establishes_credibility"] is False
    assert b["retrieval_mutates_memory"] is False
    assert b["identity_graph_mutation_performed"] is False
    assert b["evidence_graph_mutation_performed"] is False


def test_contract_roadmap_prepares_reasoning_line():
    r = contract_document()["roadmap_integration"]
    assert r["extends_v4110_contextual_memory_semantic_state"] is True
    assert r["prepares_v4130_claim_alignment_contradiction_intelligence"] is True
    assert r["prepares_v4140_evidence_context_integration"] is True
    assert r["prepares_v4200_unified_contextual_reasoning_runtime"] is True


def test_api_functions_are_directly_callable():
    assert api.contract()["release"] == "4.12.0"
    assert api.public_contract()["contract"] == "sc.core.context-retrieval-relevance-intelligence.v1"
    assert api.reference_query()["query"]["max_results"] == 5
    assert api.reference_candidates()["count"] == 6
    assert len(api.reference_results()["result_set"]["results"]) == 5


def test_bad_query_scope_fails():
    invalid(lambda p: p["queries"][0]["requested_scope_refs"].__setitem__(0, "memory-scope:missing"))


def test_bad_query_qualification_fails():
    invalid(lambda p: p["queries"][0]["qualification_refs"].__setitem__(0, "qualification:missing"))


def test_bad_signal_candidate_fails():
    invalid(lambda p: p["signals"][0].__setitem__("candidate_ref", "retrieval-candidate:missing"))


def test_bad_signal_contribution_fails():
    invalid(lambda p: p["signals"][0].__setitem__("contribution", 0.123456))


def test_bad_candidate_revision_fails():
    invalid(lambda p: p["candidates"][0].__setitem__("revision_ref", "memory-revision:missing"))


def test_bad_candidate_score_fails():
    invalid(lambda p: p["candidates"][0].__setitem__("aggregate_relevance_score", 0.1))


def test_dropping_unresolved_context_fails():
    cidx = next(i for i, c in enumerate(payload()["candidates"]) if c["memory_ref"] == "memory:continuity:actor-ministry-agency")
    invalid(lambda p: p["candidates"][cidx].__setitem__("unresolved_refs", []))


def test_noncontiguous_result_rank_fails():
    invalid(lambda p: p["result_sets"][0]["results"][1].__setitem__("rank", 4))


def test_result_score_must_match_candidate_fails():
    invalid(lambda p: p["result_sets"][0]["results"][0].__setitem__("relevance_score", 0.2))


def test_result_qualification_loss_fails():
    invalid(lambda p: p["result_sets"][0]["results"][0].__setitem__("qualification_refs", []))


def test_bad_snapshot_predecessor_fingerprint_fails():
    invalid(lambda p: p["snapshots"][0].__setitem__("predecessor_memory_fingerprint_sha256", "0" * 64))


def test_database_migration_is_none():
    assert ref().database_migration == "none"
    assert contract_document()["database_migration"] == "none"


def test_main_mounts_v412_routers():
    from app.main import create_app
    app = create_app()
    paths = {r.path for r in app.routes}
    assert "/v1/context-retrieval/contract" in paths
    assert "/public/v1/context-retrieval/contract" in paths
