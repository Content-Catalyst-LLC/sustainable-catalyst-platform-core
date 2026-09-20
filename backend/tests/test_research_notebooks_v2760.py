from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
def client(tmp_path):return TestClient(create_app(Settings(database_url='sqlite:///'+str(tmp_path/'n.db'))))
def project(c):
 r=c.post('/v1/research/projects',json={'data':{'title':'Notebook Study','project_key':'notebook-study','visibility':'public'}});assert r.status_code==200,r.text;return r.json()['project']['id']
def test_readiness(tmp_path):
 c=client(tmp_path);d=c.get('/v1/research/notebooks/readiness').json();assert d['release']=='2.76.0';assert d['contract']=='sc.research.notebook-narrative.v1';assert d['migration_0080_applied'] is True;assert d['execute_code_by_core'] is False and d['generate_narrative_by_core'] is False
def test_notebook_narrative_roundtrip(tmp_path):
 c=client(tmp_path);pid=project(c);r=c.post(f'/v1/research/notebooks/projects/{pid}/notebooks',json={'data':{'notebook_key':'thesis-analysis','title':'Thesis Analysis Notebook','visibility':'public'}});assert r.status_code==200,r.text;nid=r.json()['id']
 sec=c.post(f'/v1/research/notebooks/notebooks/{nid}/sections',json={'data':{'section_key':'methods','heading':'Methods','sequence':10}});assert sec.status_code==200,sec.text;sid=sec.json()['id']
 ent=c.post(f'/v1/research/notebooks/notebooks/{nid}/entries',json={'data':{'entry_key':'run-note','entry_type':'analysis_run','section_id':sid,'sequence':20,'body_text':'Recorded external analysis run.'}});assert ent.status_code==200,ent.text;eid=ent.json()['id']
 assert c.post(f'/v1/research/notebooks/entries/{eid}/bindings',json={'data':{'binding_key':'run','binding_type':'analysis_run','target_ref':'run:example','content_hash':'abc'}}).status_code==200
 assert c.post(f'/v1/research/notebooks/entries/{eid}/citations',json={'data':{'citation_key':'source-1','source_ref':'library:source-1','locator':'p. 12'}}).status_code==200
 nar=c.post(f'/v1/research/notebooks/notebooks/{nid}/narratives',json={'data':{'narrative_key':'main','title':'Analytical Narrative'}});assert nar.status_code==200,nar.text;aid=nar.json()['id']
 assert c.post(f'/v1/research/notebooks/narratives/{aid}/blocks',json={'data':{'block_key':'result','block_type':'result','sequence':1,'text':'External result recorded.','support_refs':['run:example']}}).status_code==200
 rev=c.post(f'/v1/research/notebooks/notebooks/{nid}/revisions',json={'data':{'change_summary':'Initial analytical record'}});assert rev.status_code==200 and len(rev.json()['state_hash'])==64
 s1=c.post(f'/v1/research/notebooks/notebooks/{nid}/snapshots',json={'data':{}}).json();s2=c.post(f'/v1/research/notebooks/notebooks/{nid}/snapshots',json={'data':{}}).json();assert s2['previous_snapshot_hash']==s1['content_hash']
 b=c.get(f'/v1/research/notebooks/notebooks/{nid}/bundle').json();assert len(b['sections'])==1 and len(b['entries'])==1 and len(b['bindings'])==1 and len(b['citations'])==1 and len(b['narratives'])==1 and len(b['narrative_blocks'])==1 and len(b['revisions'])==1
 assert c.get(f'/api/v1/research/notebooks/notebooks/{nid}/bundle').status_code==401
def test_boundaries_and_cross_notebook_section_guard(tmp_path):
 c=client(tmp_path);pid=project(c);n1=c.post(f'/v1/research/notebooks/projects/{pid}/notebooks',json={'data':{'notebook_key':'n1','title':'N1'}}).json()['id'];n2=c.post(f'/v1/research/notebooks/projects/{pid}/notebooks',json={'data':{'notebook_key':'n2','title':'N2'}}).json()['id'];sid=c.post(f'/v1/research/notebooks/notebooks/{n1}/sections',json={'data':{'section_key':'s','heading':'S'}}).json()['id']
 bad=c.post(f'/v1/research/notebooks/notebooks/{n2}/entries',json={'data':{'entry_key':'bad','entry_type':'note','section_id':sid}});assert bad.status_code==422
 bad2=c.post(f'/v1/research/notebooks/projects/{pid}/notebooks',json={'data':{'notebook_key':'bad','title':'Bad','generate_narrative_by_core':True}});assert bad2.status_code==422
