from fastapi import APIRouter

from ..services.ml_embedding_representation import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    MLEmbeddingObjectRecord,
    MLEmbeddingSpaceRecord,
    MLRepresentationClusterRecord,
    MLRepresentationIntelligenceBundle,
    MLRepresentationModelRecord,
    MLSimilarityResultRecord,
    MLVectorProjectionRecord,
    contract_document,
    reference_representation_intelligence_bundle,
)

router = APIRouter(prefix="/api/v1/ml-representations", tags=["ml-representations"])
public_router = APIRouter(prefix="/public/v1/ml-representations", tags=["public-ml-representations"])


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    bundle = reference_representation_intelligence_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
    }


@router.post("/validate-representation-model")
def validate_representation_model(body: MLRepresentationModelRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-embedding-space")
def validate_embedding_space(body: MLEmbeddingSpaceRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-embedding")
def validate_embedding(body: MLEmbeddingObjectRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-similarity")
def validate_similarity(body: MLSimilarityResultRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-projection")
def validate_projection(body: MLVectorProjectionRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-cluster")
def validate_cluster(body: MLRepresentationClusterRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(body: MLRepresentationIntelligenceBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }
