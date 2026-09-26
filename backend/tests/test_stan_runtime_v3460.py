from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.stan_runtime import (
    ADAPTER_ID,
    CMDSTAN_VERSION,
    CONTRACT_VERSION,
    PROVIDER_VERSION,
    RUNTIME_ID,
    STAN_OPERATIONS,
    StanDataBinding,
    StanExecutionRequest,
    StanExecutionResultContract,
    StanExecutionState,
    StanInferenceSettings,
    StanModelSpec,
    StanOperation,
    StanRuntimeBundle,
    StanRuntimeRegistration,
    contract_document,
    reference_environment_package,
    reference_runtime_bundle,
    reference_security_policy,
    to_scientific_stan_artifact,
)


MODEL = """data { int<lower=1> N; array[N] real y; }
parameters { real mu; }
model { mu ~ normal(0,1); y ~ normal(mu,1); }
"""


def ref_bundle():
    return reference_runtime_bundle()


def test_contract_identity():
    doc = contract_document()
    assert doc["release"] == "3.46.0"
    assert doc["contract"] == CONTRACT_VERSION


def test_provider_identity():
    assert PROVIDER_VERSION == "1.0.0"
    assert RUNTIME_ID == "sc-runtime-stan"
    assert ADAPTER_ID == "adapter:sc-runtime-stan"
    assert CMDSTAN_VERSION == "2.36.0"


def test_operation_set():
    assert STAN_OPERATIONS == [
        "compile_model",
        "sample",
        "optimize",
        "variational",
        "diagnose",
    ]


def test_model_spec_computes_hash():
    m = StanModelSpec(model_id="stan:test", name="test", source=MODEL)
    assert len(m.source_sha256) == 64


def test_model_spec_hash_stable():
    m = StanModelSpec(model_id="stan:test", name="test", source=MODEL)
    assert m.fingerprint() == deepcopy(m).fingerprint()


def test_model_spec_rejects_bad_supplied_hash():
    with pytest.raises(ValidationError):
        StanModelSpec(
            model_id="stan:test",
            name="test",
            source=MODEL,
            source_sha256="f" * 64,
        )


def test_model_spec_rejects_include():
    with pytest.raises(ValidationError):
        StanModelSpec(
            model_id="stan:test",
            name="test",
            source='#include "shared.stan"\n' + MODEL,
        )


def test_data_binding_fingerprint_stable():
    d = StanDataBinding(data_binding_id="data:test", data={"N": 1, "y": [1.0]})
    assert d.fingerprint() == deepcopy(d).fingerprint()


def test_settings_defaults():
    s = StanInferenceSettings()
    assert s.chains == 1
    assert s.num_warmup == 500
    assert s.num_samples == 1000


def test_settings_chains_limited_to_one():
    with pytest.raises(ValidationError):
        StanInferenceSettings(chains=2)


def test_settings_reject_unknown_option():
    with pytest.raises(ValidationError):
        StanInferenceSettings(extra_options={"shell": True})


def test_settings_accept_adapt_delta():
    s = StanInferenceSettings(extra_options={"adapt_delta": 0.9})
    assert s.extra_options["adapt_delta"] == 0.9


def test_settings_fingerprint_stable():
    s = StanInferenceSettings(extra_options={"adapt_delta": 0.9})
    assert s.fingerprint() == deepcopy(s).fingerprint()


def test_compile_request_can_omit_data():
    req = StanExecutionRequest(
        stan_request_id="request:test",
        operation=StanOperation.compile_model,
        model=StanModelSpec(model_id="stan:test", name="test", source=MODEL),
        computational_job_ref="job:test",
    )
    assert req.data_binding is None


def test_non_compile_request_requires_data():
    with pytest.raises(ValidationError):
        StanExecutionRequest(
            stan_request_id="request:test",
            operation=StanOperation.sample,
            model=StanModelSpec(model_id="stan:test", name="test", source=MODEL),
            computational_job_ref="job:test",
        )


def test_sample_request_valid():
    req = StanExecutionRequest(
        stan_request_id="request:test",
        operation=StanOperation.sample,
        model=StanModelSpec(model_id="stan:test", name="test", source=MODEL),
        data_binding=StanDataBinding(
            data_binding_id="data:test",
            data={"N": 1, "y": [1.0]},
        ),
        computational_job_ref="job:test",
    )
    assert req.operation == StanOperation.sample


def test_request_default_environment():
    req = ref_bundle().reference_request
    assert req.environment_package_ref == "environment-package:stan-runtime:v1"


