from fastapi import APIRouter
from ..services.ml_training_lineage import CONTRACT_VERSION, CORE_RELEASE, MLCheckpointRecord, MLEvaluationRecord, MLExperimentRecord, MLTrainingLineageBundle, MLTrainingRunRecord, contract_document, reference_training_lineage_bundle
router=APIRouter(prefix="/api/v1/ml-training-lineage",tags=["ml-training-lineage"])
public_router=APIRouter(prefix="/public/v1/ml-training-lineage",tags=["public-ml-training-lineage"])
@router.get("/contract")
def get_contract(): return contract_document()
@public_router.get("/contract")
def get_public_contract(): return contract_document()
@router.get("/reference")
def get_reference():
    b=reference_training_lineage_bundle(); return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle":b.model_dump(mode="json",exclude_none=True),"bundle_fingerprint_sha256":b.fingerprint()}
@router.post("/validate-experiment")
def validate_experiment(body:MLExperimentRecord): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-training-run")
def validate_training_run(body:MLTrainingRunRecord): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-checkpoint")
def validate_checkpoint(body:MLCheckpointRecord): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-evaluation")
def validate_evaluation(body:MLEvaluationRecord): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(body:MLTrainingLineageBundle): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle_fingerprint_sha256":body.fingerprint()}
