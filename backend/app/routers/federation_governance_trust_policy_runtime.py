from fastapi import APIRouter

from app.services.federation_governance_trust_policy_runtime import (
    FederationGovernanceTrustPolicyBundle, FederationPolicyDecision, FederationGovernedNode,
    contract_document, reference_federation_governance_trust_policy_bundle,
)

router = APIRouter(prefix="/v1/federation-governance", tags=["federation-governance"])
public_router = APIRouter(prefix="/public/v1/federation-governance", tags=["federation-governance-public"])

@router.get("/contract")
def private_contract(): return contract_document()

@public_router.get("/contract")
def public_contract(): return contract_document()

@router.get("/reference")
def reference(): return {"ok": True, "bundle": reference_federation_governance_trust_policy_bundle().model_dump(mode="json")}

@router.post("/validate-node")
def validate_node(payload: FederationGovernedNode): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}

@router.post("/validate-decision")
def validate_decision(payload: FederationPolicyDecision): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(payload: FederationGovernanceTrustPolicyBundle): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
