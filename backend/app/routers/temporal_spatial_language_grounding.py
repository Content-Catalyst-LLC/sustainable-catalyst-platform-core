from fastapi import APIRouter

from app.services.temporal_spatial_language_grounding import (
    GroundingCandidate,
    GroundingCandidateSet,
    SpatialExpression,
    SpatialGrounding,
    TemporalExpression,
    TemporalGrounding,
    TemporalRelationGrounding,
    TemporalSpatialLanguageGroundingBundle,
    TemporalSpatialGroundingInterpretation,
    contract_document,
    reference_temporal_spatial_language_grounding_bundle,
)

router = APIRouter(prefix="/v1/language-grounding", tags=["language-grounding"])
public_router = APIRouter(prefix="/public/v1/language-grounding", tags=["language-grounding-public"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle = reference_temporal_spatial_language_grounding_bundle()
    return {"ok": True, "bundle_fingerprint_sha256": bundle.fingerprint(), "bundle": bundle.model_dump(mode="json")}


@router.post("/validate-temporal-expression")
def validate_temporal_expression(payload: TemporalExpression):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-spatial-expression")
def validate_spatial_expression(payload: SpatialExpression):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-candidate")
def validate_candidate(payload: GroundingCandidate):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-candidate-set")
def validate_candidate_set(payload: GroundingCandidateSet):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-temporal-grounding")
def validate_temporal_grounding(payload: TemporalGrounding):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-spatial-grounding")
def validate_spatial_grounding(payload: SpatialGrounding):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-temporal-relation")
def validate_temporal_relation(payload: TemporalRelationGrounding):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-interpretation")
def validate_interpretation(payload: TemporalSpatialGroundingInterpretation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: TemporalSpatialLanguageGroundingBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
