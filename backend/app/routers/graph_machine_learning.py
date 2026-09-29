from fastapi import APIRouter

from app.services.graph_machine_learning import (
    CORE_RELEASE,
    contract_document,
    reference_graph_ml_foundation_bundle,
)

router = APIRouter(prefix="/api/v1/graph-ml", tags=["Graph Machine Learning"])
public_router = APIRouter(prefix="/public/v1/graph-ml", tags=["Public Graph Machine Learning"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference_bundle():
    bundle = reference_graph_ml_foundation_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "bundle": bundle.model_dump(mode="json"),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
    }
