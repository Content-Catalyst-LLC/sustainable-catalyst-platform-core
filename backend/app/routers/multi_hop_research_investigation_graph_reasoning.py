from fastapi import APIRouter

from app.services.multi_hop_research_investigation_graph_reasoning import (
    MultiHopReasoningQuery,
    MultiHopReasoningTrace,
    MultiHopResearchInvestigationGraphReasoningBundle,
    ReasoningBranch,
    contract_document,
    reference_multi_hop_research_investigation_graph_reasoning_bundle,
)

router = APIRouter(prefix="/v1/multi-hop-reasoning", tags=["multi-hop-reasoning"])
public_router = APIRouter(prefix="/public/v1/multi-hop-reasoning", tags=["multi-hop-reasoning-public"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference():
    return {"ok": True, "bundle": reference_multi_hop_research_investigation_graph_reasoning_bundle().model_dump(mode="json")}


@router.post("/validate-query")
def validate_query(payload: MultiHopReasoningQuery):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-branch")
def validate_branch(payload: ReasoningBranch):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-trace")
def validate_trace(payload: MultiHopReasoningTrace):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: MultiHopResearchInvestigationGraphReasoningBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
