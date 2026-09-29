from fastapi import APIRouter

from app.services.historical_language_variant import (
    CORE_RELEASE,
    contract_document,
    reference_historical_language_variant_bundle,
)

router = APIRouter(prefix="/api/v1/historical-language", tags=["Historical Language Identity"])
public_router = APIRouter(prefix="/public/v1/historical-language", tags=["Public Historical Language Identity"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference_bundle():
    bundle = reference_historical_language_variant_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "bundle": bundle.model_dump(mode="json"),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
    }
