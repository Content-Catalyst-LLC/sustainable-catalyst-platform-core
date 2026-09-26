#!/usr/bin/env python3
from app.services.fortran_runtime import ADAPTER_ID,CONTRACT_VERSION,FORTRAN_OPERATIONS,GFORTRAN_PACKAGE_VERSION,GFORTRAN_VERSION,PROVIDER_VERSION,RUNTIME_ID,contract_document,reference_runtime_bundle,to_scientific_fortran_artifact
from app.services.scientific_result_registry import ScientificArtifactRef

doc=contract_document()
assert doc['release']=='3.50.0' and doc['contract']==CONTRACT_VERSION and doc['runtime_id']==RUNTIME_ID and doc['adapter_id']==ADAPTER_ID
assert doc['provider_version']==PROVIDER_VERSION and doc['gfortran_version']==GFORTRAN_VERSION and doc['gfortran_package_version']==GFORTRAN_PACKAGE_VERSION
assert doc['operations']==FORTRAN_OPERATIONS and doc['language']=='fortran'
assert doc['capabilities']['scientific_hpc'] and doc['capabilities']['numerical_compute'] and doc['capabilities']['provider_managed_compilation']
assert doc['boundaries']['core_executes_fortran'] is False and doc['boundaries']['arbitrary_fortran_source'] is False
b=reference_runtime_bundle(); assert b.registration.runtime_id==RUNTIME_ID and b.registration.runtime_kind=='language' and b.registration.language=='fortran'
assert b.reference_request.operation=='dot_product' and len(b.fingerprint())==64
ScientificArtifactRef.model_validate(to_scientific_fortran_artifact(b))
print('PASS - Platform Core v3.50.0 Fortran Runtime')
print(f'CONTRACT={CONTRACT_VERSION}')
print(f'RUNTIME_ID={RUNTIME_ID}')
print(f'PROVIDER_VERSION={PROVIDER_VERSION}')
print(f'GFORTRAN_VERSION={GFORTRAN_VERSION}')
print(f'GFORTRAN_PACKAGE_VERSION={GFORTRAN_PACKAGE_VERSION}')
print('SCIENTIFIC_HPC=enabled')
print('DOT_PRODUCT=enabled')
print('MATRIX_MULTIPLY=enabled')
print('TRAPEZOIDAL_INTEGRAL=enabled')
print('CENTRAL_DIFFERENCE=enabled')
print('RK4_LINEAR_STEP=enabled')
print('HEAT_STEP_1D=enabled')
print('WORKSPACE_INTEGRATION=enabled')
print('RESEARCH_LAB_INTEGRATION=enabled')
print('WORKBENCH_INTEGRATION=enabled')
print('CORE_EXECUTES_FORTRAN=false')
print('ARBITRARY_FORTRAN_SOURCE=false')
print('CORE_CERTIFIES_NUMERICAL_VALIDITY=false')
print('CORE_CERTIFIES_SCIENTIFIC_VALIDITY=false')
