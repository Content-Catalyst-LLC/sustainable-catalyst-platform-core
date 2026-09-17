#!/usr/bin/env python3
import os,tempfile
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity
fd,path=tempfile.mkstemp(suffix='.db'); os.close(fd)
try:
 app=create_app(Settings(database_url='sqlite:///'+path,version='2.51.0')); c=TestClient(app)
 with app.state.database.session_factory() as db:
  db.add(Entity(id='project:v2510-smoke',entity_type='research-project',slug='v2510-smoke',name='v2510 smoke',visibility='public')); db.commit()
 inv=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:v2510-smoke','investigation_key':'smoke','name':'Smoke','visibility':'public'}}); assert inv.status_code==200,inv.text; iid=inv.json()['id']
 ev=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'e','evidence_kind':'record','label':'Evidence','content_hash':'a'*64}}); assert ev.status_code==200,ev.text
 pkg=c.post(f'/v1/open-forensics/investigations/{iid}/reproducible-packages',json={'data':{'package_key':'review','label':'Review Package','visibility':'public'}}); assert pkg.status_code==200,pkg.text; body=pkg.json(); pid=body['package']['id']; assert len(body['components'])==9
 verify=c.post(f'/v1/open-forensics/investigations/{iid}/reproducible-packages/{pid}/verify',json={'data':{'compare_current_state':True}}); assert verify.status_code==200,verify.text; assert verify.json()['result']=='verified'
 review=c.post(f'/v1/open-forensics/investigations/{iid}/reproducible-packages/{pid}/reviews',json={'data':{'reviewer_ref':'smoke-reviewer','limitations':['Integrity verification is not truth determination.']}}); assert review.status_code==200,review.text
 snap=c.post(f'/v1/open-forensics/investigations/{iid}/reproducible-packages/{pid}/snapshots',json={'data':{}}); assert snap.status_code==200 and len(snap.json()['content_hash'])==64
 portable=c.get(f'/v1/open-forensics/investigations/{iid}/reproducible-packages/{pid}/portable'); assert portable.status_code==200,portable.text; p=portable.json(); assert p['reproducibility_equals_truth'] is False and p['authenticity_determined'] is False and p['admissibility_determined'] is False
 r=c.get('/v1/open-forensics/readiness').json(); m=migration_status(app.state.database)
 assert r['migration_0055_applied'] is True and r['reproducible_investigation_packages_by_core'] is True and r['investigation_package_integrity_verification_by_core'] is True and r['reproducibility_equals_truth_by_core'] is False and r['automatic_truth_promotion'] is False
 assert m['pending']==[] and m['applied'][-1]=='0055'
 print({'version':'2.51.0','migration_0055_applied':True,'component_count':9,'verification':'verified','reproducibility_equals_truth':False,'automatic_truth_promotion':False})
 print('PASS - Platform Core v2.51.0 Reproducible Investigation Packages runtime validation')
finally:
 try: os.unlink(path)
 except FileNotFoundError: pass
