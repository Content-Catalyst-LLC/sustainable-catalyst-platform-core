from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.33.0"
CONTRACT_VERSION = "sc.core.ai-error-robustness.v1"

AI_MODEL_CONTRACT_VERSION = "sc.core.ai-model.v1"
AI_INFERENCE_CONTRACT_VERSION = "sc.core.ai-inference-provenance.v1"
AI_EVALUATION_CONTRACT_VERSION = "sc.core.ai-evaluation-benchmark.v1"
AI_EXPERIMENT_CONTRACT_VERSION = "sc.core.ai-experiment-reproducibility.v1"


class FailureDomain(str, Enum):
    data = "data"
    feature = "feature"
    model = "model"
    prompt = "prompt"
    retrieval = "retrieval"
    inference = "inference"
    evaluation = "evaluation"
    robustness = "robustness"
    safety = "safety"
    system = "system"
    unknown = "unknown"


class FailureSeverity(str, Enum):
    informational = "informational"
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class ErrorDisposition(str, Enum):
    observed = "observed"
    confirmed = "confirmed"
    mitigated = "mitigated"
    accepted = "accepted"
    unresolved = "unresolved"


class RobustnessTestKind(str, Enum):
    perturbation = "perturbation"
    distribution_shift = "distribution-shift"
    missingness = "missingness"
    noise = "noise"
    adversarial = "adversarial"
    prompt_variation = "prompt-variation"
    retrieval_variation = "retrieval-variation"
    subgroup = "subgroup"
    temporal = "temporal"
    spatial = "spatial"
    stress = "stress"
    other = "other"


class FailureModeDefinition(BaseModel):
    failure_mode_id: str = Field(min_length=2, max_length=300)
    name: str = Field(min_length=1, max_length=300)
    domain: FailureDomain
    description: str = Field(min_length=1, max_length=10000)
    detection_method_refs: list[str] = Field(default_factory=list)
    expected_evidence_kinds: list[str] = Field(default_factory=list)
    default_severity: FailureSeverity = FailureSeverity.moderate
    parent_failure_mode_ref: str | None = Field(default=None, max_length=300)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_parent(self):
        if self.parent_failure_mode_ref == self.failure_mode_id:
            raise ValueError("parent_failure_mode_ref cannot reference itself")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class FailureTaxonomy(BaseModel):
    failure_taxonomy_id: str = Field(min_length=2, max_length=300)
    name: str = Field(min_length=1, max_length=300)
    version: str = Field(min_length=1, max_length=120)
    failure_modes: list[FailureModeDefinition] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_taxonomy(self):
        ids = [item.failure_mode_id for item in self.failure_modes]
        if len(ids) != len(set(ids)):
            raise ValueError("failure mode ids must be unique")
        known = set(ids)
        for item in self.failure_modes:
            if item.parent_failure_mode_ref and item.parent_failure_mode_ref not in known:
                raise ValueError("parent failure mode must exist in this taxonomy")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class ErrorObservation(BaseModel):
    error_observation_id: str = Field(min_length=2, max_length=300)
    failure_mode_ref: str = Field(min_length=2, max_length=300)
    severity: FailureSeverity
    disposition: ErrorDisposition = ErrorDisposition.observed
    ai_model_version_ref: str = Field(min_length=2, max_length=300)
    evaluation_run_ref: str | None = Field(default=None, max_length=300)
    evaluation_case_ref: str | None = Field(default=None, max_length=300)
    inference_run_ref: str | None = Field(default=None, max_length=300)
    ai_artifact_refs: list[str] = Field(default_factory=list)
    dataset_version_refs: list[str] = Field(default_factory=list)
    prompt_version_ref: str | None = Field(default=None, max_length=300)
    retrieval_context_ref: str | None = Field(default=None, max_length=300)
    evidence_refs: list[str] = Field(default_factory=list)
    observed_behavior: str = Field(min_length=1, max_length=20000)
    expected_behavior: str | None = Field(default=None, max_length=20000)
    suspected_cause_refs: list[str] = Field(default_factory=list)
    confirmed_cause_refs: list[str] = Field(default_factory=list)
    mitigation_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_observation(self):
        if not self.ai_model_version_ref.startswith("ai-model-version:"):
            raise ValueError("ai_model_version_ref must identify an AI model version")
        if not any(
            [
                self.evaluation_run_ref,
                self.evaluation_case_ref,
                self.inference_run_ref,
                self.ai_artifact_refs,
                self.evidence_refs,
            ]
        ):
            raise ValueError("error observation requires at least one evidence/run/artifact link")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        payload.pop("disposition", None)
        return canonical_sha256(payload)


