from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity

def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2540.db'}",version='2.54.0'))
    return app,TestClient(app)

def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:pred-v2540',entity_type='research-project',slug='pred-v2540',name='Calibration Project',visibility='public')); db.commit()

def model_target_run(c):
    r=c.post('/v1/predictive-intelligence/models',json={'data':{'project_entity_id':'project:pred-v2540','model_key':'risk','name':'Risk forecast','model_kind':'statistical','runtime_product':'lab','visibility':'public'}}); assert r.status_code==200,r.text; mid=r.json()['id']
    t=c.post(f'/v1/predictive-intelligence/models/{mid}/targets',json={'data':{'target_key':'failure','label':'Failure event','value_kind':'binary','source_ref':'catalyst-data://risk/actuals'}}); assert t.status_code==200,t.text; tid=t.json()['id']
    run=c.post(f'/v1/predictive-intelligence/models/{mid}/forecast-runs',json={'data':{'run_key':'r1','runtime_product':'lab','runtime_run_ref':'lab://run/r1'}}); assert run.status_code==200,run.text
    return mid,tid,run.json()['id']

def test_v2540_readiness_and_boundaries(tmp_path):
    app,c=app_client(tmp_path); seed(app); d=c.get('/v1/predictive-intelligence/readiness').json()
    assert d['release']=='2.54.0' and d['migration_0058_applied'] is True and migration_status(app.state.database)['pending']==[]
    for k in ('probabilistic_forecast_registry_by_core','uncertainty_distribution_registry_by_core','calibration_study_registry_by_core','calibration_bin_evidence_by_core','external_calibration_mapping_registry_by_core','proper_scoring_evidence_registry_by_core','reproducible_calibration_packages_by_core'): assert d[k] is True,k
    for k in ('probabilistic_inference_execution_by_core','calibration_mapping_fitting_by_core','calibration_mapping_application_by_core','proper_scoring_rule_computation_by_core','calibration_metric_computation_by_core','probabilistic_model_ranking_by_core','automatic_truth_promotion'): assert d[k] is False,k

def test_probabilistic_forecasts_calibration_and_package(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid,tid,rid=model_target_run(c)
    pf=c.post(f'/v1/predictive-intelligence/models/{mid}/probabilistic-forecasts',json={'data':{'target_id':tid,'forecast_run_id':rid,'representation':'binary-event','forecast':{'probability':0.72},'source_ref':'lab://prob/r1'}}); assert pf.status_code==200,pf.text; pfid=pf.json()['id']; assert pf.json()['externally_generated'] is True
    q=c.post(f'/v1/predictive-intelligence/models/{mid}/probabilistic-forecasts',json={'data':{'target_id':tid,'forecast_run_id':rid,'representation':'quantile','forecast':{'quantiles':{'0.1':1.0,'0.5':2.0,'0.9':3.0}}}}); assert q.status_code==200,q.text
    st=c.post(f'/v1/predictive-intelligence/models/{mid}/calibration-studies',json={'data':{'target_id':tid,'study_key':'reliability-2026','assessment_kind':'reliability','scope':{'window':'2026-Q3'},'actual_outcome_source_ref':'catalyst-data://risk/actuals'}}); assert st.status_code==200,st.text; sid=st.json()['id']; assert st.json()['externally_computed'] is True
    b=c.post(f'/v1/predictive-intelligence/models/{mid}/calibration-studies/{sid}/bins',json={'data':{'bin_index':0,'lower_bound':0.6,'upper_bound':0.8,'mean_forecast':0.71,'observed_frequency':0.68,'sample_count':120}}); assert b.status_code==200,b.text
    m=c.post(f'/v1/predictive-intelligence/models/{mid}/calibration-studies/{sid}/mappings',json={'data':{'mapping_key':'iso-v1','method':'isotonic','parameters':{'artifact_ref':'lab://calibration/iso-v1'},'fit_evidence_ref':'lab://calibration/report-v1'}}); assert m.status_code==200,m.text and m.json()['externally_fitted'] is True
    e=c.post(f'/v1/predictive-intelligence/models/{mid}/probabilistic-evaluations',json={'data':{'calibration_study_id':sid,'probabilistic_forecast_id':pfid,'evaluation_key':'brier-q3','metric_family':'proper-scoring-rule','metric_name':'Brier score','metric_value':0.181,'evidence_ref':'lab://scores/brier-q3'}}); assert e.status_code==200,e.text and e.json()['externally_computed'] is True
    pkg=c.post(f'/v1/predictive-intelligence/models/{mid}/calibration-studies/{sid}/packages',json={'data':{'environment':{'runtime':'lab','version':'test'},'created_by':'test'}}); assert pkg.status_code==200,pkg.text and len(pkg.json()['content_hash'])==64
    bundle=c.get(f'/v1/predictive-intelligence/models/{mid}/calibration-studies/{sid}/bundle'); assert bundle.status_code==200,bundle.text; body=bundle.json(); assert body['contract']=='sc.predictive.calibration-package.v1' and len(body['bins'])==1 and len(body['mappings'])==1 and len(body['evaluations'])==1 and len(body['packages'])==1
    model_bundle=c.get(f'/v1/predictive-intelligence/models/{mid}/bundle').json(); assert len(model_bundle['probabilistic_forecasts'])==2 and len(model_bundle['calibration_studies'])==1 and len(model_bundle['probabilistic_evaluations'])==1

def test_invalid_probability_and_categories_rejected(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid,tid,rid=model_target_run(c)
    r=c.post(f'/v1/predictive-intelligence/models/{mid}/probabilistic-forecasts',json={'data':{'target_id':tid,'forecast_run_id':rid,'representation':'binary-event','forecast':{'probability':1.2}}}); assert r.status_code==422 and 'between 0 and 1' in r.text
    r=c.post(f'/v1/predictive-intelligence/models/{mid}/probabilistic-forecasts',json={'data':{'target_id':tid,'forecast_run_id':rid,'representation':'categorical','forecast':{'probabilities':{'a':0.7,'b':0.4}}}}); assert r.status_code==422 and 'sum to 1' in r.text

def test_core_calibration_execution_fields_rejected(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid,tid,rid=model_target_run(c)
    r=c.post(f'/v1/predictive-intelligence/models/{mid}/probabilistic-forecasts',json={'data':{'target_id':tid,'forecast_run_id':rid,'representation':'binary-event','forecast':{'probability':0.5},'recalibration_apply_by_core':True}})
    assert r.status_code==422 and 'does not fit' in r.text
