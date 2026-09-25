from copy import deepcopy
import pytest
from pydantic import ValidationError

from app.services.ai_calibration_drift_risk import (
    CONTRACT_VERSION,
    CalibrationAssessment,
    CalibrationBin,
    CalibrationMetricResult,
    CalibrationMethod,
    CalibrationDriftRiskBundle,
    DriftDomain,
    DriftMethod,
    DriftObservation,
    DriftSeverity,
    DriftSignalDefinition,
    MonitoringPolicy,
    MonitoringSnapshot,
    MonitoringState,
    MonitoringWindow,
    RiskCategory,
    RiskIndicatorDefinition,
    RiskLevel,
    RiskObservation,
    contract_document,
    reference_calibration_drift_risk_bundle,
)


def test_contract_declares_v334_system():
    doc = contract_document()
    assert doc["release"] == "3.34.0"
    assert doc["contract"] == CONTRACT_VERSION
    assert doc["boundaries"]["core_executes_monitoring_jobs"] is False
    assert doc["boundaries"]["core_autonomously_retrains_models"] is False


def test_reference_bundle_is_valid():
    bundle = reference_calibration_drift_risk_bundle()
    assert len(bundle.windows) == 2
    assert bundle.calibration_assessments
    assert bundle.drift_signals
    assert bundle.drift_observations
    assert bundle.risk_indicators
    assert bundle.risk_observations
    assert bundle.monitoring_snapshots


def test_calibration_bin_rejects_reversed_bounds():
    with pytest.raises(ValidationError):
        CalibrationBin(
            bin_id="bin:test",
            lower_bound=0.8,
            upper_bound=0.2,
            sample_count=10,
            mean_confidence=0.5,
            observed_frequency=0.5,
            absolute_gap=0.0,
        )


