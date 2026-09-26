from copy import deepcopy
import pytest
from pydantic import ValidationError
from app.services.go_runtime import *
def B():return reference_runtime_bundle()
def test_identity():assert RUNTIME_ID=='sc-runtime-go' and ADAPTER_ID=='adapter:sc-runtime-go' and CONTRACT_VERSION=='sc.core.go-runtime.v1'
def test_versions():assert GO_VERSION=='1.22.2' and GO_PACKAGE_VERSION=='1.22.2-2ubuntu0.4'
def test_operations():assert GO_OPERATIONS==['parallel_sum','parallel_map_affine','concurrent_histogram','parallel_matrix_row_sums','parallel_graph_degrees','batch_sha256']
def test_sum():GoExecutionRequest(go_request_id='g:x',operation='parallel_sum',inputs=GoInput(values=[1,2]),computational_job_ref='j:x')
def test_empty_sum():
    with pytest.raises(ValidationError):GoExecutionRequest(go_request_id='g:x',operation='parallel_sum',inputs=GoInput(),computational_job_ref='j:x')
def test_affine():GoExecutionRequest(go_request_id='g:x',operation='parallel_map_affine',inputs=GoInput(values=[1],scale=2,offset=1),computational_job_ref='j:x')
def test_hist():GoExecutionRequest(go_request_id='g:x',operation='concurrent_histogram',inputs=GoInput(values=[1,2],bins=2,minimum=0,maximum=2),computational_job_ref='j:x')
def test_hist_bad():
    with pytest.raises(ValidationError):GoExecutionRequest(go_request_id='g:x',operation='concurrent_histogram',inputs=GoInput(values=[1],bins=0,minimum=0,maximum=1),computational_job_ref='j:x')
def test_matrix():GoExecutionRequest(go_request_id='g:x',operation='parallel_matrix_row_sums',inputs=GoInput(matrix=[[1,2],[3,4]]),computational_job_ref='j:x')
def test_graph():GoExecutionRequest(go_request_id='g:x',operation='parallel_graph_degrees',inputs=GoInput(adjacency_matrix=[[0,1],[1,0]]),computational_job_ref='j:x')
def test_hash():GoExecutionRequest(go_request_id='g:x',operation='batch_sha256',inputs=GoInput(texts=['abc']),computational_job_ref='j:x')
def test_workers_bad():
    with pytest.raises(ValidationError):GoExecutionRequest(go_request_id='g:x',operation='parallel_sum',inputs=GoInput(values=[1],workers=65),computational_job_ref='j:x')
def test_result_requires():
    with pytest.raises(ValidationError):GoExecutionResultContract(result_contract_id='x:x',go_request_ref='g:x',operation='parallel_sum')
def test_result_dup():
    with pytest.raises(ValidationError):GoExecutionResultContract(result_contract_id='x:x',go_request_ref='g:x',operation='parallel_sum',expected_artifact_kinds=['a','a'])
def test_result_fingerprint():c=B().result_contract;d=deepcopy(c);d.state=GoExecutionState.completed;assert c.fingerprint()==d.fingerprint()
def test_registration():r=GoRuntimeRegistration(registration_id='r:x');assert r.language=='go'
def test_registration_bad():
    with pytest.raises(ValidationError):GoRuntimeRegistration(registration_id='r:x',runtime_id='bad')
def test_environment():e=reference_environment_package();p={x.name:x.version for x in e.system_packages};assert p['golang-1.22-go']==GO_PACKAGE_VERSION
def test_environment_meta():e=reference_environment_package();assert e.metadata['external_module_downloads'] is False and e.metadata['cgo_enabled'] is False
def test_security():p=reference_security_policy();assert p.isolation_profile.network_mode=='none' and p.isolation_profile.shell_allowed is False
def test_security_meta():p=reference_security_policy();assert p.metadata['go_module_download_allowed'] is False
def test_bundle():assert B().reference_request.operation==GoOperation.parallel_sum and len(B().fingerprint())==64
def test_source_ref():assert 'rust-runtime-bundle:reference:v1' in B().source_object_refs
def test_artifact():a=to_scientific_go_artifact(B());assert a['source_contract']==CONTRACT_VERSION and a['metadata']['runtime_id']==RUNTIME_ID
def test_registry_artifact():
    from app.services.scientific_result_registry import ScientificArtifactRef
    ScientificArtifactRef.model_validate(to_scientific_go_artifact(B()))
def test_contract():d=contract_document();assert d['release']=='3.53.0' and d['capabilities']['concurrent_distributed'] is True
@pytest.mark.parametrize('k',['core_executes_go','arbitrary_go_source','shell_execution','go_module_download_via_api','runtime_package_install_via_api','caller_filesystem_paths','core_selects_algorithm','core_certifies_numerical_validity','core_certifies_scientific_validity'])
def test_boundaries(k):assert contract_document()['boundaries'][k] is False
def test_request_fp():assert B().reference_request.fingerprint()==deepcopy(B().reference_request).fingerprint()
def test_env_fp():assert reference_environment_package().fingerprint()==deepcopy(reference_environment_package()).fingerprint()
def test_policy_fp():assert reference_security_policy().fingerprint()==deepcopy(reference_security_policy()).fingerprint()
def test_registration_fp():assert B().registration.fingerprint()==deepcopy(B().registration).fingerprint()
