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
    ResearchHypothesisSetRecord,
    ResearchHypothesisRecord,
    ResearchHypothesisRevisionRecord,
    ResearchHypothesisEvidenceAssessmentRecord,
    ResearchHypothesisPredictionRecord,
    ResearchHypothesisAssumptionRecord,
    ResearchHypothesisRelationRecord,
    ResearchHypothesisDiscriminationGapRecord,
    ResearchHypothesisSnapshotRecord,
)

CONTRACT = "sc.research.hypothesis-competing-explanation.v1"

SET_STATUSES = {"active", "closed", "archived"}
HYPOTHESIS_TYPES = {
    "explanatory", "causal", "mechanistic", "descriptive", "predictive", "null", "alternative"
}
HYPOTHESIS_STATUSES = {"proposed", "active", "qualified", "superseded", "withdrawn"}
EVIDENCE_RELATIONS = {
    "supports", "contradicts", "is_consistent_with", "is_neutral_to", "requires_more_evidence"
}
PREDICTION_STATUSES = {"untested", "observed", "not_observed", "ambiguous", "not_applicable"}
ASSUMPTION_STATUSES = {"active", "qualified", "retired"}
HYPOTHESIS_RELATIONS = {"competes_with", "alternative_to", "compatible_with", "nested_within", "refines"}
GAP_STATUSES = {"open", "partially_addressed", "closed", "external"}

FORBIDDEN = {
    "generate_hypothesis_by_core",
    "score_hypotheses_by_core",
    "rank_hypotheses_by_core",
    "select_best_hypothesis_by_core",
    "confirm_hypothesis_by_core",
    "reject_hypothesis_by_core",
    "infer_evidence_relation_by_core",
    "infer_causality_by_core",
    "infer_truth_by_core",
    "optimize_research_path_by_core",
    "publish_by_core",
}

CLASSES = [
    ResearchHypothesisSetRecord,
    ResearchHypothesisRecord,
    ResearchHypothesisRevisionRecord,
    ResearchHypothesisEvidenceAssessmentRecord,
    ResearchHypothesisPredictionRecord,
    ResearchHypothesisAssumptionRecord,
    ResearchHypothesisRelationRecord,
    ResearchHypothesisDiscriminationGapRecord,
    ResearchHypothesisSnapshotRecord,
]
COUNT_NAMES = [
    "hypothesis_sets",
    "hypotheses",
    "hypothesis_revisions",
    "evidence_assessments",
    "predictions",
    "assumptions",
    "hypothesis_relations",
    "discrimination_gaps",
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
            "Hypothesis & Competing Explanation Engine is descriptive and researcher-directed; "
            "Core does not generate, score, rank, select, confirm, reject, or infer truth/causality/evidence positions: "
            + ", ".join(bad)
        )


def boundaries() -> dict:
    return {
        "hypothesis_registry_by_core": True,
        "competing_explanation_sets_by_core": True,
        "assumption_registry_by_core": True,
        "prediction_registry_by_core": True,
        "explicit_evidence_assessments_by_core": True,
        "declared_hypothesis_relations_by_core": True,
        "declared_discrimination_gaps_by_core": True,
        "descriptive_comparison_matrix_by_core": True,
        "hypothesis_version_history_by_core": True,
        "immutable_hypothesis_snapshots_by_core": True,
        "generate_hypothesis_by_core": False,
        "score_hypotheses_by_core": False,
        "rank_hypotheses_by_core": False,
        "select_best_hypothesis_by_core": False,
        "confirm_hypothesis_by_core": False,
        "reject_hypothesis_by_core": False,
        "infer_evidence_relation_by_core": False,
        "infer_causality_by_core": False,
        "infer_truth_by_core": False,
        "optimize_research_path_by_core": False,
        "publish_by_core": False,
    }


