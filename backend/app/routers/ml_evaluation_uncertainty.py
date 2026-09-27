from fastapi import APIRouter

from ..services.ml_evaluation_uncertainty import (
    CONTRACT_VERSION, CORE_RELEASE, MLCalibrationRecord, MLConfidenceDistributionRecord,
    MLConfusionMatrixRecord, MLEvaluationCalibrationUncertaintyBundle, MLMetricObservation,
    MLOutOfDistributionIndicatorRecord, MLPredictionIntervalSummary, MLUncertaintyEstimateRecord,
    contract_document, reference_evaluation_calibration_uncertainty_bundle,
)

router=APIRouter(prefix="/api/v1/ml-evaluation-uncertainty",tags=["ml-evaluation-uncertainty"])
public_router=APIRouter(prefix="/public/v1/ml-evaluation-uncertainty",tags=["public-ml-evaluation-uncertainty"])

@router.get("/contract")
def get_contract(): return contract_document()

@public_router.get("/contract")
def get_public_contract(): return contract_document()

@router.get("/reference")
def get_reference():
    b=reference_evaluation_calibration_uncertainty_bundle()
    return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle":b.model_dump(mode="json",exclude_none=True),"bundle_fingerprint_sha256":b.fingerprint()}

@router.post("/validate-metric")
def validate_metric(body:MLMetricObservation): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-confusion-matrix")
def validate_confusion_matrix(body:MLConfusionMatrixRecord): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-calibration")
def validate_calibration(body:MLCalibrationRecord): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-confidence-distribution")
def validate_confidence(body:MLConfidenceDistributionRecord): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-prediction-interval")
def validate_interval(body:MLPredictionIntervalSummary): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-uncertainty")
def validate_uncertainty(body:MLUncertaintyEstimateRecord): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-ood-indicator")
def validate_ood(body:MLOutOfDistributionIndicatorRecord): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(body:MLEvaluationCalibrationUncertaintyBundle): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle_fingerprint_sha256":body.fingerprint()}
