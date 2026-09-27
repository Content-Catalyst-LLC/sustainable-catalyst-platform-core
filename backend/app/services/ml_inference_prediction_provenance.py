from __future__ import annotations

import math
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .machine_learning_models import MLModelBundle, reference_ml_model_bundle
from .ml_dataset_provenance import MLDatasetFeatureTransformationLineageBundle, reference_dataset_feature_transformation_bundle
from .ml_embedding_representation import MLRepresentationIntelligenceBundle, reference_representation_intelligence_bundle

CORE_RELEASE = "3.63.0"
CONTRACT_VERSION = "sc.core.neural-inference-prediction-provenance.v1"


def _finite(value: float, label: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")


class MLInferenceMode(str, Enum):
    batch = "batch"
    online = "online"
    streaming = "streaming"
    interactive = "interactive"
    scheduled = "scheduled"
    reproduction = "reproduction"


class MLPredictionKind(str, Enum):
    point = "point"
    class_label = "class-label"
    probability_vector = "probability-vector"
    distribution = "distribution"
    ranking_score = "ranking-score"
    anomaly_score = "anomaly-score"
    forecast = "forecast"
    structured = "structured"


class MLInferenceInputBindingRecord(BaseModel):
    input_binding_id: str = Field(min_length=2, max_length=500)
    tensor_input_ref: str = Field(min_length=2, max_length=500)
    source_object_ref: str = Field(min_length=2, max_length=1000)
    dataset_partition_ref: str = Field(min_length=2, max_length=500)
    feature_schema_ref: str = Field(min_length=2, max_length=500)
    sample_index: int | None = Field(default=None, ge=0)
    batch_index: int | None = Field(default=None, ge=0)
    input_artifact_ref: str | None = Field(default=None, max_length=1000)
    input_artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLInferenceRunRecord(BaseModel):
    inference_run_id: str = Field(min_length=2, max_length=500)
    inference_plan_ref: str = Field(min_length=2, max_length=500)
    model_spec_ref: str = Field(min_length=2, max_length=500)
    model_version_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str = Field(min_length=2, max_length=500)
    runtime_binding_ref: str = Field(min_length=2, max_length=500)
    environment_ref: str | None = Field(default=None, max_length=500)
    computational_job_ref: str | None = Field(default=None, max_length=1000)
    inference_mode: MLInferenceMode
    input_binding_refs: list[str] = Field(min_length=1)
    deterministic_requested: bool | None = None
    started_at: str | None = Field(default=None, max_length=80)
    completed_at: str | None = Field(default=None, max_length=80)
    output_artifact_ref: str | None = Field(default=None, max_length=1000)
    output_artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_run(self):
        if len(self.input_binding_refs) != len(set(self.input_binding_refs)):
            raise ValueError("inference input_binding_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLClassScoreRecord(BaseModel):
    label: str = Field(min_length=1, max_length=500)
    score: float
    probability: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_score(self):
        _finite(self.score, "class score")
        if self.probability is not None:
            _finite(self.probability, "class probability")
        return self


class MLPredictionRecord(BaseModel):
    prediction_id: str = Field(min_length=2, max_length=500)
    inference_run_ref: str = Field(min_length=2, max_length=500)
    input_binding_ref: str = Field(min_length=2, max_length=500)
    output_ref: str = Field(min_length=1, max_length=500)
    prediction_kind: MLPredictionKind
    predicted_value: float | int | str | bool | None = None
    unit: str | None = Field(default=None, max_length=120)
    class_scores: list[MLClassScoreRecord] = Field(default_factory=list)
    distribution_artifact_ref: str | None = Field(default=None, max_length=1000)
    distribution_artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    generated_at: str | None = Field(default=None, max_length=80)
    evidence_promotion_allowed: Literal[False] = False
    claim_promotion_allowed: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_prediction(self):
        if isinstance(self.predicted_value, float):
            _finite(self.predicted_value, "predicted value")
        if self.prediction_kind in {MLPredictionKind.point, MLPredictionKind.class_label, MLPredictionKind.ranking_score, MLPredictionKind.anomaly_score, MLPredictionKind.forecast} and self.predicted_value is None:
            raise ValueError("prediction kind requires predicted_value")
        if self.prediction_kind == MLPredictionKind.probability_vector:
            if not self.class_scores:
                raise ValueError("probability-vector prediction requires class_scores")
            probabilities = [x.probability for x in self.class_scores]
            if any(x is None for x in probabilities):
                raise ValueError("probability-vector class_scores require probabilities")
            if not math.isclose(sum(float(x) for x in probabilities), 1.0, rel_tol=1e-6, abs_tol=1e-6):
                raise ValueError("probability-vector probabilities must sum to 1")
        labels = [x.label for x in self.class_scores]
        if len(labels) != len(set(labels)):
            raise ValueError("prediction class labels must be unique")
        if self.prediction_kind == MLPredictionKind.distribution and self.distribution_artifact_ref is None:
            raise ValueError("distribution prediction requires distribution_artifact_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLPredictionConfidenceBindingRecord(BaseModel):
    confidence_binding_id: str = Field(min_length=2, max_length=500)
    prediction_ref: str = Field(min_length=2, max_length=500)
    calibration_refs: list[str] = Field(default_factory=list)
    confidence_distribution_refs: list[str] = Field(default_factory=list)
    prediction_interval_refs: list[str] = Field(default_factory=list)
    uncertainty_estimate_refs: list[str] = Field(default_factory=list)
    ood_indicator_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_binding(self):
        groups = [self.calibration_refs, self.confidence_distribution_refs, self.prediction_interval_refs, self.uncertainty_estimate_refs, self.ood_indicator_refs]
        if not any(groups):
            raise ValueError("prediction confidence binding requires at least one referenced uncertainty/calibration object")
        for refs in groups:
            if len(refs) != len(set(refs)):
                raise ValueError("prediction confidence references must be unique within each family")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLPredictionInterpretationBindingRecord(BaseModel):
    interpretation_binding_id: str = Field(min_length=2, max_length=500)
    prediction_ref: str = Field(min_length=2, max_length=500)
    feature_attribution_refs: list[str] = Field(default_factory=list)
    saliency_refs: list[str] = Field(default_factory=list)
    attention_refs: list[str] = Field(default_factory=list)
    counterfactual_refs: list[str] = Field(default_factory=list)
    embedding_explanation_refs: list[str] = Field(default_factory=list)
    similarity_result_refs: list[str] = Field(default_factory=list)
    projection_refs: list[str] = Field(default_factory=list)
    cluster_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_binding(self):
        groups = [self.feature_attribution_refs, self.saliency_refs, self.attention_refs, self.counterfactual_refs, self.embedding_explanation_refs, self.similarity_result_refs, self.projection_refs, self.cluster_refs]
        if not any(groups):
            raise ValueError("prediction interpretation binding requires at least one interpretation reference")
        for refs in groups:
            if len(refs) != len(set(refs)):
                raise ValueError("prediction interpretation references must be unique within each family")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLInferencePredictionProvenanceBundle(BaseModel):
    ml_model_bundle: MLModelBundle
    dataset_lineage_bundle: MLDatasetFeatureTransformationLineageBundle
    representation_bundle: MLRepresentationIntelligenceBundle
    input_bindings: list[MLInferenceInputBindingRecord] = Field(min_length=1)
    inference_runs: list[MLInferenceRunRecord] = Field(min_length=1)
    predictions: list[MLPredictionRecord] = Field(min_length=1)
    confidence_bindings: list[MLPredictionConfidenceBindingRecord] = Field(default_factory=list)
    interpretation_bindings: list[MLPredictionInterpretationBindingRecord] = Field(default_factory=list)
    dataset_lineage_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    representation_lineage_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_bundle(self):
        ml = self.ml_model_bundle
        dataset = self.dataset_lineage_bundle
        rep = self.representation_bundle
        if ml.inference_plan is None:
            raise ValueError("ML model bundle must include an inference plan")
        plan = ml.inference_plan
        if dataset.model_spec.model_spec_id != ml.model_spec.model_spec_id:
            raise ValueError("dataset lineage model specification must match inference model specification")
        if rep.model_spec_ref != ml.model_spec.model_spec_id:
            raise ValueError("representation lineage model_spec_ref must match inference model specification")
        if self.dataset_lineage_fingerprint_sha256 != dataset.fingerprint():
            raise ValueError("dataset lineage fingerprint must match bundled v3.59 object")
        if self.representation_lineage_fingerprint_sha256 != rep.fingerprint():
            raise ValueError("representation lineage fingerprint must match bundled v3.62 object")

        tensor_by_id = {x.tensor_input_id: x for x in dataset.tensor_inputs}
        partition_by_id = {x.partition_id: x for x in dataset.partitions}
        input_by_id = {x.input_binding_id: x for x in self.input_bindings}
        run_by_id = {x.inference_run_id: x for x in self.inference_runs}
        prediction_by_id = {x.prediction_id: x for x in self.predictions}

        for label, values in (
            ("inference input binding", list(input_by_id)),
            ("inference run", list(run_by_id)),
            ("prediction", list(prediction_by_id)),
            ("confidence binding", [x.confidence_binding_id for x in self.confidence_bindings]),
            ("interpretation binding", [x.interpretation_binding_id for x in self.interpretation_bindings]),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} ids must be unique")

        feature_schema_ref = ml.model_spec.feature_schema.schema_id
        target_names = set(ml.model_spec.feature_schema.target_names)
        for binding in self.input_bindings:
            tensor = tensor_by_id.get(binding.tensor_input_ref)
            if tensor is None:
                raise ValueError("inference input tensor_input_ref must resolve within v3.59 lineage")
            if binding.dataset_partition_ref not in partition_by_id:
                raise ValueError("inference input dataset_partition_ref must resolve within v3.59 lineage")
            if binding.feature_schema_ref != feature_schema_ref:
                raise ValueError("inference input feature_schema_ref must match model feature schema")
            if tensor.model_spec_ref != ml.model_spec.model_spec_id:
                raise ValueError("inference input tensor model_spec_ref must match inference model")
            if binding.input_artifact_ref and binding.input_artifact_ref != tensor.artifact_ref:
                raise ValueError("inference input artifact must match referenced tensor artifact")
            if binding.input_artifact_sha256 and tensor.artifact_sha256 and binding.input_artifact_sha256 != tensor.artifact_sha256:
                raise ValueError("inference input artifact hash must match referenced tensor artifact hash")

        for run in self.inference_runs:
            if run.inference_plan_ref != plan.inference_plan_id:
                raise ValueError("inference run inference_plan_ref must match bundled inference plan")
            if run.model_spec_ref != ml.model_spec.model_spec_id:
                raise ValueError("inference run model_spec_ref must match bundled model specification")
            if run.model_version_ref != plan.model_version_ref:
                raise ValueError("inference run model_version_ref must match inference plan")
            if run.runtime_binding_ref != plan.runtime_binding_ref:
                raise ValueError("inference run runtime_binding_ref must match inference plan")
            if run.checkpoint_ref != rep.checkpoint_ref:
                raise ValueError("inference run checkpoint_ref must resolve to v3.62 representation lineage checkpoint")
            for ref in run.input_binding_refs:
                if ref not in input_by_id:
                    raise ValueError("inference run input_binding_ref must resolve within bundle")

        for prediction in self.predictions:
            run = run_by_id.get(prediction.inference_run_ref)
            if run is None:
                raise ValueError("prediction inference_run_ref must resolve within bundle")
            if prediction.input_binding_ref not in run.input_binding_refs:
                raise ValueError("prediction input_binding_ref must be consumed by referenced inference run")
            if target_names and prediction.output_ref not in target_names and not prediction.output_ref.startswith("output:"):
                raise ValueError("prediction output_ref must resolve to model target or declared output ref")

        eval_bundle = rep.explainability_bundle.evaluation_bundle
        explain_bundle = rep.explainability_bundle
        calibration_ids = {x.calibration_id for x in eval_bundle.calibration_records}
        confidence_ids = {x.confidence_distribution_id for x in eval_bundle.confidence_distributions}
        interval_ids = {x.prediction_interval_id for x in eval_bundle.prediction_intervals}
        uncertainty_ids = {x.uncertainty_estimate_id for x in eval_bundle.uncertainty_estimates}
        ood_ids = {x.ood_indicator_id for x in eval_bundle.ood_indicators}
        attr_ids = {x.feature_attribution_id for x in explain_bundle.feature_attributions}
        saliency_ids = {x.saliency_map_id for x in explain_bundle.saliency_maps}
        attention_ids = {x.attention_explanation_id for x in explain_bundle.attention_explanations}
        counterfactual_ids = {x.counterfactual_id for x in explain_bundle.counterfactual_explanations}
        embedding_explanation_ids = {x.embedding_explanation_id for x in explain_bundle.embedding_explanations}
        similarity_ids = {x.similarity_result_id for x in rep.similarity_results}
        projection_ids = {x.projection_id for x in rep.vector_projections}
        cluster_ids = {x.cluster_id for x in rep.clusters}

        for binding in self.confidence_bindings:
            prediction = prediction_by_id.get(binding.prediction_ref)
            if prediction is None:
                raise ValueError("confidence binding prediction_ref must resolve within bundle")
            families = [
                (binding.calibration_refs, calibration_ids, "calibration"),
                (binding.confidence_distribution_refs, confidence_ids, "confidence distribution"),
                (binding.prediction_interval_refs, interval_ids, "prediction interval"),
                (binding.uncertainty_estimate_refs, uncertainty_ids, "uncertainty estimate"),
                (binding.ood_indicator_refs, ood_ids, "OOD indicator"),
            ]
            for refs, available, label in families:
                if set(refs) - available:
                    raise ValueError(f"confidence binding {label} refs must resolve to v3.60 objects")
            input_binding = input_by_id[prediction.input_binding_ref]
            for indicator in eval_bundle.ood_indicators:
                if indicator.ood_indicator_id in binding.ood_indicator_refs and indicator.sample_ref and indicator.sample_ref != input_binding.source_object_ref:
                    raise ValueError("OOD indicator sample_ref must match prediction input source object")

        for binding in self.interpretation_bindings:
            if binding.prediction_ref not in prediction_by_id:
                raise ValueError("interpretation binding prediction_ref must resolve within bundle")
            families = [
                (binding.feature_attribution_refs, attr_ids, "feature attribution"),
                (binding.saliency_refs, saliency_ids, "saliency"),
                (binding.attention_refs, attention_ids, "attention"),
                (binding.counterfactual_refs, counterfactual_ids, "counterfactual"),
                (binding.embedding_explanation_refs, embedding_explanation_ids, "embedding explanation"),
                (binding.similarity_result_refs, similarity_ids, "similarity result"),
                (binding.projection_refs, projection_ids, "projection"),
                (binding.cluster_refs, cluster_ids, "cluster"),
            ]
            for refs, available, label in families:
                if set(refs) - available:
                    raise ValueError(f"interpretation binding {label} refs must resolve to v3.61/v3.62 objects")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_inference_prediction_provenance_bundle() -> MLInferencePredictionProvenanceBundle:
    ml = reference_ml_model_bundle()
    dataset = reference_dataset_feature_transformation_bundle()
    rep = reference_representation_intelligence_bundle()
    validation_partition = rep.explainability_bundle.evaluation_bundle.dataset_partition.partition_id
    tensor = next(x for x in dataset.tensor_inputs if x.representation_ref.endswith(":validation"))
    source_sample = rep.explainability_bundle.feature_attributions[0].sample_ref or "sample:reference-energy:validation:001"
    input_binding = MLInferenceInputBindingRecord(
        input_binding_id="ml-inference-input:reference-energy:validation:001",
        tensor_input_ref=tensor.tensor_input_id,
        source_object_ref=source_sample,
        dataset_partition_ref=validation_partition,
        feature_schema_ref=ml.model_spec.feature_schema.schema_id,
        sample_index=0,
        batch_index=0,
        input_artifact_ref=tensor.artifact_ref,
        input_artifact_sha256=tensor.artifact_sha256,
    )
    plan = ml.inference_plan
    assert plan is not None
    run = MLInferenceRunRecord(
        inference_run_id="ml-inference-run:reference-energy:validation:001",
        inference_plan_ref=plan.inference_plan_id,
        model_spec_ref=ml.model_spec.model_spec_id,
        model_version_ref=plan.model_version_ref,
        checkpoint_ref=rep.checkpoint_ref,
        runtime_binding_ref=plan.runtime_binding_ref,
        environment_ref=ml.model_spec.runtime_bindings[0].environment_ref,
        computational_job_ref="workspace-job:reference-energy:inference:001",
        inference_mode=MLInferenceMode.batch,
        input_binding_refs=[input_binding.input_binding_id],
        deterministic_requested=True,
        started_at="2026-09-27T15:00:00Z",
        completed_at="2026-09-27T15:00:02Z",
        output_artifact_ref="artifact:reference-energy:predictions:001",
        output_artifact_sha256="8" * 64,
    )
    prediction = MLPredictionRecord(
        prediction_id="ml-prediction:reference-energy:validation:001",
        inference_run_ref=run.inference_run_id,
        input_binding_ref=input_binding.input_binding_id,
        output_ref="energy_kwh",
        prediction_kind=MLPredictionKind.point,
        predicted_value=4.8,
        unit="kWh",
        generated_at="2026-09-27T15:00:02Z",
    )
    eval_bundle = rep.explainability_bundle.evaluation_bundle
    confidence = MLPredictionConfidenceBindingRecord(
        confidence_binding_id="ml-prediction-confidence:reference-energy:validation:001",
        prediction_ref=prediction.prediction_id,
        calibration_refs=[x.calibration_id for x in eval_bundle.calibration_records],
        confidence_distribution_refs=[x.confidence_distribution_id for x in eval_bundle.confidence_distributions],
        prediction_interval_refs=[x.prediction_interval_id for x in eval_bundle.prediction_intervals],
        uncertainty_estimate_refs=[x.uncertainty_estimate_id for x in eval_bundle.uncertainty_estimates],
        ood_indicator_refs=[x.ood_indicator_id for x in eval_bundle.ood_indicators],
    )
    explain = rep.explainability_bundle
    interpretation = MLPredictionInterpretationBindingRecord(
        interpretation_binding_id="ml-prediction-interpretation:reference-energy:validation:001",
        prediction_ref=prediction.prediction_id,
        feature_attribution_refs=[x.feature_attribution_id for x in explain.feature_attributions if x.sample_ref == source_sample],
        saliency_refs=[x.saliency_map_id for x in explain.saliency_maps if x.sample_ref == source_sample],
        counterfactual_refs=[x.counterfactual_id for x in explain.counterfactual_explanations if x.sample_ref == source_sample],
        embedding_explanation_refs=[x.embedding_explanation_id for x in explain.embedding_explanations if x.sample_ref == source_sample],
        similarity_result_refs=[x.similarity_result_id for x in rep.similarity_results],
        projection_refs=[x.projection_id for x in rep.vector_projections],
        cluster_refs=[x.cluster_id for x in rep.clusters],
    )
    return MLInferencePredictionProvenanceBundle(
        ml_model_bundle=ml,
        dataset_lineage_bundle=dataset,
        representation_bundle=rep,
        input_bindings=[input_binding],
        inference_runs=[run],
        predictions=[prediction],
        confidence_bindings=[confidence],
        interpretation_bindings=[interpretation],
        dataset_lineage_fingerprint_sha256=dataset.fingerprint(),
        representation_lineage_fingerprint_sha256=rep.fingerprint(),
    )


def contract_document() -> dict[str, Any]:
    ref = reference_inference_prediction_provenance_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "object_types": [
            "MLInferenceInputBindingRecord",
            "MLInferenceRunRecord",
            "MLClassScoreRecord",
            "MLPredictionRecord",
            "MLPredictionConfidenceBindingRecord",
            "MLPredictionInterpretationBindingRecord",
            "MLInferencePredictionProvenanceBundle",
        ],
        "lineage_chain": [
            "governed-input",
            "model-and-checkpoint",
            "inference-run",
            "prediction",
            "confidence-and-uncertainty",
            "interpretation",
        ],
        "integration": {
            "extends_machine_learning_neural_model_foundation_v3570": True,
            "extends_dataset_feature_transformation_provenance_v3590": True,
            "extends_evaluation_calibration_uncertainty_v3600": True,
            "extends_explainability_model_interpretation_v3610": True,
            "extends_neural_embedding_representation_intelligence_v3620": True,
            "resolves_inference_plan_refs": True,
            "resolves_tensor_input_refs": True,
            "resolves_checkpoint_refs": True,
            "resolves_uncertainty_and_interpretation_refs": True,
            "workspace_remains_default_inference_compute_host": True,
        },
        "provenance_capabilities": {
            "source_bound_inference_inputs": True,
            "checkpoint_bound_inference_runs": True,
            "runtime_and_environment_lineage": True,
            "prediction_output_identity": True,
            "calibration_confidence_uncertainty_bindings": True,
            "ood_indicator_bindings": True,
            "explainability_bindings": True,
            "embedding_similarity_projection_bindings": True,
            "deterministic_bundle_fingerprint": True,
        },
        "governance": {
            "prediction_is_analytical_output_not_evidence": True,
            "prediction_is_not_observation": True,
            "confidence_is_not_truth_probability": True,
            "uncertainty_is_not_certainty_claim": True,
            "ood_flag_is_not_fact": True,
            "interpretation_is_not_causal_proof": True,
            "model_output_requires_source_model_and_runtime_lineage": True,
            "evidence_promotion_requires_explicit_downstream_research_step": True,
        },
        "boundaries": {
            "core_runs_inference": False,
            "core_executes_models": False,
            "core_generates_predictions": False,
            "core_calibrates_predictions": False,
            "core_estimates_uncertainty": False,
            "core_runs_ood_detection": False,
            "core_generates_explanations": False,
            "core_promotes_predictions_to_evidence": False,
            "core_promotes_predictions_to_claims": False,
            "core_autonomously_acts_on_predictions": False,
            "core_certifies_prediction_truth": False,
        },
        "reference": {
            "inference_run_id": ref.inference_runs[0].inference_run_id,
            "prediction_id": ref.predictions[0].prediction_id,
            "checkpoint_ref": ref.inference_runs[0].checkpoint_ref,
            "input_binding_id": ref.input_bindings[0].input_binding_id,
            "bundle_fingerprint_sha256": ref.fingerprint(),
        },
    }
