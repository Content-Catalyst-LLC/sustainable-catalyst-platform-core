from fastapi import APIRouter

from app.services.coreference_referential_identity import (
    CoreferenceChain,
    CoreferenceLink,
    CoreferenceReferentialIdentityBundle,
    ReferenceExpression,
    ReferentCandidate,
    ReferentCandidateSet,
    ReferentialIdentityBinding,
    ReferentialInterpretation,
    contract_document,
    reference_coreference_referential_identity_bundle,
)

router = APIRouter(prefix="/v1/referential-identity", tags=["referential-identity"])
public_router = APIRouter(prefix="/public/v1/referential-identity", tags=["referential-identity-public"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle = reference_coreference_referential_identity_bundle()
    return {
        "ok": True,
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "bundle": bundle.model_dump(mode="json"),
    }


@router.post("/validate-reference-expression")
def validate_reference_expression(payload: ReferenceExpression):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-candidate")
def validate_candidate(payload: ReferentCandidate):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-candidate-set")
def validate_candidate_set(payload: ReferentCandidateSet):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-coreference-link")
def validate_coreference_link(payload: CoreferenceLink):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-coreference-chain")
def validate_coreference_chain(payload: CoreferenceChain):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-identity-binding")
def validate_identity_binding(payload: ReferentialIdentityBinding):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-interpretation")
def validate_interpretation(payload: ReferentialInterpretation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: CoreferenceReferentialIdentityBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
