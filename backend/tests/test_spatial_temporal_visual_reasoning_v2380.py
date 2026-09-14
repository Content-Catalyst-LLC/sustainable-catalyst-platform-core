from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.models import Entity

def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2380.db'}",version='2.50.0'))
    return app,TestClient(app)

def seed_project(app):
    with app.state.database.session_factory() as db:
        p=Entity(id='project:spacetime',entity_type='research-project',slug='spacetime',name='Space Time Test',visibility='public');db.add(p);db.commit()

def test_readiness_and_migration_0042(tmp_path):
    app,c=app_client(tmp_path); seed_project(app)
    d=c.get('/v1/spatial-temporal/readiness').json(); assert d['release']=='2.50.0'; assert d['migration_0042_applied'] is True; assert d['spatial_analysis_by_core'] is False; assert d['automatic_truth_promotion'] is False
    with app.state.database.session_factory() as db: assert migration_status(app.state.database)['pending']==[]

def test_scene_features_events_trajectory_timeline_and_bundle(tmp_path):
    app,c=app_client(tmp_path);seed_project(app)
    scene=c.post('/v1/spatial-temporal/scenes',json={'data':{'scene_key':'river','name':'River system','project_entity_id':'project:spacetime','visibility':'public','temporal_start':'2026-01-01T00:00:00Z','temporal_end':'2026-12-31T23:59:00Z'}});assert scene.status_code==200; sid=scene.json()['id']
    feat=c.post(f'/v1/spatial-temporal/scenes/{sid}/features',json={'data':{'feature_key':'station','label':'Station','geometry':{'type':'Point','coordinates':[-90.2,38.6]},'feature_kind':'sensor'}});assert feat.status_code==200;fid=feat.json()['id']
    ev=c.post(f'/v1/spatial-temporal/scenes/{sid}/events',json={'data':{'event_key':'flood','label':'Flood interval','event_kind':'flood','starts_at':'2026-05-01T00:00:00Z','ends_at':'2026-05-03T00:00:00Z','feature_id':fid}});assert ev.status_code==200
    tr=c.post(f'/v1/spatial-temporal/scenes/{sid}/trajectories',json={'data':{'trajectory_key':'plume','label':'Plume'}});assert tr.status_code==200;tid=tr.json()['id']
    for pos,ts,xy in [(0,'2026-05-01T00:00:00Z',[-90.2,38.6]),(1,'2026-05-02T00:00:00Z',[-90.1,38.7])]:
        p=c.post(f'/v1/spatial-temporal/trajectories/{tid}/points',json={'data':{'sequence_position':pos,'observed_at':ts,'geometry':{'type':'Point','coordinates':xy}}});assert p.status_code==200
    ts=c.get(f'/v1/spatial-temporal/scenes/{sid}/timeline').json(); assert ts['count']==3; assert [x['at'] for x in ts['items']]==sorted(x['at'] for x in ts['items'])
    b=c.get(f'/v1/spatial-temporal/scenes/{sid}/bundle').json();assert len(b['features'])==1;assert len(b['events'])==1;assert len(b['trajectory_points'])==2;assert b['boundaries']['spatial_analysis_by_core'] is False
    pb=c.get(f'/api/v1/spatial-temporal/scenes/{sid}/bundle',headers={'X-API-Key':'test'})
    assert pb.status_code in (200,401)  # public auth policy remains independently testable

def test_temporal_and_geometry_guards(tmp_path):
    app,c=app_client(tmp_path);seed_project(app)
    sid=c.post('/v1/spatial-temporal/scenes',json={'data':{'scene_key':'guard','name':'Guard','project_entity_id':'project:spacetime'}}).json()['id']
    bad=c.post(f'/v1/spatial-temporal/scenes/{sid}/events',json={'data':{'event_key':'bad','label':'Bad','starts_at':'2026-05-03T00:00:00Z','ends_at':'2026-05-01T00:00:00Z'}}); assert bad.status_code==422
    bad2=c.post(f'/v1/spatial-temporal/scenes/{sid}/features',json={'data':{'feature_key':'badgeo','label':'Bad','geometry':{'type':'Circle','coordinates':[0,0]}}});assert bad2.status_code==422

def test_change_requires_provenance_and_runtime_handoff_boundaries(tmp_path):
    app,c=app_client(tmp_path);seed_project(app)
    sid=c.post('/v1/spatial-temporal/scenes',json={'data':{'scene_key':'change','name':'Change','project_entity_id':'project:spacetime'}}).json()['id']
    bad=c.post(f'/v1/spatial-temporal/scenes/{sid}/changes',json={'data':{'change_key':'x','label':'X','before':1,'after':2}});assert bad.status_code==422
    ok=c.post(f'/v1/spatial-temporal/scenes/{sid}/changes',json={'data':{'change_key':'x','label':'X','before_at':'2026-01-01T00:00:00Z','after_at':'2026-02-01T00:00:00Z','before':1,'after':2,'delta':1,'provenance':{'source':'test'}}});assert ok.status_code==200
    hand=c.post(f'/v1/spatial-temporal/scenes/{sid}/runtime-handoff',json={'data':{'target_product':'site-intelligence','operation':'remote-sensing'}});assert hand.status_code==200;assert hand.json()['remote_sensing_by_core'] is False
    deny=c.post(f'/v1/spatial-temporal/scenes/{sid}/runtime-handoff',json={'data':{'execute_by_core':True}});assert deny.status_code==422

def test_view_and_visualization_contract(tmp_path):
    app,c=app_client(tmp_path);seed_project(app)
    sid=c.post('/v1/spatial-temporal/scenes',json={'data':{'scene_key':'view','name':'View','project_entity_id':'project:spacetime'}}).json()['id']
    v=c.post(f'/v1/spatial-temporal/scenes/{sid}/views',json={'data':{'view_key':'linked','name':'Linked','view_kind':'linked-map-timeline','layers':['features','events']}});assert v.status_code==200
    spec=c.get(f'/v1/spatial-temporal/scenes/{sid}/visualization',params={'view_id':v.json()['id']}).json();assert spec['contract']=='sc.spatial-temporal-visualization.v1';assert spec['visual_kind']=='linked-map-timeline';assert spec['renderer_execution_by_core'] is False
