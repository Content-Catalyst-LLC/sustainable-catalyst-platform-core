from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity

def setup(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2640.db'}",version='2.64.0'));c=TestClient(app)
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:v2640',entity_type='research-project',slug='v2640',name='Linked Views Project',visibility='public'));db.commit()
    sid=c.post('/v1/visual-runtime/scenes',json={'data':{'project_entity_id':'project:v2640','scene_key':'scene','name':'Scene','visibility':'public'}}).json()['id']
    views=[]
    for key,kind in [('map','map'),('chart','chart')]:
        r=c.post(f'/v1/visual-runtime/scenes/{sid}/views',json={'data':{'view_key':key,'name':key.title(),'view_kind':kind}});assert r.status_code==200,r.text;views.append(r.json()['id'])
    cid=c.post(f'/v1/visual-runtime/composition/scenes/{sid}/compositions',json={'data':{'composition_key':'linked','name':'Linked','composition_kind':'linked','visibility':'public'}}).json()['id']
    for i,v in enumerate(views):
        r=c.post(f'/v1/visual-runtime/composition/compositions/{cid}/assignments',json={'data':{'view_id':v,'slot_key':f'p{i}'}});assert r.status_code==200,r.text
    lg=c.post(f'/v1/visual-runtime/composition/compositions/{cid}/link-groups',json={'data':{'link_key':'all','name':'All','linked_view_ids':views,'propagation_policy':{'selection':True,'filter':True}}});assert lg.status_code==200,lg.text
    gid=c.post('/v1/visual-runtime/grammar/specifications',json={'data':{'scene_id':sid,'composition_id':cid,'view_id':views[1],'grammar_key':'chart','name':'Chart grammar','visibility':'public'}}).json()['id']
    bid=c.post(f'/v1/visual-runtime/grammar/specifications/{gid}/data-bindings',json={'data':{'binding_key':'series','source_kind':'predictive','source_ref':'predictive:demo','fields':[{'name':'country','type':'nominal'},{'name':'value','type':'quantitative'}]}}).json()['id']
    return app,c,sid,views,cid,lg.json()['id'],gid,bid

def test_v2640_readiness_and_migration(tmp_path):
    app,c,*_=setup(tmp_path);r=c.get('/v1/visual-runtime/linked-views/readiness');assert r.status_code==200,r.text;d=r.json();assert d['release']=='2.64.0' and d['migration_0068_applied'] is True;assert migration_status(app.state.database)['pending']==[];assert d['cross_filter_predicate_registry_by_core'] and d['query_execution_by_core'] is False

def test_linked_views_cross_filter_roundtrip_snapshot_chain(tmp_path):
    app,c,sid,views,cid,lg,gid,bid=setup(tmp_path)
    p=c.post(f'/v1/visual-runtime/linked-views/compositions/{cid}/link-policies',json={'data':{'link_group_id':lg,'policy_key':'coordinated','name':'Coordinated','source_view_ids':[views[0]],'target_view_ids':[views[1]],'channels':['selection','filter','brush','highlight'],'propagation_mode':'one-way','policy':{'preserve_provenance':True}}});assert p.status_code==200,p.text;pid=p.json()['id']
    s=c.post(f'/v1/visual-runtime/linked-views/compositions/{cid}/selection-sets',json={'data':{'source_view_id':views[0],'selection_key':'countries','selection_kind':'set','selected_refs':['country:KEN'],'target_view_ids':[views[1]]}});assert s.status_code==200,s.text;sel=s.json()['id']
    f=c.post(f'/v1/visual-runtime/linked-views/compositions/{cid}/cross-filters',json={'data':{'source_view_id':views[1],'grammar_specification_id':gid,'data_binding_id':bid,'filter_key':'positive','predicate':{'field':'value','op':'>','value':0},'target_view_ids':[views[0]],'combine_mode':'and'}});assert f.status_code==200,f.text
    b=c.post(f'/v1/visual-runtime/linked-views/compositions/{cid}/brush-ranges',json={'data':{'source_view_id':views[1],'grammar_specification_id':gid,'data_binding_id':bid,'brush_key':'value-range','field_name':'value','channel':'x','range':{'min':10,'max':40},'target_view_ids':[views[0]]}});assert b.status_code==200,b.text
    h=c.post(f'/v1/visual-runtime/linked-views/compositions/{cid}/focus-highlights',json={'data':{'source_view_id':views[0],'state_key':'focus','focused_refs':['country:KEN'],'highlighted_refs':['country:UGA'],'target_view_ids':[views[1]],'style_contract':{'semantic':'emphasis'}}});assert h.status_code==200,h.text
    pr=c.post(f'/v1/visual-runtime/linked-views/compositions/{cid}/propagations',json={'data':{'link_policy_id':pid,'source_view_id':views[0],'target_view_id':views[1],'event_kind':'selection','source_record_kind':'selection-set','source_record_id':sel,'propagated_state':{'refs':['country:KEN']},'status':'external-applied','evidence':{'core_executed':False}}});assert pr.status_code==200,pr.text
    s1=c.post(f'/v1/visual-runtime/linked-views/compositions/{cid}/snapshots',json={'data':{'created_by':'test'}});assert s1.status_code==200,s1.text
    s2=c.post(f'/v1/visual-runtime/linked-views/compositions/{cid}/snapshots',json={'data':{'created_by':'test'}});assert s2.status_code==200,s2.text and s2.json()['previous_snapshot_hash']==s1.json()['content_hash']
    out=c.get(f'/v1/visual-runtime/linked-views/compositions/{cid}/bundle');assert out.status_code==200,out.text;d=out.json();assert d['contract']=='sc.visual-runtime.linked-views.v1';assert len(d['cross_filters'])==1 and len(d['snapshots'])==2 and len(d['propagation_records'])==1

def test_cross_composition_and_core_execution_rejection(tmp_path):
    app,c,sid,views,cid,lg,gid,bid=setup(tmp_path)
    other=c.post(f'/v1/visual-runtime/composition/scenes/{sid}/compositions',json={'data':{'composition_key':'other','name':'Other'}}).json()['id']
    bad=c.post(f'/v1/visual-runtime/linked-views/compositions/{other}/selection-sets',json={'data':{'source_view_id':views[0],'selection_key':'bad'}});assert bad.status_code==422
    bad2=c.post(f'/v1/visual-runtime/linked-views/compositions/{cid}/cross-filters',json={'data':{'source_view_id':views[0],'filter_key':'bad','predicate':{'field':'x'},'execute_query_by_core':True}});assert bad2.status_code==422
