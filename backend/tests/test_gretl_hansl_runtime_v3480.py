from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.gretl_hansl_runtime import (
    ADAPTER_ID,
    CONTRACT_VERSION,
    GRETL_OPERATIONS,
    GRETL_PACKAGE_VERSION,
    GRETL_VERSION,
    PROVIDER_VERSION,
    RUNTIME_ID,
    GretlDataset,
    GretlExecutionRequest,
    GretlExecutionResultContract,
    GretlExecutionSettings,
    GretlExecutionState,
    GretlModelSpecification,
    GretlOperation,
    GretlRuntimeBundle,
    GretlRuntimeRegistration,
    contract_document,
    reference_environment_package,
    reference_runtime_bundle,
    reference_security_policy,
    to_scientific_gretl_artifact,
)


def ref_bundle():
    return reference_runtime_bundle()


def test_contract_identity():
    doc = contract_document()
    assert doc["release"] == "3.48.0"
    assert doc["contract"] == CONTRACT_VERSION


def test_runtime_identity():
    assert RUNTIME_ID == "sc-runtime-gretl"
    assert ADAPTER_ID == "adapter:sc-runtime-gretl"
    assert PROVIDER_VERSION == "1.0.0"
    assert GRETL_VERSION == "2023c"
    assert GRETL_PACKAGE_VERSION == "2023c-2.1build3"


def test_operation_set():
    assert GRETL_OPERATIONS == [
        "ols", "robust_ols", "logit", "probit",
        "descriptive_summary", "correlation_matrix",
    ]


def test_dataset_requires_columns():
    with pytest.raises(ValidationError):
        GretlDataset(dataset_id="dataset:test", columns={})


def test_dataset_equal_lengths():
    with pytest.raises(ValidationError):
        GretlDataset(dataset_id="dataset:test", columns={"y":[1,2], "x":[1]})


def test_dataset_min_two_rows():
    with pytest.raises(ValidationError):
        GretlDataset(dataset_id="dataset:test", columns={"y":[1], "x":[2]})


def test_dataset_fingerprint_stable():
    d = GretlDataset(dataset_id="dataset:test", columns={"y":[1,2], "x":[2,3]})
    assert d.fingerprint() == deepcopy(d).fingerprint()


def test_spec_predictors_unique():
    with pytest.raises(ValidationError):
        GretlModelSpecification(dependent_variable="y", predictors=["x","x"])


def test_spec_variables_unique():
    with pytest.raises(ValidationError):
        GretlModelSpecification(variables=["x","x"])


def test_spec_dep_not_predictor():
    with pytest.raises(ValidationError):
        GretlModelSpecification(dependent_variable="y", predictors=["y"])


def test_spec_fingerprint_stable():
    s = GretlModelSpecification(dependent_variable="y", predictors=["x"])
    assert s.fingerprint() == deepcopy(s).fingerprint()


def test_settings_defaults():
    s = GretlExecutionSettings()
    assert s.max_execution_seconds == 120


def test_settings_bounds():
    with pytest.raises(ValidationError):
        GretlExecutionSettings(max_execution_seconds=0)


def test_model_request_valid():
    req = GretlExecutionRequest(
        gretl_request_id="request:test",
        operation=GretlOperation.ols,
        dataset=GretlDataset(
            dataset_id="dataset:test",
            columns={"y":[1,2,3], "x":[2,3,4]},
        ),
        specification=GretlModelSpecification(
            dependent_variable="y",
            predictors=["x"],
        ),
        computational_job_ref="job:test",
    )
    assert req.operation == GretlOperation.ols


@pytest.mark.parametrize("operation", [
    GretlOperation.ols,
    GretlOperation.robust_ols,
    GretlOperation.logit,
    GretlOperation.probit,
])
def test_model_operations_require_dep(operation):
    with pytest.raises(ValidationError):
        GretlExecutionRequest(
            gretl_request_id="request:test",
            operation=operation,
            dataset=GretlDataset(
                dataset_id="dataset:test",
                columns={"y":[1,2,3], "x":[2,3,4]},
            ),
            specification=GretlModelSpecification(predictors=["x"]),
            computational_job_ref="job:test",
        )


@pytest.mark.parametrize("operation", [
    GretlOperation.descriptive_summary,
    GretlOperation.correlation_matrix,
])
def test_summary_operations_require_variables(operation):
    with pytest.raises(ValidationError):
        GretlExecutionRequest(
            gretl_request_id="request:test",
            operation=operation,
            dataset=GretlDataset(
                dataset_id="dataset:test",
                columns={"y":[1,2,3], "x":[2,3,4]},
            ),
            specification=GretlModelSpecification(),
            computational_job_ref="job:test",
        )


