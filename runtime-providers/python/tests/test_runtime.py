import json, shutil, sys, tempfile
from pathlib import Path
import pytest
from pydantic import ValidationError
from app.server import *

def test_identity(): assert RUNTIME_ID=='sc-runtime-python' and ADAPTER_ID=='adapter:sc-runtime-python' and VERSION=='1.0.0'
def test_ops(): assert OPERATIONS==['descriptive_summary','linear_regression','matrix_multiply','standardize','bootstrap_mean_ci','token_frequency']
def test_summary_valid(): assert validate_payload('descriptive_summary',{'values':[1,2]})['values']==[1.0,2.0]
def test_summary_empty():
    with pytest.raises(ValueError): validate_payload('descriptive_summary',{'values':[]})
def test_regression(): assert validate_payload('linear_regression',{'x':[1,2],'y':[2,4]})['x']==[1.0,2.0]
def test_regression_bad_len():
    with pytest.raises(ValueError): validate_payload('linear_regression',{'x':[1,2],'y':[2]})
def test_regression_zero_var():
    with pytest.raises(ValueError): validate_payload('linear_regression',{'x':[1,1],'y':[2,3]})
def test_matrix(): assert validate_payload('matrix_multiply',{'matrix_a':[[1,2]],'matrix_b':[[3],[4]]})['matrix_a'][0]==[1.0,2.0]
def test_matrix_bad():
    with pytest.raises(ValueError): validate_payload('matrix_multiply',{'matrix_a':[[1,2]],'matrix_b':[[1,2]]})
def test_standardize(): assert validate_payload('standardize',{'values':[1,2,3]})['values'][1]==2.0
def test_standardize_zero_var():
    with pytest.raises(ValueError): validate_payload('standardize',{'values':[1,1]})
def test_bootstrap():
    p=validate_payload('bootstrap_mean_ci',{'values':[1,2,3],'iterations':100,'confidence':.95,'seed':7});assert p['seed']==7 and p['iterations']==100
def test_bootstrap_bad_iterations():
    with pytest.raises(ValueError): validate_payload('bootstrap_mean_ci',{'values':[1,2],'iterations':10})
def test_token_frequency(): assert validate_payload('token_frequency',{'text':'A a b','top_k':2})['lowercase'] is True
def test_token_empty():
    with pytest.raises(ValueError): validate_payload('token_frequency',{'text':''})
def test_source_is_bounded():
    s=generated_source('descriptive_summary',{'values':[1,2]});assert 'input.json' in s and 'eval(' not in s and 'exec(' not in s
def test_prepare_model(): PrepareRequest(operation='descriptive_summary',payload={'values':[1,2]})
def test_prepare_bad():
    with pytest.raises(ValidationError): PrepareRequest(operation='descriptive_summary',payload={})
def test_adapter():
    d=adapter_descriptor();assert d['language']=='python' and d['boundaries']['arbitrary_python_source'] is False and d['boundaries']['runtime_package_install'] is False and d['boundaries']['job_network_access'] is False
def test_generated_summary_exec(tmp_path,monkeypatch):
    monkeypatch.setattr(sys.modules[__name__], 'PYTHON_BIN', sys.executable, raising=False)
def test_reference_python_can_execute_program(tmp_path):
    src=generated_source('descriptive_summary',{'values':[1,2,3]});(tmp_path/'program.py').write_text(src);(tmp_path/'input.json').write_text(json.dumps({'operation':'descriptive_summary','payload':{'values':[1,2,3]}}));cp=subprocess.run([sys.executable,'-I','-S',str(tmp_path/'program.py')],cwd=tmp_path,text=True,capture_output=True);assert cp.returncode==0;d=json.loads((tmp_path/'result.json').read_text());assert d['mean']==2.0
def test_regression_program(tmp_path):
    src=generated_source('linear_regression',{'x':[1,2,3],'y':[2,4,6]});(tmp_path/'program.py').write_text(src);(tmp_path/'input.json').write_text(json.dumps({'operation':'linear_regression','payload':{'x':[1,2,3],'y':[2,4,6]}}));subprocess.run([sys.executable,'-I','-S',str(tmp_path/'program.py')],cwd=tmp_path,check=True);d=json.loads((tmp_path/'result.json').read_text());assert abs(d['slope']-2)<1e-12 and abs(d['r_squared']-1)<1e-12
def test_matrix_program(tmp_path):
    src=generated_source('matrix_multiply',{'matrix_a':[[1,2]],'matrix_b':[[3],[4]]});(tmp_path/'program.py').write_text(src);(tmp_path/'input.json').write_text(json.dumps({'operation':'matrix_multiply','payload':{'matrix_a':[[1,2]],'matrix_b':[[3],[4]]}}));subprocess.run([sys.executable,'-I','-S',str(tmp_path/'program.py')],cwd=tmp_path,check=True);assert json.loads((tmp_path/'result.json').read_text())['matrix']==[[11]]
def test_standardize_program(tmp_path):
    src=generated_source('standardize',{'values':[1,2,3]});(tmp_path/'program.py').write_text(src);(tmp_path/'input.json').write_text(json.dumps({'operation':'standardize','payload':{'values':[1,2,3]}}));subprocess.run([sys.executable,'-I','-S',str(tmp_path/'program.py')],cwd=tmp_path,check=True);d=json.loads((tmp_path/'result.json').read_text());assert abs(sum(d['values']))<1e-12
def test_bootstrap_deterministic(tmp_path):
    payload={'values':[1,2,3,4],'iterations':100,'confidence':.95,'seed':42};src=generated_source('bootstrap_mean_ci',payload);(tmp_path/'program.py').write_text(src);(tmp_path/'input.json').write_text(json.dumps({'operation':'bootstrap_mean_ci','payload':payload}));subprocess.run([sys.executable,'-I','-S',str(tmp_path/'program.py')],cwd=tmp_path,check=True);a=json.loads((tmp_path/'result.json').read_text());(tmp_path/'result.json').unlink();subprocess.run([sys.executable,'-I','-S',str(tmp_path/'program.py')],cwd=tmp_path,check=True);b=json.loads((tmp_path/'result.json').read_text());assert a==b and a['seed']==42
def test_token_program(tmp_path):
    payload={'text':'Alpha beta alpha','top_k':10,'lowercase':True};src=generated_source('token_frequency',payload);(tmp_path/'program.py').write_text(src);(tmp_path/'input.json').write_text(json.dumps({'operation':'token_frequency','payload':payload}));subprocess.run([sys.executable,'-I','-S',str(tmp_path/'program.py')],cwd=tmp_path,check=True);d=json.loads((tmp_path/'result.json').read_text());assert d['frequencies'][0]=={'count':2,'token':'alpha'}
def test_artifact_hash(): assert len(sha256_bytes(b'abc'))==64
