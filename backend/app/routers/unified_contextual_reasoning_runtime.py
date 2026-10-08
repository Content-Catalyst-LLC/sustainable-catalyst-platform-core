from fastapi import APIRouter

from app.services.unified_contextual_reasoning_runtime import (
    UnifiedContextualReasoningRuntimeBundle,
    contract_document,
    reference_unified_contextual_reasoning_runtime_bundle,
)

router = APIRouter(prefix="/v1/contextual-reasoning", tags=["unified-contextual-reasoning-runtime"])
public_router = APIRouter(prefix="/public/v1/contextual-reasoning", tags=["unified-contextual-reasoning-runtime-public"])

@public_router.get("/contract")
def public_contract():
    return contract_document()

@router.get("/contract")
def contract():
    return contract_document()

@router.get("/reference")
def reference():
    b=reference_unified_contextual_reasoning_runtime_bundle()
    return {"ok":True,"bundle_fingerprint_sha256":b.fingerprint(),"bundle":b.model_dump(mode="json")}

@router.get("/reference/stages")
def reference_stages():
    xs=reference_unified_contextual_reasoning_runtime_bundle().stages
    return {"ok":True,"count":len(xs),"items":[x.model_dump(mode="json") for x in xs]}

@router.get("/reference/traces")
def reference_traces():
    xs=reference_unified_contextual_reasoning_runtime_bundle().traces
    return {"ok":True,"count":len(xs),"items":[x.model_dump(mode="json") for x in xs]}

@router.post("/validate-bundle")
def validate_bundle(payload: UnifiedContextualReasoningRuntimeBundle):
    return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
