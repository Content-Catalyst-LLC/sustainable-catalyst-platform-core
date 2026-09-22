from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import analytical_runtime_provider as provider_svc
from app.services import analytical_result_provenance as result_svc
from app.services import statistical_reasoning as svc

def session(tmp_path):
    db=Database("sqlite:///"+str(tmp_path/"v330.db")); run_migrations(db); return db,db.session_factory()

def result(s):
    req=provider_svc.create_request(s,{"request_key":"analysis:policy-regression-001","provider_ref":"catalystanalyticsr","analysis_type":"econometrics","method_ref":"fit_policy_regression","input_refs":["dataset:policy"],"visibility":"public"})
    return result_svc.ingest_result(s,{"schema_version":"1.0.0","result_type":"catalyst_analytics_r_core_result","core_contract":"sc.core.analytical-runtime-provider.v1","request_ref":req["id"],"result_ref":"result:policy-regression-001","provider_ref":"catalystanalyticsr","provider_version":"2.2.0","runtime":"r","execution_host":"workspace","analysis_type":"econometrics","method_ref":"fit_policy_regression","external_execution_ref":"workspace-run:391","workspace_receipt_ref":"workspace-receipt:391","status":"completed","output_refs":[],"estimate_refs":[],"uncertainty_refs":[],"diagnostic_refs":[],"artifact_refs":[],"warnings":[],"errors":[],"provenance":{"package":{"name":"catalystanalyticsr","version":"2.2.0"}},"visibility":"public","boundary":{"core_records_result_but_does_not_execute":True,"workspace_execution_required":True,"result_does_not_certify_scientific_validity":True,"human_review_required":True}})

def evidence():
    return {"schema_version":"1.0.0","bundle_type":"statistical_validation_evidence","contract":"sc.analytics-r.statistical-diagnostics-validation.v1","id":"diagnostics:policy-regression-001","analysis_ref":"analysis:policy-regression-001","model_ref":"model:policy-regression-001","diagnostics":[{"record_type":"statistical_diagnostic","id":"diagnostic:bp","diagnostic_type":"assumption_test","name":"Breusch-Pagan statistic","observed":4.1,"p_value":0.129,"method_ref":"breusch_pagan","evidence_refs":[],"notes":[],"boundary":{"p_value_is_evidence_not_validity":True,"threshold_does_not_certify_model":True,"human_interpretation_required":True}}],"assumptions":[{"record_type":"statistical_assumption","id":"assumption:parallel-trends","label":"Parallel trends","statement":"Untreated potential outcomes would have followed comparable trends.","status":"not_assessed","evidence_refs":[],"limitations":["Requires design-specific review."],"boundary":{"status_is_evidence_state_not_certification":True,"human_review_required":True}}],"robustness":[{"record_type":"robustness_evidence","id":"robustness:spec-1","method_ref":"alternative_specification","target_ref":"model:policy-regression-001","result":{"estimate":0.9},"evidence_refs":[],"limitations":[],"boundary":{"robustness_does_not_establish_truth":True,"human_review_required":True}}],"comparisons":[{"record_type":"model_comparison_evidence","id":"comparison:models-1","model_refs":["model:a","model:b"],"criteria":{"aic":{"model:a":100,"model:b":103}},"evidence_refs":[],"notes":[],"boundary":{"no_automatic_winner":True,"criteria_require_context":True,"human_review_required":True}}],"source_status":"recorded","limitations":["Evidence only."],"review_status":"unreviewed","summary":{"diagnostic_count":1,"assumption_count":1,"robustness_count":1,"comparison_count":1},"provenance":{"package":{"name":"catalystanalyticsr","version":"2.2.0"}},"boundary":{"evidence_only":True,"no_automatic_scientific_validity_certification":True,"no_automatic_significance_conclusion":True,"no_automatic_model_selection":True,"human_review_required":True}}

def test_migration_provider_and_readiness(tmp_path):
    db,s=session(tmp_path); st=migration_status(db); r=svc.readiness(s)
    assert "0105" in st["applied"] and st["pending"]==[]
    assert r["release"]=="3.3.0" and r["contract"]=="sc.core.statistical-reasoning-object-model.v1"
    assert r["catalyst_analytics_r_version"]=="2.2.0" and r["workspace_adapter_release"]=="3.9.1"
    assert r["infer_statistical_significance_by_core"] is False and r["select_preferred_model_by_core"] is False
    s.close()

