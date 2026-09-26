from fastapi import APIRouter
from ..services.c_cpp_runtime import CONTRACT_VERSION,CORE_RELEASE,CCppExecutionRequest,CCppRuntimeBundle,contract_document,reference_environment_package,reference_runtime_bundle,reference_security_policy,to_scientific_cpp_artifact
router=APIRouter(prefix="/api/v1/c-cpp-runtime",tags=["c-cpp-runtime"]);public_router=APIRouter(prefix="/public/v1/c-cpp-runtime",tags=["public-c-cpp-runtime"])
@router.get("/contract")
def get_contract(): return contract_document()
@public_router.get("/contract")
def get_public_contract(): return contract_document()
@router.get("/reference")
def get_reference():
 b=reference_runtime_bundle();return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle":b.model_dump(mode="json",exclude_none=True),"bundle_fingerprint_sha256":b.fingerprint(),"registration_fingerprint_sha256":b.registration.fingerprint(),"environment_fingerprint_sha256":b.environment_package.fingerprint(),"security_policy_fingerprint_sha256":b.security_policy.fingerprint(),"request_fingerprint_sha256":b.reference_request.fingerprint()}
@router.get("/environment")
def get_environment():
 p=reference_environment_package();return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"environment_package":p.model_dump(mode="json",exclude_none=True),"environment_package_fingerprint_sha256":p.fingerprint()}
@router.get("/security-policy")
def get_security_policy():
 p=reference_security_policy();return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"security_policy":p.model_dump(mode="json",exclude_none=True),"security_policy_fingerprint_sha256":p.fingerprint()}
@router.post("/validate-request")
def validate_request(body:CCppExecutionRequest): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"request_fingerprint_sha256":body.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(body:CCppRuntimeBundle): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle_fingerprint_sha256":body.fingerprint()}
@router.post("/scientific-artifact")
def scientific_artifact(body:CCppRuntimeBundle): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"scientific_artifact":to_scientific_cpp_artifact(body)}
