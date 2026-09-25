from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.32.0"
CONTRACT_VERSION = "sc.core.ai-experiment-reproducibility.v1"

AI_MODEL_CONTRACT_VERSION = "sc.core.ai-model.v1"
AI_TRAINING_LINEAGE_CONTRACT_VERSION = "sc.core.ai-training-lineage.v1"
AI_INFERENCE_CONTRACT_VERSION = "sc.core.ai-inference-provenance.v1"
PROMPT_CONTEXT_CONTRACT_VERSION = "sc.core.prompt-context-retrieval.v1"
AI_EVALUATION_CONTRACT_VERSION = "sc.core.ai-evaluation-benchmark.v1"
COMPUTATIONAL_JOB_CONTRACT_VERSION = "sc.core.computational-job.v1"
ENVIRONMENT_PROVENANCE_CONTRACT_VERSION = "sc.core.execution-environment-provenance.v1"


class ExperimentStatus(str, Enum):
    draft = "draft"
    declared = "declared"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    archived = "archived"


class ReproductionStatus(str, Enum):
    declared = "declared"
    running = "running"
    completed = "completed"
    failed = "failed"
    incomplete = "incomplete"


class ReproducibilityAssessmentKind(str, Enum):
    exact = "exact"
    compatible = "compatible"
    diverged = "diverged"
    incomplete = "incomplete"


class FactorKind(str, Enum):
    model_version = "model-version"
    dataset_version = "dataset-version"
    feature_set = "feature-set"
    prompt_version = "prompt-version"
    retrieval_context = "retrieval-context"
    hyperparameter = "hyperparameter"
    random_seed = "random-seed"
    runtime_environment = "runtime-environment"
    benchmark = "benchmark"
    other = "other"


