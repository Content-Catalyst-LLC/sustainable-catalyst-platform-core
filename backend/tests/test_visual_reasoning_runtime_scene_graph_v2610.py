from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2610.db'}",version='2.61.0'))
    return app,TestClient(app)


def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:visual-v2610',entity_type='research-project',slug='visual-v2610',name='Visual Runtime Project',visibility='public'))
        db.add(Entity(id='entity:energy-demand',entity_type='research-variable',slug='energy-demand',name='Energy Demand',visibility='public'))
        db.commit()


def test_v2610_readiness_boundaries_and_migration(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    r=c.get('/v1/visual-runtime/readiness'); assert r.status_code==200,r.text
    d=r.json(); assert d['release']=='2.61.0' and d['migration_0065_applied'] is True
    assert migration_status(app.state.database)['pending']==[]
    for k in ('scene_registry_by_core','scene_graph_node_registry_by_core','scene_graph_edge_registry_by_core','scene_layer_registry_by_core','scene_annotation_registry_by_core','viewport_selection_state_by_core','cross_product_visual_bindings_by_core','immutable_scene_snapshots_by_core','renderer_neutral_scene_contract_by_core'):
        assert d[k] is True,k
    for k in ('layout_computation_by_core','canvas_svg_webgl_rendering_by_core','animation_execution_by_core','gpu_execution_by_core','hit_testing_by_core','visual_inference_by_core','automatic_visual_truth_promotion'):
        assert d[k] is False,k


def test_scene_graph_round_trip_view_state_binding_and_hash_chain(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    r=c.post('/v1/visual-runtime/scenes',json={'data':{'project_entity_id':'project:visual-v2610','scene_key':'energy-system','name':'Energy System','scene_kind':'system-map','coordinate_space':'abstract','visibility':'public','provenance':{'source':'test'}}})
    assert r.status_code==200,r.text; sid=r.json()['id']; assert r.json()['runtime_contract']=='sc.visual-runtime.scene.v1'
    la=c.post(f'/v1/visual-runtime/scenes/{sid}/layers',json={'data':{'layer_key':'model','name':'Model','layer_kind':'model','order_index':1,'style_hints':{'opacity':1}}}); assert la.status_code==200,la.text; lid=la.json()['id']
    n1=c.post(f'/v1/visual-runtime/scenes/{sid}/nodes',json={'data':{'layer_id':lid,'node_key':'demand','label':'Demand','node_kind':'variable','semantic_role':'input','source_entity_id':'entity:energy-demand','position':{'x':10,'y':20},'style_hints':{'shape':'circle'}}}); assert n1.status_code==200,n1.text
    n2=c.post(f'/v1/visual-runtime/scenes/{sid}/nodes',json={'data':{'layer_id':lid,'node_key':'emissions','label':'Emissions','node_kind':'variable','semantic_role':'output','position':{'x':160,'y':20}}}); assert n2.status_code==200,n2.text
    e=c.post(f'/v1/visual-runtime/scenes/{sid}/edges',json={'data':{'layer_id':lid,'edge_key':'demand-emissions','source_node_id':n1.json()['id'],'target_node_id':n2.json()['id'],'edge_kind':'causal','semantic_role':'influences','direction':'directed','confidence':0.8}}); assert e.status_code==200,e.text
    a=c.post(f'/v1/visual-runtime/scenes/{sid}/annotations',json={'data':{'node_id':n2.json()['id'],'annotation_kind':'uncertainty','text':'External uncertainty evidence applies.','anchor':{'placement':'north'}}}); assert a.status_code==200,a.text
    v=c.post(f'/v1/visual-runtime/scenes/{sid}/views',json={'data':{'view_key':'default','name':'Default','view_kind':'canvas','viewport':{'x':0,'y':0,'zoom':1.2},'selection':{'node_ids':[n1.json()['id']]},'layer_state':{'visible':[lid]},'interaction_state':{'mode':'inspect'},'renderer_hints':{'preferred_family':'webgl'}}}); assert v.status_code==200,v.text
    b=c.post(f'/v1/visual-runtime/scenes/{sid}/bindings',json={'data':{'node_id':n1.json()['id'],'binding_key':'demand-core','source_product':'core','source_kind':'entity','source_ref':'entity:energy-demand','binding_role':'data-source','contract_version':'core.entity.v1'}}); assert b.status_code==200,b.text
    s1=c.post(f'/v1/visual-runtime/scenes/{sid}/snapshots',json={'data':{'created_by':'test'}}); assert s1.status_code==200,s1.text and s1.json()['revision']==1 and len(s1.json()['content_hash'])==64
    s2=c.post(f'/v1/visual-runtime/scenes/{sid}/snapshots',json={'data':{'created_by':'test'}}); assert s2.status_code==200,s2.text and s2.json()['revision']==2 and s2.json()['previous_snapshot_hash']==s1.json()['content_hash']
    bundle=c.get(f'/v1/visual-runtime/scenes/{sid}/bundle'); assert bundle.status_code==200,bundle.text
    d=bundle.json(); assert d['contract']=='sc.visual-runtime.scene.v1'; assert len(d['nodes'])==2 and len(d['edges'])==1 and len(d['layers'])==1 and len(d['annotations'])==1 and len(d['views'])==1 and len(d['bindings'])==1 and len(d['snapshots'])==2
    assert d['views'][0]['viewport']['zoom']==1.2 and d['views'][0]['interaction_state']['mode']=='inspect'


def test_cross_scene_integrity_and_renderer_execution_rejection(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    def scene(key):
        r=c.post('/v1/visual-runtime/scenes',json={'data':{'project_entity_id':'project:visual-v2610','scene_key':key,'name':key,'visibility':'private'}}); assert r.status_code==200,r.text; return r.json()['id']
    s1,s2=scene('one'),scene('two')
    n1=c.post(f'/v1/visual-runtime/scenes/{s1}/nodes',json={'data':{'node_key':'a','label':'A'}}).json()['id']
    n2=c.post(f'/v1/visual-runtime/scenes/{s2}/nodes',json={'data':{'node_key':'b','label':'B'}}).json()['id']
    bad=c.post(f'/v1/visual-runtime/scenes/{s1}/edges',json={'data':{'edge_key':'bad','source_node_id':n1,'target_node_id':n2}}); assert bad.status_code==422
    bad2=c.post('/v1/visual-runtime/scenes',json={'data':{'project_entity_id':'project:visual-v2610','scene_key':'bad-render','name':'Bad','render_by_core':True}}); assert bad2.status_code==422 and 'does not fit' in bad2.text
    bad3=c.post(f'/v1/visual-runtime/scenes/{s1}/bindings',json={'data':{'node_id':n1,'binding_key':'missing','source_product':'core','source_kind':'entity','source_ref':'entity:missing'}}); assert bad3.status_code==422
