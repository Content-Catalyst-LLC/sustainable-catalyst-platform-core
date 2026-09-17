from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity

def setup(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2650.db'}",version='2.65.0'));c=TestClient(app)
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:v2650',entity_type='research-project',slug='v2650',name='Visual Query Project',visibility='public'));db.commit()
    sid=c.post('/v1/visual-runtime/scenes',json={'data':{'project_entity_id':'project:v2650','scene_key':'scene','name':'Scene','visibility':'public'}}).json()['id']
    views=[]
    for key,kind in [('map','map'),('chart','chart')]:
        r=c.post(f'/v1/visual-runtime/scenes/{sid}/views',json={'data':{'view_key':key,'name':key.title(),'view_kind':kind}});assert r.status_code==200,r.text;views.append(r.json()['id'])
    cid=c.post(f'/v1/visual-runtime/composition/scenes/{sid}/compositions',json={'data':{'composition_key':'explore','name':'Explore','composition_kind':'linked','visibility':'public'}}).json()['id']
    for i,v in enumerate(views):
        r=c.post(f'/v1/visual-runtime/composition/compositions/{cid}/assignments',json={'data':{'view_id':v,'slot_key':f'p{i}'}});assert r.status_code==200,r.text
    gid=c.post('/v1/visual-runtime/grammar/specifications',json={'data':{'scene_id':sid,'composition_id':cid,'view_id':views[1],'grammar_key':'chart','name':'Chart grammar','visibility':'public'}}).json()['id']
    bid=c.post(f'/v1/visual-runtime/grammar/specifications/{gid}/data-bindings',json={'data':{'binding_key':'series','source_kind':'predictive','source_ref':'predictive:demo','fields':[{'name':'country','type':'nominal'},{'name':'value','type':'quantitative'}]}}).json()['id']
    return app,c,sid,views,cid,gid,bid

def test_v2650_readiness_and_migration(tmp_path):
    app,c,*_=setup(tmp_path);r=c.get('/v1/visual-runtime/query/readiness');assert r.status_code==200,r.text;d=r.json();assert d['release']=='2.65.0' and d['migration_0069_applied'] is True;assert migration_status(app.state.database)['pending']==[];assert d['visual_query_request_registry_by_core'] and d['query_execution_by_core'] is False and d['graph_traversal_by_core'] is False

def test_visual_query_roundtrip_snapshot_chain(tmp_path):
    app,c,sid,views,cid,gid,bid=setup(tmp_path)
    ses=c.post(f'/v1/visual-runtime/query/compositions/{cid}/sessions',json={'data':{'session_key':'energy','name':'Energy exploration','purpose':'Trace drivers and evidence','visibility':'public'}});assert ses.status_code==200,ses.text;eid=ses.json()['id']
    t1=c.post(f'/v1/visual-runtime/query/sessions/{eid}/targets',json={'data':{'target_key':'chart','target_kind':'data-binding','view_id':views[1],'grammar_specification_id':gid,'data_binding_id':bid,'target_ref':'predictive:demo'}});assert t1.status_code==200,t1.text;tid=t1.json()['id']
    q=c.post(f'/v1/visual-runtime/query/sessions/{eid}/queries',json={'data':{'query_key':'high-values','name':'High values','query_kind':'subgraph','target_ids':[tid],'query_spec':{'question':'Which connected evidence explains values above 40?','return':['nodes','edges','evidence']},'runtime_product':'Lab'}});assert q.status_code==200,q.text;qid=q.json()['id']
    p=c.post(f'/v1/visual-runtime/query/queries/{qid}/predicates',json={'data':{'predicate_key':'threshold','field_name':'value','operator':'>','value':40,'predicate':{'field':'value','op':'>','value':40}}});assert p.status_code==200,p.text
    tr=c.post(f'/v1/visual-runtime/query/queries/{qid}/traversals',json={'data':{'traversal_key':'evidence-paths','traversal_kind':'subgraph','start_refs':['predictive:demo'],'relation_kinds':['supported-by','derived-from'],'max_depth':4,'constraints':{'preserve_provenance':True}}});assert tr.status_code==200,tr.text
    rb=c.post(f'/v1/visual-runtime/query/queries/{qid}/results',json={'data':{'result_kind':'subgraph','result_ref':'lab:query-result:1','result_summary':{'nodes':5,'edges':4},'evidence':{'verified_external_runtime':True},'runtime_product':'Lab','runtime_ref':'run:123','externally_computed':True}});assert rb.status_code==200,rb.text
    st=c.post(f'/v1/visual-runtime/query/sessions/{eid}/saved-states',json={'data':{'state_key':'review','active_query_ids':[qid],'selected_refs':['predictive:demo'],'filter_state':{'value':{'gt':40}},'view_state':{'active_view_id':views[1]}}});assert st.status_code==200,st.text
    s1=c.post(f'/v1/visual-runtime/query/sessions/{eid}/snapshots',json={'data':{'created_by':'test'}});assert s1.status_code==200,s1.text
    s2=c.post(f'/v1/visual-runtime/query/sessions/{eid}/snapshots',json={'data':{'created_by':'test'}});assert s2.status_code==200,s2.text;assert s2.json()['previous_snapshot_hash']==s1.json()['content_hash']
    out=c.get(f'/v1/visual-runtime/query/sessions/{eid}/bundle');assert out.status_code==200,out.text;d=out.json();assert d['contract']=='sc.visual-runtime.visual-query.v1';assert len(d['queries'])==1 and len(d['predicates'])==1 and len(d['traversals'])==1 and len(d['results'])==1 and len(d['snapshots'])==2
    pub=c.get(f'/api/v1/visual-runtime/query/sessions/{eid}/bundle');assert pub.status_code==401,pub.text

def test_cross_session_and_core_execution_rejection(tmp_path):
    app,c,sid,views,cid,gid,bid=setup(tmp_path)
    a=c.post(f'/v1/visual-runtime/query/compositions/{cid}/sessions',json={'data':{'session_key':'a','name':'A'}}).json()['id']
    b=c.post(f'/v1/visual-runtime/query/compositions/{cid}/sessions',json={'data':{'session_key':'b','name':'B'}}).json()['id']
    ta=c.post(f'/v1/visual-runtime/query/sessions/{a}/targets',json={'data':{'target_key':'x','target_kind':'view','view_id':views[0]}}).json()['id']
    bad=c.post(f'/v1/visual-runtime/query/sessions/{b}/queries',json={'data':{'query_key':'bad','name':'Bad','query_kind':'lookup','target_ids':[ta],'query_spec':{'x':1}}});assert bad.status_code==422
    bad2=c.post(f'/v1/visual-runtime/query/sessions/{a}/queries',json={'data':{'query_key':'bad2','name':'Bad2','query_kind':'lookup','query_spec':{'x':1},'execute_query_by_core':True}});assert bad2.status_code==422
