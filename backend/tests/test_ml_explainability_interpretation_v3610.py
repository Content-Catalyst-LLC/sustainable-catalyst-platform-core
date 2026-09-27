import copy
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import ml_explainability_interpretation
from app.services.ml_explainability_interpretation import (
    CONTRACT_VERSION, CORE_RELEASE, MLAttentionExplanationRecord, MLAttentionWeight,
    MLCounterfactualChange, MLCounterfactualExplanationRecord, MLCounterfactualFeasibility,
    MLEmbeddingNeighbor, MLEmbeddingSpaceExplanationRecord, MLExplainabilityInterpretationBundle,
    MLExplanationScope, MLFeatureAttributionRecord, MLFeatureAttributionValue,
    MLModelComparisonInterpretationRecord, MLSaliencyMapRecord, contract_document,
    reference_explainability_interpretation_bundle,
)


def test_contract_identity():
    d=contract_document(); assert CORE_RELEASE=="3.61.0"; assert CONTRACT_VERSION=="sc.core.explainability-model-interpretation.v1"; assert d["release"]=="3.61.0"

def test_extends_v360():
    assert contract_document()["integration"]["extends_neural_evaluation_calibration_uncertainty_v3600"] is True

def test_governance_semantics():
    g=contract_document()["governance"]
    for k in ("feature_attribution_is_not_causation","attention_weight_is_not_explanatory_proof","counterfactual_is_model_relative_not_real_world_causal_effect","embedding_proximity_is_not_semantic_fact","saliency_is_not_evidence","model_comparison_is_descriptive_not_autonomous_selection","explanations_are_analytical_objects_not_evidence"):
        assert g[k] is True

def test_core_does_not_compute_or_promote_explanations():
    b=contract_document()["boundaries"]
    for k in ("core_computes_explanations","core_runs_explainability_algorithms","core_perturbs_inputs","core_generates_counterfactuals","core_computes_embeddings","core_infers_causality_from_attribution","core_interprets_attention_as_proof","core_promotes_explanations_to_evidence","core_selects_best_model_from_explanations","core_certifies_interpretation_quality","core_claims_explanation_truth"):
        assert b[k] is False

def test_reference_bundle_valid_and_fingerprinted():
    b=reference_explainability_interpretation_bundle(); assert len(b.fingerprint())==64; assert b.feature_attributions; assert b.saliency_maps; assert b.counterfactual_explanations; assert b.embedding_explanations; assert b.model_comparisons

def test_fingerprint_stable():
    a=reference_explainability_interpretation_bundle(); b=MLExplainabilityInterpretationBundle.model_validate(a.model_dump(mode="json")); assert a.fingerprint()==b.fingerprint()

def invalid(mutator):
    p=reference_explainability_interpretation_bundle().model_dump(mode="json"); mutator(p)
    with pytest.raises(ValidationError): MLExplainabilityInterpretationBundle.model_validate(p)

def test_model_ref_must_match_v360_bundle(): invalid(lambda p:p.__setitem__("model_spec_ref","ml-model-spec:wrong"))
def test_training_run_ref_must_match_v360_bundle(): invalid(lambda p:p.__setitem__("training_run_ref","ml-run:wrong"))
def test_checkpoint_ref_must_match_v360_bundle(): invalid(lambda p:p.__setitem__("checkpoint_ref","ml-checkpoint:wrong"))
def test_v360_fingerprint_must_match(): invalid(lambda p:p.__setitem__("evaluation_uncertainty_fingerprint_sha256","0"*64))
def test_explanation_evaluation_ref_must_resolve(): invalid(lambda p:p["feature_attributions"][0].__setitem__("evaluation_ref","eval:wrong"))
def test_explanation_partition_ref_must_resolve(): invalid(lambda p:p["saliency_maps"][0].__setitem__("partition_ref","partition:wrong"))
def test_explanation_checkpoint_ref_must_resolve(): invalid(lambda p:p["counterfactual_explanations"][0].__setitem__("checkpoint_ref","checkpoint:wrong"))
def test_model_comparison_must_include_primary_model(): invalid(lambda p:p["model_comparisons"][0]["compared_model_refs"].__setitem__(0,"ml-model-spec:other"))
def test_duplicate_explanation_ids_rejected():
    p=reference_explainability_interpretation_bundle().model_dump(mode="json")
    p["saliency_maps"][0]["saliency_map_id"]=p["feature_attributions"][0]["feature_attribution_id"]
    with pytest.raises(ValidationError): MLExplainabilityInterpretationBundle.model_validate(p)

def test_feature_attribution_unique_features():
    r=reference_explainability_interpretation_bundle().feature_attributions[0].model_dump(mode="json"); r["values"][1]["feature_ref"]=r["values"][0]["feature_ref"]
    with pytest.raises(ValidationError): MLFeatureAttributionRecord.model_validate(r)

