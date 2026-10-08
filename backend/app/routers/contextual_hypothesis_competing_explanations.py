from fastapi import APIRouter

from app.services.contextual_hypothesis_competing_explanations import (
    CompetingExplanationComparison,
    CompetingExplanationSet,
    ContextualHypothesis,
    ContextualHypothesisCompetingExplanationBundle,
    HypothesisEvidencePosition,
    contract_document,
    reference_contextual_hypothesis_competing_explanation_bundle,
)

router = APIRouter(prefix="/v1/context-hypotheses", tags=["contextual-hypothesis-competing-explanations"])
public_router = APIRouter(prefix="/public/v1/context-hypotheses", tags=["contextual-hypothesis-competing-explanations-public"])

@public_router.get("/contract")
def public_contract(): return contract_document()
@router.get("/contract")
def contract(): return contract_document()
@router.get("/reference")
def reference():
    b = reference_contextual_hypothesis_competing_explanation_bundle()
    return {"ok": True, "bundle_fingerprint_sha256": b.fingerprint(), "bundle": b.model_dump(mode="json")}
@router.get("/reference/hypotheses")
def reference_hypotheses():
    xs = reference_contextual_hypothesis_competing_explanation_bundle().hypotheses
    return {"ok": True, "count": len(xs), "items": [x.model_dump(mode="json") for x in xs]}
@router.get("/reference/evidence-positions")
def reference_evidence_positions():
    xs = reference_contextual_hypothesis_competing_explanation_bundle().evidence_positions
    return {"ok": True, "count": len(xs), "items": [x.model_dump(mode="json") for x in xs]}
@router.get("/reference/comparisons")
def reference_comparisons():
    xs = reference_contextual_hypothesis_competing_explanation_bundle().comparisons
    return {"ok": True, "count": len(xs), "items": [x.model_dump(mode="json") for x in xs]}
@router.get("/reference/explanation-sets")
def reference_explanation_sets():
    xs = reference_contextual_hypothesis_competing_explanation_bundle().explanation_sets
    return {"ok": True, "count": len(xs), "items": [x.model_dump(mode="json") for x in xs]}
@router.post("/validate-hypothesis")
def validate_hypothesis(payload: ContextualHypothesis): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
@router.post("/validate-evidence-position")
def validate_evidence_position(payload: HypothesisEvidencePosition): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
@router.post("/validate-comparison")
def validate_comparison(payload: CompetingExplanationComparison): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
@router.post("/validate-explanation-set")
def validate_explanation_set(payload: CompetingExplanationSet): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(payload: ContextualHypothesisCompetingExplanationBundle): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
