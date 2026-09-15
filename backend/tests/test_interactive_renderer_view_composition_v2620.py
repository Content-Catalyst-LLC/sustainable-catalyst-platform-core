from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def setup(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2620.db'}",version='2.62.0'))
    c=TestClient(app)
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:v2620',entity_type='research-project',slug='v2620',name='Visual Composition Project',visibility='public')); db.commit()
    sr=c.post('/v1/visual-runtime/scenes',json={'data':{'project_entity_id':'project:v2620','scene_key':'scene','name':'Scene','visibility':'public'}}); assert sr.status_code==200,sr.text
    sid=sr.json()['id']
    views=[]
    for key,kind in [('map','map'),('chart','chart')]:
        r=c.post(f'/v1/visual-runtime/scenes/{sid}/views',json={'data':{'view_key':key,'name':key.title(),'view_kind':kind}}); assert r.status_code==200,r.text; views.append(r.json()['id'])
    return app,c,sid,views


def test_v2620_readiness_and_migration(tmp_path):
    app,c,_,_=setup(tmp_path)
    r=c.get('/v1/visual-runtime/composition/readiness'); assert r.status_code==200,r.text
    d=r.json(); assert d['release']=='2.62.0' and d['migration_0066_applied'] is True
    assert migration_status(app.state.database)['pending']==[]
    assert d['view_composition_registry_by_core'] and d['renderer_capability_resolution_by_core']
    assert d['svg_canvas_webgl_drawing_by_core'] is False and d['gpu_execution_by_core'] is False


def test_renderer_composition_roundtrip_and_snapshot_chain(tmp_path):
    app,c,sid,views=setup(tmp_path)
    rr=c.post('/v1/visual-runtime/composition/renderers',json={'data':{'renderer_key':'browser-svg','name':'Browser SVG','renderer_kind':'svg','supported_view_kinds':['map','chart'],'capabilities':{'selection':True,'zoom':True}}}); assert rr.status_code==200,rr.text; rid=rr.json()['id']
    cr=c.post(f'/v1/visual-runtime/composition/scenes/{sid}/compositions',json={'data':{'composition_key':'analysis','name':'Analysis','composition_kind':'split','layout_spec':{'columns':2},'visibility':'public'}}); assert cr.status_code==200,cr.text; cid=cr.json()['id']
    for i,vid in enumerate(views):
        a=c.post(f'/v1/visual-runtime/composition/compositions/{cid}/assignments',json={'data':{'view_id':vid,'renderer_profile_id':rid,'slot_key':f'pane-{i+1}','order_index':i,'camera_state':{'zoom':1+i*.2}}}); assert a.status_code==200,a.text
    lg=c.post(f'/v1/visual-runtime/composition/compositions/{cid}/link-groups',json={'data':{'link_key':'linked','name':'Linked views','linked_view_ids':views,'propagation_policy':{'selection':True,'filter':True,'viewport':False}}}); assert lg.status_code==200,lg.text
    st=c.post(f'/v1/visual-runtime/composition/compositions/{cid}/interaction-states',json={'data':{'source_view_id':views[0],'state_kind':'selection','state':{'node_ids':['n1']},'propagation':{'targets':[views[1]]}}}); assert st.status_code==200,st.text
    rs=c.post(f'/v1/visual-runtime/composition/compositions/{cid}/renderer-resolutions',json={'data':{'view_id':views[0],'renderer_profile_id':rid}}); assert rs.status_code==200,rs.text and rs.json()['resolution_status']=='compatible'
    s1=c.post(f'/v1/visual-runtime/composition/compositions/{cid}/snapshots',json={'data':{'created_by':'test'}}); assert s1.status_code==200,s1.text
    s2=c.post(f'/v1/visual-runtime/composition/compositions/{cid}/snapshots',json={'data':{'created_by':'test'}}); assert s2.status_code==200,s2.text and s2.json()['previous_snapshot_hash']==s1.json()['content_hash']
    b=c.get(f'/v1/visual-runtime/composition/compositions/{cid}/bundle'); assert b.status_code==200,b.text
    d=b.json(); assert d['contract']=='sc.visual-runtime.composition.v1'; assert len(d['assignments'])==2 and len(d['link_groups'])==1 and len(d['snapshots'])==2


def test_cross_scene_and_core_execution_rejection(tmp_path):
    app,c,sid,views=setup(tmp_path)
    s2=c.post('/v1/visual-runtime/scenes',json={'data':{'project_entity_id':'project:v2620','scene_key':'other','name':'Other'}}).json()['id']
    v2=c.post(f'/v1/visual-runtime/scenes/{s2}/views',json={'data':{'view_key':'other','name':'Other','view_kind':'canvas'}}).json()['id']
    cr=c.post(f'/v1/visual-runtime/composition/scenes/{sid}/compositions',json={'data':{'composition_key':'c','name':'C'}}); cid=cr.json()['id']
    bad=c.post(f'/v1/visual-runtime/composition/compositions/{cid}/assignments',json={'data':{'view_id':v2}}); assert bad.status_code==422
    bad2=c.post('/v1/visual-runtime/composition/renderers',json={'data':{'renderer_key':'bad','name':'Bad','render_by_core':True}}); assert bad2.status_code==422
