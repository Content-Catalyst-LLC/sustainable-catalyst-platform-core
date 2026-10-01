from fastapi import APIRouter

from app.services.unified_runtime_observability_audit_drift_intelligence import (
    UnifiedRuntimeObservabilityAuditDriftBundle, ObservabilityAlertDecision, DriftObservation,
    contract_document, reference_unified_runtime_observability_audit_drift_bundle,
)

router = APIRouter(prefix="/v1/runtime-observability", tags=["runtime-observability"])
public_router = APIRouter(prefix="/public/v1/runtime-observability", tags=["runtime-observability-public"])

@router.get("/contract")
def private_contract(): return contract_document()

@public_router.get("/contract")
def public_contract(): return contract_document()

@router.get("/reference")
def reference(): return {"ok": True, "bundle": reference_unified_runtime_observability_audit_drift_bundle().model_dump(mode="json")}

@router.post("/validate-drift")
def validate_drift(payload: DriftObservation): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}

@router.post("/validate-alert")
def validate_alert(payload: ObservabilityAlertDecision): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(payload: UnifiedRuntimeObservabilityAuditDriftBundle): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
