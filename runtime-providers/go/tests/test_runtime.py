import hashlib,pytest
from pydantic import ValidationError
from app.server import *
def test_identity(): assert RUNTIME_ID=='sc-runtime-go' and ADAPTER_ID=='adapter:sc-runtime-go'
def test_ops(): assert OPERATIONS==['parallel_sum','parallel_map_affine','concurrent_histogram','parallel_matrix_row_sums','parallel_graph_degrees','batch_sha256']
def test_sum_valid(): assert validate_payload('parallel_sum',{'values':[1,2],'workers':2})['values']==[1.0,2.0]
def test_workers_bad():
    with pytest.raises(ValueError):validate_payload('parallel_sum',{'values':[1],'workers':65})
def test_affine(): assert validate_payload('parallel_map_affine',{'values':[1],'scale':2,'offset':1,'workers':1})['scale']==2.0
def test_hist(): assert validate_payload('concurrent_histogram',{'values':[1,2],'bins':2,'minimum':0,'maximum':2,'workers':1})['bins']==2
def test_hist_bad():
    with pytest.raises(ValueError):validate_payload('concurrent_histogram',{'values':[1],'bins':0,'minimum':0,'maximum':1})
def test_matrix(): assert len(validate_payload('parallel_matrix_row_sums',{'matrix':[[1,2],[3,4]],'workers':2})['matrix'])==2
def test_matrix_bad():
    with pytest.raises(ValueError):validate_payload('parallel_matrix_row_sums',{'matrix':[[1],[1,2]]})
def test_graph(): assert validate_payload('parallel_graph_degrees',{'adjacency_matrix':[[0,1],[1,0]],'workers':2})['adjacency_matrix'][0][1]==1
def test_graph_bad():
    with pytest.raises(ValueError):validate_payload('parallel_graph_degrees',{'adjacency_matrix':[[0,2],[1,0]]})
def test_hash(): assert validate_payload('batch_sha256',{'texts':['abc'],'workers':1})['texts']==['abc']
def test_source_sum(): assert 'go func' in generated_source('parallel_sum',{'values':[1,2,3],'workers':2}) and 'SC_RESULT scalar' in generated_source('parallel_sum',{'values':[1],'workers':1})
def test_source_affine(): assert 'sync' in generated_source('parallel_map_affine',{'values':[1],'scale':2,'offset':1,'workers':1})
def test_source_hist(): assert 'locals' in generated_source('concurrent_histogram',{'values':[1],'bins':2,'minimum':0,'maximum':2,'workers':1})
def test_source_matrix(): assert 'jobs:=make(chan int)' in generated_source('parallel_matrix_row_sums',{'matrix':[[1,2]],'workers':1})
def test_source_graph(): assert 'SC_RESULT int_vector' in generated_source('parallel_graph_degrees',{'adjacency_matrix':[[0]],'workers':1})
def test_source_hash(): assert 'crypto/sha256' in generated_source('batch_sha256',{'texts':['abc'],'workers':1})
def test_parse_scalar(): assert parse_output('SC_RESULT scalar 3.5\n')['value']==3.5
def test_parse_vector(): assert parse_output('SC_RESULT vector 2\n1\n2\n')['values']==[1.0,2.0]
def test_parse_int_vector(): assert parse_output('SC_RESULT int_vector 2\n1\n2\n')['values']==[1,2]
def test_parse_strings(): assert parse_output('SC_RESULT string_vector 1\nabc\n')['values']==['abc']
def test_prepare_model(): PrepareRequest(operation='parallel_sum',payload={'values':[1,2]})
def test_prepare_bad():
    with pytest.raises(ValidationError):PrepareRequest(operation='parallel_sum',payload={})
def test_adapter():
    d=adapter_descriptor();assert d['language']=='go' and d['boundaries']['arbitrary_go_source'] is False and d['boundaries']['go_module_download'] is False
def test_sha_reference(): assert hashlib.sha256(b'abc').hexdigest()=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