def test_feature_attribution_shares_sum_to_one():
    r=reference_explainability_interpretation_bundle().feature_attributions[0].model_dump(mode="json"); r["values"][1]["normalized_magnitude_share"]=0.20
    with pytest.raises(ValidationError): MLFeatureAttributionRecord.model_validate(r)

def test_sample_scope_requires_sample_ref():
    r=reference_explainability_interpretation_bundle().feature_attributions[0].model_dump(mode="json"); r["sample_ref"]=None
    with pytest.raises(ValidationError): MLFeatureAttributionRecord.model_validate(r)

def test_saliency_shape_positive():
    r=reference_explainability_interpretation_bundle().saliency_maps[0].model_dump(mode="json"); r["shape"]=[0]
    with pytest.raises(ValidationError): MLSaliencyMapRecord.model_validate(r)

def test_attention_normalized_weights_sum_to_one():
    good=MLAttentionExplanationRecord(attention_explanation_id="attn:1",evaluation_ref="eval:1",partition_ref="part:1",checkpoint_ref="cp:1",sample_ref="sample:1",model_component_ref="component:transformer",query_ref="token:q",weights=[MLAttentionWeight(key_ref="token:a",weight=0.4),MLAttentionWeight(key_ref="token:b",weight=0.6)],normalized=True)
    assert good.normalized is True
    with pytest.raises(ValidationError): MLAttentionExplanationRecord(attention_explanation_id="attn:2",evaluation_ref="eval:1",partition_ref="part:1",checkpoint_ref="cp:1",sample_ref="sample:1",model_component_ref="component:transformer",query_ref="token:q",weights=[MLAttentionWeight(key_ref="token:a",weight=0.4),MLAttentionWeight(key_ref="token:b",weight=0.5)],normalized=True)

def test_attention_duplicate_keys_rejected():
    with pytest.raises(ValidationError): MLAttentionExplanationRecord(attention_explanation_id="attn:2",evaluation_ref="eval:1",partition_ref="part:1",checkpoint_ref="cp:1",sample_ref="sample:1",model_component_ref="component:transformer",query_ref="token:q",weights=[MLAttentionWeight(key_ref="token:a",weight=0.5),MLAttentionWeight(key_ref="token:a",weight=0.5)],normalized=True)

def test_counterfactual_must_change_feature():
    with pytest.raises(ValidationError): MLCounterfactualExplanationRecord(counterfactual_id="cf:1",evaluation_ref="eval:1",partition_ref="part:1",checkpoint_ref="cp:1",sample_ref="sample:1",method="search",objective="change output",changes=[MLCounterfactualChange(feature_ref="x",original_value=1.0,counterfactual_value=1.0)],feasibility=MLCounterfactualFeasibility.unknown)

def test_counterfactual_cannot_change_immutable_feature():
    with pytest.raises(ValidationError): MLCounterfactualChange(feature_ref="age",original_value=40,counterfactual_value=20,mutable=False)

def test_counterfactual_distance_requires_metric():
    r=reference_explainability_interpretation_bundle().counterfactual_explanations[0].model_dump(mode="json"); r["distance_metric"]=None
    with pytest.raises(ValidationError): MLCounterfactualExplanationRecord.model_validate(r)

def test_embedding_neighbor_ranks_contiguous():
    r=reference_explainability_interpretation_bundle().embedding_explanations[0].model_dump(mode="json"); r["neighbors"][1]["rank"]=3
    with pytest.raises(ValidationError): MLEmbeddingSpaceExplanationRecord.model_validate(r)

def test_embedding_neighbor_refs_unique():
    r=reference_explainability_interpretation_bundle().embedding_explanations[0].model_dump(mode="json"); r["neighbors"][1]["item_ref"]=r["neighbors"][0]["item_ref"]
    with pytest.raises(ValidationError): MLEmbeddingSpaceExplanationRecord.model_validate(r)

def test_model_comparison_lengths_match():
    r=reference_explainability_interpretation_bundle().model_comparisons[0].model_dump(mode="json"); r["checkpoint_refs"].pop()
    with pytest.raises(ValidationError): MLModelComparisonInterpretationRecord.model_validate(r)

def test_public_contract_route():
    app=FastAPI(); app.include_router(ml_explainability_interpretation.public_router); r=TestClient(app).get("/public/v1/ml-explainability/contract"); assert r.status_code==200; assert r.json()["release"]=="3.61.0"

def test_private_reference_route():
    app=FastAPI(); app.include_router(ml_explainability_interpretation.router); r=TestClient(app).get("/api/v1/ml-explainability/reference"); assert r.status_code==200; assert len(r.json()["bundle_fingerprint_sha256"])==64
