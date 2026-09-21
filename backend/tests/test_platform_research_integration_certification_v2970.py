from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import platform_research_certification as svc

def session(tmp_path):
    db=Database("sqlite:///"+str(tmp_path/"cert.db")); run_migrations(db); return db,db.session_factory()
def suite(s,visibility="public"):
    return svc.create_suite(s,{"suite_key":"platform-v1","title":"Platform integration certification","required_operations":["create","read","update","handoff","trace","version","snapshot"],"required_capabilities":["object:read","provenance:trace"],"visibility":visibility})
def product(s,c):
    return svc.add_product(s,{"product_key":"workspace","suite_id":c["id"],"product_ref":"product:workspace","product_version":"2.x","runtime_binding_ref":"binding:workspace","declared_capabilities":["object:read","provenance:trace"],"declared_object_types":["finding","dataset"],"visibility":"public"})
def case(s,c,key="read"):
    return svc.add_case(s,{"case_key":key,"suite_id":c["id"],"operation":"read","object_type":"finding","requirement":"Product can read a versioned finding through the runtime contract","expected_evidence":["response","trace"],"visibility":"public"})
def run(s,c,p):
    return svc.create_run(s,{"run_key":"run-1","suite_id":c["id"],"product_id":p["id"],"executed_by":"test:conformance-harness","environment_ref":"env:test","visibility":"public"})
def test_readiness_boundaries_and_migration(tmp_path):
    db,s=session(tmp_path); r=svc.readiness(s); st=migration_status(db); assert r["release"]=="2.97.0" and "0101" in st["applied"] and st["pending"]==[]; assert r["certification_suite_registry_by_core"] is True and r["invoke_product_by_core"] is False and r["determine_truth_by_core"] is False; s.close()
def test_suite_product_case_and_pass_report(tmp_path):
    db,s=session(tmp_path); c=suite(s); p=product(s,c); k=case(s,c); rr=run(s,c,p); svc.record_case_result(s,{"run_id":rr["id"],"case_id":k["id"],"status":"pass","observed_behavior":"200 + expected object version","evidence_refs":["evidence:http"],"executed_by":"test:conformance-harness","visibility":"public"}); rep=svc.run_report(s,rr["id"],True); assert rep["declared_conformance"] is True and rep["missing_required_case_ids"]==[] and rep["conformance_is_runtime_contract_evidence_not_scientific_or_quality_certification"] is True; s.close()
def test_missing_or_failed_required_case_is_not_conformant(tmp_path):
    db,s=session(tmp_path); c=suite(s); p=product(s,c); k=case(s,c); rr=run(s,c,p); rep=svc.run_report(s,rr["id"]); assert rep["declared_conformance"] is False and k["id"] in rep["missing_required_case_ids"]; svc.record_case_result(s,{"run_id":rr["id"],"case_id":k["id"],"status":"fail","executed_by":"tester"}); rep=svc.run_report(s,rr["id"]); assert rep["declared_conformance"] is False and k["id"] in rep["nonpassing_required_case_ids"]; s.close()
def test_exchange_trace_reproduction_evidence_and_findings(tmp_path):
    db,s=session(tmp_path); c=suite(s); p=product(s,c); rr=run(s,c,p); x=svc.record_exchange_check(s,{"run_id":rr["id"],"source_product_ref":"product:library","target_product_ref":"product:workspace","exchange_ref":"exchange:1","object_refs":["finding:1"],"status":"pass","evidence_refs":["hash:1"],"visibility":"public"}); t=svc.record_trace_check(s,{"run_id":rr["id"],"object_ref":"finding:1","expected_refs":["source:1"],"observed_refs":["source:1"],"status":"pass","visibility":"public"}); q=svc.record_reproduction_check(s,{"run_id":rr["id"],"project_ref":"project:1","state_version_ref":"state:v2","reconstruction_plan_ref":"reconstruct:1","status":"pass","visibility":"public"}); e=svc.add_evidence(s,{"evidence_key":"http-log","run_id":rr["id"],"evidence_type":"http_trace","evidence_ref":"artifact:trace","content_hash":"abc","captured_by":"tester","visibility":"public"}); f=svc.add_finding(s,{"finding_key":"f1","run_id":rr["id"],"category":"contract","statement":"Declared runtime exchange preserved version reference","evidence_refs":[e["id"]],"visibility":"public"}); assert x["status"]==t["status"]==q["status"]=="pass" and f["category"]=="contract"; s.close()
def test_revision_snapshot_chain_and_public_redaction(tmp_path):
    db,s=session(tmp_path); c=suite(s); svc.revise(s,{"suite_id":c["id"],"prior_state":{"v":1},"revised_state":{"v":2}}); a=svc.snapshot(s,{"suite_id":c["id"]}); b=svc.snapshot(s,{"suite_id":c["id"]}); pub=svc.suite_bundle(s,c["id"],True); assert b["previous_snapshot_hash"]==a["content_hash"] and pub["revisions"]==[] and pub["snapshots"]==[]; s.close()
def test_guardrails(tmp_path):
    db,s=session(tmp_path)
    try: svc.create_suite(s,{"suite_key":"bad","title":"bad","certify_scientific_validity_by_core":True}); assert False
    except ValueError: pass
    s.close()
