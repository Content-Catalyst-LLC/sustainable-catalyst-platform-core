from fastapi import APIRouter

from app.services.temporal_identity_intelligence import *

router = APIRouter(prefix="/v1/temporal-identity", tags=["temporal-identity-intelligence"])
public_router = APIRouter(prefix="/public/v1/temporal-identity", tags=["public-temporal-identity-intelligence"])

@router.get("/contract")
def get_contract():
    return contract_document()

@public_router.get("/contract")
def get_public_contract():
    return contract_document()

@router.get("/reference")
def get_reference():
    bundle = reference_temporal_identity_intelligence_bundle()
    return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "bundle": bundle.model_dump(mode="json", exclude_none=True), "bundle_fingerprint_sha256": bundle.fingerprint()}

@router.post("/validate-name")
def validate_name(body: TemporalNameVariant):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-identifier")
def validate_identifier(body: TemporalIdentifierAssertion):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-role")
def validate_role(body: TemporalRoleTitleAssertion):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(body: TemporalIdentityIntelligenceBundle):
    return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "bundle_fingerprint_sha256": body.fingerprint()}
