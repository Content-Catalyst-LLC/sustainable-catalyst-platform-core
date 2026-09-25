import pytest
from pydantic import ValidationError
from app.services.computational_job_runtime import reference_julia_job
from app.services.julia_runtime_integration import *

def test_contract():
 d=contract_document(); assert d["release"]=="3.26.0"; assert d["registration"]["provider_version"]=="0.3.0"; assert d["boundaries"]["core_executes_julia_directly"] is False
def test_registration():
 r=reference_registration(); assert r.adapter_id==ADAPTER_ID; assert len(r.fingerprint())==64
def test_handshake_passes(): assert validate_handshake(reference_handshake()).ok is True
def test_bad_version():
 d=reference_handshake().model_dump(mode="python"); d["provider_version"]="0.2.0"; assert validate_handshake(JuliaRuntimeHandshake.model_validate(d)).ok is False
def test_missing_method():
 d=reference_handshake().model_dump(mode="python"); d["methods"]=d["methods"][:-1]; assert validate_handshake(JuliaRuntimeHandshake.model_validate(d)).ok is False
def test_map_job():
 r=job_to_julia_request(reference_julia_job()); assert r.operation=="matrix_multiply"; assert r.provenance["integration_contract"]==CONTRACT_VERSION
def test_wrong_adapter():
 j=reference_julia_job(); j.provider_binding.adapter_id="adapter:no"
 with pytest.raises(ValueError): job_to_julia_request(j)
def test_bad_operation():
 with pytest.raises(ValidationError): JuliaExecutionRequest(request_id="r",operation="eval")
def test_normalize_result():
 x=JuliaExecutionResponse.model_validate({"ok":True,"adapter_contract":"sc.core.runtime-adapter.v1","run":{"run_id":"run:1","request_id":"req:1","runtime_id":RUNTIME_ID,"state":"completed","environment_fingerprint_sha256":"b"*64},"result":{"result_id":"res:1","run_id":"run:1","request_id":"req:1","runtime_id":RUNTIME_ID,"state":"completed","environment_fingerprint_sha256":"b"*64,"scalar_result":10.0}}); y=normalize_julia_execution_response(x); assert y.scalar_result==10.0; assert y.provenance["normalized_by"]==CONTRACT_VERSION
def test_mismatch_response():
 with pytest.raises(ValidationError): JuliaExecutionResponse.model_validate({"ok":True,"adapter_contract":"sc.core.runtime-adapter.v1","run":{"run_id":"run:a","request_id":"req:a","runtime_id":RUNTIME_ID,"state":"completed"},"result":{"result_id":"res:a","run_id":"run:b","request_id":"req:a","runtime_id":RUNTIME_ID,"state":"completed"}})
def test_environment():
 s=JuliaEnvironmentSnapshot(runtime_version="1.13.0",environment_fingerprint_sha256="c"*64,dependencies=[{"name":"HTTP"}]); r=julia_environment_to_core(s); assert r.environment.runtime_id==RUNTIME_ID; assert r.reproducibility_status.value=="locked"
def test_security_boundary():
 d=reference_registration().model_dump(mode="python"); d["arbitrary_code_execution"]=True
 with pytest.raises(ValidationError): JuliaRuntimeRegistration.model_validate(d)
def test_all_methods_required():
 d=reference_registration().model_dump(mode="python"); d["required_methods"]=d["required_methods"][:-1]
 with pytest.raises(ValidationError): JuliaRuntimeRegistration.model_validate(d)
def test_provider_fingerprint_preserved():
 s=JuliaEnvironmentSnapshot(runtime_version="1.13.0",environment_fingerprint_sha256="f"*64); r=julia_environment_to_core(s); assert r.environment.metadata["observed_environment_fingerprint_sha256"]=="f"*64; assert len(r.fingerprint())==64
