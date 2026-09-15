from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity

def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2560.db'}",version='2.56.0'))
    return app,TestClient(app)

def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:pred-v2560',entity_type='research-project',slug='pred-v2560',name='Monitoring Project',visibility='public')); db.commit()

def model(c):
    r=c.post('/v1/predictive-intelligence/models',json={'data':{'project_entity_id':'project:pred-v2560','model_key':'monitor-model','name':'Monitoring Model','model_kind':'statistical','runtime_product':'lab','visibility':'public'}}); assert r.status_code==200,r.text; return r.json()['id']

def test_v2560_readiness_and_boundaries(tmp_path):
    app,c=app_client(tmp_path); seed(app); d=c.get('/v1/predictive-intelligence/readiness').json()
    assert d['release']=='2.56.0' and d['migration_0060_applied'] is True and migration_status(app.state.database)['pending']==[]
    for k in ('monitoring_study_registry_by_core','detection_rule_registry_by_core','anomaly_evidence_registry_by_core','change_point_evidence_registry_by_core','early_warning_signal_registry_by_core','monitoring_episode_registry_by_core','reproducible_monitoring_packages_by_core'): assert d[k] is True,k
    for k in ('anomaly_detection_by_core','change_point_detection_by_core','early_warning_computation_by_core','threshold_optimization_by_core','alert_dispatch_by_core','causal_attribution_by_core','automatic_intervention_by_core','automatic_truth_promotion'): assert d[k] is False,k

def test_monitoring_evidence_and_package(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid=model(c)
    st=c.post('/v1/predictive-intelligence/monitoring-studies',json={'data':{'project_entity_id':'project:pred-v2560','model_id':mid,'study_key':'ops-watch','name':'Operations Watch','monitoring_kind':'multi-signal','monitoring_scope':{'frequency':'hourly'},'visibility':'public'}}); assert st.status_code==200,st.text; sid=st.json()['id']; assert st.json()['externally_computed'] is True
    rule=c.post(f'/v1/predictive-intelligence/monitoring-studies/{sid}/rules',json={'data':{'rule_key':'external-detector','rule_kind':'composite','method':'lab://detectors/v1','threshold':{'anomaly_score':3.0},'runtime_product':'lab','runtime_ref':'lab://runbook/detect'}}); assert rule.status_code==200,rule.text; rid=rule.json()['id']; assert rule.json()['externally_defined'] is True
    a=c.post(f'/v1/predictive-intelligence/monitoring-studies/{sid}/anomalies',json={'data':{'detection_rule_id':rid,'observation_key':'a-1','observed_at':'2026-09-14T12:00:00Z','anomaly_kind':'residual','score':{'z':3.4},'threshold':{'z':3.0},'evidence_ref':'lab://monitor/a-1'}}); assert a.status_code==200,a.text and a.json()['externally_detected'] is True
    cp=c.post(f'/v1/predictive-intelligence/monitoring-studies/{sid}/change-points',json={'data':{'detection_rule_id':rid,'change_key':'cp-1','change_time':'2026-09-14T12:30:00Z','method':'external-bocpd','statistic':{'posterior_change_probability':0.81},'uncertainty':{'window_minutes':15},'evidence_ref':'lab://monitor/cp-1'}}); assert cp.status_code==200,cp.text and cp.json()['externally_detected'] is True
    ew=c.post(f'/v1/predictive-intelligence/monitoring-studies/{sid}/early-warning-signals',json={'data':{'detection_rule_id':rid,'signal_key':'ew-1','signal_kind':'forecast-risk','observed_at':'2026-09-14T12:35:00Z','indicator':{'risk_probability':0.72},'threshold':{'risk_probability':0.65},'lead_time':{'hours':6},'evidence_ref':'lab://monitor/ew-1'}}); assert ew.status_code==200,ew.text and ew.json()['externally_detected'] is True
    ep=c.post(f'/v1/predictive-intelligence/monitoring-studies/{sid}/episodes',json={'data':{'episode_key':'episode-1','episode_kind':'regime-shift-watch','start_time':'2026-09-14T12:00:00Z','evidence_refs':[a.json()['id'],cp.json()['id'],ew.json()['id']],'descriptive_summary':{'note':'externally detected signals grouped for review'}}}); assert ep.status_code==200,ep.text
    pkg=c.post(f'/v1/predictive-intelligence/monitoring-studies/{sid}/packages',json={'data':{'environment':{'runtime':'lab','version':'test'},'created_by':'test'}}); assert pkg.status_code==200,pkg.text and len(pkg.json()['content_hash'])==64
    b=c.get(f'/v1/predictive-intelligence/monitoring-studies/{sid}/bundle'); assert b.status_code==200,b.text; body=b.json(); assert body['contract']=='sc.predictive.monitoring-package.v1'; assert len(body['detection_rules'])==1 and len(body['anomaly_observations'])==1 and len(body['change_points'])==1 and len(body['early_warning_signals'])==1 and len(body['monitoring_episodes'])==1 and len(body['packages'])==1
    mb=c.get(f'/v1/predictive-intelligence/models/{mid}/bundle').json(); assert len(mb['monitoring_studies'])==1

def test_detection_and_intervention_fields_rejected(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    r=c.post('/v1/predictive-intelligence/monitoring-studies',json={'data':{'project_entity_id':'project:pred-v2560','study_key':'bad','name':'Bad','monitoring_kind':'anomaly','anomaly_detect_by_core':True}}); assert r.status_code==422 and 'does not fit' in r.text
    r=c.post('/v1/predictive-intelligence/monitoring-studies',json={'data':{'project_entity_id':'project:pred-v2560','study_key':'bad2','name':'Bad 2','monitoring_kind':'early-warning','automatic_intervention_by_core':True}}); assert r.status_code==422 and 'does not fit' in r.text
