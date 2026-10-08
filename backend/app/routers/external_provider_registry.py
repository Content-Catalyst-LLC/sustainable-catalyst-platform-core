from fastapi import APIRouter

from app.services.external_provider_registry import (
    ExternalProviderRegistryBundle,
    contract_document,
    reference_external_provider_registry_bundle,
)

router = APIRouter(prefix="/v1/providers", tags=["external-provider-registry"])
public_router = APIRouter(prefix="/public/v1/providers", tags=["external-provider-registry-public"])


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/contract")
def contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle = reference_external_provider_registry_bundle()
    return {"ok": True, "bundle_fingerprint_sha256": bundle.fingerprint(), "bundle": bundle.model_dump(mode="json")}


@router.get("/reference/providers")
def reference_providers():
    items = reference_external_provider_registry_bundle().providers
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.get("/reference/providers/{provider_id:path}")
def reference_provider(provider_id: str):
    for item in reference_external_provider_registry_bundle().providers:
        if item.provider_id == provider_id:
            return {"ok": True, "item": item.model_dump(mode="json"), "fingerprint_sha256": item.fingerprint()}
    return {"ok": False, "error": "provider-not-found", "provider_id": provider_id}


@router.post("/validate-bundle")
def validate_bundle(payload: ExternalProviderRegistryBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
