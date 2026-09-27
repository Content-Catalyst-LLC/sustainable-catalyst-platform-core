from fastapi import APIRouter, HTTPException

from ..services.jvm_language_profiles import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    JVMLanguageProfileResolutionRequest,
    contract_document,
    reference_catalog,
    resolve_profile,
    to_scientific_profile_artifact,
)

router = APIRouter(prefix="/api/v1/jvm-language-profiles", tags=["jvm-language-profiles"])
public_router = APIRouter(prefix="/public/v1/jvm-language-profiles", tags=["public-jvm-language-profiles"])


@public_router.get("/contract")
def public_contract():
    return contract_document()


@public_router.get("/profiles")
def public_profiles():
    catalog = reference_catalog()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "catalog": catalog.model_dump(mode="json", exclude_none=True),
        "catalog_fingerprint_sha256": catalog.fingerprint(),
    }


@router.get("/reference")
def reference():
    catalog = reference_catalog()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "catalog": catalog.model_dump(mode="json", exclude_none=True),
        "catalog_fingerprint_sha256": catalog.fingerprint(),
    }


@router.post("/resolve")
def resolve(body: JVMLanguageProfileResolutionRequest):
    try:
        resolution = resolve_profile(body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "resolution": resolution.model_dump(mode="json", exclude_none=True),
        "resolution_fingerprint_sha256": resolution.fingerprint(),
    }


@router.get("/scientific-artifact")
def scientific_artifact():
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "scientific_artifact": to_scientific_profile_artifact(),
    }
