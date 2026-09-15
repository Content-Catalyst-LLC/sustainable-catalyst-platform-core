from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2590.db'}",version='2.59.0'))
    return app,TestClient(app)


def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:pred-v2590',entity_type='research-project',slug='pred-v2590',name='Predictive Decision Project',visibility='public'))
        db.commit()


def model(c):
    r=c.post('/v1/predictive-intelligence/models',json={'data':{'project_entity_id':'project:pred-v2590','model_key':'decision-risk-model','name':'Decision Risk Model','model_kind':'statistical','runtime_product':'lab','visibility':'public'}})
    assert r.status_code==200,r.text
    return r.json()['id']


def test_v2590_readiness_and_boundaries(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    d=c.get('/v1/predictive-intelligence/readiness').json()
    assert d['release']=='2.59.0' and d['migration_0063_applied'] is True and migration_status(app.state.database)['pending']==[]
    for k in ('predictive_decision_study_registry_by_core','decision_option_registry_by_core','decision_criterion_registry_by_core','decision_evidence_binding_registry_by_core','decision_scenario_assessment_registry_by_core','decision_evaluation_evidence_registry_by_core','decision_handoff_registry_by_core','reproducible_predictive_decision_packages_by_core'):
        assert d[k] is True,k
    for k in ('utility_computation_by_core','regret_computation_by_core','decision_ranking_by_core','decision_recommendation_by_core','decision_optimization_by_core','constraint_solving_by_core','decision_action_execution_by_core','automatic_action_selection','automatic_intervention_by_core','automatic_truth_promotion'):
        assert d[k] is False,k


def test_predictive_decision_round_trip_and_package(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid=model(c)
    st=c.post('/v1/predictive-intelligence/decision-studies',json={'data':{'project_entity_id':'project:pred-v2590','predictive_model_id':mid,'study_key':'adaptation-choice','name':'Adaptation Choice','decision_kind':'multi-criteria','objective_scope':{'goal':'reduce risk'},'decision_horizon':{'years':5},'constraints':['budget-bounded'],'visibility':'public'}})
    assert st.status_code==200,st.text; sid=st.json()['id']; assert st.json()['externally_computed'] is True
    op=c.post(f'/v1/predictive-intelligence/decision-studies/{sid}/options',json={'data':{'option_key':'option-a','name':'Option A','action':{'intervention':'A'},'feasibility':{'status':'feasible'},'constraints':['budget']}}); assert op.status_code==200,op.text; oid=op.json()['id']
    cr=c.post(f'/v1/predictive-intelligence/decision-studies/{sid}/criteria',json={'data':{'criterion_key':'risk','name':'Residual Risk','value_kind':'numeric','preference_direction':'minimize','threshold':{'max':0.3}}}); assert cr.status_code==200,cr.text; cid=cr.json()['id']
    eb=c.post(f'/v1/predictive-intelligence/decision-studies/{sid}/evidence-bindings',json={'data':{'binding_key':'risk-evidence','option_id':oid,'criterion_id':cid,'evidence_kind':'external','evidence_ref':'decision-studio://evidence/risk-a','interpretation':{'risk':0.24},'uncertainty':{'interval':[0.2,0.29]}}}); assert eb.status_code==200,eb.text and eb.json()['externally_computed'] is True
    sa=c.post(f'/v1/predictive-intelligence/decision-studies/{sid}/scenario-assessments',json={'data':{'option_id':oid,'assessment_key':'scenario-1','scenario':{'climate':'high'},'outcome_evidence':{'loss':12},'risk_evidence':{'tail_probability':0.08},'uncertainty':{'source':'external'},'runtime_product':'decision-studio','runtime_ref':'decision-studio://assessment/1'}}); assert sa.status_code==200,sa.text
    ev=c.post(f'/v1/predictive-intelligence/decision-studies/{sid}/evaluations',json={'data':{'evaluation_key':'eval-a','option_id':oid,'criterion_id':cid,'metric_evidence':{'expected_loss':12},'tradeoff_evidence':{'cost_vs_risk':'external'},'regret_evidence':{'max_regret':3.1},'evidence_ref':'workbench://decision/eval-a'}}); assert ev.status_code==200,ev.text and ev.json()['externally_computed'] is True
    ho=c.post(f'/v1/predictive-intelligence/decision-studies/{sid}/handoffs',json={'data':{'target_product':'decision-studio','purpose':'packet-review','request':{'study_id':sid},'response_ref':'decision-studio://packet/2590'}}); assert ho.status_code==200,ho.text
    p1=c.post(f'/v1/predictive-intelligence/decision-studies/{sid}/packages',json={'data':{'environment':{'runtime':'decision-studio'},'created_by':'test'}}); assert p1.status_code==200,p1.text and len(p1.json()['content_hash'])==64 and p1.json()['revision']==1
    p2=c.post(f'/v1/predictive-intelligence/decision-studies/{sid}/packages',json={'data':{'environment':{'runtime':'decision-studio'},'created_by':'test'}}); assert p2.status_code==200,p2.text and p2.json()['revision']==2 and p2.json()['previous_package_hash']==p1.json()['content_hash']
    body=c.get(f'/v1/predictive-intelligence/decision-studies/{sid}/bundle').json(); assert body['contract']=='sc.predictive.decision-package.v1'; assert len(body['options'])==1 and len(body['criteria'])==1 and len(body['evidence_bindings'])==1 and len(body['scenario_assessments'])==1 and len(body['evaluations'])==1 and len(body['handoffs'])==1 and len(body['packages'])==2
    mb=c.get(f'/v1/predictive-intelligence/models/{mid}/bundle').json(); assert len(mb['decision_studies'])==1


def test_predictive_decision_compute_fields_rejected(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid=model(c)
    bad=c.post('/v1/predictive-intelligence/decision-studies',json={'data':{'project_entity_id':'project:pred-v2590','predictive_model_id':mid,'study_key':'bad','name':'Bad','decision_rank_by_core':True}})
    assert bad.status_code==422 and 'does not fit' in bad.text
