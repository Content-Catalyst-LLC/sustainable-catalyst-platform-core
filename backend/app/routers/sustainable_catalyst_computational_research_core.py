from fastapi import APIRouter
from app.services.sustainable_catalyst_computational_research_core import (
    UpstreamContractBinding, MajorReleaseReadiness, SustainableCatalystComputationalResearchCoreBundle,
    contract_document, reference_sustainable_catalyst_computational_research_core_bundle,
)
router=APIRouter(prefix="/v1/computational-research-core",tags=["computational-research-core"])
public_router=APIRouter(prefix="/public/v1/computational-research-core",tags=["computational-research-core-public"])
@router.get("/contract")
def private_contract(): return contract_document()
@public_router.get("/contract")
def public_contract(): return contract_document()
@router.get("/reference")
def reference(): return {"ok":True,"bundle":reference_sustainable_catalyst_computational_research_core_bundle().model_dump(mode="json")}
@router.post("/validate-upstream-contract")
def validate_upstream_contract(payload: UpstreamContractBinding): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-readiness")
def validate_readiness(payload: MajorReleaseReadiness): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(payload: SustainableCatalystComputationalResearchCoreBundle): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
