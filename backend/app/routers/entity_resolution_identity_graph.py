from fastapi import APIRouter

from app.services.entity_resolution_identity_graph import *

router = APIRouter(prefix="/v1/entity-resolution", tags=["entity-resolution-identity-graph"])
public_router = APIRouter(prefix="/public/v1/entity-resolution", tags=["public-entity-resolution-identity-graph"])


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    bundle = reference_entity_resolution_identity_graph_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
    }


@router.post("/validate-entity")
def validate_entity(body: CanonicalEntityRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-candidate-match")
def validate_candidate_match(body: CandidateEntityMatch):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-mutation-authorization")
def validate_mutation_authorization(body: IdentityMutationAuthorization):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(body: EntityResolutionIdentityGraphBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }
