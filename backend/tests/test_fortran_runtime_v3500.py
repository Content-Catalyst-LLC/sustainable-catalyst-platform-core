from copy import deepcopy
import pytest
from pydantic import ValidationError

from app.services.fortran_runtime import (
 ADAPTER_ID,CONTRACT_VERSION,FORTRAN_OPERATIONS,GFORTRAN_PACKAGE_VERSION,GFORTRAN_VERSION,PROVIDER_VERSION,RUNTIME_ID,
 FortranExecutionRequest,FortranExecutionResultContract,FortranExecutionSettings,FortranExecutionState,FortranNumericInput,FortranOperation,FortranRuntimeBundle,FortranRuntimeRegistration,
 contract_document,reference_environment_package,reference_runtime_bundle,reference_security_policy,to_scientific_fortran_artifact,
)

def ref(): return reference_runtime_bundle()

def test_contract_identity():
 d=contract_document(); assert d['release']=='3.50.0'; assert d['contract']==CONTRACT_VERSION

def test_runtime_identity():
 assert RUNTIME_ID=='sc-runtime-fortran'; assert ADAPTER_ID=='adapter:sc-runtime-fortran'; assert PROVIDER_VERSION=='1.0.0'; assert GFORTRAN_VERSION=='13.3.0'; assert GFORTRAN_PACKAGE_VERSION=='13.3.0-6ubuntu2~24.04.1'

def test_operations(): assert FORTRAN_OPERATIONS==['dot_product','matrix_multiply','trapezoidal_integral','central_difference','rk4_linear_step','heat_step_1d']

def req(op,inputs): return FortranExecutionRequest(fortran_request_id='request:test',operation=op,inputs=inputs,computational_job_ref='job:test')

def test_dot_valid(): assert req(FortranOperation.dot_product,FortranNumericInput(vector_a=[1,2],vector_b=[3,4])).operation==FortranOperation.dot_product

def test_dot_mismatch():
 with pytest.raises(ValidationError): req(FortranOperation.dot_product,FortranNumericInput(vector_a=[1],vector_b=[2,3]))

def test_matrix_valid(): req(FortranOperation.matrix_multiply,FortranNumericInput(matrix_a=[[1,2]],matrix_b=[[3],[4]]))
def test_matrix_mismatch():
 with pytest.raises(ValidationError): req(FortranOperation.matrix_multiply,FortranNumericInput(matrix_a=[[1,2]],matrix_b=[[3,4]]))
def test_trapezoid_valid(): req(FortranOperation.trapezoidal_integral,FortranNumericInput(x=[0,1,2],y=[0,1,4]))
def test_trapezoid_increasing():
 with pytest.raises(ValidationError): req(FortranOperation.trapezoidal_integral,FortranNumericInput(x=[0,0,1],y=[0,1,2]))
def test_central_valid(): req(FortranOperation.central_difference,FortranNumericInput(x=[0,1,2],y=[0,1,4],index=1))
def test_central_boundary():
 with pytest.raises(ValidationError): req(FortranOperation.central_difference,FortranNumericInput(x=[0,1,2],y=[0,1,4],index=0))
def test_rk4_valid(): req(FortranOperation.rk4_linear_step,FortranNumericInput(scalar_y=1,step_size=.1,coefficient_a=2,coefficient_b=0))
def test_rk4_missing():
 with pytest.raises(ValidationError): req(FortranOperation.rk4_linear_step,FortranNumericInput(scalar_y=1,step_size=.1,coefficient_a=2))
def test_heat_valid(): req(FortranOperation.heat_step_1d,FortranNumericInput(vector_a=[0,1,0],alpha_dt_dx2=.25))
def test_heat_bound():
 with pytest.raises(ValidationError): req(FortranOperation.heat_step_1d,FortranNumericInput(vector_a=[0,1,0],alpha_dt_dx2=.6))
def test_settings_defaults(): assert FortranExecutionSettings().optimization_level==2
def test_settings_bound():
 with pytest.raises(ValidationError): FortranExecutionSettings(optimization_level=3)
def test_input_fingerprint():
 i=FortranNumericInput(vector_a=[1,2]); assert i.fingerprint()==deepcopy(i).fingerprint()
def test_request_defaults():
 r=ref().reference_request; assert r.environment_package_ref=='environment-package:fortran-runtime:v1'; assert r.security_policy_ref=='runtime-security-policy:fortran-runtime-standard:v1'
def test_request_fingerprint(): assert ref().reference_request.fingerprint()==deepcopy(ref().reference_request).fingerprint()
def test_result_requires_output():
 with pytest.raises(ValidationError): FortranExecutionResultContract(result_contract_id='result:test',fortran_request_ref='request:test',operation=FortranOperation.dot_product)
def test_result_duplicate():
 with pytest.raises(ValidationError): FortranExecutionResultContract(result_contract_id='result:test',fortran_request_ref='request:test',operation=FortranOperation.dot_product,expected_artifact_kinds=['x','x'])
def test_result_state_ignored():
 c=ref().result_contract; other=deepcopy(c); other.state=FortranExecutionState.completed; assert c.fingerprint()==other.fingerprint()
def test_registration():
 r=FortranRuntimeRegistration(registration_id='registration:test'); assert r.runtime_id==RUNTIME_ID; assert r.runtime_kind=='language'; assert r.language=='fortran'
