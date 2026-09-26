from fastapi import APIRouter

from ..services.unified_runtime_api import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    ProductRuntimeIntegrationProfile,
    ProductRuntimeReceipt,
    UnifiedRuntimeAPIBundle,
    UnifiedRuntimeCatalog,
    UnifiedRuntimeInvocation,
    UnifiedRuntimeRequest,
    build_invocation,
    contract_document,
    reference_product_profiles,
    reference_runtime_catalog,
    reference_unified_runtime_api_bundle,
    resolve_runtime_request,
    to_scientific_unified_runtime_artifact,
)

router = APIRouter(prefix="/api/v1/unified-runtime", tags=["unified-runtime"])
public_router = APIRouter(prefix="/public/v1/unified-runtime", tags=["public-unified-runtime"])


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/catalog")
def get_catalog():
    catalog = reference_runtime_catalog()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "catalog": catalog.model_dump(mode="json", exclude_none=True),
        "catalog_fingerprint_sha256": catalog.fingerprint(),
    }


@router.get("/product-profiles")
def get_product_profiles():
    profiles = reference_product_profiles()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "profiles": [item.model_dump(mode="json", exclude_none=True) for item in profiles],
        "profile_fingerprints": {item.product_profile_id: item.fingerprint() for item in profiles},
    }


@router.get("/reference")
def get_reference():
    bundle = reference_unified_runtime_api_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "catalog_fingerprint_sha256": bundle.catalog.fingerprint(),
        "request_fingerprint_sha256": bundle.request.fingerprint(),
        "resolution_fingerprint_sha256": bundle.resolution.fingerprint(),
        "invocation_fingerprint_sha256": bundle.invocation.fingerprint() if bundle.invocation else None,
    }


@router.post("/resolve")
def resolve(body: dict):
    catalog = UnifiedRuntimeCatalog.model_validate(body["catalog"])
    profile = ProductRuntimeIntegrationProfile.model_validate(body["profile"])
    request = UnifiedRuntimeRequest.model_validate(body["request"])
    result = resolve_runtime_request(
        catalog=catalog,
        profile=profile,
        request=request,
        resolution_id=body.get("resolution_id"),
    )
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "resolution": result.model_dump(mode="json", exclude_none=True),
        "resolution_fingerprint_sha256": result.fingerprint(),
    }


@router.post("/build-invocation")
def invocation(body: dict):
    catalog = UnifiedRuntimeCatalog.model_validate(body["catalog"])
    profile = ProductRuntimeIntegrationProfile.model_validate(body["profile"])
    request = UnifiedRuntimeRequest.model_validate(body["request"])
    from ..services.unified_runtime_api import UnifiedRuntimeResolution
    resolution = UnifiedRuntimeResolution.model_validate(body["resolution"])
    result = build_invocation(
        request=request,
        resolution=resolution,
        profile=profile,
        catalog=catalog,
        security_decision_ref=str(body["security_decision_ref"]),
        invocation_id=body.get("invocation_id"),
    )
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "invocation": result.model_dump(mode="json", exclude_none=True),
        "invocation_fingerprint_sha256": result.fingerprint(),
    }


@router.post("/validate-invocation")
def validate_invocation(body: UnifiedRuntimeInvocation):
    return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "invocation_fingerprint_sha256": body.fingerprint()}


@router.post("/validate-receipt")
def validate_receipt(body: ProductRuntimeReceipt):
    return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "receipt_fingerprint_sha256": body.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(body: UnifiedRuntimeAPIBundle):
    return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "bundle_fingerprint_sha256": body.fingerprint()}


@router.post("/scientific-artifact")
def scientific_artifact(body: UnifiedRuntimeAPIBundle):
    payload = to_scientific_unified_runtime_artifact(body)
    return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "scientific_artifact": payload}