def readiness(db: Session) -> dict:
    count = lambda cls: int(db.scalar(select(func.count()).select_from(cls)) or 0)
    return {
        "release": "2.78.0",
        "contract": CONTRACT,
        "set_statuses": sorted(SET_STATUSES),
        "hypothesis_types": sorted(HYPOTHESIS_TYPES),
        "hypothesis_statuses": sorted(HYPOTHESIS_STATUSES),
        "evidence_relations": sorted(EVIDENCE_RELATIONS),
        "prediction_statuses": sorted(PREDICTION_STATUSES),
        "hypothesis_relations": sorted(HYPOTHESIS_RELATIONS),
        "counts": dict(zip(COUNT_NAMES, [count(cls) for cls in CLASSES])),
        **boundaries(),
    }


def _project(db: Session, project_id: str):
    record = db.get(UnifiedResearchProjectProfileRecord, project_id)
    if record is None:
        raise ValueError("project_entity_id must reference a v2.72 unified research project profile.")
    return record


def _set(db: Session, set_id: str):
    record = db.get(ResearchHypothesisSetRecord, set_id)
    if record is None:
        raise ValueError("hypothesis set not found.")
    return record


def _hypothesis(db: Session, hypothesis_id: str):
    record = db.get(ResearchHypothesisRecord, hypothesis_id)
    if record is None:
        raise ValueError("research hypothesis not found.")
    return record


def _same_project(record, project_id: str):
    if record.project_entity_id != project_id:
        raise ValueError("referenced hypothesis object must belong to the same project.")
    return record


