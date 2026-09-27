from __future__ import annotations

import math
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .ml_evaluation_uncertainty import (
    MLEvaluationCalibrationUncertaintyBundle,
    reference_evaluation_calibration_uncertainty_bundle,
)

CORE_RELEASE = "3.61.0"
CONTRACT_VERSION = "sc.core.explainability-model-interpretation.v1"


def _finite(value: float, label: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")


class MLExplanationScope(str, Enum):
    global_ = "global"
    cohort = "cohort"
    sample = "sample"
    feature = "feature"
    token = "token"
    spatial_region = "spatial-region"
    pairwise = "pairwise"
    model_comparison = "model-comparison"


class MLCounterfactualFeasibility(str, Enum):
    feasible = "feasible"
    infeasible = "infeasible"
    unknown = "unknown"


class MLFeatureAttributionValue(BaseModel):
    feature_ref: str = Field(min_length=1, max_length=500)
    attribution: float
    input_value: float | str | int | bool | None = None
    baseline_value: float | str | int | bool | None = None
    normalized_magnitude_share: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_value(self):
        _finite(self.attribution, "feature attribution")
        if isinstance(self.input_value, float): _finite(self.input_value, "feature input_value")
        if isinstance(self.baseline_value, float): _finite(self.baseline_value, "feature baseline_value")
        return self


class MLFeatureAttributionRecord(BaseModel):
    feature_attribution_id: str = Field(min_length=2, max_length=300)
    evaluation_ref: str = Field(min_length=2, max_length=500)
    partition_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str = Field(min_length=2, max_length=500)
    method: str = Field(min_length=1, max_length=240)
    scope: MLExplanationScope
    target_ref: str | None = Field(default=None, max_length=500)
    sample_ref: str | None = Field(default=None, max_length=500)
    feature_schema_ref: str | None = Field(default=None, max_length=500)
    baseline_description: str | None = Field(default=None, max_length=2000)
    values: list[MLFeatureAttributionValue] = Field(min_length=1)
    computation_ref: str | None = Field(default=None, max_length=1000)
    artifact_ref: str | None = Field(default=None, max_length=1000)
    artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    assumptions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_attributions(self):
        refs=[x.feature_ref for x in self.values]
        if len(refs)!=len(set(refs)): raise ValueError("feature attribution feature_refs must be unique")
        shares=[x.normalized_magnitude_share for x in self.values]
        if shares and all(x is not None for x in shares):
            if not math.isclose(sum(float(x) for x in shares),1.0,rel_tol=1e-6,abs_tol=1e-6):
                raise ValueError("normalized attribution magnitude shares must sum to 1")
        if self.scope in {MLExplanationScope.sample, MLExplanationScope.feature} and not self.sample_ref:
            raise ValueError("sample/feature attribution scope requires sample_ref")
        return self

    def fingerprint(self)->str: return canonical_sha256(self)


class MLSaliencyMapRecord(BaseModel):
    saliency_map_id: str = Field(min_length=2, max_length=300)
    evaluation_ref: str = Field(min_length=2, max_length=500)
    partition_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str = Field(min_length=2, max_length=500)
    method: str = Field(min_length=1, max_length=240)
    sample_ref: str = Field(min_length=1, max_length=500)
    target_ref: str | None = Field(default=None, max_length=500)
    source_artifact_ref: str | None = Field(default=None, max_length=1000)
    saliency_artifact_ref: str = Field(min_length=2, max_length=1000)
    saliency_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    coordinate_space: str = Field(min_length=1, max_length=240)
    shape: list[int] = Field(min_length=1)
    signed: bool = True
    normalization: str | None = Field(default=None, max_length=240)
    computation_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_saliency(self):
        if any(x<=0 for x in self.shape): raise ValueError("saliency shape dimensions must be positive")
        return self

    def fingerprint(self)->str: return canonical_sha256(self)


class MLAttentionWeight(BaseModel):
    key_ref: str = Field(min_length=1, max_length=500)
    weight: float = Field(ge=0.0)

    @model_validator(mode="after")
    def validate_weight(self):
        _finite(self.weight,"attention weight")
        return self


class MLAttentionExplanationRecord(BaseModel):
    attention_explanation_id: str = Field(min_length=2, max_length=300)
    evaluation_ref: str = Field(min_length=2, max_length=500)
    partition_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str = Field(min_length=2, max_length=500)
    sample_ref: str = Field(min_length=1, max_length=500)
    model_component_ref: str = Field(min_length=1, max_length=500)
    layer_ref: str | None = Field(default=None, max_length=500)
    head_ref: str | None = Field(default=None, max_length=500)
    query_ref: str = Field(min_length=1, max_length=500)
    weights: list[MLAttentionWeight] = Field(min_length=1)
    normalized: bool = True
    computation_ref: str | None = Field(default=None, max_length=1000)
    artifact_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_attention(self):
        keys=[x.key_ref for x in self.weights]
        if len(keys)!=len(set(keys)): raise ValueError("attention key_refs must be unique")
        if self.normalized and not math.isclose(sum(x.weight for x in self.weights),1.0,rel_tol=1e-6,abs_tol=1e-6):
            raise ValueError("normalized attention weights must sum to 1")
        return self

    def fingerprint(self)->str: return canonical_sha256(self)


class MLCounterfactualChange(BaseModel):
    feature_ref: str = Field(min_length=1, max_length=500)
    original_value: float | str | int | bool | None = None
    counterfactual_value: float | str | int | bool | None = None
    mutable: bool = True
    constraint_ref: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_change(self):
        if isinstance(self.original_value,float): _finite(self.original_value,"counterfactual original_value")
        if isinstance(self.counterfactual_value,float): _finite(self.counterfactual_value,"counterfactual counterfactual_value")
        if not self.mutable and self.original_value != self.counterfactual_value:
            raise ValueError("immutable feature cannot change in counterfactual")
        return self


class MLCounterfactualExplanationRecord(BaseModel):
    counterfactual_id: str = Field(min_length=2, max_length=300)
    evaluation_ref: str = Field(min_length=2, max_length=500)
    partition_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str = Field(min_length=2, max_length=500)
    sample_ref: str = Field(min_length=1, max_length=500)
    target_ref: str | None = Field(default=None, max_length=500)
    method: str = Field(min_length=1, max_length=240)
    objective: str = Field(min_length=1, max_length=2000)
    original_output: float | str | int | bool | None = None
    counterfactual_output: float | str | int | bool | None = None
    changes: list[MLCounterfactualChange] = Field(min_length=1)
    distance_metric: str | None = Field(default=None, max_length=240)
    distance_value: float | None = Field(default=None, ge=0.0)
    feasibility: MLCounterfactualFeasibility = MLCounterfactualFeasibility.unknown
    constraints_ref: str | None = Field(default=None, max_length=1000)
    computation_ref: str | None = Field(default=None, max_length=1000)
    artifact_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_counterfactual(self):
        refs=[x.feature_ref for x in self.changes]
        if len(refs)!=len(set(refs)): raise ValueError("counterfactual feature_refs must be unique")
        if not any(x.original_value != x.counterfactual_value for x in self.changes):
            raise ValueError("counterfactual must change at least one feature")
        if isinstance(self.original_output,float): _finite(self.original_output,"counterfactual original_output")
        if isinstance(self.counterfactual_output,float): _finite(self.counterfactual_output,"counterfactual counterfactual_output")
        if self.distance_value is not None: _finite(self.distance_value,"counterfactual distance_value")
        if self.distance_value is not None and not self.distance_metric:
            raise ValueError("counterfactual distance_value requires distance_metric")
        return self

    def fingerprint(self)->str: return canonical_sha256(self)


class MLEmbeddingNeighbor(BaseModel):
    item_ref: str = Field(min_length=1, max_length=500)
    rank: int = Field(ge=1)
    similarity: float
    label: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_neighbor(self):
        _finite(self.similarity,"embedding similarity")
        return self


class MLEmbeddingSpaceExplanationRecord(BaseModel):
    embedding_explanation_id: str = Field(min_length=2, max_length=300)
    evaluation_ref: str = Field(min_length=2, max_length=500)
    partition_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str = Field(min_length=2, max_length=500)
    sample_ref: str | None = Field(default=None, max_length=500)
    representation_ref: str = Field(min_length=1, max_length=500)
    embedding_space_ref: str = Field(min_length=1, max_length=500)
    method: str = Field(min_length=1, max_length=240)
    dimensions: int | None = Field(default=None, ge=1)
    neighbors: list[MLEmbeddingNeighbor] = Field(default_factory=list)
    cluster_ref: str | None = Field(default=None, max_length=500)
    projection_artifact_ref: str | None = Field(default=None, max_length=1000)
    projection_artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    computation_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_embedding(self):
        refs=[x.item_ref for x in self.neighbors]; ranks=[x.rank for x in self.neighbors]
        if len(refs)!=len(set(refs)): raise ValueError("embedding neighbor item_refs must be unique")
        if len(ranks)!=len(set(ranks)): raise ValueError("embedding neighbor ranks must be unique")
        if ranks and sorted(ranks)!=list(range(1,len(ranks)+1)): raise ValueError("embedding neighbor ranks must be contiguous from 1")
        return self

    def fingerprint(self)->str: return canonical_sha256(self)


class MLModelComparisonInterpretationRecord(BaseModel):
    comparison_interpretation_id: str = Field(min_length=2, max_length=300)
    partition_ref: str = Field(min_length=2, max_length=500)
    method: str = Field(min_length=1, max_length=240)
    compared_model_refs: list[str] = Field(min_length=2)
    evaluation_refs: list[str] = Field(min_length=2)
    checkpoint_refs: list[str] = Field(min_length=2)
    metric_deltas: dict[str, float] = Field(default_factory=dict)
    interpretation_statements: list[str] = Field(min_length=1)
    computation_ref: str | None = Field(default=None, max_length=1000)
    artifact_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_comparison(self):
        n=len(self.compared_model_refs)
        if len(self.evaluation_refs)!=n or len(self.checkpoint_refs)!=n:
            raise ValueError("model, evaluation, and checkpoint comparison refs must have equal lengths")
        if len(set(self.compared_model_refs))!=n: raise ValueError("compared_model_refs must be unique")
        if len(set(self.evaluation_refs))!=n: raise ValueError("evaluation_refs must be unique")
        if len(set(self.checkpoint_refs))!=n: raise ValueError("checkpoint_refs must be unique")
        for name,value in self.metric_deltas.items(): _finite(value,f"metric delta {name}")
        return self

    def fingerprint(self)->str: return canonical_sha256(self)


class MLExplainabilityInterpretationBundle(BaseModel):
    model_spec_ref: str = Field(min_length=2, max_length=500)
    training_run_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str = Field(min_length=2, max_length=500)
    evaluation_bundle: MLEvaluationCalibrationUncertaintyBundle
    feature_attributions: list[MLFeatureAttributionRecord] = Field(default_factory=list)
    saliency_maps: list[MLSaliencyMapRecord] = Field(default_factory=list)
    attention_explanations: list[MLAttentionExplanationRecord] = Field(default_factory=list)
    counterfactual_explanations: list[MLCounterfactualExplanationRecord] = Field(default_factory=list)
    embedding_explanations: list[MLEmbeddingSpaceExplanationRecord] = Field(default_factory=list)
    model_comparisons: list[MLModelComparisonInterpretationRecord] = Field(default_factory=list)
    evaluation_uncertainty_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_bundle(self):
        e=self.evaluation_bundle
        if self.model_spec_ref != e.model_spec_ref: raise ValueError("model_spec_ref must match evaluation bundle")
        if self.training_run_ref != e.training_run_ref: raise ValueError("training_run_ref must match evaluation bundle")
        if self.checkpoint_ref != e.checkpoint_ref: raise ValueError("checkpoint_ref must match evaluation bundle")
        if self.evaluation_uncertainty_fingerprint_sha256 != e.fingerprint(): raise ValueError("evaluation uncertainty fingerprint must match bundled v3.60 object")
        evaluation_ref=e.evaluation.evaluation_id; partition_ref=e.dataset_partition.partition_id
        groups=[self.feature_attributions,self.saliency_maps,self.attention_explanations,self.counterfactual_explanations,self.embedding_explanations]
        for records in groups:
            for r in records:
                if r.evaluation_ref != evaluation_ref: raise ValueError("explanation evaluation_ref must resolve to bundled evaluation")
                if r.partition_ref != partition_ref: raise ValueError("explanation partition_ref must resolve to bundled partition")
                if r.checkpoint_ref != self.checkpoint_ref: raise ValueError("explanation checkpoint_ref must resolve to bundled checkpoint")
        for c in self.model_comparisons:
            if c.partition_ref != partition_ref: raise ValueError("model comparison partition_ref must resolve to bundled partition")
            if evaluation_ref not in c.evaluation_refs: raise ValueError("model comparison must include bundled evaluation")
            if self.checkpoint_ref not in c.checkpoint_refs: raise ValueError("model comparison must include bundled checkpoint")
            if self.model_spec_ref not in c.compared_model_refs: raise ValueError("model comparison must include bundled model specification")
        ids=[]
        for records in [self.feature_attributions,self.saliency_maps,self.attention_explanations,self.counterfactual_explanations,self.embedding_explanations,self.model_comparisons]:
            for r in records:
                for name in ("feature_attribution_id","saliency_map_id","attention_explanation_id","counterfactual_id","embedding_explanation_id","comparison_interpretation_id"):
                    if hasattr(r,name): ids.append(getattr(r,name)); break
        if len(ids)!=len(set(ids)): raise ValueError("explanation object ids must be unique")
        if not ids: raise ValueError("explainability bundle must contain at least one explanation object")
        return self

    def fingerprint(self)->str: return canonical_sha256(self)


def reference_explainability_interpretation_bundle()->MLExplainabilityInterpretationBundle:
    e=reference_evaluation_calibration_uncertainty_bundle()
    eval_ref=e.evaluation.evaluation_id; part_ref=e.dataset_partition.partition_id; cp=e.checkpoint_ref
    attribution=MLFeatureAttributionRecord(
        feature_attribution_id="ml-attribution:reference-energy:validation-example",
        evaluation_ref=eval_ref, partition_ref=part_ref, checkpoint_ref=cp,
        method="integrated-gradients", scope=MLExplanationScope.sample,
        target_ref="output:energy_kwh", sample_ref="sample:reference-energy:validation:001",
        feature_schema_ref="ml-feature-schema:reference-tabular-regression:v1",
        baseline_description="training-partition mean feature vector",
        values=[
            MLFeatureAttributionValue(feature_ref="temperature_c",attribution=0.62,input_value=31.2,baseline_value=21.0,normalized_magnitude_share=0.72),
            MLFeatureAttributionValue(feature_ref="humidity_pct",attribution=-0.24,input_value=68.0,baseline_value=50.0,normalized_magnitude_share=0.28),
        ], computation_ref="workspace-job:reference-energy:integrated-gradients:001",
        artifact_ref="artifact:reference-energy:attribution:001", artifact_sha256="4"*64,
        assumptions=["baseline choice materially affects attribution values"])
    saliency=MLSaliencyMapRecord(
        saliency_map_id="ml-saliency:reference-energy:validation-example", evaluation_ref=eval_ref,
        partition_ref=part_ref, checkpoint_ref=cp, method="input-gradient", sample_ref="sample:reference-energy:validation:001",
        target_ref="output:energy_kwh", source_artifact_ref="artifact:reference-energy:tensor-validation",
        saliency_artifact_ref="artifact:reference-energy:saliency:001", saliency_artifact_sha256="5"*64,
        coordinate_space="input-feature-vector", shape=[2], signed=True, normalization="absolute-max",
        computation_ref="workspace-job:reference-energy:saliency:001")
    counterfactual=MLCounterfactualExplanationRecord(
        counterfactual_id="ml-counterfactual:reference-energy:validation-example", evaluation_ref=eval_ref,
        partition_ref=part_ref, checkpoint_ref=cp, sample_ref="sample:reference-energy:validation:001",
        target_ref="output:energy_kwh", method="constrained-gradient-search", objective="reduce predicted energy_kwh by at least 10%",
        original_output=4.8, counterfactual_output=4.2,
        changes=[MLCounterfactualChange(feature_ref="temperature_c",original_value=31.2,counterfactual_value=27.0,mutable=True,constraint_ref="constraint:temperature-observed-range")],
        distance_metric="scaled-l1", distance_value=0.21, feasibility=MLCounterfactualFeasibility.feasible,
        constraints_ref="constraints:reference-energy:plausibility:v1", computation_ref="workspace-job:reference-energy:counterfactual:001")
    embedding=MLEmbeddingSpaceExplanationRecord(
        embedding_explanation_id="ml-embedding-explanation:reference-energy:validation-example", evaluation_ref=eval_ref,
        partition_ref=part_ref, checkpoint_ref=cp, sample_ref="sample:reference-energy:validation:001",
        representation_ref="model-component:reference-energy:penultimate-layer", embedding_space_ref="embedding-space:reference-energy:hidden-v1",
        method="nearest-neighbor-cosine", dimensions=16,
        neighbors=[MLEmbeddingNeighbor(item_ref="sample:reference-energy:train:117",rank=1,similarity=0.94,label="similar-load-profile"),MLEmbeddingNeighbor(item_ref="sample:reference-energy:train:442",rank=2,similarity=0.89,label="similar-weather-profile")],
        cluster_ref="cluster:reference-energy:hidden:3", projection_artifact_ref="artifact:reference-energy:embedding-projection:001",
        projection_artifact_sha256="6"*64, computation_ref="workspace-job:reference-energy:embedding-explanation:001")
    comparison=MLModelComparisonInterpretationRecord(
        comparison_interpretation_id="ml-model-comparison:reference-energy:baseline-vs-alternative", partition_ref=part_ref,
        method="paired-metric-delta-summary",
        compared_model_refs=[e.model_spec_ref,"ml-model-spec:reference-energy:alternative-regressor:v1"],
        evaluation_refs=[eval_ref,"ml-evaluation:reference-energy:alternative-validation"],
        checkpoint_refs=[cp,"ml-checkpoint:reference-energy:alternative-final"],
        metric_deltas={"mae_alternative_minus_baseline":-0.03,"rmse_alternative_minus_baseline":0.01},
        interpretation_statements=["The alternative has lower MAE on the referenced partition.","The alternative has slightly higher RMSE on the referenced partition."],
        computation_ref="workspace-job:reference-energy:model-comparison:001")
    return MLExplainabilityInterpretationBundle(
        model_spec_ref=e.model_spec_ref, training_run_ref=e.training_run_ref, checkpoint_ref=e.checkpoint_ref,
        evaluation_bundle=e, feature_attributions=[attribution], saliency_maps=[saliency],
        counterfactual_explanations=[counterfactual], embedding_explanations=[embedding], model_comparisons=[comparison],
        evaluation_uncertainty_fingerprint_sha256=e.fingerprint())


def contract_document()->dict[str,Any]:
    ref=reference_explainability_interpretation_bundle()
    return {
        "ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
        "object_types":["MLFeatureAttributionValue","MLFeatureAttributionRecord","MLSaliencyMapRecord","MLAttentionWeight","MLAttentionExplanationRecord","MLCounterfactualChange","MLCounterfactualExplanationRecord","MLEmbeddingNeighbor","MLEmbeddingSpaceExplanationRecord","MLModelComparisonInterpretationRecord","MLExplainabilityInterpretationBundle"],
        "explainability_capabilities":{"feature_attribution":True,"saliency":True,"attention_weight_capture":True,"counterfactual_explanations":True,"embedding_space_explanations":True,"model_comparison_interpretations":True,"artifact_and_computation_refs":True},
        "integration":{"extends_neural_evaluation_calibration_uncertainty_v3600":True,"links_evaluation_checkpoint_and_partition":True,"preserves_v360_evaluation_bundle_fingerprint":True,"links_model_specification_and_training_run":True,"workspace_remains_default_compute_host":True,"lab_remains_experiment_host":True},
        "reproducibility":{"deterministic_bundle_fingerprint":True,"attribution_artifact_hashes_supported":True,"saliency_artifact_hashes_required":True,"embedding_projection_hashes_supported":True,"method_and_computation_refs_supported":True,"counterfactual_constraints_supported":True,"comparison_metric_deltas_supported":True},
        "governance":{"feature_attribution_is_not_causation":True,"attention_weight_is_not_explanatory_proof":True,"counterfactual_is_model_relative_not_real_world_causal_effect":True,"embedding_proximity_is_not_semantic_fact":True,"saliency_is_not_evidence":True,"model_comparison_is_descriptive_not_autonomous_selection":True,"explanations_are_analytical_objects_not_evidence":True,"explanation_objects_require_lineage":True},
        "boundaries":{"core_computes_explanations":False,"core_runs_explainability_algorithms":False,"core_perturbs_inputs":False,"core_generates_counterfactuals":False,"core_computes_embeddings":False,"core_infers_causality_from_attribution":False,"core_interprets_attention_as_proof":False,"core_promotes_explanations_to_evidence":False,"core_selects_best_model_from_explanations":False,"core_certifies_interpretation_quality":False,"core_claims_explanation_truth":False},
        "reference":{"evaluation_id":ref.evaluation_bundle.evaluation.evaluation_id,"checkpoint_id":ref.checkpoint_ref,"feature_attribution_id":ref.feature_attributions[0].feature_attribution_id,"counterfactual_id":ref.counterfactual_explanations[0].counterfactual_id,"bundle_fingerprint_sha256":ref.fingerprint()}
    }
