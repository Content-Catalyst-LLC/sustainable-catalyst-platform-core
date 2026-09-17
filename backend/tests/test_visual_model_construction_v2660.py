from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.database import Base
from app.models import Entity,VisualReasoningObjectRecord,ModelCanvasRecord

def seed(app):
    with app.state.database.session_factory() as db:
        p=Entity(id='proj266',entity_type='project',name='P',slug='p266');m=Entity(id='model266',entity_type='model',name='M',slug='m266');v=Entity(id='canvas266',entity_type='visual',name='Canvas',slug='canvas266');db.add_all([p,m,v]);db.flush();db.add(VisualReasoningObjectRecord(entity_id=v.id,project_entity_id=p.id,visual_kind='model-canvas'));db.flush();db.add(ModelCanvasRecord(visual_entity_id=v.id,project_entity_id=p.id,model_entity_id=m.id));db.commit();return v.id
def test_readiness_and_roundtrip(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'x.db'}",version='2.66.0'));c=TestClient(app);canvas=seed(app)
    d=c.get('/v1/visual-runtime/model-construction/readiness').json();assert d['release']=='2.66.0' and d['migration_0070_applied'] and d['model_execution_by_core'] is False
    x=c.post(f'/v1/visual-runtime/model-construction/canvases/{canvas}/constructions',json={'data':{'construction_key':'energy','name':'Energy Model','visibility':'public'}});assert x.status_code==200,x.text;cid=x.json()['id']
    a=c.post(f'/v1/visual-runtime/model-construction/constructions/{cid}/components',json={'data':{'component_key':'demand','component_kind':'variable','label':'Demand','symbol':'D'}});assert a.status_code==200,a.text
    b=c.post(f'/v1/visual-runtime/model-construction/constructions/{cid}/components',json={'data':{'component_key':'price','component_kind':'parameter','label':'Price','symbol':'P'}});assert b.status_code==200,b.text
    r=c.post(f'/v1/visual-runtime/model-construction/constructions/{cid}/relationships',json={'data':{'relationship_key':'eq','relationship_kind':'equation','source_component_id':b.json()['id'],'target_component_id':a.json()['id'],'expression':'D = a - b*P'}});assert r.status_code==200,r.text
    assert c.post(f'/v1/visual-runtime/model-construction/constructions/{cid}/assumptions',json={'data':{'assumption_key':'linear','statement':'Demand response is locally linear.'}}).status_code==200
    assert c.post(f'/v1/visual-runtime/model-construction/constructions/{cid}/constraints',json={'data':{'constraint_key':'positive','expression':'D >= 0'}}).status_code==200
    assert c.post(f'/v1/visual-runtime/model-construction/constructions/{cid}/interventions',json={'data':{'intervention_key':'price-shock','name':'Price shock','target_component_ids':[b.json()['id']],'intervention_spec':{'delta':10}}}).status_code==200
    assert c.post(f'/v1/visual-runtime/model-construction/constructions/{cid}/handoffs',json={'data':{'target_product':'Lab','purpose':'simulate','request':{'mode':'scenario'}}}).status_code==200
    s1=c.post(f'/v1/visual-runtime/model-construction/constructions/{cid}/snapshots',json={'data':{}}).json();s2=c.post(f'/v1/visual-runtime/model-construction/constructions/{cid}/snapshots',json={'data':{}}).json();assert s2['previous_snapshot_hash']==s1['content_hash']
    bun=c.get(f'/v1/visual-runtime/model-construction/constructions/{cid}/bundle').json();assert len(bun['components'])==2 and len(bun['relationships'])==1 and bun['boundaries']['equation_execution_by_core'] is False
def test_execution_boundary(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'b.db'}",version='2.66.0'));c=TestClient(app);canvas=seed(app)
    r=c.post(f'/v1/visual-runtime/model-construction/canvases/{canvas}/constructions',json={'data':{'construction_key':'bad','name':'Bad','model_execution_by_core':True}});assert r.status_code==422
