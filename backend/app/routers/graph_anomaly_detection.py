from fastapi import APIRouter
from app.services.graph_anomaly_detection import *

router=APIRouter(prefix="/v1/graph-anomalies",tags=["graph-anomaly-detection"])
public_router=APIRouter(prefix="/public/v1/graph-anomalies",tags=["public-graph-anomaly-detection"])

@router.get("/contract")
def get_contract(): return contract_document()
@public_router.get("/contract")
def get_public_contract(): return contract_document()
@router.get("/reference")
def get_reference():
    b=reference_graph_anomaly_detection_bundle(); return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle":b.model_dump(mode="json",exclude_none=True),"bundle_fingerprint_sha256":b.fingerprint()}
@router.post("/validate-runtime")
def validate_runtime(body:GraphAnomalyRuntimeContract): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-score")
def validate_score(body:GraphAnomalyScoreRecord): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-review")
def validate_review(body:GraphAnomalyReviewRecord): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(body:GraphAnomalyDetectionBundle): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle_fingerprint_sha256":body.fingerprint()}
