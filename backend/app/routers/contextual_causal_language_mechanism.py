from fastapi import APIRouter

from app.services.contextual_causal_language_mechanism import (
    CausalAssessment,
    CausalLanguageSignal,
    ContextualCausalLanguageMechanismBundle,
    CounterfactualContext,
    InterventionContext,
    MechanismHypothesis,
    contract_document,
    reference_contextual_causal_language_mechanism_bundle,
)

router = APIRouter(prefix="/v1/causal-context", tags=["contextual-causal-language-mechanism"])
public_router = APIRouter(prefix="/public/v1/causal-context", tags=["contextual-causal-language-mechanism-public"])

@public_router.get("/contract")
def public_contract(): return contract_document()

@router.get("/contract")
def contract(): return contract_document()

@router.get("/reference")
def reference():
    b=reference_contextual_causal_language_mechanism_bundle()
    return {"ok":True,"bundle_fingerprint_sha256":b.fingerprint(),"bundle":b.model_dump(mode="json")}

@router.get("/reference/signals")
def reference_signals():
    xs=reference_contextual_causal_language_mechanism_bundle().signals
    return {"ok":True,"count":len(xs),"items":[x.model_dump(mode="json") for x in xs]}

@router.get("/reference/mechanisms")
def reference_mechanisms():
    xs=reference_contextual_causal_language_mechanism_bundle().mechanisms
    return {"ok":True,"count":len(xs),"items":[x.model_dump(mode="json") for x in xs]}

@router.get("/reference/interventions")
def reference_interventions():
    xs=reference_contextual_causal_language_mechanism_bundle().intervention_contexts
    return {"ok":True,"count":len(xs),"items":[x.model_dump(mode="json") for x in xs]}

@router.get("/reference/counterfactuals")
def reference_counterfactuals():
    xs=reference_contextual_causal_language_mechanism_bundle().counterfactual_contexts
    return {"ok":True,"count":len(xs),"items":[x.model_dump(mode="json") for x in xs]}

@router.get("/reference/assessments")
def reference_assessments():
    xs=reference_contextual_causal_language_mechanism_bundle().assessments
    return {"ok":True,"count":len(xs),"items":[x.model_dump(mode="json") for x in xs]}

@router.post("/validate-signal")
def validate_signal(payload:CausalLanguageSignal): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-mechanism")
def validate_mechanism(payload:MechanismHypothesis): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-intervention")
def validate_intervention(payload:InterventionContext): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-counterfactual")
def validate_counterfactual(payload:CounterfactualContext): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-assessment")
def validate_assessment(payload:CausalAssessment): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(payload:ContextualCausalLanguageMechanismBundle): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
