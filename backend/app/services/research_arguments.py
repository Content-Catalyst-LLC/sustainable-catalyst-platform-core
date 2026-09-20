from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json

from sqlalchemy import func, select
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session

from ..models import (
    UnifiedResearchProjectProfileRecord,
    ResearchArgumentRecord,
    ResearchArgumentNodeRecord,
    ResearchArgumentEdgeRecord,
    ResearchEvidentiarySynthesisRecord,
    ResearchSynthesisComponentRecord,
    ResearchCounterargumentRecord,
    ResearchArgumentTensionRecord,
    ResearchArgumentRevisionRecord,
    ResearchArgumentSnapshotRecord,
)

CONTRACT = "sc.research.argument-evidentiary-synthesis.v1"

ARGUMENT_TYPES = {"analytical", "explanatory", "comparative", "causal", "interpretive", "methodological"}
ARGUMENT_STATUSES = {"draft", "active", "revised", "archived"}
NODE_TYPES = {"evidence", "finding", "interpretation", "claim", "hypothesis", "assumption", "counterclaim", "limitation", "context", "method"}
NODE_ROLES = {"premise", "support", "objection", "qualifier", "conclusion", "context", "gap"}
EDGE_RELATIONS = {"supports", "contradicts", "qualifies", "depends_on", "contextualizes", "responds_to", "derived_from", "is_relevant_to"}
SYNTHESIS_TYPES = {"evidentiary", "narrative", "thematic", "comparative", "integrative"}
SYNTHESIS_STATUSES = {"draft", "active", "superseded", "archived"}
COMPONENT_ROLES = {"primary_evidence", "supporting_evidence", "contradictory_evidence", "context", "limitation", "method", "finding", "claim", "hypothesis"}
COUNTERARGUMENT_STATUSES = {"open", "addressed", "unresolved", "withdrawn"}
TENSION_STATUSES = {"open", "contextualized", "resolved_by_researcher", "external"}

FORBIDDEN = {
    "generate_argument_by_core",
    "generate_synthesis_by_core",
    "infer_argument_relation_by_core",
    "score_evidence_by_core",
    "rank_arguments_by_core",
    "select_best_argument_by_core",
    "resolve_tensions_by_core",
    "infer_truth_by_core",
    "publish_by_core",
}

CLASSES = [
    ResearchArgumentRecord,
    ResearchArgumentNodeRecord,
    ResearchArgumentEdgeRecord,
    ResearchEvidentiarySynthesisRecord,
    ResearchSynthesisComponentRecord,
    ResearchCounterargumentRecord,
    ResearchArgumentTensionRecord,
    ResearchArgumentRevisionRecord,
    ResearchArgumentSnapshotRecord,
]
COUNT_NAMES = [
    "arguments",
    "nodes",
    "edges",
    "syntheses",
    "synthesis_components",
    "counterarguments",
    "tensions",
    "argument_revisions",
    "snapshots",
]


def _ser(record):
    out = {}
    for attr in sa_inspect(record).mapper.column_attrs:
        value = getattr(record, attr.key)
        out[attr.key] = value.isoformat() if isinstance(value, datetime) else value
    for key in list(out):
        if key.endswith("_json"):
            out[key[:-5]] = out.pop(key)
    return out


