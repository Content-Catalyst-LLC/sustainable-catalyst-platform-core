from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.octave_runtime import (
    ADAPTER_ID,
    CONTRACT_VERSION,
    OCTAVE_OPERATIONS,
    OCTAVE_VERSION,
    PROVIDER_VERSION,
    RUNTIME_ID,
    OctaveExecutionRequest,
    OctaveExecutionResultContract,
    OctaveExecutionSettings,
    OctaveExecutionState,
    OctaveNumericPayload,
    OctaveOperation,
    OctaveRuntimeBundle,
    OctaveRuntimeRegistration,
    contract_document,
    reference_environment_package,
    reference_runtime_bundle,
    reference_security_policy,
    to_scientific_octave_artifact,
)


def ref_bundle():
    return reference_runtime_bundle()


def test_contract_identity():
    doc = contract_document()
    assert doc["release"] == "3.47.0"
    assert doc["contract"] == CONTRACT_VERSION


def test_runtime_identity():
    assert RUNTIME_ID == "sc-runtime-octave"
    assert ADAPTER_ID == "adapter:sc-runtime-octave"
    assert PROVIDER_VERSION == "1.0.0"
    assert OCTAVE_VERSION == "8.4.0"


def test_operation_set():
    assert OCTAVE_OPERATIONS == [
        "matrix_multiply",
        "linear_solve",
        "eigenvalues",
        "svd",
        "fft",
        "polynomial_roots",
    ]


def test_payload_requires_values():
    with pytest.raises(ValidationError):
        OctaveNumericPayload(payload_id="payload:test", values={})


def test_payload_fingerprint_stable():
    p = OctaveNumericPayload(payload_id="payload:test", values={"x": [1,2,3]})
    assert p.fingerprint() == deepcopy(p).fingerprint()


def test_settings_defaults():
    s = OctaveExecutionSettings()
    assert s.precision_digits == 15
    assert s.max_execution_seconds == 120


def test_settings_bounds():
    with pytest.raises(ValidationError):
        OctaveExecutionSettings(precision_digits=3)


def test_settings_fingerprint_stable():
    s = OctaveExecutionSettings()
    assert s.fingerprint() == deepcopy(s).fingerprint()


@pytest.mark.parametrize("operation", list(OctaveOperation))
def test_request_operations(operation):
    req = OctaveExecutionRequest(
        octave_request_id=f"request:{operation.value}",
        operation=operation,
        payload=OctaveNumericPayload(payload_id="payload:test", values={"x":[1]}),
        computational_job_ref="job:test",
    )
    assert req.operation == operation


def test_request_default_environment():
    assert ref_bundle().reference_request.environment_package_ref == "environment-package:octave-runtime:v1"


def test_request_default_security():
    assert ref_bundle().reference_request.security_policy_ref == "runtime-security-policy:octave-runtime-standard:v1"


def test_request_fingerprint_stable():
    r = ref_bundle().reference_request
    assert r.fingerprint() == deepcopy(r).fingerprint()


def test_result_contract_requires_output():
    with pytest.raises(ValidationError):
        OctaveExecutionResultContract(
            result_contract_id="result:test",
            octave_request_ref="request:test",
            operation=OctaveOperation.linear_solve,
        )


def test_result_contract_rejects_duplicate_artifacts():
    with pytest.raises(ValidationError):
        OctaveExecutionResultContract(
            result_contract_id="result:test",
            octave_request_ref="request:test",
            operation=OctaveOperation.linear_solve,
            expected_artifact_kinds=["json", "json"],
        )


def test_result_contract_fingerprint_ignores_state():
    c = ref_bundle().result_contract
    other = deepcopy(c)
    other.state = OctaveExecutionState.completed
    assert c.fingerprint() == other.fingerprint()


def test_registration_identity():
    r = OctaveRuntimeRegistration(registration_id="registration:test")
    assert r.runtime_id == RUNTIME_ID
    assert r.adapter_id == ADAPTER_ID
    assert r.provider_version == PROVIDER_VERSION


def test_registration_rejects_wrong_identity():
    with pytest.raises(ValidationError):
        OctaveRuntimeRegistration(
            registration_id="registration:test",
            runtime_id="wrong",
        )


def test_registration_rejects_operation_mismatch():
    with pytest.raises(ValidationError):
        OctaveRuntimeRegistration(
            registration_id="registration:test",
            operations=["linear_solve"],
        )


def test_registration_fingerprint_stable():
    r = ref_bundle().registration
    assert r.fingerprint() == deepcopy(r).fingerprint()


def test_environment_identity():
    env = reference_environment_package()
    assert env.environment_package_id == "environment-package:octave-runtime:v1"
    assert env.state == "verified"


def test_environment_runtime_binding():
    env = reference_environment_package()
    assert env.runtimes[0].runtime_ref == RUNTIME_ID
    assert env.runtimes[0].runtime_adapter_ref == ADAPTER_ID


def test_environment_octave_package():
    env = reference_environment_package()
    assert env.system_packages[0].name == "octave"
    assert env.system_packages[0].version == OCTAVE_VERSION


def test_environment_paths():
    env = reference_environment_package()
    values = {x.name:x.value for x in env.environment_variables}
    assert values["SC_OCTAVE_ARTIFACT_ROOT"] == "/var/lib/sc-octave-runtime/artifacts"
    assert values["SC_OCTAVE_WORK_ROOT"] == "/var/lib/sc-octave-runtime/work"


def test_environment_build_steps():
    env = reference_environment_package()
    assert [x.ordinal for x in env.build_instructions] == [1,2,3]