def test_request_rejects_missing_column():
    with pytest.raises(ValidationError):
        GretlExecutionRequest(
            gretl_request_id="request:test",
            operation=GretlOperation.ols,
            dataset=GretlDataset(
                dataset_id="dataset:test",
                columns={"y":[1,2,3], "x":[2,3,4]},
            ),
            specification=GretlModelSpecification(
                dependent_variable="y",
                predictors=["missing"],
            ),
            computational_job_ref="job:test",
        )


def test_request_defaults():
    req = ref_bundle().reference_request
    assert req.environment_package_ref == "environment-package:gretl-hansl-runtime:v1"
    assert req.security_policy_ref == "runtime-security-policy:gretl-hansl-runtime-standard:v1"


def test_request_fingerprint_stable():
    req = ref_bundle().reference_request
    assert req.fingerprint() == deepcopy(req).fingerprint()


def test_result_contract_requires_outputs():
    with pytest.raises(ValidationError):
        GretlExecutionResultContract(
            result_contract_id="result:test",
            gretl_request_ref="request:test",
            operation=GretlOperation.ols,
        )


def test_result_contract_rejects_duplicate_artifacts():
    with pytest.raises(ValidationError):
        GretlExecutionResultContract(
            result_contract_id="result:test",
            gretl_request_ref="request:test",
            operation=GretlOperation.ols,
            expected_artifact_kinds=["x","x"],
        )


def test_result_contract_fingerprint_ignores_state():
    c = ref_bundle().result_contract
    other = deepcopy(c)
    other.state = GretlExecutionState.completed
    assert c.fingerprint() == other.fingerprint()


def test_registration_identity():
    r = GretlRuntimeRegistration(registration_id="registration:test")
    assert r.runtime_id == RUNTIME_ID
    assert r.adapter_id == ADAPTER_ID
    assert r.language == "hansl"
    assert r.runtime_kind == "domain"


def test_registration_rejects_wrong_runtime():
    with pytest.raises(ValidationError):
        GretlRuntimeRegistration(registration_id="registration:test", runtime_id="wrong")


def test_registration_rejects_operation_mismatch():
    with pytest.raises(ValidationError):
        GretlRuntimeRegistration(registration_id="registration:test", operations=["ols"])


def test_registration_fingerprint_stable():
    r = ref_bundle().registration
    assert r.fingerprint() == deepcopy(r).fingerprint()


def test_environment_identity():
    env = reference_environment_package()
    assert env.environment_package_id == "environment-package:gretl-hansl-runtime:v1"
    assert env.state == "verified"


def test_environment_runtime_binding():
    env = reference_environment_package()
    assert env.runtimes[0].runtime_ref == RUNTIME_ID
    assert env.runtimes[0].runtime_adapter_ref == ADAPTER_ID


def test_environment_pins_gretl_packages():
    env = reference_environment_package()
    packages = {x.name:x.version for x in env.system_packages}
    assert packages["gretl"] == GRETL_PACKAGE_VERSION
    assert packages["gretl-common"] == GRETL_PACKAGE_VERSION


def test_environment_paths():
    env = reference_environment_package()
    values = {x.name:x.value for x in env.environment_variables}
    assert values["SC_GRETL_ARTIFACT_ROOT"] == "/var/lib/sc-gretl-runtime/artifacts"
    assert values["SC_GRETL_WORK_ROOT"] == "/var/lib/sc-gretl-runtime/work"


def test_environment_build_steps():
    assert [x.ordinal for x in reference_environment_package().build_instructions] == [1,2,3]


def test_environment_fingerprint_stable():
    env = reference_environment_package()
    assert env.fingerprint() == deepcopy(env).fingerprint()


def test_security_identity():
    p = reference_security_policy()
    assert p.security_policy_id == "runtime-security-policy:gretl-hansl-runtime-standard:v1"


def test_security_runtime_scope():
    p = reference_security_policy()
    assert p.allowed_runtime_refs == [RUNTIME_ID]
    assert p.allowed_adapter_refs == [ADAPTER_ID]


def test_security_operation_scope():
    assert reference_security_policy().allowed_operations[RUNTIME_ID] == GRETL_OPERATIONS


def test_security_network_disabled():
    assert reference_security_policy().isolation_profile.network_mode == "none"


def test_security_package_install_disabled():
    assert reference_security_policy().isolation_profile.package_install_mode == "denied"


