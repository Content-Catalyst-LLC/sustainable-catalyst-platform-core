from fastapi import APIRouter

from app.services.cross_source_semantic_reconciliation import (
    CrossSourceSemanticReconciliationBundle,
    ReconciliationAnchor,
    ReconciliationConflict,
    ReconciliationDecision,
    ReconciledSemanticCluster,
    SemanticCorrespondenceCandidate,
    contract_document,
    reference_cross_source_semantic_reconciliation_bundle,
)

router = APIRouter(prefix="/v1/source-reconciliation", tags=["cross-source-semantic-reconciliation"])
public_router = APIRouter(prefix="/public/v1/source-reconciliation", tags=["cross-source-semantic-reconciliation-public"])

@public_router.get("/contract")
def public_contract(): return contract_document()
@router.get("/contract")
def contract(): return contract_document()
@router.get("/reference")
def reference():
    b = reference_cross_source_semantic_reconciliation_bundle()
    return {"ok": True, "bundle_fingerprint_sha256": b.fingerprint(), "bundle": b.model_dump(mode="json")}
@router.get("/reference/anchors")
def reference_anchors():
    xs = reference_cross_source_semantic_reconciliation_bundle().anchors
    return {"ok": True, "count": len(xs), "items": [x.model_dump(mode="json") for x in xs]}
@router.get("/reference/candidates")
def reference_candidates():
    xs = reference_cross_source_semantic_reconciliation_bundle().candidates
    return {"ok": True, "count": len(xs), "items": [x.model_dump(mode="json") for x in xs]}
@router.get("/reference/conflicts")
def reference_conflicts():
    xs = reference_cross_source_semantic_reconciliation_bundle().conflicts
    return {"ok": True, "count": len(xs), "items": [x.model_dump(mode="json") for x in xs]}
@router.get("/reference/decisions")
def reference_decisions():
    xs = reference_cross_source_semantic_reconciliation_bundle().decisions
    return {"ok": True, "count": len(xs), "items": [x.model_dump(mode="json") for x in xs]}
@router.get("/reference/clusters")
def reference_clusters():
    xs = reference_cross_source_semantic_reconciliation_bundle().clusters
    return {"ok": True, "count": len(xs), "items": [x.model_dump(mode="json") for x in xs]}
@router.post("/validate-anchor")
def validate_anchor(payload: ReconciliationAnchor): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
@router.post("/validate-candidate")
def validate_candidate(payload: SemanticCorrespondenceCandidate): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
@router.post("/validate-conflict")
def validate_conflict(payload: ReconciliationConflict): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
@router.post("/validate-decision")
def validate_decision(payload: ReconciliationDecision): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
@router.post("/validate-cluster")
def validate_cluster(payload: ReconciledSemanticCluster): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(payload: CrossSourceSemanticReconciliationBundle): return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
