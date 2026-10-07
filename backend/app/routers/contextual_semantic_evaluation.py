from fastapi import APIRouter

from app.services.contextual_semantic_evaluation import (
    ContextualSemanticBenchmarkCase,
    ContextualSemanticEvaluationBenchmarkBundle,
    ContextualSemanticEvaluationRun,
    EvaluationPrediction,
    EvaluationTask,
    BenchmarkGoldAnnotation,
    BenchmarkCaseEvaluation,
    MetricResult,
    contract_document,
    reference_contextual_semantic_evaluation_bundle,
)

router = APIRouter(prefix="/v1/context-evaluation", tags=["contextual-semantic-evaluation"])
public_router = APIRouter(prefix="/public/v1/context-evaluation", tags=["contextual-semantic-evaluation-public"])


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/contract")
def contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle = reference_contextual_semantic_evaluation_bundle()
    return {"ok": True, "bundle_fingerprint_sha256": bundle.fingerprint(), "bundle": bundle.model_dump(mode="json")}


@router.get("/reference/cases")
def reference_cases(task: EvaluationTask | None = None):
    items = reference_contextual_semantic_evaluation_bundle().benchmark_cases
    if task is not None:
        items = [x for x in items if x.task == task]
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.get("/reference/metrics")
def reference_metrics():
    bundle = reference_contextual_semantic_evaluation_bundle()
    return {"ok": True, "count": len(bundle.metric_definitions), "definitions": [x.model_dump(mode="json") for x in bundle.metric_definitions], "results": [x.model_dump(mode="json") for x in bundle.metric_results]}


@router.get("/reference/run")
def reference_run():
    run = reference_contextual_semantic_evaluation_bundle().evaluation_runs[0]
    return {"ok": True, "run": run.model_dump(mode="json"), "fingerprint_sha256": run.fingerprint()}


@router.post("/validate-case")
def validate_case(payload: ContextualSemanticBenchmarkCase):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-gold")
def validate_gold(payload: BenchmarkGoldAnnotation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-prediction")
def validate_prediction(payload: EvaluationPrediction):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-case-evaluation")
def validate_case_evaluation(payload: BenchmarkCaseEvaluation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-metric-result")
def validate_metric_result(payload: MetricResult):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-run")
def validate_run(payload: ContextualSemanticEvaluationRun):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: ContextualSemanticEvaluationBenchmarkBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
