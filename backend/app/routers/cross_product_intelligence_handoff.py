from fastapi import APIRouter

from app.services.cross_product_intelligence_handoff import (
    CrossProductIntelligenceHandoffBundle,
    CrossProductIntelligenceHandoffRequest,
    contract_document,
    reference_cross_product_intelligence_handoff_bundle,
)

router = APIRouter(prefix="/v1/cross-product-handoff", tags=["cross-product-handoff"])
public_router = APIRouter(prefix="/public/v1/cross-product-handoff", tags=["cross-product-handoff-public"])

@router.get("/contract")
def private_contract(): return contract_document()

@public_router.get("/contract")
def public_contract(): return contract_document()

@router.get("/reference")
def reference(): return {"ok": True, "bundle": reference_cross_product_intelligence_handoff_bundle().model_dump(mode="json")}

@router.post("/validate-request")
def validate_request(payload: CrossProductIntelligenceHandoffRequest): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(payload: CrossProductIntelligenceHandoffBundle): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
