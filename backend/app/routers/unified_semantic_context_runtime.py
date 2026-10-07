from fastapi import APIRouter

from app.services.unified_semantic_context_runtime import (
    RuntimeStageKind,
    SemanticRuntimeStageResult,
    UnifiedSemanticContextRuntimeBundle,
    UnifiedSemanticContextSession,
    UnifiedSemanticRuntimePlan,
    contract_document,
    reference_unified_semantic_context_runtime_bundle,
)

router = APIRouter(prefix="/v1/semantic-context-runtime", tags=["unified-semantic-context-runtime"])
public_router = APIRouter(prefix="/public/v1/semantic-context-runtime", tags=["unified-semantic-context-runtime-public"])


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/contract")
def contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle = reference_unified_semantic_context_runtime_bundle()
    return {"ok": True, "bundle_fingerprint_sha256": bundle.fingerprint(), "bundle": bundle.model_dump(mode="json")}


@router.get("/reference/plan")
def reference_plan():
    plan = reference_unified_semantic_context_runtime_bundle().plans[0]
    return {"ok": True, "plan": plan.model_dump(mode="json"), "fingerprint_sha256": plan.fingerprint()}


@router.get("/reference/session")
def reference_session():
    session = reference_unified_semantic_context_runtime_bundle().sessions[0]
    return {"ok": True, "session": session.model_dump(mode="json"), "fingerprint_sha256": session.fingerprint()}


@router.get("/reference/stages")
def reference_stages(kind: RuntimeStageKind | None = None):
    items = reference_unified_semantic_context_runtime_bundle().stage_definitions
    if kind is not None:
        items = [x for x in items if x.kind == kind]
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.get("/reference/artifacts")
def reference_artifacts(stage_ref: str | None = None):
    items = reference_unified_semantic_context_runtime_bundle().artifacts
    if stage_ref is not None:
        items = [x for x in items if x.stage_ref == stage_ref]
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.post("/validate-plan")
def validate_plan(payload: UnifiedSemanticRuntimePlan):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-stage-result")
def validate_stage_result(payload: SemanticRuntimeStageResult):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-session")
def validate_session(payload: UnifiedSemanticContextSession):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: UnifiedSemanticContextRuntimeBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
