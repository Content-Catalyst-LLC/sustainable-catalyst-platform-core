from fastapi import APIRouter

from app.services.discourse_rhetorical_semantics import (
    ArgumentRelation,
    ArgumentUnit,
    DiscourseInterpretation,
    DiscourseSegment,
    DiscourseStructureRhetoricalSemanticsBundle,
    RhetoricalRelation,
    contract_document,
    reference_discourse_structure_rhetorical_semantics_bundle,
)

router = APIRouter(prefix="/v1/discourse-semantics", tags=["discourse-semantics"])
public_router = APIRouter(prefix="/public/v1/discourse-semantics", tags=["discourse-semantics-public"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle = reference_discourse_structure_rhetorical_semantics_bundle()
    return {
        "ok": True,
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "bundle": bundle.model_dump(mode="json"),
    }


@router.post("/validate-segment")
def validate_segment(payload: DiscourseSegment):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-rhetorical-relation")
def validate_rhetorical_relation(payload: RhetoricalRelation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-argument-unit")
def validate_argument_unit(payload: ArgumentUnit):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-argument-relation")
def validate_argument_relation(payload: ArgumentRelation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-interpretation")
def validate_interpretation(payload: DiscourseInterpretation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: DiscourseStructureRhetoricalSemanticsBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
