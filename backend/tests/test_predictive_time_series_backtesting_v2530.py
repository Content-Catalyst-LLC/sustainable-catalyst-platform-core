from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2530.db'}",version='2.54.0'))
    return app,TestClient(app)

def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:pred-v2530',entity_type='research-project',slug='pred-v2530',name='Backtest Project',visibility='public')); db.commit()

def model_target(c):
    r=c.post('/v1/predictive-intelligence/models',json={'data':{'project_entity_id':'project:pred-v2530','model_key':'load','name':'Load forecast','model_kind':'statistical','runtime_product':'lab','runtime_model_ref':'lab://models/load','model_version_ref':'v2','visibility':'public'}}); assert r.status_code==200,r.text; mid=r.json()['id']
    t=c.post(f'/v1/predictive-intelligence/models/{mid}/targets',json={'data':{'target_key':'load','label':'Electric load','unit':'MW','horizon':{'steps':24,'unit':'hours'},'source_ref':'catalyst-data://energy/load'}}); assert t.status_code==200,t.text
    return mid,t.json()['id']

def test_v2530_readiness_and_boundaries(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    r=c.get('/v1/predictive-intelligence/readiness'); assert r.status_code==200,r.text; d=r.json()
    assert d['release']=='2.54.0' and d['migration_0056_applied'] is True and d['migration_0057_applied'] is True
    for k in ('time_series_dataset_registry_by_core','forecast_window_registry_by_core','baseline_model_reference_registry_by_core','rolling_expanding_backtest_semantics_by_core','temporal_leakage_guardrails_by_core','backtest_fold_provenance_by_core','prediction_actual_pair_recording_by_core','descriptive_backtest_evaluation_by_core','reproducible_backtest_packages_by_core'): assert d[k] is True,k
    for k in ('model_fitting_by_core','forecast_inference_execution_by_core','backtest_execution_by_core','metric_computation_by_core','time_series_resampling_by_core','automatic_model_ranking_by_core','automatic_truth_promotion'): assert d[k] is False,k
    assert migration_status(app.state.database)['pending']==[]

def test_time_series_dataset_windows_baseline_and_backtest_package(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid,tid=model_target(c)
    ds=c.post(f'/v1/predictive-intelligence/models/{mid}/time-series-datasets',json={'data':{'dataset_key':'hourly-load','source_product':'catalyst-data','source_ref':'catalyst-data://energy/hourly','time_field':'timestamp','frequency':'1h','timezone':'UTC','target_keys':['load'],'manifest_hash':'a'*64}}); assert ds.status_code==200,ds.text; dsid=ds.json()['id']
    w=c.post(f'/v1/predictive-intelligence/models/{mid}/forecast-windows',json={'data':{'window_key':'rolling-1','strategy':'rolling','train_start':'2025-01-01T00:00:00+00:00','train_end':'2025-12-31T23:00:00+00:00','cutoff_time':'2026-01-01T00:00:00+00:00','test_start':'2026-01-01T01:00:00+00:00','test_end':'2026-01-02T00:00:00+00:00','horizon':{'steps':24,'unit':'hours'},'step':{'steps':24,'unit':'hours'}}}); assert w.status_code==200,w.text
    b=c.post(f'/v1/predictive-intelligence/models/{mid}/baselines',json={'data':{'baseline_key':'seasonal-naive','baseline_kind':'seasonal-naive','runtime_product':'lab','runtime_model_ref':'lab://baselines/seasonal-naive','parameters':{'seasonal_period':24}}}); assert b.status_code==200,b.text; bid=b.json()['id']
    p=c.post(f'/v1/predictive-intelligence/models/{mid}/backtest-plans',json={'data':{'plan_key':'rolling-2025','dataset_id':dsid,'target_id':tid,'strategy':'rolling','initial_train_window':{'days':180},'forecast_horizon':{'steps':24,'unit':'hours'},'step':{'steps':24,'unit':'hours'},'baseline_ids':[bid],'runtime_product':'lab','runtime_plan_ref':'lab://backtests/rolling-2025'}}); assert p.status_code==200,p.text; pid=p.json()['id']; assert p.json()['leakage_controls_json']['strict_temporal_cutoff'] is True
    f=c.post(f'/v1/predictive-intelligence/models/{mid}/backtest-plans/{pid}/folds',json={'data':{'fold_key':'fold-000','fold_index':0,'train_start':'2025-01-01T00:00:00+00:00','train_end':'2025-06-30T23:00:00+00:00','cutoff_time':'2025-07-01T00:00:00+00:00','test_start':'2025-07-01T01:00:00+00:00','test_end':'2025-07-02T00:00:00+00:00','runtime_run_ref':'lab://backtests/fold-000','input_manifest_hash':'b'*64}}); assert f.status_code==200,f.text; fid=f.json()['id']; assert f.json()['leakage_check_json']['passed'] is True
    o=c.post(f'/v1/predictive-intelligence/models/{mid}/backtest-plans/{pid}/folds/{fid}/observations',json={'data':{'target_id':tid,'valid_time':'2025-07-01T01:00:00+00:00','prediction':412.5,'actual':410.0,'unit':'MW','actual_source_ref':'catalyst-data://energy/actuals','error':{'absolute':2.5}}}); assert o.status_code==200,o.text
    e=c.post(f'/v1/predictive-intelligence/models/{mid}/backtest-plans/{pid}/evaluations',json={'data':{'evaluation_key':'model-mae','metric_name':'MAE','metric_value':7.4,'comparator_kind':'model','evidence_ref':'lab://evaluations/model-mae'}}); assert e.status_code==200,e.text and e.json()['externally_computed'] is True
    pkg=c.post(f'/v1/predictive-intelligence/models/{mid}/backtest-plans/{pid}/packages',json={'data':{'environment':{'runtime':'lab','version':'test'},'created_by':'test'}}); assert pkg.status_code==200,pkg.text and len(pkg.json()['content_hash'])==64
    bundle=c.get(f'/v1/predictive-intelligence/models/{mid}/backtest-plans/{pid}/bundle'); assert bundle.status_code==200,bundle.text; body=bundle.json(); assert body['contract']=='sc.predictive.backtest-package.v1' and len(body['folds'])==1 and len(body['observations'])==1 and len(body['evaluations'])==1 and len(body['packages'])==1

def test_temporal_leakage_is_rejected(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid,tid=model_target(c)
    ds=c.post(f'/v1/predictive-intelligence/models/{mid}/time-series-datasets',json={'data':{'dataset_key':'d','source_ref':'external://d','time_field':'ts'}}).json()['id']
    p=c.post(f'/v1/predictive-intelligence/models/{mid}/backtest-plans',json={'data':{'plan_key':'p','dataset_id':ds,'target_id':tid,'strategy':'rolling'}}).json()['id']
    r=c.post(f'/v1/predictive-intelligence/models/{mid}/backtest-plans/{p}/folds',json={'data':{'fold_key':'leak','fold_index':0,'train_end':'2025-07-01T00:00:00+00:00','cutoff_time':'2025-07-01T00:00:00+00:00','test_start':'2025-07-01T00:00:00+00:00'}})
    assert r.status_code==422 and 'temporal leakage' in r.text

def test_core_execution_fields_rejected(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid,tid=model_target(c)
    r=c.post(f'/v1/predictive-intelligence/models/{mid}/time-series-datasets',json={'data':{'dataset_key':'bad','source_ref':'external://d','time_field':'ts','resample_by_core':True}})
    assert r.status_code==422 and 'does not fit' in r.text
