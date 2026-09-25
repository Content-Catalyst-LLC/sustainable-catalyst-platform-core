from fastapi import APIRouter

from ..services.runtime_data_interchange import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    DataInterchangeArtifact,
    DataInterchangeConversionSpec,
    DataInterchangeNegotiationRequest,
    DataInterchangeSchema,
    DataInterchangeTransfer,
    RuntimeDataInterchangeBundle,
    RuntimeInterchangeProfile,
    contract_document,
    negotiate_interchange,
    reference_runtime_data_interchange_bundle,
    to_scientific_artifact_payload,
)

router = APIRouter(
    prefix="/api/v1/runtime-data-interchange",
    tags=["runtime-data-interchange"],
)
public_router = APIRouter(
    prefix="/public/v1/runtime-data-interchange",
    tags=["public-runtime-data-interchange"],
)


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    bundle = reference_runtime_data_interchange_bundle()
    transfer = bundle.transfers[0]
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "source_artifact_fingerprint_sha256": transfer.source_artifact.fingerprint(),
        "target_artifact_fingerprint_sha256": transfer.target_artifact.fingerprint(),
        "transfer_fingerprint_sha256": transfer.fingerprint(),
    }


@router.post("/validate-schema")
def validate_schema(body: DataInterchangeSchema):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "schema_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-profile")
def validate_profile(body: RuntimeInterchangeProfile):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "profile_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-artifact")
def validate_artifact(body: DataInterchangeArtifact):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "artifact_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/negotiate")
def negotiate(body: DataInterchangeNegotiationRequest):
    result = negotiate_interchange(body)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "negotiation": result.model_dump(mode="json", exclude_none=True),
        "negotiation_fingerprint_sha256": result.fingerprint(),
    }


@router.post("/validate-conversion")
def validate_conversion(body: DataInterchangeConversionSpec):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "conversion_spec_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-transfer")
def validate_transfer(body: DataInterchangeTransfer):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "transfer_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-bundle")
def validate_bundle(body: RuntimeDataInterchangeBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/scientific-artifact")
def scientific_artifact(body: DataInterchangeArtifact):
    payload = to_scientific_artifact_payload(body)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "scientific_artifact": payload,
    }
