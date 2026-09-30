from fastapi import APIRouter

from app.services.contradictory_identity_relationship_resolution import (
    ContradictionResolutionDecision,
    ContradictionSet,
    ContradictoryIdentityRelationshipResolutionBundle,
    contract_document,
    reference_contradictory_identity_relationship_resolution_bundle,
)

router = APIRouter(prefix="/v1/contradiction-resolution", tags=["contradiction-resolution"])
public_router = APIRouter(prefix="/public/v1/contradiction-resolution", tags=["contradiction-resolution-public"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference():
    return {"ok": True, "bundle": reference_contradictory_identity_relationship_resolution_bundle().model_dump(mode="json")}


@router.post("/validate-contradiction-set")
def validate_contradiction_set(payload: ContradictionSet):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-decision")
def validate_decision(payload: ContradictionResolutionDecision):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: ContradictoryIdentityRelationshipResolutionBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
