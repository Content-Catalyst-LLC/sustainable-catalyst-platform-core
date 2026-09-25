from copy import deepcopy
import pytest
from pydantic import ValidationError

from app.services.ai_error_robustness import (
    CONTRACT_VERSION,
    AIRobustnessFailureBundle,
    ErrorAnalysisReport,
    ErrorDisposition,
    ErrorObservation,
    EvaluationSliceDefinition,
    FailureCluster,
    FailureDomain,
    FailureModeDefinition,
    FailureSeverity,
    FailureTaxonomy,
    RobustnessPerturbation,
    RobustnessRun,
    RobustnessTestDefinition,
    RobustnessTestKind,
    RobustnessTrialResult,
    SliceMetricResult,
    SlicePerformanceResult,
    contract_document,
    reference_robustness_failure_bundle,
)


def test_contract_declares_v333_system():
    doc = contract_document()
    assert doc["release"] == "3.33.0"
    assert doc["contract"] == CONTRACT_VERSION
    assert doc["boundaries"]["core_executes_robustness_tests"] is False
    assert doc["boundaries"]["core_certifies_model_robustness"] is False


def test_reference_bundle_is_valid():
    bundle = reference_robustness_failure_bundle()
    assert bundle.failure_taxonomy.failure_modes
    assert bundle.error_observations
    assert bundle.robustness_tests
    assert bundle.robustness_runs
    assert bundle.error_analysis_report


def test_failure_mode_fingerprint_is_stable():
    mode = reference_robustness_failure_bundle().failure_taxonomy.failure_modes[0]
    assert mode.fingerprint() == deepcopy(mode).fingerprint()
    assert len(mode.fingerprint()) == 64


def test_failure_mode_rejects_self_parent():
    with pytest.raises(ValidationError):
        FailureModeDefinition(
            failure_mode_id="failure-mode:test",
            name="Test",
            domain=FailureDomain.model,
            description="test",
            parent_failure_mode_ref="failure-mode:test",
        )


def test_taxonomy_rejects_duplicate_mode_ids():
    mode = FailureModeDefinition(
        failure_mode_id="failure-mode:test",
        name="Test",
        domain=FailureDomain.model,
        description="test",
    )
    with pytest.raises(ValidationError):
        FailureTaxonomy(
            failure_taxonomy_id="taxonomy:test",
            name="Test",
            version="1",
            failure_modes=[mode, deepcopy(mode)],
        )


def test_taxonomy_rejects_unknown_parent():
    mode = FailureModeDefinition(
        failure_mode_id="failure-mode:child",
        name="Child",
        domain=FailureDomain.model,
        description="child",
        parent_failure_mode_ref="failure-mode:missing",
    )
    with pytest.raises(ValidationError):
        FailureTaxonomy(
            failure_taxonomy_id="taxonomy:test",
            name="Test",
            version="1",
            failure_modes=[mode],
        )


def test_taxonomy_fingerprint_ignores_created_at():
    taxonomy = reference_robustness_failure_bundle().failure_taxonomy
    assert taxonomy.fingerprint() == deepcopy(taxonomy).fingerprint()


def test_error_observation_requires_ai_model_version():
    bundle = reference_robustness_failure_bundle()
    data = bundle.error_observations[0].model_dump(mode="python")
    data["ai_model_version_ref"] = "model-version:test"
    with pytest.raises(ValidationError):
        ErrorObservation.model_validate(data)


def test_error_observation_requires_evidence_link():
    with pytest.raises(ValidationError):
        ErrorObservation(
            error_observation_id="error:test",
            failure_mode_ref="failure-mode:test",
            severity=FailureSeverity.high,
            ai_model_version_ref="ai-model-version:test:1",
            observed_behavior="failure",
        )


def test_error_observation_fingerprint_ignores_disposition():
    observation = reference_robustness_failure_bundle().error_observations[0]
    other = deepcopy(observation)
    other.disposition = ErrorDisposition.mitigated
    assert observation.fingerprint() == other.fingerprint()


def test_slice_definition_fingerprint_is_stable():
    slice_def = reference_robustness_failure_bundle().slice_definitions[0]
    assert slice_def.fingerprint() == deepcopy(slice_def).fingerprint()


def test_slice_metric_ci_requires_two_bounds():
    with pytest.raises(ValidationError):
        SliceMetricResult(
            metric_ref="metric:test",
            value=0.5,
            confidence_interval=[0.4],
        )


