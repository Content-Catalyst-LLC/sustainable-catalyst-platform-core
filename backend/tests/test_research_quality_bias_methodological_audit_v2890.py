from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

def client(tmp_path): return TestClient(create_app(Settings(database_url="sqlite:///"+str(tmp_path/"quality.db"))))
def audit(c,key="a",visibility="public",**extra):
 r=c.post("/v1/research/quality-audits",json={"data":{"audit_key":"audit-"+key,"title":"Methodological audit","visibility":visibility,**extra}}); assert r.status_code==200,r.text; return r.json()["id"]
def test_readiness(tmp_path):
 c=client(tmp_path); d=c.get("/v1/research/quality-audits/readiness").json(); assert d["release"]=="2.89.0" and d["migration_0093_applied"] is True; assert d["quality_audit_registry_by_core"] is True and d["score_research_quality_by_core"] is False and d["determine_truth_by_core"] is False; c.close()
def test_systematic_checks_findings_and_evidence(tmp_path):
 c=client(tmp_path); a=audit(c,"checks",project_ref="project-1",protocol_ref="protocol-1")
 assert c.post(f"/v1/research/quality-audits/{a}/subjects",json={"data":{"subject_key":"claim","object_type":"claim","object_ref":"claim-1","role":"primary_subject"}}).status_code==200
 assert c.post(f"/v1/research/quality-audits/{a}/checks",json={"data":{"check_key":"causal","check_type":"unsupported_causal_claim","status":"concern","statement_text":"Causal language requires methodological support.","affected_object_ref":"claim-1"}}).status_code==200
 f=c.post(f"/v1/research/quality-audits/{a}/findings",json={"data":{"finding_key":"causal-gap","category":"unsupported_causal_claim","finding_type":"concern","statement_text":"Declared audit concern.","affected_object_type":"claim","affected_object_ref":"claim-1","declared_concern_level":"high"}}); assert f.status_code==200
 assert c.post(f"/v1/research/quality-audits/{a}/evidence",json={"data":{"evidence_key":"method-doc","finding_ref":f.json()["id"],"evidence_type":"protocol","evidence_ref":"protocol-1","relation":"documents"}}).status_code==200
 s=c.get(f"/v1/research/quality-audits/{a}/summary").json(); assert s["check_types"]["unsupported_causal_claim"]==1 and s["coverage_is_descriptive_not_a_quality_score"] is True; c.close()
def test_bias_and_method_assessments(tmp_path):
 c=client(tmp_path); a=audit(c,"bias",execution_ref="exec-1",inference_ref="inf-1")
 assert c.post(f"/v1/research/quality-audits/{a}/bias-assessments",json={"data":{"bias_key":"conf","bias_type":"confounding","status":"concern","statement_text":"Residual confounding is assessor-declared.","residual_uncertainty":"Unmeasured factors may remain."}}).status_code==200
 assert c.post(f"/v1/research/quality-audits/{a}/method-assessments",json={"data":{"method_assessment_key":"did","method_ref":"method:did","assessment_type":"causal","status":"indeterminate","statement_text":"Parallel-trends support remains under review.","execution_ref":"exec-1"}}).status_code==200
 b=c.get(f"/v1/research/quality-audits/{a}/bundle").json(); assert len(b["bias_assessments"])==1 and len(b["method_assessments"])==1
 l=c.get(f"/v1/research/quality-audits/{a}/lineage").json(); assert l["lineage_is_declared_not_inferred"] is True and any(x["relation"]=="assesses_method" for x in l["edges"]); c.close()
def test_response_revision_snapshot_and_guardrails(tmp_path):
 c=client(tmp_path); a=audit(c,"rev")
 assert c.post(f"/v1/research/quality-audits/{a}/responses",json={"data":{"response_key":"r1","response_type":"sensitivity_analysis","status":"planned","statement_text":"Run a sensitivity analysis."}}).status_code==200
 r=c.post(f"/v1/research/quality-audits/{a}/revisions",json={"data":{"status":"in_progress","change_summary":"Audit initiated."}}); assert r.status_code==200 and r.json()["revision"]==1
 s1=c.post(f"/v1/research/quality-audits/{a}/snapshots",json={"data":{}}).json(); s2=c.post(f"/v1/research/quality-audits/{a}/snapshots",json={"data":{}}).json(); assert s2["previous_snapshot_hash"]==s1["content_hash"]
 for k in ("infer_bias_by_core","score_research_quality_by_core","rank_studies_by_core","determine_method_validity_by_core","determine_causal_validity_by_core","certify_reproducibility_by_core","determine_truth_by_core"):
  bad={"audit_key":"bad-"+k,"title":"Bad",k:True}; assert c.post("/v1/research/quality-audits",json={"data":bad}).status_code==422
 c.close()
def test_public_boundary(tmp_path):
 c=client(tmp_path); pub=audit(c,"pub","public"); priv=audit(c,"priv","private")
 from app.services import research_quality_audit as svc
 with c.app.state.database.session_factory() as db:
  assert svc.bundle(db,pub,True)["audit"]["visibility"]=="public"
  try: svc.bundle(db,priv,True); assert False,"expected private rejection"
  except ValueError as e: assert "not public" in str(e)
 c.close()
