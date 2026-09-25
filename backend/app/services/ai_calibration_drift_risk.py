from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.34.0"
CONTRACT_VERSION = "sc.core.ai-calibration-drift-risk.v1"

AI_MODEL_CONTRACT_VERSION = "sc.core.ai-model.v1"
AI_INFERENCE_CONTRACT_VERSION = "sc.core.ai-inference-provenance.v1"
AI_EVALUATION_CONTRACT_VERSION = "sc.core.ai-evaluation-benchmark.v1"
AI_EXPERIMENT_CONTRACT_VERSION = "sc.core.ai-experiment-reproducibility.v1"
AI_ERROR_ROBUSTNESS_CONTRACT_VERSION = "sc.core.ai-error-robustness.v1"


class CalibrationMethod(str, Enum):
    reliability_diagram = "reliability-diagram"
    expected_calibration_error = "expected-calibration-error"
    maximum_calibration_error = "maximum-calibration-error"
    brier_score = "brier-score"
    log_loss = "log-loss"
    isotonic = "isotonic"
    platt = "platt"
    temperature_scaling = "temperature-scaling"
    conformal = "conformal"
    other = "other"


class DriftDomain(str, Enum):
    input = "input"
    feature = "feature"
    label = "label"
    prediction = "prediction"
    probability = "probability"
    embedding = "embedding"
    retrieval = "retrieval"
    prompt = "prompt"
    performance = "performance"
    latency = "latency"
    cost = "cost"
    other = "other"


class DriftMethod(str, Enum):
    population_stability_index = "population-stability-index"
    kolmogorov_smirnov = "kolmogorov-smirnov"
    chi_square = "chi-square"
    jensen_shannon = "jensen-shannon"
    kl_divergence = "kl-divergence"
    wasserstein = "wasserstein"
    mean_shift = "mean-shift"
    variance_shift = "variance-shift"
    performance_delta = "performance-delta"
    embedding_distance = "embedding-distance"
    custom = "custom"


class DriftSeverity(str, Enum):
    none = "none"
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class RiskCategory(str, Enum):
    reliability = "reliability"
    calibration = "calibration"
    drift = "drift"
    robustness = "robustness"
    data_quality = "data-quality"
    retrieval_quality = "retrieval-quality"
    operational = "operational"
    cost = "cost"
    safety = "safety"
    governance = "governance"
    other = "other"


class RiskLevel(str, Enum):
    informational = "informational"
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class MonitoringState(str, Enum):
    declared = "declared"
    active = "active"
    paused = "paused"
    completed = "completed"
    failed = "failed"