def test_slice_metric_ci_ordered():
    with pytest.raises(ValidationError):
        SliceMetricResult(
            metric_ref="metric:test",
            value=0.5,
            confidence_interval=[0.7, 0.4],
        )


def test_slice_result_rejects_duplicate_metric_refs():
    metric = SliceMetricResult(metric_ref="metric:test", value=0.5)
    with pytest.raises(ValidationError):
        SlicePerformanceResult(
            slice_result_id="slice-result:test",
            slice_ref="slice:test",
            evaluation_run_ref="evaluation-run:test",
            ai_model_version_ref="ai-model-version:test:1",
            metric_results=[metric, deepcopy(metric)],
        )


def test_slice_result_fingerprint_is_stable():
    result = reference_robustness_failure_bundle().slice_results[0]
    assert result.fingerprint() == deepcopy(result).fingerprint()


def test_perturbation_hash_is_validated():
    with pytest.raises(ValidationError):
        RobustnessPerturbation(
            perturbation_id="perturbation:test",
            name="Test",
            test_kind=RobustnessTestKind.noise,
            target="input",
            implementation_sha256="abc",
        )


def test_perturbation_fingerprint_is_stable():
    p = reference_robustness_failure_bundle().robustness_tests[0].perturbations[0]
    assert p.fingerprint() == deepcopy(p).fingerprint()


def test_robustness_test_requires_perturbation():
    with pytest.raises(ValidationError):
        RobustnessTestDefinition(
            robustness_test_id="robustness-test:test",
            name="Test",
            benchmark_ref="benchmark:test",
            baseline_evaluation_run_ref="evaluation-run:test",
            perturbations=[],
            metric_refs=["metric:test"],
        )


def test_robustness_test_requires_metrics():
    perturbation = RobustnessPerturbation(
        perturbation_id="perturbation:test",
        name="Test",
        test_kind=RobustnessTestKind.noise,
        target="input",
    )
    with pytest.raises(ValidationError):
        RobustnessTestDefinition(
            robustness_test_id="robustness-test:test",
            name="Test",
            benchmark_ref="benchmark:test",
            baseline_evaluation_run_ref="evaluation-run:test",
            perturbations=[perturbation],
            metric_refs=[],
        )


def test_robustness_test_rejects_duplicate_perturbations():
    p = RobustnessPerturbation(
        perturbation_id="perturbation:test",
        name="Test",
        test_kind=RobustnessTestKind.noise,
        target="input",
    )
    with pytest.raises(ValidationError):
        RobustnessTestDefinition(
            robustness_test_id="robustness-test:test",
            name="Test",
            benchmark_ref="benchmark:test",
            baseline_evaluation_run_ref="evaluation-run:test",
            perturbations=[p, deepcopy(p)],
            metric_refs=["metric:test"],
        )


def test_robustness_test_fingerprint_is_stable():
    test = reference_robustness_failure_bundle().robustness_tests[0]
    assert test.fingerprint() == deepcopy(test).fingerprint()


def test_robustness_run_requires_ai_model_version():
    run = reference_robustness_failure_bundle().robustness_runs[0]
    data = run.model_dump(mode="python")
    data["ai_model_version_ref"] = "model-version:test"
    with pytest.raises(ValidationError):
        RobustnessRun.model_validate(data)


def test_robustness_run_requires_jobs():
    run = reference_robustness_failure_bundle().robustness_runs[0]
    data = run.model_dump(mode="python")
    data["computational_job_refs"] = []
    with pytest.raises(ValidationError):
        RobustnessRun.model_validate(data)


def test_robustness_run_requires_environment():
    run = reference_robustness_failure_bundle().robustness_runs[0]
    data = run.model_dump(mode="python")
    data["runtime_environment_refs"] = []
    with pytest.raises(ValidationError):
        RobustnessRun.model_validate(data)


def test_robustness_run_requires_trials():
    run = reference_robustness_failure_bundle().robustness_runs[0]
    data = run.model_dump(mode="python")
    data["trial_results"] = []
    with pytest.raises(ValidationError):
        RobustnessRun.model_validate(data)


def test_robustness_run_fingerprint_ignores_created_at():
    run = reference_robustness_failure_bundle().robustness_runs[0]
    assert run.fingerprint() == deepcopy(run).fingerprint()


def test_failure_cluster_requires_observations():
    with pytest.raises(ValidationError):
        FailureCluster(
            failure_cluster_id="cluster:test",
            name="Test",
            error_observation_refs=[],
        )


