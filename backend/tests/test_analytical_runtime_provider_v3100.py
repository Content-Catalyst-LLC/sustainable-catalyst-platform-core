from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import analytical_runtime_provider as svc

def session(tmp_path):
    db=Database("sqlite:///"+str(tmp_path/"v310.db")); run_migrations(db); return db,db.session_factory()

def test_migration_and_seeded_r_provider(tmp_path):
    db,s=session(tmp_path); st=migration_status(db); r=svc.readiness(s)
    assert "0103" in st["applied"] and st["pending"]==[]
    assert r["release"]=="3.2.0" and r["catalyst_analytics_r_registered"] is True
    assert r["catalyst_analytics_r_version"]=="2.1.0" and r["workspace_is_execution_host"] is True
    assert r["execute_r_by_core"] is False and r["determine_truth_by_core"] is False
    b=svc.provider_bundle(s,"catalystanalyticsr",True)
    assert b["provider"]["runtime"]=="r" and b["execution_host"]=="workspace" and len(b["capabilities"])>=12
    s.close()

def test_request_result_provenance_roundtrip(tmp_path):
    db,s=session(tmp_path)
    req=svc.create_request(s,{"request_key":"analysis-1","provider_ref":"catalystanalyticsr","analysis_type":"uncertainty_analysis","input_refs":["dataset:1"],"parameters":{"samples":1000},"reproducibility":{"seed":42},"visibility":"public"})
    assert req["runtime"]=="r" and req["execution_host"]=="workspace" and req["status"]=="declared"
    env=svc.record_environment(s,{"provider_ref":"catalystanalyticsr","environment_ref":"env:r:1","runtime":"r","runtime_version":"4.x","package_manifest":{"catalystanalyticsr":"2.1.0"},"visibility":"public"})
    svc.record_diagnostic(s,{"request_ref":req["id"],"diagnostic_ref":"diag:1","diagnostic_type":"convergence","metrics":{"ok":True},"visibility":"public"})
    svc.record_artifact(s,{"request_ref":req["id"],"artifact_ref":"artifact:1","artifact_type":"json","content_hash":"abc","visibility":"public"})
    svc.record_reproduction(s,{"request_ref":req["id"],"reproduction_ref":"repro:1","environment_ref":env["environment_ref"],"code_ref":"script:1","random_seed":42,"input_snapshot_refs":["snapshot:1"],"visibility":"public"})
    svc.record_result(s,{"request_ref":req["id"],"result_ref":"result:1","environment_ref":env["environment_ref"],"output_refs":["object:result:1"],"diagnostic_refs":["diag:1"],"artifact_refs":["artifact:1"],"visibility":"public"})
    b=svc.request_bundle(s,req["id"],True)
    assert len(b["results"])==1 and len(b["diagnostics"])==1 and len(b["artifacts"])==1 and len(b["reproduction_references"])==1
    assert b["execution_occurs_outside_core"] is True
    s.close()

def test_provider_capability_guard_and_runtime_boundary(tmp_path):
    db,s=session(tmp_path)
    try:
        svc.create_request(s,{"request_key":"bad-cap","provider_ref":"catalystanalyticsr","analysis_type":"not_declared","input_refs":[]})
        assert False
    except ValueError: pass
    try:
        svc.create_request(s,{"request_key":"bad-runtime","provider_ref":"catalystanalyticsr","analysis_type":"forecasting","runtime":"python","input_refs":[]})
        assert False
    except ValueError: pass
    try:
        svc.create_request(s,{"request_key":"bad-boundary","provider_ref":"catalystanalyticsr","analysis_type":"forecasting","input_refs":[],"execute_r_by_core":True})
        assert False
    except ValueError: pass
    s.close()
