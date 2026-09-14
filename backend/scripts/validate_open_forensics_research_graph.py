#!/usr/bin/env python3
import os,tempfile
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity
fd,path=tempfile.mkstemp(suffix='.db'); os.close(fd)
try:
 app=create_app(Settings(database_url='sqlite:///'+path,version='2.50.0')); c=TestClient(app)
 with app.state.database.session_factory() as db:
  db.add(Entity(id='project:v2500-smoke',entity_type='research-project',slug='v2500-smoke',name='v2500 smoke',visibility='public')); db.commit()
 inv=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:v2500-smoke','investigation_key':'smoke','name':'Smoke','visibility':'public'}}); assert inv.status_code==200,inv.text; iid=inv.json()['id']
 ev=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'e','evidence_kind':'record','label':'Evidence','content_hash':'a'*64}}); assert ev.status_code==200,ev.text; eid=ev.json()['id']
 claim=c.post(f'/v1/open-forensics/investigations/{iid}/claims',json={'data':{'claim_key':'c','claim_kind':'factual','statement':'Recorded claim'}}); assert claim.status_code==200,claim.text
 g=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs',json={'data':{'graph_key':'g','label':'Smoke graph','visibility':'public'}}); assert g.status_code==200,g.text; gid=g.json()['id']
 n1=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/nodes',json={'data':{'node_key':'evidence','node_kind':'evidence','label':'Evidence','record_id':eid}}); assert n1.status_code==200,n1.text
 n2=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/nodes',json={'data':{'node_key':'claim','node_kind':'claim','label':'Claim','record_id':claim.json()['id']}}); assert n2.status_code==200,n2.text
 edge=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/edges',json={'data':{'edge_key':'edge','source_node_id':n1.json()['id'],'target_node_id':n2.json()['id'],'relation_kind':'evidence-for','evidence_basis_ids':[eid]}}); assert edge.status_code==200,edge.text
 c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/views',json={'data':{'view_key':'overview','name':'Overview'}}).raise_for_status()
 c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/handoffs',json={'data':{'handoff_key':'lab','target_product':'lab'}}).raise_for_status()
 snap=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/snapshots',json={'data':{}}); assert snap.status_code==200 and len(snap.json()['content_hash'])==64
 pkg=c.post(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/packages',json={'data':{'package_key':'portable'}}); assert pkg.status_code==200 and len(pkg.json()['manifest_hash'])==64
 r=c.get('/v1/open-forensics/readiness').json(); spec=c.get(f'/v1/open-forensics/investigations/{iid}/research-graphs/{gid}/visual-spec').json(); m=migration_status(app.state.database)
 assert r['migration_0054_applied'] is True and r['automatic_graph_edge_inference_by_core'] is False and r['automatic_entity_resolution_by_core'] is False and r['automatic_truth_promotion'] is False
 assert spec['renderer_neutral'] is True and spec['execution']['graph_analytics_execution_by_core'] is False
 assert m['pending']==[] and m['applied'][-1]=='0054'
 print({'version':'2.50.0','migration_0054_applied':True,'research_graph_nodes':2,'research_graph_edges':1,'renderer_neutral':True,'automatic_graph_edge_inference_by_core':False,'automatic_truth_promotion':False})
 print('PASS - Platform Core v2.50.0 Forensic Research Graph runtime validation')
finally:
 try: os.unlink(path)
 except FileNotFoundError: pass