class ExperimentalFactor(BaseModel):
    factor_id: str = Field(min_length=2, max_length=300)
    name: str = Field(min_length=1, max_length=300)
    factor_kind: FactorKind
    values: list[Any] = Field(default_factory=list)
    controlled: bool = True
    description: str | None = Field(default=None, max_length=5000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_values(self):
        if not self.values:
            raise ValueError("experimental factor must declare at least one value")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ExperimentalCondition(BaseModel):
    condition_id: str = Field(min_length=2, max_length=300)
    name: str = Field(min_length=1, max_length=300)
    factor_assignments: dict[str, Any] = Field(default_factory=dict)
    baseline: bool = False
    replication_count: int = Field(default=1, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class AIExperimentDefinition(BaseModel):
    experiment_id: str = Field(min_length=2, max_length=300)
    name: str = Field(min_length=1, max_length=300)
    objective: str = Field(min_length=1, max_length=20000)
    status: ExperimentStatus = ExperimentStatus.declared
    hypothesis_refs: list[str] = Field(default_factory=list)
    research_question_refs: list[str] = Field(default_factory=list)
    factors: list[ExperimentalFactor] = Field(default_factory=list)
    conditions: list[ExperimentalCondition] = Field(default_factory=list)
    benchmark_refs: list[str] = Field(default_factory=list)
    evaluation_metric_refs: list[str] = Field(default_factory=list)
    source_commit: str | None = Field(default=None, max_length=300)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_design(self):
        factor_ids = [item.factor_id for item in self.factors]
        if len(factor_ids) != len(set(factor_ids)):
            raise ValueError("experimental factor ids must be unique")

        condition_ids = [item.condition_id for item in self.conditions]
        if len(condition_ids) != len(set(condition_ids)):
            raise ValueError("experimental condition ids must be unique")

        known_factors = set(factor_ids)
        for condition in self.conditions:
            unknown = [
                factor_id
                for factor_id in condition.factor_assignments
                if factor_id not in known_factors
            ]
            if unknown:
                raise ValueError(
                    "condition references undeclared factors: " + ", ".join(unknown)
                )

        if self.conditions and not any(item.baseline for item in self.conditions):
            raise ValueError("experiment with conditions must declare a baseline condition")

        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("status", None)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class ExperimentRunBinding(BaseModel):
    experiment_run_binding_id: str = Field(min_length=2, max_length=300)
    experiment_ref: str = Field(min_length=2, max_length=300)
    condition_ref: str = Field(min_length=2, max_length=300)
    replicate_index: int = Field(ge=1)
    ai_model_version_refs: list[str] = Field(default_factory=list)
    training_lineage_refs: list[str] = Field(default_factory=list)
    inference_run_refs: list[str] = Field(default_factory=list)
    evaluation_run_refs: list[str] = Field(default_factory=list)
    computational_job_refs: list[str] = Field(default_factory=list)
    runtime_environment_refs: list[str] = Field(default_factory=list)
    prompt_version_refs: list[str] = Field(default_factory=list)
    retrieval_context_refs: list[str] = Field(default_factory=list)
    dataset_version_refs: list[str] = Field(default_factory=list)
    random_seed: int | None = None
    artifacts: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_run_binding(self):
        if not self.computational_job_refs:
            raise ValueError("experiment run binding requires at least one computational job")
        if not self.runtime_environment_refs:
            raise ValueError("experiment run binding requires at least one runtime environment")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReproducibilityRequirement(BaseModel):
    requirement_id: str = Field(min_length=2, max_length=300)
    component_kind: Literal[
        "model-version",
        "dataset-version",
        "feature-set",
        "prompt-version",
        "retrieval-context",
        "benchmark",
        "runtime-environment",
        "computational-job",
        "source-commit",
        "artifact",
        "other",
    ]
    component_ref: str = Field(min_length=1, max_length=2000)
    expected_fingerprint_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    strict: bool = True
    notes: str | None = Field(default=None, max_length=5000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReproducibilityPackageArtifact(BaseModel):
    package_artifact_id: str = Field(min_length=2, max_length=300)
    artifact_kind: Literal[
        "manifest",
        "source",
        "configuration",
        "environment-lock",
        "dataset-manifest",
        "model-artifact",
        "prompt",
        "benchmark",
        "result",
        "report",
        "log",
        "other",
    ]
    uri: str | None = Field(default=None, max_length=4000)
    content_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    size_bytes: int | None = Field(default=None, ge=0)
    media_type: str | None = Field(default=None, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_identity(self):
        if self.uri is None and self.content_sha256 is None:
            raise ValueError("reproducibility package artifact requires URI or content hash")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class AIExperimentReproducibilityPackage(BaseModel):
    reproducibility_package_id: str = Field(min_length=2, max_length=300)
    experiment_ref: str = Field(min_length=2, max_length=300)
    experiment_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    run_binding_refs: list[str] = Field(default_factory=list)
    requirements: list[ReproducibilityRequirement] = Field(default_factory=list)
    artifacts: list[ReproducibilityPackageArtifact] = Field(default_factory=list)
    source_commit: str | None = Field(default=None, max_length=300)
    package_format_version: str = Field(default="1.0.0", min_length=1, max_length=120)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_package(self):
        req_ids = [item.requirement_id for item in self.requirements]
        if len(req_ids) != len(set(req_ids)):
            raise ValueError("reproducibility requirement ids must be unique")

        artifact_ids = [item.package_artifact_id for item in self.artifacts]
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("reproducibility package artifact ids must be unique")

        if not self.run_binding_refs:
            raise ValueError("reproducibility package requires at least one run binding")
        if not self.requirements:
            raise ValueError("reproducibility package requires at least one requirement")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class ReproductionObservation(BaseModel):
    requirement_ref: str = Field(min_length=2, max_length=300)
    observed_component_ref: str | None = Field(default=None, max_length=2000)
    observed_fingerprint_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    matched: bool | None = None
    deviation: str | None = Field(default=None, max_length=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReproductionAttempt(BaseModel):
    reproduction_attempt_id: str = Field(min_length=2, max_length=300)
    reproducibility_package_ref: str = Field(min_length=2, max_length=300)
    status: ReproductionStatus = ReproductionStatus.declared
    computational_job_refs: list[str] = Field(default_factory=list)
    runtime_environment_refs: list[str] = Field(default_factory=list)
    reproduced_run_binding_refs: list[str] = Field(default_factory=list)
    observations: list[ReproductionObservation] = Field(default_factory=list)
    output_artifact_refs: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_attempt(self):
        observation_refs = [item.requirement_ref for item in self.observations]
        if len(observation_refs) != len(set(observation_refs)):
            raise ValueError("reproduction observations must be unique per requirement_ref")

        if self.status == ReproductionStatus.completed and not self.observations:
            raise ValueError("completed reproduction attempt requires observations")

        if (
            self.started_at is not None
            and self.completed_at is not None
            and self.completed_at < self.started_at
        ):
            raise ValueError("completed_at cannot precede started_at")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        for key in ("status", "started_at", "completed_at", "created_at"):
            payload.pop(key, None)
        return canonical_sha256(payload)


class ReproducibilityAssessment(BaseModel):
    reproducibility_assessment_id: str = Field(min_length=2, max_length=300)
    reproducibility_package_ref: str = Field(min_length=2, max_length=300)
    reproduction_attempt_ref: str = Field(min_length=2, max_length=300)
    assessment: ReproducibilityAssessmentKind
    strict_requirements_total: int = Field(ge=0)
    strict_requirements_matched: int = Field(ge=0)
    non_strict_requirements_total: int = Field(ge=0)
    non_strict_requirements_matched: int = Field(ge=0)
    deviations: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_counts(self):
        if self.strict_requirements_matched > self.strict_requirements_total:
            raise ValueError("strict matched count exceeds total")
        if self.non_strict_requirements_matched > self.non_strict_requirements_total:
            raise ValueError("non-strict matched count exceeds total")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class AIExperimentPackageBundle(BaseModel):
    experiment: AIExperimentDefinition
    run_bindings: list[ExperimentRunBinding] = Field(default_factory=list)
    reproducibility_package: AIExperimentReproducibilityPackage
    reproduction_attempts: list[ReproductionAttempt] = Field(default_factory=list)
    assessments: list[ReproducibilityAssessment] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.reproducibility_package.experiment_ref != self.experiment.experiment_id:
            raise ValueError("package experiment_ref must match experiment")

        if (
            self.reproducibility_package.experiment_fingerprint_sha256
            != self.experiment.fingerprint()
        ):
            raise ValueError("package experiment fingerprint must match experiment")

        run_ids = {item.experiment_run_binding_id for item in self.run_bindings}
        missing = [
            ref
            for ref in self.reproducibility_package.run_binding_refs
            if ref not in run_ids
        ]
        if missing:
            raise ValueError(
                "package references run bindings not present in bundle: "
                + ", ".join(missing)
            )

        package_id = self.reproducibility_package.reproducibility_package_id
        for attempt in self.reproduction_attempts:
            if attempt.reproducibility_package_ref != package_id:
                raise ValueError("reproduction attempt must reference package")

        attempt_ids = {item.reproduction_attempt_id for item in self.reproduction_attempts}
        for assessment in self.assessments:
            if assessment.reproducibility_package_ref != package_id:
                raise ValueError("assessment must reference package")
            if assessment.reproduction_attempt_ref not in attempt_ids:
                raise ValueError("assessment references attempt not present in bundle")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "experiment_fingerprint_sha256": self.experiment.fingerprint(),
            "run_binding_fingerprints": sorted(
                item.fingerprint() for item in self.run_bindings
            ),
            "reproducibility_package_fingerprint_sha256": (
                self.reproducibility_package.fingerprint()
            ),
            "reproduction_attempt_fingerprints": sorted(
                item.fingerprint() for item in self.reproduction_attempts
            ),
            "assessment_fingerprints": sorted(
                item.fingerprint() for item in self.assessments
            ),
        })


def reference_experiment_bundle() -> AIExperimentPackageBundle:
    factors = [
        ExperimentalFactor(
            factor_id="factor:model-version",
            name="Model Version",
            factor_kind=FactorKind.model_version,
            values=[
                "ai-model-version:reference-classifier:0.9.0",
                "ai-model-version:reference-classifier:1.0.0",
            ],
        ),
        ExperimentalFactor(
            factor_id="factor:random-seed",
            name="Random Seed",
            factor_kind=FactorKind.random_seed,
            values=[432],
        ),
    ]

    conditions = [
        ExperimentalCondition(
            condition_id="condition:baseline",
            name="Baseline",
            factor_assignments={
                "factor:model-version": "ai-model-version:reference-classifier:0.9.0",
                "factor:random-seed": 432,
            },
            baseline=True,
        ),
        ExperimentalCondition(
            condition_id="condition:candidate",
            name="Candidate",
            factor_assignments={
                "factor:model-version": "ai-model-version:reference-classifier:1.0.0",
                "factor:random-seed": 432,
            },
            baseline=False,
        ),
    ]

    experiment = AIExperimentDefinition(
        experiment_id="ai-experiment:reference-classifier-comparison:v1",
        name="Reference Classifier Controlled Comparison",
        objective=(
            "Compare two exact classifier model versions on the same benchmark "
            "while holding evaluation data and random seed constant."
        ),
        status=ExperimentStatus.completed,
        hypothesis_refs=["hypothesis:reference-classifier-improves-f1"],
        factors=factors,
        conditions=conditions,
        benchmark_refs=["benchmark:reference-classification:v1"],
        evaluation_metric_refs=["metric:accuracy", "metric:f1-macro"],
        source_commit="reference-experiment-commit",
        provenance={
            "descriptive_evidence_only": True,
            "core_selects_winner": False,
        },
    )

    baseline_run = ExperimentRunBinding(
        experiment_run_binding_id="experiment-run-binding:baseline:001",
        experiment_ref=experiment.experiment_id,
        condition_ref="condition:baseline",
        replicate_index=1,
        ai_model_version_refs=["ai-model-version:reference-classifier:0.9.0"],
        inference_run_refs=["inference-run:evaluation:baseline"],
        evaluation_run_refs=["evaluation-run:reference-classifier:legacy"],
        computational_job_refs=["job:reference-evaluation-baseline"],
        runtime_environment_refs=["environment:reference-python"],
        dataset_version_refs=["dataset-version:reference-classification:v1"],
        random_seed=432,
        artifacts=["benchmark-result:reference-classifier:legacy"],
    )

    candidate_run = ExperimentRunBinding(
        experiment_run_binding_id="experiment-run-binding:candidate:001",
        experiment_ref=experiment.experiment_id,
        condition_ref="condition:candidate",
        replicate_index=1,
        ai_model_version_refs=["ai-model-version:reference-classifier:1.0.0"],
        inference_run_refs=["inference-run:evaluation:candidate"],
        evaluation_run_refs=["evaluation-run:reference-classifier:001"],
        computational_job_refs=["job:reference-evaluation-001"],
        runtime_environment_refs=["environment:reference-python"],
        dataset_version_refs=["dataset-version:reference-classification:v1"],
        random_seed=432,
        artifacts=["benchmark-result:reference-classifier:001"],
    )

    requirements = [
        ReproducibilityRequirement(
            requirement_id="repro-req:experiment-source",
            component_kind="source-commit",
            component_ref="reference-experiment-commit",
            expected_fingerprint_sha256="1" * 64,
            strict=True,
        ),
        ReproducibilityRequirement(
            requirement_id="repro-req:dataset",
            component_kind="dataset-version",
            component_ref="dataset-version:reference-classification:v1",
            expected_fingerprint_sha256="2" * 64,
            strict=True,
        ),
        ReproducibilityRequirement(
            requirement_id="repro-req:environment",
            component_kind="runtime-environment",
            component_ref="environment:reference-python",
            expected_fingerprint_sha256="3" * 64,
            strict=True,
        ),
        ReproducibilityRequirement(
            requirement_id="repro-req:benchmark",
            component_kind="benchmark",
            component_ref="benchmark:reference-classification:v1",
            expected_fingerprint_sha256="4" * 64,
            strict=True,
        ),
    ]

    package = AIExperimentReproducibilityPackage(
        reproducibility_package_id="repro-package:reference-classifier-comparison:v1",
        experiment_ref=experiment.experiment_id,
        experiment_fingerprint_sha256=experiment.fingerprint(),
        run_binding_refs=[
            baseline_run.experiment_run_binding_id,
            candidate_run.experiment_run_binding_id,
        ],
        requirements=requirements,
        artifacts=[
            ReproducibilityPackageArtifact(
                package_artifact_id="repro-artifact:manifest",
                artifact_kind="manifest",
                content_sha256="5" * 64,
                media_type="application/json",
            ),
            ReproducibilityPackageArtifact(
                package_artifact_id="repro-artifact:report",
                artifact_kind="report",
                content_sha256="6" * 64,
                media_type="application/pdf",
            ),
        ],
        source_commit="reference-experiment-commit",
        provenance={
            "package_purpose": "Platform Core v3.32.0 reproducibility proof",
        },
    )

    observations = [
        ReproductionObservation(
            requirement_ref=item.requirement_id,
            observed_component_ref=item.component_ref,
            observed_fingerprint_sha256=item.expected_fingerprint_sha256,
            matched=True,
        )
        for item in requirements
    ]

    attempt = ReproductionAttempt(
        reproduction_attempt_id="reproduction-attempt:reference:001",
        reproducibility_package_ref=package.reproducibility_package_id,
        status=ReproductionStatus.completed,
        computational_job_refs=[
            "job:reproduce-reference-baseline",
            "job:reproduce-reference-candidate",
        ],
        runtime_environment_refs=["environment:reference-python"],
        reproduced_run_binding_refs=[
            baseline_run.experiment_run_binding_id,
            candidate_run.experiment_run_binding_id,
        ],
        observations=observations,
        output_artifact_refs=["artifact:reproduced-evaluation-bundle"],
        started_at=datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 9, 25, 12, 0, 5, tzinfo=timezone.utc),
    )

    assessment = ReproducibilityAssessment(
        reproducibility_assessment_id="repro-assessment:reference:001",
        reproducibility_package_ref=package.reproducibility_package_id,
        reproduction_attempt_ref=attempt.reproduction_attempt_id,
        assessment=ReproducibilityAssessmentKind.exact,
        strict_requirements_total=4,
        strict_requirements_matched=4,
        non_strict_requirements_total=0,
        non_strict_requirements_matched=0,
        deviations=[],
        provenance={"assessment_is_descriptive": True},
    )

    return AIExperimentPackageBundle(
        experiment=experiment,
        run_bindings=[baseline_run, candidate_run],
        reproducibility_package=package,
        reproduction_attempts=[attempt],
        assessments=[assessment],
    )


def contract_document() -> dict[str, Any]:
    reference = reference_experiment_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            AI_MODEL_CONTRACT_VERSION,
            AI_TRAINING_LINEAGE_CONTRACT_VERSION,
            AI_INFERENCE_CONTRACT_VERSION,
            PROMPT_CONTEXT_CONTRACT_VERSION,
            AI_EVALUATION_CONTRACT_VERSION,
            COMPUTATIONAL_JOB_CONTRACT_VERSION,
            ENVIRONMENT_PROVENANCE_CONTRACT_VERSION,
        ],
        "object_types": [
            "ExperimentalFactor",
            "ExperimentalCondition",
            "AIExperimentDefinition",
            "ExperimentRunBinding",
            "ReproducibilityRequirement",
            "ReproducibilityPackageArtifact",
            "AIExperimentReproducibilityPackage",
            "ReproductionObservation",
            "ReproductionAttempt",
            "ReproducibilityAssessment",
            "AIExperimentPackageBundle",
        ],
        "capabilities": {
            "controlled_experiment_definition": True,
            "baseline_condition_required": True,
            "factor_assignment_lineage": True,
            "replication_count_capture": True,
            "model_version_binding": True,
            "dataset_version_binding": True,
            "prompt_context_binding": True,
            "benchmark_binding": True,
            "computational_job_binding": True,
            "runtime_environment_binding": True,
            "package_manifest_identity": True,
            "strict_reproducibility_requirements": True,
            "reproduction_attempts": True,
            "requirement_level_observations": True,
            "reproducibility_assessment": True,
        },
        "integration": {
            "lab_executes_experiments": True,
            "workspace_or_runtime_executes_jobs": True,
            "core_owns_experiment_and_package_semantics": True,
            "core_duplicates_dataset_storage": False,
            "core_duplicates_model_artifacts": False,
            "core_duplicates_evaluation_storage": False,
        },
        "reference": {
            "experiment_id": reference.experiment.experiment_id,
            "reproducibility_package_id": (
                reference.reproducibility_package.reproducibility_package_id
            ),
            "bundle_fingerprint_sha256": reference.fingerprint(),
        },
        "boundaries": {
            "core_executes_experiments": False,
            "core_selects_winning_condition": False,
            "core_certifies_scientific_validity": False,
            "core_declares_reproducibility_from_metrics_alone": False,
            "core_owns_identity_lineage_and_reproduction_contracts": True,
        },
    }
