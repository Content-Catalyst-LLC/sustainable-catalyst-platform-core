import pytest
from pydantic import ValidationError
from app.server import *
def test_identity(): assert RUNTIME_ID=="sc-runtime-cpp" and ADAPTER_ID=="adapter:sc-runtime-cpp"
def test_ops(): assert len(OPERATIONS)==6
def test_map(): assert OPERATION_LANGUAGE["dot_product"]=="c11" and OPERATION_LANGUAGE["matrix_multiply"]=="cpp17"
def test_dot(): assert validate_payload("dot_product",{"a":[1,2],"b":[3,4]})["a"]==[1.0,2.0]
def test_dot_bad():
 with pytest.raises(ValueError): validate_payload("dot_product",{"a":[1],"b":[2,3]})
def test_matrix(): assert validate_payload("matrix_multiply",{"a":[[1,2]],"b":[[3],[4]]})["b"][1][0]==4.0
def test_interp(): assert validate_payload("linear_interpolation",{"x":[0,1],"y":[0,2],"query_x":.5})["query_x"]==.5
def test_poly(): assert validate_payload("polynomial_evaluate",{"coefficients":[1,2,3],"x":2})["x"]==2.0
def test_fir(): assert validate_payload("fir_filter",{"signal":[1,2],"kernel":[.5]})["kernel"]==[.5]
def test_graph(): assert validate_payload("dijkstra_shortest_path",{"adjacency":[[0,1],[1,0]],"source":0,"target":1})["target"]==1
@pytest.mark.parametrize("op,payload",[("dot_product",{"a":[1],"b":[2]}),("matrix_multiply",{"a":[[1]],"b":[[2]]}),("linear_interpolation",{"x":[0,1],"y":[0,2],"query_x":.5}),("polynomial_evaluate",{"coefficients":[1,2],"x":2}),("fir_filter",{"signal":[1,2],"kernel":[1]}),("dijkstra_shortest_path",{"adjacency":[[0,1],[1,0]],"source":0,"target":1})])
def test_source(op,payload):
 lang,src=generated_source(op,payload);assert "main" in src and "SC_RESULT" in src and lang in {"c11","cpp17"}
def test_parse_scalar(): assert parse_output("SC_RESULT scalar 3.5\n")["value"]==3.5
def test_parse_vector(): assert parse_output("SC_RESULT vector 2\n1\n2\n")["values"]==[1.0,2.0]
def test_parse_matrix(): assert parse_output("SC_RESULT matrix 1 2\n1\n2\n")["values"]==[[1.0,2.0]]
def test_adapter():
 d=adapter_descriptor();assert d["language_profiles"]==["c11","cpp17"] and d["boundaries"]["arbitrary_c_cpp_source"] is False
def test_prepare(): assert PrepareRequest(operation="dot_product",payload={"a":[1],"b":[2]}).optimization_level==2
def test_prepare_bad():
 with pytest.raises(ValidationError): PrepareRequest(operation="shell",payload={})

def test_version_descriptor():
 d=version();assert d['runtime_id']==RUNTIME_ID and d['version']==PROVIDER_VERSION and d['gcc_version']=='13.3.0'

def test_capabilities_descriptor():
 d=capabilities();assert d['operations']==OPERATIONS and d['language_profiles']==['c11','cpp17']

def test_adapter_lifecycle_methods_complete():
 d=adapter_descriptor();assert d['lifecycle_methods']==['health','version','capabilities','prepare','execute','cancel','inspect','collect_results','collect_artifacts','diagnose']

def test_prepare_records_run():
 out=prepare(PrepareRequest(operation='dot_product',payload={'a':[1,2],'b':[3,4]}));assert out['status']=='prepared' and out['run_id'] in RUNS

def test_inspect_prepared_run():
 out=prepare(PrepareRequest(operation='dot_product',payload={'a':[1],'b':[2]}));d=inspect_run(RunRequest(run_id=out['run_id']));assert d['status']=='prepared' and d['operation']=='dot_product'

def test_cancel_prepared_run():
 out=prepare(PrepareRequest(operation='dot_product',payload={'a':[1],'b':[2]}));d=cancel(RunRequest(run_id=out['run_id']));assert d['status']=='cancelled'

def test_collect_results_before_execution():
 out=prepare(PrepareRequest(operation='dot_product',payload={'a':[1],'b':[2]}));d=collect_results(RunRequest(run_id=out['run_id']));assert d['result'] is None

def test_collect_artifacts_before_execution():
 out=prepare(PrepareRequest(operation='dot_product',payload={'a':[1],'b':[2]}));d=collect_artifacts(RunRequest(run_id=out['run_id']));assert d['artifacts']==[]

def test_diagnose_prepared_run_reports_profile():
 out=prepare(PrepareRequest(operation='matrix_multiply',payload={'a':[[1]],'b':[[2]]}));d=diagnose(RunRequest(run_id=out['run_id']));assert d['language_profile']=='cpp17'
