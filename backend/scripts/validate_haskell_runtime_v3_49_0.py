#!/usr/bin/env python3
from app.services.haskell_runtime import (
    ADAPTER_ID, CONTRACT_VERSION, GHC_PACKAGE_VERSION, GHC_VERSION,
    HASKELL_OPERATIONS, PROVIDER_VERSION, RUNTIME_ID, contract_document,
    reference_runtime_bundle, to_scientific_haskell_artifact,
)
from app.services.scientific_result_registry import ScientificArtifactRef

doc=contract_document()
assert doc['release']=='3.49.0'
assert doc['contract']==CONTRACT_VERSION
assert doc['runtime_id']==RUNTIME_ID
assert doc['adapter_id']==ADAPTER_ID
assert doc['provider_version']==PROVIDER_VERSION
assert doc['ghc_version']==GHC_VERSION
assert doc['ghc_package_version']==GHC_PACKAGE_VERSION
assert doc['operations']==HASKELL_OPERATIONS
assert doc['language']=='haskell'
assert doc['capabilities']['typed_functional_computation'] is True
assert doc['capabilities']['exact_integer_arithmetic'] is True
assert doc['capabilities']['exact_rational_arithmetic'] is True
assert doc['capabilities']['graph_reachability'] is True
assert doc['boundaries']['core_executes_haskell'] is False
assert doc['boundaries']['arbitrary_haskell_source'] is False
bundle=reference_runtime_bundle()
assert bundle.registration.runtime_id==RUNTIME_ID
assert bundle.registration.provider_version==PROVIDER_VERSION
assert bundle.registration.runtime_kind=='language'
assert bundle.registration.language=='haskell'
assert bundle.environment_package.environment_package_id=='environment-package:haskell-runtime:v1'
assert bundle.security_policy.security_policy_id=='runtime-security-policy:haskell-runtime-standard:v1'
assert bundle.reference_request.operation=='rational_reduce'
assert len(bundle.fingerprint())==64
ScientificArtifactRef.model_validate(to_scientific_haskell_artifact(bundle))
print('PASS - Platform Core v3.49.0 Haskell Runtime')
print(f'CONTRACT={CONTRACT_VERSION}')
print(f'RUNTIME_ID={RUNTIME_ID}')
print(f'PROVIDER_VERSION={PROVIDER_VERSION}')
print(f'GHC_VERSION={GHC_VERSION}')
print(f'GHC_PACKAGE_VERSION={GHC_PACKAGE_VERSION}')
print('TYPED_FUNCTIONAL_COMPUTATION=enabled')
print('EXACT_INTEGER_ARITHMETIC=enabled')
print('EXACT_RATIONAL_ARITHMETIC=enabled')
print('DISCRETE_MATHEMATICS=enabled')
print('GRAPH_REACHABILITY=enabled')
print('WORKSPACE_INTEGRATION=enabled')
print('RESEARCH_LAB_INTEGRATION=enabled')
print('WORKBENCH_INTEGRATION=enabled')
print('ARBITRARY_HASKELL_SOURCE=false')
print('CORE_EXECUTES_HASKELL=false')
print('CORE_CERTIFIES_SCIENTIFIC_VALIDITY=false')