def test_ingest_analytics_r_validation_bundle(tmp_path):
    db,s=session(tmp_path); result(s)
    x=svc.ingest_validation_bundle(s,{"result_ref":"result:policy-regression-001","evidence":evidence(),"visibility":"public"})
    assert x["idempotent_replay"] is False
    replay=svc.ingest_validation_bundle(s,{"result_ref":"result:policy-regression-001","evidence":evidence(),"visibility":"public"})
    assert replay["idempotent_replay"] is True
    b=svc.reasoning_bundle(s,x["reasoning"]["reasoning_ref"],True)
    assert len(b["diagnostics"])==1 and len(b["assumptions"])==1 and len(b["robustness_evidence"])==1 and len(b["model_comparisons"])==1 and len(b["snapshots"])==1
    assert b["diagnostics"][0]["p_value"]==0.129 and b["core_infers_statistical_significance"] is False
    s.close()

def test_coefficients_intervals_and_human_interpretation(tmp_path):
    db,s=session(tmp_path); result(s); x=svc.ingest_validation_bundle(s,{"result_ref":"result:policy-regression-001","evidence":evidence(),"visibility":"public"}); ref=x["reasoning"]["reasoning_ref"]
    i=svc.record_interval(s,ref,{"interval_ref":"interval:beta-policy","interval_type":"confidence_interval","level":0.95,"lower":0.1,"upper":0.8,"target_ref":"coefficient:policy","visibility":"public"})
    c=svc.record_coefficient(s,ref,{"coefficient_ref":"coefficient:policy","term":"policy","estimate":0.45,"standard_error":0.18,"statistic":2.5,"p_value":0.02,"interval_ref":i["interval_ref"],"visibility":"public"})
    interp=svc.record_interpretation(s,ref,{"interpretation_ref":"interpretation:researcher-1","statement":"The estimate is positive in this specification; causal interpretation requires design review.","author_ref":"researcher:tariq","evidence_refs":[c["coefficient_ref"],i["interval_ref"]],"human_authored":True,"visibility":"public"})
    snap=svc.create_snapshot(s,ref,{"visibility":"public"}); s.commit(); b=svc.reasoning_bundle(s,ref,True)
    assert c["p_value"]==0.02 and interp["human_authored"] is True and len(b["coefficients"])==1 and len(b["intervals"])==1 and len(b["interpretations"])==1 and len(b["snapshots"])==2
    s.close()

def test_rejects_invalid_boundaries_and_automatic_interpretation(tmp_path):
    db,s=session(tmp_path); result(s)
    bad=evidence(); bad["boundary"]["no_automatic_significance_conclusion"]=False
    try: svc.ingest_validation_bundle(s,{"result_ref":"result:policy-regression-001","evidence":bad}); assert False
    except ValueError: pass
    x=svc.ingest_validation_bundle(s,{"result_ref":"result:policy-regression-001","evidence":evidence()}); ref=x["reasoning"]["reasoning_ref"]
    try: svc.record_interpretation(s,ref,{"interpretation_ref":"auto","statement":"auto","author_ref":"system","human_authored":False}); assert False
    except ValueError: pass
    try: svc.record_coefficient(s,ref,{"coefficient_ref":"bad","term":"x","p_value":1.5}); assert False
    except ValueError: pass
    s.close()

def test_core_does_not_turn_p_values_or_comparisons_into_verdicts(tmp_path):
    db,s=session(tmp_path); result(s); x=svc.ingest_validation_bundle(s,{"result_ref":"result:policy-regression-001","evidence":evidence()}); b=svc.reasoning_bundle(s,x["reasoning"]["reasoning_ref"])
    assert b["evidence_only"] is True and b["core_certifies_scientific_validity"] is False and b["core_infers_statistical_significance"] is False and b["core_selects_preferred_model"] is False
    assert "winner" not in b["model_comparisons"][0]
    s.close()
