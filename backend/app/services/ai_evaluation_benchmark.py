from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator
from .computational_runtime_objects import canonical_sha256

CORE_RELEASE="3.31.0"
CONTRACT_VERSION="sc.core.ai-evaluation-benchmark.v1"

class EvaluationTask(str, Enum):
    classification="classification"; regression="regression"; forecasting="forecasting"
    ranking="ranking"; retrieval="retrieval"; generation="generation"
    summarization="summarization"; extraction="extraction"; question_answering="question-answering"
    embedding="embedding"; multimodal="multimodal"; scientific_ml="scientific-ml"
    safety="safety"; robustness="robustness"; calibration="calibration"; other="other"

class EvaluationStatus(str, Enum):
    declared="declared"; queued="queued"; running="running"; completed="completed"
    failed="failed"; cancelled="cancelled"

class MetricDirection(str, Enum):
    maximize="maximize"; minimize="minimize"; target="target"; informational="informational"

class EvaluationDatasetBinding(BaseModel):
    evaluation_dataset_binding_id:str=Field(min_length=2,max_length=300)
    dataset_version_ref:str=Field(min_length=2,max_length=300)
    role:Literal["benchmark","holdout","validation","gold","stress-test","adversarial","safety","calibration","other"]="benchmark"
    slice_refs:list[str]=Field(default_factory=list)
    ground_truth_artifact_ref:str|None=Field(default=None,max_length=300)
    sample_count:int|None=Field(default=None,ge=0)
    metadata:dict[str,Any]=Field(default_factory=dict)
    def fingerprint(self)->str: return canonical_sha256(self)

class EvaluationMetricDefinition(BaseModel):
    metric_id:str=Field(min_length=2,max_length=300)
    name:str=Field(min_length=1,max_length=300)
    task:EvaluationTask
    direction:MetricDirection
    unit:str|None=Field(default=None,max_length=120)
    target_value:float|None=None
    threshold:float|None=None
    aggregation:Literal["mean","median","sum","min","max","micro","macro","weighted","none","other"]="mean"
    method_ref:str|None=Field(default=None,max_length=300)
    implementation_ref:str|None=Field(default=None,max_length=2000)
    implementation_sha256:str|None=Field(default=None,pattern=r"^[0-9a-f]{64}$")
    metadata:dict[str,Any]=Field(default_factory=dict)
    def fingerprint(self)->str: return canonical_sha256(self)

class BenchmarkDefinition(BaseModel):
    benchmark_id:str=Field(min_length=2,max_length=300)
    name:str=Field(min_length=1,max_length=300)
    task:EvaluationTask
    benchmark_version:str=Field(min_length=1,max_length=240)
    description:str|None=Field(default=None,max_length=10000)
    dataset_bindings:list[EvaluationDatasetBinding]=Field(default_factory=list)
    metric_definitions:list[EvaluationMetricDefinition]=Field(default_factory=list)
    prompt_version_ref:str|None=Field(default=None,max_length=300)
    retrieval_context_ref:str|None=Field(default=None,max_length=300)
    created_at:datetime=Field(default_factory=lambda:datetime.now(timezone.utc))
    provenance:dict[str,Any]=Field(default_factory=dict)
    metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_unique(self):
        ds=[x.evaluation_dataset_binding_id for x in self.dataset_bindings]
        ms=[x.metric_id for x in self.metric_definitions]
        if len(ds)!=len(set(ds)): raise ValueError("evaluation dataset binding ids must be unique")
        if len(ms)!=len(set(ms)): raise ValueError("evaluation metric ids must be unique")
        return self
    def fingerprint(self)->str:
        d=self.model_dump(mode="json",exclude_none=True); d.pop("created_at",None); return canonical_sha256(d)

class EvaluationCase(BaseModel):
    evaluation_case_id:str=Field(min_length=2,max_length=300)
    benchmark_ref:str=Field(min_length=2,max_length=300)
    dataset_version_ref:str|None=Field(default=None,max_length=300)
    sample_ref:str|None=Field(default=None,max_length=300)
    input_ref:str|None=Field(default=None,max_length=300)
    expected_output:Any=None
    expected_output_sha256:str|None=Field(default=None,pattern=r"^[0-9a-f]{64}$")
    slice_refs:list[str]=Field(default_factory=list)
    metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_source(self):
        if not any([self.dataset_version_ref,self.sample_ref,self.input_ref]):
            raise ValueError("evaluation case requires dataset_version_ref, sample_ref, or input_ref")
        return self
    def fingerprint(self)->str: return canonical_sha256(self)

