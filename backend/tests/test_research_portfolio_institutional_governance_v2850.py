from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

def client(tmp_path): return TestClient(create_app(Settings(database_url="sqlite:///"+str(tmp_path/"portfolio.db"))))
def program(c,key,visibility="public"):
    r=c.post("/v1/research/programs",json={"data":{"program_key":key,"title":key.replace("-"," ").title(),"visibility":visibility}}); assert r.status_code==200,r.text; return r.json()["id"]
def portfolio(c,visibility="public"):
    r=c.post("/v1/research/portfolios",json={"data":{"portfolio_key":"institutional-research","title":"Institutional Research Portfolio","visibility":visibility,"charter_text":"Govern multiple research programs with explicit institutional provenance."}}); assert r.status_code==200,r.text; return r.json()["id"]
def test_readiness(tmp_path):
    c=client(tmp_path); d=c.get("/v1/research/portfolios/readiness").json(); assert d["release"]=="2.85.0"; assert d["migration_0089_applied"] is True; assert d["research_portfolio_registry_by_core"] is True; assert d["descriptive_portfolio_map_by_core"] is True; assert d["prioritize_programs_by_core"] is False; assert d["allocate_resources_by_core"] is False; assert d["infer_truth_by_core"] is False; c.close()
def test_membership_themes_objectives_resources_and_risks(tmp_path):
    c=client(tmp_path); a=program(c,"climate"); p=portfolio(c)
    assert c.post(f"/v1/research/portfolios/{p}/programs",json={"data":{"membership_key":"climate","program_id":a,"role":"lead"}}).status_code==200
    assert c.post(f"/v1/research/portfolios/{p}/themes",json={"data":{"theme_key":"resilience","title":"Climate resilience","evidence_refs":["program:"+a]}}).status_code==200
    assert c.post(f"/v1/research/portfolios/{p}/objectives",json={"data":{"objective_key":"reproducibility","title":"Increase reproducibility","success_criteria":["replication packages"]}}).status_code==200
    assert c.post(f"/v1/research/portfolios/{p}/resources",json={"data":{"envelope_key":"compute-2027","resource_type":"compute","label":"Declared research compute envelope","declared_amount_text":"institution-declared capacity","constraints":["not an allocation decision"]}}).status_code==200
    assert c.post(f"/v1/research/portfolios/{p}/risks",json={"data":{"risk_key":"source-continuity","title":"Source continuity risk","status":"monitoring","evidence_refs":["risk-register:1"]}}).status_code==200
    b=c.get(f"/v1/research/portfolios/{p}/bundle").json(); assert len(b["program_memberships"])==1; assert len(b["themes"])==1; assert len(b["objectives"])==1; assert len(b["resource_envelopes"])==1; assert len(b["risks"])==1; assert b["rank_programs_by_core"] is False; c.close()
def test_dependencies_reviews_decisions_map_and_lineage(tmp_path):
    c=client(tmp_path); a=program(c,"energy"); b=program(c,"carbon"); p=portfolio(c)
    for key,x in (("energy",a),("carbon",b)): assert c.post(f"/v1/research/portfolios/{p}/programs",json={"data":{"membership_key":key,"program_id":x}}).status_code==200
    d=c.post(f"/v1/research/portfolios/{p}/dependencies",json={"data":{"dependency_key":"carbon-needs-energy","source_program_id":b,"target_program_id":a,"relation_type":"depends_on","evidence_refs":["review:1"]}}); assert d.status_code==200,d.text
    assert c.post(f"/v1/research/portfolios/{p}/reviews",json={"data":{"review_key":"q1","reviewed_at":"2027-03-31","summary_text":"Recorded institutional review.","recommendations":["researcher-authored recommendation"]}}).status_code==200
    assert c.post(f"/v1/research/portfolios/{p}/decisions",json={"data":{"decision_key":"decision-1","decided_at":"2027-04-02","decision_type":"scope","statement_text":"Retain both research programs.","decision_maker":"research governance board","evidence_refs":["review:q1"]}}).status_code==200
    m=c.get(f"/v1/research/portfolios/{p}/map").json(); assert len(m["programs"])==2 and len(m["dependencies"])==1; assert m["map_is_declared_not_inferred"] is True
    l=c.get(f"/v1/research/portfolios/{p}/lineage").json(); assert len(l["program_membership_edges"])==2; assert len(l["dependency_edges"])==1; assert len(l["decision_evidence_edges"])==1; c.close()
def test_revision_snapshot_and_guardrails(tmp_path):
    c=client(tmp_path); p=portfolio(c); r=c.post(f"/v1/research/portfolios/{p}/revisions",json={"data":{"charter_text":"Updated institutional charter.","change_summary":"Annual charter review."}}); assert r.status_code==200 and r.json()["revision"]==1
    s1=c.post(f"/v1/research/portfolios/{p}/snapshots",json={"data":{}}).json(); s2=c.post(f"/v1/research/portfolios/{p}/snapshots",json={"data":{}}).json(); assert s2["previous_snapshot_hash"]==s1["content_hash"]
    for bad in ({"portfolio_key":"bad","title":"Bad","rank_programs_by_core":True},{"portfolio_key":"bad2","title":"Bad","allocate_resources_by_core":True},{"portfolio_key":"bad3","title":"Bad","decide_governance_by_core":True}): assert c.post("/v1/research/portfolios",json={"data":bad}).status_code==422
    c.close()
def test_public_boundary_and_private_program_redaction(tmp_path):
    c=client(tmp_path); pub=program(c,"public-program","public"); priv=program(c,"private-program","private"); p=portfolio(c,"public")
    for key,x in (("pub",pub),("priv",priv)): assert c.post(f"/v1/research/portfolios/{p}/programs",json={"data":{"membership_key":key,"program_id":x}}).status_code==200
    from app.services import research_portfolios as svc
    with c.app.state.database.session_factory() as db:
        pb=svc.bundle(db,p,True); assert len(pb["program_memberships"])==1 and pb["program_memberships"][0]["program_id"]==pub
        q=portfolio(c,"private")
        try: svc.bundle(db,q,True); assert False,"expected private portfolio rejection"
        except ValueError as e: assert "not public" in str(e)
    c.close()
