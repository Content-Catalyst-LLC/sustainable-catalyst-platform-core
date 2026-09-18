from fastapi.testclient import TestClient
from app.main import create_app


def test_readiness_and_boundaries(tmp_path, monkeypatch):
    monkeypatch.setenv("SC_CORE_DATABASE_URL", f"sqlite:///{tmp_path/'a.db'}")
    app=create_app(); c=TestClient(app)
    d=c.get('/v1/research/projects/readiness').json()
    assert d['release']=='2.72.0' and d['migration_0076_applied'] is True
    assert d['contract']=='sc.research.unified-project.v1'
    assert 'finding' in d['component_kinds'] and 'dataset' in d['component_kinds']
    assert d['research_project_registry_by_core'] is True
    assert d['execute_analysis_by_core'] is False
    assert d['generate_findings_by_core'] is False
    assert d['infer_originality_by_core'] is False
    assert d['promote_conclusion_by_core'] is False


def test_project_roundtrip_components_provenance_and_snapshot(tmp_path, monkeypatch):
    monkeypatch.setenv("SC_CORE_DATABASE_URL", f"sqlite:///{tmp_path/'b.db'}")
    app=create_app(); c=TestClient(app)
    r=c.post('/v1/research/projects',json={'data':{
        'title':'Carbon Systems Study','project_key':'carbon-study','visibility':'public',
        'research_type':'sustainable-development','research_question':'How do scenarios differ?',
        'objective':'Compare scenarios','methodology':'Reproducible mixed-method analysis',
        'scope':{'domain':'carbon'},'ethics':{'human_subjects':False}
    }})
    assert r.status_code==200, r.text
    pid=r.json()['project']['id']
    assert c.post(f'/v1/research/projects/{pid}/questions',json={'data':{'question_key':'q1','question_text':'How do scenarios differ?'}}).status_code==200
    assert c.post(f'/v1/research/projects/{pid}/objectives',json={'data':{'objective_key':'o1','objective_text':'Compare scenario outcomes','success_criteria':['reproducible']}}).status_code==200
    assert c.post(f'/v1/research/projects/{pid}/components',json={'data':{'component_key':'dataset-1','component_kind':'dataset','title':'Input dataset','product_key':'workspace','product_ref':'dataset:1','provenance':{'source':'official'}}}).status_code==200
    assert c.post(f'/v1/research/projects/{pid}/components',json={'data':{'component_key':'finding-1','component_kind':'finding','title':'Recorded finding','product_key':'lab','product_ref':'finding:1','content':{'finding_type':'statistical-result'}}}).status_code==200
    assert c.post(f'/v1/research/projects/{pid}/relationships',json={'data':{'subject_ref':'finding:1','predicate':'supported_by','object_ref':'dataset:1','evidence_refs':['evidence:1']}}).status_code==200
    assert c.post(f'/v1/research/projects/{pid}/provenance',json={'data':{'provenance_key':'run-1','activity_type':'analysis','source_refs':['source:1'],'input_refs':['dataset:1'],'output_refs':['finding:1'],'runtime':{'product':'lab','version':'test'}}}).status_code==200
    assert c.post(f'/v1/research/projects/{pid}/handoffs',json={'data':{'handoff_key':'lab-run','target_product':'lab','capability':'statistical-analysis','request_contract':{'external':True}}}).status_code==200
    s1=c.post(f'/v1/research/projects/{pid}/snapshots',json={'data':{}}).json()
    s2=c.post(f'/v1/research/projects/{pid}/snapshots',json={'data':{}}).json()
    assert s2['previous_snapshot_hash']==s1['content_hash']
    b=c.get(f'/v1/research/projects/{pid}/bundle').json()
    assert b['project']['unified_profile']['project_key']=='carbon-study'
    assert len(b['questions'])==1 and len(b['objectives'])==1 and len(b['components'])==2
    assert len(b['relationships'])==1 and len(b['provenance_records'])==1 and len(b['handoffs'])==1
    pub=c.get(f'/api/v1/research/projects/{pid}/bundle')
    assert pub.status_code==401  # public API contract remains key-scoped


def test_adopts_existing_v228_project_identity(tmp_path, monkeypatch):
    monkeypatch.setenv("SC_CORE_DATABASE_URL", f"sqlite:///{tmp_path/'c.db'}")
    app=create_app(); c=TestClient(app)
    old=c.post('/v1/research-objects',json={'object_type':'research-project','name':'Existing Project','visibility':'private','attributes':{'owner_product':'workspace'}})
    assert old.status_code==200, old.text
    pid=old.json()['id']
    r=c.post(f'/v1/research/projects/{pid}/profile',json={'data':{'project_key':'existing','title':'Existing Project','research_type':'general'}})
    assert r.status_code==200, r.text
    assert r.json()['project_entity_id']==pid


def test_rejects_core_execution_and_unknown_component(tmp_path, monkeypatch):
    monkeypatch.setenv("SC_CORE_DATABASE_URL", f"sqlite:///{tmp_path/'d.db'}")
    app=create_app(); c=TestClient(app)
    r=c.post('/v1/research/projects',json={'data':{'title':'Boundary Test','project_key':'boundary','execute_analysis_by_core':True}})
    assert r.status_code==422
    good=c.post('/v1/research/projects',json={'data':{'title':'Boundary Test','project_key':'boundary'}})
    assert good.status_code==200, good.text; pid=good.json()['project']['id']
    bad=c.post(f'/v1/research/projects/{pid}/components',json={'data':{'component_key':'x','component_kind':'unsupported','title':'x'}})
    assert bad.status_code==422
