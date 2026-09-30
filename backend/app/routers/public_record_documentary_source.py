from fastapi import APIRouter

from app.services.public_record_documentary_source import (
    DocumentaryEvidenceInterpretation,
    DocumentarySourceDescriptor,
    PublicRecordDocumentarySourceBundle,
    contract_document,
    reference_public_record_documentary_source_bundle,
)

router = APIRouter(prefix="/v1/documentary-sources", tags=["documentary-sources"])
public_router = APIRouter(prefix="/public/v1/documentary-sources", tags=["documentary-sources-public"])


@router.get("/contract")
def private_contract():
    return contract_document()


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/reference")
def reference():
    return {"ok": True, "bundle": reference_public_record_documentary_source_bundle().model_dump(mode="json")}


@router.post("/validate-source")
def validate_source(payload: DocumentarySourceDescriptor):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-interpretation")
def validate_interpretation(payload: DocumentaryEvidenceInterpretation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: PublicRecordDocumentarySourceBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
