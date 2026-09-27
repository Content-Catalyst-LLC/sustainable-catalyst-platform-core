from __future__ import annotations

import math
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .ml_dataset_provenance import MLDatasetPartitionRecord, MLPartitionRole, reference_dataset_feature_transformation_bundle
from .ml_training_lineage import MLEvaluationRecord, MLEvaluationSplit, reference_training_lineage_bundle

CORE_RELEASE = "3.60.0"
CONTRACT_VERSION = "sc.core.neural-evaluation-calibration-uncertainty.v1"


def _finite(value: float, label: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")


class MLMetricFamily(str, Enum):
    loss = "loss"
    regression = "regression"
    classification = "classification"
    ranking = "ranking"
    calibration = "calibration"
    probabilistic = "probabilistic"
    robustness = "robustness"
    fairness = "fairness"
    custom = "custom"


class MLMetricDirection(str, Enum):
    lower_is_better = "lower-is-better"
    higher_is_better = "higher-is-better"
    target_is_better = "target-is-better"
    descriptive = "descriptive"


class MLCalibrationKind(str, Enum):
    probability = "probability"
    interval_coverage = "interval-coverage"
    quantile = "quantile"
    reliability = "reliability"
    other = "other"


class MLConfidenceQuantity(str, Enum):
    class_confidence = "class-confidence"
    predictive_stddev = "predictive-stddev"
    entropy = "entropy"
    margin = "margin"
    interval_width = "interval-width"
    other = "other"


class MLUncertaintyKind(str, Enum):
    aleatoric = "aleatoric"
    epistemic = "epistemic"
    predictive = "predictive"
    total = "total"
    ensemble = "ensemble"
    sampling = "sampling"
    other = "other"


class MLOODDirection(str, Enum):
    greater_is_ood = "greater-is-ood"
    lower_is_ood = "lower-is-ood"


class MLMetricObservation(BaseModel):
    metric_observation_id: str = Field(min_length=2, max_length=300)
    evaluation_ref: str = Field(min_length=2, max_length=500)
    partition_ref: str = Field(min_length=2, max_length=500)
    metric_name: str = Field(min_length=1, max_length=240)
    metric_family: MLMetricFamily
    value: float
    direction: MLMetricDirection = MLMetricDirection.descriptive
    target_value: float | None = None
    threshold: float | None = None
    sample_count: int | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=120)
    computation_ref: str | None = Field(default=None, max_length=1000)
    artifact_ref: str | None = Field(default=None, max_length=1000)
    artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metric(self):
        _finite(self.value, "metric value")
        if self.target_value is not None: _finite(self.target_value, "metric target_value")
        if self.threshold is not None: _finite(self.threshold, "metric threshold")
        if self.direction == MLMetricDirection.target_is_better and self.target_value is None:
            raise ValueError("target-is-better metric requires target_value")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class MLConfusionMatrixRecord(BaseModel):
    confusion_matrix_id: str = Field(min_length=2, max_length=300)
    evaluation_ref: str = Field(min_length=2, max_length=500)
    partition_ref: str = Field(min_length=2, max_length=500)
    labels: list[str] = Field(min_length=2)
    counts: list[list[int]] = Field(min_length=2)
    sample_count: int | None = Field(default=None, ge=0)
    artifact_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_matrix(self):
        n=len(self.labels)
        if len(self.labels)!=len(set(self.labels)): raise ValueError("confusion-matrix labels must be unique")
        if len(self.counts)!=n or any(len(row)!=n for row in self.counts): raise ValueError("confusion matrix must be square and match label count")
        if any(v<0 for row in self.counts for v in row): raise ValueError("confusion-matrix counts must be non-negative")
        total=sum(sum(row) for row in self.counts)
        if self.sample_count is not None and self.sample_count!=total: raise ValueError("confusion-matrix sample_count must equal sum of counts")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class MLCalibrationBinRecord(BaseModel):
    lower_bound: float = Field(ge=0.0, le=1.0)
    upper_bound: float = Field(gt=0.0, le=1.0)
    predicted_value: float = Field(ge=0.0, le=1.0)
    observed_frequency: float = Field(ge=0.0, le=1.0)
    sample_count: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_bin(self):
        if self.upper_bound <= self.lower_bound: raise ValueError("calibration bin upper_bound must exceed lower_bound")
        return self


class MLCalibrationRecord(BaseModel):
    calibration_id: str = Field(min_length=2, max_length=300)
    evaluation_ref: str = Field(min_length=2, max_length=500)
    partition_ref: str = Field(min_length=2, max_length=500)
    calibration_kind: MLCalibrationKind
    method: str = Field(min_length=1, max_length=240)
    bins: list[MLCalibrationBinRecord] = Field(min_length=1)
    expected_calibration_error: float | None = Field(default=None, ge=0.0, le=1.0)
    maximum_calibration_error: float | None = Field(default=None, ge=0.0, le=1.0)
    brier_score: float | None = Field(default=None, ge=0.0)
    artifact_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_calibration(self):
        bins=sorted(self.bins,key=lambda b:b.lower_bound)
        for a,b in zip(bins,bins[1:]):
            if b.lower_bound < a.upper_bound: raise ValueError("calibration bins must not overlap")
        for v,label in ((self.expected_calibration_error,"expected_calibration_error"),(self.maximum_calibration_error,"maximum_calibration_error"),(self.brier_score,"brier_score")):
            if v is not None: _finite(v,label)
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class MLConfidenceDistributionRecord(BaseModel):
    confidence_distribution_id: str = Field(min_length=2, max_length=300)
    evaluation_ref: str = Field(min_length=2, max_length=500)
    partition_ref: str = Field(min_length=2, max_length=500)
    quantity: MLConfidenceQuantity
    quantiles: dict[str, float] = Field(default_factory=dict)
    histogram_edges: list[float] = Field(min_length=2)
    histogram_counts: list[int] = Field(min_length=1)
    sample_count: int | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=120)
    artifact_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_distribution(self):
        if len(self.histogram_edges)!=len(self.histogram_counts)+1: raise ValueError("histogram_edges must contain one more value than histogram_counts")
        if any(b<=a for a,b in zip(self.histogram_edges,self.histogram_edges[1:])): raise ValueError("histogram_edges must be strictly increasing")
        if any(v<0 for v in self.histogram_counts): raise ValueError("histogram_counts must be non-negative")
        if self.sample_count is not None and sum(self.histogram_counts)!=self.sample_count: raise ValueError("histogram counts must sum to sample_count")
        for k,v in self.quantiles.items(): _finite(v,f"quantile {k}")
        for v in self.histogram_edges: _finite(v,"histogram edge")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class MLPredictionIntervalSummary(BaseModel):
    prediction_interval_id: str = Field(min_length=2, max_length=300)
    evaluation_ref: str = Field(min_length=2, max_length=500)
    partition_ref: str = Field(min_length=2, max_length=500)
    nominal_coverage: float = Field(gt=0.0, lt=1.0)
    empirical_coverage: float = Field(ge=0.0, le=1.0)
    mean_width: float = Field(ge=0.0)
    median_width: float | None = Field(default=None, ge=0.0)
    lower_quantile: float = Field(ge=0.0, lt=1.0)
    upper_quantile: float = Field(gt=0.0, le=1.0)
    sample_count: int | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=120)
    method: str | None = Field(default=None, max_length=240)
    artifact_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_interval(self):
        if self.upper_quantile <= self.lower_quantile: raise ValueError("upper_quantile must exceed lower_quantile")
        expected=self.upper_quantile-self.lower_quantile
        if abs(expected-self.nominal_coverage)>1e-6: raise ValueError("nominal_coverage must equal upper_quantile - lower_quantile")
        for v,label in ((self.empirical_coverage,"empirical_coverage"),(self.mean_width,"mean_width")):
            _finite(v,label)
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class MLUncertaintyEstimateRecord(BaseModel):
    uncertainty_estimate_id: str = Field(min_length=2, max_length=300)
    evaluation_ref: str = Field(min_length=2, max_length=500)
    partition_ref: str = Field(min_length=2, max_length=500)
    uncertainty_kind: MLUncertaintyKind
    estimate: float = Field(ge=0.0)
    statistic: str = Field(min_length=1, max_length=240)
    sample_count: int | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=120)
    method: str | None = Field(default=None, max_length=240)
    computation_ref: str | None = Field(default=None, max_length=1000)
    artifact_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_uncertainty(self):
        _finite(self.estimate,"uncertainty estimate")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class MLOutOfDistributionIndicatorRecord(BaseModel):
    ood_indicator_id: str = Field(min_length=2, max_length=300)
    evaluation_ref: str = Field(min_length=2, max_length=500)
    partition_ref: str = Field(min_length=2, max_length=500)
    detector_ref: str = Field(min_length=2, max_length=1000)
    score: float
    threshold: float
    direction: MLOODDirection
    is_out_of_distribution: bool
    sample_ref: str | None = Field(default=None, max_length=1000)
    computation_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ood(self):
        _finite(self.score,"OOD score"); _finite(self.threshold,"OOD threshold")
        expected = self.score >= self.threshold if self.direction==MLOODDirection.greater_is_ood else self.score <= self.threshold
        if self.is_out_of_distribution != expected: raise ValueError("OOD flag must be consistent with score, threshold, and direction")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class MLEvaluationCalibrationUncertaintyBundle(BaseModel):
    model_spec_ref: str = Field(min_length=2, max_length=500)
    training_run_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str = Field(min_length=2, max_length=500)
    evaluation: MLEvaluationRecord
    dataset_partition: MLDatasetPartitionRecord
    metric_observations: list[MLMetricObservation] = Field(min_length=1)
    confusion_matrices: list[MLConfusionMatrixRecord] = Field(default_factory=list)
    calibration_records: list[MLCalibrationRecord] = Field(default_factory=list)
    confidence_distributions: list[MLConfidenceDistributionRecord] = Field(default_factory=list)
    prediction_intervals: list[MLPredictionIntervalSummary] = Field(default_factory=list)
    uncertainty_estimates: list[MLUncertaintyEstimateRecord] = Field(default_factory=list)
    ood_indicators: list[MLOutOfDistributionIndicatorRecord] = Field(default_factory=list)
    training_lineage_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    dataset_lineage_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.evaluation.training_run_ref != self.training_run_ref: raise ValueError("evaluation training_run_ref must match bundle")
        if self.evaluation.checkpoint_ref != self.checkpoint_ref: raise ValueError("evaluation checkpoint_ref must match bundle checkpoint_ref")
        if self.dataset_partition.dataset_version_ref != self.evaluation.dataset_version_ref: raise ValueError("evaluation dataset must match dataset partition")
        split_to_role={MLEvaluationSplit.train:MLPartitionRole.train, MLEvaluationSplit.validation:MLPartitionRole.validation, MLEvaluationSplit.test:MLPartitionRole.test}
        expected_role=split_to_role.get(self.evaluation.split)
        if expected_role and self.dataset_partition.role != expected_role: raise ValueError("evaluation split must match dataset partition role")
        groups=[self.metric_observations,self.confusion_matrices,self.calibration_records,self.confidence_distributions,self.prediction_intervals,self.uncertainty_estimates,self.ood_indicators]
        for records in groups:
            for record in records:
                if record.evaluation_ref != self.evaluation.evaluation_id: raise ValueError("evaluation-derived object evaluation_ref must resolve to bundled evaluation")
                if record.partition_ref != self.dataset_partition.partition_id: raise ValueError("evaluation-derived object partition_ref must resolve to bundled partition")
        ids=[]
        for records in groups:
            for r in records:
                for name in ("metric_observation_id","confusion_matrix_id","calibration_id","confidence_distribution_id","prediction_interval_id","uncertainty_estimate_id","ood_indicator_id"):
                    if hasattr(r,name): ids.append(getattr(r,name)); break
        if len(ids)!=len(set(ids)): raise ValueError("evaluation-derived object ids must be unique")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