class EvaluationSliceDefinition(BaseModel):
    slice_id: str = Field(min_length=2, max_length=300)
    name: str = Field(min_length=1, max_length=300)
    dataset_version_ref: str = Field(min_length=2, max_length=300)
    criteria: dict[str, Any] = Field(default_factory=dict)
    purpose: str | None = Field(default=None, max_length=5000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SliceMetricResult(BaseModel):
    metric_ref: str = Field(min_length=2, max_length=300)
    value: float | int | None = None
    baseline_value: float | int | None = None
    delta: float | int | None = None
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


class SlicePerformanceResult(BaseModel):
    slice_result_id: str = Field(min_length=2, max_length=300)
    slice_ref: str = Field(min_length=2, max_length=300)
    evaluation_run_ref: str = Field(min_length=2, max_length=300)
    ai_model_version_ref: str = Field(min_length=2, max_length=300)
    metric_results: list[SliceMetricResult] = Field(default_factory=list)
    error_observation_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metrics(self):
        refs = [item.metric_ref for item in self.metric_results]
        if len(refs) != len(set(refs)):
            raise ValueError("slice metric results must be unique per metric_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RobustnessPerturbation(BaseModel):
    perturbation_id: str = Field(min_length=2, max_length=300)
    name: str = Field(min_length=1, max_length=300)
    test_kind: RobustnessTestKind
    target: Literal[
        "input",
        "dataset",
        "feature",
        "prompt",
        "retrieval-context",
        "runtime",
        "other",
    ]
    parameters: dict[str, Any] = Field(default_factory=dict)
    implementation_ref: str | None = Field(default=None, max_length=2000)
    implementation_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RobustnessTestDefinition(BaseModel):
    robustness_test_id: str = Field(min_length=2, max_length=300)
    name: str = Field(min_length=1, max_length=300)
    benchmark_ref: str = Field(min_length=2, max_length=300)
    baseline_evaluation_run_ref: str = Field(min_length=2, max_length=300)
    perturbations: list[RobustnessPerturbation] = Field(default_factory=list)
    metric_refs: list[str] = Field(default_factory=list)
    tolerance_rules: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_perturbations(self):
        ids = [item.perturbation_id for item in self.perturbations]
        if len(ids) != len(set(ids)):
            raise ValueError("robustness perturbation ids must be unique")
        if not self.perturbations:
            raise ValueError("robustness test requires at least one perturbation")
        if not self.metric_refs:
            raise ValueError("robustness test requires at least one metric")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RobustnessTrialResult(BaseModel):
    perturbation_ref: str = Field(min_length=2, max_length=300)
    evaluation_run_ref: str = Field(min_length=2, max_length=300)
    metric_results: list[SliceMetricResult] = Field(default_factory=list)
    error_observation_refs: list[str] = Field(default_factory=list)
    passed: bool | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RobustnessRun(BaseModel):
    robustness_run_id: str = Field(min_length=2, max_length=300)
    robustness_test_ref: str = Field(min_length=2, max_length=300)
    ai_model_version_ref: str = Field(min_length=2, max_length=300)
    computational_job_refs: list[str] = Field(default_factory=list)
    runtime_environment_refs: list[str] = Field(default_factory=list)
    trial_results: list[RobustnessTrialResult] = Field(default_factory=list)
    overall_passed: bool | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_run(self):
        if not self.ai_model_version_ref.startswith("ai-model-version:"):
            raise ValueError("ai_model_version_ref must identify an AI model version")
        if not self.computational_job_refs:
            raise ValueError("robustness run requires computational job refs")
        if not self.runtime_environment_refs:
            raise ValueError("robustness run requires runtime environment refs")
        if not self.trial_results:
            raise ValueError("robustness run requires trial results")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class FailureCluster(BaseModel):
    failure_cluster_id: str = Field(min_length=2, max_length=300)
    name: str = Field(min_length=1, max_length=300)
    error_observation_refs: list[str] = Field(default_factory=list)
    dominant_failure_mode_ref: str | None = Field(default=None, max_length=300)
    shared_characteristics: dict[str, Any] = Field(default_factory=dict)
    clustering_method_ref: str | None = Field(default=None, max_length=300)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_cluster(self):
        if not self.error_observation_refs:
            raise ValueError("failure cluster requires error observations")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ErrorAnalysisReport(BaseModel):
    error_analysis_report_id: str = Field(min_length=2, max_length=300)
    ai_model_version_ref: str = Field(min_length=2, max_length=300)
    benchmark_refs: list[str] = Field(default_factory=list)
    evaluation_run_refs: list[str] = Field(default_factory=list)
    error_observation_refs: list[str] = Field(default_factory=list)
    slice_result_refs: list[str] = Field(default_factory=list)
    robustness_run_refs: list[str] = Field(default_factory=list)
    failure_cluster_refs: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1, max_length=20000)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_report(self):
        if not self.error_observation_refs and not self.robustness_run_refs:
            raise ValueError("error analysis report requires errors or robustness runs")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class AIRobustnessFailureBundle(BaseModel):
    failure_taxonomy: FailureTaxonomy
    error_observations: list[ErrorObservation] = Field(default_factory=list)
    slice_definitions: list[EvaluationSliceDefinition] = Field(default_factory=list)
    slice_results: list[SlicePerformanceResult] = Field(default_factory=list)
    robustness_tests: list[RobustnessTestDefinition] = Field(default_factory=list)
    robustness_runs: list[RobustnessRun] = Field(default_factory=list)
    failure_clusters: list[FailureCluster] = Field(default_factory=list)
    error_analysis_report: ErrorAnalysisReport

    @model_validator(mode="after")
    def validate_bundle(self):
        taxonomy_modes = {
            item.failure_mode_id for item in self.failure_taxonomy.failure_modes
        }
        for observation in self.error_observations:
            if observation.failure_mode_ref not in taxonomy_modes:
                raise ValueError("error observation references failure mode outside taxonomy")

        observation_ids = {
            item.error_observation_id for item in self.error_observations
        }
        for cluster in self.failure_clusters:
            missing = [
                ref for ref in cluster.error_observation_refs
                if ref not in observation_ids
            ]
            if missing:
                raise ValueError(
                    "failure cluster references observations outside bundle"
                )

        robustness_test_ids = {
            item.robustness_test_id for item in self.robustness_tests
        }
        for run in self.robustness_runs:
            if run.robustness_test_ref not in robustness_test_ids:
                raise ValueError("robustness run references test outside bundle")

        report = self.error_analysis_report
        report_error_refs = set(report.error_observation_refs)
        if not report_error_refs.issubset(observation_ids):
            raise ValueError("report references error observations outside bundle")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "failure_taxonomy_fingerprint_sha256": self.failure_taxonomy.fingerprint(),
            "error_observation_fingerprints": sorted(
                item.fingerprint() for item in self.error_observations
            ),
            "slice_definition_fingerprints": sorted(
                item.fingerprint() for item in self.slice_definitions
            ),
            "slice_result_fingerprints": sorted(
                item.fingerprint() for item in self.slice_results
            ),
            "robustness_test_fingerprints": sorted(
                item.fingerprint() for item in self.robustness_tests
            ),
            "robustness_run_fingerprints": sorted(
                item.fingerprint() for item in self.robustness_runs
            ),
            "failure_cluster_fingerprints": sorted(
                item.fingerprint() for item in self.failure_clusters
            ),
            "error_analysis_report_fingerprint_sha256": (
                self.error_analysis_report.fingerprint()
            ),
        })


