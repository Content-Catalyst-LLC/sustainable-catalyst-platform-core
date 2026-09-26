from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.rust_runtime import *


def B():
    return reference_runtime_bundle()


def test_identity():
    assert RUNTIME_ID == "sc-runtime-rust"
    assert ADAPTER_ID == "adapter:sc-runtime-rust"
    assert CONTRACT_VERSION == "sc.core.rust-runtime.v1"


def test_versions():
    assert RUSTC_VERSION == "1.75.0"
    assert CARGO_VERSION == "1.75.0"
    assert RUST_PACKAGE_VERSION == "1.75.0+dfsg0ubuntu1-0ubuntu7.4"


def test_operations():
    assert RUST_OPERATIONS == ["prefix_sum","moving_average","connected_components","topological_sort","levenshtein_distance","fnv1a_64"]


def test_prefix_request():
    RustExecutionRequest(rust_request_id="r:x",operation="prefix_sum",inputs=RustInput(integers=[1,2,3]),computational_job_ref="j:x")


def test_prefix_empty():
    with pytest.raises(ValidationError):
        RustExecutionRequest(rust_request_id="r:x",operation="prefix_sum",inputs=RustInput(),computational_job_ref="j:x")


def test_moving_average_request():
    RustExecutionRequest(rust_request_id="r:x",operation="moving_average",inputs=RustInput(values=[1,2,3],window=2),computational_job_ref="j:x")


def test_moving_average_window():
    with pytest.raises(ValidationError):
        RustExecutionRequest(rust_request_id="r:x",operation="moving_average",inputs=RustInput(values=[1,2],window=3),computational_job_ref="j:x")


def test_components_request():
    RustExecutionRequest(rust_request_id="r:x",operation="connected_components",inputs=RustInput(adjacency_matrix=[[0,1],[1,0]]),computational_job_ref="j:x")


def test_components_bad_symmetry():
    with pytest.raises(ValidationError):
        RustExecutionRequest(rust_request_id="r:x",operation="connected_components",inputs=RustInput(adjacency_matrix=[[0,1],[0,0]]),computational_job_ref="j:x")


def test_topological_request():
    RustExecutionRequest(rust_request_id="r:x",operation="topological_sort",inputs=RustInput(vertex_count=3,edge_list=[[0,1],[1,2]]),computational_job_ref="j:x")


def test_topological_bad_edge():
    with pytest.raises(ValidationError):
        RustExecutionRequest(rust_request_id="r:x",operation="topological_sort",inputs=RustInput(vertex_count=2,edge_list=[[0,2]]),computational_job_ref="j:x")


def test_levenshtein_request():
    RustExecutionRequest(rust_request_id="r:x",operation="levenshtein_distance",inputs=RustInput(text_a="kitten",text_b="sitting"),computational_job_ref="j:x")


def test_levenshtein_non_ascii():
    with pytest.raises(ValidationError):
        RustExecutionRequest(rust_request_id="r:x",operation="levenshtein_distance",inputs=RustInput(text_a="café",text_b="cafe"),computational_job_ref="j:x")


def test_fnv_request():
    RustExecutionRequest(rust_request_id="r:x",operation="fnv1a_64",inputs=RustInput(text="abc"),computational_job_ref="j:x")


def test_result_contract_requires_output():
    with pytest.raises(ValidationError):
        RustExecutionResultContract(result_contract_id="x:x",rust_request_ref="r:x",operation="prefix_sum")


def test_result_contract_duplicate_artifact():
    with pytest.raises(ValidationError):
        RustExecutionResultContract(result_contract_id="x:x",rust_request_ref="r:x",operation="prefix_sum",expected_artifact_kinds=["a","a"])


def test_result_fingerprint_ignores_state():
    c=B().result_contract; d=deepcopy(c); d.state=RustExecutionState.completed; assert c.fingerprint()==d.fingerprint()


def test_registration():
    r=RustRuntimeRegistration(registration_id="r:x"); assert r.language=="rust" and r.edition=="2021"


def test_registration_bad_runtime():
    with pytest.raises(ValidationError): RustRuntimeRegistration(registration_id="r:x",runtime_id="bad")


def test_registration_bad_ops():
    with pytest.raises(ValidationError): RustRuntimeRegistration(registration_id="r:x",operations=["prefix_sum"])


def test_environment():
    e=reference_environment_package(); p={x.name:x.version for x in e.system_packages}; assert p["rustc"]==RUST_PACKAGE_VERSION and p["cargo"]==CARGO_PACKAGE_VERSION


def test_environment_metadata():
    e=reference_environment_package(); assert e.metadata["unsafe_code_forbidden"] is True and e.metadata["arbitrary_rust_code"] is False


def test_security():
    p=reference_security_policy(); assert p.isolation_profile.network_mode=="none" and p.isolation_profile.shell_allowed is False and p.isolation_profile.arbitrary_code_allowed is False


def test_security_metadata():
    p=reference_security_policy(); assert p.metadata["unsafe_code_allowed"] is False and p.metadata["cargo_dependency_install_allowed"] is False


def test_bundle():
    assert B().reference_request.operation==RustOperation.prefix_sum and len(B().fingerprint())==64


def test_bundle_source_ref():
    assert "c-cpp-runtime-bundle:reference:v1" in B().source_object_refs


def test_artifact():
    a=to_scientific_rust_artifact(B()); assert a["source_contract"]==CONTRACT_VERSION and a["metadata"]["runtime_id"]==RUNTIME_ID


def test_registry_artifact():
    from app.services.scientific_result_registry import ScientificArtifactRef
    ScientificArtifactRef.model_validate(to_scientific_rust_artifact(B()))


def test_contract():
    d=contract_document(); assert d["release"]=="3.52.0" and d["capabilities"]["safe_native_systems"] is True and d["capabilities"]["unsafe_code_forbidden"] is True


@pytest.mark.parametrize("k",[
    "core_executes_rust","arbitrary_rust_source","unsafe_rust_code","shell_execution",
    "runtime_package_install_via_api","caller_filesystem_paths","core_selects_algorithm",
    "core_certifies_numerical_validity","core_certifies_scientific_validity",
])
def test_boundaries_false(k):
    assert contract_document()["boundaries"][k] is False


def test_request_fingerprint():
    assert B().reference_request.fingerprint()==deepcopy(B().reference_request).fingerprint()


def test_environment_fingerprint():
    assert reference_environment_package().fingerprint()==deepcopy(reference_environment_package()).fingerprint()


def test_policy_fingerprint():
    assert reference_security_policy().fingerprint()==deepcopy(reference_security_policy()).fingerprint()


def test_registration_fingerprint():
    assert B().registration.fingerprint()==deepcopy(B().registration).fingerprint()
