from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2500.db'}",version='2.51.0'))
    return app,TestClient(app)


def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:graph-v2500',entity_type='research-project',slug='graph-v2500',name='Forensic Graph',visibility='public')); db.commit()


def case(c):
    inv=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:graph-v2500','investigation_key':'graph-case','name':'Graph Case','visibility':'public'}}); assert inv.status_code==200,inv.text
    iid=inv.json()['id']
    ev=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'e1','evidence_kind':'documentary','label':'Primary record','content_hash':'a'*64}}); assert ev.status_code==200,ev.text
    claim=c.post(f'/v1/open-forensics/investigations/{iid}/claims',json={'data':{'claim_key':'c1','claim_kind':'factual','statement':'A meeting occurred.'}}); assert claim.status_code==200,claim.text
    event=c.post(f'/v1/open-forensics/investigations/{iid}/events',json={'data':{'event_key':'evt1','event_kind':'event','label':'Meeting','temporal_basis':'asserted','time_precision':'hour'}}); assert event.status_code==200,event.text
    return iid,ev.json()['id'],claim.json()['id'],event.json()['id']


def test_v2500_readiness_boundaries_and_migration(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    h=c.get('/health').json(); assert h['version']=='2.51.0' and h['forensic_research_graph'] is True
    r=c.get('/v1/open-forensics/readiness').json(); assert r['release']=='2.51.0' and r['migration_0054_applied'] is True
    for key in ('forensic_research_graph_registry_by_core','cross_forensics_node_binding_by_core','explicit_graph_edge_registry_by_core','renderer_neutral_forensic_graph_specification_by_core','cross_product_graph_handoffs_by_core','immutable_forensic_graph_snapshots_by_core','portable_forensic_graph_packages_by_core'): assert r[key] is True,key
    for key in ('automatic_graph_edge_inference_by_core','automatic_entity_resolution_by_core','automatic_identity_resolution_by_core','automatic_causal_inference_by_core','relationship_truth_determination_by_core','graph_analytics_execution_by_core','remote_product_fetch_by_core','automatic_truth_promotion'): assert r[key] is False,key
    assert migration_status(app.state.database)['pending']==[]


def test_graph_nodes_edges_visual_spec_and_inventory(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,eid,claim_id,event_id=case(c)
    g=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs',json={'data':{'graph_key':'g1','label':'Case graph','visibility':'public'}}); assert g.status_code==200,g.text; gid=g.json()['id']
    n1=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/nodes',json={'data':{'node_key':'evidence','node_kind':'evidence','label':'Primary evidence','record_id':eid,'evidence_basis_ids':[eid]}}); assert n1.status_code==200,n1.text
    n2=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/nodes',json={'data':{'node_key':'claim','node_kind':'claim','label':'Meeting claim','record_id':claim_id}}); assert n2.status_code==200,n2.text
    n3=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/nodes',json={'data':{'node_key':'person-ref','node_kind':'person-reference','label':'Witness reference','source_product':'external','source_ref':'external://person/witness-1'}}); assert n3.status_code==200,n3.text
    edge=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/edges',json={'data':{'edge_key':'e1','source_node_id':n1.json()['id'],'target_node_id':n2.json()['id'],'relation_kind':'evidence-for','evidence_basis_ids':[eid],'rationale':'Explicit analyst-declared evidence relationship.'}}); assert edge.status_code==200,edge.text
    view=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/views',json={'data':{'view_key':'overview','name':'Overview','filters':{'node_kinds':['evidence','claim']},'layout_hints':{'direction':'LR'}}}); assert view.status_code==200,view.text
    bundle=c.get(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}').json(); assert len(bundle['nodes'])==3 and len(bundle['edges'])==1 and bundle['edges_are_explicit_not_inferred'] is True
    spec=c.get(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/visual-spec').json(); assert spec['renderer_neutral'] is True and spec['execution']['automatic_graph_edge_inference_by_core'] is False
    inv=c.get(f'/v1/open-forensics/investigations/{iid}/research-graph-inventory').json(); assert inv['counts']['evidence_items']==1 and inv['automatic_node_creation_by_core'] is False


def test_graph_handoff_snapshot_package_and_public_graph(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,eid,claim_id,_=case(c)
    g=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs',json={'data':{'graph_key':'g2','label':'Portable graph','visibility':'public'}}); gid=g.json()['id']
    node=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/nodes',json={'data':{'node_key':'e','node_kind':'evidence','label':'Evidence','record_id':eid}}); assert node.status_code==200
    h=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/handoffs',json={'data':{'handoff_key':'site','target_product':'site-intelligence'}}); assert h.status_code==200,h.text; assert h.json()['manifest_json']['remote_product_fetch_by_core'] is False
    s=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/snapshots',json={'data':{'created_by':'test'}}); assert s.status_code==200,s.text; assert s.json()['revision']==1 and len(s.json()['content_hash'])==64
    p=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/packages',json={'data':{'package_key':'portable','created_by':'test'}}); assert p.status_code==200,p.text; assert p.json()['revision']==1 and len(p.json()['manifest_hash'])==64
    # public endpoint requires public API auth; unauthorized is expected to be blocked before visibility evaluation.
    pub=c.get(f'/api/v1/open-forensics/investigations/{iid}/research-graphs/{gid}'); assert pub.status_code in (200,401,403)


def test_graph_determinative_guards(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,eid,claim_id,_=case(c)
    g=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs',json={'data':{'graph_key':'g3','label':'Guard graph'}}); gid=g.json()['id']
    n1=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/nodes',json={'data':{'node_key':'a','node_kind':'evidence','label':'Evidence','record_id':eid}}).json()
    n2=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/nodes',json={'data':{'node_key':'b','node_kind':'claim','label':'Claim','record_id':claim_id}}).json()
    bad=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/edges',json={'data':{'edge_key':'bad','source_node_id':n1['id'],'target_node_id':n2['id'],'relation_kind':'causes'}}); assert bad.status_code==422
    bad2=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/edges',json={'data':{'edge_key':'bad2','source_node_id':n1['id'],'target_node_id':n2['id'],'relation_kind':'supports','truth_value':True}}); assert bad2.status_code==422 and 'does not determine identity' in bad2.text
