from fastapi import APIRouter

from ..services.fortran_runtime import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    FortranExecutionRequest,
    FortranRuntimeBundle,
    contract_document,
    reference_environment_package,
    reference_runtime_bundle,
    reference_security_policy,
    to_scientific_fortran_artifact,
)

router = APIRouter(prefix="/api/v1/fortran-runtime", tags=["fortran-runtime"])
public_router = APIRouter(prefix="/public/v1/fortran-runtime", tags=["public-fortran-runtime"])

@router.get("/contract")
def get_contract(): return contract_document()

@public_router.get("/contract")
def get_public_contract(): return contract_document()

@router.get("/reference")
def get_reference():
    bundle=reference_runtime_bundle()
    return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
            "bundle":bundle.model_dump(mode="json",exclude_none=True),
            "bundle_fingerprint_sha256":bundle.fingerprint(),
            "registration_fingerprint_sha256":bundle.registration.fingerprint(),
            "environment_fingerprint_sha256":bundle.environment_package.fingerprint(),
            "security_policy_fingerprint_sha256":bundle.security_policy.fingerprint(),
            "request_fingerprint_sha256":bundle.reference_request.fingerprint()}

@router.get("/environment")
def get_environment():
    package=reference_environment_package()
    return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
            "environment_package":package.model_dump(mode="json",exclude_none=True),
            "environment_package_fingerprint_sha256":package.fingerprint()}

@router.get("/security-policy")
def get_security_policy():
    policy=reference_security_policy()
    return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
            "security_policy":policy.model_dump(mode="json",exclude_none=True),
            "security_policy_fingerprint_sha256":policy.fingerprint()}

@router.post("/validate-request")
def validate_request(body: FortranExecutionRequest):
    return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
            "request_fingerprint_sha256":body.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(body: FortranRuntimeBundle):
    return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
            "bundle_fingerprint_sha256":body.fingerprint()}

@router.post("/scientific-artifact")
def scientific_artifact(body: FortranRuntimeBundle):
    return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
            "scientific_artifact":to_scientific_fortran_artifact(body)}
