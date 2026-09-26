from pathlib import Path
import math
import pytest
from pydantic import ValidationError

from app.server import (
 ADAPTER_ID,GFORTRAN_PACKAGE_VERSION,GFORTRAN_VERSION,OPERATIONS,PROVIDER_VERSION,RUNTIME_ID,
 PrepareRequest,adapter_descriptor,finite_matrix,finite_vector,fortran_source,parse_native_output,validate_payload,
)

def test_identity():
 assert RUNTIME_ID=='sc-runtime-fortran'; assert ADAPTER_ID=='adapter:sc-runtime-fortran'; assert PROVIDER_VERSION=='1.0.0'
 assert GFORTRAN_VERSION=='13.3.0'; assert GFORTRAN_PACKAGE_VERSION=='13.3.0-6ubuntu2~24.04.1'

def test_operations(): assert OPERATIONS==['dot_product','matrix_multiply','trapezoidal_integral','central_difference','rk4_linear_step','heat_step_1d']

def test_vector_validation(): assert finite_vector([1,2.5],'x')==[1.0,2.5]
def test_vector_rejects_inf():
 with pytest.raises(ValueError): finite_vector([1,float('inf')],'x')
def test_matrix_validation(): assert finite_matrix([[1,2],[3,4]],'a')==[[1.0,2.0],[3.0,4.0]]
def test_matrix_rectangular():
 with pytest.raises(ValueError): finite_matrix([[1,2],[3]],'a')

def test_dot_payload(): assert validate_payload('dot_product',{'a':[1,2],'b':[3,4]})['a']==[1.0,2.0]
def test_dot_length_mismatch():
 with pytest.raises(ValueError): validate_payload('dot_product',{'a':[1],'b':[2,3]})
def test_matrix_payload(): validate_payload('matrix_multiply',{'a':[[1,2]],'b':[[3],[4]]})
def test_matrix_mismatch():
 with pytest.raises(ValueError): validate_payload('matrix_multiply',{'a':[[1,2]],'b':[[3,4]]})
def test_trapezoid_payload(): validate_payload('trapezoidal_integral',{'x':[0,1,2],'y':[0,1,4]})
def test_trapezoid_increasing():
 with pytest.raises(ValueError): validate_payload('trapezoidal_integral',{'x':[0,0,1],'y':[0,1,2]})
def test_central_difference(): validate_payload('central_difference',{'x':[0,1,2],'y':[0,1,4],'index':1})
def test_central_boundary_rejected():
 with pytest.raises(ValueError): validate_payload('central_difference',{'x':[0,1,2],'y':[0,1,4],'index':0})
def test_rk4(): validate_payload('rk4_linear_step',{'y':1,'h':0.1,'a':2,'b':0})
def test_rk4_zero_step():
 with pytest.raises(ValueError): validate_payload('rk4_linear_step',{'y':1,'h':0,'a':2,'b':0})
def test_heat(): validate_payload('heat_step_1d',{'u':[0,1,0],'alpha_dt_dx2':0.25})
def test_heat_stability_bound():
 with pytest.raises(ValueError): validate_payload('heat_step_1d',{'u':[0,1,0],'alpha_dt_dx2':0.6})

@pytest.mark.parametrize('op,payload,needle',[('dot_product',{'a':[1,2,3],'b':[4,5,6]},'dot_product(a,b)'),('matrix_multiply',{'a':[[1,2]],'b':[[3],[4]]},'matmul(a,b)'),('trapezoidal_integral',{'x':[0,1,2],'y':[0,1,4]},'0.5_real64'),('central_difference',{'x':[0,1,2],'y':[0,1,4],'index':1},'value = (y(3)-y(1))/(x(3)-x(1))'),('rk4_linear_step',{'y':1,'h':0.1,'a':2,'b':0},'k4 ='),('heat_step_1d',{'u':[0,1,0],'alpha_dt_dx2':0.25},'next(i)=u(i)+r')])
def test_generated_source(op,payload,needle):
 s=fortran_source(op,payload); assert 'program sc_fortran_job' in s; assert needle in s; assert 'execute_command_line' not in s

def test_parse_scalar(): assert parse_native_output('SC_RESULT scalar 3.2000000000000000E+001\n')['value']==32.0
def test_parse_vector(): assert parse_native_output('SC_RESULT vector 3\n0\n0.5\n0\n')['values']==[0.0,0.5,0.0]
def test_parse_matrix(): assert parse_native_output('SC_RESULT matrix 2 2\n1\n2\n3\n4\n')['values']==[[1.0,2.0],[3.0,4.0]]
def test_prepare_valid(): assert PrepareRequest(operation='dot_product',payload={'a':[1,2],'b':[3,4]}).operation=='dot_product'
def test_prepare_invalid():
 with pytest.raises(ValidationError): PrepareRequest(operation='unknown',payload={})
def test_adapter_identity():
 d=adapter_descriptor(); assert d['adapter_id']==ADAPTER_ID; assert d['provider_id']==RUNTIME_ID; assert d['language']=='fortran'
def test_adapter_boundaries():
 b=adapter_descriptor()['boundaries']; assert b['arbitrary_fortran_source'] is False; assert b['shell_execution'] is False; assert b['runtime_package_install'] is False; assert b['provider_managed_compilation'] is True
