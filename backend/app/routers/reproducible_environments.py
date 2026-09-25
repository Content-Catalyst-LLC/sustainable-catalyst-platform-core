from fastapi import APIRouter

from ..services.reproducible_environment_packages import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    EnvironmentReproductionVerification,
    EnvironmentReproductionRequest,
    PlatformDescriptor,
    ReproducibleEnvironmentPackage,
    ReproducibleEnvironmentPackageBundle,
    contract_document,
    evaluate_platform_compatibility,
    reference_environment_package_bundle,
    to_scientific_environment_artifact,
)

router = APIRouter(
    prefix="/api/v1/reproducible-environments",
    tags=["reproducible-environments"],
)
public_router = APIRouter(
    prefix="/public/v1/reproducible-environments",
    tags=["public-reproducible-environments"],
)


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    bundle = reference_environment_package_bundle()
    package = bundle.packages[0]
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "environment_package_fingerprint_sha256": package.fingerprint(),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
    }


@router.post("/validate-package")
def validate_package(body: ReproducibleEnvironmentPackage):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "environment_package_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/compatibility")
def compatibility(body: dict):
    package = ReproducibleEnvironmentPackage.model_validate(body["package"])
    target = PlatformDescriptor.model_validate(body["target_platform"])
    report = evaluate_platform_compatibility(package, target)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "compatibility_report": report.model_dump(mode="json", exclude_none=True),
        "compatibility_report_fingerprint_sha256": report.fingerprint(),
    }


@router.post("/validate-reproduction-request")
def validate_reproduction_request(body: EnvironmentReproductionRequest):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "reproduction_request_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-verification")
def validate_verification(body: EnvironmentReproductionVerification):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "verification_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-bundle")
def validate_bundle(body: ReproducibleEnvironmentPackageBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/scientific-artifact")
def scientific_artifact(body: ReproducibleEnvironmentPackage):
    payload = to_scientific_environment_artifact(body)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "scientific_artifact": payload,
    }
