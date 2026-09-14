from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity

def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2520.db'}",version='2.53.0')); return app,TestClient(app)
def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:pred-v2520',entity_type='research-project',slug='pred-v2520',name='Predictive Project',visibility='public')); db.commit()
def model(c):
    r=c.post('/v1/predictive-intelligence/models',json={'data':{'project_entity_id':'project:pred-v2520','model_key':'demand','name':'Demand forecast','model_kind':'statistical','runtime_product':'lab','runtime_model_ref':'lab://models/demand','model_version_ref':'v1','visibility':'public'}}); assert r.status_code==200,r.text; return r.json()['id']
def test_v2520_readiness_and_boundaries(tmp_path):
    app,c=app_client(tmp_path); seed(app); r=c.get('/v1/predictive-intelligence/readiness'); assert r.status_code==200,r.text; d=r.json(); assert d['release']=='2.53.0' and d['migration_0056_applied'] is True
    for k in ('predictive_model_registry_by_core','prediction_target_registry_by_core','feature_provenance_registry_by_core','training_window_manifest_by_core','forecast_provenance_capture_by_core','forecast_observation_binding_by_core','descriptive_evaluation_evidence_by_core','specialist_runtime_handoffs_by_core','immutable_forecast_snapshots_by_core'): assert d[k] is True,k
    for k in ('model_fitting_by_core','forecast_inference_execution_by_core','probabilistic_calibration_by_core','ensemble_selection_by_core','automatic_model_ranking_by_core','automatic_truth_promotion'): assert d[k] is False,k
    assert migration_status(app.state.database)['pending']==[]
def test_model_targets_features_training_and_forecast_provenance(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid=model(c)
    t=c.post(f'/v1/predictive-intelligence/models/{mid}/targets',json={'data':{'target_key':'load','label':'Electric load','unit':'MW','horizon':{'steps':24,'unit':'hours'},'source_ref':'catalyst-data://energy/load'}}); assert t.status_code==200,t.text; tid=t.json()['id']
    f=c.post(f'/v1/predictive-intelligence/models/{mid}/features',json={'data':{'feature_key':'temp','label':'Temperature','feature_role':'exogenous','unit':'C','source_product':'site-intelligence','source_ref':'site-intelligence://weather/temp'}}); assert f.status_code==200,f.text
    w=c.post(f'/v1/predictive-intelligence/models/{mid}/training-windows',json={'data':{'window_key':'train-2025','start_time':'2025-01-01T00:00:00+00:00','end_time':'2025-12-31T23:00:00+00:00','cutoff_time':'2026-01-01T00:00:00+00:00','dataset_ref':'catalyst-data://energy/train','input_manifest_hash':'a'*64}}); assert w.status_code==200,w.text; wid=w.json()['id']
    run=c.post(f'/v1/predictive-intelligence/models/{mid}/forecast-runs',json={'data':{'run_key':'fc-1','training_window_id':wid,'horizon_start':'2026-01-02T00:00:00+00:00','horizon_end':'2026-01-03T00:00:00+00:00','runtime_product':'lab','runtime_run_ref':'lab://runs/1','input_manifest_hash':'b'*64}}); assert run.status_code==200,run.text; rid=run.json()['id']
    o=c.post(f'/v1/predictive-intelligence/models/{mid}/forecast-runs/{rid}/observations',json={'data':{'target_id':tid,'valid_time':'2026-01-02T01:00:00+00:00','forecast_value':412.5,'unit':'MW','observed_value':410.0,'observation_source_ref':'catalyst-data://energy/actuals'}}); assert o.status_code==200,o.text
    b=c.get(f'/v1/predictive-intelligence/models/{mid}/bundle'); assert b.status_code==200,b.text; body=b.json(); assert len(body['targets'])==1 and len(body['features'])==1 and len(body['training_windows'])==1 and len(body['forecast_runs'])==1 and len(body['forecast_observations'])==1
def test_evaluation_handoff_snapshot_are_descriptive_and_nonexecuting(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid=model(c)
    e=c.post(f'/v1/predictive-intelligence/models/{mid}/evaluations',json={'data':{'evaluation_key':'baseline-mae','metric_name':'MAE','metric_value':7.4,'evaluation_window':{'kind':'holdout'},'evidence_ref':'lab://evaluations/mae'}}); assert e.status_code==200,e.text and e.json()['externally_computed'] is True
    h=c.post(f'/v1/predictive-intelligence/models/{mid}/handoffs',json={'data':{'handoff_key':'lab-run','target_product':'lab','manifest':{'task':'fit-and-forecast'}}}); assert h.status_code==200,h.text; assert h.json()['manifest_json']['core_executes'] is False
    s=c.post(f'/v1/predictive-intelligence/models/{mid}/snapshots',json={'data':{'created_by':'test'}}); assert s.status_code==200,s.text and len(s.json()['content_hash'])==64
    b=c.get(f'/v1/predictive-intelligence/models/{mid}/bundle').json(); assert b['boundaries']['forecast_inference_execution_by_core'] is False
def test_determinative_execution_fields_rejected(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    r=c.post('/v1/predictive-intelligence/models',json={'data':{'project_entity_id':'project:pred-v2520','model_key':'bad','name':'Bad','fit_by_core':True}}); assert r.status_code==422 and 'does not fit' in r.text