def test_registration_wrong_runtime():
 with pytest.raises(ValidationError): FortranRuntimeRegistration(registration_id='registration:test',runtime_id='wrong')
def test_registration_ops():
 with pytest.raises(ValidationError): FortranRuntimeRegistration(registration_id='registration:test',operations=['dot_product'])
def test_environment_identity(): assert reference_environment_package().environment_package_id=='environment-package:fortran-runtime:v1'
def test_environment_runtime():
 e=reference_environment_package(); assert e.runtimes[0].runtime_ref==RUNTIME_ID; assert e.runtimes[0].runtime_adapter_ref==ADAPTER_ID
def test_environment_package_pin():
 e=reference_environment_package(); p={x.name:x.version for x in e.system_packages}; assert p['gfortran-13']==GFORTRAN_PACKAGE_VERSION
def test_environment_paths():
 e=reference_environment_package(); v={x.name:x.value for x in e.environment_variables}; assert v['SC_FORTRAN_ARTIFACT_ROOT']=='/var/lib/sc-fortran-runtime/artifacts'; assert v['SC_FORTRAN_WORK_ROOT']=='/var/lib/sc-fortran-runtime/work'
def test_environment_steps(): assert [x.ordinal for x in reference_environment_package().build_instructions]==[1,2,3]
def test_security_identity(): assert reference_security_policy().security_policy_id=='runtime-security-policy:fortran-runtime-standard:v1'
def test_security_runtime_scope():
 p=reference_security_policy(); assert p.allowed_runtime_refs==[RUNTIME_ID]; assert p.allowed_adapter_refs==[ADAPTER_ID]
def test_security_ops(): assert reference_security_policy().allowed_operations[RUNTIME_ID]==FORTRAN_OPERATIONS
def test_security_network(): assert reference_security_policy().isolation_profile.network_mode=='none'
def test_security_install(): assert reference_security_policy().isolation_profile.package_install_mode=='denied'
def test_security_shell(): assert reference_security_policy().isolation_profile.shell_allowed is False
def test_security_arbitrary(): assert reference_security_policy().isolation_profile.arbitrary_code_allowed is False
def test_security_metadata():
 p=reference_security_policy(); assert p.metadata['arbitrary_fortran_source_allowed'] is False; assert p.metadata['compiler_invocation_provider_managed'] is True
def test_reference_bundle():
 b=ref(); assert b.registration.runtime_id==RUNTIME_ID; assert b.reference_request.operation==FortranOperation.dot_product
def test_reference_vectors():
 i=ref().reference_request.inputs; assert i.vector_a==[1.0,2.0,3.0]; assert i.vector_b==[4.0,5.0,6.0]
def test_reference_result_contract():
 c=ref().result_contract; assert 'fortran-generated-source' in c.expected_artifact_kinds; assert 'scientific-numeric-result' in c.expected_result_kinds
def test_bundle_env_mismatch():
 d=ref().model_dump(mode='python'); d['reference_request']['environment_package_ref']='wrong';
 with pytest.raises(ValidationError): FortranRuntimeBundle.model_validate(d)
def test_bundle_security_mismatch():
 d=ref().model_dump(mode='python'); d['reference_request']['security_policy_ref']='wrong';
 with pytest.raises(ValidationError): FortranRuntimeBundle.model_validate(d)
def test_bundle_request_mismatch():
 d=ref().model_dump(mode='python'); d['result_contract']['fortran_request_ref']='wrong';
 with pytest.raises(ValidationError): FortranRuntimeBundle.model_validate(d)
def test_bundle_operation_mismatch():
 d=ref().model_dump(mode='python'); d['result_contract']['operation']='heat_step_1d';
 with pytest.raises(ValidationError): FortranRuntimeBundle.model_validate(d)
def test_bundle_fingerprint(): assert len(ref().fingerprint())==64 and ref().fingerprint()==deepcopy(ref()).fingerprint()
def test_scientific_artifact():
 a=to_scientific_fortran_artifact(ref()); assert a['artifact_kind']=='package'; assert a['source_contract']==CONTRACT_VERSION; assert a['content_sha256']==ref().fingerprint()
def test_scientific_registry_validation():
 from app.services.scientific_result_registry import ScientificArtifactRef
 assert ScientificArtifactRef.model_validate(to_scientific_fortran_artifact(ref())).source_object_ref==ref().bundle_id
def test_capabilities():
 c=contract_document()['capabilities']; assert c['scientific_hpc'] is True; assert c['numerical_compute'] is True; assert c['differential_equation_methods'] is True; assert c['provider_managed_compilation'] is True
def test_product_integration():
 c=contract_document()['capabilities']; assert c['workspace_product_profile_integration'] and c['research_lab_product_profile_integration'] and c['workbench_product_profile_integration']
def test_boundaries():
 b=contract_document()['boundaries']; assert b['core_executes_fortran'] is False; assert b['provider_compiles_and_executes_fortran'] is True; assert b['arbitrary_fortran_source'] is False; assert b['shell_execution'] is False; assert b['core_selects_numerical_method'] is False; assert b['core_certifies_numerical_validity'] is False; assert b['core_certifies_scientific_validity'] is False
def test_reference_hash(): assert len(contract_document()['reference']['bundle_fingerprint_sha256'])==64
