from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity

def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2550.db'}",version='2.55.0'))
    return app,TestClient(app)

def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:pred-v2550',entity_type='research-project',slug='pred-v2550',name='Ensemble Project',visibility='public')); db.commit()

def model(c,key):
    r=c.post('/v1/predictive-intelligence/models',json={'data':{'project_entity_id':'project:pred-v2550','model_key':key,'name':key.title(),'model_kind':'statistical','runtime_product':'lab','visibility':'public'}}); assert r.status_code==200,r.text; return r.json()['id']

def test_v2550_readiness_and_boundaries(tmp_path):
    app,c=app_client(tmp_path); seed(app); d=c.get('/v1/predictive-intelligence/readiness').json()
    assert d['release']=='2.55.0' and d['migration_0059_applied'] is True and migration_status(app.state.database)['pending']==[]
    for k in ('ensemble_registry_by_core','ensemble_member_registry_by_core','ensemble_forecast_provenance_by_core','model_comparison_study_registry_by_core','comparison_candidate_registry_by_core','comparative_metric_evidence_by_core','pairwise_comparison_evidence_by_core','reproducible_model_comparison_packages_by_core'): assert d[k] is True,k
    for k in ('ensemble_construction_by_core','ensemble_weight_optimization_by_core','ensemble_forecast_execution_by_core','model_comparison_metric_computation_by_core','statistical_significance_computation_by_core','model_ranking_by_core','automatic_model_selection','automatic_truth_promotion'): assert d[k] is False,k

def test_ensemble_comparison_and_package(tmp_path):
    app,c=app_client(tmp_path); seed(app); m1=model(c,'model-a'); m2=model(c,'model-b')
    e=c.post('/v1/predictive-intelligence/ensembles',json={'data':{'project_entity_id':'project:pred-v2550','ensemble_key':'blend','name':'External Blend','ensemble_kind':'weighted-average','combination_rule':{'source':'lab://ensemble/blend'},'visibility':'public'}}); assert e.status_code==200,e.text; eid=e.json()['id']; assert e.json()['externally_defined'] is True
    a=c.post(f'/v1/predictive-intelligence/ensembles/{eid}/members',json={'data':{'model_id':m1,'member_key':'a','role':'member','weight':0.6}}); assert a.status_code==200,a.text
    b=c.post(f'/v1/predictive-intelligence/ensembles/{eid}/members',json={'data':{'model_id':m2,'member_key':'b','role':'member','weight':0.4}}); assert b.status_code==200,b.text
    f=c.post(f'/v1/predictive-intelligence/ensembles/{eid}/forecasts',json={'data':{'representation':'binary-event','forecast':{'probability':0.64},'member_forecast_refs':['lab://a/f1','lab://b/f1'],'source_ref':'lab://ensemble/f1'}}); assert f.status_code==200,f.text and f.json()['externally_generated'] is True
    eb=c.get(f'/v1/predictive-intelligence/ensembles/{eid}/bundle'); assert eb.status_code==200,eb.text; assert len(eb.json()['members'])==2 and len(eb.json()['forecasts'])==1
    st=c.post('/v1/predictive-intelligence/comparison-studies',json={'data':{'project_entity_id':'project:pred-v2550','comparison_key':'q3','name':'Q3 model comparison','evaluation_scope':{'window':'2026-Q3'},'visibility':'public'}}); assert st.status_code==200,st.text; sid=st.json()['id']; assert st.json()['externally_computed'] is True
    c1=c.post(f'/v1/predictive-intelligence/comparison-studies/{sid}/candidates',json={'data':{'candidate_key':'a','candidate_kind':'model','candidate_ref':m1,'label':'Model A'}}); assert c1.status_code==200,c1.text; c1id=c1.json()['id']
    c2=c.post(f'/v1/predictive-intelligence/comparison-studies/{sid}/candidates',json={'data':{'candidate_key':'ens','candidate_kind':'ensemble','candidate_ref':eid,'label':'Blend'}}); assert c2.status_code==200,c2.text; c2id=c2.json()['id']
    ev=c.post(f'/v1/predictive-intelligence/comparison-studies/{sid}/evidence',json={'data':{'candidate_id':c2id,'evidence_key':'brier','metric_family':'proper-scoring-rule','metric_name':'Brier score','metric_value':0.16,'uncertainty':{'bootstrap_se':0.01},'evidence_ref':'lab://compare/brier'}}); assert ev.status_code==200,ev.text and ev.json()['externally_computed'] is True
    pw=c.post(f'/v1/predictive-intelligence/comparison-studies/{sid}/pairwise-evidence',json={'data':{'left_candidate_id':c2id,'right_candidate_id':c1id,'comparison_kind':'skill-difference','statistic':{'metric':'Brier score','difference':-0.02},'uncertainty':{'ci95':[-0.04,-0.001]},'evidence_ref':'lab://compare/pair'}}); assert pw.status_code==200,pw.text and pw.json()['externally_computed'] is True
    pkg=c.post(f'/v1/predictive-intelligence/comparison-studies/{sid}/packages',json={'data':{'environment':{'runtime':'lab','version':'test'},'created_by':'test'}}); assert pkg.status_code==200,pkg.text and len(pkg.json()['content_hash'])==64
    cb=c.get(f'/v1/predictive-intelligence/comparison-studies/{sid}/bundle'); assert cb.status_code==200,cb.text; body=cb.json(); assert body['contract']=='sc.predictive.model-comparison-package.v1' and len(body['candidates'])==2 and len(body['evidence'])==1 and len(body['pairwise_evidence'])==1 and len(body['packages'])==1
    mb=c.get(f'/v1/predictive-intelligence/models/{m1}/bundle').json(); assert len(mb['ensemble_memberships'])==1

def test_core_ranking_and_weight_optimization_rejected(tmp_path):
    app,c=app_client(tmp_path); seed(app); m=model(c,'model-a')
    r=c.post('/v1/predictive-intelligence/ensembles',json={'data':{'project_entity_id':'project:pred-v2550','ensemble_key':'bad','name':'Bad','ensemble_kind':'weighted-average','ensemble_weight_optimize_by_core':True}}); assert r.status_code==422 and 'does not fit' in r.text
    st=c.post('/v1/predictive-intelligence/comparison-studies',json={'data':{'project_entity_id':'project:pred-v2550','comparison_key':'badcmp','name':'Bad comparison','rank_models_by_core':True}}); assert st.status_code==422 and 'does not fit' in st.text
