from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity, CausalGraphRecord, CausalVariableRecord


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2580.db'}",version='2.58.0'))
    return app,TestClient(app)


def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:pred-v2580',entity_type='research-project',slug='pred-v2580',name='Causal Predictive Project',visibility='public'))
        graph=CausalGraphRecord(id='graph-v2580',graph_key='risk-dag',name='Risk DAG',project_entity_id='project:pred-v2580',visibility='public')
        db.add(graph); db.flush()
        db.add(CausalVariableRecord(id='var-treatment',graph_id=graph.id,variable_key='policy',label='Policy',causal_role='treatment'))
        db.add(CausalVariableRecord(id='var-outcome',graph_id=graph.id,variable_key='risk',label='Risk',causal_role='outcome'))
        db.commit()


def model_target_feature(c):
    m=c.post('/v1/predictive-intelligence/models',json={'data':{'project_entity_id':'project:pred-v2580','model_key':'risk-model','name':'Risk Model','model_kind':'statistical','runtime_product':'lab','visibility':'public'}})
    assert m.status_code==200,m.text; mid=m.json()['id']
    t=c.post(f'/v1/predictive-intelligence/models/{mid}/targets',json={'data':{'target_key':'risk','label':'Risk','value_kind':'numeric'}})
    assert t.status_code==200,t.text
    f=c.post(f'/v1/predictive-intelligence/models/{mid}/features',json={'data':{'feature_key':'policy','label':'Policy','feature_role':'predictor','source_product':'external','source_ref':'dataset://policy'}})
    assert f.status_code==200,f.text
    return mid,t.json()['id'],f.json()['id']


def test_v2580_readiness_and_boundaries(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    d=c.get('/v1/predictive-intelligence/readiness').json()
    assert d['release']=='2.58.0' and d['migration_0062_applied'] is True and migration_status(app.state.database)['pending']==[]
    for k in ('causal_predictive_study_registry_by_core','causal_variable_binding_registry_by_core','intervention_scenario_registry_by_core','counterfactual_forecast_provenance_by_core','causal_effect_evidence_registry_by_core','causal_predictive_evaluation_evidence_by_core','causal_predictive_handoff_registry_by_core','reproducible_causal_predictive_packages_by_core'):
        assert d[k] is True,k
    for k in ('causal_structure_learning_by_core','causal_identification_by_core','causal_effect_estimation_by_core','counterfactual_execution_by_core','intervention_simulation_by_core','causal_predictive_metric_computation_by_core','decision_optimization_by_core','automatic_intervention_by_core','automatic_truth_promotion'):
        assert d[k] is False,k


def test_causal_predictive_round_trip_and_package(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid,tid,fid=model_target_feature(c)
    st=c.post('/v1/predictive-intelligence/causal-predictive-studies',json={'data':{'project_entity_id':'project:pred-v2580','predictive_model_id':mid,'causal_graph_id':'graph-v2580','target_id':tid,'study_key':'policy-risk','name':'Policy Risk Integration','integration_kind':'intervention-forecast','estimand_scope':{'estimand':'ATE'},'visibility':'public'}})
    assert st.status_code==200,st.text; sid=st.json()['id']; assert st.json()['externally_computed'] is True
    b1=c.post(f'/v1/predictive-intelligence/causal-predictive-studies/{sid}/variable-bindings',json={'data':{'binding_key':'policy-binding','causal_variable_id':'var-treatment','predictive_feature_id':fid,'binding_role':'treatment'}}); assert b1.status_code==200,b1.text
    b2=c.post(f'/v1/predictive-intelligence/causal-predictive-studies/{sid}/variable-bindings',json={'data':{'binding_key':'risk-binding','causal_variable_id':'var-outcome','predictive_target_id':tid,'binding_role':'outcome'}}); assert b2.status_code==200,b2.text
    sc=c.post(f'/v1/predictive-intelligence/causal-predictive-studies/{sid}/intervention-scenarios',json={'data':{'scenario_key':'policy-up','name':'Policy Increase','intervention':{'variable':'policy','set':1},'baseline':{'policy':0},'assumptions':['consistency'],'horizon':{'days':30},'source_ref':'lab://scenario/policy-up'}}); assert sc.status_code==200,sc.text; scenario_id=sc.json()['id']
    cf=c.post(f'/v1/predictive-intelligence/causal-predictive-studies/{sid}/counterfactual-forecasts',json={'data':{'intervention_scenario_id':scenario_id,'forecast_key':'cf-1','issued_at':'2026-09-15T00:00:00Z','horizon':{'days':30},'factual_forecast':{'risk':0.62},'counterfactual_forecast':{'risk':0.48},'contrast':{'difference':-0.14},'uncertainty':{'interval':[-0.22,-0.06]},'runtime_product':'lab','runtime_ref':'lab://run/cf-1'}}); assert cf.status_code==200,cf.text and cf.json()['externally_computed'] is True
    ee=c.post(f'/v1/predictive-intelligence/causal-predictive-studies/{sid}/effect-evidence',json={'data':{'evidence_key':'effect-1','estimand':'ATE','effect':{'estimate':-0.12},'uncertainty':{'lower':-0.2,'upper':-0.04},'assumptions':['exchangeability'],'evidence_ref':'lab://causal/effect-1'}}); assert ee.status_code==200,ee.text and ee.json()['externally_computed'] is True
    ev=c.post(f'/v1/predictive-intelligence/causal-predictive-studies/{sid}/evaluations',json={'data':{'evaluation_key':'eval-1','metric_evidence':{'external_rmse':0.11},'diagnostic_evidence':{'overlap':'adequate'},'comparison_scope':{'scenario':'policy-up'},'evidence_ref':'workbench://eval/causal-1'}}); assert ev.status_code==200,ev.text
    ho=c.post(f'/v1/predictive-intelligence/causal-predictive-studies/{sid}/handoffs',json={'data':{'target_product':'decision-studio','purpose':'decision-scenario-review','request':{'study_id':sid},'response_ref':'decision-studio://packet/1'}}); assert ho.status_code==200,ho.text
    pkg=c.post(f'/v1/predictive-intelligence/causal-predictive-studies/{sid}/packages',json={'data':{'environment':{'runtime':'lab','version':'test'},'created_by':'test'}}); assert pkg.status_code==200,pkg.text and len(pkg.json()['content_hash'])==64
    body=c.get(f'/v1/predictive-intelligence/causal-predictive-studies/{sid}/bundle').json(); assert body['contract']=='sc.predictive.causal-package.v1'; assert len(body['variable_bindings'])==2 and len(body['intervention_scenarios'])==1 and len(body['counterfactual_forecasts'])==1 and len(body['causal_effect_evidence'])==1 and len(body['evaluations'])==1 and len(body['handoffs'])==1 and len(body['packages'])==1
    mb=c.get(f'/v1/predictive-intelligence/models/{mid}/bundle').json(); assert len(mb['causal_predictive_studies'])==1


def test_causal_predictive_cross_project_and_compute_fields_rejected(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid,tid,_=model_target_feature(c)
    bad=c.post('/v1/predictive-intelligence/causal-predictive-studies',json={'data':{'project_entity_id':'project:pred-v2580','predictive_model_id':mid,'causal_graph_id':'graph-v2580','target_id':tid,'study_key':'bad','name':'Bad','causal_effect_estimate_by_core':True}})
    assert bad.status_code==422 and 'does not fit' in bad.text