class CalibrationBin(BaseModel):
    bin_id: str = Field(min_length=2, max_length=300)
    lower_bound: float = Field(ge=0.0, le=1.0)
    upper_bound: float = Field(ge=0.0, le=1.0)
    sample_count: int = Field(ge=0)
    mean_confidence: float = Field(ge=0.0, le=1.0)
    observed_frequency: float = Field(ge=0.0, le=1.0)
    absolute_gap: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.lower_bound > self.upper_bound:
            raise ValueError("calibration bin lower_bound exceeds upper_bound")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CalibrationMetricResult(BaseModel):
    metric_id: str = Field(min_length=2, max_length=300)
    method: CalibrationMethod
    value: float | int | None = None
    threshold: float | None = None
    passed: bool | None = None
    sample_count: int | None = Field(default=None, ge=0)
    confidence_interval: list[float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ci(self):
        if self.confidence_interval is not None:
            if len(self.confidence_interval) != 2:
                raise ValueError("confidence_interval must contain [lower, upper]")
            if self.confidence_interval[0] > self.confidence_interval[1]:
                raise ValueError("confidence interval bounds are reversed")
        return self


class CalibrationAssessment(BaseModel):
    calibration_assessment_id: str = Field(min_length=2, max_length=300)
    ai_model_version_ref: str = Field(min_length=2, max_length=300)
    benchmark_ref: str | None = Field(default=None, max_length=300)
    evaluation_run_ref: str = Field(min_length=2, max_length=300)
    dataset_version_ref: str | None = Field(default=None, max_length=300)
    slice_ref: str | None = Field(default=None, max_length=300)
    bins: list[CalibrationBin] = Field(default_factory=list)
    metric_results: list[CalibrationMetricResult] = Field(default_factory=list)
    recalibration_artifact_ref: str | None = Field(default=None, max_length=300)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_assessment(self):
        if not self.ai_model_version_ref.startswith("ai-model-version:"):
            raise ValueError("ai_model_version_ref must identify an AI model version")

        bin_ids = [item.bin_id for item in self.bins]
        if len(bin_ids) != len(set(bin_ids)):
            raise ValueError("calibration bin ids must be unique")

        metric_ids = [item.metric_id for item in self.metric_results]
        if len(metric_ids) != len(set(metric_ids)):
            raise ValueError("calibration metric ids must be unique")

        if not self.metric_results:
            raise ValueError("calibration assessment requires metric results")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class MonitoringWindow(BaseModel):
    monitoring_window_id: str = Field(min_length=2, max_length=300)
    start_at: datetime
    end_at: datetime
    dataset_version_refs: list[str] = Field(default_factory=list)
    inference_run_refs: list[str] = Field(default_factory=list)
    evaluation_run_refs: list[str] = Field(default_factory=list)
    sample_count: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_window(self):
        if self.end_at <= self.start_at:
            raise ValueError("monitoring window end_at must follow start_at")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DriftSignalDefinition(BaseModel):
    drift_signal_id: str = Field(min_length=2, max_length=300)
    name: str = Field(min_length=1, max_length=300)
    domain: DriftDomain
    method: DriftMethod
    source_field_ref: str | None = Field(default=None, max_length=500)
    baseline_ref: str = Field(min_length=2, max_length=500)
    warning_threshold: float | None = None
    critical_threshold: float | None = None
    direction: Literal[
        "higher-is-worse",
        "lower-is-worse",
        "absolute-difference",
        "informational",
    ] = "higher-is-worse"
    implementation_ref: str | None = Field(default=None, max_length=2000)
    implementation_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_thresholds(self):
        if (
            self.warning_threshold is not None
            and self.critical_threshold is not None
            and self.direction == "higher-is-worse"
            and self.warning_threshold > self.critical_threshold
        ):
            raise ValueError("warning threshold cannot exceed critical threshold")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DriftObservation(BaseModel):
    drift_observation_id: str = Field(min_length=2, max_length=300)
    drift_signal_ref: str = Field(min_length=2, max_length=300)
    ai_model_version_ref: str = Field(min_length=2, max_length=300)
    baseline_window_ref: str = Field(min_length=2, max_length=300)
    comparison_window_ref: str = Field(min_length=2, max_length=300)
    observed_value: float | int | None = None
    baseline_value: float | int | None = None
    delta: float | int | None = None
    severity: DriftSeverity = DriftSeverity.none
    threshold_exceeded: bool = False
    evidence_refs: list[str] = Field(default_factory=list)
    error_observation_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_observation(self):
        if not self.ai_model_version_ref.startswith("ai-model-version:"):
            raise ValueError("ai_model_version_ref must identify an AI model version")
        if self.baseline_window_ref == self.comparison_window_ref:
            raise ValueError("baseline and comparison windows must differ")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class RiskIndicatorDefinition(BaseModel):
    risk_indicator_id: str = Field(min_length=2, max_length=300)
    name: str = Field(min_length=1, max_length=300)
    category: RiskCategory
    description: str = Field(min_length=1, max_length=10000)
    source_ref_kind: Literal[
        "calibration",
        "drift",
        "robustness",
        "error",
        "evaluation",
        "operational",
        "other",
    ]
    warning_threshold: float | None = None
    critical_threshold: float | None = None
    direction: Literal[
        "higher-is-worse",
        "lower-is-worse",
        "absolute-difference",
        "boolean",
        "informational",
    ] = "higher-is-worse"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_thresholds(self):
        if (
            self.warning_threshold is not None
            and self.critical_threshold is not None
            and self.direction == "higher-is-worse"
            and self.warning_threshold > self.critical_threshold
        ):
            raise ValueError("risk warning threshold cannot exceed critical threshold")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RiskObservation(BaseModel):
    risk_observation_id: str = Field(min_length=2, max_length=300)
    risk_indicator_ref: str = Field(min_length=2, max_length=300)
    ai_model_version_ref: str = Field(min_length=2, max_length=300)
    observed_value: float | int | bool | None = None
    risk_level: RiskLevel
    source_object_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    mitigation_refs: list[str] = Field(default_factory=list)
    acknowledged: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_observation(self):
        if not self.ai_model_version_ref.startswith("ai-model-version:"):
            raise ValueError("ai_model_version_ref must identify an AI model version")
        if not self.source_object_refs and not self.evidence_refs:
            raise ValueError("risk observation requires source objects or evidence")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        payload.pop("acknowledged", None)
        return canonical_sha256(payload)


class MonitoringPolicy(BaseModel):
    monitoring_policy_id: str = Field(min_length=2, max_length=300)
    name: str = Field(min_length=1, max_length=300)
    ai_model_version_ref: str = Field(min_length=2, max_length=300)
    calibration_metric_refs: list[str] = Field(default_factory=list)
    drift_signal_refs: list[str] = Field(default_factory=list)
    risk_indicator_refs: list[str] = Field(default_factory=list)
    schedule_hint: str | None = Field(default=None, max_length=300)
    minimum_sample_count: int | None = Field(default=None, ge=1)
    retention_days: int | None = Field(default=None, ge=1)
    state: MonitoringState = MonitoringState.declared
    notification_policy_ref: str | None = Field(default=None, max_length=300)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy(self):
        if not self.ai_model_version_ref.startswith("ai-model-version:"):
            raise ValueError("ai_model_version_ref must identify an AI model version")
        if not any(
            [
                self.calibration_metric_refs,
                self.drift_signal_refs,
                self.risk_indicator_refs,
            ]
        ):
            raise ValueError("monitoring policy requires at least one monitored signal")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        return canonical_sha256(payload)


class MonitoringSnapshot(BaseModel):
    monitoring_snapshot_id: str = Field(min_length=2, max_length=300)
    monitoring_policy_ref: str = Field(min_length=2, max_length=300)
    ai_model_version_ref: str = Field(min_length=2, max_length=300)
    monitoring_window_ref: str = Field(min_length=2, max_length=300)
    calibration_assessment_refs: list[str] = Field(default_factory=list)
    drift_observation_refs: list[str] = Field(default_factory=list)
    risk_observation_refs: list[str] = Field(default_factory=list)
    robustness_run_refs: list[str] = Field(default_factory=list)
    error_analysis_report_refs: list[str] = Field(default_factory=list)
    overall_risk_level: RiskLevel = RiskLevel.informational
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        if not self.ai_model_version_ref.startswith("ai-model-version:"):
            raise ValueError("ai_model_version_ref must identify an AI model version")
        if not any(
            [
                self.calibration_assessment_refs,
                self.drift_observation_refs,
                self.risk_observation_refs,
                self.robustness_run_refs,
                self.error_analysis_report_refs,
            ]
        ):
            raise ValueError("monitoring snapshot requires monitored evidence")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class CalibrationDriftRiskBundle(BaseModel):
    windows: list[MonitoringWindow] = Field(default_factory=list)
    calibration_assessments: list[CalibrationAssessment] = Field(default_factory=list)
    drift_signals: list[DriftSignalDefinition] = Field(default_factory=list)
    drift_observations: list[DriftObservation] = Field(default_factory=list)
    risk_indicators: list[RiskIndicatorDefinition] = Field(default_factory=list)
    risk_observations: list[RiskObservation] = Field(default_factory=list)
    monitoring_policy: MonitoringPolicy
    monitoring_snapshots: list[MonitoringSnapshot] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_bundle(self):
        window_ids = {item.monitoring_window_id for item in self.windows}
        for observation in self.drift_observations:
            if observation.baseline_window_ref not in window_ids:
                raise ValueError("drift observation baseline window missing from bundle")
            if observation.comparison_window_ref not in window_ids:
                raise ValueError("drift observation comparison window missing from bundle")

        signal_ids = {item.drift_signal_id for item in self.drift_signals}
        for observation in self.drift_observations:
            if observation.drift_signal_ref not in signal_ids:
                raise ValueError("drift observation references signal outside bundle")

        indicator_ids = {item.risk_indicator_id for item in self.risk_indicators}
        for observation in self.risk_observations:
            if observation.risk_indicator_ref not in indicator_ids:
                raise ValueError("risk observation references indicator outside bundle")

        if self.monitoring_policy.ai_model_version_ref:
            all_model_refs = {
                item.ai_model_version_ref for item in self.calibration_assessments
            } | {
                item.ai_model_version_ref for item in self.drift_observations
            } | {
                item.ai_model_version_ref for item in self.risk_observations
            }
            if all_model_refs and self.monitoring_policy.ai_model_version_ref not in all_model_refs:
                raise ValueError("monitoring policy model version is not represented in bundle")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "window_fingerprints": sorted(item.fingerprint() for item in self.windows),
            "calibration_fingerprints": sorted(
                item.fingerprint() for item in self.calibration_assessments
            ),
            "drift_signal_fingerprints": sorted(
                item.fingerprint() for item in self.drift_signals
            ),
            "drift_observation_fingerprints": sorted(
                item.fingerprint() for item in self.drift_observations
            ),
            "risk_indicator_fingerprints": sorted(
                item.fingerprint() for item in self.risk_indicators
            ),
            "risk_observation_fingerprints": sorted(
                item.fingerprint() for item in self.risk_observations
            ),
            "monitoring_policy_fingerprint_sha256": self.monitoring_policy.fingerprint(),
            "monitoring_snapshot_fingerprints": sorted(
                item.fingerprint() for item in self.monitoring_snapshots
            ),
        })


