from __future__ import annotations
import hashlib, json
from datetime import datetime
from sqlalchemy import func, select, inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (
    UnifiedVisualReasoningWorkspaceRecord,
    CrossProductVisualRuntimeIntegrationRecord,
    CrossProductVisualObjectBindingRecord,
    CrossProductVisualContextBindingRecord,
    CrossProductVisualCapabilityBindingRecord,
    CrossProductVisualViewBindingRecord,
    CrossProductVisualHandoffRouteRecord,
    CrossProductVisualSyncRecord,
    CrossProductVisualIntegrationSnapshotRecord,
)

CONTRACT = "sc.visual-runtime.cross-product-integration.v1"
PRODUCTS = {
    "library",
    "lab",
    "workbench",
    "decision-studio",
    "site-intelligence",
    "workspace",
    "research-librarian",
}
CAPABILITIES = {
    "graph", "timeline", "map", "plot", "table", "network", "model",
    "forecast", "evidence", "decision", "notebook", "document", "linked-view",
}
FORBIDDEN = {
    "render_by_core",
    "compute_by_core",
    "mutate_specialist_state_by_core",
    "execute_handoff_by_core",
    "automatic_cross_product_sync",
    "automatic_visual_inference",
    "automatic_truth_promotion",
}


def _ser(row):
    out = {}
    for a in sa_inspect(row).mapper.column_attrs:
        v = getattr(row, a.key)
        out[a.key] = v.isoformat() if isinstance(v, datetime) else v
    for k in list(out):
        if k.endswith("_json"):
            out[k[:-5]] = out.pop(k)
    return out


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _reject(payload):
    bad = sorted(k for k in FORBIDDEN if payload.get(k) not in (None, False))
    if bad:
        raise ValueError("Cross-product visual integration is declarative; Core does not execute: " + ", ".join(bad))


def _product(value: str) -> str:
    if value not in PRODUCTS:
        raise ValueError("unsupported Catalyst product: " + value)
    return value


def boundaries():
    return {
        "product_integration_registry_by_core": True,
        "shared_object_binding_registry_by_core": True,
        "research_context_binding_registry_by_core": True,
        "visual_capability_contract_registry_by_core": True,
        "cross_product_view_binding_registry_by_core": True,
        "handoff_route_registry_by_core": True,
        "synchronization_evidence_registry_by_core": True,
        "immutable_cross_product_visual_snapshots_by_core": True,
        "render_by_core": False,
        "compute_by_core": False,
        "mutate_specialist_state_by_core": False,
        "execute_handoff_by_core": False,
        "automatic_cross_product_sync": False,
        "automatic_visual_inference": False,
        "automatic_truth_promotion": False,
    }


CLASSES = [
    CrossProductVisualRuntimeIntegrationRecord,
    CrossProductVisualObjectBindingRecord,
    CrossProductVisualContextBindingRecord,
    CrossProductVisualCapabilityBindingRecord,
    CrossProductVisualViewBindingRecord,
    CrossProductVisualHandoffRouteRecord,
    CrossProductVisualSyncRecord,
    CrossProductVisualIntegrationSnapshotRecord,
]


def readiness(db: Session):
    c = lambda cls: db.scalar(select(func.count()).select_from(cls)) or 0
    names = ["integrations", "object_bindings", "context_bindings", "capability_bindings", "view_bindings", "handoff_routes", "sync_records", "snapshots"]
    return {
        "release": "2.71.0",
        "contract": CONTRACT,
        "products": sorted(PRODUCTS),
        "capabilities": sorted(CAPABILITIES),
        "counts": dict(zip(names, [c(x) for x in CLASSES])),
        **boundaries(),
    }


def _workspace(db: Session, workspace_id: str):
    row = db.get(UnifiedVisualReasoningWorkspaceRecord, workspace_id)
    if not row:
        raise ValueError("unified visual reasoning workspace not found.")
    return row


def _integration(db: Session, integration_id: str):
    row = db.get(CrossProductVisualRuntimeIntegrationRecord, integration_id)
    if not row:
        raise ValueError("cross-product visual runtime integration not found.")
    return row


def create_integration(db: Session, workspace_id: str, payload: dict):
    _reject(payload)
    _workspace(db, workspace_id)
    product_key = _product(payload["product_key"])
    row = CrossProductVisualRuntimeIntegrationRecord(
        workspace_id=workspace_id,
        product_key=product_key,
        integration_key=payload["integration_key"],
        name=payload["name"],
        status=payload.get("status", "declared"),
        runtime_contract_json=payload.get("runtime_contract", {}),
        provenance_json=payload.get("provenance", {}),
        metadata_json=payload.get("metadata", {}),
    )
    db.add(row); db.commit(); db.refresh(row)
    return _ser(row)


