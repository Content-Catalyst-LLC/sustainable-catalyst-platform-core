from fastapi import APIRouter

from app.services.cross_document_context_graph import (
    ContextEdgeType,
    ContextGraphEdge,
    ContextGraphInterpretation,
    ContextNodeType,
    CrossDocumentContextGraphBundle,
    CrossDocumentContextThread,
    GraphReviewState,
    contract_document,
    reference_cross_document_context_graph_bundle,
)

router = APIRouter(prefix="/v1/context-graph", tags=["cross-document-context-graph"])
public_router = APIRouter(prefix="/public/v1/context-graph", tags=["cross-document-context-graph-public"])


@public_router.get("/contract")
def public_contract():
    return contract_document()


@router.get("/contract")
def contract():
    return contract_document()


@router.get("/reference")
def reference():
    bundle = reference_cross_document_context_graph_bundle()
    return {"ok": True, "bundle_fingerprint_sha256": bundle.fingerprint(), "bundle": bundle.model_dump(mode="json")}


@router.get("/reference/nodes")
def reference_nodes(node_type: ContextNodeType | None = None, document_ref: str | None = None):
    items = reference_cross_document_context_graph_bundle().nodes
    if node_type is not None:
        items = [x for x in items if x.node_type == node_type]
    if document_ref is not None:
        items = [x for x in items if x.document_ref == document_ref]
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.get("/reference/edges")
def reference_edges(edge_type: ContextEdgeType | None = None, cross_document: bool | None = None, state: GraphReviewState | None = None):
    items = reference_cross_document_context_graph_bundle().edges
    if edge_type is not None:
        items = [x for x in items if x.edge_type == edge_type]
    if cross_document is not None:
        items = [x for x in items if x.cross_document is cross_document]
    if state is not None:
        items = [x for x in items if x.state == state]
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.get("/reference/threads")
def reference_threads(state: GraphReviewState | None = None):
    items = reference_cross_document_context_graph_bundle().threads
    if state is not None:
        items = [x for x in items if x.state == state]
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}


@router.post("/validate-edge")
def validate_edge(payload: ContextGraphEdge):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-thread")
def validate_thread(payload: CrossDocumentContextThread):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-interpretation")
def validate_interpretation(payload: ContextGraphInterpretation):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(payload: CrossDocumentContextGraphBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