def test_request_default_security_policy():
    req = ref_bundle().reference_request
    assert req.security_policy_ref == "runtime-security-policy:stan-runtime-standard:v1"


def test_request_fingerprint_stable():
    req = ref_bundle().reference_request
    assert req.fingerprint() == deepcopy(req).fingerprint()


def test_result_contract_requires_output():
    with pytest.raises(ValidationError):
        StanExecutionResultContract(
            result_contract_id="result:test",
            stan_request_ref="request:test",
            operation=StanOperation.sample,
        )


def test_result_contract_rejects_duplicate_artifacts():
    with pytest.raises(ValidationError):
        StanExecutionResultContract(
            result_contract_id="result:test",
            stan_request_ref="request:test",
            operation=StanOperation.sample,
            expected_artifact_kinds=["csv", "csv"],
        )


def test_result_contract_fingerprint_ignores_state():
    c = ref_bundle().result_contract
    other = deepcopy(c)
    other.state = StanExecutionState.completed
    assert c.fingerprint() == other.fingerprint()


def test_registration_identity():
    r = StanRuntimeRegistration(registration_id="registration:test")
    assert r.runtime_id == RUNTIME_ID
    assert r.adapter_id == ADAPTER_ID
    assert r.provider_version == PROVIDER_VERSION


def test_registration_rejects_wrong_runtime():
    with pytest.raises(ValidationError):
        StanRuntimeRegistration(
            registration_id="registration:test",
            runtime_id="wrong",
        )


def test_registration_rejects_operation_mismatch():
    with pytest.raises(ValidationError):
        StanRuntimeRegistration(
            registration_id="registration:test",
            operations=["sample"],
        )


def test_registration_fingerprint_stable():
    r = ref_bundle().registration
    assert r.fingerprint() == deepcopy(r).fingerprint()


def test_environment_identity():
    env = reference_environment_package()
    assert env.environment_package_id == "environment-package:stan-runtime:v1"
    assert env.state == "verified"


def test_environment_contains_stan_runtime():
    env = reference_environment_package()
    assert env.runtimes[0].runtime_ref == RUNTIME_ID
    assert env.runtimes[0].runtime_version == PROVIDER_VERSION
    assert env.runtimes[0].runtime_adapter_ref == ADAPTER_ID


def test_environment_contains_build_toolchain():
    env = reference_environment_package()
    names = {x.name for x in env.system_packages}
    assert {"build-essential", "git"}.issubset(names)


def test_environment_contains_cmdstanpy():
    env = reference_environment_package()
    assert any(x.name == "cmdstanpy" for x in env.language_packages)


def test_environment_has_cmdstan_home():
    env = reference_environment_package()
    values = {x.name: x.value for x in env.environment_variables}
    assert "cmdstan-2.36.0" in values["SC_STAN_CMDSTAN_HOME"]


def test_environment_build_steps_contiguous():
    env = reference_environment_package()
    assert [x.ordinal for x in env.build_instructions] == [1, 2, 3, 4]


def test_environment_fingerprint_stable():
    env = reference_environment_package()
    assert env.fingerprint() == deepcopy(env).fingerprint()


def test_security_policy_identity():
    p = reference_security_policy()
    assert p.security_policy_id == "runtime-security-policy:stan-runtime-standard:v1"


def test_security_policy_only_stan_runtime():
    p = reference_security_policy()
    assert p.allowed_runtime_refs == [RUNTIME_ID]
    assert p.allowed_adapter_refs == [ADAPTER_ID]


def test_security_policy_operation_set():
    p = reference_security_policy()
    assert p.allowed_operations[RUNTIME_ID] == STAN_OPERATIONS


def test_security_network_disabled():
    p = reference_security_policy()
    assert p.isolation_profile.network_mode == "none"


def test_security_package_install_disabled():
    p = reference_security_policy()
    assert p.isolation_profile.package_install_mode == "denied"


def test_security_shell_disabled():
    p = reference_security_policy()
    assert p.isolation_profile.shell_allowed is False


def test_security_arbitrary_code_disabled():
    p = reference_security_policy()
    assert p.isolation_profile.arbitrary_code_allowed is False


def test_security_metadata_domain_model():
    p = reference_security_policy()
    assert p.metadata["stan_source_is_governed_domain_model"] is True
    assert p.metadata["stan_include_directives_allowed"] is False


