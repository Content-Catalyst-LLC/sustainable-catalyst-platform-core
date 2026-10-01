from fastapi import APIRouter

from app.services.unified_entity_evidence_intelligence_runtime import (
    UnifiedEntityEvidenceIntelligenceRuntimeBundle, UnifiedRuntimeRequest,
    contract_document, reference_unified_entity_evidence_intelligence_runtime_bundle,
)

router=APIRouter(prefix="/v1/unified-entity-evidence-runtime",tags=["unified-entity-evidence-runtime"])
public_router=APIRouter(prefix="/public/v1/unified-entity-evidence-runtime",tags=["unified-entity-evidence-runtime-public"])

@router.get("/contract")
def private_contract(): return contract_document()

@public_router.get("/contract")
def public_contract(): return contract_document()

@router.get("/reference")
def reference(): return {"ok":True,"bundle":reference_unified_entity_evidence_intelligence_runtime_bundle().model_dump(mode="json")}

@router.post("/validate-request")
def validate_request(payload: UnifiedRuntimeRequest): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(payload: UnifiedEntityEvidenceIntelligenceRuntimeBundle): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
