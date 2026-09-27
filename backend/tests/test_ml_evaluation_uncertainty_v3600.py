import copy
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import ml_evaluation_uncertainty
from app.services.ml_evaluation_uncertainty import (
    CONTRACT_VERSION, CORE_RELEASE, MLCalibrationRecord, MLConfusionMatrixRecord,
    MLEvaluationCalibrationUncertaintyBundle, MLOODDirection, MLOutOfDistributionIndicatorRecord,
    MLPredictionIntervalSummary, MLMetricObservation, MLMetricDirection, MLMetricFamily,
    contract_document, reference_evaluation_calibration_uncertainty_bundle,
)


def test_contract_identity():
    d=contract_document(); assert CORE_RELEASE=="3.60.0"; assert CONTRACT_VERSION=="sc.core.neural-evaluation-calibration-uncertainty.v1"; assert d["release"]=="3.60.0"

def test_extends_v358_and_v359():
    i=contract_document()["integration"]; assert i["extends_training_run_checkpoint_experiment_lineage_v3580"] is True; assert i["extends_neural_dataset_feature_transformation_provenance_v3590"] is True

def test_governance_distinguishes_analysis_from_evidence():
    g=contract_document()["governance"]; assert g["metric_is_analytical_result_not_evidence"] is True; assert g["confidence_is_not_truth_probability"] is True; assert g["ood_indicator_is_not_fact"] is True

def test_core_does_not_execute_evaluation():
    b=contract_document()["boundaries"]
    for key in ("core_computes_metrics","core_calibrates_models","core_generates_predictions","core_estimates_uncertainty","core_runs_ood_detection","core_selects_thresholds","core_selects_best_model","core_promotes_models_autonomously","core_certifies_model_quality","core_treats_scores_as_evidence","core_claims_prediction_truth"):
        assert b[key] is False

def test_reference_bundle_valid_and_fingerprinted():
    b=reference_evaluation_calibration_uncertainty_bundle(); assert len(b.fingerprint())==64; assert len(b.metric_observations)==2; assert b.dataset_partition.role.value=="validation"; assert b.evaluation.split.value=="validation"

def test_fingerprint_stable():
    a=reference_evaluation_calibration_uncertainty_bundle(); b=MLEvaluationCalibrationUncertaintyBundle.model_validate(a.model_dump(mode="json")); assert a.fingerprint()==b.fingerprint()

def invalid(mutator):
    p=reference_evaluation_calibration_uncertainty_bundle().model_dump(mode="json"); mutator(p)
    with pytest.raises(ValidationError): MLEvaluationCalibrationUncertaintyBundle.model_validate(p)

def test_evaluation_run_must_match_bundle(): invalid(lambda p:p.__setitem__("training_run_ref","ml-run:wrong"))
def test_checkpoint_must_match_evaluation(): invalid(lambda p:p.__setitem__("checkpoint_ref","ml-checkpoint:wrong"))
def test_dataset_partition_must_match_evaluation_dataset(): invalid(lambda p:p["dataset_partition"].__setitem__("dataset_version_ref","dataset-version:wrong"))
def test_evaluation_split_must_match_partition_role(): invalid(lambda p:p["dataset_partition"].__setitem__("role","test"))
def test_metric_evaluation_ref_must_resolve(): invalid(lambda p:p["metric_observations"][0].__setitem__("evaluation_ref","ml-evaluation:wrong"))
def test_metric_partition_ref_must_resolve(): invalid(lambda p:p["metric_observations"][0].__setitem__("partition_ref","ml-partition:wrong"))
def test_duplicate_derived_ids_rejected(): invalid(lambda p:p["metric_observations"][1].__setitem__("metric_observation_id",p["metric_observations"][0]["metric_observation_id"]))

def test_target_direction_requires_target_value():
    p=reference_evaluation_calibration_uncertainty_bundle().metric_observations[0].model_dump(mode="json"); p["direction"]="target-is-better"; p["target_value"]=None
    with pytest.raises(ValidationError): MLMetricObservation.model_validate(p)

def test_nonfinite_metric_rejected():
    p=reference_evaluation_calibration_uncertainty_bundle().metric_observations[0].model_dump(mode="json"); p["value"]=float("nan")
    with pytest.raises(ValidationError): MLMetricObservation.model_validate(p)

def test_confusion_matrix_shape_and_count_validation():
    base=dict(confusion_matrix_id="cm:1",evaluation_ref="eval:1",partition_ref="partition:1",labels=["a","b"],counts=[[8,2],[1,9]],sample_count=20)
    assert MLConfusionMatrixRecord(**base).sample_count==20
    bad=copy.deepcopy(base); bad["counts"]=[[8,2,0],[1,9,0]]
    with pytest.raises(ValidationError): MLConfusionMatrixRecord(**bad)

def test_confusion_matrix_sample_count_must_equal_counts():
    with pytest.raises(ValidationError): MLConfusionMatrixRecord(confusion_matrix_id="cm:1",evaluation_ref="eval:1",partition_ref="part:1",labels=["a","b"],counts=[[8,2],[1,9]],sample_count=19)

def test_calibration_bins_cannot_overlap():
    p=reference_evaluation_calibration_uncertainty_bundle().calibration_records[0].model_dump(mode="json"); p["bins"][1]["lower_bound"]=0.7
    with pytest.raises(ValidationError): MLCalibrationRecord.model_validate(p)

def test_confidence_histogram_counts_must_sum_to_sample_count(): invalid(lambda p:p["confidence_distributions"][0].__setitem__("sample_count",99))
def test_prediction_interval_quantiles_define_nominal_coverage(): invalid(lambda p:p["prediction_intervals"][0].__setitem__("nominal_coverage",0.8))
def test_negative_uncertainty_rejected(): invalid(lambda p:p["uncertainty_estimates"][0].__setitem__("estimate",-0.01))
def test_ood_flag_must_match_threshold_semantics(): invalid(lambda p:p["ood_indicators"][0].__setitem__("is_out_of_distribution",True))

def test_ood_lower_direction_semantics():
    obj=MLOutOfDistributionIndicatorRecord(ood_indicator_id="ood:1",evaluation_ref="eval:1",partition_ref="part:1",detector_ref="detector:1",score=0.1,threshold=0.2,direction=MLOODDirection.lower_is_ood,is_out_of_distribution=True); assert obj.is_out_of_distribution is True

def test_public_contract_route():
    app=FastAPI(); app.include_router(ml_evaluation_uncertainty.public_router); r=TestClient(app).get("/public/v1/ml-evaluation-uncertainty/contract"); assert r.status_code==200; assert r.json()["release"]=="3.60.0"

def test_private_reference_route():
    app=FastAPI(); app.include_router(ml_evaluation_uncertainty.router); r=TestClient(app).get("/api/v1/ml-evaluation-uncertainty/reference"); assert r.status_code==200; assert len(r.json()["bundle_fingerprint_sha256"])==64
