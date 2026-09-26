#!/usr/bin/env python3
from app.server import ADAPTER_ID,GFORTRAN_PACKAGE_VERSION,GFORTRAN_VERSION,OPERATIONS,PROVIDER_VERSION,RUNTIME_ID,adapter_descriptor,fortran_source,parse_native_output,validate_payload
p=validate_payload('dot_product',{'a':[1,2,3],'b':[4,5,6]})
s=fortran_source('dot_product',p)
d=adapter_descriptor()
assert d['adapter_id']==ADAPTER_ID and d['provider_id']==RUNTIME_ID and d['provider_version']==PROVIDER_VERSION
assert d['capabilities']==OPERATIONS and d['native_runtime_version']==GFORTRAN_VERSION and d['native_package_version']==GFORTRAN_PACKAGE_VERSION
assert 'dot_product(a,b)' in s and 'execute_command_line' not in s
assert parse_native_output('SC_RESULT scalar 3.2000000000000000E+001\n')['value']==32.0
assert d['boundaries']['arbitrary_fortran_source'] is False
print('PASS - Sustainable Catalyst Fortran Runtime v1.0.0 contract validation')
print(f'RUNTIME_ID={RUNTIME_ID}')
print(f'ADAPTER_ID={ADAPTER_ID}')
print(f'OPERATIONS={",".join(OPERATIONS)}')
