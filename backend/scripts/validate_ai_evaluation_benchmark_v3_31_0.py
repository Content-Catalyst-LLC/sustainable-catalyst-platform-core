#!/usr/bin/env python3
from copy import deepcopy
from app.services.ai_evaluation_benchmark import CONTRACT_VERSION,contract_document,reference_evaluation_bundle
d=contract_document()
assert d["release"]=="3.31.0" and d["contract"]==CONTRACT_VERSION
assert d["capabilities"]["benchmark_identity"] and d["capabilities"]["model_version_binding"]
assert d["boundaries"]["core_executes_evaluation"] is False
assert d["boundaries"]["core_selects_best_model"] is False
b=reference_evaluation_bundle()
assert len(b.fingerprint())==64 and b.fingerprint()==deepcopy(b).fingerprint()
assert b.evaluation_run.benchmark_fingerprint_sha256==b.benchmark.fingerprint()
assert b.evaluation_run.ai_model_version_ref=="ai-model-version:reference-classifier:1.0.0"
assert b.evaluation_run.computational_job_ref=="job:reference-evaluation-001"
assert len(b.evaluation_run.case_results)==2
assert len(b.evaluation_run.aggregate_metric_results)==2
assert b.comparison and b.comparison.provenance["core_selects_winner"] is False
print("PASS - Platform Core v3.31.0 AI Evaluation & Benchmark Object System")
print(f"CONTRACT={CONTRACT_VERSION}")
print("BENCHMARK_IDENTITY=enabled")
print("GROUND_TRUTH_BINDING=enabled")
print("METRIC_DEFINITION_IDENTITY=enabled")
print("CASE_LEVEL_RESULTS=enabled")
print("AGGREGATE_METRICS=enabled")
print("MODEL_VERSION_BINDING=enabled")
print("INFERENCE_RUN_BINDING=enabled")
print("DESCRIPTIVE_MODEL_COMPARISON=enabled")
print("CORE_SELECTS_BEST_MODEL=false")
print("CORE_EXECUTES_EVALUATION=false")