class EvaluationMetricResult(BaseModel):
    metric_ref:str=Field(min_length=2,max_length=300)
    value:float|int|None=None
    passed:bool|None=None
    sample_count:int|None=Field(default=None,ge=0)
    confidence_interval:list[float]|None=None
    metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_ci(self):
        if self.confidence_interval is not None:
            if len(self.confidence_interval)!=2: raise ValueError("confidence_interval must contain [lower, upper]")
            if self.confidence_interval[0]>self.confidence_interval[1]: raise ValueError("confidence_interval lower bound exceeds upper bound")
        return self

class EvaluationCaseResult(BaseModel):
    evaluation_case_result_id:str=Field(min_length=2,max_length=300)
    evaluation_case_ref:str=Field(min_length=2,max_length=300)
    inference_run_ref:str=Field(min_length=2,max_length=300)
    ai_artifact_refs:list[str]=Field(default_factory=list)
    metric_results:list[EvaluationMetricResult]=Field(default_factory=list)
    observed_output:Any=None
    observed_output_sha256:str|None=Field(default=None,pattern=r"^[0-9a-f]{64}$")
    error_category:str|None=Field(default=None,max_length=300)
    notes:str|None=Field(default=None,max_length=10000)
    metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_metrics(self):
        refs=[x.metric_ref for x in self.metric_results]
        if len(refs)!=len(set(refs)): raise ValueError("metric results must be unique per metric_ref")
        return self
    def fingerprint(self)->str: return canonical_sha256(self)

class EvaluationRun(BaseModel):
    evaluation_run_id:str=Field(min_length=2,max_length=300)
    status:EvaluationStatus=EvaluationStatus.declared
    benchmark_ref:str=Field(min_length=2,max_length=300)
    benchmark_fingerprint_sha256:str=Field(pattern=r"^[0-9a-f]{64}$")
    ai_model_ref:str=Field(min_length=2,max_length=300)
    ai_model_version_ref:str=Field(min_length=2,max_length=300)
    computational_job_ref:str=Field(min_length=2,max_length=300)
    runtime_environment_ref:str|None=Field(default=None,max_length=300)
    case_refs:list[str]=Field(default_factory=list)
    case_results:list[EvaluationCaseResult]=Field(default_factory=list)
    aggregate_metric_results:list[EvaluationMetricResult]=Field(default_factory=list)
    started_at:datetime|None=None; completed_at:datetime|None=None
    created_at:datetime=Field(default_factory=lambda:datetime.now(timezone.utc))
    provenance:dict[str,Any]=Field(default_factory=dict)
    metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_run(self):
        if not self.ai_model_version_ref.startswith("ai-model-version:"): raise ValueError("ai_model_version_ref must identify an AI model version")
        if len({x.evaluation_case_result_id for x in self.case_results})!=len(self.case_results): raise ValueError("evaluation case result ids must be unique")
        refs=[x.metric_ref for x in self.aggregate_metric_results]
        if len(refs)!=len(set(refs)): raise ValueError("aggregate metric results must be unique per metric_ref")
        known=set(self.case_refs)
        if any(x.evaluation_case_ref not in known for x in self.case_results): raise ValueError("evaluation case result references undeclared case")
        if self.status==EvaluationStatus.completed and (not self.case_results or not self.aggregate_metric_results):
            raise ValueError("completed evaluation run requires case results and aggregate metrics")
        if self.started_at and self.completed_at and self.completed_at<self.started_at: raise ValueError("completed_at cannot precede started_at")
        return self
    def fingerprint(self)->str:
        d=self.model_dump(mode="json",exclude_none=True)
        for k in ("status","started_at","completed_at","created_at"): d.pop(k,None)
        return canonical_sha256(d)

class BenchmarkResult(BaseModel):
    benchmark_result_id:str=Field(min_length=2,max_length=300)
    benchmark_ref:str=Field(min_length=2,max_length=300)
    evaluation_run_ref:str=Field(min_length=2,max_length=300)
    ai_model_version_ref:str=Field(min_length=2,max_length=300)
    metric_results:list[EvaluationMetricResult]=Field(default_factory=list)
    case_count:int=Field(ge=0); pass_count:int|None=Field(default=None,ge=0); fail_count:int|None=Field(default=None,ge=0)
    metadata:dict[str,Any]=Field(default_factory=dict)
    def fingerprint(self)->str: return canonical_sha256(self)

