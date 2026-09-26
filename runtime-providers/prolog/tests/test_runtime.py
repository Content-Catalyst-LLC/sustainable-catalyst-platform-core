import pytest
from pydantic import ValidationError
from app.server import ADAPTER_ID,OPERATIONS,RUNTIME_ID,PrepareRequest,adapter_descriptor,build_program,validate_payload

def test_identity(): assert RUNTIME_ID=="sc-runtime-prolog" and ADAPTER_ID=="adapter:sc-runtime-prolog"
def test_operations(): assert OPERATIONS==["relation_reachable","relation_paths_bounded","transitive_closure","contradiction_scan","temporal_consistency","graph_coloring"]
def test_reachable_program():
    s=build_program("relation_reachable",{"edges":[{"source":"a","target":"b"},{"source":"b","target":"c"}],"source":"a","target":"c"});assert "reach(a,c)" in s and "edge(a,b)." in s
def test_paths_program(): assert "path(a,c,4" in build_program("relation_paths_bounded",{"edges":[{"source":"a","target":"b"},{"source":"b","target":"c"}],"source":"a","target":"c","max_depth":4})
def test_closure_program(): assert "findall([X,Y],reach(X,Y)" in build_program("transitive_closure",{"edges":[{"source":"a","target":"b"}]})
def test_contradiction_program():
    s=build_program("contradiction_scan",{"assertions":["claim_a","claim_b"],"negations":["claim_b"]});assert "assertion(claim_b)." in s and "negation(claim_b)." in s
def test_temporal_program(): assert "precedes(X,X)" in build_program("temporal_consistency",{"temporal_edges":[{"source":"event_a","target":"event_b"}]})
def test_coloring_program():
    s=build_program("graph_coloring",{"vertex_count":3,"max_colors":3,"undirected_edges":[[0,1],[1,2],[0,2]]});assert "library(clpfd)" in s and "C ins 1..3" in s
def test_bad_identifier():
    with pytest.raises(ValueError): validate_payload("relation_reachable",{"edges":[{"source":"a');halt.","target":"b"}],"source":"a","target":"b"})
def test_bad_depth():
    with pytest.raises(ValueError): validate_payload("relation_paths_bounded",{"edges":[{"source":"a","target":"b"}],"source":"a","target":"b","max_depth":99})
def test_bad_coloring():
    with pytest.raises(ValueError): validate_payload("graph_coloring",{"vertex_count":2,"max_colors":2,"undirected_edges":[[0,2]]})
def test_prepare_model(): PrepareRequest(operation="contradiction_scan",payload={"assertions":["claim_a"],"negations":["claim_a"]})
def test_prepare_bad():
    with pytest.raises(ValidationError): PrepareRequest(operation="contradiction_scan",payload={})
def test_adapter_boundaries():
    a=adapter_descriptor();assert a["boundaries"]["arbitrary_prolog_source"] is False;assert a["boundaries"]["runtime_package_install"] is False
