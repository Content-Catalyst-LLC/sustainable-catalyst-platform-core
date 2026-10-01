from fastapi import APIRouter

from app.services.unified_runtime_policy_capability_negotiation import (
    RuntimeConsumerProfile,
    UnifiedRuntimePolicyCapabilityNegotiationBundle,
    contract_document,
    reference_unified_runtime_policy_capability_negotiation_bundle,
)

router = APIRouter(prefix="/v1/runtime-capabilities", tags=["runtime-capabilities"])
public_router = APIRouter(prefix="/public/v1/runtime-capabilities", tags=["runtime-capabilities-public"])

@router.get("/contract")
def private_contract(): return contract_document()

@public_router.get("/contract")
def public_contract(): return contract_document()

@router.get("/reference")
def reference(): return {"ok":True,"bundle":reference_unified_runtime_policy_capability_negotiation_bundle().model_dump(mode="json")}

@router.post("/validate-consumer")
def validate_consumer(payload: RuntimeConsumerProfile): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(payload: UnifiedRuntimePolicyCapabilityNegotiationBundle): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
