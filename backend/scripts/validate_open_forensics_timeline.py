#!/usr/bin/env python3
import json,tempfile
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.models import Entity
p=tempfile.mktemp(prefix='sc-core-v2450-',suffix='.db'); app=create_app(Settings(database_url='sqlite:///'+p,version='2.45.0')); c=TestClient(app)
with app.state.database.session_factory() as db:
    db.add(Entity(id='project:validate-v2450',entity_type='research-project',slug='validate-v2450',name='Timeline validation',visibility='public')); db.commit()
inv=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:validate-v2450','investigation_key':'validation','name':'Validation','visibility':'public'}}).json(); iid=inv['id']
ev=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'clock','evidence_kind':'record','label':'Clock record','content_hash':'c'*64}}).json()
e1=c.post(f'/v1/open-forensics/investigations/{iid}/events',json={'data':{'event_key':'first','label':'First event','event_kind':'observation','temporal_basis':'observed','time_precision':'minute','start_time':'2026-09-13T10:00:00Z'}}).json()
e2=c.post(f'/v1/open-forensics/investigations/{iid}/events',json={'data':{'event_key':'second','label':'Second event','event_kind':'communication','temporal_basis':'reconstructed','time_precision':'bounded','earliest_time':'2026-09-13T10:10:00Z','latest_time':'2026-09-13T10:30:00Z'}}).json()
c.post(f"/v1/open-forensics/investigations/{iid}/events/{e1['id']}/evidence-bindings",json={'data':{'binding_key':'clock','evidence_item_id':ev['id'],'role':'supports-time'}})
rel=c.post(f'/v1/open-forensics/investigations/{iid}/event-relations',json={'data':{'relation_key':'first-before-second','source_event_id':e1['id'],'target_event_id':e2['id'],'relation_kind':'before','basis_evidence_ids':[ev['id']]}}).json()
rec=c.post(f'/v1/open-forensics/investigations/{iid}/event-reconstructions',json={'data':{'reconstruction_key':'working','label':'Working sequence','ordered_event_ids':[e1['id'],e2['id']],'event_relation_ids':[rel['id']],'assumptions':['timestamps use a common clock']}}).json()
ready=c.get('/v1/open-forensics/readiness').json(); timeline=c.get(f'/v1/open-forensics/investigations/{iid}/timeline').json(); spec=c.get(f'/v1/open-forensics/investigations/{iid}/timeline-specification').json(); snap=c.post(f'/v1/open-forensics/investigations/{iid}/timeline-snapshots',json={'data':{}}).json()
assert ready['migration_0049_applied'] and ready['release']=='2.45.0'; assert ready['automatic_event_inference_by_core'] is False and ready['automatic_sequence_truth_determination_by_core'] is False; assert len(timeline['events'])==2 and len(timeline['reconstructions'])==1; assert spec['renderer_neutral'] is True and spec['execution']['automatic_sequence_truth_determination'] is False; assert len(snap['content_hash'])==64
print(json.dumps({'version':'2.45.0','migration_0049_applied':True,'events':len(timeline['events']),'reconstructions':len(timeline['reconstructions']),'snapshot_hash':snap['content_hash'],'automatic_sequence_truth_determination_by_core':ready['automatic_sequence_truth_determination_by_core']},sort_keys=True)); print('PASS - Platform Core v2.45.0 Forensic Timeline & Event Reconstruction runtime validation')
