from fastapi import APIRouter
from ..services.python_runtime import (
    CONTRACT_VERSION, CORE_RELEASE, PythonExecutionRequest, PythonRuntimeBundle,
    contract_document, reference_environment_package, reference_runtime_bundle,
    reference_security_policy, to_scientific_python_artifact,
)
router=APIRouter(prefix="/api/v1/python-runtime",tags=["python-runtime"])
public_router=APIRouter(prefix="/public/v1/python-runtime",tags=["public-python-runtime"])
@router.get("/contract")
def get_contract(): return contract_document()
@public_router.get("/contract")
def get_public_contract(): return contract_document()
@router.get("/reference")
def get_reference():
    b=reference_runtime_bundle(); return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle":b.model_dump(mode="json",exclude_none=True),"bundle_fingerprint_sha256":b.fingerprint()}
@router.get("/environment")
def get_environment():
    e=reference_environment_package(); return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"environment_package":e.model_dump(mode="json",exclude_none=True),"environment_package_fingerprint_sha256":e.fingerprint()}
@router.get("/security-policy")
def get_security_policy():
    p=reference_security_policy(); return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"security_policy":p.model_dump(mode="json",exclude_none=True),"security_policy_fingerprint_sha256":p.fingerprint()}
@router.post("/validate-request")
def validate_request(body:PythonExecutionRequest): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"request_fingerprint_sha256":body.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(body:PythonRuntimeBundle): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle_fingerprint_sha256":body.fingerprint()}
@router.post("/scientific-artifact")
def scientific_artifact(body:PythonRuntimeBundle): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"scientific_artifact":to_scientific_python_artifact(body)}
