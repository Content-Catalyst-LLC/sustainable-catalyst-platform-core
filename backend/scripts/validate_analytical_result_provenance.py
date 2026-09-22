#!/usr/bin/env python3
from pathlib import Path
import tempfile
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import analytical_runtime_provider as provider_svc
from app.services import analytical_result_provenance as result_svc

with tempfile.TemporaryDirectory() as td:
    db=Database("sqlite:///"+str(Path(td)/"v320.db")); run_migrations(db); s=db.session_factory()
    st=migration_status(db); assert "0104" in st["applied"] and st["pending"]==[],st
    ready=result_svc.readiness(s); assert ready["release"]=="3.2.0" and ready["catalyst_analytics_r_version"]=="2.1.0",ready
    req=provider_svc.create_request(s,{"request_key":"validate-v320","provider_ref":"catalystanalyticsr","analysis_type":"uncertainty_analysis","method_ref":"run_uncertainty","input_refs":["dataset:validation"],"reproducibility":{"seed":42},"visibility":"public"})
    provider_svc.record_environment(s,{"provider_ref":"catalystanalyticsr","environment_ref":"env:workspace-r:validation","runtime":"r","runtime_version":"4.x","package_manifest":{"catalystanalyticsr":"2.1.0"},"visibility":"public"})
    provider_svc.record_reproduction(s,{"request_ref":req["id"],"reproduction_ref":"repro:validation","environment_ref":"env:workspace-r:validation","random_seed":42,"input_snapshot_refs":["snapshot:dataset:validation"],"visibility":"public"})
    env={"schema_version":"1.0.0","result_type":"catalyst_analytics_r_core_result","core_contract":"sc.core.analytical-runtime-provider.v1","request_ref":"validate-v320","result_ref":"result:validate-v320","provider_ref":"catalystanalyticsr","provider_version":"2.1.0","runtime":"r","execution_host":"workspace","analysis_type":"uncertainty_analysis","method_ref":"run_uncertainty","external_execution_ref":"workspace-run:validation","workspace_receipt_ref":"workspace-receipt:validation","environment_ref":"env:workspace-r:validation","status":"completed","output_refs":["object:validation"],"estimate_refs":["estimate:validation"],"uncertainty_refs":["uncertainty:validation"],"diagnostic_refs":[],"artifact_refs":[],"warnings":[],"errors":[],"native_result":{"summary":"validation"},"provenance":{"package":{"name":"catalystanalyticsr","version":"2.1.0"}},"completed_at":"2026-09-22T04:00:00Z","visibility":"public","boundary":{"core_records_result_but_does_not_execute":True,"workspace_execution_required":True,"result_does_not_certify_scientific_validity":True,"human_review_required":True}}
    got=result_svc.ingest_result(s,env); assert got["result"]["provider_version"]=="2.1.0" and got["idempotent_replay"] is False,got
    replay=result_svc.ingest_result(s,env); assert replay["idempotent_replay"] is True,replay
    result_svc.record_uncertainty(s,"result:validate-v320",{"uncertainty_ref":"uncertainty:validation","uncertainty_type":"empirical_distribution","level":0.95,"summary":{"mean":1.2},"visibility":"public"})
    result_svc.record_estimate(s,"result:validate-v320",{"estimate_ref":"estimate:validation","estimate_type":"point_estimate","name":"mean","value":{"value":1.2},"uncertainty_ref":"uncertainty:validation","visibility":"public"})
    b=result_svc.result_bundle(s,"result:validate-v320",True); assert len(b["estimates"])==1 and len(b["uncertainty_objects"])==1 and len(b["lineage"])>=7 and len(b["snapshots"])>=1,b
    lin=result_svc.result_lineage(s,"result:validate-v320",True); assert lin["workspace_receipt_ref"]=="workspace-receipt:validation" and lin["result_fingerprint"],lin
    assert b["core_executes_analysis"] is False and b["human_review_required"] is True
    s.close()
print("PASS - Platform Core v3.2.0 Analytical Result & Provenance Integration")
