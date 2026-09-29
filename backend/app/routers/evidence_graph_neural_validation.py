from fastapi import APIRouter
from app.services.evidence_graph_neural_validation import *

router=APIRouter(prefix="/v1/evidence-graph-neural-validation",tags=["evidence-graph-neural-validation"])
public_router=APIRouter(prefix="/public/v1/evidence-graph-neural-validation",tags=["public-evidence-graph-neural-validation"])

@router.get("/contract")
def get_contract(): return contract_document()
@public_router.get("/contract")
def get_public_contract(): return contract_document()
@router.get("/reference")
def get_reference():
    b=reference_evidence_graph_neural_validation_bundle(); return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle":b.model_dump(mode="json",exclude_none=True),"bundle_fingerprint_sha256":b.fingerprint()}
@router.post("/validate-signal")
def validate_signal(body:NeuralAnalysisSignalRef): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-case")
def validate_case(body:EvidenceGraphNeuralValidationCase): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-authorization")
def validate_authorization(body:EvidenceEdgePromotionAuthorization): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(body:EvidenceGraphNeuralValidationBundle): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle_fingerprint_sha256":body.fingerprint()}
