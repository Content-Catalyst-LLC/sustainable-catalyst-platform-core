from fastapi import APIRouter

from app.services.probabilistic_record_linkage import (
    ProbabilisticRecordLinkageBundle,
    RecordLinkageCandidatePair,
    EntityMatchProbabilityRecord,
    PairwiseEntityMatchDecision,
    contract_document,
    reference_probabilistic_record_linkage_bundle,
)

router = APIRouter(prefix="/v1/record-linkage", tags=["record-linkage"])
public_router = APIRouter(prefix="/public/v1/record-linkage", tags=["record-linkage-public"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference():
    return {"ok": True, "bundle": reference_probabilistic_record_linkage_bundle().model_dump(mode="json")}


@router.post("/validate-pair")
def validate_pair(payload: RecordLinkageCandidatePair):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-probability")
def validate_probability(payload: EntityMatchProbabilityRecord):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-decision")
def validate_decision(payload: PairwiseEntityMatchDecision):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: ProbabilisticRecordLinkageBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
