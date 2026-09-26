from copy import deepcopy
import pytest
from pydantic import ValidationError
from app.services.c_cpp_runtime import *
def B():return reference_runtime_bundle()
def test_identity():assert RUNTIME_ID=="sc-runtime-cpp" and ADAPTER_ID=="adapter:sc-runtime-cpp"
def test_versions():assert GCC_VERSION=="13.3.0" and GPP_VERSION=="13.3.0"
def test_ops():assert len(CPP_OPERATIONS)==6
def test_dot():CCppExecutionRequest(cpp_request_id="r:x",operation="dot_product",inputs=CCppNumericInput(vector_a=[1,2],vector_b=[3,4]),computational_job_ref="j:x")
def test_dot_bad():
 with pytest.raises(ValidationError):CCppExecutionRequest(cpp_request_id="r:x",operation="dot_product",inputs=CCppNumericInput(vector_a=[1],vector_b=[2,3]),computational_job_ref="j:x")
def test_matrix():CCppExecutionRequest(cpp_request_id="r:x",operation="matrix_multiply",inputs=CCppNumericInput(matrix_a=[[1,2]],matrix_b=[[3],[4]]),computational_job_ref="j:x")
def test_interp():CCppExecutionRequest(cpp_request_id="r:x",operation="linear_interpolation",inputs=CCppNumericInput(x=[0,1],y=[0,2],query_x=.5),computational_job_ref="j:x")
def test_poly():CCppExecutionRequest(cpp_request_id="r:x",operation="polynomial_evaluate",inputs=CCppNumericInput(coefficients=[1,2],scalar_x=3),computational_job_ref="j:x")
def test_fir():CCppExecutionRequest(cpp_request_id="r:x",operation="fir_filter",inputs=CCppNumericInput(signal=[1,2],kernel=[.5]),computational_job_ref="j:x")
def test_graph():CCppExecutionRequest(cpp_request_id="r:x",operation="dijkstra_shortest_path",inputs=CCppNumericInput(adjacency_matrix=[[0,1],[1,0]],source_index=0,target_index=1),computational_job_ref="j:x")
def test_result_requires():
 with pytest.raises(ValidationError):CCppExecutionResultContract(result_contract_id="x:x",cpp_request_ref="r:x",operation="dot_product")
def test_registration():assert CCppRuntimeRegistration(registration_id="r:x").language_profiles==["c11","cpp17"]
def test_env():
 e=reference_environment_package();p={x.name:x.version for x in e.system_packages};assert p["gcc-13"]==GCC_PACKAGE_VERSION and p["g++-13"]==GPP_PACKAGE_VERSION
def test_security():
 p=reference_security_policy();assert p.isolation_profile.network_mode=="none" and p.isolation_profile.shell_allowed is False and p.isolation_profile.arbitrary_code_allowed is False
def test_bundle():assert B().reference_request.operation==CCppOperation.dot_product and len(B().fingerprint())==64
def test_artifact():assert to_scientific_cpp_artifact(B())["source_contract"]==CONTRACT_VERSION
def test_registry_artifact():
 from app.services.scientific_result_registry import ScientificArtifactRef
 ScientificArtifactRef.model_validate(to_scientific_cpp_artifact(B()))
def test_contract():
 d=contract_document();assert d["release"]=="3.51.0" and d["capabilities"]["native_engineering"] is True
@pytest.mark.parametrize("k",["core_executes_c_cpp","arbitrary_c_cpp_source","shell_execution","runtime_package_install_via_api","caller_filesystem_paths","core_selects_algorithm","core_certifies_numerical_validity","core_certifies_scientific_validity"])
def test_false(k):assert contract_document()["boundaries"][k] is False
@pytest.mark.parametrize("op",CPP_OPERATIONS)
def test_language(op):assert OPERATION_LANGUAGE[op] in {"c11","cpp17"}
def test_request_fp():assert B().reference_request.fingerprint()==deepcopy(B().reference_request).fingerprint()
def test_env_fp():assert reference_environment_package().fingerprint()==deepcopy(reference_environment_package()).fingerprint()
def test_policy_fp():assert reference_security_policy().fingerprint()==deepcopy(reference_security_policy()).fingerprint()
def test_reg_fp():assert B().registration.fingerprint()==deepcopy(B().registration).fingerprint()
def test_source_ref():assert "fortran-runtime-bundle:reference:v1" in B().source_object_refs
