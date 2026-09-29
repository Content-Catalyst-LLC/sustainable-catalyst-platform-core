from fastapi import APIRouter
from ..services.graph_classification import (
    CORE_RELEASE, CONTRACT_VERSION, GraphClassificationBundle, GraphClassificationLabelSpace,
    GraphClassificationPrediction, GraphClassificationRuntimeContract, contract_document,
    reference_graph_classification_bundle,
)
router=APIRouter(prefix="/api/v1/graph-classification",tags=["graph-classification"])
public_router=APIRouter(prefix="/public/v1/graph-classification",tags=["public-graph-classification"])
@router.get("/contract")
def get_contract(): return contract_document()
@public_router.get("/contract")
def get_public_contract(): return contract_document()
@router.get("/reference")
def get_reference():
    b=reference_graph_classification_bundle(); return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle":b.model_dump(mode="json",exclude_none=True),"bundle_fingerprint_sha256":b.fingerprint()}
@router.post("/validate-label-space")
def validate_label_space(body:GraphClassificationLabelSpace): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-runtime")
def validate_runtime(body:GraphClassificationRuntimeContract): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-prediction")
def validate_prediction(body:GraphClassificationPrediction): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(body:GraphClassificationBundle): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle_fingerprint_sha256":body.fingerprint()}
