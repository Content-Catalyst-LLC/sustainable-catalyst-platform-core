from fastapi import APIRouter

from ..services.machine_learning_models import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    MLFeatureSchema,
    MLInferencePlan,
    MLModelBundle,
    MLModelSpecification,
    MLTrainingPlan,
    NeuralArchitectureSpec,
    contract_document,
    reference_ml_model_bundle,
)

router = APIRouter(prefix="/api/v1/ml-models", tags=["ml-models"])
public_router = APIRouter(prefix="/public/v1/ml-models", tags=["public-ml-models"])

@router.get("/contract")
def get_contract(): return contract_document()

@public_router.get("/contract")
def get_public_contract(): return contract_document()

@router.get("/reference")
def get_reference():
    bundle = reference_ml_model_bundle()
    return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "bundle": bundle.model_dump(mode="json", exclude_none=True), "bundle_fingerprint_sha256": bundle.fingerprint()}

@router.post("/validate-feature-schema")
def validate_feature_schema(body: MLFeatureSchema): return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-neural-architecture")
def validate_neural_architecture(body: NeuralArchitectureSpec): return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-model-specification")
def validate_model_specification(body: MLModelSpecification): return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-training-plan")
def validate_training_plan(body: MLTrainingPlan): return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-inference-plan")
def validate_inference_plan(body: MLInferencePlan): return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(body: MLModelBundle): return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "bundle_fingerprint_sha256": body.fingerprint()}
