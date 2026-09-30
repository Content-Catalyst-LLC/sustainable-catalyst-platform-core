from fastapi import APIRouter

from app.services.network_structure_community_motif import (
    CommunityAssignment,
    MotifInstance,
    NetworkStructureCommunityMotifBundle,
    NetworkStructureSnapshot,
    contract_document,
    reference_network_structure_community_motif_bundle,
)

router = APIRouter(prefix="/v1/network-intelligence", tags=["network-intelligence"])
public_router = APIRouter(prefix="/public/v1/network-intelligence", tags=["network-intelligence-public"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference():
    return {"ok": True, "bundle": reference_network_structure_community_motif_bundle().model_dump(mode="json")}


@router.post("/validate-structure")
def validate_structure(payload: NetworkStructureSnapshot):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-community-assignment")
def validate_community_assignment(payload: CommunityAssignment):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-motif-instance")
def validate_motif_instance(payload: MotifInstance):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: NetworkStructureCommunityMotifBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
