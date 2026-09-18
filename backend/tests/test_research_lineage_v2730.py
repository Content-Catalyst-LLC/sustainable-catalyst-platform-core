from fastapi.testclient import TestClient
from app.main import create_app

def make_project(c):
    r=c.post('/v1/research/projects',json={'data':{'title':'Carbon Lineage Study','project_key':'carbon-lineage','visibility':'public'}})
    assert r.status_code==200,r.text
    return r.json()['project']['id']

def test_readiness_boundaries(tmp_path,monkeypatch):
    monkeypatch.setenv('SC_CORE_DATABASE_URL',f"sqlite:///{tmp_path/'a.db'}")
    c=TestClient(create_app()); d=c.get('/v1/research/lineage/readiness').json()
    assert d['release']=='2.73.0' and d['migration_0077_applied'] is True
    assert d['contract']=='sc.research.lineage-graph.v1'
    assert d['deterministic_declared_trace_by_core'] is True
    assert d['infer_missing_edges_by_core'] is False and d['infer_causality_by_core'] is False
    assert d['execute_analysis_by_core'] is False and d['promote_truth_by_core'] is False

def test_lineage_roundtrip_trace_and_snapshots(tmp_path,monkeypatch):
    monkeypatch.setenv('SC_CORE_DATABASE_URL',f"sqlite:///{tmp_path/'b.db'}")
    c=TestClient(create_app()); pid=make_project(c)
    r=c.post(f'/v1/research/lineage/projects/{pid}/graphs',json={'data':{'graph_key':'main','title':'Finding lineage','root_refs':['finding:1']}}); assert r.status_code==200,r.text; gid=r.json()['id']
    ids={}
    for key,typ,label,product in [('finding','finding','Finding','lab'),('run','analysis_run','Analysis run','lab'),('model','model','Model','workbench'),('dataset','dataset','Dataset','workspace'),('source','source','Original source','library')]:
        x=c.post(f'/v1/research/lineage/graphs/{gid}/nodes',json={'data':{'node_key':key,'node_type':typ,'label':label,'product_key':product,'product_ref':f'{typ}:{key}'}}); assert x.status_code==200,x.text; ids[key]=x.json()['id']
    edges=[('e1','finding','derived_from','run'),('e2','run','executed_with','model'),('e3','run','used_input','dataset'),('e4','dataset','derived_from','source')]
    for ek,a,pred,b in edges:
        x=c.post(f'/v1/research/lineage/graphs/{gid}/edges',json={'data':{'edge_key':ek,'source_node_id':ids[a],'predicate':pred,'target_node_id':ids[b]}}); assert x.status_code==200,x.text
    assert c.post(f'/v1/research/lineage/graphs/{gid}/activities',json={'data':{'activity_key':'analysis-1','activity_type':'analyze','product_key':'lab','input_node_ids':[ids['dataset']], 'output_node_ids':[ids['finding']], 'method_ref':'method:1','environment':{'runtime':'python'}}}).status_code==200
    assert c.post(f'/v1/research/lineage/graphs/{gid}/transformations',json={'data':{'transformation_key':'tx-1','source_node_id':ids['source'],'output_node_id':ids['dataset'],'operation':'clean-and-normalize','method_ref':'method:clean'}}).status_code==200
    assert c.post(f'/v1/research/lineage/graphs/{gid}/source-bindings',json={'data':{'binding_key':'src-1','node_id':ids['source'],'source_ref':'library:source-1','source_kind':'official-dataset','source_version':'2026','content_hash':'abc123'}}).status_code==200
    tr=c.post(f'/v1/research/lineage/graphs/{gid}/traces',json={'data':{'trace_key':'finding-to-source','start_node_id':ids['finding'],'end_node_id':ids['source'],'orientation':'outbound','purpose':'Where did this finding come from?'}}); assert tr.status_code==200,tr.text
    assert tr.json()['path_node_ids'][0]==ids['finding'] and tr.json()['path_node_ids'][-1]==ids['source'] and len(tr.json()['path_edge_ids'])==3
    s1=c.post(f'/v1/research/lineage/graphs/{gid}/snapshots',json={'data':{}}).json(); s2=c.post(f'/v1/research/lineage/graphs/{gid}/snapshots',json={'data':{}}).json(); assert s2['previous_snapshot_hash']==s1['content_hash']
    b=c.get(f'/v1/research/lineage/graphs/{gid}/bundle').json(); assert len(b['nodes'])==5 and len(b['edges'])==4 and len(b['source_bindings'])==1 and len(b['traces'])==1
    assert c.get(f'/api/v1/research/lineage/graphs/{gid}/bundle').status_code==401

def test_rejects_inference_and_undeclared_links(tmp_path,monkeypatch):
    monkeypatch.setenv('SC_CORE_DATABASE_URL',f"sqlite:///{tmp_path/'c.db'}")
    c=TestClient(create_app()); pid=make_project(c)
    r=c.post(f'/v1/research/lineage/projects/{pid}/graphs',json={'data':{'graph_key':'g','title':'Boundary','infer_causality_by_core':True}}); assert r.status_code==422
    r=c.post(f'/v1/research/lineage/projects/{pid}/graphs',json={'data':{'graph_key':'g','title':'Boundary'}}); gid=r.json()['id']
    a=c.post(f'/v1/research/lineage/graphs/{gid}/nodes',json={'data':{'node_key':'a','node_type':'finding','label':'A'}}).json()['id']
    b=c.post(f'/v1/research/lineage/graphs/{gid}/nodes',json={'data':{'node_key':'b','node_type':'source','label':'B'}}).json()['id']
    bad=c.post(f'/v1/research/lineage/graphs/{gid}/edges',json={'data':{'edge_key':'bad','source_node_id':a,'predicate':'proves_truth','target_node_id':b}}); assert bad.status_code==422
    no_path=c.post(f'/v1/research/lineage/graphs/{gid}/traces',json={'data':{'trace_key':'x','start_node_id':a,'end_node_id':b}}); assert no_path.status_code==422
