import shutil
import subprocess
import pytest
from app.server import OPERATIONS,RUNTIME_ID,ADAPTER_ID,adapter_descriptor,build_source,validate_payload

def operational_jdk():
    javac = shutil.which('javac')
    java = shutil.which('java')
    if not javac or not java:
        return None, None
    try:
        c = subprocess.run([javac, '-version'], capture_output=True, text=True, timeout=10)
        r = subprocess.run([java, '-version'], capture_output=True, text=True, timeout=10)
    except Exception:
        return None, None
    if c.returncode != 0 or r.returncode != 0:
        return None, None
    return javac, java

JAVAC_OK, JAVA_OK = operational_jdk()

def test_identity(): assert RUNTIME_ID=='sc-runtime-jvm' and ADAPTER_ID=='adapter:sc-runtime-jvm'
def test_operations(): assert OPERATIONS==['jvm_runtime_info','parallel_sum','parallel_map_affine','matrix_row_sums','graph_bfs','batch_sha256']
def test_parallel_sum_source():
    s=build_source('parallel_sum',{'values':[1,2,3]});assert 'parallel().sum()' in s and 'new double[]{1.0,2.0,3.0}' in s
def test_affine_source(): assert 'parallel().map' in build_source('parallel_map_affine',{'values':[1,2],'scale':2,'offset':1})
def test_matrix_source(): assert 'mapToDouble' in build_source('matrix_row_sums',{'matrix':[[1,2],[3,4]]})
def test_bfs_source(): assert 'ArrayDeque' in build_source('graph_bfs',{'adjacency_matrix':[[0,1],[1,0]],'source_index':0})
def test_sha_source(): assert 'MessageDigest.getInstance("SHA-256")' in build_source('batch_sha256',{'strings':['abc']})
def test_bad_graph():
    with pytest.raises(ValueError): validate_payload('graph_bfs',{'adjacency_matrix':[[0,2],[1,0]],'source_index':0})
def test_bad_matrix():
    with pytest.raises(ValueError): validate_payload('matrix_row_sums',{'matrix':[[1,2],[3]]})
def test_adapter():
    d=adapter_descriptor();assert d['runtime_kind']=='execution-target';assert d['boundaries']['arbitrary_jvm_bytecode'] is False;assert d['boundaries']['caller_classpath'] is False
@pytest.mark.skipif(not (JAVAC_OK and JAVA_OK),reason='Operational JDK unavailable; production deployment performs mandatory OpenJDK 21 validation')
def test_native_parallel_sum(monkeypatch,tmp_path):
    import app.server as s
    monkeypatch.setattr(s,'WORK_ROOT',tmp_path/'work');monkeypatch.setattr(s,'ARTIFACT_ROOT',tmp_path/'art');monkeypatch.setattr(s,'JAVAC',JAVAC_OK);monkeypatch.setattr(s,'JAVA',JAVA_OK)
    out,arts=s.execute_program('jvm-run:test','parallel_sum',{'values':[1,2,3,4,5]},60,128);assert out['result']['sum']==15.0;assert len(arts)>=4
@pytest.mark.skipif(not (JAVAC_OK and JAVA_OK),reason='Operational JDK unavailable; production deployment performs mandatory OpenJDK 21 validation')
def test_native_sha(monkeypatch,tmp_path):
    import app.server as s
    monkeypatch.setattr(s,'WORK_ROOT',tmp_path/'work');monkeypatch.setattr(s,'ARTIFACT_ROOT',tmp_path/'art');monkeypatch.setattr(s,'JAVAC',JAVAC_OK);monkeypatch.setattr(s,'JAVA',JAVA_OK)
    out,_=s.execute_program('jvm-run:sha','batch_sha256',{'strings':['abc']},60,128);assert out['result']['sha256'][0]=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
