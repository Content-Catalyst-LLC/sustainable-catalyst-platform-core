from fastapi import APIRouter

from ..services.ml_model_registry_packages import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    MLIntendedUseStatement,
    MLModelArtifactRecord,
    MLModelLimitationRecord,
    MLModelRegistryEntry,
    MLModelRegistryPackageBundle,
    MLReproducibilityManifest,
    MLReproducibleModelPackage,
    MLRuntimeRequirementRecord,
    contract_document,
    reference_model_registry_package_bundle,
)

router = APIRouter(prefix="/api/v1/ml-model-registry", tags=["ml-model-registry"])
public_router = APIRouter(prefix="/public/v1/ml-model-registry", tags=["public-ml-model-registry"])


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    bundle = reference_model_registry_package_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
    }


@router.post("/validate-artifact")
def validate_artifact(body: MLModelArtifactRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-runtime-requirement")
def validate_runtime_requirement(body: MLRuntimeRequirementRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-intended-use")
def validate_intended_use(body: MLIntendedUseStatement):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-limitation")
def validate_limitation(body: MLModelLimitationRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-registry-entry")
def validate_registry_entry(body: MLModelRegistryEntry):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-manifest")
def validate_manifest(body: MLReproducibilityManifest):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-model-package")
def validate_model_package(body: MLReproducibleModelPackage):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(body: MLModelRegistryPackageBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }
