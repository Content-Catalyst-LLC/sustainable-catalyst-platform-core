from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2430.db'}",version='2.50.0'))
    return app,TestClient(app)


def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:custody-v2430',entity_type='research-project',slug='custody-v2430',name='Custody v2430',visibility='public')); db.commit()


def create_case(c):
    inv=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:custody-v2430','investigation_key':'case-243','name':'Case 243','visibility':'public'}}); assert inv.status_code==200,inv.text
    iid=inv.json()['id']
    ev=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'digital-1','evidence_kind':'digital','label':'Digital evidence','content_hash':'a'*64}}); assert ev.status_code==200,ev.text
    return iid,ev.json()['id']


def custodian(c,iid,key):
    r=c.post(f'/v1/open-forensics/investigations/{iid}/custodians',json={'data':{'custodian_key':key,'display_name':key.title(),'actor_ref':f'external:{key}'}}); assert r.status_code==200,r.text; return r.json()['id']


def test_v2430_readiness_and_boundaries(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    h=c.get('/health').json(); assert h['version']=='2.50.0' and h['open_forensics'] is True
    r=c.get('/v1/open-forensics/readiness').json(); assert r['release']=='2.50.0' and r['migration_0046_applied'] and r['migration_0047_applied']
    for key in ('chain_of_custody_by_core','chain_of_custody_recording_by_core','tamper_evident_custody_event_chain_by_core','evidence_integrity_verification_by_core','seal_state_recording_by_core','custody_continuity_analysis_by_core','external_custody_attestation_binding_by_core'):
        assert r[key] is True,key
    for key in ('custody_transfer_attestation_by_core','physical_transfer_verification_by_core','identity_verification_by_core','authenticity_determination_by_core','legal_admissibility_determination_by_core','ownership_determination_by_core','causal_conclusion_by_core','legal_conclusion_by_core','automatic_truth_promotion'):
        assert r[key] is False,key
    assert migration_status(app.state.database)['pending']==[]


def test_hash_chained_custody_integrity_seals_and_snapshot(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,eid=create_case(c); alice=custodian(c,iid,'alice'); bob=custodian(c,iid,'bob')
    one=c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/custody-events',json={'data':{'event_kind':'intake','to_custodian_id':alice,'location_ref':'vault','external_attestation_ref':'attest:intake'}}); assert one.status_code==200,one.text
    two=c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/custody-events',json={'data':{'event_kind':'transfer','from_custodian_id':alice,'to_custodian_id':bob,'location_ref':'lab','external_attestation_ref':'attest:transfer'}}); assert two.status_code==200,two.text
    assert one.json()['sequence']==1 and two.json()['sequence']==2 and two.json()['previous_event_hash']==one.json()['event_hash']
    chain=c.get(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/custody-chain').json(); assert chain['hash_chain_valid'] is True and chain['gap_count']==0 and chain['continuity_status']=='continuous' and chain['current_custodian_id']==bob
    check=c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/integrity-checks',json={'data':{'check_key':'verify-a','observed_hash':'a'*64,'checker_ref':'hash-tool:v1'}}); assert check.status_code==200 and check.json()['status']=='match'
    bad=c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/integrity-checks',json={'data':{'check_key':'verify-b','observed_hash':'b'*64,'checker_ref':'hash-tool:v1'}}); assert bad.status_code==200 and bad.json()['status']=='mismatch'
    seal=c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/seals',json={'data':{'action':'seal','seal_identifier':'seal-001','custodian_id':bob,'external_attestation_ref':'attest:seal'}}); assert seal.status_code==200 and seal.json()['status']=='sealed' and seal.json()['content_hash_at_seal']=='a'*64
    unseal=c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/seals',json={'data':{'action':'unseal','seal_identifier':'seal-001','custodian_id':bob,'reason':'inspection'}}); assert unseal.status_code==200 and unseal.json()['status']=='unsealed'
    assessment=c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/continuity-assessments',json={'data':{'assessment_key':'continuity-1'}}); assert assessment.status_code==200 and assessment.json()['status']=='continuous' and assessment.json()['hash_chain_valid'] is True
    snap1=c.post(f'/v1/open-forensics/investigations/{iid}/custody-snapshots',json={'data':{'created_by':'test'}}); assert snap1.status_code==200 and snap1.json()['revision']==1 and len(snap1.json()['content_hash'])==64
    snap2=c.post(f'/v1/open-forensics/investigations/{iid}/custody-snapshots',json={'data':{'created_by':'test'}}); assert snap2.status_code==200 and snap2.json()['revision']==2 and snap2.json()['previous_snapshot_hash']==snap1.json()['content_hash']
    bundle=c.get(f'/v1/open-forensics/investigations/{iid}/custody-bundle').json(); assert bundle['contract']=='sc.open-forensics.custody-bundle.v1' and len(bundle['custody_events'])==2 and len(bundle['integrity_checks'])==2


def test_custody_continuity_detects_discontinuity_without_making_legal_claim(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,eid=create_case(c); alice=custodian(c,iid,'alice'); bob=custodian(c,iid,'bob'); charlie=custodian(c,iid,'charlie')
    assert c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/custody-events',json={'data':{'event_kind':'intake','to_custodian_id':alice}}).status_code==200
    # The API records asserted custody data, but continuity analysis detects that the asserted sender is not current custodian.
    assert c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/custody-events',json={'data':{'event_kind':'transfer','from_custodian_id':charlie,'to_custodian_id':bob}}).status_code==200
    chain=c.get(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/custody-chain').json(); assert chain['hash_chain_valid'] is True and chain['continuity_status']=='review-required' and chain['gap_count']==1
    assert chain['findings'][0]['kind']=='custodian-discontinuity'
    ready=c.get('/v1/open-forensics/readiness').json(); assert ready['legal_admissibility_determination_by_core'] is False and ready['physical_transfer_verification_by_core'] is False


def test_custody_validation_guards(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,eid=create_case(c); alice=custodian(c,iid,'alice')
    bad=c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/custody-events',json={'data':{'event_kind':'transfer','from_custodian_id':alice,'to_custodian_id':alice}}); assert bad.status_code==422
    bad_hash=c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/integrity-checks',json={'data':{'check_key':'bad-hash','observed_hash':'not-a-hash'}}); assert bad_hash.status_code==422
    unknown=c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/custody-events',json={'data':{'event_kind':'court-admissible','to_custodian_id':alice}}); assert unknown.status_code==422
