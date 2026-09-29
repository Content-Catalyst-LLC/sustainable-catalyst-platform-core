from fastapi import APIRouter

from app.services.cross_lingual_semantic_exchange import (
    CORE_RELEASE,
    contract_document,
    reference_cross_lingual_semantic_exchange_bundle,
)

router = APIRouter(prefix="/api/v1/cross-lingual-exchange", tags=["Cross-Lingual Semantic Exchange"])
public_router = APIRouter(prefix="/public/v1/cross-lingual-exchange", tags=["Public Cross-Lingual Semantic Exchange"])

@router.get("/contract")
def private_contract():
    return contract_document()

@public_router.get("/contract")
def public_contract():
    return contract_document()

@router.get("/reference")
def reference_bundle():
    bundle = reference_cross_lingual_semantic_exchange_bundle()
    return {"ok": True, "release": CORE_RELEASE, "bundle": bundle.model_dump(mode="json"), "bundle_fingerprint_sha256": bundle.fingerprint()}
