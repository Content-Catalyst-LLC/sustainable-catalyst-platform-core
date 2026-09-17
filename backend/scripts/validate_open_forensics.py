#!/usr/bin/env python3
import json,tempfile
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.models import Entity

p=tempfile.mktemp(prefix='sc-core-v2420-',suffix='.db'); app=create_app(Settings(database_url='sqlite:///'+p,version='2.42.0')); c=TestClient(app)
with app.state.database.session_factory() as db:
    db.add(Entity(id='project:validate-v2420',entity_type='research-project',slug='validate-v2420',name='Forensics validation',visibility='public')); db.commit()
i=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:validate-v2420','investigation_key':'validation','name':'Validation','visibility':'public'}}).json()
o=c.post(f"/v1/open-forensics/investigations/{i['id']}/objects",json={'data':{'object_key':'artifact','object_kind':'artifact','label':'Artifact','source_product':'external','source_ref':'https://example.org/artifact'}}).json()
e=c.post(f"/v1/open-forensics/investigations/{i['id']}/evidence",json={'data':{'evidence_key':'evidence','evidence_kind':'digital','label':'Evidence','forensic_object_id':o['id'],'content_hash':'a'*64}}).json()
c.post(f"/v1/open-forensics/investigations/{i['id']}/evidence/{e['id']}/source-bindings",json={'data':{'binding_key':'source','source_kind':'external','source_ref':'https://example.org/artifact','content_hash':'a'*64}})
ready=c.get('/v1/open-forensics/readiness').json(); graph=c.get(f"/v1/open-forensics/investigations/{i['id']}/provenance-graph").json(); snap=c.post(f"/v1/open-forensics/investigations/{i['id']}/snapshots",json={'data':{}}).json()
assert ready['migration_0046_applied'] and ready['release']=='2.42.0'; assert ready['chain_of_custody_by_core'] is False and ready['authenticity_determination_by_core'] is False and ready['automatic_truth_promotion'] is False; assert graph['nodes'] and len(snap['content_hash'])==64
print(json.dumps({'version':'2.42.0','migration_0046_applied':True,'forensic_object_count':ready['counts']['objects'],'snapshot_hash':snap['content_hash'],'chain_of_custody_by_core':ready['chain_of_custody_by_core'],'automatic_truth_promotion':ready['automatic_truth_promotion']},sort_keys=True)); print('PASS - Platform Core v2.42.0 Forensic Object Model & Evidence Provenance runtime validation')