def test_failure_cluster_fingerprint_is_stable():
    cluster = reference_robustness_failure_bundle().failure_clusters[0]
    assert cluster.fingerprint() == deepcopy(cluster).fingerprint()


def test_report_requires_errors_or_robustness():
    with pytest.raises(ValidationError):
        ErrorAnalysisReport(
            error_analysis_report_id="report:test",
            ai_model_version_ref="ai-model-version:test:1",
            summary="test",
        )


def test_report_fingerprint_ignores_created_at():
    report = reference_robustness_failure_bundle().error_analysis_report
    assert report.fingerprint() == deepcopy(report).fingerprint()


def test_bundle_rejects_observation_outside_taxonomy():
    bundle = reference_robustness_failure_bundle()
    observation = deepcopy(bundle.error_observations[0])
    observation.failure_mode_ref = "failure-mode:outside"
    with pytest.raises(ValidationError):
        AIRobustnessFailureBundle(
            failure_taxonomy=bundle.failure_taxonomy,
            error_observations=[observation],
            slice_definitions=bundle.slice_definitions,
            slice_results=bundle.slice_results,
            robustness_tests=bundle.robustness_tests,
            robustness_runs=bundle.robustness_runs,
            failure_clusters=[],
            error_analysis_report=deepcopy(bundle.error_analysis_report),
        )


def test_bundle_rejects_cluster_observation_outside_bundle():
    bundle = reference_robustness_failure_bundle()
    cluster = deepcopy(bundle.failure_clusters[0])
    cluster.error_observation_refs = ["error-observation:missing"]
    with pytest.raises(ValidationError):
        AIRobustnessFailureBundle(
            failure_taxonomy=bundle.failure_taxonomy,
            error_observations=bundle.error_observations,
            slice_definitions=bundle.slice_definitions,
            slice_results=bundle.slice_results,
            robustness_tests=bundle.robustness_tests,
            robustness_runs=bundle.robustness_runs,
            failure_clusters=[cluster],
            error_analysis_report=bundle.error_analysis_report,
        )


def test_bundle_rejects_unknown_robustness_test_ref():
    bundle = reference_robustness_failure_bundle()
    run = deepcopy(bundle.robustness_runs[0])
    run.robustness_test_ref = "robustness-test:missing"
    with pytest.raises(ValidationError):
        AIRobustnessFailureBundle(
            failure_taxonomy=bundle.failure_taxonomy,
            error_observations=bundle.error_observations,
            slice_definitions=bundle.slice_definitions,
            slice_results=bundle.slice_results,
            robustness_tests=bundle.robustness_tests,
            robustness_runs=[run],
            failure_clusters=bundle.failure_clusters,
            error_analysis_report=bundle.error_analysis_report,
        )


def test_bundle_fingerprint_is_stable():
    bundle = reference_robustness_failure_bundle()
    assert bundle.fingerprint() == deepcopy(bundle).fingerprint()
    assert len(bundle.fingerprint()) == 64


def test_reference_slice_records_degradation():
    result = reference_robustness_failure_bundle().slice_results[0]
    metric = result.metric_results[0]
    assert metric.delta == -0.13
    assert metric.passed is False


def test_reference_robustness_run_fails_recall_tolerance():
    run = reference_robustness_failure_bundle().robustness_runs[0]
    assert run.overall_passed is False
    recall = [x for x in run.trial_results[0].metric_results if x.metric_ref == "metric:recall"][0]
    assert recall.passed is False


def test_reference_error_links_evaluation_and_inference():
    observation = reference_robustness_failure_bundle().error_observations[0]
    assert observation.evaluation_run_ref is not None
    assert observation.inference_run_ref is not None
    assert observation.ai_artifact_refs


def test_reference_report_preserves_limitations():
    report = reference_robustness_failure_bundle().error_analysis_report
    assert len(report.limitations) >= 1
    assert report.provenance["core_certifies_robustness"] is False


def test_core_does_not_certify_or_autonomously_diagnose():
    doc = contract_document()
    assert doc["boundaries"]["core_diagnoses_causality_autonomously"] is False
    assert doc["boundaries"]["core_certifies_model_robustness"] is False
    assert doc["boundaries"]["core_certifies_model_safety"] is False


def test_core_does_not_duplicate_existing_evaluation_or_inference_storage():
    doc = contract_document()
    assert doc["integration"]["core_duplicates_evaluation_storage"] is False
    assert doc["integration"]["core_duplicates_inference_artifacts"] is False