def test_security_shell_disabled():
    assert reference_security_policy().isolation_profile.shell_allowed is False


def test_security_arbitrary_code_disabled():
    assert reference_security_policy().isolation_profile.arbitrary_code_allowed is False


def test_security_metadata():
    p = reference_security_policy()
    assert p.metadata["arbitrary_hansl_source_allowed"] is False
    assert p.metadata["caller_filesystem_paths_allowed"] is False


def test_security_fingerprint_stable():
    p = reference_security_policy()
    assert p.fingerprint() == deepcopy(p).fingerprint()


def test_reference_bundle():
    b = ref_bundle()
    assert b.registration.runtime_id == RUNTIME_ID
    assert b.reference_request.operation == GretlOperation.ols


def test_reference_dataset():
    d = ref_bundle().reference_request.dataset
    assert list(d.columns) == ["y","x"]
    assert len(d.columns["y"]) == 5


def test_reference_specification():
    s = ref_bundle().reference_request.specification
    assert s.dependent_variable == "y"
    assert s.predictors == ["x"]
    assert s.include_constant is True


def test_reference_result_contract():
    c = ref_bundle().result_contract
    assert "gretl-transcript" in c.expected_artifact_kinds
    assert "regression-coefficients" in c.expected_result_kinds


def test_bundle_rejects_environment_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["reference_request"]["environment_package_ref"] = "environment:wrong"
    with pytest.raises(ValidationError):
        GretlRuntimeBundle.model_validate(data)


def test_bundle_rejects_security_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["reference_request"]["security_policy_ref"] = "policy:wrong"
    with pytest.raises(ValidationError):
        GretlRuntimeBundle.model_validate(data)


def test_bundle_rejects_result_request_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["result_contract"]["gretl_request_ref"] = "request:wrong"
    with pytest.raises(ValidationError):
        GretlRuntimeBundle.model_validate(data)


def test_bundle_rejects_operation_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["result_contract"]["operation"] = "probit"
    with pytest.raises(ValidationError):
        GretlRuntimeBundle.model_validate(data)


def test_bundle_fingerprint_stable():
    b = ref_bundle()
    assert b.fingerprint() == deepcopy(b).fingerprint()
    assert len(b.fingerprint()) == 64


def test_scientific_artifact_bridge():
    a = to_scientific_gretl_artifact(ref_bundle())
    assert a["artifact_kind"] == "package"
    assert a["source_contract"] == CONTRACT_VERSION
    assert a["content_sha256"] == ref_bundle().fingerprint()


def test_scientific_artifact_validates_registry():
    from app.services.scientific_result_registry import ScientificArtifactRef
    item = ScientificArtifactRef.model_validate(to_scientific_gretl_artifact(ref_bundle()))
    assert item.source_object_ref == ref_bundle().bundle_id


def test_contract_capabilities():
    caps = contract_document()["capabilities"]
    assert caps["econometrics"] is True
    assert caps["ordinary_least_squares"] is True
    assert caps["binary_logit"] is True
    assert caps["binary_probit"] is True
    assert caps["runtime_adapter_registration"] is True
    assert caps["unified_runtime_catalog_integration"] is True


def test_contract_workspace_integration():
    assert contract_document()["capabilities"]["workspace_product_profile_integration"] is True


def test_contract_lab_integration():
    assert contract_document()["capabilities"]["research_lab_product_profile_integration"] is True


def test_contract_core_does_not_execute():
    assert contract_document()["boundaries"]["core_executes_gretl"] is False


def test_contract_provider_executes():
    assert contract_document()["boundaries"]["provider_executes_gretl"] is True


def test_contract_no_hansl_source():
    assert contract_document()["boundaries"]["arbitrary_hansl_source"] is False


def test_contract_no_shell():
    assert contract_document()["boundaries"]["shell_execution"] is False


def test_contract_no_package_install():
    assert contract_document()["boundaries"]["runtime_package_install_via_api"] is False


def test_contract_no_paths():
    assert contract_document()["boundaries"]["caller_filesystem_paths"] is False


def test_contract_no_model_selection():
    assert contract_document()["boundaries"]["core_selects_model"] is False


def test_contract_no_econometric_validity_cert():
    assert contract_document()["boundaries"]["core_certifies_econometric_validity"] is False


def test_contract_no_scientific_validity_cert():
    assert contract_document()["boundaries"]["core_certifies_scientific_validity"] is False


def test_contract_reference_hash():
    assert len(contract_document()["reference"]["bundle_fingerprint_sha256"]) == 64