class ModelBenchmarkComparisonEntry(BaseModel):
    ai_model_version_ref:str=Field(min_length=2,max_length=300)
    benchmark_result_ref:str=Field(min_length=2,max_length=300)
    metric_values:dict[str,float|int|None]=Field(default_factory=dict)
    metadata:dict[str,Any]=Field(default_factory=dict)

class ModelBenchmarkComparison(BaseModel):
    comparison_id:str=Field(min_length=2,max_length=300)
    benchmark_ref:str=Field(min_length=2,max_length=300)
    entries:list[ModelBenchmarkComparisonEntry]=Field(default_factory=list)
    created_at:datetime=Field(default_factory=lambda:datetime.now(timezone.utc))
    provenance:dict[str,Any]=Field(default_factory=dict)
    metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_entries(self):
        versions=[x.ai_model_version_ref for x in self.entries]
        if len(versions)!=len(set(versions)): raise ValueError("comparison entries must use unique model versions")
        return self
    def fingerprint(self)->str:
        d=self.model_dump(mode="json",exclude_none=True); d.pop("created_at",None); return canonical_sha256(d)

class EvaluationBundle(BaseModel):
    benchmark:BenchmarkDefinition
    evaluation_cases:list[EvaluationCase]=Field(default_factory=list)
    evaluation_run:EvaluationRun
    benchmark_result:BenchmarkResult
    comparison:ModelBenchmarkComparison|None=None
    @model_validator(mode="after")
    def validate_bundle(self):
        if self.evaluation_run.benchmark_ref!=self.benchmark.benchmark_id: raise ValueError("evaluation run benchmark_ref must match benchmark")
        if self.benchmark_result.benchmark_ref!=self.benchmark.benchmark_id: raise ValueError("benchmark result benchmark_ref must match benchmark")
        if self.benchmark_result.evaluation_run_ref!=self.evaluation_run.evaluation_run_id: raise ValueError("benchmark result evaluation_run_ref must match evaluation run")
        if self.benchmark_result.ai_model_version_ref!=self.evaluation_run.ai_model_version_ref: raise ValueError("benchmark result model version must match evaluation run")
        case_ids={x.evaluation_case_id for x in self.evaluation_cases}
        missing=[x for x in self.evaluation_run.case_refs if x not in case_ids]
        if missing: raise ValueError("evaluation run references cases not present in bundle")
        return self
    def fingerprint(self)->str:
        return canonical_sha256({
            "benchmark":self.benchmark.fingerprint(),
            "cases":sorted(x.fingerprint() for x in self.evaluation_cases),
            "run":self.evaluation_run.fingerprint(),
            "result":self.benchmark_result.fingerprint(),
            "comparison":self.comparison.fingerprint() if self.comparison else None,
        })

