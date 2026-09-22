#!/usr/bin/env python3
from pathlib import Path
import tempfile
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import analytical_runtime_provider as provider_svc
from app.services import analytical_result_provenance as result_svc
from app.services import statistical_reasoning as svc

with tempfile.TemporaryDirectory() as td:
    db=Database("sqlite:///"+str(Path(td)/"v330.db")); run_migrations(db); s=db.session_factory()
    st=migration_status(db); assert "0105" in st["applied"] and st["pending"]==[],st
    ready=svc.readiness(s); assert ready["release"]=="3.3.0" and ready["catalyst_analytics_r_version"]=="2.2.0" and ready["workspace_adapter_release"]=="3.9.1",ready
    req=provider_svc.create_request(s,{"request_key":"validate-v330","provider_ref":"catalystanalyticsr","analysis_type":"model_validation","method_ref":"validate_model_fit","input_refs":["dataset:validation"],"visibility":"public"})
    result_svc.ingest_result(s,{"schema_version":"1.0.0","result_type":"catalyst_analytics_r_core_result","core_contract":"sc.core.analytical-runtime-provider.v1","request_ref":req["id"],"result_ref":"result:validate-v330","provider_ref":"catalystanalyticsr","provider_version":"2.2.0","runtime":"r","execution_host":"workspace","analysis_type":"model_validation","method_ref":"validate_model_fit","status":"completed","output_refs":[],"estimate_refs":[],"uncertainty_refs":[],"diagnostic_refs":[],"artifact_refs":[],"provenance":{"package":{"name":"catalystanalyticsr","version":"2.2.0"}},"visibility":"public","boundary":{"core_records_result_but_does_not_execute":True,"workspace_execution_required":True,"result_does_not_certify_scientific_validity":True,"human_review_required":True}})
    ev={"schema_version":"1.0.0","bundle_type":"statistical_validation_evidence","contract":"sc.analytics-r.statistical-diagnostics-validation.v1","id":"diagnostics:validate-v330","analysis_ref":"analysis:validate-v330","diagnostics":[],"assumptions":[],"robustness":[],"comparisons":[],"review_status":"unreviewed","summary":{},"provenance":{"package":{"name":"catalystanalyticsr","version":"2.2.0"}},"boundary":{"evidence_only":True,"no_automatic_scientific_validity_certification":True,"no_automatic_significance_conclusion":True,"no_automatic_model_selection":True,"human_review_required":True}}
    x=svc.ingest_validation_bundle(s,{"result_ref":"result:validate-v330","evidence":ev,"visibility":"public"}); b=svc.reasoning_bundle(s,x["reasoning"]["reasoning_ref"],True)
    assert b["core_certifies_scientific_validity"] is False and b["core_infers_statistical_significance"] is False and len(b["snapshots"])==1,b
    s.close()
print("PASS - Platform Core v3.3.0 Statistical Reasoning Object Model")
