from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

def client(tmp_path): return TestClient(create_app(Settings(database_url="sqlite:///"+str(tmp_path/"workflow.db"))))
def wf(c,key="w",visibility="public",**extra):
 r=c.post("/v1/research/workflows",json={"data":{"workflow_key":"workflow-"+key,"title":"Research lifecycle","visibility":visibility,**extra}}); assert r.status_code==200,r.text; return r.json()["id"]
def test_readiness(tmp_path):
 c=client(tmp_path); d=c.get("/v1/research/workflows/readiness").json(); assert d["release"]=="2.90.0" and d["migration_0094_applied"] is True; assert d["workflow_registry_by_core"] is True and d["autonomously_advance_workflow_by_core"] is False and d["determine_truth_by_core"] is False; c.close()
def test_lifecycle_transition(tmp_path):
 c=client(tmp_path); w=wf(c,"life",project_ref="project-1",protocol_ref="protocol-1",status="active")
 for key,typ,ord,status,prod in [("question","question",1,"in_progress","workspace"),("search","search",2,"pending","research_librarian"),("evidence","evidence",3,"pending","library")]:
  assert c.post(f"/v1/research/workflows/{w}/stages",json={"data":{"stage_key":key,"stage_type":typ,"ordinal":ord,"status":status,"responsible_product":prod}}).status_code==200
 assert c.post(f"/v1/research/workflows/{w}/transitions",json={"data":{"transition_key":"q-search","from_stage_key":"question","to_stage_key":"search","trigger_type":"manual"}}).status_code==200
 bad=c.post(f"/v1/research/workflows/{w}/transitions/q-search/apply",json={"data":{}}); assert bad.status_code==422
 ok=c.post(f"/v1/research/workflows/{w}/transitions/q-search/apply",json={"data":{"declared_complete":True,"actor_ref":"researcher-1"}}); assert ok.status_code==200 and ok.json()["current_stage_key"]=="search" and ok.json()["autonomous"] is False
 s=c.get(f"/v1/research/workflows/{w}/summary").json(); assert s["current_stage_key"]=="search" and s["summary_is_descriptive_not_research_judgment"] is True; c.close()
def test_context_handoff_checkpoint_policy(tmp_path):
 c=client(tmp_path); w=wf(c,"handoff",status="active")
 assert c.post(f"/v1/research/workflows/{w}/stages",json={"data":{"stage_key":"analysis","stage_type":"analysis","ordinal":1,"status":"ready","responsible_product":"workbench"}}).status_code==200
 assert c.post(f"/v1/research/workflows/{w}/context-bindings",json={"data":{"binding_key":"dataset","stage_key":"analysis","product_key":"workbench","object_type":"dataset","object_ref":"dataset:42","relation":"analysis_input"}}).status_code==200
 assert c.post(f"/v1/research/workflows/{w}/handoffs",json={"data":{"handoff_key":"lab-workbench","stage_key":"analysis","from_product":"research_lab","to_product":"workbench","status":"ready","context":{"dataset_ref":"dataset:42"}}}).status_code==200
 assert c.post(f"/v1/research/workflows/{w}/checkpoints",json={"data":{"checkpoint_key":"method-ready","stage_key":"analysis","checkpoint_type":"method_ready","status":"satisfied","statement_text":"Method declared.","evidence_refs":["method:ols"]}}).status_code==200
 assert c.post(f"/v1/research/workflows/{w}/policies",json={"data":{"policy_key":"manual-analysis","scope":"transition","rule_type":"manual_approval","rule":{"stage_key":"analysis"}}}).status_code==200
 l=c.get(f"/v1/research/workflows/{w}/lineage").json(); assert l["lineage_is_declared_not_inferred"] is True and any(x["relation"]=="workflow_handoff" for x in l["edges"]); c.close()
def test_events_revision_snapshot_and_guardrails(tmp_path):
 c=client(tmp_path); w=wf(c,"rev")
 assert c.post(f"/v1/research/workflows/{w}/events",json={"data":{"event_key":"e1","event_type":"challenge_recorded","details":{"challenge_ref":"challenge-1"}}}).status_code==200
 r=c.post(f"/v1/research/workflows/{w}/revisions",json={"data":{"status":"active","change_summary":"Workflow initiated."}}); assert r.status_code==200 and r.json()["revision"]==1
 s1=c.post(f"/v1/research/workflows/{w}/snapshots",json={"data":{}}).json(); s2=c.post(f"/v1/research/workflows/{w}/snapshots",json={"data":{}}).json(); assert s2["previous_snapshot_hash"]==s1["content_hash"]
 for k in ("choose_research_path_by_core","autonomously_advance_workflow_by_core","execute_specialist_work_by_core","dispatch_external_handoff_by_core","infer_stage_completion_by_core","approve_scientific_validity_by_core","determine_truth_by_core"):
  bad={"workflow_key":"bad-"+k,"title":"Bad",k:True}; assert c.post("/v1/research/workflows",json={"data":bad}).status_code==422
 c.close()
def test_public_boundary(tmp_path):
 c=client(tmp_path); pub=wf(c,"pub","public"); priv=wf(c,"priv","private")
 from app.services import research_workflows as svc
 with c.app.state.database.session_factory() as db:
  assert svc.bundle(db,pub,True)["workflow"]["visibility"]=="public"
  try: svc.bundle(db,priv,True); assert False,"expected private rejection"
  except ValueError as e: assert "not public" in str(e)
 c.close()
