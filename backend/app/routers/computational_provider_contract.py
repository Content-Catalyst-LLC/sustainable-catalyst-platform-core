from fastapi import APIRouter

from app.services.computational_provider_contract import (
    ComputationalProviderContractBundle,
    contract_document,
    reference_computational_provider_contract_bundle,
)

router = APIRouter(prefix="/v1/computational-providers", tags=["computational-provider-contract"])
public_router = APIRouter(prefix="/public/v1/computational-providers", tags=["computational-provider-contract-public"])


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/contract")
def contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle=reference_computational_provider_contract_bundle()
    return {"ok":True,"bundle_fingerprint_sha256":bundle.fingerprint(),"bundle":bundle.model_dump(mode="json")}


@router.get("/reference/providers")
def reference_providers():
    items=reference_computational_provider_contract_bundle().providers
    return {"ok":True,"count":len(items),"items":[x.model_dump(mode="json") for x in items]}


@router.get("/reference/providers/{profile_id:path}")
def reference_provider(profile_id:str):
    for item in reference_computational_provider_contract_bundle().providers:
        if item.profile_id==profile_id:
            return {"ok":True,"item":item.model_dump(mode="json"),"fingerprint_sha256":item.fingerprint()}
    return {"ok":False,"error":"computational-provider-profile-not-found","profile_id":profile_id}


@router.get("/reference/requests")
def reference_requests():
    b=reference_computational_provider_contract_bundle()
    return {"ok":True,"count":len(b.requests),"items":[x.model_dump(mode="json") for x in b.requests]}


@router.get("/reference/comparisons")
def reference_comparisons():
    b=reference_computational_provider_contract_bundle()
    return {"ok":True,"count":len(b.comparisons),"items":[x.model_dump(mode="json") for x in b.comparisons]}


@router.post("/validate-bundle")
def validate_bundle(payload:ComputationalProviderContractBundle):
    return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
