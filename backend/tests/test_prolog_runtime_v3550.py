import pytest
from pydantic import ValidationError
from app.services.prolog_runtime import ADAPTER_ID,CONTRACT_VERSION,PROLOG_OPERATIONS,RUNTIME_ID,LogicEdge,PrologExecutionRequest,PrologLogicInput,PrologOperation,contract_document,reference_runtime_bundle,to_scientific_prolog_artifact

def test_identity(): assert CONTRACT_VERSION=="sc.core.prolog-runtime.v1" and RUNTIME_ID=="sc-runtime-prolog" and ADAPTER_ID=="adapter:sc-runtime-prolog"
def test_operations(): assert PROLOG_OPERATIONS==["relation_reachable","relation_paths_bounded","transitive_closure","contradiction_scan","temporal_consistency","graph_coloring"]
def test_reference():
    b=reference_runtime_bundle();assert b.registration.swi_prolog_version=="9.0.4";assert b.reference_request.operation==PrologOperation.relation_reachable;assert len(b.fingerprint())==64
def test_security():
    p=reference_runtime_bundle().security_policy;assert p.isolation_profile.arbitrary_code_allowed is False;assert p.isolation_profile.shell_allowed is False
def test_bad_identifier():
    with pytest.raises(ValidationError): LogicEdge(source="Bad",target="b")
def test_bad_depth():
    with pytest.raises(ValidationError): PrologExecutionRequest(prolog_request_id="r:x",operation=PrologOperation.relation_paths_bounded,inputs=PrologLogicInput(edges=[LogicEdge(source="a",target="b")],source="a",target="b",max_depth=13),computational_job_ref="job:x")
def test_coloring_validation():
    r=PrologExecutionRequest(prolog_request_id="r:c",operation=PrologOperation.graph_coloring,inputs=PrologLogicInput(vertex_count=3,max_colors=3,undirected_edges=[[0,1],[1,2],[0,2]]),computational_job_ref="job:c");assert r.inputs.vertex_count==3
def test_contract():
    d=contract_document();assert d["release"]=="3.55.0";assert d["capabilities"]["logic_constraint_reasoning"] is True;assert d["boundaries"]["core_certifies_truth"] is False
def test_artifact():
    a=to_scientific_prolog_artifact(reference_runtime_bundle());assert a["source_contract"]==CONTRACT_VERSION;assert a["metadata"]["runtime_id"]==RUNTIME_ID;assert len(a["content_sha256"])==64
