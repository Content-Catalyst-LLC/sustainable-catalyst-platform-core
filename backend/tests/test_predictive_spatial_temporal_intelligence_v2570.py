from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2570.db'}",version='2.57.0'))
    return app,TestClient(app)

def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:pred-v2570',entity_type='research-project',slug='pred-v2570',name='Spatial Predictive Project',visibility='public')); db.commit()

def model(c):
    r=c.post('/v1/predictive-intelligence/models',json={'data':{'project_entity_id':'project:pred-v2570','model_key':'spatial-model','name':'Spatial Model','model_kind':'statistical','runtime_product':'site-intelligence','visibility':'public'}})
    assert r.status_code==200,r.text
    return r.json()['id']

def test_v2570_readiness_and_boundaries(tmp_path):
    app,c=app_client(tmp_path); seed(app); d=c.get('/v1/predictive-intelligence/readiness').json()
    assert d['release']=='2.57.0' and d['migration_0061_applied'] is True and migration_status(app.state.database)['pending']==[]
    for k in ('spatial_temporal_study_registry_by_core','spatial_unit_registry_by_core','spatial_temporal_forecast_provenance_by_core','spatial_temporal_observation_registry_by_core','propagation_evidence_registry_by_core','hotspot_evidence_registry_by_core','spatial_temporal_evaluation_evidence_by_core','reproducible_spatial_temporal_packages_by_core'): assert d[k] is True,k
    for k in ('spatial_interpolation_by_core','spatial_inference_execution_by_core','trajectory_prediction_by_core','propagation_modeling_by_core','hotspot_detection_by_core','spatial_temporal_metric_computation_by_core','automatic_intervention_by_core','automatic_truth_promotion'): assert d[k] is False,k

def test_spatial_temporal_evidence_and_package(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid=model(c)
    st=c.post('/v1/predictive-intelligence/spatial-temporal-studies',json={'data':{'project_entity_id':'project:pred-v2570','model_id':mid,'study_key':'regional-risk','name':'Regional Risk','spatial_reference':'EPSG:4326','temporal_reference':'UTC','spatial_scope':{'country':'USA'},'forecast_horizon':{'hours':24},'visibility':'public'}})
    assert st.status_code==200,st.text; sid=st.json()['id']; assert st.json()['externally_computed'] is True
    u1=c.post(f'/v1/predictive-intelligence/spatial-temporal-studies/{sid}/units',json={'data':{'unit_key':'west','unit_kind':'region','label':'West','bbox':[-125,30,-100,50],'source_ref':'site-intelligence://regions/west'}}); assert u1.status_code==200,u1.text
    u2=c.post(f'/v1/predictive-intelligence/spatial-temporal-studies/{sid}/units',json={'data':{'unit_key':'central','unit_kind':'region','label':'Central','bbox':[-100,30,-85,50],'source_ref':'site-intelligence://regions/central'}}); assert u2.status_code==200,u2.text
    f=c.post(f'/v1/predictive-intelligence/spatial-temporal-studies/{sid}/forecasts',json={'data':{'spatial_unit_id':u1.json()['id'],'forecast_key':'f-1','issued_at':'2026-09-15T00:00:00Z','valid_time':'2026-09-15T06:00:00Z','representation':'probability','forecast':{'risk_probability':0.72},'uncertainty':{'interval':[0.61,0.81]},'runtime_product':'site-intelligence','runtime_ref':'site-intelligence://forecast/f-1'}}); assert f.status_code==200,f.text and f.json()['externally_computed'] is True
    o=c.post(f'/v1/predictive-intelligence/spatial-temporal-studies/{sid}/observations',json={'data':{'spatial_unit_id':u1.json()['id'],'observation_key':'o-1','observed_at':'2026-09-15T06:00:00Z','value':{'risk_index':0.68},'source_ref':'site-intelligence://observation/o-1'}}); assert o.status_code==200,o.text
    p=c.post(f'/v1/predictive-intelligence/spatial-temporal-studies/{sid}/propagation-evidence',json={'data':{'evidence_key':'p-1','source_unit_id':u1.json()['id'],'target_unit_id':u2.json()['id'],'evidence_kind':'lagged-association','lag':{'hours':3},'statistic':{'external_score':0.64},'evidence_ref':'lab://spatial/p-1'}}); assert p.status_code==200,p.text and p.json()['externally_computed'] is True
    h=c.post(f'/v1/predictive-intelligence/spatial-temporal-studies/{sid}/hotspot-evidence',json={'data':{'spatial_unit_id':u1.json()['id'],'hotspot_key':'h-1','observed_at':'2026-09-15T06:00:00Z','hotspot_kind':'external','score':{'z':3.1},'threshold':{'z':2.5},'evidence_ref':'site-intelligence://hotspot/h-1'}}); assert h.status_code==200,h.text and h.json()['externally_detected'] is True
    e=c.post(f'/v1/predictive-intelligence/spatial-temporal-studies/{sid}/evaluations',json={'data':{'evaluation_key':'eval-1','evaluation_kind':'spatial-temporal','window':{'start':'2026-09-15T00:00:00Z','end':'2026-09-15T12:00:00Z'},'metric_evidence':{'external_rmse':0.17},'evidence_ref':'workbench://eval/eval-1'}}); assert e.status_code==200,e.text and e.json()['externally_computed'] is True
    pkg=c.post(f'/v1/predictive-intelligence/spatial-temporal-studies/{sid}/packages',json={'data':{'environment':{'runtime':'site-intelligence','version':'test'},'created_by':'test'}}); assert pkg.status_code==200,pkg.text and len(pkg.json()['content_hash'])==64
    b=c.get(f'/v1/predictive-intelligence/spatial-temporal-studies/{sid}/bundle'); assert b.status_code==200,b.text; body=b.json(); assert body['contract']=='sc.predictive.spatial-temporal-package.v1'; assert len(body['spatial_units'])==2 and len(body['forecasts'])==1 and len(body['observations'])==1 and len(body['propagation_evidence'])==1 and len(body['hotspot_evidence'])==1 and len(body['evaluations'])==1 and len(body['packages'])==1
    mb=c.get(f'/v1/predictive-intelligence/models/{mid}/bundle').json(); assert len(mb['spatial_temporal_studies'])==1

def test_spatial_compute_fields_rejected(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    r=c.post('/v1/predictive-intelligence/spatial-temporal-studies',json={'data':{'project_entity_id':'project:pred-v2570','study_key':'bad','name':'Bad','spatial_interpolate_by_core':True}})
    assert r.status_code==422 and 'does not fit' in r.text