def test_environment_fingerprint_stable():
    env = reference_environment_package()
    assert env.fingerprint() == deepcopy(env).fingerprint()


def test_security_policy_identity():
    p = reference_security_policy()
    assert p.security_policy_id == "runtime-security-policy:octave-runtime-standard:v1"


def test_security_runtime_scope():
    p = reference_security_policy()
    assert p.allowed_runtime_refs == [RUNTIME_ID]
    assert p.allowed_adapter_refs == [ADAPTER_ID]


def test_security_operation_scope():
    assert reference_security_policy().allowed_operations[RUNTIME_ID] == OCTAVE_OPERATIONS


def test_security_network_disabled():
    assert reference_security_policy().isolation_profile.network_mode == "none"


def test_security_package_install_disabled():
    assert reference_security_policy().isolation_profile.package_install_mode == "denied"


def test_security_shell_disabled():
    assert reference_security_policy().isolation_profile.shell_allowed is False


def test_security_arbitrary_code_disabled():
    assert reference_security_policy().isolation_profile.arbitrary_code_allowed is False


def test_security_metadata_no_source():
    p = reference_security_policy()
    assert p.metadata["arbitrary_octave_source_allowed"] is False
    assert p.metadata["caller_filesystem_paths_allowed"] is False


def test_security_fingerprint_stable():
    p = reference_security_policy()
    assert p.fingerprint() == deepcopy(p).fingerprint()


def test_reference_bundle():
    b = ref_bundle()
    assert b.registration.runtime_id == RUNTIME_ID
    assert b.reference_request.operation == OctaveOperation.linear_solve


def test_reference_linear_system():
    values = ref_bundle().reference_request.payload.values
    assert values["A"] == [[3.0,1.0],[1.0,2.0]]
    assert values["b"] == [9.0,8.0]


def test_reference_expected_solution_metadata():
    assert ref_bundle().reference_request.payload.metadata["expected_solution"] == [2.0,3.0]


def test_reference_result_contract():
    c = ref_bundle().result_contract
    assert "octave-result-json" in c.expected_artifact_kinds
    assert "numerical-vector" in c.expected_result_kinds


def test_bundle_rejects_environment_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["reference_request"]["environment_package_ref"] = "environment:wrong"
    with pytest.raises(ValidationError):
        OctaveRuntimeBundle.model_validate(data)


def test_bundle_rejects_security_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["reference_request"]["security_policy_ref"] = "policy:wrong"
    with pytest.raises(ValidationError):
        OctaveRuntimeBundle.model_validate(data)


def test_bundle_rejects_result_request_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["result_contract"]["octave_request_ref"] = "request:wrong"
    with pytest.raises(ValidationError):
        OctaveRuntimeBundle.model_validate(data)


def test_bundle_rejects_operation_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["result_contract"]["operation"] = "fft"
    with pytest.raises(ValidationError):
        OctaveRuntimeBundle.model_validate(data)


def test_bundle_fingerprint_stable():
    b = ref_bundle()
    assert b.fingerprint() == deepcopy(b).fingerprint()
    assert len(b.fingerprint()) == 64


def test_scientific_artifact_bridge():
    a = to_scientific_octave_artifact(ref_bundle())
    assert a["artifact_kind"] == "package"
    assert a["source_contract"] == CONTRACT_VERSION
    assert a["content_sha256"] == ref_bundle().fingerprint()


def test_scientific_artifact_validates_v338():
    from app.services.scientific_result_registry import ScientificArtifactRef
    item = ScientificArtifactRef.model_validate(to_scientific_octave_artifact(ref_bundle()))
    assert item.source_object_ref == ref_bundle().bundle_id


def test_contract_capabilities():
    caps = contract_document()["capabilities"]
    assert caps["matrix_compute"] is True
    assert caps["linear_system_solving"] is True
    assert caps["eigenvalue_analysis"] is True
    assert caps["fast_fourier_transform"] is True
    assert caps["runtime_adapter_registration"] is True
    assert caps["unified_runtime_catalog_integration"] is True


def test_contract_workspace_integration():
    assert contract_document()["capabilities"]["workspace_product_profile_integration"] is True


def test_contract_lab_integration():
    assert contract_document()["capabilities"]["research_lab_product_profile_integration"] is True


def test_contract_workbench_integration():
    assert contract_document()["capabilities"]["workbench_product_profile_integration"] is True


def test_contract_core_does_not_execute():
    assert contract_document()["boundaries"]["core_executes_octave"] is False


def test_contract_provider_executes():
    assert contract_document()["boundaries"]["provider_executes_octave"] is True


def test_contract_no_arbitrary_source():
    assert contract_document()["boundaries"]["arbitrary_octave_source"] is False


def test_contract_no_shell():
    assert contract_document()["boundaries"]["shell_execution"] is False


def test_contract_no_package_install():
    assert contract_document()["boundaries"]["runtime_package_install_via_api"] is False


def test_contract_no_paths():
    assert contract_document()["boundaries"]["caller_filesystem_paths"] is False


def test_contract_no_method_selection():
    assert contract_document()["boundaries"]["core_selects_method"] is False


def test_contract_no_numerical_validity_cert():
    assert contract_document()["boundaries"]["core_certifies_numerical_validity"] is False


def test_contract_no_scientific_validity_cert():
    assert contract_document()["boundaries"]["core_certifies_scientific_validity"] is False


def test_contract_reference_hash():
    assert len(contract_document()["reference"]["bundle_fingerprint_sha256"]) == 64
