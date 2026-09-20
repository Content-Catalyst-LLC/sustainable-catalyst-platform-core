from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app


def client(tmp_path):
    return TestClient(create_app(Settings(database_url="sqlite:///"+str(tmp_path/"program.db"))))


def project(c, key="program-project", visibility="public"):
    r=c.post("/v1/research/projects",json={"data":{"title":"Program Project","project_key":key,"visibility":visibility}})
    assert r.status_code==200,r.text
    return r.json()["project"]["id"]


def program(c, visibility="public"):
    r=c.post("/v1/research/programs",json={"data":{"program_key":"climate-resilience","title":"Climate Resilience Research Program","visibility":visibility,"horizon_start":"2026-01-01","horizon_end":"2030-12-31","vision_text":"Track cumulative research and evidence evolution."}})
    assert r.status_code==200,r.text
    return r.json()["id"]


def test_readiness(tmp_path):
    c=client(tmp_path); d=c.get("/v1/research/programs/readiness").json()
    assert d["release"]=="2.84.0"; assert d["migration_0088_applied"] is True
    assert d["research_program_registry_by_core"] is True
    assert d["longitudinal_knowledge_node_registry_by_core"] is True
    assert d["descriptive_longitudinal_timeline_by_core"] is True
    assert d["prioritize_research_by_core"] is False
    assert d["auto_link_knowledge_graph_by_core"] is False
    assert d["infer_truth_by_core"] is False
    c.close()


def test_program_projects_objectives_milestones(tmp_path):
    c=client(tmp_path); pid=project(c); rid=program(c)
    m=c.post(f"/v1/research/programs/{rid}/projects",json={"data":{"membership_key":"primary-project","project_entity_id":pid,"role":"lead","joined_at":"2026-09-20"}}); assert m.status_code==200,m.text
    o=c.post(f"/v1/research/programs/{rid}/objectives",json={"data":{"objective_key":"obj-1","title":"Establish a reproducible longitudinal evidence base","target_horizon":"2028","success_criteria":["replication records","cross-study synthesis"],"evidence_refs":["program:charter"]}}); assert o.status_code==200,o.text
    ms=c.post(f"/v1/research/programs/{rid}/milestones",json={"data":{"milestone_key":"m1","title":"First synthesis published","milestone_type":"publication","status":"planned","target_at":"2027-06-30","related_refs":["publication:planned"]}}); assert ms.status_code==200,ms.text
    b=c.get(f"/v1/research/programs/{rid}/bundle").json(); assert len(b["project_memberships"])==1; assert len(b["objectives"])==1; assert len(b["milestones"])==1
    assert b["rank_projects_by_core"] is False
    c.close()


def test_longitudinal_graph_states_events_and_lineage(tmp_path):
    c=client(tmp_path); rid=program(c)
    n1=c.post(f"/v1/research/programs/{rid}/longitudinal/nodes",json={"data":{"node_key":"claim-a","object_type":"claim","object_ref":"claim:alpha","label":"Initial claim","first_observed_at":"2026-01-01","state":{"status":"proposed"}}}); assert n1.status_code==200,n1.text
    n2=c.post(f"/v1/research/programs/{rid}/longitudinal/nodes",json={"data":{"node_key":"synthesis-a","object_type":"evidence_synthesis","object_ref":"synthesis:alpha","label":"Later synthesis","first_observed_at":"2027-01-15","state":{"status":"completed"}}}); assert n2.status_code==200,n2.text
    e=c.post(f"/v1/research/programs/{rid}/longitudinal/edges",json={"data":{"edge_key":"edge-1","source_node_id":n1.json()["id"],"target_node_id":n2.json()["id"],"relation_type":"qualified_by" if False else "qualifies","valid_from":"2027-01-15","evidence_refs":["synthesis:alpha"]}}); assert e.status_code==200,e.text
    s1=c.post(f"/v1/research/programs/{rid}/knowledge-states",json={"data":{"state_key":"state-1","observed_at":"2026-01-01","subject_type":"claim","subject_ref":"claim:alpha","status":"proposed","summary_text":"Initial state.","evidence_refs":["source:1"]}}); assert s1.status_code==200,s1.text
    s2=c.post(f"/v1/research/programs/{rid}/knowledge-states",json={"data":{"state_key":"state-2","observed_at":"2027-01-15","subject_type":"claim","subject_ref":"claim:alpha","status":"qualified","summary_text":"Later synthesis qualified the original claim.","evidence_refs":["synthesis:alpha"]}}); assert s2.status_code==200,s2.text
    ev=c.post(f"/v1/research/programs/{rid}/evolution-events",json={"data":{"event_key":"event-1","event_type":"updated","occurred_at":"2027-01-15","subject_ref":"claim:alpha","prior_state_ref":s1.json()["id"],"resulting_state_ref":s2.json()["id"],"description_text":"Recorded change in the research state.","evidence_refs":["synthesis:alpha"]}}); assert ev.status_code==200,ev.text
    g=c.get(f"/v1/research/programs/{rid}/graph").json(); assert len(g["nodes"])==2; assert len(g["edges"])==1; assert g["graph_is_declared_not_inferred"] is True
    tl=c.get(f"/v1/research/programs/{rid}/timeline").json(); assert len(tl["entries"])==3; assert tl["entries"][0]["timestamp"]=="2026-01-01"
    ln=c.get(f"/v1/research/programs/{rid}/lineage").json(); assert len(ln["longitudinal_edges"])==1; assert len(ln["knowledge_state_evidence_edges"])==2; assert ln["lineage_is_declared_not_inferred"] is True
    c.close()


def test_revision_snapshot_and_boundaries(tmp_path):
    c=client(tmp_path); rid=program(c)
    r=c.post(f"/v1/research/programs/{rid}/revisions",json={"data":{"status":"active","vision_text":"Updated researcher-authored program vision.","change_summary":"Program charter refreshed."}}); assert r.status_code==200,r.text; assert r.json()["revision"]==1
    s1=c.post(f"/v1/research/programs/{rid}/snapshots",json={"data":{}}).json(); s2=c.post(f"/v1/research/programs/{rid}/snapshots",json={"data":{}}).json(); assert s2["previous_snapshot_hash"]==s1["content_hash"]
    bad=c.post("/v1/research/programs",json={"data":{"program_key":"bad","title":"Bad","prioritize_research_by_core":True}}); assert bad.status_code==422,bad.text
    bad2=c.post(f"/v1/research/programs/{rid}/longitudinal/nodes",json={"data":{"node_key":"bad","object_type":"claim","object_ref":"claim:x","auto_link_knowledge_graph_by_core":True}}); assert bad2.status_code==422,bad2.text
    c.close()


def test_public_boundary_and_private_membership_redaction(tmp_path):
    c=client(tmp_path); private_program=program(c,"private")
    from app.services import research_programs as svc
    with c.app.state.database.session_factory() as db:
        try: svc.bundle(db,private_program,True); assert False,"expected private-program rejection"
        except ValueError as e: assert "not public" in str(e)
    c.close()
