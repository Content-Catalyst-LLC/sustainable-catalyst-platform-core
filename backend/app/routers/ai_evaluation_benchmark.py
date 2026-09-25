from fastapi import APIRouter
from ..services.ai_evaluation_benchmark import (
    CORE_RELEASE, CONTRACT_VERSION, BenchmarkDefinition, EvaluationCase,
    EvaluationRun, EvaluationBundle, ModelBenchmarkComparison,
    contract_document, reference_evaluation_bundle
)
router=APIRouter(prefix="/api/v1/ai-evaluation-benchmarks",tags=["ai-evaluation-benchmarks"])
public_router=APIRouter(prefix="/public/v1/ai-evaluation-benchmarks",tags=["public-ai-evaluation-benchmarks"])
@router.get("/contract")
def get_contract(): return contract_document()
@public_router.get("/contract")
def get_public_contract(): return contract_document()
@router.get("/reference")
def get_reference():
    b=reference_evaluation_bundle()
    return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle":b.model_dump(mode="json",exclude_none=True),"bundle_fingerprint_sha256":b.fingerprint(),"benchmark_fingerprint_sha256":b.benchmark.fingerprint(),"evaluation_run_fingerprint_sha256":b.evaluation_run.fingerprint(),"benchmark_result_fingerprint_sha256":b.benchmark_result.fingerprint(),"comparison_fingerprint_sha256":b.comparison.fingerprint() if b.comparison else None}
@router.post("/validate-benchmark")
def validate_benchmark(body:BenchmarkDefinition): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"benchmark_fingerprint_sha256":body.fingerprint()}
@router.post("/validate-case")
def validate_case(body:EvaluationCase): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"evaluation_case_fingerprint_sha256":body.fingerprint()}
@router.post("/validate-run")
def validate_run(body:EvaluationRun): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"evaluation_run_fingerprint_sha256":body.fingerprint()}
@router.post("/validate-comparison")
def validate_comparison(body:ModelBenchmarkComparison): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"comparison_fingerprint_sha256":body.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(body:EvaluationBundle): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle_fingerprint_sha256":body.fingerprint()}
