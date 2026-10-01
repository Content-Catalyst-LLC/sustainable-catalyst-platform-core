from fastapi import APIRouter

from app.services.unified_core_production_certification_soak import (
    ContractCertificationRecord,
    ProductionReadinessDecision,
    UnifiedCoreProductionCertificationSoakBundle,
    contract_document,
    reference_unified_core_production_certification_soak_bundle,
)

router = APIRouter(prefix="/v1/production-certification", tags=["production-certification"])
public_router = APIRouter(prefix="/public/v1/production-certification", tags=["production-certification-public"])

@router.get("/contract")
def private_contract(): return contract_document()

@public_router.get("/contract")
def public_contract(): return contract_document()

@router.get("/reference")
def reference(): return {"ok": True, "bundle": reference_unified_core_production_certification_soak_bundle().model_dump(mode="json")}

@router.post("/validate-contract-record")
def validate_contract_record(payload: ContractCertificationRecord): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}

@router.post("/validate-decision")
def validate_decision(payload: ProductionReadinessDecision): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(payload: UnifiedCoreProductionCertificationSoakBundle): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
