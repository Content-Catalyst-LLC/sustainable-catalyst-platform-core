from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.routers import contextual_semantic_evaluation as api
from app.services.contextual_semantic_evaluation import (
    BenchmarkReviewState,
    ContextualSemanticEvaluationBenchmarkBundle,
    ErrorCategory,
    EvaluationPrediction,
    EvaluationStatus,
    EvaluationTask,
    contract_document,
    evaluate_prediction,
    reference_contextual_semantic_evaluation_bundle,
)


def ref():
    return reference_contextual_semantic_evaluation_bundle()


def payload():
    return ref().model_dump(mode="json")


def invalid(mutator):
    p = payload(); mutator(p)
    with pytest.raises((ValidationError, ValueError)):
        ContextualSemanticEvaluationBenchmarkBundle.model_validate(p)


def test_release_identity():
    assert Settings().version == "4.9.0"
    assert ref().release == "4.9.0"
    assert ref().contract == "sc.core.contextual-semantic-evaluation-benchmark-framework.v1"
    assert ref().predecessor_contract == "sc.core.multilingual-context-semantic-alignment.v1"


def test_v48_predecessor_is_preserved():
    assert ref().multilingual_context.release == "4.8.0"
    assert ref().multilingual_context.contract == "sc.core.multilingual-context-semantic-alignment.v1"


def test_reference_suite_has_twelve_cases_and_all_task_families():
    assert len(ref().benchmark_cases) == 12
    assert {x.task for x in ref().benchmark_cases} == set(EvaluationTask)


def test_reference_metrics_cover_contextual_semantic_dimensions():
    names = {x.name for x in ref().metric_definitions}
    assert "Context Resolution Accuracy" in names
    assert "Entity Reference Accuracy" in names
    assert "Temporal Grounding Accuracy" in names
    assert "Spatial Grounding Accuracy" in names
    assert "Discourse Relation Accuracy" in names
    assert "Epistemic Classification Accuracy" in names
    assert "Cross-Language Meaning Preservation" in names
    assert "Context Graph Consistency" in names
    assert "Ambiguity Preservation Accuracy" in names


def test_gold_annotations_are_reviewed_targets_not_truth():
    assert all(x.review_state == BenchmarkReviewState.reviewed for x in ref().gold_annotations)
    assert all(x.annotation_is_benchmark_target_not_world_truth for x in ref().gold_annotations)


def test_original_language_cases_are_explicit():
    xs = [x for x in ref().benchmark_cases if x.original_language_required]
    assert len(xs) == 3
    assert all("language:zh" in x.language_refs for x in xs)


def test_coreference_case_scores_ambiguity_preservation():
    c = next(x for x in ref().benchmark_cases if x.case_id == "benchmark:coreference-it-proposal")
    assert c.ambiguity_is_scored is True
    assert "metric:ambiguity-preservation" in c.metric_refs


def test_cross_document_case_forbids_identity_merge():
    g = next(x for x in ref().gold_annotations if x.case_ref == "benchmark:cross-document-actor-continuity")
    assert g.expected_outcome["canonical_actor_merge"] is False
    assert g.expected_outcome["unresolved_identity_preserved"] is True


def test_cross_language_case_preserves_original_authority():
    g = next(x for x in ref().gold_annotations if x.case_ref == "benchmark:cross-language-proposal-modality")
    assert g.expected_outcome["original_language_authoritative"] is True
    assert g.expected_outcome["modality_preserved"] == "possibility"


def test_governance_case_rejects_exact_equivalence():
    g = next(x for x in ref().gold_annotations if x.case_ref == "benchmark:governance-cultural-divergence")
    assert g.expected_outcome["relation"] == "culturally-conditioned"
    assert g.expected_outcome["exact_equivalence"] is False


def test_reference_predictions_all_score_one_without_truth_claim():
    assert len(ref().predictions) == 12
    assert all(x.prediction_is_interpretation_not_truth_verdict for x in ref().predictions)
    assert all(x.score == 1.0 and x.status == EvaluationStatus.pass_ for x in ref().case_evaluations)


def test_wrong_prediction_produces_error_category():
    c = next(x for x in ref().benchmark_cases if x.task == EvaluationTask.coreference_resolution)
    g = next(x for x in ref().gold_annotations if x.case_ref == c.case_id)
    p = EvaluationPrediction(prediction_id="prediction:test:wrong", case_ref=c.case_id, system_ref="system:test", predicted_outcome={"referent_ref":"referent:estimate"}, confidence=0.2, provenance_ref="prov:test")
    ev = evaluate_prediction(c,g,p)
    assert ev.status in {EvaluationStatus.partial, EvaluationStatus.fail}
    assert ErrorCategory.wrong_referent in ev.error_categories
    assert ev.evaluation_does_not_establish_claim_truth is True