def reference_evaluation_calibration_uncertainty_bundle() -> MLEvaluationCalibrationUncertaintyBundle:
    training=reference_training_lineage_bundle(); dataset=reference_dataset_feature_transformation_bundle()
    run=training.training_runs[0]; evaluation=run.evaluations[0]
    partition=next(p for p in dataset.partitions if p.role==MLPartitionRole.validation)
    metrics=[
        MLMetricObservation(metric_observation_id="ml-metric:reference-energy:mae",evaluation_ref=evaluation.evaluation_id,partition_ref=partition.partition_id,metric_name="mae",metric_family=MLMetricFamily.regression,value=0.44,direction=MLMetricDirection.lower_is_better,sample_count=100,unit="kwh"),
        MLMetricObservation(metric_observation_id="ml-metric:reference-energy:rmse",evaluation_ref=evaluation.evaluation_id,partition_ref=partition.partition_id,metric_name="rmse",metric_family=MLMetricFamily.regression,value=0.58,direction=MLMetricDirection.lower_is_better,sample_count=100,unit="kwh"),
    ]
    calibration=MLCalibrationRecord(calibration_id="ml-calibration:reference-energy:coverage",evaluation_ref=evaluation.evaluation_id,partition_ref=partition.partition_id,calibration_kind=MLCalibrationKind.interval_coverage,method="empirical-coverage-by-nominal-level",bins=[MLCalibrationBinRecord(lower_bound=0.0,upper_bound=0.8,predicted_value=0.80,observed_frequency=0.77,sample_count=100),MLCalibrationBinRecord(lower_bound=0.8,upper_bound=0.9,predicted_value=0.90,observed_frequency=0.88,sample_count=100),MLCalibrationBinRecord(lower_bound=0.9,upper_bound=1.0,predicted_value=0.95,observed_frequency=0.93,sample_count=100)],expected_calibration_error=0.023,maximum_calibration_error=0.03,artifact_ref="artifact:reference-energy:coverage-calibration")
    confidence=MLConfidenceDistributionRecord(confidence_distribution_id="ml-confidence:reference-energy:predictive-stddev",evaluation_ref=evaluation.evaluation_id,partition_ref=partition.partition_id,quantity=MLConfidenceQuantity.predictive_stddev,quantiles={"p10":0.11,"p50":0.21,"p90":0.39},histogram_edges=[0.0,0.15,0.30,0.45,0.60],histogram_counts=[25,45,25,5],sample_count=100,unit="kwh")
    interval=MLPredictionIntervalSummary(prediction_interval_id="ml-interval:reference-energy:90",evaluation_ref=evaluation.evaluation_id,partition_ref=partition.partition_id,nominal_coverage=0.90,empirical_coverage=0.88,mean_width=1.64,median_width=1.51,lower_quantile=0.05,upper_quantile=0.95,sample_count=100,unit="kwh",method="quantile-regression")
    uncertainties=[
        MLUncertaintyEstimateRecord(uncertainty_estimate_id="ml-uncertainty:reference-energy:aleatoric",evaluation_ref=evaluation.evaluation_id,partition_ref=partition.partition_id,uncertainty_kind=MLUncertaintyKind.aleatoric,estimate=0.19,statistic="mean-standard-deviation",sample_count=100,unit="kwh",method="heteroscedastic-head"),
        MLUncertaintyEstimateRecord(uncertainty_estimate_id="ml-uncertainty:reference-energy:epistemic",evaluation_ref=evaluation.evaluation_id,partition_ref=partition.partition_id,uncertainty_kind=MLUncertaintyKind.epistemic,estimate=0.12,statistic="mean-standard-deviation",sample_count=100,unit="kwh",method="ensemble-dispersion"),
    ]
    ood=MLOutOfDistributionIndicatorRecord(ood_indicator_id="ml-ood:reference-energy:validation-example",evaluation_ref=evaluation.evaluation_id,partition_ref=partition.partition_id,detector_ref="ood-detector:reference-energy:mahalanobis:v1",score=1.2,threshold=3.0,direction=MLOODDirection.greater_is_ood,is_out_of_distribution=False,sample_ref="sample:reference-energy:validation:001")
    return MLEvaluationCalibrationUncertaintyBundle(model_spec_ref=training.model_spec.model_spec_id,training_run_ref=run.training_run_id,checkpoint_ref=evaluation.checkpoint_ref or "",evaluation=evaluation,dataset_partition=partition,metric_observations=metrics,calibration_records=[calibration],confidence_distributions=[confidence],prediction_intervals=[interval],uncertainty_estimates=uncertainties,ood_indicators=[ood],training_lineage_fingerprint_sha256=training.fingerprint(),dataset_lineage_fingerprint_sha256=dataset.fingerprint())


