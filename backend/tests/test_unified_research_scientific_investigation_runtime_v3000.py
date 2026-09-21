from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import unified_research_scientific_runtime as svc
def session(tmp_path):
 db=Database("sqlite:///"+str(tmp_path/"v300.db")); run_migrations(db); return db,db.session_factory()
def root(s,visibility="public"):
 return svc.create_session(s,{"session_key":"project-1-runtime","title":"Unified project runtime","project_ref":"project:1","workflow_ref":"workflow:1","project_state_ref":"state:v3","visibility":visibility})
def test_readiness_and_migration(tmp_path):
 db,s=session(tmp_path); r=svc.readiness(s); st=migration_status(db); assert r["release"]=="3.0.0" and "0102" in st["applied"] and st["pending"]==[]; assert r["reference_first_runtime_by_core"] is True and r["execute_scientific_work_by_core"] is False and r["determine_truth_by_core"] is False; s.close()
def test_cross_layer_bindings(tmp_path):
 db,s=session(tmp_path); x=root(s); sid=x["id"]; svc.add_object_binding(s,{"session_id":sid,"object_type":"finding","object_ref":"finding:1","version_ref":"finding:v2","content_hash":"abc","visibility":"public"}); svc.add_product_binding(s,{"session_id":sid,"product_ref":"product:workspace","product_version":"3.0","declared_capabilities":["object:read"],"visibility":"public"}); svc.add_execution_binding(s,{"session_id":sid,"execution_ref":"execution:python:1","runtime":"python","environment_ref":"env:1","input_refs":["dataset:1"],"output_refs":["result:1"],"visibility":"public"}); b=svc.bundle(s,sid,True); assert len(b["object_bindings"])==1 and len(b["product_bindings"])==1 and len(b["execution_bindings"])==1 and b["underlying_objects_remain_authoritative"] is True; s.close()
def test_investigation_visual_validation_package_handoff(tmp_path):
 db,s=session(tmp_path); x=root(s); sid=x["id"]; svc.add_investigation_binding(s,{"session_id":sid,"investigation_ref":"investigation:1","investigation_type":"forensic","evidence_refs":["evidence:1"],"visibility":"public"}); svc.add_visual_binding(s,{"session_id":sid,"visual_ref":"visual:1","visual_type":"scene","source_refs":["evidence:1"],"visibility":"public"}); svc.add_validation_binding(s,{"session_id":sid,"validation_ref":"challenge:1","validation_type":"replication","target_refs":["finding:1"],"visibility":"public"}); svc.add_package_binding(s,{"session_id":sid,"package_ref":"package:1","package_type":"scholarly","content_hash":"def","visibility":"public"}); svc.add_handoff_binding(s,{"session_id":sid,"handoff_ref":"handoff:1","source_product_ref":"product:library","target_product_ref":"product:lab","visibility":"public"}); b=svc.bundle(s,sid,True); assert all(len(b[k])==1 for k in ("investigation_bindings","visual_bindings","validation_bindings","package_bindings","handoff_bindings")); s.close()
def test_summary_and_declared_lineage(tmp_path):
 db,s=session(tmp_path); x=root(s); sid=x["id"]; svc.add_object_binding(s,{"session_id":sid,"object_type":"dataset","object_ref":"dataset:1","visibility":"public"}); svc.add_execution_binding(s,{"session_id":sid,"execution_ref":"execution:1","visibility":"public"}); q=svc.summary(s,sid,True); lin=svc.lineage(s,sid,True); assert q["counts"]["object_bindings"]==1 and q["core_executes_specialist_work"] is False; assert len(lin["edges"])==2 and lin["lineage_is_declared_not_inferred"] is True; s.close()
def test_milestone_revision_snapshot_chain(tmp_path):
 db,s=session(tmp_path); x=root(s); sid=x["id"]; svc.add_milestone(s,{"session_id":sid,"milestone_key":"analysis-complete","milestone_type":"declared","state_ref":"state:v3"}); svc.revise(s,{"session_id":sid,"prior_state":{"v":1},"revised_state":{"v":2}}); a=svc.snapshot(s,{"session_id":sid}); b=svc.snapshot(s,{"session_id":sid}); assert b["previous_snapshot_hash"]==a["content_hash"]; s.close()
def test_public_redaction(tmp_path):
 db,s=session(tmp_path); x=root(s); sid=x["id"]; svc.revise(s,{"session_id":sid,"prior_state":{},"revised_state":{"x":1}}); svc.snapshot(s,{"session_id":sid}); b=svc.bundle(s,sid,True); assert b["revisions"]==[] and b["snapshots"]==[]; s.close()
def test_guardrails(tmp_path):
 db,s=session(tmp_path)
 try: svc.create_session(s,{"session_key":"bad","title":"bad","project_ref":"p","execute_code_by_core":True}); assert False
 except ValueError: pass
 s.close()
