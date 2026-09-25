from fastapi import APIRouter

from ..services.scientific_result_registry import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    ScientificRegistryPackage,
    ScientificRegistryQuery,
    ScientificResultArtifactRegistry,
    contract_document,
    query_registry,
    reference_scientific_registry_package,
    register_statistical_analysis_package,
)

router = APIRouter(
    prefix="/api/v1/scientific-registry",
    tags=["scientific-registry"],
)
public_router = APIRouter(
    prefix="/public/v1/scientific-registry",
    tags=["public-scientific-registry"],
)


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    package = reference_scientific_registry_package()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "package": package.model_dump(mode="json", exclude_none=True),
        "registry_fingerprint_sha256": package.registry.fingerprint(),
        "snapshot_fingerprint_sha256": package.snapshot.fingerprint(),
        "package_fingerprint_sha256": package.fingerprint(),
    }


@router.post("/validate-registry")
def validate_registry(body: ScientificResultArtifactRegistry):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "registry_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-package")
def validate_package(body: ScientificRegistryPackage):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "package_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/query-reference")
def query_reference(body: ScientificRegistryQuery):
    package = reference_scientific_registry_package()
    result = query_registry(package.registry, body)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "query_result": result.model_dump(mode="json", exclude_none=True),
        "query_result_fingerprint_sha256": result.fingerprint(),
    }


@router.post("/register-statistical-package")
def register_statistical_package(body: dict):
    registry = register_statistical_analysis_package(
        analysis_package=body,
    )
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "registry": registry.model_dump(mode="json", exclude_none=True),
        "registry_fingerprint_sha256": registry.fingerprint(),
    }
