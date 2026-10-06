from fastapi import APIRouter

from app.services.epistemic_modal_negation_certainty import (
    Attribution,
    ConditionalScope,
    EpistemicAssessment,
    EpistemicCue,
    EpistemicInterpretation,
    EpistemicModalNegationCertaintyBundle,
    ModalScope,
    NegationScope,
    Proposition,
    contract_document,
    reference_epistemic_modal_negation_certainty_bundle,
)

router = APIRouter(prefix="/v1/epistemic-semantics", tags=["epistemic-semantics"])
public_router = APIRouter(prefix="/public/v1/epistemic-semantics", tags=["epistemic-semantics-public"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle = reference_epistemic_modal_negation_certainty_bundle()
    return {"ok": True, "bundle_fingerprint_sha256": bundle.fingerprint(), "bundle": bundle.model_dump(mode="json")}


@router.post("/validate-proposition")
def validate_proposition(payload: Proposition):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-attribution")
def validate_attribution(payload: Attribution):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-cue")
def validate_cue(payload: EpistemicCue):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-negation-scope")
def validate_negation_scope(payload: NegationScope):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-modal-scope")
def validate_modal_scope(payload: ModalScope):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-conditional-scope")
def validate_conditional_scope(payload: ConditionalScope):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-assessment")
def validate_assessment(payload: EpistemicAssessment):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-interpretation")
def validate_interpretation(payload: EpistemicInterpretation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: EpistemicModalNegationCertaintyBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
