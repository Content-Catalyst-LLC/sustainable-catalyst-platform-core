from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

def client(tmp_path): return TestClient(create_app(Settings(database_url="sqlite:///"+str(tmp_path/"pub.db"))))
def project(c,visibility="public"):
    r=c.post("/v1/research/projects",json={"data":{"title":"Publication Study","project_key":"publication-study-"+visibility,"visibility":visibility}}); assert r.status_code==200,r.text; return r.json()["project"]["id"]
def publication(c,pid,**extra):
    data={"publication_key":"pub-1","title":"Reproducible paper","publication_type":"paper","required_sections":["methods","results","conclusion"]}; data.update(extra); r=c.post(f"/v1/research/publications/projects/{pid}",json={"data":data}); assert r.status_code==200,r.text; return r.json()["id"]
def test_readiness(tmp_path):
    c=client(tmp_path); d=c.get("/v1/research/publications/readiness").json(); assert d["release"]=="2.81.0"; assert d["migration_0085_applied"] is True; assert d["claim_citation_traceability_by_core"] is True; assert d["structural_readiness_diagnostics_by_core"] is True; assert d["generate_manuscript_by_core"] is False; assert d["fabricate_citation_by_core"] is False; assert d["judge_publication_quality_by_core"] is False; assert d["publish_external_by_core"] is False; c.close()
def test_publication_roundtrip(tmp_path):
    c=client(tmp_path); pid=project(c); pub=publication(c,pid,abstract_text="Declared abstract.")
    m=c.post(f"/v1/research/publications/{pub}/sections",json={"data":{"section_key":"methods","section_type":"methods","heading":"Methods","section_index":1,"body_text":"Registered methods narrative.","source_refs":["method:1"]}}).json()
    r=c.post(f"/v1/research/publications/{pub}/sections",json={"data":{"section_key":"results","section_type":"results","heading":"Results","section_index":2,"body_text":"Researcher-authored results.","claim_refs":["claim:1"]}}).json()
    c.post(f"/v1/research/publications/{pub}/sections",json={"data":{"section_key":"conclusion","section_type":"conclusion","heading":"Conclusion","section_index":3,"body_text":"Researcher-authored conclusion."}})
    ref=c.post(f"/v1/research/publications/{pub}/references",json={"data":{"reference_key":"ref-1","reference_type":"article","title":"Source article","doi":"10.1000/example","source_ref":"source:1"}}).json()
    q=c.post(f"/v1/research/publications/{pub}/citations",json={"data":{"citation_key":"cite-1","section_id":r["id"],"reference_id":ref["id"],"claim_ref":"claim:1","locator":"p. 4"}}); assert q.status_code==200,q.text
    assert c.post(f"/v1/research/publications/{pub}/figures",json={"data":{"figure_key":"fig-1","figure_type":"chart","title":"Observed values","source_ref":"visualization:1","version_ref":"v3"}}).status_code==200
    assert c.post(f"/v1/research/publications/{pub}/supplements",json={"data":{"supplement_key":"supp-1","supplement_type":"reproducibility_package","title":"Reproduction package","artifact_ref":"package:1","version_ref":"v1","integrity":{"sha256":"abc"}}}).status_code==200
    assert c.post(f"/v1/research/publications/{pub}/identifiers",json={"data":{"identifier_type":"doi","identifier_value":"10.1000/example-publication","authority":"external"}}).status_code==200
    d=c.get(f"/v1/research/publications/{pub}/readiness").json(); assert d["structural_readiness"]["missing_required_sections"]==[]; assert d["structural_readiness"]["uncited_claim_refs"]==[]; assert d["diagnostic_is_structural_only"] is True; assert d["quality_score_computed"] is False
    l=c.get(f"/v1/research/publications/{pub}/lineage").json(); assert l["lineage_is_declared_not_inferred"] is True; assert l["missing_links_inferred_by_core"] is False
    e=c.post(f"/v1/research/publications/{pub}/exports",json={"data":{"export_key":"export-1","formats":["markdown","json","pdf"]}}); assert e.status_code==200,e.text; assert e.json()["manifest"]["generated_content"] is False; assert e.json()["manifest"]["external_renderer_required_for_pdf_docx"] is True
    v=c.post(f"/v1/research/publications/{pub}/revisions",json={"data":{"status":"in_review","change_summary":"Submitted for review."}}); assert v.status_code==200; assert v.json()["revision"]==1
    s1=c.post(f"/v1/research/publications/{pub}/snapshots",json={"data":{}}).json(); s2=c.post(f"/v1/research/publications/{pub}/snapshots",json={"data":{}}).json(); assert s2["previous_snapshot_hash"]==s1["content_hash"]
    b=c.get(f"/v1/research/publications/{pub}/bundle").json(); assert len(b["sections"])==3; assert len(b["references"])==1; assert len(b["citations"])==1; assert len(b["figures"])==1; assert len(b["supplements"])==1; assert len(b["identifiers"])==1; assert b["generate_manuscript_by_core"] is False; c.close()
def test_structural_gap_and_boundary(tmp_path):
    c=client(tmp_path); pid=project(c); pub=publication(c,pid); s=c.post(f"/v1/research/publications/{pub}/sections",json={"data":{"section_key":"results","section_type":"results","heading":"Results","claim_refs":["claim:uncited"]}}); assert s.status_code==200
    d=c.get(f"/v1/research/publications/{pub}/readiness").json()["structural_readiness"]; assert set(d["missing_required_sections"])=={"methods","conclusion"}; assert d["uncited_claim_refs"]==["claim:uncited"]
    bad=c.post(f"/v1/research/publications/projects/{pid}",json={"data":{"publication_key":"bad","title":"Bad","publication_type":"paper","generate_manuscript_by_core":True}}); assert bad.status_code==422; c.close()
def test_private_public_boundary(tmp_path):
    c=client(tmp_path); pid=project(c,"private"); pub=publication(c,pid); from app.services import research_publications as svc
    with c.app.state.database.session_factory() as db:
        try: svc.bundle(db,pub,True); assert False,"expected private-project rejection"
        except ValueError as e: assert "not public" in str(e)
    c.close()
def test_conclusion_binding(tmp_path):
    c=client(tmp_path); pid=project(c); ar=c.post(f"/v1/research/arguments/projects/{pid}",json={"data":{"argument_key":"a1","title":"Argument","thesis_text":"Thesis"}}).json(); con=c.post(f"/v1/research/conclusions/arguments/{ar['id']}",json={"data":{"conclusion_key":"c1","title":"Conclusion","conclusion_text":"Text"}}).json(); pub=publication(c,pid,conclusion_id=con["id"]); l=c.get(f"/v1/research/publications/{pub}/lineage").json(); assert l["conclusion"]["id"]==con["id"]; c.close()