def reference_robustness_failure_bundle() -> AIRobustnessFailureBundle:
    modes = [
        FailureModeDefinition(
            failure_mode_id="failure-mode:data-distribution-shift",
            name="Data Distribution Shift",
            domain=FailureDomain.data,
            description="Performance degradation associated with changed input distribution.",
            default_severity=FailureSeverity.high,
        ),
        FailureModeDefinition(
            failure_mode_id="failure-mode:subgroup-performance-degradation",
            name="Subgroup Performance Degradation",
            domain=FailureDomain.robustness,
            description="Material performance degradation on a defined evaluation slice.",
            default_severity=FailureSeverity.high,
        ),
        FailureModeDefinition(
            failure_mode_id="failure-mode:retrieval-context-loss",
            name="Retrieval Context Loss",
            domain=FailureDomain.retrieval,
            description="Relevant supporting context is absent from the assembled retrieval context.",
            default_severity=FailureSeverity.moderate,
        ),
    ]

    taxonomy = FailureTaxonomy(
        failure_taxonomy_id="failure-taxonomy:sc-ai:v1",
        name="Sustainable Catalyst AI Failure Taxonomy",
        version="1.0.0",
        failure_modes=modes,
        provenance={"purpose": "Platform Core v3.33.0 reference taxonomy"},
    )

    observation = ErrorObservation(
        error_observation_id="error-observation:reference:001",
        failure_mode_ref="failure-mode:subgroup-performance-degradation",
        severity=FailureSeverity.high,
        disposition=ErrorDisposition.confirmed,
        ai_model_version_ref="ai-model-version:reference-classifier:1.0.0",
        evaluation_run_ref="evaluation-run:reference-classifier:001",
        evaluation_case_ref="evaluation-case:reference:002",
        inference_run_ref="inference-run:evaluation:002",
        ai_artifact_refs=["ai-artifact:evaluation:002"],
        dataset_version_refs=["dataset-version:reference-classification:v1"],
        evidence_refs=["evidence:reference-error-case"],
        observed_behavior="Recall decreases on the reference subgroup under synthetic noise.",
        expected_behavior="Recall remains within the declared robustness tolerance.",
        confirmed_cause_refs=["cause:synthetic-noise-sensitivity"],
    )

    slice_def = EvaluationSliceDefinition(
        slice_id="slice:reference-subgroup",
        name="Reference Subgroup",
        dataset_version_ref="dataset-version:reference-classification:v1",
        criteria={"group": "reference-subgroup"},
        purpose="Measure subgroup-specific robustness.",
    )

    slice_result = SlicePerformanceResult(
        slice_result_id="slice-result:reference-subgroup:001",
        slice_ref=slice_def.slice_id,
        evaluation_run_ref="evaluation-run:reference-classifier:001",
        ai_model_version_ref="ai-model-version:reference-classifier:1.0.0",
        metric_results=[
            SliceMetricResult(
                metric_ref="metric:recall",
                value=0.81,
                baseline_value=0.94,
                delta=-0.13,
                passed=False,
                sample_count=50,
                confidence_interval=[0.75, 0.87],
            )
        ],
        error_observation_refs=[observation.error_observation_id],
    )

    perturbation = RobustnessPerturbation(
        perturbation_id="perturbation:gaussian-noise:reference",
        name="Reference Gaussian Noise",
        test_kind=RobustnessTestKind.noise,
        target="input",
        parameters={"stddev": 0.05, "seed": 433},
        implementation_ref="method:gaussian-input-noise",
        implementation_sha256="a" * 64,
    )

    robustness_test = RobustnessTestDefinition(
        robustness_test_id="robustness-test:reference-classifier-noise:v1",
        name="Reference Classifier Noise Robustness",
        benchmark_ref="benchmark:reference-classification:v1",
        baseline_evaluation_run_ref="evaluation-run:reference-classifier:001",
        perturbations=[perturbation],
        metric_refs=["metric:accuracy", "metric:recall"],
        tolerance_rules={
            "metric:accuracy": {"max_absolute_drop": 0.05},
            "metric:recall": {"max_absolute_drop": 0.08},
        },
    )

    trial = RobustnessTrialResult(
        perturbation_ref=perturbation.perturbation_id,
        evaluation_run_ref="evaluation-run:reference-classifier:noise:001",
        metric_results=[
            SliceMetricResult(
                metric_ref="metric:accuracy",
                value=0.91,
                baseline_value=0.96,
                delta=-0.05,
                passed=True,
                sample_count=100,
            ),
            SliceMetricResult(
                metric_ref="metric:recall",
                value=0.81,
                baseline_value=0.94,
                delta=-0.13,
                passed=False,
                sample_count=100,
            ),
        ],
        error_observation_refs=[observation.error_observation_id],
        passed=False,
    )

    robustness_run = RobustnessRun(
        robustness_run_id="robustness-run:reference-classifier-noise:001",
        robustness_test_ref=robustness_test.robustness_test_id,
        ai_model_version_ref="ai-model-version:reference-classifier:1.0.0",
        computational_job_refs=["job:reference-robustness-noise-001"],
        runtime_environment_refs=["environment:reference-python"],
        trial_results=[trial],
        overall_passed=False,
        provenance={
            "experiment_ref": "ai-experiment:reference-classifier-comparison:v1"
        },
    )

    cluster = FailureCluster(
        failure_cluster_id="failure-cluster:noise-sensitive-subgroup",
        name="Noise-sensitive subgroup failures",
        error_observation_refs=[observation.error_observation_id],
        dominant_failure_mode_ref=observation.failure_mode_ref,
        shared_characteristics={"perturbation": "gaussian-noise", "subgroup": True},
        clustering_method_ref="method:manual-forensic-grouping",
    )

    report = ErrorAnalysisReport(
        error_analysis_report_id="error-analysis-report:reference-classifier:v1",
        ai_model_version_ref="ai-model-version:reference-classifier:1.0.0",
        benchmark_refs=["benchmark:reference-classification:v1"],
        evaluation_run_refs=[
            "evaluation-run:reference-classifier:001",
            "evaluation-run:reference-classifier:noise:001",
        ],
        error_observation_refs=[observation.error_observation_id],
        slice_result_refs=[slice_result.slice_result_id],
        robustness_run_refs=[robustness_run.robustness_run_id],
        failure_cluster_refs=[cluster.failure_cluster_id],
        summary=(
            "Reference model remains within the accuracy tolerance under noise, "
            "but recall degrades beyond tolerance for the reference subgroup."
        ),
        limitations=[
            "Synthetic perturbation is not equivalent to observed production drift.",
            "Failure cause is limited to the evidence recorded in this reference run.",
        ],
        provenance={
            "descriptive_analysis_only": True,
            "core_certifies_robustness": False,
        },
    )

    return AIRobustnessFailureBundle(
        failure_taxonomy=taxonomy,
        error_observations=[observation],
        slice_definitions=[slice_def],
        slice_results=[slice_result],
        robustness_tests=[robustness_test],
        robustness_runs=[robustness_run],
        failure_clusters=[cluster],
        error_analysis_report=report,
    )


