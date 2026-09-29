from fastapi import APIRouter

from ..services.graph_link_prediction import (
    CORE_RELEASE, CONTRACT_VERSION, CandidateRelationship, GraphLinkPredictionBundle,
    LinkPredictionRecord, LinkPredictionRuntimeContract, contract_document,
    reference_graph_link_prediction_bundle,
)

router = APIRouter(prefix="/api/v1/link-prediction", tags=["graph-link-prediction"])
public_router = APIRouter(prefix="/public/v1/link-prediction", tags=["public-graph-link-prediction"])

@router.get("/contract")
def get_contract(): return contract_document()

@public_router.get("/contract")
def get_public_contract(): return contract_document()

@router.get("/reference")
def get_reference():
    b = reference_graph_link_prediction_bundle()
    return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "bundle": b.model_dump(mode="json", exclude_none=True), "bundle_fingerprint_sha256": b.fingerprint()}

@router.post("/validate-runtime")
def validate_runtime(body: LinkPredictionRuntimeContract): return {"ok": True, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-prediction")
def validate_prediction(body: LinkPredictionRecord): return {"ok": True, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-candidate")
def validate_candidate(body: CandidateRelationship): return {"ok": True, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(body: GraphLinkPredictionBundle): return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "bundle_fingerprint_sha256": body.fingerprint()}
