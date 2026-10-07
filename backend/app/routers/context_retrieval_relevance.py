from fastapi import APIRouter

from app.services.context_retrieval_relevance import (
    ContextRetrievalQuery,
    ContextRetrievalRelevanceBundle,
    ContextRetrievalResultSet,
    RetrievalCandidate,
    contract_document,
    reference_context_retrieval_relevance_bundle,
)

router = APIRouter(prefix="/v1/context-retrieval", tags=["context-retrieval-relevance"])
public_router = APIRouter(prefix="/public/v1/context-retrieval", tags=["context-retrieval-relevance-public"])


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/contract")
def contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle = reference_context_retrieval_relevance_bundle()
    return {"ok": True, "bundle_fingerprint_sha256": bundle.fingerprint(), "bundle": bundle.model_dump(mode="json")}


@router.get("/reference/query")
def reference_query():
    q = reference_context_retrieval_relevance_bundle().queries[0]
    return {"ok": True, "query": q.model_dump(mode="json"), "fingerprint_sha256": q.fingerprint()}


@router.get("/reference/candidates")
def reference_candidates():
    items = reference_context_retrieval_relevance_bundle().candidates
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.get("/reference/results")
def reference_results():
    item = reference_context_retrieval_relevance_bundle().result_sets[0]
    return {"ok": True, "result_set": item.model_dump(mode="json"), "fingerprint_sha256": item.fingerprint()}


@router.post("/validate-query")
def validate_query(payload: ContextRetrievalQuery):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-candidate")
def validate_candidate(payload: RetrievalCandidate):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-result-set")
def validate_result_set(payload: ContextRetrievalResultSet):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: ContextRetrievalRelevanceBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
