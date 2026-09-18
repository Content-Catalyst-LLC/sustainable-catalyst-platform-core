import os
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings

def client(tmp_path):
 return TestClient(create_app(Settings(database_url='sqlite:///'+str(tmp_path/'t.db'))))

def project(c):
 r=c.post('/v1/research/projects',json={'data':{'title':'Methods Study','project_key':'methods-study','visibility':'public'}}); assert r.status_code==200,r.text; return r.json()['project']['id']

def test_readiness(tmp_path):
 c=client(tmp_path); d=c.get('/v1/research/methodology/readiness').json(); assert d['release']=='2.74.0'; assert d['migration_0078_applied'] is True; assert d['contract']=='sc.research.methodology-analysis.v1'; assert d['execute_analysis_by_core'] is False

def test_methodology_run_roundtrip(tmp_path):
 c=client(tmp_path); pid=project(c)
 m=c.post(f'/v1/research/methodology/projects/{pid}/methodologies',json={'data':{'method_key':'m1','title':'Regression protocol','method_type':'statistical','purpose':'Estimate association'}}); assert m.status_code==200,m.text; mid=m.json()['id']
 v=c.post(f'/v1/research/methodology/methodologies/{mid}/versions',json={'data':{'version_key':'1.0','protocol':{'estimator':'OLS'},'software_refs':['python:3.12']}}); assert v.status_code==200,v.text; vid=v.json()['id']
 assert c.post(f'/v1/research/methodology/methodologies/{mid}/variables',json={'data':{'variable_key':'x','role':'independent','label':'X','unit':'kg'}}).status_code==200
 assert c.post(f'/v1/research/methodology/methodologies/{mid}/assumptions',json={'data':{'assumption_key':'a1','kind':'assumption','statement':'Linearity is an explicit modeling assumption.'}}).status_code==200
 assert c.post(f'/v1/research/methodology/methodologies/{mid}/parameters',json={'data':{'parameter_key':'alpha','value':{'value':0.05}}}).status_code==200
 e=c.post(f'/v1/research/methodology/projects/{pid}/environments',json={'data':{'environment_key':'py','product_key':'lab','runtime':'python','runtime_version':'3.12','package_manifest':{'statsmodels':'x'}}}); assert e.status_code==200,e.text; eid=e.json()['id']
 r=c.post(f'/v1/research/methodology/projects/{pid}/runs',json={'data':{'run_key':'run1','methodology_id':mid,'methodology_version_id':vid,'environment_id':eid,'product_key':'lab','external_run_ref':'lab:run-1','status':'completed','parameters':{'alpha':0.05}}}); assert r.status_code==200,r.text; rid=r.json()['id']
 assert c.post(f'/v1/research/methodology/runs/{rid}/inputs',json={'data':{'input_key':'data','input_type':'dataset','input_ref':'dataset:1','content_hash':'abc'}}).status_code==200
 assert c.post(f'/v1/research/methodology/runs/{rid}/outputs',json={'data':{'output_key':'result','output_type':'finding','output_ref':'finding:1','content_hash':'def'}}).status_code==200
 s1=c.post(f'/v1/research/methodology/projects/{pid}/snapshots',json={'data':{}}).json(); s2=c.post(f'/v1/research/methodology/projects/{pid}/snapshots',json={'data':{}}).json(); assert s2['previous_snapshot_hash']==s1['content_hash']
 b=c.get(f'/v1/research/methodology/projects/{pid}/bundle').json(); assert len(b['methodologies'])==1 and len(b['runs'])==1 and len(b['inputs'])==1 and len(b['outputs'])==1
 assert c.get(f'/api/v1/research/methodology/projects/{pid}/bundle').status_code==401

def test_boundaries(tmp_path):
 c=client(tmp_path); pid=project(c)
 bad=c.post(f'/v1/research/methodology/projects/{pid}/methodologies',json={'data':{'method_key':'bad','title':'Bad','execute_analysis_by_core':True}}); assert bad.status_code==422
