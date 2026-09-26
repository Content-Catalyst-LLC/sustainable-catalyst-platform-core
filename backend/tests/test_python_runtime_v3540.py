from copy import deepcopy
import pytest
from pydantic import ValidationError
from app.services.python_runtime import *
def B():return reference_runtime_bundle()
def test_identity():assert RUNTIME_ID=='sc-runtime-python' and ADAPTER_ID=='adapter:sc-runtime-python' and CONTRACT_VERSION=='sc.core.python-runtime.v1'
def test_versions():assert PYTHON_VERSION=='3.12.3' and PYTHON_PACKAGE_CONSTRAINT=='3.12.3-*'
def test_operations():assert PYTHON_OPERATIONS==['descriptive_summary','linear_regression','matrix_multiply','standardize','bootstrap_mean_ci','token_frequency']
def test_summary():PythonExecutionRequest(python_request_id='p:x',operation='descriptive_summary',inputs=PythonInput(values=[1,2]),computational_job_ref='j:x')
def test_summary_empty():
    with pytest.raises(ValidationError):PythonExecutionRequest(python_request_id='p:x',operation='descriptive_summary',inputs=PythonInput(),computational_job_ref='j:x')
def test_regression():PythonExecutionRequest(python_request_id='p:x',operation='linear_regression',inputs=PythonInput(x=[1,2],y=[2,4]),computational_job_ref='j:x')
def test_regression_bad_len():
    with pytest.raises(ValidationError):PythonExecutionRequest(python_request_id='p:x',operation='linear_regression',inputs=PythonInput(x=[1,2],y=[2]),computational_job_ref='j:x')
def test_regression_zero_var():
    with pytest.raises(ValidationError):PythonExecutionRequest(python_request_id='p:x',operation='linear_regression',inputs=PythonInput(x=[1,1],y=[2,3]),computational_job_ref='j:x')
def test_matrix():PythonExecutionRequest(python_request_id='p:x',operation='matrix_multiply',inputs=PythonInput(matrix_a=[[1,2]],matrix_b=[[3],[4]]),computational_job_ref='j:x')
def test_matrix_bad():
    with pytest.raises(ValidationError):PythonExecutionRequest(python_request_id='p:x',operation='matrix_multiply',inputs=PythonInput(matrix_a=[[1,2]],matrix_b=[[1,2]]),computational_job_ref='j:x')
def test_standardize():PythonExecutionRequest(python_request_id='p:x',operation='standardize',inputs=PythonInput(values=[1,2,3]),computational_job_ref='j:x')
def test_standardize_bad():
    with pytest.raises(ValidationError):PythonExecutionRequest(python_request_id='p:x',operation='standardize',inputs=PythonInput(values=[1,1]),computational_job_ref='j:x')
def test_bootstrap():PythonExecutionRequest(python_request_id='p:x',operation='bootstrap_mean_ci',inputs=PythonInput(values=[1,2,3],iterations=100,seed=7),computational_job_ref='j:x')
def test_bootstrap_bad():
    with pytest.raises(ValidationError):PythonExecutionRequest(python_request_id='p:x',operation='bootstrap_mean_ci',inputs=PythonInput(values=[1,2],iterations=10),computational_job_ref='j:x')
def test_token():PythonExecutionRequest(python_request_id='p:x',operation='token_frequency',inputs=PythonInput(text='hello hello',top_k=5),computational_job_ref='j:x')
def test_token_empty():
    with pytest.raises(ValidationError):PythonExecutionRequest(python_request_id='p:x',operation='token_frequency',inputs=PythonInput(text=''),computational_job_ref='j:x')
def test_result_requires():
    with pytest.raises(ValidationError):PythonExecutionResultContract(result_contract_id='x:x',python_request_ref='p:x',operation='descriptive_summary')
def test_result_dup():
    with pytest.raises(ValidationError):PythonExecutionResultContract(result_contract_id='x:x',python_request_ref='p:x',operation='descriptive_summary',expected_artifact_kinds=['a','a'])
def test_result_fingerprint():c=B().result_contract;d=deepcopy(c);d.state=PythonExecutionState.completed;assert c.fingerprint()==d.fingerprint()
def test_registration():r=PythonRuntimeRegistration(registration_id='r:x');assert r.language=='python'
def test_registration_bad():
    with pytest.raises(ValidationError):PythonRuntimeRegistration(registration_id='r:x',runtime_id='bad')
def test_environment():e=reference_environment_package();p={x.name:x.version for x in e.system_packages};assert p['python3.12']==PYTHON_PACKAGE_CONSTRAINT and p['python3.12-venv']==PYTHON_PACKAGE_CONSTRAINT
def test_environment_meta():e=reference_environment_package();assert e.metadata['arbitrary_python_code'] is False and e.metadata['site_imports_disabled_for_jobs'] is True
def test_security():p=reference_security_policy();assert p.isolation_profile.network_mode=='none' and p.isolation_profile.shell_allowed is False
def test_security_meta():p=reference_security_policy();assert p.metadata['runtime_package_install_allowed'] is False and p.metadata['isolated_python_jobs'] is True
def test_bundle():assert B().reference_request.operation==PythonOperation.descriptive_summary and len(B().fingerprint())==64
def test_source_ref():assert 'go-runtime-bundle:reference:v1' in B().source_object_refs
def test_artifact():a=to_scientific_python_artifact(B());assert a['source_contract']==CONTRACT_VERSION and a['metadata']['runtime_id']==RUNTIME_ID
def test_registry_artifact():
    from app.services.scientific_result_registry import ScientificArtifactRef
    ScientificArtifactRef.model_validate(to_scientific_python_artifact(B()))
def test_contract():d=contract_document();assert d['release']=='3.54.0' and d['capabilities']['general_scientific'] is True and d['capabilities']['reproducible_randomness'] is True
@pytest.mark.parametrize('k',['core_executes_python_jobs','arbitrary_python_source','shell_execution','runtime_package_install_via_api','caller_filesystem_paths','network_access_for_jobs','core_selects_algorithm','core_certifies_numerical_validity','core_certifies_scientific_validity'])
def test_boundaries(k):assert contract_document()['boundaries'][k] is False
def test_request_fp():assert B().reference_request.fingerprint()==deepcopy(B().reference_request).fingerprint()
def test_env_fp():assert reference_environment_package().fingerprint()==deepcopy(reference_environment_package()).fingerprint()
def test_policy_fp():assert reference_security_policy().fingerprint()==deepcopy(reference_security_policy()).fingerprint()
def test_registration_fp():assert B().registration.fingerprint()==deepcopy(B().registration).fingerprint()