def reference_calibration_drift_risk_bundle() -> CalibrationDriftRiskBundle:
    model_ref = "ai-model-version:reference-classifier:1.0.0"

    baseline_window = MonitoringWindow(
        monitoring_window_id="monitoring-window:reference:baseline",
        start_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        end_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
        dataset_version_refs=["dataset-version:reference-classification:v1"],
        evaluation_run_refs=["evaluation-run:reference-classifier:baseline"],
        sample_count=1000,
    )
    comparison_window = MonitoringWindow(
        monitoring_window_id="monitoring-window:reference:current",
        start_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
        end_at=datetime(2026, 9, 22, tzinfo=timezone.utc),
        dataset_version_refs=["dataset-version:reference-classification:v2"],
        evaluation_run_refs=["evaluation-run:reference-classifier:current"],
        sample_count=1000,
    )

    calibration = CalibrationAssessment(
        calibration_assessment_id="calibration-assessment:reference:current",
        ai_model_version_ref=model_ref,
        benchmark_ref="benchmark:reference-classification:v1",
        evaluation_run_ref="evaluation-run:reference-classifier:current",
        dataset_version_ref="dataset-version:reference-classification:v2",
        bins=[
            CalibrationBin(
                bin_id="calibration-bin:0.0-0.5",
                lower_bound=0.0,
                upper_bound=0.5,
                sample_count=400,
                mean_confidence=0.31,
                observed_frequency=0.28,
                absolute_gap=0.03,
            ),
            CalibrationBin(
                bin_id="calibration-bin:0.5-1.0",
                lower_bound=0.5,
                upper_bound=1.0,
                sample_count=600,
                mean_confidence=0.82,
                observed_frequency=0.74,
                absolute_gap=0.08,
            ),
        ],
        metric_results=[
            CalibrationMetricResult(
                metric_id="calibration-metric:ece",
                method=CalibrationMethod.expected_calibration_error,
                value=0.06,
                threshold=0.05,
                passed=False,
                sample_count=1000,
            ),
            CalibrationMetricResult(
                metric_id="calibration-metric:brier",
                method=CalibrationMethod.brier_score,
                value=0.17,
                threshold=0.20,
                passed=True,
                sample_count=1000,
            ),
        ],
        provenance={
            "calibration_owner": "research-lab",
            "core_executes_calibration": False,
        },
    )

    signal = DriftSignalDefinition(
        drift_signal_id="drift-signal:prediction-probability-js",
        name="Prediction Probability Jensen-Shannon Drift",
        domain=DriftDomain.probability,
        method=DriftMethod.jensen_shannon,
        baseline_ref=baseline_window.monitoring_window_id,
        warning_threshold=0.10,
        critical_threshold=0.20,
        direction="higher-is-worse",
        implementation_ref="method:jensen-shannon-probability-drift",
        implementation_sha256="a" * 64,
    )

    drift = DriftObservation(
        drift_observation_id="drift-observation:reference:current",
        drift_signal_ref=signal.drift_signal_id,
        ai_model_version_ref=model_ref,
        baseline_window_ref=baseline_window.monitoring_window_id,
        comparison_window_ref=comparison_window.monitoring_window_id,
        observed_value=0.14,
        baseline_value=0.02,
        delta=0.12,
        severity=DriftSeverity.moderate,
        threshold_exceeded=True,
        evidence_refs=["evidence:reference-drift-analysis"],
        error_observation_refs=["error-observation:reference:001"],
        provenance={"experiment_ref": "ai-experiment:reference-classifier-comparison:v1"},
    )

    calibration_risk = RiskIndicatorDefinition(
        risk_indicator_id="risk-indicator:calibration-ece",
        name="Calibration Error Risk",
        category=RiskCategory.calibration,
        description="Risk signal derived from expected calibration error.",
        source_ref_kind="calibration",
        warning_threshold=0.05,
        critical_threshold=0.10,
        direction="higher-is-worse",
    )
    drift_risk = RiskIndicatorDefinition(
        risk_indicator_id="risk-indicator:prediction-drift",
        name="Prediction Drift Risk",
        category=RiskCategory.drift,
        description="Risk signal derived from prediction probability drift.",
        source_ref_kind="drift",
        warning_threshold=0.10,
        critical_threshold=0.20,
        direction="higher-is-worse",
    )
    robustness_risk = RiskIndicatorDefinition(
        risk_indicator_id="risk-indicator:robustness-failure",
        name="Robustness Failure Risk",
        category=RiskCategory.robustness,
        description="Risk signal from failed robustness tolerance checks.",
        source_ref_kind="robustness",
        direction="boolean",
    )

    risk_observations = [
        RiskObservation(
            risk_observation_id="risk-observation:calibration:current",
            risk_indicator_ref=calibration_risk.risk_indicator_id,
            ai_model_version_ref=model_ref,
            observed_value=0.06,
            risk_level=RiskLevel.moderate,
            source_object_refs=[calibration.calibration_assessment_id],
            evidence_refs=["evidence:reference-calibration-analysis"],
        ),
        RiskObservation(
            risk_observation_id="risk-observation:drift:current",
            risk_indicator_ref=drift_risk.risk_indicator_id,
            ai_model_version_ref=model_ref,
            observed_value=0.14,
            risk_level=RiskLevel.moderate,
            source_object_refs=[drift.drift_observation_id],
            evidence_refs=["evidence:reference-drift-analysis"],
        ),
        RiskObservation(
            risk_observation_id="risk-observation:robustness:current",
            risk_indicator_ref=robustness_risk.risk_indicator_id,
            ai_model_version_ref=model_ref,
            observed_value=True,
            risk_level=RiskLevel.high,
            source_object_refs=["robustness-run:reference-classifier-noise:001"],
            evidence_refs=["evidence:reference-error-case"],
        ),
    ]

    policy = MonitoringPolicy(
        monitoring_policy_id="monitoring-policy:reference-classifier:v1",
        name="Reference Classifier Reliability Monitoring",
        ai_model_version_ref=model_ref,
        calibration_metric_refs=[
            "calibration-metric:ece",
            "calibration-metric:brier",
        ],
        drift_signal_refs=[signal.drift_signal_id],
        risk_indicator_refs=[
            calibration_risk.risk_indicator_id,
            drift_risk.risk_indicator_id,
            robustness_risk.risk_indicator_id,
        ],
        schedule_hint="daily",
        minimum_sample_count=500,
        retention_days=365,
        state=MonitoringState.active,
        provenance={
            "execution_owner": "research-lab-or-workspace",
            "core_performs_scheduling": False,
        },
    )

    snapshot = MonitoringSnapshot(
        monitoring_snapshot_id="monitoring-snapshot:reference:current",
        monitoring_policy_ref=policy.monitoring_policy_id,
        ai_model_version_ref=model_ref,
        monitoring_window_ref=comparison_window.monitoring_window_id,
        calibration_assessment_refs=[calibration.calibration_assessment_id],
        drift_observation_refs=[drift.drift_observation_id],
        risk_observation_refs=[
            item.risk_observation_id for item in risk_observations
        ],
        robustness_run_refs=["robustness-run:reference-classifier-noise:001"],
        error_analysis_report_refs=["error-analysis-report:reference-classifier:v1"],
        overall_risk_level=RiskLevel.high,
        provenance={
            "aggregate_is_descriptive": True,
            "core_certifies_operational_safety": False,
        },
    )

    return CalibrationDriftRiskBundle(
        windows=[baseline_window, comparison_window],
        calibration_assessments=[calibration],
        drift_signals=[signal],
        drift_observations=[drift],
        risk_indicators=[calibration_risk, drift_risk, robustness_risk],
        risk_observations=risk_observations,
        monitoring_policy=policy,
        monitoring_snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    reference = reference_calibration_drift_risk_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            AI_MODEL_CONTRACT_VERSION,
            AI_INFERENCE_CONTRACT_VERSION,
            AI_EVALUATION_CONTRACT_VERSION,
            AI_EXPERIMENT_CONTRACT_VERSION,
            AI_ERROR_ROBUSTNESS_CONTRACT_VERSION,
        ],
        "object_types": [
            "CalibrationBin",
            "CalibrationMetricResult",
            "CalibrationAssessment",
            "MonitoringWindow",
            "DriftSignalDefinition",
            "DriftObservation",
            "RiskIndicatorDefinition",
            "RiskObservation",
            "MonitoringPolicy",
            "MonitoringSnapshot",
            "CalibrationDriftRiskBundle",
        ],
        "capabilities": {
            "probability_calibration": True,
            "reliability_bins": True,
            "calibration_metric_thresholds": True,
            "monitoring_windows": True,
            "data_and_prediction_drift": True,
            "performance_drift": True,
            "embedding_retrieval_prompt_drift": True,
            "drift_severity": True,
            "risk_indicators": True,
            "risk_observations": True,
            "monitoring_policies": True,
            "monitoring_snapshots": True,
            "robustness_and_error_links": True,
            "model_version_binding": True,
        },
        "integration": {
            "lab_executes_calibration_and_drift_analysis": True,
            "workspace_or_runtime_executes_jobs": True,
            "core_owns_monitoring_semantics": True,
            "core_duplicates_robustness_storage": False,
            "core_duplicates_evaluation_storage": False,
            "core_performs_background_scheduling": False,
        },
        "reference": {
            "monitoring_policy_id": reference.monitoring_policy.monitoring_policy_id,
            "monitoring_snapshot_id": (
                reference.monitoring_snapshots[0].monitoring_snapshot_id
            ),
            "bundle_fingerprint_sha256": reference.fingerprint(),
        },
        "boundaries": {
            "core_executes_monitoring_jobs": False,
            "core_autonomously_retrains_models": False,
            "core_autonomously_blocks_models": False,
            "core_certifies_model_safety": False,
            "core_certifies_operational_readiness": False,
            "core_owns_calibration_drift_risk_contracts": True,
        },
    }
