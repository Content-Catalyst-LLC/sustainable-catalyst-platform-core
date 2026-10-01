from fastapi import APIRouter

from app.services.signed_runtime_artifacts_execution_attestations import (
    SignedRuntimeArtifactsExecutionAttestationsBundle, DetachedExecutionAttestation, RuntimeExecutionManifest,
    contract_document, reference_signed_runtime_artifacts_execution_attestations_bundle,
)

router = APIRouter(prefix="/v1/signed-runtime-attestations", tags=["signed-runtime-attestations"])
public_router = APIRouter(prefix="/public/v1/signed-runtime-attestations", tags=["signed-runtime-attestations-public"])

@router.get("/contract")
def private_contract(): return contract_document()

@public_router.get("/contract")
def public_contract(): return contract_document()

@router.get("/reference")
def reference(): return {"ok": True, "bundle": reference_signed_runtime_artifacts_execution_attestations_bundle().model_dump(mode="json")}

@router.post("/validate-manifest")
def validate_manifest(payload: RuntimeExecutionManifest): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}

@router.post("/validate-attestation")
def validate_attestation(payload: DetachedExecutionAttestation): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(payload: SignedRuntimeArtifactsExecutionAttestationsBundle): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
