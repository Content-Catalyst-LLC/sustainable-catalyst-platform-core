import copy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import ml_inference_prediction_provenance
from app.services.ml_inference_prediction_provenance import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    MLClassScoreRecord,
    MLInferencePredictionProvenanceBundle,
    MLInferenceRunRecord,
    MLPredictionConfidenceBindingRecord,
    MLPredictionInterpretationBindingRecord,
    MLPredictionKind,
    MLPredictionRecord,
    contract_document,
    reference_inference_prediction_provenance_bundle,
)


def payload():
    return reference_inference_prediction_provenance_bundle().model_dump(mode="json")


def invalid(mutator):
    data = payload()
    mutator(data)
    with pytest.raises(ValidationError):
        MLInferencePredictionProvenanceBundle.model_validate(data)


def test_release_and_contract():
    assert CORE_RELEASE == "3.63.0"
    assert CONTRACT_VERSION == "sc.core.neural-inference-prediction-provenance.v1"


def test_reference_bundle_fingerprint_is_deterministic():
    a = reference_inference_prediction_provenance_bundle()
    b = reference_inference_prediction_provenance_bundle()
    assert a.fingerprint() == b.fingerprint()
    assert len(a.fingerprint()) == 64


def test_reference_prediction_cannot_promote_to_evidence_or_claim():
    prediction = reference_inference_prediction_provenance_bundle().predictions[0]
    assert prediction.evidence_promotion_allowed is False
    assert prediction.claim_promotion_allowed is False


def test_contract_governance_boundaries():
    c = contract_document()
    assert c["governance"]["prediction_is_analytical_output_not_evidence"] is True
    assert c["governance"]["prediction_is_not_observation"] is True
    assert c["boundaries"]["core_runs_inference"] is False
    assert c["boundaries"]["core_generates_predictions"] is False
    assert c["boundaries"]["core_promotes_predictions_to_evidence"] is False
    assert c["boundaries"]["core_promotes_predictions_to_claims"] is False


def test_dataset_fingerprint_must_match():
    invalid(lambda p: p.__setitem__("dataset_lineage_fingerprint_sha256", "0" * 64))


def test_representation_fingerprint_must_match():
    invalid(lambda p: p.__setitem__("representation_lineage_fingerprint_sha256", "0" * 64))


def test_input_tensor_ref_must_resolve():
    invalid(lambda p: p["input_bindings"][0].__setitem__("tensor_input_ref", "ml-tensor-input:missing"))


def test_input_partition_ref_must_resolve():
    invalid(lambda p: p["input_bindings"][0].__setitem__("dataset_partition_ref", "ml-partition:missing"))


def test_input_feature_schema_must_match_model():
    invalid(lambda p: p["input_bindings"][0].__setitem__("feature_schema_ref", "ml-feature-schema:wrong"))


def test_input_artifact_must_match_tensor():
    invalid(lambda p: p["input_bindings"][0].__setitem__("input_artifact_ref", "artifact:wrong"))


def test_input_artifact_hash_must_match_tensor():
    invalid(lambda p: p["input_bindings"][0].__setitem__("input_artifact_sha256", "f" * 64))


def test_inference_plan_ref_must_match():
    invalid(lambda p: p["inference_runs"][0].__setitem__("inference_plan_ref", "ml-inference-plan:wrong"))


def test_inference_run_model_spec_ref_must_match():
    invalid(lambda p: p["inference_runs"][0].__setitem__("model_spec_ref", "ml-model-spec:wrong"))


def test_inference_run_model_version_must_match_plan():
    invalid(lambda p: p["inference_runs"][0].__setitem__("model_version_ref", "ai-model-version:wrong"))


def test_inference_run_runtime_binding_must_match_plan():
    invalid(lambda p: p["inference_runs"][0].__setitem__("runtime_binding_ref", "runtime:wrong"))


def test_inference_run_checkpoint_must_match_v362_lineage():
    invalid(lambda p: p["inference_runs"][0].__setitem__("checkpoint_ref", "ml-checkpoint:wrong"))


def test_inference_run_input_ref_must_resolve():
    invalid(lambda p: p["inference_runs"][0]["input_binding_refs"].__setitem__(0, "ml-inference-input:missing"))


def test_inference_run_input_refs_unique():
    run = reference_inference_prediction_provenance_bundle().inference_runs[0].model_dump(mode="json")
    run["input_binding_refs"].append(run["input_binding_refs"][0])
    with pytest.raises(ValidationError):
        MLInferenceRunRecord.model_validate(run)


def test_prediction_run_ref_must_resolve():
    invalid(lambda p: p["predictions"][0].__setitem__("inference_run_ref", "ml-inference-run:missing"))


def test_prediction_input_must_belong_to_run():
    invalid(lambda p: p["predictions"][0].__setitem__("input_binding_ref", "ml-inference-input:other"))


def test_prediction_output_ref_must_match_model_target_or_output():
    invalid(lambda p: p["predictions"][0].__setitem__("output_ref", "not-a-target"))


def test_point_prediction_requires_value():
    with pytest.raises(ValidationError):
        MLPredictionRecord(prediction_id="p:1", inference_run_ref="r:1", input_binding_ref="i:1", output_ref="y", prediction_kind=MLPredictionKind.point)


def test_probability_vector_requires_scores():
    with pytest.raises(ValidationError):
        MLPredictionRecord(prediction_id="p:1", inference_run_ref="r:1", input_binding_ref="i:1", output_ref="y", prediction_kind=MLPredictionKind.probability_vector)