def object_binding(db: Session, integration_id: str, payload: dict):
    _reject(payload); _integration(db, integration_id)
    row = CrossProductVisualObjectBindingRecord(
        integration_id=integration_id,
        binding_key=payload["binding_key"],
        canonical_object_refs_json=payload.get("canonical_object_refs", []),
        product_object_refs_json=payload.get("product_object_refs", []),
        semantic_roles_json=payload.get("semantic_roles", []),
        provenance_json=payload.get("provenance", {}),
    )
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def context_binding(db: Session, integration_id: str, payload: dict):
    _reject(payload); _integration(db, integration_id)
    row = CrossProductVisualContextBindingRecord(
        integration_id=integration_id,
        context_key=payload["context_key"],
        context_type=payload["context_type"],
        canonical_context_ref=payload.get("canonical_context_ref"),
        product_context_refs_json=payload.get("product_context_refs", []),
        context_contract_json=payload.get("context_contract", {}),
        provenance_json=payload.get("provenance", {}),
    )
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def capability_binding(db: Session, integration_id: str, payload: dict):
    _reject(payload); _integration(db, integration_id)
    capability = payload["capability_key"]
    if capability not in CAPABILITIES:
        raise ValueError("unsupported visual capability: " + capability)
    row = CrossProductVisualCapabilityBindingRecord(
        integration_id=integration_id,
        capability_key=capability,
        object_kinds_json=payload.get("object_kinds", []),
        operation_contract_json=payload.get("operation_contract", {}),
        output_contract_json=payload.get("output_contract", {}),
        provenance_json=payload.get("provenance", {}),
    )
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def view_binding(db: Session, integration_id: str, payload: dict):
    _reject(payload); _integration(db, integration_id)
    row = CrossProductVisualViewBindingRecord(
        integration_id=integration_id,
        binding_key=payload["binding_key"],
        unified_view_ids_json=payload.get("unified_view_ids", []),
        product_view_refs_json=payload.get("product_view_refs", []),
        view_contract_json=payload.get("view_contract", {}),
        provenance_json=payload.get("provenance", {}),
    )
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def handoff_route(db: Session, workspace_id: str, payload: dict):
    _reject(payload); _workspace(db, workspace_id)
    source = payload.get("source_product", "workspace")
    target = payload["target_product"]
    _product(source); _product(target)
    capability = payload["capability_key"]
    if capability not in CAPABILITIES:
        raise ValueError("unsupported visual capability: " + capability)
    row = CrossProductVisualHandoffRouteRecord(
        workspace_id=workspace_id,
        route_key=payload["route_key"],
        source_product=source,
        target_product=target,
        capability_key=capability,
        request_contract_json=payload.get("request_contract", {}),
        result_contract_json=payload.get("result_contract", {}),
        provenance_json=payload.get("provenance", {}),
    )
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def sync_record(db: Session, workspace_id: str, payload: dict):
    _reject(payload); _workspace(db, workspace_id)
    source = _product(payload["source_product"]); target = _product(payload["target_product"])
    row = CrossProductVisualSyncRecord(
        workspace_id=workspace_id,
        sync_key=payload["sync_key"],
        source_product=source,
        target_product=target,
        direction=payload.get("direction", "declared"),
        state_hashes_json=payload.get("state_hashes", {}),
        synchronization_evidence_json=payload.get("synchronization_evidence", {}),
        provenance_json=payload.get("provenance", {}),
    )
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def bundle(db: Session, workspace_id: str, public_only: bool = False):
    workspace = _workspace(db, workspace_id)
    if public_only and workspace.visibility != "public":
        raise ValueError("unified visual reasoning workspace is not public.")
    integrations = db.scalars(select(CrossProductVisualRuntimeIntegrationRecord).where(CrossProductVisualRuntimeIntegrationRecord.workspace_id == workspace_id)).all()
    integration_ids = [x.id for x in integrations]
    def children(cls):
        if not integration_ids: return []
        return [_ser(x) for x in db.scalars(select(cls).where(cls.integration_id.in_(integration_ids))).all()]
    return {
        "contract": CONTRACT,
        "workspace_id": workspace_id,
        "products": sorted(PRODUCTS),
        "capabilities": sorted(CAPABILITIES),
        "boundaries": boundaries(),
        "integrations": [_ser(x) for x in integrations],
        "object_bindings": children(CrossProductVisualObjectBindingRecord),
        "context_bindings": children(CrossProductVisualContextBindingRecord),
        "capability_bindings": children(CrossProductVisualCapabilityBindingRecord),
        "view_bindings": children(CrossProductVisualViewBindingRecord),
        "handoff_routes": [_ser(x) for x in db.scalars(select(CrossProductVisualHandoffRouteRecord).where(CrossProductVisualHandoffRouteRecord.workspace_id == workspace_id)).all()],
        "sync_records": [_ser(x) for x in db.scalars(select(CrossProductVisualSyncRecord).where(CrossProductVisualSyncRecord.workspace_id == workspace_id)).all()],
        "snapshots": [_ser(x) for x in db.scalars(select(CrossProductVisualIntegrationSnapshotRecord).where(CrossProductVisualIntegrationSnapshotRecord.workspace_id == workspace_id)).all()],
    }


def snapshot(db: Session, workspace_id: str, payload: dict):
    _reject(payload)
    state = bundle(db, workspace_id); state.pop("snapshots", None)
    prev = db.scalars(select(CrossProductVisualIntegrationSnapshotRecord).where(CrossProductVisualIntegrationSnapshotRecord.workspace_id == workspace_id).order_by(CrossProductVisualIntegrationSnapshotRecord.revision.asc())).all()
    revision = len(prev) + 1
    previous_hash = prev[-1].content_hash if prev else None
    content_hash = _hash({"revision": revision, "previous_snapshot_hash": previous_hash, "state": state})
    row = CrossProductVisualIntegrationSnapshotRecord(
        workspace_id=workspace_id,
        revision=revision,
        content_hash=content_hash,
        previous_snapshot_hash=previous_hash,
        state_json=state,
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(row); db.commit(); db.refresh(row); return _ser(row)
