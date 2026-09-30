from fastapi import APIRouter

from app.services.cross_source_entity_reconciliation import (
    CrossSourceEntityReconciliationBundle,
    CrossSourceEntityReconciliationCluster,
    CrossSourceReconciliationDecision,
    SourceIdentityObservation,
    contract_document,
    reference_cross_source_entity_reconciliation_bundle,
)

router = APIRouter(prefix="/v1/entity-reconciliation", tags=["entity-reconciliation"])
public_router = APIRouter(prefix="/public/v1/entity-reconciliation", tags=["entity-reconciliation-public"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference():
    return {"ok": True, "bundle": reference_cross_source_entity_reconciliation_bundle().model_dump(mode="json")}


@router.post("/validate-observation")
def validate_observation(payload: SourceIdentityObservation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-cluster")
def validate_cluster(payload: CrossSourceEntityReconciliationCluster):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-decision")
def validate_decision(payload: CrossSourceReconciliationDecision):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: CrossSourceEntityReconciliationBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