def test_calibration_bin_fingerprint_is_stable():
    item = reference_calibration_drift_risk_bundle().calibration_assessments[0].bins[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_calibration_metric_ci_requires_two_values():
    with pytest.raises(ValidationError):
        CalibrationMetricResult(
            metric_id="calibration-metric:test",
            method=CalibrationMethod.brier_score,
            value=0.1,
            confidence_interval=[0.05],
        )


def test_calibration_metric_ci_bounds_ordered():
    with pytest.raises(ValidationError):
        CalibrationMetricResult(
            metric_id="calibration-metric:test",
            method=CalibrationMethod.brier_score,
            value=0.1,
            confidence_interval=[0.2, 0.1],
        )


def test_calibration_assessment_requires_model_version():
    item = reference_calibration_drift_risk_bundle().calibration_assessments[0]
    data = item.model_dump(mode="python")
    data["ai_model_version_ref"] = "model-version:test"
    with pytest.raises(ValidationError):
        CalibrationAssessment.model_validate(data)


def test_calibration_assessment_requires_metric_results():
    item = reference_calibration_drift_risk_bundle().calibration_assessments[0]
    data = item.model_dump(mode="python")
    data["metric_results"] = []
    with pytest.raises(ValidationError):
        CalibrationAssessment.model_validate(data)


def test_calibration_assessment_rejects_duplicate_bins():
    item = reference_calibration_drift_risk_bundle().calibration_assessments[0]
    data = item.model_dump(mode="python")
    data["bins"] = [data["bins"][0], deepcopy(data["bins"][0])]
    with pytest.raises(ValidationError):
        CalibrationAssessment.model_validate(data)


def test_calibration_assessment_rejects_duplicate_metrics():
    item = reference_calibration_drift_risk_bundle().calibration_assessments[0]
    data = item.model_dump(mode="python")
    data["metric_results"] = [
        data["metric_results"][0],
        deepcopy(data["metric_results"][0]),
    ]
    with pytest.raises(ValidationError):
        CalibrationAssessment.model_validate(data)


def test_calibration_assessment_fingerprint_ignores_created_at():
    item = reference_calibration_drift_risk_bundle().calibration_assessments[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()
    assert len(item.fingerprint()) == 64


def test_monitoring_window_requires_positive_interval():
    bundle = reference_calibration_drift_risk_bundle()
    w = bundle.windows[0]
    data = w.model_dump(mode="python")
    data["end_at"] = data["start_at"]
    with pytest.raises(ValidationError):
        MonitoringWindow.model_validate(data)


def test_monitoring_window_fingerprint_is_stable():
    w = reference_calibration_drift_risk_bundle().windows[0]
    assert w.fingerprint() == deepcopy(w).fingerprint()


def test_drift_signal_warning_not_above_critical_for_higher_is_worse():
    with pytest.raises(ValidationError):
        DriftSignalDefinition(
            drift_signal_id="drift:test",
            name="Test",
            domain=DriftDomain.input,
            method=DriftMethod.jensen_shannon,
            baseline_ref="window:test",
            warning_threshold=0.4,
            critical_threshold=0.2,
            direction="higher-is-worse",
        )


def test_drift_signal_sha256_is_validated():
    with pytest.raises(ValidationError):
        DriftSignalDefinition(
            drift_signal_id="drift:test",
            name="Test",
            domain=DriftDomain.input,
            method=DriftMethod.custom,
            baseline_ref="window:test",
            implementation_sha256="abc",
        )


def test_drift_signal_fingerprint_is_stable():
    signal = reference_calibration_drift_risk_bundle().drift_signals[0]
    assert signal.fingerprint() == deepcopy(signal).fingerprint()


def test_drift_observation_requires_model_version():
    item = reference_calibration_drift_risk_bundle().drift_observations[0]
    data = item.model_dump(mode="python")
    data["ai_model_version_ref"] = "model-version:test"
    with pytest.raises(ValidationError):
        DriftObservation.model_validate(data)


def test_drift_observation_windows_must_differ():
    item = reference_calibration_drift_risk_bundle().drift_observations[0]
    data = item.model_dump(mode="python")
    data["comparison_window_ref"] = data["baseline_window_ref"]
    with pytest.raises(ValidationError):
        DriftObservation.model_validate(data)


def test_drift_observation_fingerprint_ignores_created_at():
    item = reference_calibration_drift_risk_bundle().drift_observations[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_risk_indicator_warning_not_above_critical():
    with pytest.raises(ValidationError):
        RiskIndicatorDefinition(
            risk_indicator_id="risk:test",
            name="Test",
            category=RiskCategory.drift,
            description="test",
            source_ref_kind="drift",
            warning_threshold=0.5,
            critical_threshold=0.2,
            direction="higher-is-worse",
        )


def test_risk_indicator_fingerprint_is_stable():
    item = reference_calibration_drift_risk_bundle().risk_indicators[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_risk_observation_requires_model_version():
    item = reference_calibration_drift_risk_bundle().risk_observations[0]
    data = item.model_dump(mode="python")
    data["ai_model_version_ref"] = "model-version:test"
    with pytest.raises(ValidationError):
        RiskObservation.model_validate(data)


def test_risk_observation_requires_source_or_evidence():
    with pytest.raises(ValidationError):
        RiskObservation(
            risk_observation_id="risk-observation:test",
            risk_indicator_ref="risk:test",
            ai_model_version_ref="ai-model-version:test:1",
            observed_value=1.0,
            risk_level=RiskLevel.high,
        )


def test_risk_observation_fingerprint_ignores_acknowledged():
    item = reference_calibration_drift_risk_bundle().risk_observations[0]
    other = deepcopy(item)
    other.acknowledged = True
    assert item.fingerprint() == other.fingerprint()


def test_monitoring_policy_requires_model_version():
    policy = reference_calibration_drift_risk_bundle().monitoring_policy
    data = policy.model_dump(mode="python")
    data["ai_model_version_ref"] = "model-version:test"
    with pytest.raises(ValidationError):
        MonitoringPolicy.model_validate(data)


def test_monitoring_policy_requires_at_least_one_signal():
    with pytest.raises(ValidationError):
        MonitoringPolicy(
            monitoring_policy_id="policy:test",
            name="Test",
            ai_model_version_ref="ai-model-version:test:1",
        )


def test_monitoring_policy_fingerprint_ignores_state():
    policy = reference_calibration_drift_risk_bundle().monitoring_policy
    other = deepcopy(policy)
    other.state = MonitoringState.paused
    assert policy.fingerprint() == other.fingerprint()


def test_monitoring_snapshot_requires_model_version():
    snapshot = reference_calibration_drift_risk_bundle().monitoring_snapshots[0]
    data = snapshot.model_dump(mode="python")
    data["ai_model_version_ref"] = "model-version:test"
    with pytest.raises(ValidationError):
        MonitoringSnapshot.model_validate(data)


def test_monitoring_snapshot_requires_evidence():
    with pytest.raises(ValidationError):
        MonitoringSnapshot(
            monitoring_snapshot_id="snapshot:test",
            monitoring_policy_ref="policy:test",
            ai_model_version_ref="ai-model-version:test:1",
            monitoring_window_ref="window:test",
        )


def test_monitoring_snapshot_fingerprint_is_stable():
    snapshot = reference_calibration_drift_risk_bundle().monitoring_snapshots[0]
    assert snapshot.fingerprint() == deepcopy(snapshot).fingerprint()


def test_bundle_rejects_missing_baseline_window():
    bundle = reference_calibration_drift_risk_bundle()
    with pytest.raises(ValidationError):
        CalibrationDriftRiskBundle(
            windows=[bundle.windows[1]],
            calibration_assessments=bundle.calibration_assessments,
            drift_signals=bundle.drift_signals,
            drift_observations=bundle.drift_observations,
            risk_indicators=bundle.risk_indicators,
            risk_observations=bundle.risk_observations,
            monitoring_policy=bundle.monitoring_policy,
            monitoring_snapshots=bundle.monitoring_snapshots,
        )


def test_bundle_rejects_unknown_drift_signal():
    bundle = reference_calibration_drift_risk_bundle()
    observation = deepcopy(bundle.drift_observations[0])
    observation.drift_signal_ref = "drift-signal:missing"
    with pytest.raises(ValidationError):
        CalibrationDriftRiskBundle(
            windows=bundle.windows,
            calibration_assessments=bundle.calibration_assessments,
            drift_signals=bundle.drift_signals,
            drift_observations=[observation],
            risk_indicators=bundle.risk_indicators,
            risk_observations=bundle.risk_observations,
            monitoring_policy=bundle.monitoring_policy,
            monitoring_snapshots=bundle.monitoring_snapshots,
        )


def test_bundle_rejects_unknown_risk_indicator():
    bundle = reference_calibration_drift_risk_bundle()
    observation = deepcopy(bundle.risk_observations[0])
    observation.risk_indicator_ref = "risk-indicator:missing"
    with pytest.raises(ValidationError):
        CalibrationDriftRiskBundle(
            windows=bundle.windows,
            calibration_assessments=bundle.calibration_assessments,
            drift_signals=bundle.drift_signals,
            drift_observations=bundle.drift_observations,
            risk_indicators=bundle.risk_indicators,
            risk_observations=[observation],
            monitoring_policy=bundle.monitoring_policy,
            monitoring_snapshots=bundle.monitoring_snapshots,
        )


def test_bundle_fingerprint_is_stable():
    bundle = reference_calibration_drift_risk_bundle()
    assert bundle.fingerprint() == deepcopy(bundle).fingerprint()
    assert len(bundle.fingerprint()) == 64


def test_reference_calibration_detects_ece_threshold_failure():
    assessment = reference_calibration_drift_risk_bundle().calibration_assessments[0]
    ece = [x for x in assessment.metric_results if x.metric_id == "calibration-metric:ece"][0]
    assert ece.value == 0.06
    assert ece.passed is False


def test_reference_drift_crosses_warning_not_critical():
    bundle = reference_calibration_drift_risk_bundle()
    signal = bundle.drift_signals[0]
    observation = bundle.drift_observations[0]
    assert observation.observed_value == 0.14
    assert observation.observed_value > signal.warning_threshold
    assert observation.observed_value < signal.critical_threshold
    assert observation.severity == DriftSeverity.moderate


def test_reference_high_risk_is_robustness_linked():
    bundle = reference_calibration_drift_risk_bundle()
    high = [x for x in bundle.risk_observations if x.risk_level == RiskLevel.high]
    assert len(high) == 1
    assert "robustness-run:reference-classifier-noise:001" in high[0].source_object_refs


def test_reference_snapshot_integrates_v333_objects():
    snapshot = reference_calibration_drift_risk_bundle().monitoring_snapshots[0]
    assert snapshot.robustness_run_refs
    assert snapshot.error_analysis_report_refs
    assert snapshot.overall_risk_level == RiskLevel.high


def test_reference_policy_does_not_claim_core_scheduler():
    policy = reference_calibration_drift_risk_bundle().monitoring_policy
    assert policy.provenance["core_performs_scheduling"] is False
    assert policy.schedule_hint == "daily"


def test_core_does_not_schedule_or_retrain():
    doc = contract_document()
    assert doc["integration"]["core_performs_background_scheduling"] is False
    assert doc["boundaries"]["core_executes_monitoring_jobs"] is False
    assert doc["boundaries"]["core_autonomously_retrains_models"] is False


def test_core_does_not_certify_safety_or_readiness():
    doc = contract_document()
    assert doc["boundaries"]["core_certifies_model_safety"] is False
    assert doc["boundaries"]["core_certifies_operational_readiness"] is False


def test_core_does_not_duplicate_robustness_or_evaluation_storage():
    doc = contract_document()
    assert doc["integration"]["core_duplicates_robustness_storage"] is False
    assert doc["integration"]["core_duplicates_evaluation_storage"] is False


def test_contract_links_v333_error_robustness():
    doc = contract_document()
    assert "sc.core.ai-error-robustness.v1" in doc["depends_on"]


def test_reference_window_samples_are_recorded():
    bundle = reference_calibration_drift_risk_bundle()
    assert all(window.sample_count == 1000 for window in bundle.windows)


def test_reference_risk_indicators_cover_calibration_drift_robustness():
    bundle = reference_calibration_drift_risk_bundle()
    categories = {item.category for item in bundle.risk_indicators}
    assert RiskCategory.calibration in categories
    assert RiskCategory.drift in categories
    assert RiskCategory.robustness in categories
