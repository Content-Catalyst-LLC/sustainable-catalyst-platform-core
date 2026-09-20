from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
def client(tmp_path): return TestClient(create_app(Settings(database_url='sqlite:///'+str(tmp_path/'t.db'))))
def project(c):
 r=c.post('/v1/research/projects',json={'data':{'title':'Repro Study','project_key':'repro-study','visibility':'public'}});assert r.status_code==200,r.text;return r.json()['project']['id']
def test_readiness(tmp_path):
 c=client(tmp_path);d=c.get('/v1/research/reproducibility/readiness').json();assert d['release']=='2.75.0';assert d['migration_0079_applied'] is True;assert d['contract']=='sc.research.reproducible-package.v1';assert d['execute_replay_by_core'] is False
def test_package_roundtrip(tmp_path):
 c=client(tmp_path);pid=project(c);r=c.post(f'/v1/research/reproducibility/projects/{pid}/packages',json={'data':{'package_key':'p1','title':'Frozen thesis analysis'}});assert r.status_code==200,r.text;pk=r.json()['id']
 assert c.post(f'/v1/research/reproducibility/packages/{pk}/components',json={'data':{'component_key':'run','component_type':'analysis_run','component_ref':'run:1','content_hash':'abc'}}).status_code==200
 assert c.post(f'/v1/research/reproducibility/packages/{pk}/artifacts',json={'data':{'artifact_key':'notebook','artifact_type':'notebook','artifact_ref':'artifact:notebook','content_hash':'def'}}).status_code==200
 assert c.post(f'/v1/research/reproducibility/packages/{pk}/environments',json={'data':{'environment_key':'py','runtime_manifest':{'python':'3.12'},'dependency_manifest':{'pandas':'2.x'}}}).status_code==200
 assert c.post(f'/v1/research/reproducibility/packages/{pk}/replay-plans',json={'data':{'plan_key':'replay','target_product':'workbench','instructions':{'steps':['load','run']},'expected_outputs':['finding:1']}}).status_code==200
 assert c.post(f'/v1/research/reproducibility/packages/{pk}/verifications',json={'data':{'verification_type':'hash','status':'passed','observed_hash':'abc'}}).status_code==200
 assert c.post(f'/v1/research/reproducibility/packages/{pk}/reviews',json={'data':{'reviewer_ref':'reviewer:1','status':'recorded','findings':{'note':'replay described'}}}).status_code==200
 s1=c.post(f'/v1/research/reproducibility/packages/{pk}/snapshots',json={'data':{}}).json();s2=c.post(f'/v1/research/reproducibility/packages/{pk}/snapshots',json={'data':{}}).json();assert s2['previous_snapshot_hash']==s1['content_hash']
 b=c.get(f'/v1/research/reproducibility/packages/{pk}/bundle').json();assert len(b['components'])==1 and len(b['artifacts'])==1 and len(b['replay_plans'])==1 and len(b['verifications'])==1;assert c.get(f'/api/v1/research/reproducibility/packages/{pk}/bundle').status_code==401
def test_boundaries(tmp_path):
 c=client(tmp_path);pid=project(c);bad=c.post(f'/v1/research/reproducibility/projects/{pid}/packages',json={'data':{'package_key':'bad','title':'Bad','execute_replay_by_core':True}});assert bad.status_code==422
