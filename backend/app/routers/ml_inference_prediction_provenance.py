from fastapi import APIRouter

from ..services.ml_inference_prediction_provenance import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    MLInferenceInputBindingRecord,
    MLInferencePredictionProvenanceBundle,
    MLInferenceRunRecord,
    MLPredictionConfidenceBindingRecord,
    MLPredictionInterpretationBindingRecord,
    MLPredictionRecord,
    contract_document,
    reference_inference_prediction_provenance_bundle,
)

router = APIRouter(prefix="/api/v1/ml-inference", tags=["ml-inference"])
public_router = APIRouter(prefix="/public/v1/ml-inference", tags=["public-ml-inference"])


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    bundle = reference_inference_prediction_provenance_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
    }


@router.post("/validate-input-binding")
def validate_input_binding(body: MLInferenceInputBindingRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-inference-run")
def validate_inference_run(body: MLInferenceRunRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-prediction")
def validate_prediction(body: MLPredictionRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-confidence-binding")
def validate_confidence_binding(body: MLPredictionConfidenceBindingRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-interpretation-binding")
def validate_interpretation_binding(body: MLPredictionInterpretationBindingRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(body: MLInferencePredictionProvenanceBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }
