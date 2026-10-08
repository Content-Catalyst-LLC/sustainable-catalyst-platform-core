from fastapi import APIRouter

from app.services.narrative_framing_perspective import (
    FramingSignal,
    NarrativeFrame,
    NarrativeFramingAssessment,
    NarrativeFramingPerspectiveBundle,
    PerspectiveComparison,
    SourcePerspective,
    contract_document,
    reference_narrative_framing_perspective_bundle,
)

router = APIRouter(prefix="/v1/narrative-framing", tags=["narrative-framing-perspective"])
public_router = APIRouter(prefix="/public/v1/narrative-framing", tags=["narrative-framing-perspective-public"])

@public_router.get("/contract")
def public_contract(): return contract_document()
@router.get("/contract")
def contract(): return contract_document()
@router.get("/reference")
def reference():
    b=reference_narrative_framing_perspective_bundle()
    return {"ok":True,"bundle_fingerprint_sha256":b.fingerprint(),"bundle":b.model_dump(mode="json")}
@router.get("/reference/perspectives")
def reference_perspectives():
    xs=reference_narrative_framing_perspective_bundle().perspectives
    return {"ok":True,"count":len(xs),"items":[x.model_dump(mode="json") for x in xs]}
@router.get("/reference/signals")
def reference_signals():
    xs=reference_narrative_framing_perspective_bundle().signals
    return {"ok":True,"count":len(xs),"items":[x.model_dump(mode="json") for x in xs]}
@router.get("/reference/frames")
def reference_frames():
    xs=reference_narrative_framing_perspective_bundle().frames
    return {"ok":True,"count":len(xs),"items":[x.model_dump(mode="json") for x in xs]}
@router.get("/reference/comparisons")
def reference_comparisons():
    xs=reference_narrative_framing_perspective_bundle().comparisons
    return {"ok":True,"count":len(xs),"items":[x.model_dump(mode="json") for x in xs]}
@router.get("/reference/assessments")
def reference_assessments():
    xs=reference_narrative_framing_perspective_bundle().assessments
    return {"ok":True,"count":len(xs),"items":[x.model_dump(mode="json") for x in xs]}
@router.post("/validate-perspective")
def validate_perspective(payload:SourcePerspective): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-signal")
def validate_signal(payload:FramingSignal): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-frame")
def validate_frame(payload:NarrativeFrame): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-comparison")
def validate_comparison(payload:PerspectiveComparison): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-assessment")
def validate_assessment(payload:NarrativeFramingAssessment): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(payload:NarrativeFramingPerspectiveBundle): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
