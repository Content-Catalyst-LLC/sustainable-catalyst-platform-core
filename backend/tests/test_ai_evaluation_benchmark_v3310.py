from copy import deepcopy
import pytest
from pydantic import ValidationError
from app.services.ai_evaluation_benchmark import *

def test_contract():
    d=contract_document(); assert d["release"]=="3.31.0"; assert d["contract"]==CONTRACT_VERSION
    assert d["boundaries"]["core_executes_evaluation"] is False
    assert d["boundaries"]["core_selects_best_model"] is False
def test_reference():
    b=reference_evaluation_bundle(); assert b.evaluation_run.status==EvaluationStatus.completed; assert b.comparison is not None
def test_benchmark_fingerprint(): 
    x=reference_evaluation_bundle().benchmark; assert x.fingerprint()==deepcopy(x).fingerprint()
def test_duplicate_dataset_bindings():
    d=EvaluationDatasetBinding(evaluation_dataset_binding_id="ds:x",dataset_version_ref="dataset-version:x")
    with pytest.raises(ValidationError): BenchmarkDefinition(benchmark_id="b:x",name="x",task="classification",benchmark_version="1",dataset_bindings=[d,deepcopy(d)])
def test_duplicate_metrics():
    m=EvaluationMetricDefinition(metric_id="m:x",name="x",task="classification",direction="maximize")
    with pytest.raises(ValidationError): BenchmarkDefinition(benchmark_id="b:x",name="x",task="classification",benchmark_version="1",metric_definitions=[m,deepcopy(m)])
def test_metric_hash():
    m=reference_evaluation_bundle().benchmark.metric_definitions[0]; assert m.fingerprint()==deepcopy(m).fingerprint()
def test_case_requires_source():
    with pytest.raises(ValidationError): EvaluationCase(evaluation_case_id="c:x",benchmark_ref="b:x")
def test_ci_len():
    with pytest.raises(ValidationError): EvaluationMetricResult(metric_ref="m:x",value=1.0,confidence_interval=[.9])
def test_ci_order():
    with pytest.raises(ValidationError): EvaluationMetricResult(metric_ref="m:x",value=1.0,confidence_interval=[1,.9])
def test_completed_requires_cases():
    r=reference_evaluation_bundle().evaluation_run.model_dump(mode="python"); r["case_results"]=[]
    with pytest.raises(ValidationError): EvaluationRun.model_validate(r)
def test_completed_requires_aggregates():
    r=reference_evaluation_bundle().evaluation_run.model_dump(mode="python"); r["aggregate_metric_results"]=[]
    with pytest.raises(ValidationError): EvaluationRun.model_validate(r)
def test_unknown_case():
    r=reference_evaluation_bundle().evaluation_run.model_dump(mode="python"); r["case_results"][0]["evaluation_case_ref"]="c:missing"
    with pytest.raises(ValidationError): EvaluationRun.model_validate(r)
def test_duplicate_aggregate_metric():
    r=reference_evaluation_bundle().evaluation_run.model_dump(mode="python"); r["aggregate_metric_results"]=[r["aggregate_metric_results"][0],deepcopy(r["aggregate_metric_results"][0])]
    with pytest.raises(ValidationError): EvaluationRun.model_validate(r)
def test_run_fingerprint_ignores_lifecycle():
    r=reference_evaluation_bundle().evaluation_run; x=deepcopy(r); x.status=EvaluationStatus.running; x.started_at=None; x.completed_at=None
    assert r.fingerprint()==x.fingerprint()
def test_model_version_identity():
    r=reference_evaluation_bundle().evaluation_run.model_dump(mode="python"); r["ai_model_version_ref"]="model-version:x"
    with pytest.raises(ValidationError): EvaluationRun.model_validate(r)
def test_comparison_unique_versions():
    e=ModelBenchmarkComparisonEntry(ai_model_version_ref="ai-model-version:x:1",benchmark_result_ref="br:x")
    with pytest.raises(ValidationError): ModelBenchmarkComparison(comparison_id="cmp:x",benchmark_ref="b:x",entries=[e,deepcopy(e)])
def test_comparison_fingerprint():
    c=reference_evaluation_bundle().comparison; assert c.fingerprint()==deepcopy(c).fingerprint()
def test_bundle_fingerprint():
    b=reference_evaluation_bundle(); assert b.fingerprint()==deepcopy(b).fingerprint(); assert len(b.fingerprint())==64
def test_inference_links():
    b=reference_evaluation_bundle(); assert all(x.inference_run_ref.startswith("inference-run:") for x in b.evaluation_run.case_results)
def test_job_environment_links():
    r=reference_evaluation_bundle().evaluation_run; assert r.computational_job_ref; assert r.runtime_environment_ref
def test_ground_truth():
    d=reference_evaluation_bundle().benchmark.dataset_bindings[0]; assert d.ground_truth_artifact_ref
def test_aggregate_passes():
    assert all(x.passed is True for x in reference_evaluation_bundle().evaluation_run.aggregate_metric_results)
def test_descriptive_only():
    c=reference_evaluation_bundle().comparison; assert c.provenance["descriptive_comparison_only"] is True; assert c.provenance["core_selects_winner"] is False
def test_storage_not_duplicated():
    d=contract_document(); assert d["integration"]["core_duplicates_inference_artifacts"] is False; assert d["integration"]["core_duplicates_dataset_storage"] is False
def test_no_quality_certification():
    d=contract_document(); assert d["boundaries"]["core_certifies_model_quality"] is False; assert d["boundaries"]["core_declares_scientific_truth"] is False
def test_metric_sha():
    with pytest.raises(ValidationError): EvaluationMetricDefinition(metric_id="m:x",name="x",task="regression",direction="minimize",implementation_sha256="abc")
def test_benchmark_result_fp():
    x=reference_evaluation_bundle().benchmark_result; assert x.fingerprint()==deepcopy(x).fingerprint()
def test_run_benchmark_fp():
    b=reference_evaluation_bundle(); assert b.evaluation_run.benchmark_fingerprint_sha256==b.benchmark.fingerprint()
def test_case_results_trace():
    b=reference_evaluation_bundle(); ids={x.evaluation_case_id for x in b.evaluation_cases}; assert all(x.evaluation_case_ref in ids for x in b.evaluation_run.case_results)
def test_comparison_same_benchmark():
    b=reference_evaluation_bundle(); assert b.comparison.benchmark_ref==b.benchmark.benchmark_id
def test_metric_thresholds():
    b=reference_evaluation_bundle(); assert all(x.threshold is not None for x in b.benchmark.metric_definitions)