def create_hypothesis_set(db: Session, project_id: str, payload: dict) -> dict:
    _reject(payload)
    _project(db, project_id)
    status = payload.get("status", "active")
    if status not in SET_STATUSES:
        raise ValueError("unsupported hypothesis set status: " + status)
    if not str(payload.get("title") or "").strip():
        raise ValueError("title is required.")
    record = ResearchHypothesisSetRecord(
        project_entity_id=project_id,
        hypothesis_set_key=payload["hypothesis_set_key"],
        title=payload["title"],
        description=payload.get("description"),
        research_question_ref=payload.get("research_question_ref"),
        status=status,
        scope_json=payload.get("scope", {}),
        metadata_json=payload.get("metadata", {}),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ser(record)


def create_hypothesis(db: Session, set_id: str, payload: dict) -> dict:
    _reject(payload)
    hypothesis_set = _set(db, set_id)
    hypothesis_type = payload.get("hypothesis_type", "explanatory")
    status = payload.get("status", "proposed")
    if hypothesis_type not in HYPOTHESIS_TYPES:
        raise ValueError("unsupported hypothesis_type: " + hypothesis_type)
    if status not in HYPOTHESIS_STATUSES:
        raise ValueError("unsupported hypothesis status: " + status)
    if not str(payload.get("title") or "").strip() or not str(payload.get("proposition") or "").strip():
        raise ValueError("title and proposition are required.")
    record = ResearchHypothesisRecord(
        project_entity_id=hypothesis_set.project_entity_id,
        hypothesis_set_id=set_id,
        hypothesis_key=payload["hypothesis_key"],
        title=payload["title"],
        proposition=payload["proposition"],
        explanation_text=payload.get("explanation_text"),
        hypothesis_type=hypothesis_type,
        status=status,
        claim_refs_json=payload.get("claim_refs", []),
        finding_refs_json=payload.get("finding_refs", []),
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


def revise_hypothesis(db: Session, hypothesis_id: str, payload: dict) -> dict:
    _reject(payload)
    record = _hypothesis(db, hypothesis_id)
    prior = _ser(record)
    allowed = {
        "title", "proposition", "explanation_text", "hypothesis_type", "status",
        "claim_refs", "finding_refs", "uncertainty", "limitations", "metadata", "provenance",
    }
    for key in payload:
        if key not in allowed | {"change_summary", "created_by"} and key not in FORBIDDEN:
            raise ValueError("unsupported hypothesis revision field: " + key)
    if "hypothesis_type" in payload and payload["hypothesis_type"] not in HYPOTHESIS_TYPES:
        raise ValueError("unsupported hypothesis_type: " + payload["hypothesis_type"])
    if "status" in payload and payload["status"] not in HYPOTHESIS_STATUSES:
        raise ValueError("unsupported hypothesis status: " + payload["status"])
    mapping = {
        "claim_refs": "claim_refs_json",
        "finding_refs": "finding_refs_json",
        "uncertainty": "uncertainty_json",
        "limitations": "limitations_json",
        "metadata": "metadata_json",
        "provenance": "provenance_json",
    }
    for key in allowed:
        if key in payload:
            setattr(record, mapping.get(key, key), payload[key])
    if not str(record.title or "").strip() or not str(record.proposition or "").strip():
        raise ValueError("title and proposition are required.")
    db.flush()
    revised = _ser(record)
    previous = db.scalar(
        select(ResearchHypothesisRevisionRecord)
        .where(ResearchHypothesisRevisionRecord.hypothesis_id == hypothesis_id)
        .order_by(ResearchHypothesisRevisionRecord.revision.desc())
        .limit(1)
    )
    revision = 1 if previous is None else previous.revision + 1
    revision_record = ResearchHypothesisRevisionRecord(
        hypothesis_id=hypothesis_id,
        project_entity_id=record.project_entity_id,
        revision=revision,
        state_hash=_hash(revised),
        prior_state_json=prior,
        revised_state_json=revised,
        change_summary=payload.get("change_summary"),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(revision_record)
    db.commit()
    db.refresh(revision_record)
    return _ser(revision_record)


def add_evidence_assessment(db: Session, hypothesis_id: str, payload: dict) -> dict:
    _reject(payload)
    hypothesis = _hypothesis(db, hypothesis_id)
    relation = payload["relation"]
    if relation not in EVIDENCE_RELATIONS:
        raise ValueError("unsupported evidence relation: " + relation)
    if not str(payload.get("evidence_ref") or "").strip():
        raise ValueError("evidence_ref is required.")
    record = ResearchHypothesisEvidenceAssessmentRecord(
        project_entity_id=hypothesis.project_entity_id,
        hypothesis_id=hypothesis_id,
        assessment_key=payload["assessment_key"],
        evidence_ref=payload["evidence_ref"],
        evidence_kind=payload.get("evidence_kind", "source"),
        relation=relation,
        declared_strength=payload.get("declared_strength"),
        assessment_basis=payload.get("assessment_basis"),
        uncertainty_json=payload.get("uncertainty", {}),
        metadata_json=payload.get("metadata", {}),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ser(record)


def add_prediction(db: Session, hypothesis_id: str, payload: dict) -> dict:
    _reject(payload)
    hypothesis = _hypothesis(db, hypothesis_id)
    status = payload.get("status", "untested")
    if status not in PREDICTION_STATUSES:
        raise ValueError("unsupported prediction status: " + status)
    if not str(payload.get("statement") or "").strip():
        raise ValueError("prediction statement is required.")
    record = ResearchHypothesisPredictionRecord(
        project_entity_id=hypothesis.project_entity_id,
        hypothesis_id=hypothesis_id,
        prediction_key=payload["prediction_key"],
        statement=payload["statement"],
        expected_observation=payload.get("expected_observation"),
        disconfirming_observation=payload.get("disconfirming_observation"),
        status=status,
        evidence_refs_json=payload.get("evidence_refs", []),
        uncertainty_json=payload.get("uncertainty", {}),
        metadata_json=payload.get("metadata", {}),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ser(record)


def add_assumption(db: Session, hypothesis_id: str, payload: dict) -> dict:
    _reject(payload)
    hypothesis = _hypothesis(db, hypothesis_id)
    status = payload.get("status", "active")
    if status not in ASSUMPTION_STATUSES:
        raise ValueError("unsupported assumption status: " + status)
    if not str(payload.get("assumption_text") or "").strip():
        raise ValueError("assumption_text is required.")
    record = ResearchHypothesisAssumptionRecord(
        project_entity_id=hypothesis.project_entity_id,
        hypothesis_id=hypothesis_id,
        assumption_key=payload["assumption_key"],
        assumption_text=payload["assumption_text"],
        status=status,
        testability=payload.get("testability"),
        basis_refs_json=payload.get("basis_refs", []),
        limitations_json=payload.get("limitations", []),
        metadata_json=payload.get("metadata", {}),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ser(record)


def add_hypothesis_relation(db: Session, set_id: str, payload: dict) -> dict:
    _reject(payload)
    hypothesis_set = _set(db, set_id)
    source = _same_project(_hypothesis(db, payload["source_hypothesis_id"]), hypothesis_set.project_entity_id)
    target = _same_project(_hypothesis(db, payload["target_hypothesis_id"]), hypothesis_set.project_entity_id)
    if source.hypothesis_set_id != set_id or target.hypothesis_set_id != set_id:
        raise ValueError("both hypotheses must belong to the supplied hypothesis set.")
    if source.id == target.id:
        raise ValueError("a hypothesis cannot be related to itself.")
    relationship = payload.get("relationship", "alternative_to")
    if relationship not in HYPOTHESIS_RELATIONS:
        raise ValueError("unsupported hypothesis relationship: " + relationship)
    record = ResearchHypothesisRelationRecord(
        project_entity_id=hypothesis_set.project_entity_id,
        hypothesis_set_id=set_id,
        relation_key=payload["relation_key"],
        source_hypothesis_id=source.id,
        target_hypothesis_id=target.id,
        relationship=relationship,
        rationale=payload.get("rationale"),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ser(record)


def add_discrimination_gap(db: Session, set_id: str, payload: dict) -> dict:
    _reject(payload)
    hypothesis_set = _set(db, set_id)
    status = payload.get("status", "open")
    if status not in GAP_STATUSES:
        raise ValueError("unsupported discrimination gap status: " + status)
    ids = payload.get("hypothesis_ids", [])
    if len(ids) < 2:
        raise ValueError("hypothesis_ids must contain at least two competing hypotheses.")
    for hypothesis_id in ids:
        hypothesis = _same_project(_hypothesis(db, hypothesis_id), hypothesis_set.project_entity_id)
        if hypothesis.hypothesis_set_id != set_id:
            raise ValueError("all discrimination-gap hypotheses must belong to the supplied hypothesis set.")
    if not str(payload.get("title") or "").strip() or not str(payload.get("question") or "").strip():
        raise ValueError("title and question are required.")
    record = ResearchHypothesisDiscriminationGapRecord(
        project_entity_id=hypothesis_set.project_entity_id,
        hypothesis_set_id=set_id,
        gap_key=payload["gap_key"],
        title=payload["title"],
        question=payload["question"],
        hypothesis_ids_json=ids,
        evidence_needed_json=payload.get("evidence_needed", []),
        status=status,
        rationale=payload.get("rationale"),
        metadata_json=payload.get("metadata", {}),
        provenance_json=payload.get("provenance", {}),
        created_by=payload.get("created_by", "operator"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ser(record)


def comparison_matrix(db: Session, set_id: str, public: bool = False) -> dict:
    hypothesis_set = _set(db, set_id)
    project = _project(db, hypothesis_set.project_entity_id)
    if public and project.visibility != "public":
        raise ValueError("research project is not public.")
    hypotheses = list(
        db.scalars(
            select(ResearchHypothesisRecord)
            .where(ResearchHypothesisRecord.hypothesis_set_id == set_id)
            .order_by(ResearchHypothesisRecord.created_at, ResearchHypothesisRecord.id)
        ).all()
    )
    rows = []
    for hypothesis in hypotheses:
        assessments = list(db.scalars(select(ResearchHypothesisEvidenceAssessmentRecord).where(ResearchHypothesisEvidenceAssessmentRecord.hypothesis_id == hypothesis.id)).all())
        predictions = list(db.scalars(select(ResearchHypothesisPredictionRecord).where(ResearchHypothesisPredictionRecord.hypothesis_id == hypothesis.id)).all())
        assumptions = list(db.scalars(select(ResearchHypothesisAssumptionRecord).where(ResearchHypothesisAssumptionRecord.hypothesis_id == hypothesis.id)).all())
        relation_counts = Counter(item.relation for item in assessments)
        prediction_counts = Counter(item.status for item in predictions)
        rows.append({
            "hypothesis_id": hypothesis.id,
            "hypothesis_key": hypothesis.hypothesis_key,
            "title": hypothesis.title,
            "status": hypothesis.status,
            "evidence_relation_counts": {key: relation_counts.get(key, 0) for key in sorted(EVIDENCE_RELATIONS)},
            "prediction_status_counts": {key: prediction_counts.get(key, 0) for key in sorted(PREDICTION_STATUSES)},
            "assumption_count": len(assumptions),
        })
    return {
        "release": "2.78.0",
        "contract": CONTRACT,
        "hypothesis_set": _ser(hypothesis_set),
        "rows": rows,
        "comparison_is_descriptive_only": True,
        "scores_computed": False,
        "ranking_computed": False,
        "winner_selected": False,
        "truth_determination_performed": False,
    }


def bundle(db: Session, set_id: str, public: bool = False) -> dict:
    hypothesis_set = _set(db, set_id)
    project = _project(db, hypothesis_set.project_entity_id)
    if public and project.visibility != "public":
        raise ValueError("research project is not public.")

    def rows(cls, field="hypothesis_set_id"):
        return [_ser(item) for item in db.scalars(select(cls).where(getattr(cls, field) == set_id)).all()]

    hypotheses = rows(ResearchHypothesisRecord)
    hypothesis_ids = [item["id"] for item in hypotheses]

    def by_hypothesis(cls):
        if not hypothesis_ids:
            return []
        return [_ser(item) for item in db.scalars(select(cls).where(cls.hypothesis_id.in_(hypothesis_ids))).all()]

    return {
        "release": "2.78.0",
        "contract": CONTRACT,
        "project": _ser(project),
        "hypothesis_set": _ser(hypothesis_set),
        "hypotheses": hypotheses,
        "hypothesis_revisions": by_hypothesis(ResearchHypothesisRevisionRecord),
        "evidence_assessments": by_hypothesis(ResearchHypothesisEvidenceAssessmentRecord),
        "predictions": by_hypothesis(ResearchHypothesisPredictionRecord),
        "assumptions": by_hypothesis(ResearchHypothesisAssumptionRecord),
        "hypothesis_relations": rows(ResearchHypothesisRelationRecord),
        "discrimination_gaps": rows(ResearchHypothesisDiscriminationGapRecord),
        "snapshots": rows(ResearchHypothesisSnapshotRecord),
        **boundaries(),
    }


def _state(db: Session, set_id: str) -> dict:
    state = bundle(db, set_id)
    state.pop("snapshots", None)
    return state


def snapshot(db: Session, set_id: str, payload: dict) -> dict:
    _reject(payload)
    hypothesis_set = _set(db, set_id)
    state = _state(db, set_id)
    content_hash = _hash(state)
    previous = db.scalar(
        select(ResearchHypothesisSnapshotRecord)
        .where(ResearchHypothesisSnapshotRecord.hypothesis_set_id == set_id)
        .order_by(ResearchHypothesisSnapshotRecord.revision.desc())
        .limit(1)
    )
    revision = 1 if previous is None else previous.revision + 1
    record = ResearchHypothesisSnapshotRecord(
        project_entity_id=hypothesis_set.project_entity_id,
        hypothesis_set_id=set_id,
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
