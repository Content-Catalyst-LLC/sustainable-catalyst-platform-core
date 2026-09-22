from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import analytical_runtime_provider as provider_svc
from app.services import analytical_result_provenance as svc
from app.models import AnalyticalRuntimeProviderRecord
from sqlalchemy import select

def session(tmp_path):
    db=Database("sqlite:///"+str(tmp_path/"v320.db")); run_migrations(db); return db,db.session_factory()

def request(s,key="analysis-1",visibility="public"):
    return provider_svc.create_request(s,{"request_key":key,"provider_ref":"catalystanalyticsr","analysis_type":"uncertainty_analysis","method_ref":"run_uncertainty","input_refs":["dataset:1"],"reproducibility":{"seed":42},"visibility":visibility})

def envelope(key="analysis-1",result_ref="result:1",visibility="public"):
    return {"schema_version":"1.0.0","result_type":"catalyst_analytics_r_core_result","core_contract":"sc.core.analytical-runtime-provider.v1","request_ref":key,"result_ref":result_ref,"provider_ref":"catalystanalyticsr","provider_version":"2.1.0","runtime":"r","execution_host":"workspace","analysis_type":"uncertainty_analysis","method_ref":"run_uncertainty","external_execution_ref":"workspace-run:1","workspace_receipt_ref":"workspace-receipt:1","environment_ref":"env:r:1","status":"completed","output_refs":["object:1"],"estimate_refs":["estimate:1"],"uncertainty_refs":["uncertainty:1"],"diagnostic_refs":["diag:1"],"artifact_refs":["artifact:1"],"warnings":[],"errors":[],"native_result":{"summary":"provider-native summary"},"provenance":{"package":{"name":"catalystanalyticsr","version":"2.1.0"}},"completed_at":"2026-09-22T04:00:00Z","visibility":visibility,"boundary":{"core_records_result_but_does_not_execute":True,"workspace_execution_required":True,"result_does_not_certify_scientific_validity":True,"human_review_required":True}}

def test_migration_seed_and_provider_promotion(tmp_path):
    db,s=session(tmp_path); st=migration_status(db); r=svc.readiness(s)
    assert "0104" in st["applied"] and st["pending"]==[]
    assert r["release"]=="3.2.0" and r["contract"]=="sc.core.analytical-result-provenance.v1"
    assert r["catalyst_analytics_r_version"]=="2.1.0" and r["workspace_adapter_release"]=="3.5.0"
    provider=s.scalar(select(AnalyticalRuntimeProviderRecord).where(AnalyticalRuntimeProviderRecord.provider_key=="catalystanalyticsr"))
    assert provider.provider_version=="2.1.0" and provider.metadata_json["core_release"]=="3.2.0"
    s.close()

def test_ingest_idempotent_and_lineage_snapshot(tmp_path):
    db,s=session(tmp_path); req=request(s)
    provider_svc.record_environment(s,{"provider_ref":"catalystanalyticsr","environment_ref":"env:r:1","runtime":"r","package_manifest":{"catalystanalyticsr":"2.1.0"},"visibility":"public"})
    provider_svc.record_artifact(s,{"request_ref":req["id"],"artifact_ref":"artifact:1","artifact_type":"json","visibility":"public"})
    provider_svc.record_diagnostic(s,{"request_ref":req["id"],"diagnostic_ref":"diag:1","diagnostic_type":"runtime","visibility":"public"})
    provider_svc.record_reproduction(s,{"request_ref":req["id"],"reproduction_ref":"repro:1","environment_ref":"env:r:1","random_seed":42,"visibility":"public"})
    first=svc.ingest_result(s,envelope()); assert first["idempotent_replay"] is False and len(first["result_fingerprint"])==64
    replay=svc.ingest_result(s,envelope()); assert replay["idempotent_replay"] is True
    b=svc.result_bundle(s,"result:1",True)
    kinds={x["binding_type"] for x in b["lineage"]}
    assert {"request_input","provider","environment","workspace_receipt","external_execution","result_output","estimate","uncertainty","diagnostic","artifact","reproduction"}.issubset(kinds)
    assert len(b["snapshots"])==1 and len(b["ingestion_receipts"])==1 and len(b["artifacts"])==1 and len(b["diagnostics"])==1
    assert b["result"]["provenance_hash"] and b["result"]["result_fingerprint"]
    s.close()

def test_first_class_estimate_uncertainty_and_explicit_lineage(tmp_path):
    db,s=session(tmp_path); request(s); svc.ingest_result(s,envelope())
    u=svc.record_uncertainty(s,"result:1",{"uncertainty_ref":"uncertainty:1","uncertainty_type":"confidence_interval","level":0.95,"summary":{"lower":0.5,"upper":1.5},"visibility":"public"})
    e=svc.record_estimate(s,"result:1",{"estimate_ref":"estimate:1","estimate_type":"point_estimate","name":"effect","value":{"value":1.0},"unit":"index","uncertainty_ref":"uncertainty:1","visibility":"public"})
    svc.record_lineage(s,"result:1",{"binding_type":"derived_from","source_ref":"dataset:derived","target_ref":"result:1","content_hash":"abc","visibility":"public"})
    snap=svc.create_snapshot(s,"result:1",{"visibility":"public"}); s.commit()
    b=svc.result_bundle(s,"result:1",True)
    assert u["level"]==0.95 and e["uncertainty_ref"]=="uncertainty:1" and len(b["estimates"])==1 and len(b["uncertainty_objects"])==1
    assert len(b["snapshots"])==2 and any(x["binding_type"]=="derived_from" for x in b["lineage"])
    assert b["snapshots"][-1]["previous_snapshot_hash"]==b["snapshots"][0]["snapshot_hash"]
    s.close()

def test_rejects_boundary_provider_and_mutating_replay(tmp_path):
    db,s=session(tmp_path); request(s)
    bad=envelope(); bad["boundary"]["core_records_result_but_does_not_execute"]=False
    try: svc.ingest_result(s,bad); assert False
    except ValueError: pass
    bad=envelope(); bad["provider_version"]="2.0.1"
    try: svc.ingest_result(s,bad); assert False
    except ValueError: pass
    good=envelope(); svc.ingest_result(s,good); changed=envelope(); changed["warnings"]=["changed"]
    try: svc.ingest_result(s,changed); assert False
    except ValueError: pass
    s.close()

def test_declared_reference_guards_and_core_boundaries(tmp_path):
    db,s=session(tmp_path); request(s); svc.ingest_result(s,envelope())
    try: svc.record_estimate(s,"result:1",{"estimate_ref":"estimate:other","estimate_type":"point_estimate"}); assert False
    except ValueError: pass
    try: svc.record_uncertainty(s,"result:1",{"uncertainty_ref":"uncertainty:other","uncertainty_type":"interval"}); assert False
    except ValueError: pass
    try: svc.record_lineage(s,"result:1",{"binding_type":"truth","source_ref":"a","target_ref":"b"}); assert False
    except ValueError: pass
    r=svc.readiness(s)
    assert r["execute_r_by_core"] is False and r["certify_scientific_validity_by_core"] is False and r["determine_truth_by_core"] is False
    s.close()
