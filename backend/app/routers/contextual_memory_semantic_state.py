from fastapi import APIRouter

from app.services.contextual_memory_semantic_state import (
    ContextualMemoryCheckpoint,
    ContextualMemorySemanticStateBundle,
    MemoryScopeKind,
    SemanticMemoryKind,
    SemanticStateRevision,
    contract_document,
    reference_contextual_memory_semantic_state_bundle,
)

router = APIRouter(prefix="/v1/context-memory", tags=["contextual-memory-semantic-state"])
public_router = APIRouter(prefix="/public/v1/context-memory", tags=["contextual-memory-semantic-state-public"])


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/contract")
def contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle = reference_contextual_memory_semantic_state_bundle()
    return {"ok": True, "bundle_fingerprint_sha256": bundle.fingerprint(), "bundle": bundle.model_dump(mode="json")}


@router.get("/reference/scopes")
def reference_scopes(kind: MemoryScopeKind | None = None):
    items = reference_contextual_memory_semantic_state_bundle().scopes
    if kind is not None:
        items = [x for x in items if x.kind == kind]
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.get("/reference/memories")
def reference_memories(kind: SemanticMemoryKind | None = None, scope_ref: str | None = None):
    items = reference_contextual_memory_semantic_state_bundle().memories
    if kind is not None:
        items = [x for x in items if x.kind == kind]
    if scope_ref is not None:
        items = [x for x in items if x.scope_ref == scope_ref]
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.get("/reference/revisions/{memory_id}")
def reference_revisions(memory_id: str):
    items = [x for x in reference_contextual_memory_semantic_state_bundle().revisions if x.memory_ref == memory_id]
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.get("/reference/checkpoint")
def reference_checkpoint():
    item = reference_contextual_memory_semantic_state_bundle().checkpoints[0]
    return {"ok": True, "checkpoint": item.model_dump(mode="json"), "fingerprint_sha256": item.fingerprint()}


@router.post("/validate-revision")
def validate_revision(payload: SemanticStateRevision):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-checkpoint")
def validate_checkpoint(payload: ContextualMemoryCheckpoint):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: ContextualMemorySemanticStateBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
