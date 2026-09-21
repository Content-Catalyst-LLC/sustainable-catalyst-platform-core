from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

def client(tmp_path): return TestClient(create_app(Settings(database_url="sqlite:///"+str(tmp_path/"inference.db"))))
def inf(c,key="obs",itype="observation",visibility="public",**extra):
 p={"inference_key":"inf-"+key,"title":"Inference","statement_text":"Declared research statement.","inference_type":itype,"visibility":visibility,**extra}; r=c.post("/v1/research/inferences",json={"data":p}); assert r.status_code==200,r.text; return r.json()["id"]
def test_readiness(tmp_path):
 c=client(tmp_path); d=c.get("/v1/research/inferences/readiness").json(); assert d["release"]=="2.88.0" and d["migration_0092_applied"] is True; assert d["inference_registry_by_core"] is True and d["generate_inferences_by_core"] is False and d["determine_truth_by_core"] is False; c.close()
def test_taxonomy_classification_basis_and_lineage(tmp_path):
 c=client(tmp_path); i=inf(c,"stat","statistical_inference",execution_ref="exec-1",source_object_type="finding",source_object_ref="finding-1")
 assert c.post(f"/v1/research/inferences/{i}/classifications",json={"data":{"classification_key":"claim-class","object_type":"claim","object_ref":"claim-1","inference_type":"statistical_inference","classification_basis":"Researcher-declared classification."}}).status_code==200
 assert c.post(f"/v1/research/inferences/{i}/basis",json={"data":{"basis_key":"coef","basis_type":"computation_output","basis_ref":"result:coef","relation":"computed_from"}}).status_code==200
 assert c.post(f"/v1/research/inferences/{i}/assumptions",json={"data":{"assumption_key":"iid","statement_text":"Residual independence assumed."}}).status_code==200
 assert c.post(f"/v1/research/inferences/{i}/uncertainties",json={"data":{"uncertainty_key":"sampling","uncertainty_type":"sampling","description":"Sampling uncertainty declared.","quantitative":{"se":0.2}}}).status_code==200
 b=c.get(f"/v1/research/inferences/{i}/bundle").json(); assert len(b["classifications"])==1 and len(b["basis_bindings"])==1 and len(b["uncertainties"])==1
 l=c.get(f"/v1/research/inferences/{i}/lineage").json(); assert l["lineage_is_declared_not_inferred"] is True and any(x["relation"]=="computed_from" for x in l["edges"]); c.close()
def test_causal_distinction_and_challenge(tmp_path):
 c=client(tmp_path)
 bad=c.post("/v1/research/inferences",json={"data":{"inference_key":"causal-bad","title":"Causal","statement_text":"X caused Y.","inference_type":"causal_inference"}}); assert bad.status_code==422
 i=inf(c,"causal","causal_inference",method_ref="causal-method:did",protocol_ref="protocol-1")
 assert c.post(f"/v1/research/inferences/{i}/challenges",json={"data":{"challenge_key":"confounding","challenge_type":"causal","statement_text":"Residual confounding remains possible.","evidence_refs":["evidence:7"]}}).status_code==200
 s=c.get(f"/v1/research/inferences/{i}/summary").json(); assert s["challenge_types"]["causal"]==1 and s["confidence_is_researcher_declared_not_scored"] is True; c.close()
def test_relations_revision_snapshot_and_guardrails(tmp_path):
 c=client(tmp_path); a=inf(c,"a","interpretation"); b=inf(c,"b","speculation")
 assert c.post(f"/v1/research/inferences/{a}/relations",json={"data":{"relation_key":"alt","target_inference_ref":b,"relation":"alternative_to"}}).status_code==200
 r=c.post(f"/v1/research/inferences/{a}/revisions",json={"data":{"status":"qualified","change_summary":"Qualified after review."}}); assert r.status_code==200 and r.json()["revision"]==1
 s1=c.post(f"/v1/research/inferences/{a}/snapshots",json={"data":{}}).json(); s2=c.post(f"/v1/research/inferences/{a}/snapshots",json={"data":{}}).json(); assert s2["previous_snapshot_hash"]==s1["content_hash"]
 for k in ("infer_causality_by_core","score_confidence_by_core","rank_evidence_by_core","resolve_contradictions_by_core","determine_truth_by_core"):
  bad={"inference_key":"bad-"+k,"title":"Bad","statement_text":"Bad","inference_type":"observation",k:True}; assert c.post("/v1/research/inferences",json={"data":bad}).status_code==422
 c.close()
def test_public_boundary(tmp_path):
 c=client(tmp_path); pub=inf(c,"pub","descriptive_finding","public"); priv=inf(c,"priv","interpretation","private")
 from app.services import unified_inference as svc
 with c.app.state.database.session_factory() as db:
  assert svc.bundle(db,pub,True)["inference"]["visibility"]=="public"
  try: svc.bundle(db,priv,True); assert False,"expected private rejection"
  except ValueError as e: assert "not public" in str(e)
 c.close()