def test_security_policy_fingerprint_stable():
    p = reference_security_policy()
    assert p.fingerprint() == deepcopy(p).fingerprint()


def test_reference_bundle_valid():
    b = ref_bundle()
    assert b.registration.runtime_id == RUNTIME_ID
    assert b.reference_request.operation == StanOperation.sample


def test_reference_model_is_normal_model():
    assert "normal(" in ref_bundle().reference_request.model.source


def test_reference_data_has_five_values():
    d = ref_bundle().reference_request.data_binding
    assert d is not None
    assert d.data["N"] == 5
    assert len(d.data["y"]) == 5


def test_reference_settings_bounded():
    s = ref_bundle().reference_request.settings
    assert s.chains == 1
    assert s.num_warmup == 100
    assert s.num_samples == 200
    assert s.max_execution_seconds == 300


def test_reference_result_contract():
    c = ref_bundle().result_contract
    assert "stan-sample-csv" in c.expected_artifact_kinds
    assert "posterior-sample-summary" in c.expected_result_kinds


def test_bundle_rejects_environment_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["reference_request"]["environment_package_ref"] = "environment-package:wrong"
    with pytest.raises(ValidationError):
        StanRuntimeBundle.model_validate(data)


def test_bundle_rejects_security_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["reference_request"]["security_policy_ref"] = "policy:wrong"
    with pytest.raises(ValidationError):
        StanRuntimeBundle.model_validate(data)


def test_bundle_rejects_result_request_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["result_contract"]["stan_request_ref"] = "request:wrong"
    with pytest.raises(ValidationError):
        StanRuntimeBundle.model_validate(data)


def test_bundle_rejects_result_operation_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["result_contract"]["operation"] = "optimize"
    with pytest.raises(ValidationError):
        StanRuntimeBundle.model_validate(data)


def test_bundle_fingerprint_stable():
    b = ref_bundle()
    assert b.fingerprint() == deepcopy(b).fingerprint()
    assert len(b.fingerprint()) == 64


def test_scientific_artifact_bridge():
    a = to_scientific_stan_artifact(ref_bundle())
    assert a["artifact_kind"] == "package"
    assert a["source_contract"] == CONTRACT_VERSION
    assert a["content_sha256"] == ref_bundle().fingerprint()


def test_scientific_artifact_validates_v338():
    from app.services.scientific_result_registry import ScientificArtifactRef
    item = ScientificArtifactRef.model_validate(to_scientific_stan_artifact(ref_bundle()))
    assert item.source_object_ref == ref_bundle().bundle_id


def test_contract_dependencies():
    deps = set(contract_document()["depends_on"])
    assert "sc.core.runtime-adapter.v1" in deps
    assert "sc.core.reproducible-environment-package.v1" in deps
    assert "sc.core.runtime-security-governance.v1" in deps
    assert "sc.core.unified-runtime-api.v1" in deps


def test_contract_capabilities():
    caps = contract_document()["capabilities"]
    assert caps["stan_model_compilation"] is True
    assert caps["posterior_sampling"] is True
    assert caps["variational_inference"] is True
    assert caps["runtime_adapter_registration"] is True
    assert caps["unified_runtime_catalog_integration"] is True


def test_contract_core_does_not_execute_stan():
    assert contract_document()["boundaries"]["core_executes_stan"] is False


def test_contract_provider_executes_stan():
    assert contract_document()["boundaries"]["provider_executes_stan"] is True


def test_contract_no_shell():
    assert contract_document()["boundaries"]["arbitrary_shell_execution"] is False


def test_contract_no_package_install_api():
    assert contract_document()["boundaries"]["runtime_package_install_via_api"] is False


def test_contract_no_include_directives():
    assert contract_document()["boundaries"]["stan_include_directives"] is False


def test_contract_no_external_cpp_extensions():
    assert contract_document()["boundaries"]["external_cpp_extensions"] is False


def test_contract_single_chain_v1():
    assert contract_document()["boundaries"]["multi_chain_parallel_execution_v1"] is False


def test_contract_no_method_selection():
    assert contract_document()["boundaries"]["core_selects_model_or_method"] is False


def test_contract_no_convergence_certification():
    assert contract_document()["boundaries"]["core_certifies_convergence"] is False


def test_contract_no_scientific_validity_certification():
    assert contract_document()["boundaries"]["core_certifies_scientific_validity"] is False


def test_contract_reference_hash():
    assert len(contract_document()["reference"]["bundle_fingerprint_sha256"]) == 64
