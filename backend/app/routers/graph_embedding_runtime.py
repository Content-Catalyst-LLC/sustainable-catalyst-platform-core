from fastapi import APIRouter

from ..services.graph_embedding_runtime import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    GraphEmbeddingBundle,
    GraphEmbeddingObject,
    GraphEmbeddingRuntimeContract,
    GraphEmbeddingSpaceContract,
    GraphSimilarityQueryRecord,
    contract_document,
    reference_graph_embedding_bundle,
)

router = APIRouter(prefix="/api/v1/graph-embeddings", tags=["graph-embeddings"])
public_router = APIRouter(prefix="/public/v1/graph-embeddings", tags=["public-graph-embeddings"])


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    bundle = reference_graph_embedding_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
    }


@router.post("/validate-runtime")
def validate_runtime(body: GraphEmbeddingRuntimeContract):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-space")
def validate_space(body: GraphEmbeddingSpaceContract):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-embedding")
def validate_embedding(body: GraphEmbeddingObject):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-similarity-query")
def validate_similarity_query(body: GraphSimilarityQueryRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(body: GraphEmbeddingBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }
