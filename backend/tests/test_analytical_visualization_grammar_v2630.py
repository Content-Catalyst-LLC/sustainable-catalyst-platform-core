from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity

def setup(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2630.db'}",version='2.63.0'))
    c=TestClient(app)
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:v2630',entity_type='research-project',slug='v2630',name='Visualization Grammar Project',visibility='public'));db.commit()
    sid=c.post('/v1/visual-runtime/scenes',json={'data':{'project_entity_id':'project:v2630','scene_key':'scene','name':'Scene','visibility':'public'}}).json()['id']
    vid=c.post(f'/v1/visual-runtime/scenes/{sid}/views',json={'data':{'view_key':'chart','name':'Chart','view_kind':'chart'}}).json()['id']
    cid=c.post(f'/v1/visual-runtime/composition/scenes/{sid}/compositions',json={'data':{'composition_key':'analysis','name':'Analysis','visibility':'public'}}).json()['id']
    a=c.post(f'/v1/visual-runtime/composition/compositions/{cid}/assignments',json={'data':{'view_id':vid,'slot_key':'main'}});assert a.status_code==200,a.text
    return app,c,sid,vid,cid

def test_v2630_readiness_and_migration(tmp_path):
    app,c,_,_,_=setup(tmp_path);r=c.get('/v1/visual-runtime/grammar/readiness');assert r.status_code==200,r.text
    d=r.json();assert d['release']=='2.63.0' and d['migration_0067_applied'] is True;assert migration_status(app.state.database)['pending']==[]
    assert d['grammar_specification_registry_by_core'] and d['immutable_grammar_snapshots_by_core'];assert d['transform_execution_by_core'] is False and d['mark_drawing_by_core'] is False

def test_analytical_grammar_roundtrip_snapshot_chain(tmp_path):
    app,c,sid,vid,cid=setup(tmp_path)
    r=c.post('/v1/visual-runtime/grammar/specifications',json={'data':{'scene_id':sid,'composition_id':cid,'view_id':vid,'grammar_key':'forecast','name':'Forecast grammar','grammar_kind':'cartesian','coordinate_system':'cartesian','visibility':'public'}});assert r.status_code==200,r.text;gid=r.json()['id']
    b=c.post(f'/v1/visual-runtime/grammar/specifications/{gid}/data-bindings',json={'data':{'binding_key':'series','source_kind':'predictive','source_ref':'predictive:forecast:demo','fields':[{'name':'time','type':'temporal'},{'name':'value','type':'quantitative'}]}});assert b.status_code==200,b.text;bid=b.json()['id']
    m=c.post(f'/v1/visual-runtime/grammar/specifications/{gid}/marks',json={'data':{'mark_key':'forecast-line','mark_kind':'line','data_binding_id':bid,'mark_spec':{'interpolate':'linear'}}});assert m.status_code==200,m.text;mid=m.json()['id']
    sx=c.post(f'/v1/visual-runtime/grammar/specifications/{gid}/scales',json={'data':{'scale_key':'time','scale_kind':'utc'}});assert sx.status_code==200,sx.text;sxid=sx.json()['id']
    sy=c.post(f'/v1/visual-runtime/grammar/specifications/{gid}/scales',json={'data':{'scale_key':'value','scale_kind':'linear','nice':True}});assert sy.status_code==200,sy.text;syid=sy.json()['id']
    for ch,field,typ,scale in [('x','time','temporal',sxid),('y','value','quantitative',syid)]:
        e=c.post(f'/v1/visual-runtime/grammar/specifications/{gid}/encodings',json={'data':{'mark_id':mid,'scale_id':scale,'channel':ch,'field_name':field,'data_type':typ}});assert e.status_code==200,e.text
    t=c.post(f'/v1/visual-runtime/grammar/specifications/{gid}/transforms',json={'data':{'transform_key':'window','transform_kind':'external','input_binding_id':bid,'parameters':{'contract':'runtime:rolling-window','core_executes':False}}});assert t.status_code==200,t.text
    g=c.post(f'/v1/visual-runtime/grammar/specifications/{gid}/guides',json={'data':{'guide_key':'y-axis','guide_kind':'axis','channel':'y','scale_id':syid,'title':'Forecast value'}});assert g.status_code==200,g.text
    s1=c.post(f'/v1/visual-runtime/grammar/specifications/{gid}/snapshots',json={'data':{'created_by':'test'}});assert s1.status_code==200,s1.text
    s2=c.post(f'/v1/visual-runtime/grammar/specifications/{gid}/snapshots',json={'data':{'created_by':'test'}});assert s2.status_code==200,s2.text and s2.json()['previous_snapshot_hash']==s1.json()['content_hash']
    out=c.get(f'/v1/visual-runtime/grammar/specifications/{gid}/bundle');assert out.status_code==200,out.text;d=out.json();assert d['contract']=='sc.visual-runtime.grammar.v1';assert len(d['marks'])==1 and len(d['encodings'])==2 and len(d['scales'])==2 and len(d['snapshots'])==2

def test_cross_spec_and_core_execution_rejection(tmp_path):
    app,c,sid,vid,cid=setup(tmp_path)
    def spec(key):
        r=c.post('/v1/visual-runtime/grammar/specifications',json={'data':{'scene_id':sid,'composition_id':cid,'view_id':vid,'grammar_key':key,'name':key}});assert r.status_code==200,r.text;return r.json()['id']
    a,b=spec('a'),spec('b')
    sc=c.post(f'/v1/visual-runtime/grammar/specifications/{a}/scales',json={'data':{'scale_key':'x','scale_kind':'linear'}}).json()['id']
    bad=c.post(f'/v1/visual-runtime/grammar/specifications/{b}/guides',json={'data':{'guide_key':'bad','scale_id':sc}});assert bad.status_code==422
    bad2=c.post('/v1/visual-runtime/grammar/specifications',json={'data':{'scene_id':sid,'grammar_key':'bad','name':'Bad','draw_marks_by_core':True}});assert bad2.status_code==422
