from app.services.python_runtime import *
from app.services.runtime_adapter_registry import REGISTRY
from app.services.unified_runtime_api import reference_product_profiles, reference_runtime_catalog
assert CORE_RELEASE=='3.54.0';assert CONTRACT_VERSION=='sc.core.python-runtime.v1';assert RUNTIME_ID=='sc-runtime-python';assert ADAPTER_ID=='adapter:sc-runtime-python';assert PYTHON_VERSION=='3.12.3';assert PYTHON_OPERATIONS==['descriptive_summary','linear_regression','matrix_multiply','standardize','bootstrap_mean_ci','token_frequency']
b=reference_runtime_bundle();assert b.registration.runtime_id==RUNTIME_ID;assert b.environment_package.environment_package_id=='environment-package:python-runtime:v1';assert b.security_policy.security_policy_id=='runtime-security-policy:python-runtime-standard:v1';assert b.reference_request.operation==PythonOperation.descriptive_summary;assert len(b.fingerprint())==64
c=contract_document();assert c['capabilities']['general_scientific'] is True;assert c['boundaries']['arbitrary_python_source'] is False;assert c['boundaries']['network_access_for_jobs'] is False
reg=REGISTRY.get(ADAPTER_ID);assert reg.runtime.runtime_id==RUNTIME_ID;assert reg.runtime.language=='python';assert reg.runtime.runtime_version=='3.12.3'
cat=reference_runtime_catalog();refs=[e.runtime_ref for e in cat.entries];assert refs[-1]==RUNTIME_ID and len(refs)==11
p={x.product_id.value:x for x in reference_product_profiles()};assert all(RUNTIME_ID in p[x].allowed_runtime_refs for x in ['workspace','research-lab','workbench'])
print('PASS - Platform Core v3.54.0 Python Runtime Core Integration')
print('CONTRACT=sc.core.python-runtime.v1')
print('RUNTIME_ID=sc-runtime-python')
print('ADAPTER_ID=adapter:sc-runtime-python')
print('OPERATIONS='+','.join(PYTHON_OPERATIONS))
print('UNIFIED_RUNTIME_CATALOG_ENTRIES=11')
print('ARBITRARY_PYTHON_SOURCE=false')
print('JOB_NETWORK_ACCESS=false')
print('RUNTIME_PACKAGE_INSTALL=false')
print('CORE_EXECUTES_PYTHON_JOBS=false')
