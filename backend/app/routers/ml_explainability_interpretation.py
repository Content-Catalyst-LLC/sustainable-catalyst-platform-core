from fastapi import APIRouter

from ..services.ml_explainability_interpretation import (
    CONTRACT_VERSION, CORE_RELEASE, MLAttentionExplanationRecord, MLCounterfactualExplanationRecord,
    MLEmbeddingSpaceExplanationRecord, MLExplainabilityInterpretationBundle, MLFeatureAttributionRecord,
    MLModelComparisonInterpretationRecord, MLSaliencyMapRecord, contract_document,
    reference_explainability_interpretation_bundle,
)

router=APIRouter(prefix="/api/v1/ml-explainability",tags=["ml-explainability"])
public_router=APIRouter(prefix="/public/v1/ml-explainability",tags=["public-ml-explainability"])

@router.get("/contract")
def get_contract(): return contract_document()

@public_router.get("/contract")
def get_public_contract(): return contract_document()

@router.get("/reference")
def get_reference():
    b=reference_explainability_interpretation_bundle()
    return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle":b.model_dump(mode="json",exclude_none=True),"bundle_fingerprint_sha256":b.fingerprint()}

@router.post("/validate-feature-attribution")
def validate_feature_attribution(body:MLFeatureAttributionRecord): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-saliency")
def validate_saliency(body:MLSaliencyMapRecord): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-attention")
def validate_attention(body:MLAttentionExplanationRecord): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-counterfactual")
def validate_counterfactual(body:MLCounterfactualExplanationRecord): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-embedding-explanation")
def validate_embedding(body:MLEmbeddingSpaceExplanationRecord): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-model-comparison")
def validate_comparison(body:MLModelComparisonInterpretationRecord): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(body:MLExplainabilityInterpretationBundle): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle_fingerprint_sha256":body.fingerprint()}
