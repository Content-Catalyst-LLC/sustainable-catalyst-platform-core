from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Entity,
    EvidenceRecord,
    SourceSnapshot,
    ResearchVisualExplanationRecord,
    ResearchExplanationNodeRecord,
    ResearchExplanationRelationRecord,
    ResearchExplanationCitationRecord,
    ResearchExplanationViewRecord,
    ResearchExplanationSnapshotRecord,
)

EXPLANATION_KINDS = {
    "evidence-map", "argument-map", "concept-map", "source-trace", "timeline",
    "comparison", "causal-explanation", "spatial-explanation", "mixed",
}
NODE_KINDS = {
    "question", "claim", "evidence", "source", "concept", "entity", "event",
    "method", "result", "uncertainty", "counterclaim", "inference", "context",
}
RELATION_KINDS = {
    "supports", "contradicts", "qualifies", "derived-from", "cites", "about",
    "precedes", "causes", "associated-with", "compares-with", "depends-on",
    "explains", "relates-to",
}
VIEW_KINDS = {
    "evidence-map", "argument-map", "concept-map", "source-trace", "timeline",
    "comparison", "linked-explanation", "custom",
}
TARGET_PRODUCTS = {"research-librarian", "lab", "workbench", "site-intelligence", "external"}


def _ser(row):
    out = {}
    for c in row.__table__.columns:
        value = getattr(row, c.name)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        out[c.name] = value
    return out


