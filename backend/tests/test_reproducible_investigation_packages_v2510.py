from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity

def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2510.db'}",version='2.51.0')); return app,TestClient(app)

def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:pkg-v2510',entity_type='research-project',slug='pkg-v2510',name='Package Project',visibility='public')); db.commit()

def investigation(c):
    r=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:pkg-v2510','investigation_key':'case','name':'Reproducible Case','visibility':'public'}}); assert r.status_code==200,r.text; return r.json()['id']

def test_v2510_readiness_and_boundaries(tmp_path):
    app,c=app_client(tmp_path); seed(app); r=c.get('/v1/open-forensics/readiness').json(); assert r['release']=='2.51.0' and r['migration_0055_applied'] is True
    for k in ('reproducible_investigation_packages_by_core','frozen_cross_forensics_component_manifests_by_core','investigation_package_artifact_registry_by_core','investigation_environment_manifest_capture_by_core','investigation_package_integrity_verification_by_core','independent_review_recording_by_core','portable_investigation_review_bundles_by_core'): assert r[k] is True,k
    for k in ('reproducibility_equals_truth_by_core','automatic_package_authenticity_determination_by_core','automatic_package_admissibility_determination_by_core','automatic_truth_promotion'): assert r[k] is False,k
    assert migration_status(app.state.database)['pending']==[]

def test_package_freezes_nine_cross_forensics_components(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid=investigation(c)
    ev=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'e1','evidence_kind':'documentary','label':'Record','content_hash':'a'*64}}); assert ev.status_code==200,ev.text
    p=c.post(f'/v1/open-forensics/investigations/{iid}/reproducible-packages',json={'data':{'package_key':'review','label':'Review package','visibility':'public'}}); assert p.status_code==200,p.text; body=p.json(); assert len(body['components'])==9
    assert {x['component_kind'] for x in body['components']}=={'evidence-provenance','custody-integrity','claims-hypotheses','timeline-reconstruction','spatial-temporal','media-provenance','quantitative-reconstruction','documentary-evidence','research-graphs'}
    assert body['package']['manifest_json']['frozen'] is True and body['package']['manifest_json']['reproducibility_equals_truth'] is False

def test_package_artifact_verify_review_snapshot_and_portable(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid=investigation(c)
    p=c.post(f'/v1/open-forensics/investigations/{iid}/reproducible-packages',json={'data':{'package_key':'p1','label':'Portable','visibility':'public'}}); assert p.status_code==200,p.text; pid=p.json()['package']['id']
    a=c.post(f'/v1/open-forensics/investigations/{iid}/reproducible-packages/{pid}/artifacts',json={'data':{'artifact_key':'source','source_ref':'external://archive/source.pdf','content_hash':'b'*64}}); assert a.status_code==200,a.text
    v=c.post(f'/v1/open-forensics/investigations/{iid}/reproducible-packages/{pid}/verify',json={'data':{'compare_current_state':True,'verified_by':'test'}}); assert v.status_code==200,v.text; assert v.json()['result']=='verified'
    rv=c.post(f'/v1/open-forensics/investigations/{iid}/reproducible-packages/{pid}/reviews',json={'data':{'reviewer_ref':'reviewer:test','scope':{'components':'all'},'limitations':['Independent review does not establish truth.']}}); assert rv.status_code==200,rv.text
    s=c.post(f'/v1/open-forensics/investigations/{iid}/reproducible-packages/{pid}/snapshots',json={'data':{'created_by':'test'}}); assert s.status_code==200,s.text and len(s.json()['content_hash'])==64
    portable=c.get(f'/v1/open-forensics/investigations/{iid}/reproducible-packages/{pid}/portable'); assert portable.status_code==200,portable.text; assert portable.json()['reproducibility_equals_truth'] is False and portable.json()['authenticity_determined'] is False
    pub=c.get(f'/api/v1/open-forensics/investigations/{iid}/reproducible-packages/{pid}'); assert pub.status_code in (200,401,403)

def test_package_determinative_fields_rejected(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid=investigation(c)
    bad=c.post(f'/v1/open-forensics/investigations/{iid}/reproducible-packages',json={'data':{'package_key':'bad','label':'Bad','truth_value':True}}); assert bad.status_code==422 and 'does not determine truth' in bad.text
