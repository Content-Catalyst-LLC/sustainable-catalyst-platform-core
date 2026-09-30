from fastapi import APIRouter

from app.services.explainable_connection_paths_evidence_chains import (
    ConnectionPathEvidenceSnapshot,
    EvidenceChain,
    ExplainableConnectionPath,
    ExplainableConnectionPathsEvidenceChainsBundle,
    contract_document,
    reference_explainable_connection_paths_evidence_chains_bundle,
)

router = APIRouter(prefix="/v1/connection-paths", tags=["connection-paths"])
public_router = APIRouter(prefix="/public/v1/connection-paths", tags=["connection-paths-public"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference():
    return {"ok": True, "bundle": reference_explainable_connection_paths_evidence_chains_bundle().model_dump(mode="json")}


@router.post("/validate-path")
def validate_path(payload: ExplainableConnectionPath):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-evidence-chain")
def validate_evidence_chain(payload: EvidenceChain):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-snapshot")
def validate_snapshot(payload: ConnectionPathEvidenceSnapshot):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: ExplainableConnectionPathsEvidenceChainsBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
