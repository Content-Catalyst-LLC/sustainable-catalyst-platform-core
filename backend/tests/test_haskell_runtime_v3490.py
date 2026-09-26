from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.haskell_runtime import (
    ADAPTER_ID, CONTRACT_VERSION, GHC_PACKAGE_VERSION, GHC_VERSION,
    HASKELL_OPERATIONS, PROVIDER_VERSION, RUNTIME_ID,
    HaskellExecutionRequest, HaskellExecutionResultContract,
    HaskellExecutionSettings, HaskellExecutionState, HaskellOperation,
    HaskellRuntimeBundle, HaskellRuntimeRegistration, HaskellTypedInput,
    contract_document, reference_environment_package, reference_runtime_bundle,
    reference_security_policy, to_scientific_haskell_artifact,
)


def ref_bundle():
    return reference_runtime_bundle()


def test_contract_identity():
    d=contract_document(); assert d['release']=='3.49.0'; assert d['contract']==CONTRACT_VERSION

def test_runtime_identity():
    assert RUNTIME_ID=='sc-runtime-haskell'; assert ADAPTER_ID=='adapter:sc-runtime-haskell'

def test_versions():
    assert PROVIDER_VERSION=='1.0.0'; assert GHC_VERSION=='9.4.7'; assert GHC_PACKAGE_VERSION=='9.4.7-3'

def test_operation_set():
    assert HASKELL_OPERATIONS == ['gcd','lcm','rational_reduce','factorial','fibonacci','binomial_coefficient','integer_power','graph_reachable']

def test_input_fingerprint_stable():
    x=HaskellTypedInput(integers=[84,30]); assert x.fingerprint()==deepcopy(x).fingerprint()

def test_settings_defaults():
    s=HaskellExecutionSettings(); assert s.max_execution_seconds==60; assert s.max_integer_digits==20000

def test_settings_bounds():
    with pytest.raises(ValidationError): HaskellExecutionSettings(max_execution_seconds=0)

@pytest.mark.parametrize('op', [HaskellOperation.gcd,HaskellOperation.lcm])
def test_binary_integer_valid(op):
    r=HaskellExecutionRequest(haskell_request_id='r:test',operation=op,inputs=HaskellTypedInput(integers=[84,30]),computational_job_ref='job:test'); assert r.operation==op

@pytest.mark.parametrize('op', [HaskellOperation.gcd,HaskellOperation.lcm])
def test_binary_integer_requires_two(op):
    with pytest.raises(ValidationError):
        HaskellExecutionRequest(haskell_request_id='r:test',operation=op,inputs=HaskellTypedInput(integers=[84]),computational_job_ref='job:test')

def test_rational_valid():
    r=HaskellExecutionRequest(haskell_request_id='r:test',operation='rational_reduce',inputs=HaskellTypedInput(numerator=42,denominator=56),computational_job_ref='job:test'); assert r.inputs.denominator==56

def test_rational_zero_denominator():
    with pytest.raises(ValidationError):
        HaskellExecutionRequest(haskell_request_id='r:test',operation='rational_reduce',inputs=HaskellTypedInput(numerator=1,denominator=0),computational_job_ref='job:test')

@pytest.mark.parametrize('op', [HaskellOperation.factorial,HaskellOperation.fibonacci])
def test_sequence_valid(op):
    r=HaskellExecutionRequest(haskell_request_id='r:test',operation=op,inputs=HaskellTypedInput(n=20),computational_job_ref='job:test'); assert r.inputs.n==20

@pytest.mark.parametrize('op', [HaskellOperation.factorial,HaskellOperation.fibonacci])
def test_sequence_negative_rejected(op):
    with pytest.raises(ValidationError):
        HaskellExecutionRequest(haskell_request_id='r:test',operation=op,inputs=HaskellTypedInput(n=-1),computational_job_ref='job:test')

def test_binomial_valid():
    r=HaskellExecutionRequest(haskell_request_id='r:test',operation='binomial_coefficient',inputs=HaskellTypedInput(n=10,k=3),computational_job_ref='job:test'); assert r.inputs.k==3

def test_binomial_invalid_k():
    with pytest.raises(ValidationError):
        HaskellExecutionRequest(haskell_request_id='r:test',operation='binomial_coefficient',inputs=HaskellTypedInput(n=4,k=7),computational_job_ref='job:test')

