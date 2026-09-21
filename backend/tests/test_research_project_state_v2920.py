from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_project_state as svc

def session(tmp_path):
 db=Database("sqlite:///"+str(tmp_path/"state.db")); run_migrations(db); return db,db.session_factory()
def state(s,key="s",visibility="public"):
 return svc.create_state(s,{"state_key":"state-"+key,"project_ref":"project:1","title":"Research project state","visibility":visibility})["id"]
def test_readiness_and_boundaries(tmp_path):
 db,s=session(tmp_path); d=svc.readiness(s); assert d["release"]=="2.92.0" and "0096" in migration_status(db)["applied"] and migration_status(db)["pending"]==[]; assert d["immutable_version_registry_by_core"] is True and d["replay_executions_by_core"] is False and d["determine_truth_by_core"] is False; s.close()
def test_version_freeze_and_historical_manifest(tmp_path):
 db,s=session(tmp_path); i=state(s,"history"); v=svc.create_version(s,i,{"label":"analysis state"}); assert v["version"]==1
 svc.add_binding(s,i,1,{"binding_key":"dataset","product_key":"catalyst_data","object_type":"dataset","object_ref":"dataset:42","object_version_ref":"v3","content_hash":"a"*64,"visibility":"public"})
 svc.add_binding(s,i,1,{"binding_key":"analysis","product_key":"workbench","object_type":"execution","object_ref":"execution:7","object_version_ref":"run-7","visibility":"public"})
 svc.add_dependency(s,i,1,{"dependency_key":"dataset-analysis","from_binding_key":"dataset","to_binding_key":"analysis","relation":"input_to"})
 svc.add_environment(s,i,1,{"environment_key":"python","environment_type":"python","environment_ref":"python:3.12","version_ref":"3.12.12","content_hash":"b"*64,"visibility":"public"})
 f=svc.freeze_version(s,i,1,{}); assert f["status"]=="frozen" and len(f["content_hash"])==64
 m=svc.historical_manifest(s,i,1); assert len(m["bindings"])==2 and m["dependencies"][0]["relation"]=="input_to" and m["manifest_is_reference_first_not_restored_execution"] is True
 try: svc.add_binding(s,i,1,{"binding_key":"late","product_key":"library","object_type":"source","object_ref":"source:late"}); assert False
 except ValueError: pass
 s.close()
def test_version_hash_chain_checkpoint_and_reconstruction(tmp_path):
 db,s=session(tmp_path); i=state(s,"reconstruct")
 for n in (1,2):
  svc.create_version(s,i,{"version":n}); svc.add_binding(s,i,n,{"binding_key":"source","product_key":"library","object_type":"source","object_ref":f"source:{n}","visibility":"public"}); svc.add_environment(s,i,n,{"environment_key":"container","environment_type":"container","environment_ref":f"image:{n}","visibility":"public"}); out=svc.freeze_version(s,i,n,{})
 if n==2: assert out["previous_version_hash"] is not None
 cp=svc.add_checkpoint(s,i,{"checkpoint_key":"publication","version":2,"checkpoint_type":"publication","title":"Submitted manuscript"}); assert cp["checkpoint_type"]=="publication"
 plan=svc.create_reconstruction_plan(s,i,{"plan_key":"rebuild-v2","version":2,"steps":[{"action":"resolve references"}]}); assert plan["declared_requirements_complete"] is True and plan["plan_does_not_execute_reconstruction"] is True
 ver=svc.add_verification(s,i,"rebuild-v2",{"verification_key":"external-1","status":"passed","verifier_ref":"replication-team","checks":[{"check":"hashes","status":"passed"}]}); assert ver["verification_is_attributed_evidence_not_core_certification"] is True
 s.close()
def test_revision_snapshot_guardrails(tmp_path):
 db,s=session(tmp_path); i=state(s,"rev",visibility="internal"); r=svc.revise_state(s,i,{"title":"Updated project state","change_summary":"metadata update"}); assert r["revision"]==1; a=svc.snapshot(s,i,{}); b=svc.snapshot(s,i,{}); assert b["previous_snapshot_hash"]==a["content_hash"]
 try: svc.revise_state(s,i,{"infer_reproducibility_by_core":True}); assert False
 except ValueError: pass
 try: svc.bundle(s,i,True); assert False
 except ValueError: pass
 s.close()
def test_public_redaction_and_lineage(tmp_path):
 db,s=session(tmp_path); i=state(s,"public"); svc.create_version(s,i,{"version":1}); svc.add_binding(s,i,1,{"binding_key":"public-source","product_key":"library","object_type":"source","object_ref":"source:1","visibility":"public"}); svc.add_binding(s,i,1,{"binding_key":"private-data","product_key":"catalyst_data","object_type":"dataset","object_ref":"dataset:secret","visibility":"internal"}); svc.add_environment(s,i,1,{"environment_key":"public-env","environment_type":"software","environment_ref":"tool:1","visibility":"public"}); svc.add_environment(s,i,1,{"environment_key":"private-env","environment_type":"database","environment_ref":"db:secret","visibility":"internal"}); svc.freeze_version(s,i,1,{})
 b=svc.bundle(s,i,True); m=b["historical_manifests"][0]; assert [x["binding_key"] for x in m["bindings"]]==["public-source"] and [x["environment_key"] for x in m["environments"]]==["public-env"] and b["reconstruction_plans"]==[]
 l=svc.lineage(s,i,True); assert l["lineage_is_declared_not_inferred"] is True and any(x["relation"]=="has_frozen_version" for x in l["edges"]); s.close()
