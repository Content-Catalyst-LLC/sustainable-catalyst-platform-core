from fastapi import APIRouter

from app.services.multilingual_context_semantic_alignment import (
    AlignmentReviewState,
    ContextAlignmentRelation,
    ContextGraphProjectionBinding,
    ContextLanguageRepresentation,
    ContextRepresentationRole,
    MultilingualContextAlignment,
    MultilingualContextInterpretation,
    MultilingualContextSemanticAlignmentBundle,
    SemanticDivergenceRecord,
    contract_document,
    reference_multilingual_context_semantic_alignment_bundle,
)

router = APIRouter(prefix="/v1/multilingual-context", tags=["multilingual-context-semantic-alignment"])
public_router = APIRouter(prefix="/public/v1/multilingual-context", tags=["multilingual-context-semantic-alignment-public"])


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/contract")
def contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle = reference_multilingual_context_semantic_alignment_bundle()
    return {"ok": True, "bundle_fingerprint_sha256": bundle.fingerprint(), "bundle": bundle.model_dump(mode="json")}


@router.get("/reference/representations")
def reference_representations(role: ContextRepresentationRole | None = None, language_ref: str | None = None):
    items = reference_multilingual_context_semantic_alignment_bundle().representations
    if role is not None:
        items = [x for x in items if x.role == role]
    if language_ref is not None:
        items = [x for x in items if x.language_ref == language_ref]
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.get("/reference/alignments")
def reference_alignments(relation: ContextAlignmentRelation | None = None, state: AlignmentReviewState | None = None):
    items = reference_multilingual_context_semantic_alignment_bundle().alignments
    if relation is not None:
        items = [x for x in items if x.relation == relation]
    if state is not None:
        items = [x for x in items if x.state == state]
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.get("/reference/divergences")
def reference_divergences(state: AlignmentReviewState | None = None):
    items = reference_multilingual_context_semantic_alignment_bundle().divergences
    if state is not None:
        items = [x for x in items if x.state == state]
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.post("/validate-representation")
def validate_representation(payload: ContextLanguageRepresentation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-alignment")
def validate_alignment(payload: MultilingualContextAlignment):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-divergence")
def validate_divergence(payload: SemanticDivergenceRecord):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-projection")
def validate_projection(payload: ContextGraphProjectionBinding):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-interpretation")
def validate_interpretation(payload: MultilingualContextInterpretation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: MultilingualContextSemanticAlignmentBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
