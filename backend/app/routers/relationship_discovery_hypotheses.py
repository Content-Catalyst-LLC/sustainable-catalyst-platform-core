from fastapi import APIRouter

from app.services.relationship_discovery_hypotheses import (
    ConnectionCandidate,
    ConnectionHypothesis,
    RelationshipDiscoveryHypothesisBundle,
    RelationshipDiscoverySignal,
    contract_document,
    reference_relationship_discovery_hypothesis_bundle,
)

router = APIRouter(prefix="/v1/relationship-discovery", tags=["relationship-discovery"])
public_router = APIRouter(prefix="/public/v1/relationship-discovery", tags=["relationship-discovery-public"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference():
    return {"ok": True, "bundle": reference_relationship_discovery_hypothesis_bundle().model_dump(mode="json")}


@router.post("/validate-signal")
def validate_signal(payload: RelationshipDiscoverySignal):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-candidate")
def validate_candidate(payload: ConnectionCandidate):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-hypothesis")
def validate_hypothesis(payload: ConnectionHypothesis):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: RelationshipDiscoveryHypothesisBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
