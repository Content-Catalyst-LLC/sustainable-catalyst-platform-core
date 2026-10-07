from fastapi import APIRouter

from app.services.claim_alignment_agreement_contradiction import (
    ClaimAlignmentAgreementContradictionBundle,
    ClaimComparisonPair,
    ClaimComparisonQuery,
    ClaimRelationAssessment,
    ClaimUnit,
    contract_document,
    reference_claim_alignment_agreement_contradiction_bundle,
)

router = APIRouter(prefix="/v1/claim-comparison", tags=["claim-alignment-agreement-contradiction"])
public_router = APIRouter(prefix="/public/v1/claim-comparison", tags=["claim-alignment-agreement-contradiction-public"])


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/contract")
def contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle = reference_claim_alignment_agreement_contradiction_bundle()
    return {"ok": True, "bundle_fingerprint_sha256": bundle.fingerprint(), "bundle": bundle.model_dump(mode="json")}


@router.get("/reference/claims")
def reference_claims():
    items = reference_claim_alignment_agreement_contradiction_bundle().claims
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.get("/reference/pairs")
def reference_pairs():
    items = reference_claim_alignment_agreement_contradiction_bundle().pairs
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.get("/reference/assessments")
def reference_assessments():
    items = reference_claim_alignment_agreement_contradiction_bundle().assessments
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.post("/validate-claim")
def validate_claim(payload: ClaimUnit):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-query")
def validate_query(payload: ClaimComparisonQuery):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-pair")
def validate_pair(payload: ClaimComparisonPair):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-assessment")
def validate_assessment(payload: ClaimRelationAssessment):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: ClaimAlignmentAgreementContradictionBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
