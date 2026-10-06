from fastapi import APIRouter

from app.services.pragmatic_meaning_speech_act_intent import (
    CommunicativeIntent,
    PragmaticContext,
    PragmaticInterpretation,
    PragmaticMeaningSpeechActIntentBundle,
    SpeechAct,
    contract_document,
    reference_pragmatic_meaning_speech_act_intent_bundle,
)

router = APIRouter(prefix="/v1/pragmatic-semantics", tags=["pragmatic-semantics"])
public_router = APIRouter(prefix="/public/v1/pragmatic-semantics", tags=["pragmatic-semantics-public"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle = reference_pragmatic_meaning_speech_act_intent_bundle()
    return {"ok": True, "bundle_fingerprint_sha256": bundle.fingerprint(), "bundle": bundle.model_dump(mode="json")}


@router.post("/validate-context")
def validate_context(payload: PragmaticContext):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-speech-act")
def validate_speech_act(payload: SpeechAct):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-intent")
def validate_intent(payload: CommunicativeIntent):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-interpretation")
def validate_interpretation(payload: PragmaticInterpretation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: PragmaticMeaningSpeechActIntentBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
