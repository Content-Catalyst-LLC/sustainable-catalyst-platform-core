#!/usr/bin/env python3
import json,tempfile
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.models import Entity
p=tempfile.mktemp(prefix='sc-core-v2440-',suffix='.db'); app=create_app(Settings(database_url='sqlite:///'+p,version='2.44.0')); c=TestClient(app)
with app.state.database.session_factory() as db: db.add(Entity(id='project:validate-v2440',entity_type='research-project',slug='validate-v2440',name='Forensic reasoning validation',visibility='public')); db.commit()
i=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:validate-v2440','investigation_key':'validation','name':'Validation','visibility':'public'}}).json(); iid=i['id']
e=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'e','evidence_kind':'digital','label':'Evidence','content_hash':'a'*64}}).json(); eid=e['id']
c1=c.post(f'/v1/open-forensics/investigations/{iid}/claims',json={'data':{'claim_key':'c1','statement':'Claim one'}}).json(); c2=c.post(f'/v1/open-forensics/investigations/{iid}/claims',json={'data':{'claim_key':'c2','statement':'Claim two'}}).json()
c.post(f"/v1/open-forensics/investigations/{iid}/claims/{c1['id']}/evidence-assessments",json={'data':{'assessment_key':'c1-e','evidence_item_id':eid,'stance':'supports','diagnosticity':0.8}})
c.post(f'/v1/open-forensics/investigations/{iid}/contradictions',json={'data':{'contradiction_key':'c1-c2','left_claim_id':c1['id'],'right_claim_id':c2['id'],'contradiction_kind':'direct','basis_evidence_ids':[eid]}})
h1=c.post(f'/v1/open-forensics/investigations/{iid}/hypotheses',json={'data':{'hypothesis_key':'h1','label':'H1','statement':'Hypothesis one','focal_claim_id':c1['id']}}).json(); h2=c.post(f'/v1/open-forensics/investigations/{iid}/hypotheses',json={'data':{'hypothesis_key':'h2','label':'H2','statement':'Hypothesis two','focal_claim_id':c1['id']}}).json()
c.post(f'/v1/open-forensics/investigations/{iid}/hypothesis-relations',json={'data':{'relation_key':'h1-h2','source_hypothesis_id':h1['id'],'target_hypothesis_id':h2['id'],'relation_kind':'competes-with'}})
c.post(f"/v1/open-forensics/investigations/{iid}/hypotheses/{h1['id']}/evidence-assessments",json={'data':{'assessment_key':'h1-e','evidence_item_id':eid,'consistency':'supports','diagnosticity':0.8}})
c.post(f"/v1/open-forensics/investigations/{iid}/hypotheses/{h2['id']}/evidence-assessments",json={'data':{'assessment_key':'h2-e','evidence_item_id':eid,'consistency':'inconsistent','diagnosticity':0.8}})
ready=c.get('/v1/open-forensics/readiness').json(); matrix=c.get(f'/v1/open-forensics/investigations/{iid}/hypothesis-matrix').json(); snap=c.post(f'/v1/open-forensics/investigations/{iid}/reasoning-snapshots',json={'data':{}}).json()
assert ready['release']=='2.44.0' and ready['migration_0048_applied']; assert matrix['ranked'] is False and matrix['probabilities_assigned'] is False and matrix['verdict'] is None; assert len(snap['content_hash'])==64; assert ready['claim_truth_determination_by_core'] is False and ready['verdict_generation_by_core'] is False
print(json.dumps({'version':'2.44.0','migration_0048_applied':True,'claims':ready['counts']['claims'],'contradictions':ready['counts']['contradictions'],'hypotheses':ready['counts']['hypotheses'],'matrix_ranked':matrix['ranked'],'probabilities_assigned':matrix['probabilities_assigned']},sort_keys=True)); print('PASS - Platform Core v2.44.0 Claims, Contradictions & Competing Hypotheses runtime validation')