def _hash(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def _reject(payload: dict) -> None:
    bad = sorted(key for key in FORBIDDEN if payload.get(key) not in (None, False))
    if bad:
        raise ValueError(
            "Research Argument & Evidentiary Synthesis is researcher-directed; Core does not generate arguments/syntheses, "
            "infer relations, score evidence, rank/select arguments, resolve tensions, infer truth, or publish: "
            + ", ".join(bad)
        )


def boundaries() -> dict:
    return {
        "argument_registry_by_core": True,
        "declared_argument_graph_by_core": True,
        "researcher_authored_synthesis_registry_by_core": True,
        "counterargument_registry_by_core": True,
        "unresolved_tension_registry_by_core": True,
        "descriptive_coverage_summary_by_core": True,
        "argument_version_history_by_core": True,
        "immutable_argument_snapshots_by_core": True,
        "generate_argument_by_core": False,
        "generate_synthesis_by_core": False,
        "infer_argument_relation_by_core": False,
        "score_evidence_by_core": False,
        "rank_arguments_by_core": False,
        "select_best_argument_by_core": False,
        "resolve_tensions_by_core": False,
        "infer_truth_by_core": False,
        "publish_by_core": False,
    }


def readiness(db: Session) -> dict:
    count = lambda cls: int(db.scalar(select(func.count()).select_from(cls)) or 0)
    return {
        "release": "2.79.0",
        "contract": CONTRACT,
        "argument_types": sorted(ARGUMENT_TYPES),
        "argument_statuses": sorted(ARGUMENT_STATUSES),
        "node_types": sorted(NODE_TYPES),
        "node_roles": sorted(NODE_ROLES),
        "edge_relations": sorted(EDGE_RELATIONS),
        "synthesis_types": sorted(SYNTHESIS_TYPES),
        "component_roles": sorted(COMPONENT_ROLES),
        "counts": dict(zip(COUNT_NAMES, [count(cls) for cls in CLASSES])),
        **boundaries(),
    }


def _project(db: Session, project_id: str):
    record = db.get(UnifiedResearchProjectProfileRecord, project_id)
    if record is None:
        raise ValueError("project_entity_id must reference a v2.72 unified research project profile.")
    return record


def _argument(db: Session, argument_id: str):
    record = db.get(ResearchArgumentRecord, argument_id)
    if record is None:
        raise ValueError("research argument not found.")
    return record


def _node(db: Session, node_id: str):
    record = db.get(ResearchArgumentNodeRecord, node_id)
    if record is None:
        raise ValueError("research argument node not found.")
    return record


def _synthesis(db: Session, synthesis_id: str):
    record = db.get(ResearchEvidentiarySynthesisRecord, synthesis_id)
    if record is None:
        raise ValueError("evidentiary synthesis not found.")
    return record


def create_argument(db: Session, project_id: str, payload: dict) -> dict:
    _reject(payload)
    _project(db, project_id)
    title = str(payload.get("title") or "").strip()
    key = str(payload.get("argument_key") or "").strip()
    if not title or not key:
        raise ValueError("argument_key and title are required.")
    argument_type = payload.get("argument_type", "analytical")
    status = payload.get("status", "draft")
    if argument_type not in ARGUMENT_TYPES:
        raise ValueError("unsupported argument_type: " + argument_type)
    if status not in ARGUMENT_STATUSES:
        raise ValueError("unsupported argument status: " + status)
    record = ResearchArgumentRecord(
        project_entity_id=project_id,
        argument_key=key,
        title=title,
        thesis_text=payload.get("thesis_text"),
        central_claim_ref=payload.get("central_claim_ref"),
        argument_type=argument_type,
        status=status,
        scope_json=payload.get("scope", {}),
        limitations_json=payload.get("limitations", []),
        metadata_json=payload.get("metadata", {}),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ser(record)


def revise_argument(db: Session, argument_id: str, payload: dict) -> dict:
    _reject(payload)
    record = _argument(db, argument_id)
    prior = _ser(record)
    allowed = {"title", "thesis_text", "central_claim_ref", "argument_type", "status", "scope", "limitations", "metadata", "provenance"}
    unknown = set(payload) - allowed - {"change_summary", "created_by"} - FORBIDDEN
    if unknown:
        raise ValueError("unsupported argument revision field: " + sorted(unknown)[0])
    if "argument_type" in payload and payload["argument_type"] not in ARGUMENT_TYPES:
        raise ValueError("unsupported argument_type: " + payload["argument_type"])
    if "status" in payload and payload["status"] not in ARGUMENT_STATUSES:
        raise ValueError("unsupported argument status: " + payload["status"])
    mapping = {"scope": "scope_json", "limitations": "limitations_json", "metadata": "metadata_json", "provenance": "provenance_json"}
    for key in allowed:
        if key in payload:
            setattr(record, mapping.get(key, key), payload[key])
    if not str(record.title or "").strip():
        raise ValueError("title is required.")
    db.flush()
    revised = _ser(record)
    previous = db.scalar(
        select(ResearchArgumentRevisionRecord)
        .where(ResearchArgumentRevisionRecord.argument_id == argument_id)
        .order_by(ResearchArgumentRevisionRecord.revision.desc())
        .limit(1)
    )
    revision = 1 if previous is None else previous.revision + 1
    rev = ResearchArgumentRevisionRecord(
        argument_id=argument_id,
        project_entity_id=record.project_entity_id,
        revision=revision,
        state_hash=_hash(revised),
        prior_state_json=prior,
        revised_state_json=revised,
        change_summary=payload.get("change_summary"),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(rev)
    db.commit()
    db.refresh(rev)
    return _ser(rev)


def add_node(db: Session, argument_id: str, payload: dict) -> dict:
    _reject(payload)
    argument = _argument(db, argument_id)
    node_type = payload.get("node_type")
    role = payload.get("role", "context")
    if node_type not in NODE_TYPES:
        raise ValueError("unsupported node_type: " + str(node_type))
    if role not in NODE_ROLES:
        raise ValueError("unsupported node role: " + role)
    if not str(payload.get("node_key") or "").strip():
        raise ValueError("node_key is required.")
    if not str(payload.get("source_ref") or "").strip() and not str(payload.get("statement_text") or "").strip():
        raise ValueError("a node requires source_ref or statement_text.")
    record = ResearchArgumentNodeRecord(
        project_entity_id=argument.project_entity_id,
        argument_id=argument_id,
        node_key=payload["node_key"],
        node_type=node_type,
        role=role,
        source_ref=payload.get("source_ref"),
        statement_text=payload.get("statement_text"),
        citation_refs_json=payload.get("citation_refs", []),
        uncertainty_json=payload.get("uncertainty", {}),
        metadata_json=payload.get("metadata", {}),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ser(record)


def add_edge(db: Session, argument_id: str, payload: dict) -> dict:
    _reject(payload)
    argument = _argument(db, argument_id)
    source = _node(db, payload["source_node_id"])
    target = _node(db, payload["target_node_id"])
    if source.argument_id != argument_id or target.argument_id != argument_id:
        raise ValueError("both nodes must belong to the supplied argument.")
    if source.id == target.id:
        raise ValueError("an argument edge cannot be self-referential.")
    relation = payload.get("relation")
    if relation not in EDGE_RELATIONS:
        raise ValueError("unsupported argument relation: " + str(relation))
    record = ResearchArgumentEdgeRecord(
        project_entity_id=argument.project_entity_id,
        argument_id=argument_id,
        edge_key=payload["edge_key"],
        source_node_id=source.id,
        target_node_id=target.id,
        relation=relation,
        rationale=payload.get("rationale"),
        evidence_refs_json=payload.get("evidence_refs", []),
        metadata_json=payload.get("metadata", {}),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ser(record)


def create_synthesis(db: Session, argument_id: str, payload: dict) -> dict:
    _reject(payload)
    argument = _argument(db, argument_id)
    synthesis_type = payload.get("synthesis_type", "evidentiary")
    status = payload.get("status", "draft")
    if synthesis_type not in SYNTHESIS_TYPES:
        raise ValueError("unsupported synthesis_type: " + synthesis_type)
    if status not in SYNTHESIS_STATUSES:
        raise ValueError("unsupported synthesis status: " + status)
    if not str(payload.get("title") or "").strip() or not str(payload.get("synthesis_text") or "").strip():
        raise ValueError("title and researcher-authored synthesis_text are required.")
    record = ResearchEvidentiarySynthesisRecord(
        project_entity_id=argument.project_entity_id,
        argument_id=argument_id,
        synthesis_key=payload["synthesis_key"],
        title=payload["title"],
        synthesis_type=synthesis_type,
        status=status,
        synthesis_text=payload["synthesis_text"],
        scope_json=payload.get("scope", {}),
        uncertainty_json=payload.get("uncertainty", {}),
        limitations_json=payload.get("limitations", []),
        metadata_json=payload.get("metadata", {}),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ser(record)


def add_synthesis_component(db: Session, synthesis_id: str, payload: dict) -> dict:
    _reject(payload)
    synthesis = _synthesis(db, synthesis_id)
    role = payload.get("role", "context")
    if role not in COMPONENT_ROLES:
        raise ValueError("unsupported synthesis component role: " + role)
    if not str(payload.get("source_ref") or "").strip() or not str(payload.get("source_type") or "").strip():
        raise ValueError("source_type and source_ref are required.")
    record = ResearchSynthesisComponentRecord(
        project_entity_id=synthesis.project_entity_id,
        synthesis_id=synthesis_id,
        component_key=payload["component_key"],
        source_type=payload["source_type"],
        source_ref=payload["source_ref"],
        role=role,
        locator=payload.get("locator"),
        researcher_note=payload.get("researcher_note"),
        uncertainty_json=payload.get("uncertainty", {}),
        metadata_json=payload.get("metadata", {}),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ser(record)


def add_counterargument(db: Session, argument_id: str, payload: dict) -> dict:
    _reject(payload)
    argument = _argument(db, argument_id)
    status = payload.get("status", "open")
    if status not in COUNTERARGUMENT_STATUSES:
        raise ValueError("unsupported counterargument status: " + status)
    responds_to = payload.get("responds_to_node_id")
    if responds_to:
        node = _node(db, responds_to)
        if node.argument_id != argument_id:
            raise ValueError("responds_to_node_id must belong to the supplied argument.")
    if not str(payload.get("statement_text") or "").strip():
        raise ValueError("statement_text is required.")
    record = ResearchCounterargumentRecord(
        project_entity_id=argument.project_entity_id,
        argument_id=argument_id,
        counterargument_key=payload["counterargument_key"],
        statement_text=payload["statement_text"],
        responds_to_node_id=responds_to,
        status=status,
        evidence_refs_json=payload.get("evidence_refs", []),
        response_text=payload.get("response_text"),
        limitations_json=payload.get("limitations", []),
        metadata_json=payload.get("metadata", {}),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ser(record)


def add_tension(db: Session, argument_id: str, payload: dict) -> dict:
    _reject(payload)
    argument = _argument(db, argument_id)
    status = payload.get("status", "open")
    if status not in TENSION_STATUSES:
        raise ValueError("unsupported tension status: " + status)
    if not str(payload.get("title") or "").strip() or not str(payload.get("description") or "").strip():
        raise ValueError("title and description are required.")
    record = ResearchArgumentTensionRecord(
        project_entity_id=argument.project_entity_id,
        argument_id=argument_id,
        tension_key=payload["tension_key"],
        title=payload["title"],
        description=payload["description"],
        source_refs_json=payload.get("source_refs", []),
        status=status,
        researcher_resolution_note=payload.get("researcher_resolution_note"),
        metadata_json=payload.get("metadata", {}),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ser(record)


def argument_map(db: Session, argument_id: str, public: bool = False) -> dict:
    argument = _argument(db, argument_id)
    project = _project(db, argument.project_entity_id)
    if public and project.visibility != "public":
        raise ValueError("research project is not public.")
    nodes = list(db.scalars(select(ResearchArgumentNodeRecord).where(ResearchArgumentNodeRecord.argument_id == argument_id)).all())
    edges = list(db.scalars(select(ResearchArgumentEdgeRecord).where(ResearchArgumentEdgeRecord.argument_id == argument_id)).all())
    counterarguments = list(db.scalars(select(ResearchCounterargumentRecord).where(ResearchCounterargumentRecord.argument_id == argument_id)).all())
    tensions = list(db.scalars(select(ResearchArgumentTensionRecord).where(ResearchArgumentTensionRecord.argument_id == argument_id)).all())
    node_types = Counter(item.node_type for item in nodes)
    node_roles = Counter(item.role for item in nodes)
    edge_relations = Counter(item.relation for item in edges)
    return {
        "release": "2.79.0",
        "contract": CONTRACT,
        "argument": _ser(argument),
        "nodes": [_ser(item) for item in nodes],
        "edges": [_ser(item) for item in edges],
        "descriptive_coverage": {
            "node_type_counts": dict(sorted(node_types.items())),
            "node_role_counts": dict(sorted(node_roles.items())),
            "edge_relation_counts": dict(sorted(edge_relations.items())),
            "counterargument_count": len(counterarguments),
            "open_tension_count": sum(1 for item in tensions if item.status == "open"),
        },
        "coverage_is_descriptive_only": True,
        "evidence_scores_computed": False,
        "argument_ranking_computed": False,
        "truth_determination_performed": False,
    }


def bundle(db: Session, argument_id: str, public: bool = False) -> dict:
    argument = _argument(db, argument_id)
    project = _project(db, argument.project_entity_id)
    if public and project.visibility != "public":
        raise ValueError("research project is not public.")

    def rows(cls, field="argument_id"):
        return [_ser(item) for item in db.scalars(select(cls).where(getattr(cls, field) == argument_id)).all()]

    syntheses = rows(ResearchEvidentiarySynthesisRecord)
    synthesis_ids = [item["id"] for item in syntheses]
    components = [] if not synthesis_ids else [
        _ser(item) for item in db.scalars(
            select(ResearchSynthesisComponentRecord).where(ResearchSynthesisComponentRecord.synthesis_id.in_(synthesis_ids))
        ).all()
    ]
    return {
        "release": "2.79.0",
        "contract": CONTRACT,
        "project": _ser(project),
        "argument": _ser(argument),
        "nodes": rows(ResearchArgumentNodeRecord),
        "edges": rows(ResearchArgumentEdgeRecord),
        "syntheses": syntheses,
        "synthesis_components": components,
        "counterarguments": rows(ResearchCounterargumentRecord),
        "tensions": rows(ResearchArgumentTensionRecord),
        "argument_revisions": rows(ResearchArgumentRevisionRecord),
        "snapshots": rows(ResearchArgumentSnapshotRecord),
        "argument_map": argument_map(db, argument_id, public),
        **boundaries(),
    }


def _state(db: Session, argument_id: str) -> dict:
    state = bundle(db, argument_id)
    state.pop("snapshots", None)
    return state


def snapshot(db: Session, argument_id: str, payload: dict) -> dict:
    _reject(payload)
    argument = _argument(db, argument_id)
    state = _state(db, argument_id)
    content_hash = _hash(state)
    previous = db.scalar(
        select(ResearchArgumentSnapshotRecord)
        .where(ResearchArgumentSnapshotRecord.argument_id == argument_id)
        .order_by(ResearchArgumentSnapshotRecord.revision.desc())
        .limit(1)
    )
    revision = 1 if previous is None else previous.revision + 1
    record = ResearchArgumentSnapshotRecord(
        project_entity_id=argument.project_entity_id,
        argument_id=argument_id,
        revision=revision,
        content_hash=content_hash,
        previous_snapshot_hash=None if previous is None else previous.content_hash,
        state_json=state,
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ser(record)