def reference_evaluation_bundle()->EvaluationBundle:
    acc=EvaluationMetricDefinition(metric_id="metric:accuracy",name="Accuracy",task=EvaluationTask.classification,direction=MetricDirection.maximize,threshold=.9)
    f1=EvaluationMetricDefinition(metric_id="metric:f1-macro",name="Macro F1",task=EvaluationTask.classification,direction=MetricDirection.maximize,threshold=.85,aggregation="macro")
    ds=EvaluationDatasetBinding(evaluation_dataset_binding_id="evaluation-dataset:reference-holdout",dataset_version_ref="dataset-version:reference-classification:v1",role="holdout",ground_truth_artifact_ref="artifact:reference-ground-truth",sample_count=100)
    bench=BenchmarkDefinition(benchmark_id="benchmark:reference-classification:v1",name="Reference Classification Benchmark",task=EvaluationTask.classification,benchmark_version="1.0.0",dataset_bindings=[ds],metric_definitions=[acc,f1],provenance={"core_selects_winner":False})
    c1=EvaluationCase(evaluation_case_id="evaluation-case:reference:001",benchmark_ref=bench.benchmark_id,dataset_version_ref=ds.dataset_version_ref,sample_ref="sample:001",expected_output={"label":"positive"},expected_output_sha256="a"*64)
    c2=EvaluationCase(evaluation_case_id="evaluation-case:reference:002",benchmark_ref=bench.benchmark_id,dataset_version_ref=ds.dataset_version_ref,sample_ref="sample:002",expected_output={"label":"negative"},expected_output_sha256="b"*64)
    r1=EvaluationCaseResult(evaluation_case_result_id="evaluation-case-result:001",evaluation_case_ref=c1.evaluation_case_id,inference_run_ref="inference-run:evaluation:001",ai_artifact_refs=["ai-artifact:evaluation:001"],metric_results=[EvaluationMetricResult(metric_ref=acc.metric_id,value=1.0,passed=True,sample_count=1),EvaluationMetricResult(metric_ref=f1.metric_id,value=1.0,passed=True,sample_count=1)],observed_output={"label":"positive"},observed_output_sha256="c"*64)
    r2=EvaluationCaseResult(evaluation_case_result_id="evaluation-case-result:002",evaluation_case_ref=c2.evaluation_case_id,inference_run_ref="inference-run:evaluation:002",ai_artifact_refs=["ai-artifact:evaluation:002"],metric_results=[EvaluationMetricResult(metric_ref=acc.metric_id,value=1.0,passed=True,sample_count=1),EvaluationMetricResult(metric_ref=f1.metric_id,value=1.0,passed=True,sample_count=1)],observed_output={"label":"negative"},observed_output_sha256="d"*64)
    agg=[EvaluationMetricResult(metric_ref=acc.metric_id,value=1.0,passed=True,sample_count=2,confidence_interval=[.84,1.0]),EvaluationMetricResult(metric_ref=f1.metric_id,value=1.0,passed=True,sample_count=2,confidence_interval=[.84,1.0])]
    run=EvaluationRun(evaluation_run_id="evaluation-run:reference-classifier:001",status=EvaluationStatus.completed,benchmark_ref=bench.benchmark_id,benchmark_fingerprint_sha256=bench.fingerprint(),ai_model_ref="ai-model:reference-classifier",ai_model_version_ref="ai-model-version:reference-classifier:1.0.0",computational_job_ref="job:reference-evaluation-001",runtime_environment_ref="environment:reference-python",case_refs=[c1.evaluation_case_id,c2.evaluation_case_id],case_results=[r1,r2],aggregate_metric_results=agg,started_at=datetime(2026,9,25,12,0,tzinfo=timezone.utc),completed_at=datetime(2026,9,25,12,0,2,tzinfo=timezone.utc))
    result=BenchmarkResult(benchmark_result_id="benchmark-result:reference-classifier:001",benchmark_ref=bench.benchmark_id,evaluation_run_ref=run.evaluation_run_id,ai_model_version_ref=run.ai_model_version_ref,metric_results=agg,case_count=2,pass_count=2,fail_count=0)
    comp=ModelBenchmarkComparison(comparison_id="benchmark-comparison:reference:v1",benchmark_ref=bench.benchmark_id,entries=[ModelBenchmarkComparisonEntry(ai_model_version_ref=run.ai_model_version_ref,benchmark_result_ref=result.benchmark_result_id,metric_values={acc.metric_id:1.0,f1.metric_id:1.0}),ModelBenchmarkComparisonEntry(ai_model_version_ref="ai-model-version:reference-classifier:0.9.0",benchmark_result_ref="benchmark-result:legacy",metric_values={acc.metric_id:.92,f1.metric_id:.90})],provenance={"descriptive_comparison_only":True,"core_selects_winner":False})
    return EvaluationBundle(benchmark=bench,evaluation_cases=[c1,c2],evaluation_run=run,benchmark_result=result,comparison=comp)

def contract_document()->dict[str,Any]:
    ref=reference_evaluation_bundle()
    return {
      "ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
      "object_types":["EvaluationDatasetBinding","EvaluationMetricDefinition","BenchmarkDefinition","EvaluationCase","EvaluationMetricResult","EvaluationCaseResult","EvaluationRun","BenchmarkResult","ModelBenchmarkComparison","EvaluationBundle"],
      "capabilities":{"benchmark_identity":True,"dataset_version_binding":True,"ground_truth_binding":True,"metric_definition_identity":True,"case_level_results":True,"aggregate_metrics":True,"model_version_binding":True,"inference_run_binding":True,"descriptive_model_comparison":True},
      "integration":{"lab_executes_evaluations":True,"workspace_or_runtime_executes_jobs":True,"core_duplicates_inference_artifacts":False,"core_duplicates_dataset_storage":False},
      "boundaries":{"core_executes_evaluation":False,"core_selects_best_model":False,"core_certifies_model_quality":False,"core_declares_scientific_truth":False,"core_owns_evaluation_contracts_and_provenance":True},
      "reference":{"benchmark_id":ref.benchmark.benchmark_id,"evaluation_run_id":ref.evaluation_run.evaluation_run_id,"bundle_fingerprint_sha256":ref.fingerprint()}
    }
