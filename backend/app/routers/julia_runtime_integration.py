from fastapi import APIRouter,HTTPException
from ..services.computational_job_runtime import ComputationalJob
from ..services.julia_runtime_integration import *
router=APIRouter(prefix="/api/v1/runtime-integrations/julia",tags=["runtime-integrations-julia"])
public_router=APIRouter(prefix="/public/v1/runtime-integrations/julia",tags=["public-runtime-integrations-julia"])
@router.get("/contract")
def get_contract(): return contract_document()
@public_router.get("/contract")
def get_public_contract(): return contract_document()
@router.get("/registration")
def registration():
 r=reference_registration(); return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"registration":r.model_dump(mode="json",exclude_none=True),"registration_fingerprint_sha256":r.fingerprint()}
@router.get("/reference-handshake")
def ref_handshake():
 h=reference_handshake(); return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"handshake":h.model_dump(mode="json",exclude_none=True),"validation":validate_handshake(h).model_dump(mode="json",exclude_none=True)}
@router.post("/validate-handshake")
def vhandshake(body:JuliaRuntimeHandshake): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"validation":validate_handshake(body).model_dump(mode="json",exclude_none=True)}
@router.post("/map-job")
def map_job(job:ComputationalJob):
 try: r=job_to_julia_request(job)
 except ValueError as e: raise HTTPException(status_code=409,detail=str(e)) from e
 return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"julia_execution_request":r.model_dump(mode="json",exclude_none=True)}
@router.post("/normalize-execution-response")
def norm(body:JuliaExecutionResponse): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"normalized":normalize_julia_execution_response(body).model_dump(mode="json",exclude_none=True)}
@router.post("/normalize-environment")
def nenv(body:JuliaEnvironmentSnapshot):
 r=julia_environment_to_core(body); return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"environment_provenance":r.model_dump(mode="json",exclude_none=True),"core_environment_fingerprint_sha256":r.fingerprint(),"provider_environment_fingerprint_sha256":body.environment_fingerprint_sha256}
