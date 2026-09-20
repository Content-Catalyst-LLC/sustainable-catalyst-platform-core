from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

def client(tmp_path): return TestClient(create_app(Settings(database_url="sqlite:///" + str(tmp_path / "conclusion.db"))))

def project(c):
    r=c.post("/v1/research/projects",json={"data":{"title":"Conclusion Governance Study","project_key":"conclusion-governance-study","visibility":"public"}}); assert r.status_code==200,r.text; return r.json()["project"]["id"]

def argument(c,pid):
    r=c.post(f"/v1/research/arguments/projects/{pid}",json={"data":{"argument_key":"arg-1","title":"Governed argument","thesis_text":"Researcher-authored thesis."}}); assert r.status_code==200,r.text; return r.json()["id"]

def conclusion(c,aid):
    r=c.post(f"/v1/research/conclusions/arguments/{aid}",json={"data":{"conclusion_key":"conclusion-1","title":"Bounded conclusion","conclusion_text":"The researcher records a bounded conclusion.","conclusion_type":"interpretive","uncertainty":{"note":"material uncertainty remains"}}}); assert r.status_code==200,r.text; return r.json()["id"]

def test_readiness(tmp_path):
    c=client(tmp_path); d=c.get("/v1/research/conclusions/readiness").json(); assert d["release"]=="2.80.0"; assert d["migration_0084_applied"] is True; assert d["researcher_authored_conclusion_registry_by_core"] is True; assert d["descriptive_governance_summary_by_core"] is True; assert d["choose_conclusion_by_core"] is False; assert d["certify_conclusion_by_core"] is False; assert d["infer_truth_by_core"] is False; c.close()

def test_conclusion_governance_roundtrip(tmp_path):
    c=client(tmp_path); pid=project(c); aid=argument(c,pid); cid=conclusion(c,aid)
    r=c.post(f"/v1/research/conclusions/{cid}/evidence-bindings",json={"data":{"binding_key":"ev-1","source_type":"evidence","source_ref":"evidence:1","role":"supports","researcher_assessment":"directly relevant","rationale":"Declared by researcher."}}); assert r.status_code==200,r.text
    r=c.post(f"/v1/research/conclusions/{cid}/evidence-bindings",json={"data":{"binding_key":"ev-2","source_type":"counterargument","source_ref":"counterargument:1","role":"contradicts"}}); assert r.status_code==200,r.text
    r=c.post(f"/v1/research/conclusions/{cid}/caveats",json={"data":{"caveat_key":"cav-1","caveat_type":"generalizability","statement_text":"Scope is limited to the registered sample.","status":"open"}}); assert r.status_code==200,r.text
    r=c.post(f"/v1/research/conclusions/{cid}/dissent",json={"data":{"dissent_key":"d-1","statement_text":"A competing interpretation remains viable.","status":"recorded","evidence_refs":["evidence:2"]}}); assert r.status_code==200,r.text
    for i,(typ,text) in enumerate((("reviewed","Reviewed registered evidence."),("qualified_by_researcher","Qualified conclusion because of unresolved caveat."))):
        r=c.post(f"/v1/research/conclusions/{cid}/decision-trace",json={"data":{"trace_key":f"t-{i}","step_index":i,"step_type":typ,"action_text":text}}); assert r.status_code==200,r.text
    r=c.post(f"/v1/research/conclusions/{cid}/reviews",json={"data":{"review_key":"review-1","review_type":"peer_review","reviewer_ref":"reviewer:external","disposition":"accepted_with_caveats","review_text":"Caveat should remain visible."}}); assert r.status_code==200,r.text
    r=c.post(f"/v1/research/conclusions/{cid}/revisions",json={"data":{"status":"qualified","limitations":["Registered scope limitation."],"change_summary":"Qualified after review."}}); assert r.status_code==200,r.text; assert r.json()["revision"]==1; assert len(r.json()["state_hash"])==64
    g=c.get(f"/v1/research/conclusions/{cid}/governance"); assert g.status_code==200,g.text; d=g.json()["descriptive_governance"]; assert d["evidence_role_counts"]["supports"]==1; assert d["evidence_role_counts"]["contradicts"]==1; assert d["open_caveat_count"]==1; assert d["dissent_status_counts"]["recorded"]==1; assert d["review_disposition_counts"]["accepted_with_caveats"]==1; assert g.json()["governance_summary_is_descriptive_only"] is True; assert g.json()["conclusion_score_computed"] is False
    s1=c.post(f"/v1/research/conclusions/{cid}/snapshots",json={"data":{}}).json(); s2=c.post(f"/v1/research/conclusions/{cid}/snapshots",json={"data":{}}).json(); assert s2["previous_snapshot_hash"]==s1["content_hash"]
    b=c.get(f"/v1/research/conclusions/{cid}/bundle").json(); assert len(b["evidence_bindings"])==2; assert len(b["caveats"])==1; assert len(b["dissent_records"])==1; assert len(b["decision_trace_steps"])==2; assert len(b["reviews"])==1; assert len(b["revisions"])==1; assert len(b["snapshots"])==2; assert b["choose_conclusion_by_core"] is False; assert b["publish_by_core"] is False; c.close()

def test_boundary_rejection(tmp_path):
    c=client(tmp_path); pid=project(c); aid=argument(c,pid)
    r=c.post(f"/v1/research/conclusions/arguments/{aid}",json={"data":{"conclusion_key":"bad","title":"Bad","conclusion_text":"Bad","choose_conclusion_by_core":True}}); assert r.status_code==422; c.close()

def test_private_public_boundary(tmp_path):
    c=client(tmp_path)
    r=c.post("/v1/research/projects",json={"data":{"title":"Private","project_key":"private-conclusion","visibility":"private"}}); pid=r.json()["project"]["id"]; aid=argument(c,pid); cid=conclusion(c,aid)
    # Internal endpoint remains available; public service path enforces project visibility at service level.
    from app.services import research_conclusions as svc
    with c.app.state.database.session_factory() as db:
        try: svc.bundle(db,cid,True); assert False,"expected private-project rejection"
        except ValueError as e: assert "not public" in str(e)
    c.close()