def contract_document() -> dict[str, Any]:
    ref=reference_evaluation_calibration_uncertainty_bundle()
    return {
        "ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
        "object_types":["MLMetricObservation","MLConfusionMatrixRecord","MLCalibrationBinRecord","MLCalibrationRecord","MLConfidenceDistributionRecord","MLPredictionIntervalSummary","MLUncertaintyEstimateRecord","MLOutOfDistributionIndicatorRecord","MLEvaluationCalibrationUncertaintyBundle"],
        "integration":{"extends_training_run_checkpoint_experiment_lineage_v3580":True,"extends_neural_dataset_feature_transformation_provenance_v3590":True,"links_evaluation_to_checkpoint":True,"links_evaluation_to_dataset_partition":True,"preserves_training_and_dataset_lineage_fingerprints":True,"workspace_remains_default_compute_host":True,"lab_remains_experiment_host":True},
        "evaluation_capabilities":{"scalar_metric_observations":True,"confusion_matrices":True,"calibration_curves_and_bins":True,"confidence_distributions":True,"prediction_interval_summaries":True,"aleatoric_epistemic_and_predictive_uncertainty":True,"out_of_distribution_indicators":True},
        "reproducibility":{"deterministic_bundle_fingerprint":True,"metric_artifact_hashes_supported":True,"evaluation_partition_resolution_required":True,"calibration_bin_validation":True,"interval_coverage_validation":True,"ood_threshold_semantics_validated":True},
        "governance":{"metric_is_analytical_result_not_evidence":True,"confidence_is_not_truth_probability":True,"uncertainty_is_not_certainty_claim":True,"ood_indicator_is_not_fact":True,"evaluation_outputs_require_lineage":True},
        "boundaries":{"core_computes_metrics":False,"core_calibrates_models":False,"core_generates_predictions":False,"core_estimates_uncertainty":False,"core_runs_ood_detection":False,"core_selects_thresholds":False,"core_selects_best_model":False,"core_promotes_models_autonomously":False,"core_certifies_model_quality":False,"core_treats_scores_as_evidence":False,"core_claims_prediction_truth":False},
        "reference":{"evaluation_id":ref.evaluation.evaluation_id,"partition_id":ref.dataset_partition.partition_id,"checkpoint_ref":ref.checkpoint_ref,"metric_count":len(ref.metric_observations),"bundle_fingerprint_sha256":ref.fingerprint()}
    }