def test_power_valid():
    r=HaskellExecutionRequest(haskell_request_id='r:test',operation='integer_power',inputs=HaskellTypedInput(base=2,exponent=64),computational_job_ref='job:test'); assert r.inputs.exponent==64

def test_power_negative_exponent():
    with pytest.raises(ValidationError):
        HaskellExecutionRequest(haskell_request_id='r:test',operation='integer_power',inputs=HaskellTypedInput(base=2,exponent=-1),computational_job_ref='job:test')

def test_graph_valid():
    r=HaskellExecutionRequest(haskell_request_id='r:test',operation='graph_reachable',inputs=HaskellTypedInput(graph_edges=[(1,2),(2,3)],graph_source=1,graph_target=3),computational_job_ref='job:test'); assert len(r.inputs.graph_edges)==2

def test_graph_requires_endpoints():
    with pytest.raises(ValidationError):
        HaskellExecutionRequest(haskell_request_id='r:test',operation='graph_reachable',inputs=HaskellTypedInput(graph_edges=[(1,2)]),computational_job_ref='job:test')

def test_request_defaults():
    r=ref_bundle().reference_request; assert r.environment_package_ref=='environment-package:haskell-runtime:v1'; assert r.security_policy_ref=='runtime-security-policy:haskell-runtime-standard:v1'

def test_request_fingerprint_stable():
    r=ref_bundle().reference_request; assert r.fingerprint()==deepcopy(r).fingerprint()

def test_result_contract_requires_outputs():
    with pytest.raises(ValidationError): HaskellExecutionResultContract(result_contract_id='c:test',haskell_request_ref='r:test',operation='gcd')

def test_result_contract_duplicates():
    with pytest.raises(ValidationError): HaskellExecutionResultContract(result_contract_id='c:test',haskell_request_ref='r:test',operation='gcd',expected_artifact_kinds=['x','x'])

def test_result_contract_fingerprint_ignores_state():
    c=ref_bundle().result_contract; d=deepcopy(c); d.state=HaskellExecutionState.completed; assert c.fingerprint()==d.fingerprint()

def test_registration_identity():
    r=HaskellRuntimeRegistration(registration_id='reg:test'); assert r.runtime_id==RUNTIME_ID; assert r.runtime_kind=='language'; assert r.language=='haskell'

def test_registration_wrong_runtime():
    with pytest.raises(ValidationError): HaskellRuntimeRegistration(registration_id='reg:test',runtime_id='wrong')

def test_registration_operation_mismatch():
    with pytest.raises(ValidationError): HaskellRuntimeRegistration(registration_id='reg:test',operations=['gcd'])

def test_registration_fingerprint_stable():
    r=ref_bundle().registration; assert r.fingerprint()==deepcopy(r).fingerprint()

def test_environment_identity():
    e=reference_environment_package(); assert e.environment_package_id=='environment-package:haskell-runtime:v1'; assert e.state=='verified'

def test_environment_runtime_binding():
    e=reference_environment_package(); assert e.runtimes[0].runtime_ref==RUNTIME_ID; assert e.runtimes[0].runtime_adapter_ref==ADAPTER_ID

def test_environment_ghc_pin():
    e=reference_environment_package(); p={x.name:x.version for x in e.system_packages}; assert p['ghc']==GHC_PACKAGE_VERSION

def test_environment_paths():
    e=reference_environment_package(); v={x.name:x.value for x in e.environment_variables}; assert v['SC_HASKELL_ARTIFACT_ROOT']=='/var/lib/sc-haskell-runtime/artifacts'; assert v['SC_HASKELL_WORK_ROOT']=='/var/lib/sc-haskell-runtime/work'

def test_environment_steps():
    assert [x.ordinal for x in reference_environment_package().build_instructions]==[1,2,3]

def test_environment_metadata():
    e=reference_environment_package(); assert e.metadata['arbitrary_haskell_source'] is False

def test_environment_fingerprint_stable():
    e=reference_environment_package(); assert e.fingerprint()==deepcopy(e).fingerprint()

def test_security_identity():
    p=reference_security_policy(); assert p.security_policy_id=='runtime-security-policy:haskell-runtime-standard:v1'

def test_security_scope():
    p=reference_security_policy(); assert p.allowed_runtime_refs==[RUNTIME_ID]; assert p.allowed_adapter_refs==[ADAPTER_ID]

def test_security_operations():
    assert reference_security_policy().allowed_operations[RUNTIME_ID]==HASKELL_OPERATIONS

def test_security_network_none():
    assert reference_security_policy().isolation_profile.network_mode=='none'

