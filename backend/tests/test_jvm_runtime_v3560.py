import pytest
from pydantic import ValidationError
from app.services.jvm_runtime import *

def test_identity(): assert CONTRACT_VERSION=='sc.core.jvm-runtime.v1' and RUNTIME_ID=='sc-runtime-jvm' and ADAPTER_ID=='adapter:sc-runtime-jvm'
def test_registration():
    r=JVMRuntimeRegistration(registration_id='reg:test');assert r.runtime_kind=='execution-target';assert r.language=='jvm-bytecode';assert r.jvm_major_version=='21'
def test_reference_bundle():
    b=reference_runtime_bundle();assert b.reference_request.operation==JVMOperation.parallel_sum;assert len(b.fingerprint())==64
def test_environment(): assert reference_runtime_bundle().environment_package.environment_package_id=='environment-package:jvm-runtime:v1'
def test_security():
    p=reference_security_policy();assert p.isolation_profile.arbitrary_code_allowed is False;assert p.isolation_profile.shell_allowed is False
def test_request():
    r=JVMExecutionRequest(jvm_request_id='req:test',operation=JVMOperation.parallel_sum,inputs=JVMInput(values=[1,2]),computational_job_ref='job:test');assert len(r.fingerprint())==64
def test_bad_graph():
    with pytest.raises(ValidationError): JVMExecutionRequest(jvm_request_id='req:test',operation=JVMOperation.graph_bfs,inputs=JVMInput(adjacency_matrix=[[0,2],[1,0]],source_index=0),computational_job_ref='job:test')
def test_contract():
    d=contract_document();assert d['release']=='3.56.0';assert d['capabilities']['managed_vm_execution'] is True;assert d['boundaries']['java_kotlin_scala_profiles_deferred_to']=='3.56.1'
def test_artifact():
    a=to_scientific_jvm_artifact(reference_runtime_bundle());assert a['source_contract']==CONTRACT_VERSION;assert len(a['content_sha256'])==64
