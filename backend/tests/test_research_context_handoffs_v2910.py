from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_context_handoffs as svc

def session(tmp_path):
 db=Database("sqlite:///"+str(tmp_path/"context.db")); run_migrations(db); return db,db.session_factory()
def context(s,key="c",visibility="public"):
 return svc.create_context(s,{"context_key":"context-"+key,"title":"Cross-product context","source_product":"workspace","visibility":visibility,"project_ref":"project:1","workflow_ref":"workflow:1","workflow_stage_ref":"analysis","protocol_ref":"protocol:1"})["id"]
def test_readiness_and_boundaries(tmp_path):
 db,s=session(tmp_path); d=svc.readiness(s); assert d["release"]=="2.91.0" and migration_status(db)["pending"]==[] and "0095" in migration_status(db)["applied"]; assert d["handoff_package_manifest_by_core"] is True and d["auto_route_handoff_by_core"] is False and d["determine_truth_by_core"] is False; s.close()
def test_context_bindings_and_contract_diagnostics(tmp_path):
 db,s=session(tmp_path); i=context(s,"diag")
 svc.add_object_binding(s,i,{"binding_key":"dataset","product_key":"catalyst_data","object_type":"dataset","object_ref":"dataset:42","role":"analysis_input","visibility":"public","version_ref":"v3"})
 svc.add_provenance_binding(s,i,{"provenance_key":"run","relation":"generated_by","activity_ref":"execution:7","agent_ref":"workbench"})
 svc.add_state_marker(s,i,{"state_key":"workflow-stage","namespace":"workflow","product_key":"core","visibility":"public","value":{"stage":"analysis"}})
 svc.add_protocol(s,i,{"handoff_key":"workspace-workbench","from_product":"workspace","to_product":"workbench","required_bindings":["dataset"],"required_state_keys":["workflow-stage"],"requested_capabilities":["python"]})
 d=svc.contract_diagnostics(s,i,"workspace-workbench"); assert d["declared_contract_complete"] is True and not d["missing_bindings"] and d["diagnostic_is_structural_not_scientific_judgment"] is True; s.close()
def test_package_integrity_acknowledgement(tmp_path):
 db,s=session(tmp_path); i=context(s,"pkg")
 svc.add_object_binding(s,i,{"binding_key":"evidence","product_key":"library","object_type":"evidence","object_ref":"evidence:9","visibility":"internal"})
 svc.add_protocol(s,i,{"handoff_key":"library-lab","from_product":"library","to_product":"research_lab","required_bindings":["evidence"],"transfer_mode":"manifest"})
 pkg=svc.create_package(s,i,{"handoff_key":"library-lab","package_key":"package-1","require_complete":True}); assert len(pkg["content_hash"])==64 and pkg["missing_requirements"]["missing_bindings"]==[]
 ack=svc.acknowledge_package(s,i,"package-1",{"ack_key":"ack-1","product_key":"research_lab","received_hash":pkg["content_hash"],"status":"accepted"}); assert ack["integrity_match"] is True
 ack2=svc.acknowledge_package(s,i,"package-1",{"ack_key":"ack-2","product_key":"research_lab","received_hash":"0"*64,"status":"needs_review"}); assert ack2["integrity_match"] is False; s.close()
def test_conflict_revision_snapshot_and_guardrails(tmp_path):
 db,s=session(tmp_path); i=context(s,"rev",visibility="internal")
 svc.add_conflict(s,i,{"conflict_key":"version","conflict_type":"version_mismatch","source_ref":"dataset:v2","target_ref":"dataset:v1","details":{"declared":True}})
 r=svc.revise_context(s,i,{"workflow_stage_ref":"challenge","change_summary":"Recorded workflow progression"}); assert r["revision"]==1
 a=svc.snapshot(s,i,{}); b=svc.snapshot(s,i,{}); assert b["previous_snapshot_hash"]==a["content_hash"]
 try: svc.revise_context(s,i,{"auto_route_handoff_by_core":True}); assert False
 except ValueError: pass
 try: svc.bundle(s,i,True); assert False
 except ValueError: pass
 s.close()
def test_public_bundle_redaction_and_lineage(tmp_path):
 db,s=session(tmp_path); i=context(s,"public")
 svc.add_object_binding(s,i,{"binding_key":"public-source","product_key":"library","object_type":"source","object_ref":"source:1","visibility":"public"})
 svc.add_object_binding(s,i,{"binding_key":"private-data","product_key":"catalyst_data","object_type":"dataset","object_ref":"dataset:secret","visibility":"internal"})
 svc.add_state_marker(s,i,{"state_key":"public-stage","namespace":"workflow","product_key":"core","visibility":"public","value":{"stage":"evidence"}})
 svc.add_protocol(s,i,{"handoff_key":"library-workspace","from_product":"library","to_product":"workspace"})
 p=svc.bundle(s,i,True); assert [x["binding_key"] for x in p["object_bindings"]]==["public-source"] and p["packages"]==[] and p["conflicts"]==[]
 l=svc.lineage(s,i,True); assert l["lineage_is_declared_not_inferred"] is True and any(x["relation"]=="declared_handoff_protocol" for x in l["edges"]); s.close()
