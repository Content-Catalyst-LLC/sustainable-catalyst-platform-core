from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings

def client(tmp_path):return TestClient(create_app(Settings(database_url='sqlite:///'+str(tmp_path/'i.db'))))
def project(c,visibility='public'):
 r=c.post('/v1/research/projects',json={'data':{'title':'Evidence Intelligence Study','project_key':'evidence-intelligence-study','visibility':visibility}});assert r.status_code==200,r.text;return r.json()['project']['id']

def test_readiness(tmp_path):
 c=client(tmp_path);d=c.get('/v1/research/intelligence/readiness').json();assert d['release']=='2.77.0';assert d['contract']=='sc.research.finding-claim-evidence.v1';assert d['migration_0081_applied'] is True;assert d['infer_truth_by_core'] is False and d['deterministic_structured_contradiction_candidates_by_core'] is True

def test_finding_interpretation_claim_evidence_roundtrip(tmp_path):
 c=client(tmp_path);pid=project(c)
 f=c.post(f'/v1/research/intelligence/projects/{pid}/findings',json={'data':{'finding_key':'f1','title':'Observed result','statement':'Recorded externally computed result.','finding_type':'result','analysis_run_ref':'run:1','notebook_ref':'notebook:1','source_refs':['dataset:1'],'uncertainty':{'interval':[1.1,1.5]}}});assert f.status_code==200,f.text;fid=f.json()['id']
 i=c.post(f'/v1/research/intelligence/projects/{pid}/interpretations',json={'data':{'interpretation_key':'i1','title':'Interpretation','interpretation_text':'The recorded result is consistent with the stated interpretation.','assumptions':['assumption:a']}});assert i.status_code==200,i.text;iid=i.json()['id']
 ca=c.post(f'/v1/research/intelligence/projects/{pid}/claims',json={'data':{'claim_key':'c-a','claim_text':'Entity X has property Y.','claim_type':'descriptive','subject_ref':'entity:x','predicate':'has_property','object_ref':'property:y','polarity':'affirmed'}});assert ca.status_code==200,ca.text;aid=ca.json()['id']
 cb=c.post(f'/v1/research/intelligence/projects/{pid}/claims',json={'data':{'claim_key':'c-b','claim_text':'Entity X does not have property Y.','claim_type':'descriptive','subject_ref':'entity:x','predicate':'has_property','object_ref':'property:y','polarity':'denied','status':'contested'}});assert cb.status_code==200,cb.text;bid=cb.json()['id']
 ev=c.post(f'/v1/research/intelligence/projects/{pid}/evidence-links',json={'data':{'evidence_link_key':'ev-f1','evidence_ref':'library:source:1','target_type':'finding','target_id':fid,'relation':'supports','declared_strength':'source-specific','assessment_basis':'Declared by researcher; Core does not calculate strength.'}});assert ev.status_code==200,ev.text
 d1=c.post(f'/v1/research/intelligence/projects/{pid}/derivations',json={'data':{'derivation_key':'f-i','source_type':'finding','source_id':fid,'target_type':'interpretation','target_id':iid,'relationship':'interpreted_as'}});assert d1.status_code==200,d1.text
 d2=c.post(f'/v1/research/intelligence/projects/{pid}/derivations',json={'data':{'derivation_key':'i-c','source_type':'interpretation','source_id':iid,'target_type':'claim','target_id':aid,'relationship':'supports_claim'}});assert d2.status_code==200,d2.text
 cand=c.get(f'/v1/research/intelligence/projects/{pid}/contradiction-candidates');assert cand.status_code==200,cand.text;cc=cand.json();assert len(cc['candidates'])==1 and cc['semantic_inference_performed'] is False
 cr=c.post(f'/v1/research/intelligence/projects/{pid}/contradictions',json={'data':{'contradiction_key':'cx1','claim_a_id':aid,'claim_b_id':bid,'status':'unresolved','basis_refs':['evidence:1']}});assert cr.status_code==200,cr.text;assert cr.json()['deterministic_match']['candidate'] is True
 fr=c.post(f'/v1/research/intelligence/findings/{fid}/revisions',json={'data':{'statement':'Recorded externally computed result, revised for precision.','status':'revised','change_summary':'Clarified wording'}});assert fr.status_code==200,fr.text;assert fr.json()['revision']==1 and len(fr.json()['state_hash'])==64
 rr=c.post(f'/v1/research/intelligence/claims/{aid}/revisions',json={'data':{'status':'qualified','qualifications':['Scope is limited to the registered evidence.'],'change_summary':'Added qualification'}});assert rr.status_code==200,rr.text;assert rr.json()['revision']==1
 s1=c.post(f'/v1/research/intelligence/projects/{pid}/snapshots',json={'data':{}}).json();s2=c.post(f'/v1/research/intelligence/projects/{pid}/snapshots',json={'data':{}}).json();assert s2['previous_snapshot_hash']==s1['content_hash']
 b=c.get(f'/v1/research/intelligence/projects/{pid}/bundle');assert b.status_code==200,b.text;j=b.json();assert len(j['findings'])==1 and len(j['interpretations'])==1 and len(j['claims'])==2 and len(j['evidence_links'])==1 and len(j['derivation_links'])==2 and len(j['contradictions'])==1 and len(j['finding_revisions'])==1 and len(j['claim_revisions'])==1
 assert c.get(f'/api/v1/research/intelligence/projects/{pid}/bundle').status_code==401

def test_boundaries_and_structured_claim_guard(tmp_path):
 c=client(tmp_path);pid=project(c)
 bad=c.post(f'/v1/research/intelligence/projects/{pid}/claims',json={'data':{'claim_key':'bad','claim_text':'Incomplete structured claim','subject_ref':'entity:x','polarity':'affirmed'}});assert bad.status_code==422
 bad2=c.post(f'/v1/research/intelligence/projects/{pid}/findings',json={'data':{'finding_key':'bad-f','title':'Bad','statement':'Bad','infer_truth_by_core':True}});assert bad2.status_code==422
