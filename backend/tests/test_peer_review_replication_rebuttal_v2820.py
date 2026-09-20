from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

def client(tmp_path): return TestClient(create_app(Settings(database_url="sqlite:///"+str(tmp_path/"review.db"))))
def project(c, visibility="public"):
    r=c.post("/v1/research/projects",json={"data":{"title":"Review Study","project_key":"review-study-"+visibility,"visibility":visibility}}); assert r.status_code==200,r.text; return r.json()["project"]["id"]
def publication(c,pid):
    r=c.post(f"/v1/research/publications/projects/{pid}",json={"data":{"publication_key":"pub-1","title":"Reviewable paper","publication_type":"paper"}}); assert r.status_code==200,r.text; return r.json()["id"]

def test_readiness(tmp_path):
    c=client(tmp_path); d=c.get("/v1/research/peer-review/readiness").json(); assert d["release"]=="2.82.0"; assert d["migration_0086_applied"] is True; assert d["peer_review_registry_by_core"] is True; assert d["replication_study_registry_by_core"] is True; assert d["rebuttal_registry_by_core"] is True; assert d["generate_peer_review_by_core"] is False; assert d["score_manuscript_quality_by_core"] is False; assert d["infer_replication_success_by_core"] is False; assert d["decide_publication_by_core"] is False; c.close()

def test_peer_review_comment_response_revision(tmp_path):
    c=client(tmp_path); pid=project(c); pub=publication(c,pid)
    rv=c.post(f"/v1/research/peer-review/publications/{pub}/reviews",json={"data":{"review_key":"r1","review_type":"peer","reviewer_role":"reviewer_1","summary_text":"Reviewer-authored summary.","declared_recommendation":"major_revision"}}); assert rv.status_code==200,rv.text; rid=rv.json()["id"]
    cm=c.post(f"/v1/research/peer-review/reviews/{rid}/comments",json={"data":{"comment_key":"c1","comment_type":"methods","priority":"major","target_type":"section","target_ref":"methods","comment_text":"Clarify the sampling frame.","evidence_refs":["source:methods"]}}); assert cm.status_code==200,cm.text; cid=cm.json()["id"]
    rp=c.post(f"/v1/research/peer-review/comments/{cid}/responses",json={"data":{"response_key":"resp1","response_text":"Sampling frame clarified.","disposition":"addressed","change_refs":["section:methods:v2"]}}); assert rp.status_code==200,rp.text
    rev=c.post(f"/v1/research/peer-review/reviews/{rid}/revisions",json={"data":{"stage":"revision","status":"responded","declared_recommendation":"minor_revision","change_summary":"Reviewer updated declared recommendation."}}); assert rev.status_code==200,rev.text; assert rev.json()["revision"]==1
    b=c.get(f"/v1/research/peer-review/publications/{pub}/bundle").json(); assert len(b["reviews"])==1; assert len(b["review_comments"])==1; assert len(b["review_responses"])==1; assert len(b["review_revisions"])==1; assert b["generate_peer_review_by_core"] is False; c.close()

def test_replication_rebuttal_lineage_and_snapshot(tmp_path):
    c=client(tmp_path); pid=project(c); pub=publication(c,pid)
    st=c.post(f"/v1/research/peer-review/publications/{pub}/replications",json={"data":{"study_key":"rep1","title":"Independent direct replication","replication_type":"direct","status":"completed","protocol_ref":"protocol:1"}}); assert st.status_code==200,st.text; sid=st.json()["id"]
    at=c.post(f"/v1/research/peer-review/replications/{sid}/attempts",json={"data":{"attempt_key":"a1","method_ref":"method:1","dataset_refs":["dataset:rep1"],"execution_refs":["run:rep1"],"result_summary":"Independent team result.","declared_outcome":"partially_consistent"}}); assert at.status_code==200,at.text
    cp=c.post(f"/v1/research/peer-review/replications/{sid}/comparisons",json={"data":{"comparison_key":"cmp1","original_ref":"result:original","replication_ref":"result:rep1","metric_name":"effect_size","original_value":{"value":0.42},"replication_value":{"value":0.31},"declared_relation":"mixed","interpretation_text":"Researcher-declared comparison."}}); assert cp.status_code==200,cp.text
    rb=c.post(f"/v1/research/peer-review/publications/{pub}/rebuttals",json={"data":{"rebuttal_key":"rb1","title":"Methodological rebuttal","target_type":"review_comment","target_ref":"comment:external","rebuttal_text":"Author-authored rebuttal."}}); assert rb.status_code==200,rb.text; rbid=rb.json()["id"]
    pt=c.post(f"/v1/research/peer-review/rebuttals/{rbid}/points",json={"data":{"point_key":"p1","point_text":"The criticism does not account for the preregistered exclusion rule.","target_ref":"comment:external","evidence_refs":["protocol:1"]}}); assert pt.status_code==200,pt.text
    sm=c.get(f"/v1/research/peer-review/publications/{pub}/summary").json(); assert sm["declared_replication_outcomes"]["partially_consistent"]==1; assert sm["declared_comparison_relations"]["mixed"]==1; assert sm["replication_success_inferred"] is False; assert sm["publication_decision_made_by_core"] is False
    ln=c.get(f"/v1/research/peer-review/publications/{pub}/lineage").json(); assert ln["lineage_is_declared_not_inferred"] is True; assert len(ln["replication_edges"])==1; assert len(ln["rebuttal_edges"])==1
    s1=c.post(f"/v1/research/peer-review/publications/{pub}/snapshots",json={"data":{}}).json(); s2=c.post(f"/v1/research/peer-review/publications/{pub}/snapshots",json={"data":{}}).json(); assert s2["previous_snapshot_hash"]==s1["content_hash"]; c.close()

def test_boundary_rejection(tmp_path):
    c=client(tmp_path); pid=project(c); pub=publication(c,pid)
    bad=c.post(f"/v1/research/peer-review/publications/{pub}/reviews",json={"data":{"review_key":"bad","generate_peer_review_by_core":True}}); assert bad.status_code==422,bad.text
    bad2=c.post(f"/v1/research/peer-review/publications/{pub}/replications",json={"data":{"study_key":"bad","title":"Bad","infer_replication_success_by_core":True}}); assert bad2.status_code==422,bad2.text; c.close()

def test_private_public_boundary(tmp_path):
    c=client(tmp_path); pid=project(c,"private"); pub=publication(c,pid); from app.services import peer_review_intelligence as svc
    with c.app.state.database.session_factory() as db:
        try: svc.bundle(db,pub,True); assert False,"expected private-project rejection"
        except ValueError as e: assert "not public" in str(e)
    c.close()
