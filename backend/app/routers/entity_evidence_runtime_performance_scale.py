from fastapi import APIRouter

from app.services.entity_evidence_runtime_performance_scale import (
    EntityEvidenceRuntimePerformanceScaleBundle,
    ScaleBenchmarkResult,
    DegradationDecision,
    contract_document,
    reference_entity_evidence_runtime_performance_scale_bundle,
)

router = APIRouter(prefix="/v1/runtime-performance-scale", tags=["runtime-performance-scale"])
public_router = APIRouter(prefix="/public/v1/runtime-performance-scale", tags=["runtime-performance-scale-public"])

@router.get("/contract")
def private_contract(): return contract_document()

@public_router.get("/contract")
def public_contract(): return contract_document()

@router.get("/reference")
def reference(): return {"ok": True, "bundle": reference_entity_evidence_runtime_performance_scale_bundle().model_dump(mode="json")}

@router.post("/validate-benchmark")
def validate_benchmark(payload: ScaleBenchmarkResult): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}

@router.post("/validate-degradation")
def validate_degradation(payload: DegradationDecision): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(payload: EntityEvidenceRuntimePerformanceScaleBundle): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
