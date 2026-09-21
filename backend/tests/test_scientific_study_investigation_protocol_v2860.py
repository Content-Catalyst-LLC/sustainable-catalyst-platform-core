from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
def client(tmp_path): return TestClient(create_app(Settings(database_url="sqlite:///"+str(tmp_path/"protocol.db"))))
def protocol(c,study_type="experimental",visibility="public"):
 r=c.post("/v1/research/protocols",json={"data":{"protocol_key":"p-"+study_type,"title":"Protocol","study_type":study_type,"visibility":visibility,"research_question_text":"What happens?"}}); assert r.status_code==200,r.text; return r.json()["id"]
def test_readiness(tmp_path):
 c=client(tmp_path); d=c.get("/v1/research/protocols/readiness").json(); assert d["release"]=="2.86.0" and d["migration_0090_applied"] is True; assert d["universal_protocol_registry_by_core"] is True and d["execute_protocol_by_core"] is False and d["infer_truth_by_core"] is False; c.close()
def test_experimental_protocol_components(tmp_path):
 c=client(tmp_path); p=protocol(c)
 assert c.post(f"/v1/research/protocols/{p}/objectives",json={"data":{"objective_key":"primary","statement_text":"Estimate intervention effect."}}).status_code==200
 assert c.post(f"/v1/research/protocols/{p}/scope",json={"data":{"scope_key":"population","scope_type":"population","label":"Eligible participants","inclusion_criteria":["declared"]}}).status_code==200
 assert c.post(f"/v1/research/protocols/{p}/measures",json={"data":{"measure_key":"outcome","measure_type":"outcome","name":"Primary outcome","role":"primary"}}).status_code==200
 assert c.post(f"/v1/research/protocols/{p}/acquisition-plans",json={"data":{"acquisition_key":"sample","acquisition_type":"sampling","procedure_text":"Declared sampling procedure.","quality_controls":["double check"]}}).status_code==200
 assert c.post(f"/v1/research/protocols/{p}/methods",json={"data":{"method_key":"model","method_type":"statistical","planned_inference_type":"statistical","parameters":{"alpha":0.05}}}).status_code==200
 b=c.get(f"/v1/research/protocols/{p}/bundle").json(); assert len(b["objectives"])==1 and len(b["scope_units"])==1 and len(b["method_plans"])==1; c.close()
def test_forensic_and_literature_protocols_are_universal(tmp_path):
 c=client(tmp_path); f=protocol(c,"forensic_investigation"); l=protocol(c,"systematic_review")
 assert c.post(f"/v1/research/protocols/{f}/sources",json={"data":{"source_key":"evidence","source_type":"forensic_evidence","source_ref":"evidence:1"}}).status_code==200
 assert c.post(f"/v1/research/protocols/{f}/validation-plans",json={"data":{"validation_key":"challenge","validation_type":"competing_hypotheses","procedure_text":"Compare declared competing explanations."}}).status_code==200
 assert c.post(f"/v1/research/protocols/{l}/sources",json={"data":{"source_key":"search","source_type":"literature_database","selection_criteria":["declared inclusion criteria"]}}).status_code==200
 assert c.post(f"/v1/research/protocols/{l}/outputs",json={"data":{"output_key":"synthesis","output_type":"systematic_review","label":"Review synthesis"}}).status_code==200
 assert c.get(f"/v1/research/protocols/{f}/lineage").json()["lineage_is_declared_not_inferred"] is True; c.close()
def test_deviation_revision_snapshot_and_guardrails(tmp_path):
 c=client(tmp_path); p=protocol(c,"engineering_investigation")
 assert c.post(f"/v1/research/protocols/{p}/assumptions",json={"data":{"assumption_key":"boundary","statement_text":"Boundary condition held constant.","sensitivity_plan_text":"Vary boundary in robustness analysis."}}).status_code==200
 assert c.post(f"/v1/research/protocols/{p}/deviations",json={"data":{"deviation_key":"d1","description_text":"Instrument substitution recorded.","rationale_text":"Original instrument unavailable."}}).status_code==200
 r=c.post(f"/v1/research/protocols/{p}/revisions",json={"data":{"protocol_version":"1.1","change_summary":"Documented amendment."}}); assert r.status_code==200 and r.json()["revision"]==1
 s1=c.post(f"/v1/research/protocols/{p}/snapshots",json={"data":{}}).json(); s2=c.post(f"/v1/research/protocols/{p}/snapshots",json={"data":{}}).json(); assert s2["previous_snapshot_hash"]==s1["content_hash"]
 for bad in ({"protocol_key":"bad1","title":"Bad","study_type":"experimental","execute_protocol_by_core":True},{"protocol_key":"bad2","title":"Bad","study_type":"observational","infer_causality_by_core":True},{"protocol_key":"bad3","title":"Bad","study_type":"forensic_investigation","certify_ethics_by_core":True}): assert c.post("/v1/research/protocols",json={"data":bad}).status_code==422
 c.close()
def test_public_boundary(tmp_path):
 c=client(tmp_path); pub=protocol(c,"mixed_method","public"); priv=protocol(c,"case_study","private")
 from app.services import research_protocols as svc
 with c.app.state.database.session_factory() as db:
  assert svc.bundle(db,pub,True)["protocol"]["visibility"]=="public"
  try: svc.bundle(db,priv,True); assert False,"expected private protocol rejection"
  except ValueError as e: assert "not public" in str(e)
 c.close()