def test_probability_vector_probabilities_sum_to_one():
    with pytest.raises(ValidationError):
        MLPredictionRecord(
            prediction_id="p:1", inference_run_ref="r:1", input_binding_ref="i:1", output_ref="y",
            prediction_kind=MLPredictionKind.probability_vector,
            class_scores=[MLClassScoreRecord(label="a", score=2.0, probability=0.7), MLClassScoreRecord(label="b", score=1.0, probability=0.2)],
        )


def test_probability_vector_unique_labels():
    with pytest.raises(ValidationError):
        MLPredictionRecord(
            prediction_id="p:1", inference_run_ref="r:1", input_binding_ref="i:1", output_ref="y",
            prediction_kind=MLPredictionKind.probability_vector,
            class_scores=[MLClassScoreRecord(label="a", score=2.0, probability=0.5), MLClassScoreRecord(label="a", score=1.0, probability=0.5)],
        )


def test_valid_probability_vector():
    record = MLPredictionRecord(
        prediction_id="p:1", inference_run_ref="r:1", input_binding_ref="i:1", output_ref="output:class",
        prediction_kind=MLPredictionKind.probability_vector,
        class_scores=[MLClassScoreRecord(label="a", score=2.0, probability=0.7), MLClassScoreRecord(label="b", score=1.0, probability=0.3)],
    )
    assert len(record.fingerprint()) == 64


def test_distribution_prediction_requires_artifact():
    with pytest.raises(ValidationError):
        MLPredictionRecord(prediction_id="p:1", inference_run_ref="r:1", input_binding_ref="i:1", output_ref="output:d", prediction_kind=MLPredictionKind.distribution)


def test_confidence_binding_requires_reference_family():
    with pytest.raises(ValidationError):
        MLPredictionConfidenceBindingRecord(confidence_binding_id="c:1", prediction_ref="p:1")


def test_confidence_binding_prediction_must_resolve():
    invalid(lambda p: p["confidence_bindings"][0].__setitem__("prediction_ref", "ml-prediction:missing"))


def test_calibration_ref_must_resolve():
    invalid(lambda p: p["confidence_bindings"][0]["calibration_refs"].__setitem__(0, "ml-calibration:missing"))


def test_confidence_distribution_ref_must_resolve():
    invalid(lambda p: p["confidence_bindings"][0]["confidence_distribution_refs"].__setitem__(0, "ml-confidence:missing"))


def test_prediction_interval_ref_must_resolve():
    invalid(lambda p: p["confidence_bindings"][0]["prediction_interval_refs"].__setitem__(0, "ml-interval:missing"))


def test_uncertainty_ref_must_resolve():
    invalid(lambda p: p["confidence_bindings"][0]["uncertainty_estimate_refs"].__setitem__(0, "ml-uncertainty:missing"))


def test_ood_ref_must_resolve():
    invalid(lambda p: p["confidence_bindings"][0]["ood_indicator_refs"].__setitem__(0, "ml-ood:missing"))


def test_ood_sample_must_match_input_source():
    invalid(lambda p: p["input_bindings"][0].__setitem__("source_object_ref", "sample:wrong"))


def test_interpretation_binding_requires_reference_family():
    with pytest.raises(ValidationError):
        MLPredictionInterpretationBindingRecord(interpretation_binding_id="x:1", prediction_ref="p:1")


def test_interpretation_prediction_must_resolve():
    invalid(lambda p: p["interpretation_bindings"][0].__setitem__("prediction_ref", "ml-prediction:missing"))


def test_feature_attribution_ref_must_resolve():
    invalid(lambda p: p["interpretation_bindings"][0]["feature_attribution_refs"].__setitem__(0, "ml-attribution:missing"))


def test_counterfactual_ref_must_resolve():
    invalid(lambda p: p["interpretation_bindings"][0]["counterfactual_refs"].__setitem__(0, "ml-counterfactual:missing"))


def test_embedding_explanation_ref_must_resolve():
    invalid(lambda p: p["interpretation_bindings"][0]["embedding_explanation_refs"].__setitem__(0, "ml-embedding-explanation:missing"))


def test_similarity_result_ref_must_resolve():
    invalid(lambda p: p["interpretation_bindings"][0]["similarity_result_refs"].__setitem__(0, "ml-similarity:missing"))


def test_projection_ref_must_resolve():
    invalid(lambda p: p["interpretation_bindings"][0]["projection_refs"].__setitem__(0, "ml-projection:missing"))


def test_cluster_ref_must_resolve():
    invalid(lambda p: p["interpretation_bindings"][0]["cluster_refs"].__setitem__(0, "cluster:missing"))


def test_public_contract_route():
    app = FastAPI()
    app.include_router(ml_inference_prediction_provenance.public_router)
    response = TestClient(app).get("/public/v1/ml-inference/contract")
    assert response.status_code == 200
    body = response.json()
    assert body["release"] == "3.63.0"
    assert body["governance"]["prediction_is_analytical_output_not_evidence"] is True


def test_private_reference_route():
    app = FastAPI()
    app.include_router(ml_inference_prediction_provenance.router)
    response = TestClient(app).get("/api/v1/ml-inference/reference")
    assert response.status_code == 200
    assert len(response.json()["bundle_fingerprint_sha256"]) == 64