def test_all_metric_results_are_reproducible_reference_fixture_scores():
    assert len(ref().metric_results) == len(ref().metric_definitions)
    assert all(x.score == 1.0 for x in ref().metric_results)
    assert all(x.score_is_benchmark_measure_not_truth_probability for x in ref().metric_results)


def test_reference_run_is_not_safety_or_truth_claim():
    run = ref().evaluation_runs[0]
    assert run.overall_score == 1.0
    assert run.reproducible is True
    assert run.run_does_not_establish_system_truthfulness_or_safety is True


def test_policy_boundaries_are_strict():
    p = ref().policy
    assert p.benchmark_pass_does_not_establish_claim_truth is True
    assert p.benchmark_pass_does_not_establish_evidence_validity is True
    assert p.benchmark_score_does_not_establish_model_safety is True
    assert p.unresolved_ambiguity_may_be_correct_behavior is True
    assert p.context_graph_mutation_authorized is False
    assert p.identity_graph_mutation_authorized is False
    assert p.evidence_graph_mutation_authorized is False
    assert p.knowledge_graph_mutation_authorized is False


def test_contract_boundaries_are_explicit():
    b = contract_document()["boundaries"]
    assert b["benchmark_pass_establishes_claim_truth"] is False
    assert b["benchmark_pass_establishes_evidence_validity"] is False
    assert b["benchmark_score_is_probability_of_truth"] is False
    assert b["benchmark_score_establishes_model_safety"] is False
    assert b["evaluation_run_mutates_v480_predecessor"] is False


def test_contract_reference_counts():
    r = contract_document()["reference"]
    assert r["predecessor_release"] == "4.8.0"
    assert r["benchmark_cases"] == 12
    assert r["gold_annotations"] == 12
    assert r["metric_definitions"] == 11
    assert r["predictions"] == 12
    assert r["case_evaluations"] == 12
    assert r["failed_reference_cases"] == 0
    assert r["partial_reference_cases"] == 0
    assert r["context_graph_mutations_created"] == 0


def test_snapshot_matches_predecessor_fingerprint():
    s=ref().benchmark_snapshots[0]
    assert s.predecessor_fingerprint_sha256 == ref().multilingual_context.fingerprint()
    assert s.snapshot_does_not_freeze_semantic_truth is True


def test_snapshot_bad_predecessor_fingerprint_fails():
    invalid(lambda p: p["benchmark_snapshots"][0].__setitem__("predecessor_fingerprint_sha256", "0"*64))


def test_case_gold_ref_must_resolve():
    invalid(lambda p: p["benchmark_cases"][0].__setitem__("gold_annotation_ref", "gold:missing"))


def test_case_metric_ref_must_resolve():
    invalid(lambda p: p["benchmark_cases"][0]["metric_refs"].append("metric:missing"))


def test_prediction_case_ref_must_resolve():
    invalid(lambda p: p["predictions"][0].__setitem__("case_ref", "benchmark:missing"))


def test_evaluation_prediction_must_match_case():
    invalid(lambda p: p["case_evaluations"][0].__setitem__("prediction_ref", p["predictions"][1]["prediction_id"]))


def test_metric_result_case_ref_must_resolve():
    invalid(lambda p: p["metric_results"][0]["case_refs"].append("benchmark:missing"))


def test_run_snapshot_ref_must_resolve():
    invalid(lambda p: p["evaluation_runs"][0].__setitem__("benchmark_snapshot_ref", "snapshot:missing"))


def test_bundle_fingerprint_is_deterministic():
    assert ref().fingerprint() == reference_contextual_semantic_evaluation_bundle().fingerprint()


def test_api_contract_functions_are_directly_callable():
    assert api.contract()["release"] == "4.9.0"
    assert api.public_contract()["contract"] == "sc.core.contextual-semantic-evaluation-benchmark-framework.v1"
    assert api.reference_cases()["count"] == 12
    assert api.reference_metrics()["count"] == 11
    assert api.reference_run()["run"]["overall_score"] == 1.0


def test_main_mounts_v49_routers():
    from app.main import create_app
    app=create_app()
    paths={r.path for r in app.routes}
    assert "/v1/context-evaluation/contract" in paths
    assert "/public/v1/context-evaluation/contract" in paths
