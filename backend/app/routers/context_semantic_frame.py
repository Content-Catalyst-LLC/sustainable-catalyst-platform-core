from fastapi import APIRouter

from app.services.context_semantic_frame import (
    ContextObject,
    ContextObjectSemanticFrameBundle,
    SemanticFrame,
    SemanticInterpretation,
    contract_document,
    reference_context_object_semantic_frame_bundle,
)

router = APIRouter(prefix="/v1/context-semantics", tags=["context-semantics"])
public_router = APIRouter(prefix="/public/v1/context-semantics", tags=["context-semantics-public"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle = reference_context_object_semantic_frame_bundle()
    return {
        "ok": True,
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "bundle": bundle.model_dump(mode="json"),
    }


@router.post("/validate-context")
def validate_context(payload: ContextObject):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-frame")
def validate_frame(payload: SemanticFrame):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-interpretation")
def validate_interpretation(payload: SemanticInterpretation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: ContextObjectSemanticFrameBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