def _explanation(db: Session, explanation_id: str) -> ResearchVisualExplanationRecord:
    row = db.get(ResearchVisualExplanationRecord, explanation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Research visual explanation not found.")
    return row


def _node(db: Session, explanation_id: str, node_id: str) -> ResearchExplanationNodeRecord:
    row = db.get(ResearchExplanationNodeRecord, node_id)
    if row is None or row.explanation_id != explanation_id:
        raise ValueError("node_id must belong to this explanation.")
    return row


def readiness(db: Session) -> dict[str, Any]:
    counts = {
        "explanations": int(db.scalar(select(func.count()).select_from(ResearchVisualExplanationRecord)) or 0),
        "nodes": int(db.scalar(select(func.count()).select_from(ResearchExplanationNodeRecord)) or 0),
        "relations": int(db.scalar(select(func.count()).select_from(ResearchExplanationRelationRecord)) or 0),
        "citations": int(db.scalar(select(func.count()).select_from(ResearchExplanationCitationRecord)) or 0),
        "views": int(db.scalar(select(func.count()).select_from(ResearchExplanationViewRecord)) or 0),
        "snapshots": int(db.scalar(select(func.count()).select_from(ResearchExplanationSnapshotRecord)) or 0),
    }
    return {
        "migration_0043_applied": True,
        "citation_aware_explanations": True,
        "evidence_ledger_bindings": True,
        "immutable_explanation_snapshots": True,
        "renderer_neutral": True,
        "research_librarian_handoff": True,
        "source_retrieval_by_core": False,
        "natural_language_generation_by_core": False,
        "citation_selection_by_core": False,
        "source_ranking_by_core": False,
        "layout_execution_by_core": False,
        "renderer_execution_by_core": False,
        "automatic_truth_promotion": False,
        "counts": counts,
    }


def create_explanation(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    project_id = str(payload.get("project_entity_id") or "")
    project = db.get(Entity, project_id)
    if project is None or project.entity_type != "research-project":
        raise ValueError("project_entity_id must reference a research-project.")
    subject_id = payload.get("research_subject_entity_id")
    if subject_id and db.get(Entity, subject_id) is None:
        raise ValueError("research_subject_entity_id must reference an existing Core entity.")
    kind = str(payload.get("explanation_kind") or "evidence-map")
    if kind not in EXPLANATION_KINDS:
        raise ValueError("Unsupported explanation_kind.")
    row = ResearchVisualExplanationRecord(
        explanation_key=str(payload.get("explanation_key") or "visual-explanation"),
        name=str(payload.get("name") or "Research visual explanation"),
        question=payload.get("question"),
        summary=payload.get("summary"),
        explanation_kind=kind,
        explanation_state=str(payload.get("explanation_state") or "draft"),
        visibility=str(payload.get("visibility") or "private"),
        audience=str(payload.get("audience") or "general"),
        project_entity_id=project_id,
        research_subject_entity_id=subject_id,
        visual_entity_id=payload.get("visual_entity_id"),
        source_scope_json=dict(payload.get("source_scope") or {}),
        provenance_json=dict(payload.get("provenance") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
        created_by=str(payload.get("created_by") or "operator"),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Explanation key already exists in this research project.") from exc
    return _ser(row)


def list_explanations(
    db: Session, *, project_entity_id: str | None = None, explanation_kind: str | None = None,
    public_only: bool = False, limit: int = 100, offset: int = 0,
):
    q = select(ResearchVisualExplanationRecord)
    cq = select(func.count()).select_from(ResearchVisualExplanationRecord)
    filters = []
    if project_entity_id:
        filters.append(ResearchVisualExplanationRecord.project_entity_id == project_entity_id)
    if explanation_kind:
        filters.append(ResearchVisualExplanationRecord.explanation_kind == explanation_kind)
    if public_only:
        filters.append(ResearchVisualExplanationRecord.visibility == "public")
    for condition in filters:
        q = q.where(condition); cq = cq.where(condition)
    total = int(db.scalar(cq) or 0)
    rows = db.scalars(q.order_by(ResearchVisualExplanationRecord.created_at.desc()).limit(limit).offset(offset)).all()
    return [_ser(row) for row in rows], total


def read_explanation(db: Session, explanation_id: str, *, public_only: bool = False):
    row = _explanation(db, explanation_id)
    if public_only and row.visibility != "public":
        raise HTTPException(status_code=404, detail="Research visual explanation not found.")
    return _ser(row)


def add_node(db: Session, explanation_id: str, payload: dict[str, Any]):
    _explanation(db, explanation_id)
    kind = str(payload.get("node_kind") or "concept")
    if kind not in NODE_KINDS:
        raise ValueError("Unsupported node_kind.")
    bound_entity_id = payload.get("bound_entity_id")
    if bound_entity_id and db.get(Entity, bound_entity_id) is None:
        raise ValueError("bound_entity_id must reference an existing Core entity.")
    confidence = payload.get("confidence")
    if confidence is not None and not 0 <= float(confidence) <= 1:
        raise ValueError("confidence must be between 0 and 1.")
    row = ResearchExplanationNodeRecord(
        explanation_id=explanation_id,
        node_key=str(payload.get("node_key") or kind),
        node_kind=kind,
        label=str(payload.get("label") or payload.get("node_key") or kind),
        body=payload.get("body"),
        bound_entity_id=bound_entity_id,
        visual_element_id=payload.get("visual_element_id"),
        confidence=float(confidence) if confidence is not None else None,
        sequence_position=int(payload.get("sequence_position") or 0),
        citation_required=bool(payload.get("citation_required", False)),
        visual_role=str(payload.get("visual_role") or "content"),
        provenance_json=dict(payload.get("provenance") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Explanation node key already exists.") from exc
    return _ser(row)


def add_relation(db: Session, explanation_id: str, payload: dict[str, Any]):
    _explanation(db, explanation_id)
    source = _node(db, explanation_id, str(payload.get("source_node_id") or ""))
    target = _node(db, explanation_id, str(payload.get("target_node_id") or ""))
    if source.id == target.id:
        raise ValueError("Self-relations are not permitted in a visual explanation.")
    kind = str(payload.get("relation_kind") or "relates-to")
    if kind not in RELATION_KINDS:
        raise ValueError("Unsupported relation_kind.")
    strength = payload.get("strength")
    if strength is not None and not 0 <= float(strength) <= 1:
        raise ValueError("strength must be between 0 and 1.")
    row = ResearchExplanationRelationRecord(
        explanation_id=explanation_id,
        relation_key=str(payload.get("relation_key") or f"{source.node_key}-{kind}-{target.node_key}"),
        source_node_id=source.id,
        target_node_id=target.id,
        relation_kind=kind,
        label=payload.get("label"),
        strength=float(strength) if strength is not None else None,
        rationale=payload.get("rationale"),
        provenance_json=dict(payload.get("provenance") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Explanation relation key already exists.") from exc
    return _ser(row)


def add_citation(db: Session, explanation_id: str, payload: dict[str, Any]):
    _explanation(db, explanation_id)
    node_id = payload.get("node_id")
    if node_id:
        _node(db, explanation_id, str(node_id))
    evidence_id = payload.get("evidence_id")
    snapshot_id = payload.get("source_snapshot_id")
    source_entity_id = payload.get("source_entity_id")
    external_uri = payload.get("external_uri")
    if evidence_id and db.get(EvidenceRecord, evidence_id) is None:
        raise ValueError("evidence_id must reference an existing Evidence Ledger record.")
    if snapshot_id and db.get(SourceSnapshot, snapshot_id) is None:
        raise ValueError("source_snapshot_id must reference an existing source snapshot.")
    if source_entity_id and db.get(Entity, source_entity_id) is None:
        raise ValueError("source_entity_id must reference an existing Core entity.")
    if not any([evidence_id, snapshot_id, source_entity_id, external_uri]):
        raise ValueError("A citation requires evidence_id, source_snapshot_id, source_entity_id, or external_uri.")
    locator = dict(payload.get("locator") or {})
    if not locator:
        raise ValueError("A citation requires an explicit locator (page, section, timestamp, record, or equivalent).")
    row = ResearchExplanationCitationRecord(
        explanation_id=explanation_id,
        citation_key=str(payload.get("citation_key") or "citation"),
        node_id=node_id,
        evidence_id=evidence_id,
        source_snapshot_id=snapshot_id,
        source_entity_id=source_entity_id,
        external_uri=str(external_uri) if external_uri else None,
        citation_label=payload.get("citation_label"),
        locator_json=locator,
        note=payload.get("note"),
        provenance_json=dict(payload.get("provenance") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Explanation citation key already exists.") from exc
    return _ser(row)


def add_view(db: Session, explanation_id: str, payload: dict[str, Any]):
    _explanation(db, explanation_id)
    kind = str(payload.get("view_kind") or "evidence-map")
    if kind not in VIEW_KINDS:
        raise ValueError("Unsupported view_kind.")
    focus_ids = list(payload.get("focus_node_ids") or [])
    for node_id in focus_ids:
        _node(db, explanation_id, str(node_id))
    row = ResearchExplanationViewRecord(
        explanation_id=explanation_id,
        view_key=str(payload.get("view_key") or kind),
        name=str(payload.get("name") or kind.replace("-", " ").title()),
        view_kind=kind,
        renderer_contract=str(payload.get("renderer_contract") or "contract.d3"),
        focus_node_ids_json=focus_ids,
        layer_config_json=list(payload.get("layers") or []),
        layout_hints_json=dict(payload.get("layout_hints") or {}),
        legend_json=dict(payload.get("legend") or {}),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Explanation view key already exists.") from exc
    return _ser(row)


def citation_coverage(db: Session, explanation_id: str):
    _explanation(db, explanation_id)
    nodes = db.scalars(select(ResearchExplanationNodeRecord).where(ResearchExplanationNodeRecord.explanation_id == explanation_id)).all()
    citations = db.scalars(select(ResearchExplanationCitationRecord).where(ResearchExplanationCitationRecord.explanation_id == explanation_id)).all()
    cited = {row.node_id for row in citations if row.node_id}
    required = [row.id for row in nodes if row.citation_required]
    uncovered = [node_id for node_id in required if node_id not in cited]
    return {
        "explanation_id": explanation_id,
        "citation_required_node_count": len(required),
        "cited_required_node_count": len(required) - len(uncovered),
        "uncovered_required_node_ids": uncovered,
        "coverage_complete": not uncovered,
        "citation_selection_by_core": False,
        "source_ranking_by_core": False,
    }


def visualization_spec(db: Session, explanation_id: str, view_id: str | None = None, *, public_only: bool = False):
    explanation = read_explanation(db, explanation_id, public_only=public_only)
    nodes = db.scalars(select(ResearchExplanationNodeRecord).where(ResearchExplanationNodeRecord.explanation_id == explanation_id).order_by(ResearchExplanationNodeRecord.sequence_position, ResearchExplanationNodeRecord.created_at)).all()
    relations = db.scalars(select(ResearchExplanationRelationRecord).where(ResearchExplanationRelationRecord.explanation_id == explanation_id)).all()
    citations = db.scalars(select(ResearchExplanationCitationRecord).where(ResearchExplanationCitationRecord.explanation_id == explanation_id)).all()
    view = None
    if view_id:
        view = db.get(ResearchExplanationViewRecord, view_id)
        if view is None or view.explanation_id != explanation_id:
            raise ValueError("view_id must belong to this explanation.")
    if view is None:
        view = db.scalar(select(ResearchExplanationViewRecord).where(ResearchExplanationViewRecord.explanation_id == explanation_id).order_by(ResearchExplanationViewRecord.created_at))
    citation_by_node: dict[str, list[str]] = {}
    for citation in citations:
        if citation.node_id:
            citation_by_node.setdefault(citation.node_id, []).append(citation.id)
    return {
        "contract": "sc.research-librarian-visual-explanation.v1",
        "explanation_id": explanation_id,
        "question": explanation.get("question"),
        "explanation_kind": explanation["explanation_kind"],
        "visual_kind": view.view_kind if view else explanation["explanation_kind"],
        "renderer_contract": view.renderer_contract if view else "contract.d3",
        "nodes": [dict(_ser(node), citation_ids=citation_by_node.get(node.id, [])) for node in nodes],
        "relations": [_ser(relation) for relation in relations],
        "citations": [_ser(citation) for citation in citations],
        "coverage": citation_coverage(db, explanation_id),
        "view": _ser(view) if view else None,
        "renderer_neutral": True,
        "layout_execution_by_core": False,
        "renderer_execution_by_core": False,
        "source_retrieval_by_core": False,
        "natural_language_generation_by_core": False,
        "citation_selection_by_core": False,
        "source_ranking_by_core": False,
        "automatic_truth_promotion": False,
    }


def _snapshot_state(db: Session, explanation_id: str):
    explanation = read_explanation(db, explanation_id)
    nodes = db.scalars(select(ResearchExplanationNodeRecord).where(ResearchExplanationNodeRecord.explanation_id == explanation_id).order_by(ResearchExplanationNodeRecord.sequence_position, ResearchExplanationNodeRecord.id)).all()
    relations = db.scalars(select(ResearchExplanationRelationRecord).where(ResearchExplanationRelationRecord.explanation_id == explanation_id).order_by(ResearchExplanationRelationRecord.id)).all()
    citations = db.scalars(select(ResearchExplanationCitationRecord).where(ResearchExplanationCitationRecord.explanation_id == explanation_id).order_by(ResearchExplanationCitationRecord.id)).all()
    views = db.scalars(select(ResearchExplanationViewRecord).where(ResearchExplanationViewRecord.explanation_id == explanation_id).order_by(ResearchExplanationViewRecord.id)).all()
    return {
        "contract": "sc.research-librarian-visual-explanation-snapshot.v1",
        "explanation": explanation,
        "nodes": [_ser(row) for row in nodes],
        "relations": [_ser(row) for row in relations],
        "citations": [_ser(row) for row in citations],
        "views": [_ser(row) for row in views],
        "coverage": citation_coverage(db, explanation_id),
    }


def create_snapshot(db: Session, explanation_id: str, payload: dict[str, Any]):
    _explanation(db, explanation_id)
    state = _snapshot_state(db, explanation_id)
    encoded = json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    current = db.scalar(select(func.max(ResearchExplanationSnapshotRecord.revision)).where(ResearchExplanationSnapshotRecord.explanation_id == explanation_id))
    revision = int(current or 0) + 1
    row = ResearchExplanationSnapshotRecord(
        explanation_id=explanation_id,
        revision=revision,
        content_hash=digest,
        state_json=state,
        provenance_json=dict(payload.get("provenance") or {}),
        created_by=str(payload.get("created_by") or "operator"),
    )
    db.add(row); db.commit(); db.refresh(row)
    return _ser(row)


def runtime_handoff(db: Session, explanation_id: str, payload: dict[str, Any]):
    explanation = _explanation(db, explanation_id)
    target = str(payload.get("target_product") or "research-librarian")
    if target not in TARGET_PRODUCTS:
        raise ValueError("target_product must be research-librarian, lab, workbench, site-intelligence, or external.")
    if payload.get("execute_by_core") is True:
        raise ValueError("Platform Core does not execute Research Librarian retrieval, synthesis, model analysis, layout, or rendering.")
    return {
        "contract": "sc.research-visual-explanation-handoff.v1",
        "explanation_id": explanation_id,
        "project_entity_id": explanation.project_entity_id,
        "target_product": target,
        "operation": str(payload.get("operation") or "explain-research"),
        "input_manifest": dict(payload.get("input_manifest") or {}),
        "requested_outputs": list(payload.get("requested_outputs") or ["evidence-bindings", "visual-explanation-spec"]),
        "source_retrieval_by_core": False,
        "natural_language_generation_by_core": False,
        "model_execution_by_core": False,
        "layout_execution_by_core": False,
        "renderer_execution_by_core": False,
        "automatic_truth_promotion": False,
    }


def bundle(db: Session, explanation_id: str, *, public_only: bool = False):
    explanation = read_explanation(db, explanation_id, public_only=public_only)
    nodes = db.scalars(select(ResearchExplanationNodeRecord).where(ResearchExplanationNodeRecord.explanation_id == explanation_id).order_by(ResearchExplanationNodeRecord.sequence_position, ResearchExplanationNodeRecord.created_at)).all()
    relations = db.scalars(select(ResearchExplanationRelationRecord).where(ResearchExplanationRelationRecord.explanation_id == explanation_id)).all()
    citations = db.scalars(select(ResearchExplanationCitationRecord).where(ResearchExplanationCitationRecord.explanation_id == explanation_id)).all()
    views = db.scalars(select(ResearchExplanationViewRecord).where(ResearchExplanationViewRecord.explanation_id == explanation_id)).all()
    snapshots = db.scalars(select(ResearchExplanationSnapshotRecord).where(ResearchExplanationSnapshotRecord.explanation_id == explanation_id).order_by(ResearchExplanationSnapshotRecord.revision.desc())).all()
    return {
        "explanation": explanation,
        "nodes": [_ser(row) for row in nodes],
        "relations": [_ser(row) for row in relations],
        "citations": [_ser(row) for row in citations],
        "views": [_ser(row) for row in views],
        "snapshots": [_ser(row) for row in snapshots],
        "coverage": citation_coverage(db, explanation_id),
        "visualization": visualization_spec(db, explanation_id, public_only=public_only),
        "boundaries": {
            "renderer_neutral": True,
            "source_retrieval_by_core": False,
            "natural_language_generation_by_core": False,
            "citation_selection_by_core": False,
            "source_ranking_by_core": False,
            "layout_execution_by_core": False,
            "renderer_execution_by_core": False,
            "automatic_truth_promotion": False,
        },
    }
