#!/usr/bin/env python3
import json,tempfile
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.models import Entity
p=tempfile.mktemp(prefix='sc-core-v2430-',suffix='.db'); app=create_app(Settings(database_url='sqlite:///'+p,version='2.43.0')); c=TestClient(app)
with app.state.database.session_factory() as db: db.add(Entity(id='project:validate-v2430',entity_type='research-project',slug='validate-v2430',name='Custody validation',visibility='public')); db.commit()
i=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:validate-v2430','investigation_key':'validation','name':'Validation','visibility':'public'}}).json(); iid=i['id']
e=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'evidence','evidence_kind':'digital','label':'Evidence','content_hash':'a'*64}}).json(); eid=e['id']
a=c.post(f'/v1/open-forensics/investigations/{iid}/custodians',json={'data':{'custodian_key':'a','display_name':'A'}}).json(); b=c.post(f'/v1/open-forensics/investigations/{iid}/custodians',json={'data':{'custodian_key':'b','display_name':'B'}}).json()
c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/custody-events',json={'data':{'event_kind':'intake','to_custodian_id':a['id'],'external_attestation_ref':'external:intake'}})
c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/custody-events',json={'data':{'event_kind':'transfer','from_custodian_id':a['id'],'to_custodian_id':b['id'],'external_attestation_ref':'external:transfer'}})
check=c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/integrity-checks',json={'data':{'check_key':'hash','observed_hash':'a'*64}}).json(); chain=c.get(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/custody-chain').json(); ready=c.get('/v1/open-forensics/readiness').json(); snap=c.post(f'/v1/open-forensics/investigations/{iid}/custody-snapshots',json={'data':{}}).json()
assert ready['migration_0047_applied'] and ready['release']=='2.43.0'; assert chain['hash_chain_valid'] and chain['continuity_status']=='continuous'; assert check['status']=='match'; assert len(snap['content_hash'])==64; assert ready['legal_admissibility_determination_by_core'] is False and ready['automatic_truth_promotion'] is False
print(json.dumps({'version':'2.43.0','migration_0047_applied':True,'custody_events':len(chain['events']),'hash_chain_valid':chain['hash_chain_valid'],'integrity_status':check['status'],'legal_admissibility_determination_by_core':ready['legal_admissibility_determination_by_core']},sort_keys=True)); print('PASS - Platform Core v2.43.0 Evidence Integrity & Chain of Custody runtime validation')
