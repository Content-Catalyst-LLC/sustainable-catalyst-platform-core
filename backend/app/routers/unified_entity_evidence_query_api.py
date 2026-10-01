from fastapi import APIRouter

from app.services.unified_entity_evidence_query_api import (
    UnifiedEntityEvidenceQuery,
    UnifiedEntityEvidenceQueryBundle,
    contract_document,
    reference_unified_entity_evidence_query_bundle,
)

router = APIRouter(prefix="/v1/entity-evidence-query", tags=["entity-evidence-query"])
public_router = APIRouter(prefix="/public/v1/entity-evidence-query", tags=["entity-evidence-query-public"])

@router.get("/contract")
def private_contract(): return contract_document()

@public_router.get("/contract")
def public_contract(): return contract_document()

@router.get("/reference")
def reference(): return {"ok":True,"bundle":reference_unified_entity_evidence_query_bundle().model_dump(mode="json")}

@router.post("/validate-query")
def validate_query(payload: UnifiedEntityEvidenceQuery): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(payload: UnifiedEntityEvidenceQueryBundle): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