def contract_document() -> dict[str, Any]:
    reference = reference_robustness_failure_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            AI_MODEL_CONTRACT_VERSION,
            AI_INFERENCE_CONTRACT_VERSION,
            AI_EVALUATION_CONTRACT_VERSION,
            AI_EXPERIMENT_CONTRACT_VERSION,
        ],
        "object_types": [
            "FailureModeDefinition",
            "FailureTaxonomy",
            "ErrorObservation",
            "EvaluationSliceDefinition",
            "SliceMetricResult",
            "SlicePerformanceResult",
            "RobustnessPerturbation",
            "RobustnessTestDefinition",
            "RobustnessTrialResult",
            "RobustnessRun",
            "FailureCluster",
            "ErrorAnalysisReport",
            "AIRobustnessFailureBundle",
        ],
        "capabilities": {
            "failure_taxonomy": True,
            "case_level_error_observations": True,
            "evidence_linked_failure_records": True,
            "evaluation_slice_definitions": True,
            "slice_level_metrics": True,
            "baseline_delta_capture": True,
            "robustness_perturbations": True,
            "robustness_tolerance_rules": True,
            "robustness_trials": True,
            "failure_clustering": True,
            "error_analysis_reports": True,
            "model_version_binding": True,
            "evaluation_run_binding": True,
            "experiment_provenance_binding": True,
        },
        "integration": {
            "lab_executes_robustness_tests": True,
            "workspace_or_runtime_executes_jobs": True,
            "core_owns_failure_and_robustness_semantics": True,
            "core_duplicates_evaluation_storage": False,
            "core_duplicates_inference_artifacts": False,
        },
        "reference": {
            "failure_taxonomy_id": reference.failure_taxonomy.failure_taxonomy_id,
            "error_analysis_report_id": (
                reference.error_analysis_report.error_analysis_report_id
            ),
            "bundle_fingerprint_sha256": reference.fingerprint(),
        },
        "boundaries": {
            "core_executes_robustness_tests": False,
            "core_diagnoses_causality_autonomously": False,
            "core_certifies_model_robustness": False,
            "core_certifies_model_safety": False,
            "core_selects_best_model": False,
            "core_owns_failure_taxonomy_lineage_and_exchange": True,
        },
    }