def test_security_package_install_denied():
    assert reference_security_policy().isolation_profile.package_install_mode=='denied'

def test_security_shell_denied():
    assert reference_security_policy().isolation_profile.shell_allowed is False

def test_security_arbitrary_code_denied():
    assert reference_security_policy().isolation_profile.arbitrary_code_allowed is False

def test_security_metadata():
    p=reference_security_policy(); assert p.metadata['arbitrary_haskell_source_allowed'] is False; assert p.metadata['caller_filesystem_paths_allowed'] is False

def test_security_fingerprint_stable():
    p=reference_security_policy(); assert p.fingerprint()==deepcopy(p).fingerprint()

def test_reference_bundle():
    b=ref_bundle(); assert b.registration.runtime_id==RUNTIME_ID; assert b.reference_request.operation==HaskellOperation.rational_reduce

def test_reference_input():
    i=ref_bundle().reference_request.inputs; assert i.numerator==42; assert i.denominator==56

def test_reference_result_contract():
    c=ref_bundle().result_contract; assert 'haskell-generated-source' in c.expected_artifact_kinds; assert 'exact-rational-result' in c.expected_result_kinds

def test_bundle_environment_mismatch():
    d=ref_bundle().model_dump(mode='python'); d['reference_request']['environment_package_ref']='environment:wrong'
    with pytest.raises(ValidationError): HaskellRuntimeBundle.model_validate(d)

def test_bundle_security_mismatch():
    d=ref_bundle().model_dump(mode='python'); d['reference_request']['security_policy_ref']='policy:wrong'
    with pytest.raises(ValidationError): HaskellRuntimeBundle.model_validate(d)

def test_bundle_result_mismatch():
    d=ref_bundle().model_dump(mode='python'); d['result_contract']['haskell_request_ref']='request:wrong'
    with pytest.raises(ValidationError): HaskellRuntimeBundle.model_validate(d)

def test_bundle_operation_mismatch():
    d=ref_bundle().model_dump(mode='python'); d['result_contract']['operation']='gcd'
    with pytest.raises(ValidationError): HaskellRuntimeBundle.model_validate(d)

def test_bundle_fingerprint_stable():
    b=ref_bundle(); assert b.fingerprint()==deepcopy(b).fingerprint(); assert len(b.fingerprint())==64

def test_scientific_artifact_bridge():
    a=to_scientific_haskell_artifact(ref_bundle()); assert a['artifact_kind']=='package'; assert a['source_contract']==CONTRACT_VERSION; assert a['content_sha256']==ref_bundle().fingerprint()

def test_scientific_artifact_registry_validation():
    from app.services.scientific_result_registry import ScientificArtifactRef
    x=ScientificArtifactRef.model_validate(to_scientific_haskell_artifact(ref_bundle())); assert x.source_object_ref==ref_bundle().bundle_id

def test_capabilities():
    c=contract_document()['capabilities']; assert c['typed_functional_computation']; assert c['exact_integer_arithmetic']; assert c['exact_rational_arithmetic']; assert c['discrete_mathematics']; assert c['graph_reachability']

def test_product_capabilities():
    c=contract_document()['capabilities']; assert c['workspace_product_profile_integration']; assert c['research_lab_product_profile_integration']; assert c['workbench_product_profile_integration']

def test_boundaries_core_does_not_execute():
    assert contract_document()['boundaries']['core_executes_haskell'] is False

def test_boundaries_provider_executes():
    assert contract_document()['boundaries']['provider_executes_haskell'] is True

def test_boundaries_no_arbitrary_source():
    assert contract_document()['boundaries']['arbitrary_haskell_source'] is False

def test_boundaries_no_shell():
    assert contract_document()['boundaries']['shell_execution'] is False

def test_boundaries_no_package_install():
    assert contract_document()['boundaries']['runtime_package_install_via_api'] is False

def test_boundaries_no_paths():
    assert contract_document()['boundaries']['caller_filesystem_paths'] is False

def test_boundaries_no_method_selection():
    assert contract_document()['boundaries']['core_selects_method'] is False

def test_boundaries_no_math_validity_cert():
    assert contract_document()['boundaries']['core_certifies_mathematical_validity'] is False

def test_boundaries_no_scientific_validity_cert():
    assert contract_document()['boundaries']['core_certifies_scientific_validity'] is False

def test_contract_reference_hash():
    assert len(contract_document()['reference']['bundle_fingerprint_sha256'])==64
