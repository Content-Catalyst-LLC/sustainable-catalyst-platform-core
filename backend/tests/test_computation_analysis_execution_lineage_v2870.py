from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
def client(tmp_path): return TestClient(create_app(Settings(database_url="sqlite:///"+str(tmp_path/"lineage.db"))))
def execution(c,key="py",runtime="python",visibility="public",etype="statistical_analysis"):
 r=c.post("/v1/research/computation-lineage/executions",json={"data":{"execution_key":"exec-"+key,"title":"Analysis execution","execution_type":etype,"runtime_kind":runtime,"visibility":visibility,"external_run_ref":"workspace:run-1","source_revision":"abc123"}}); assert r.status_code==200,r.text; return r.json()["id"]
def test_readiness(tmp_path):
 c=client(tmp_path); d=c.get("/v1/research/computation-lineage/readiness").json(); assert d["release"]=="2.87.0" and d["migration_0091_applied"] is True; assert d["execution_registry_by_core"] is True and d["run_python_by_core"] is False and d["infer_truth_by_core"] is False; c.close()
def test_python_execution_full_lineage(tmp_path):
 c=client(tmp_path); e=execution(c)
 assert c.post(f"/v1/research/computation-lineage/executions/{e}/inputs",json={"data":{"input_key":"dataset","input_type":"dataset","object_ref":"dataset:climate-v4","version_ref":"v4","content_hash":"sha256:123"}}).status_code==200
 assert c.post(f"/v1/research/computation-lineage/executions/{e}/parameters",json={"data":{"parameter_key":"alpha","value":{"number":0.05}}}).status_code==200
 assert c.post(f"/v1/research/computation-lineage/executions/{e}/assumptions",json={"data":{"assumption_key":"iid","statement_text":"Residual independence declared."}}).status_code==200
 assert c.post(f"/v1/research/computation-lineage/executions/{e}/environments",json={"data":{"environment_key":"python","environment_type":"python","runtime_name":"CPython","runtime_version":"3.12","packages":["pandas==2.x"]}}).status_code==200
 assert c.post(f"/v1/research/computation-lineage/executions/{e}/steps",json={"data":{"step_key":"fit","sequence":1,"step_type":"analyze","tool_ref":"python:statsmodels","code_ref":"git:abc123"}}).status_code==200
 assert c.post(f"/v1/research/computation-lineage/executions/{e}/outputs",json={"data":{"output_key":"coef","output_type":"statistic","object_ref":"result:coef-1","content_hash":"sha256:456"}}).status_code==200
 assert c.post(f"/v1/research/computation-lineage/executions/{e}/research-bindings",json={"data":{"binding_key":"claim","source_output_ref":"result:coef-1","target_type":"claim","target_ref":"claim:42","relation":"basis_for"}}).status_code==200
 b=c.get(f"/v1/research/computation-lineage/executions/{e}/bundle").json(); assert len(b["inputs"])==1 and len(b["environments"])==1 and len(b["research_bindings"])==1
 l=c.get(f"/v1/research/computation-lineage/executions/{e}/lineage").json(); assert l["lineage_is_declared_not_inferred"] is True and any(x["relation"]=="basis_for" for x in l["edges"]); c.close()
def test_multi_runtime_dependencies_and_verification(tmp_path):
 c=client(tmp_path); a=execution(c,"r","r","public","causal_analysis"); b=execution(c,"julia","julia","public","simulation")
 assert c.post(f"/v1/research/computation-lineage/executions/{b}/dependencies",json={"data":{"dependency_key":"upstream","upstream_execution_ref":a,"relation":"consumes_output"}}).status_code==200
 assert c.post(f"/v1/research/computation-lineage/executions/{b}/verifications",json={"data":{"verification_key":"checksum","verification_type":"checksum","status":"passed","evidence":{"hash":"abc"}}}).status_code==200
 s=c.get(f"/v1/research/computation-lineage/executions/{b}/summary").json(); assert s["counts"]["dependencies"]==1 and s["counts"]["verifications"]==1; c.close()
def test_revision_snapshot_and_guardrails(tmp_path):
 c=client(tmp_path); e=execution(c,"workbench","workbench","public","engineering_calculation")
 r=c.post(f"/v1/research/computation-lineage/executions/{e}/revisions",json={"data":{"status":"completed","finished_at":"2026-09-20T12:00:00Z","change_summary":"Recorded external completion."}}); assert r.status_code==200 and r.json()["revision"]==1
 s1=c.post(f"/v1/research/computation-lineage/executions/{e}/snapshots",json={"data":{}}).json(); s2=c.post(f"/v1/research/computation-lineage/executions/{e}/snapshots",json={"data":{}}).json(); assert s2["previous_snapshot_hash"]==s1["content_hash"]
 for bad in ({"execution_key":"bad1","title":"Bad","execution_type":"notebook","runtime_kind":"python","execute_code_by_core":True},{"execution_key":"bad2","title":"Bad","execution_type":"ml_training","runtime_kind":"ml_runtime","train_ml_by_core":True},{"execution_key":"bad3","title":"Bad","execution_type":"statistical_analysis","runtime_kind":"r","infer_claims_by_core":True}): assert c.post("/v1/research/computation-lineage/executions",json={"data":bad}).status_code==422
 c.close()
def test_public_boundary(tmp_path):
 c=client(tmp_path); pub=execution(c,"pub","container","public","workflow_step"); priv=execution(c,"priv","external_service","private","other")
 from app.services import computation_lineage as svc
 with c.app.state.database.session_factory() as db:
  assert svc.bundle(db,pub,True)["execution"]["visibility"]=="public"
  try: svc.bundle(db,priv,True); assert False,"expected private execution rejection"
  except ValueError as e: assert "not public" in str(e)
 c.close()
