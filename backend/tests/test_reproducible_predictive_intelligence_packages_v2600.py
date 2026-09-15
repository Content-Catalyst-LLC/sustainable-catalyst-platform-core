from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2600.db'}",version='2.60.0'))
    return app,TestClient(app)


def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:pred-v2600',entity_type='research-project',slug='pred-v2600',name='Reproducible Predictive Project',visibility='public'))
        db.commit()


def model(c):
    r=c.post('/v1/predictive-intelligence/models',json={'data':{'project_entity_id':'project:pred-v2600','model_key':'package-model','name':'Package Model','model_kind':'statistical','runtime_product':'lab','visibility':'public'}})
    assert r.status_code==200,r.text
    return r.json()['id']


def test_v2600_readiness_and_boundaries(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    d=c.get('/v1/predictive-intelligence/readiness').json()
    assert d['release']=='2.60.0' and d['migration_0064_applied'] is True and migration_status(app.state.database)['pending']==[]
    for k in ('reproducible_predictive_package_registry_by_core','predictive_package_component_manifest_by_core','predictive_package_artifact_registry_by_core','predictive_package_environment_registry_by_core','predictive_package_verification_registry_by_core','predictive_package_review_registry_by_core','immutable_predictive_package_snapshots_by_core','cross_predictive_layer_packaging_by_core'):
        assert d[k] is True,k
    for k in ('predictive_execution_by_core','model_refitting_by_core','forecast_regeneration_by_core','backtest_reexecution_by_core','calibration_reexecution_by_core','causal_estimation_by_core','decision_optimization_by_core','automatic_reproduction_by_core','automatic_truth_promotion'):
        assert d[k] is False,k


def test_reproducible_predictive_package_round_trip_and_hash_chain(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid=model(c)
    r=c.post('/v1/predictive-intelligence/packages',json={'data':{'project_entity_id':'project:pred-v2600','package_key':'forecast-review-2026','name':'Forecast Review 2026','scope':{'purpose':'reproduction-and-review'},'visibility':'public'}})
    assert r.status_code==200,r.text; pid=r.json()['id']; assert r.json()['contract_version']=='sc.predictive.reproducible-package.v1'
    co=c.post(f'/v1/predictive-intelligence/packages/{pid}/components',json={'data':{'component_key':'model','component_kind':'model','component_ref':mid,'snapshot':{'version':'external-v1'}}}); assert co.status_code==200,co.text
    exthash='a'*64
    co2=c.post(f'/v1/predictive-intelligence/packages/{pid}/components',json={'data':{'component_key':'external-notebook','component_kind':'external','component_ref':'lab://notebooks/reproduce-2600','content_hash':exthash,'required':False}}); assert co2.status_code==200,co2.text
    ar=c.post(f'/v1/predictive-intelligence/packages/{pid}/artifacts',json={'data':{'artifact_key':'model-card','artifact_kind':'report','artifact_ref':'library://predictive/model-card.pdf','media_type':'application/pdf','content_hash':'b'*64,'size_bytes':1234}}); assert ar.status_code==200,ar.text
    en=c.post(f'/v1/predictive-intelligence/packages/{pid}/environments',json={'data':{'environment_key':'lab-runtime','runtime_product':'lab','runtime_version':'1.0','environment':{'python':'3.12','packages':['numpy']},'lockfile_hash':'c'*64}}); assert en.status_code==200,en.text
    ve=c.post(f'/v1/predictive-intelligence/packages/{pid}/verifications',json={'data':{'verification_key':'integrity-1','verification_kind':'integrity','status':'pass','result':{'hashes_verified':True},'evidence_ref':'workbench://verification/2600','verifier':'workbench'}}); assert ve.status_code==200,ve.text and ve.json()['externally_computed'] is True
    rv=c.post(f'/v1/predictive-intelligence/packages/{pid}/reviews',json={'data':{'review_key':'technical-1','review_kind':'technical','status':'reviewed','reviewer':'reviewer','findings':{'reproducible':True}}}); assert rv.status_code==200,rv.text
    s1=c.post(f'/v1/predictive-intelligence/packages/{pid}/snapshots',json={'data':{'created_by':'test'}}); assert s1.status_code==200,s1.text and s1.json()['revision']==1 and len(s1.json()['content_hash'])==64
    s2=c.post(f'/v1/predictive-intelligence/packages/{pid}/snapshots',json={'data':{'created_by':'test'}}); assert s2.status_code==200,s2.text and s2.json()['revision']==2 and s2.json()['previous_snapshot_hash']==s1.json()['content_hash']
    bundle=c.get(f'/v1/predictive-intelligence/packages/{pid}/bundle'); assert bundle.status_code==200,bundle.text; body=bundle.json(); assert body['contract']=='sc.predictive.reproducible-package.v1'; assert len(body['components'])==2 and len(body['artifacts'])==1 and len(body['environments'])==1 and len(body['verifications'])==1 and len(body['reviews'])==1 and len(body['snapshots'])==2
    mb=c.get(f'/v1/predictive-intelligence/models/{mid}/bundle').json(); assert len(mb['reproducible_predictive_packages'])==1


def test_reproducible_predictive_package_project_integrity_and_compute_rejection(tmp_path):
    app,c=app_client(tmp_path); seed(app); mid=model(c)
    r=c.post('/v1/predictive-intelligence/packages',json={'data':{'project_entity_id':'project:pred-v2600','package_key':'guarded','name':'Guarded','visibility':'private'}}); pid=r.json()['id']
    bad=c.post(f'/v1/predictive-intelligence/packages/{pid}/components',json={'data':{'component_key':'missing','component_kind':'model','component_ref':'missing-model'}}); assert bad.status_code==422
    compute=c.post('/v1/predictive-intelligence/packages',json={'data':{'project_entity_id':'project:pred-v2600','package_key':'bad','name':'Bad','reproduce_by_core':True}}); assert compute.status_code==422 and 'does not fit' in compute.text
