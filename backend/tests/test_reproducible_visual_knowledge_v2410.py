from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2410.db'}",version="2.41.0"))
    return app, TestClient(app)


def seed(app, client):
    with app.state.database.session_factory() as db:
        db.add(Entity(id="project:repro",entity_type="research-project",slug="repro",name="Repro Test",visibility="public")); db.commit()
    obj=client.post('/v1/cross-product-visual-research',json={'data':{'project_entity_id':'project:repro','object_key':'energy-composite','name':'Energy Composite','visibility':'public'}})
    assert obj.status_code==200,obj.text
    oid=obj.json()['id']
    mem=client.post(f'/v1/cross-product-visual-research/{oid}/members',json={'data':{'member_key':'lab-result','member_kind':'result','source_product':'lab','label':'Lab result','external_ref':'sc://lab/results/1','source_ref':{'version':'0.103.0'}}})
    assert mem.status_code==200,mem.text
    return oid


def create_package(client, oid):
    r=client.post('/v1/reproducible-visual-knowledge',json={'data':{'project_entity_id':'project:repro','source_object_id':oid,'package_key':'repro-1','name':'Reproducible Energy Knowledge','visibility':'public','reproducibility_level':'replay-ready'}})
    assert r.status_code==200,r.text; return r.json()['id']


def test_readiness_health_and_migration_0045(tmp_path):
    app,c=app_client(tmp_path); seed(app,c)
    h=c.get('/health').json(); assert h['version']=='2.41.0' and h['reproducible_visual_knowledge_layer'] is True
    r=c.get('/v1/reproducible-visual-knowledge/readiness').json(); assert r['release']=='2.41.0' and r['migration_0045_applied'] is True
    assert r['specialist_execution_by_core'] is False and r['replay_execution_by_core'] is False and r['automatic_truth_promotion'] is False
    assert migration_status(app.state.database)['pending']==[]


def test_manifest_replay_verification_snapshot_and_portability(tmp_path):
    app,c=app_client(tmp_path); oid=seed(app,c); pid=create_package(c,oid)
    inp=c.post(f'/v1/reproducible-visual-knowledge/{pid}/inputs',json={'data':{'input_key':'lab-result','label':'Lab result','input_role':'artifact','source_product':'lab','source_ref':'sc://lab/results/1','source_version':'0.103.0','content_hash':'a'*64}})
    assert inp.status_code==200,inp.text
    env=c.post(f'/v1/reproducible-visual-knowledge/{pid}/environments',json={'data':{'environment_key':'lab-env','name':'Lab runtime','runtime_versions':{'python':'3.12'},'dependencies':['numpy==2.0'],'container_ref':'ghcr.io/content-catalyst/lab:0.103.0','container_digest':'sha256:'+'b'*64,'code_ref':'git:abc123','random_seed':42,'deterministic_claim':True}})
    assert env.status_code==200,env.text
    plan=c.post(f'/v1/reproducible-visual-knowledge/{pid}/replay-plans',json={'data':{'plan_key':'replay','name':'Replay analysis','environment_id':env.json()['id'],'steps':[{'target_product':'lab','operation':'recompute-study','input_keys':['lab-result']}],'expected_outputs':[{'role':'visual-spec'}]}})
    assert plan.status_code==200,plan.text
    mf=c.get(f'/v1/reproducible-visual-knowledge/{pid}/manifest').json(); assert len(mf['fingerprint'])==64 and mf['all_inputs_content_hashed'] is True and mf['replay_ready'] is True
    valid=c.get(f'/v1/reproducible-visual-knowledge/{pid}/validate').json(); assert valid['valid'] is True
    integ=c.post(f'/v1/reproducible-visual-knowledge/{pid}/verifications',json={'data':{'verification_kind':'integrity','expected_fingerprint':mf['fingerprint']}}); assert integ.status_code==200 and integ.json()['status']=='match'
    denied=c.post(f'/v1/reproducible-visual-knowledge/{pid}/verifications',json={'data':{'verification_kind':'output','verifier_product':'platform-core','expected_fingerprint':mf['fingerprint']}}); assert denied.status_code==422
    ext=c.post(f'/v1/reproducible-visual-knowledge/{pid}/verifications',json={'data':{'verification_kind':'output','verifier_product':'lab','external_run_ref':'sc://lab/runs/replay-1','expected_fingerprint':mf['fingerprint'],'observed_fingerprint':mf['fingerprint']}}); assert ext.status_code==200 and ext.json()['status']=='match'
    s1=c.post(f'/v1/reproducible-visual-knowledge/{pid}/snapshots',json={'data':{'created_by':'test'}}).json(); s2=c.post(f'/v1/reproducible-visual-knowledge/{pid}/snapshots',json={'data':{'created_by':'test'}}).json(); assert s1['revision']==1 and s2['revision']==2 and len(s1['content_hash'])==64 and len(s1['manifest_hash'])==64
    portable=c.get(f'/v1/reproducible-visual-knowledge/{pid}/portable-package').json(); assert portable['portable'] is True and portable['execution_embedded'] is False and portable['validation']['valid'] is True


def test_replay_plan_cannot_request_core_execution(tmp_path):
    app,c=app_client(tmp_path); oid=seed(app,c); pid=create_package(c,oid)
    bad=c.post(f'/v1/reproducible-visual-knowledge/{pid}/replay-plans',json={'data':{'plan_key':'bad','name':'Bad','steps':[{'target_product':'lab','operation':'run','execute_by_core':True}]}})
    assert bad.status_code==422
