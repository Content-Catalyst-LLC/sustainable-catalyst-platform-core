from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json

from sqlalchemy import func, select
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session

from ..models import (
    UnifiedResearchProjectProfileRecord, ResearchPublicationRecord,
    ResearchPeerReviewRecord, ResearchPeerReviewCommentRecord, ResearchPeerReviewResponseRecord,
    ResearchReplicationStudyRecord, ResearchReplicationAttemptRecord, ResearchReplicationComparisonRecord,
    ResearchRebuttalRecord, ResearchRebuttalPointRecord, ResearchPeerReviewRevisionRecord,
    ResearchPeerReviewSnapshotRecord,
)

CONTRACT = "sc.research.peer-review-replication-rebuttal.v1"
REVIEW_TYPES = {"peer", "editorial", "methodological", "statistical", "replication", "post_publication", "internal"}
REVIEW_STAGES = {"initial", "revision", "resubmission", "post_publication"}
REVIEW_STATUSES = {"open", "submitted", "responded", "closed", "withdrawn"}
RECOMMENDATIONS = {"accept", "minor_revision", "major_revision", "reject", "undecided", "no_recommendation"}
COMMENT_TYPES = {"general", "methods", "evidence", "analysis", "claim", "citation", "presentation", "ethics", "reproducibility", "other"}
PRIORITIES = {"unspecified", "minor", "major", "critical"}
RESPONSE_DISPOSITIONS = {"responded", "addressed", "partially_addressed", "declined", "clarified", "deferred"}
REPLICATION_TYPES = {"direct", "conceptual", "reanalysis", "reproduction", "robustness", "extension"}
REPLICATION_STATUSES = {"planned", "registered", "in_progress", "completed", "withdrawn", "archived"}
DECLARED_OUTCOMES = {"consistent", "partially_consistent", "divergent", "inconclusive", "not_evaluated"}
DECLARED_RELATIONS = {"consistent", "divergent", "mixed", "inconclusive", "not_comparable"}
REBUTTAL_STATUSES = {"draft", "submitted", "responded", "closed", "withdrawn", "archived"}
FORBIDDEN = {
    "generate_peer_review_by_core", "recommend_acceptance_by_core", "score_manuscript_quality_by_core",
    "infer_replication_success_by_core", "resolve_rebuttal_by_core", "rank_reviewer_arguments_by_core",
    "decide_publication_by_core", "infer_truth_by_core"
}
CLASSES = [ResearchPeerReviewRecord, ResearchPeerReviewCommentRecord, ResearchPeerReviewResponseRecord, ResearchReplicationStudyRecord, ResearchReplicationAttemptRecord, ResearchReplicationComparisonRecord, ResearchRebuttalRecord, ResearchRebuttalPointRecord, ResearchPeerReviewRevisionRecord, ResearchPeerReviewSnapshotRecord]
COUNT_NAMES = ["reviews", "review_comments", "review_responses", "replication_studies", "replication_attempts", "replication_comparisons", "rebuttals", "rebuttal_points", "review_revisions", "snapshots"]

def _ser(record):
    out = {}
    for attr in sa_inspect(record).mapper.column_attrs:
        value = getattr(record, attr.key)
        out[attr.key] = value.isoformat() if isinstance(value, datetime) else value
    for key in list(out):
        if key.endswith("_json"):
            out[key[:-5]] = out.pop(key)
    return out

def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()

def _reject(payload):
    bad = sorted(k for k in FORBIDDEN if payload.get(k) not in (None, False))
    if bad:
        raise ValueError("Core records declared peer-review, replication, and rebuttal evidence; it does not author reviews, score quality, infer replication success, resolve disputes, decide publication, or infer truth: " + ", ".join(bad))

def boundaries():
    return {
        "peer_review_registry_by_core": True,
        "review_comment_response_traceability_by_core": True,
        "declared_reviewer_recommendation_registry_by_core": True,
        "replication_study_registry_by_core": True,
        "replication_attempt_registry_by_core": True,
        "declared_replication_comparison_by_core": True,
        "rebuttal_registry_by_core": True,
        "rebuttal_point_evidence_traceability_by_core": True,
        "review_replication_rebuttal_lineage_by_core": True,
        "review_revision_history_by_core": True,
        "immutable_review_snapshots_by_core": True,
        "generate_peer_review_by_core": False,
        "recommend_acceptance_by_core": False,
        "score_manuscript_quality_by_core": False,
        "infer_replication_success_by_core": False,
        "resolve_rebuttal_by_core": False,
        "rank_reviewer_arguments_by_core": False,
        "decide_publication_by_core": False,
        "infer_truth_by_core": False,
    }

def readiness(db):
    count = lambda cls: int(db.scalar(select(func.count()).select_from(cls)) or 0)
    return {
        "release": "2.82.0", "contract": CONTRACT,
        "review_types": sorted(REVIEW_TYPES), "review_stages": sorted(REVIEW_STAGES),
        "review_statuses": sorted(REVIEW_STATUSES), "declared_recommendations": sorted(RECOMMENDATIONS),
        "comment_types": sorted(COMMENT_TYPES), "priorities": sorted(PRIORITIES),
        "response_dispositions": sorted(RESPONSE_DISPOSITIONS), "replication_types": sorted(REPLICATION_TYPES),
        "replication_statuses": sorted(REPLICATION_STATUSES), "declared_replication_outcomes": sorted(DECLARED_OUTCOMES),
        "declared_comparison_relations": sorted(DECLARED_RELATIONS), "rebuttal_statuses": sorted(REBUTTAL_STATUSES),
        "counts": dict(zip(COUNT_NAMES, [count(c) for c in CLASSES])), **boundaries()
    }

def _publication(db, publication_id):
    p = db.get(ResearchPublicationRecord, publication_id)
    if p is None:
        raise ValueError("publication_id must reference a v2.81 research publication.")
    return p

def _project(db, project_id):
    p = db.get(UnifiedResearchProjectProfileRecord, project_id)
    if p is None:
        raise ValueError("research project not found.")
    return p

def _review(db, review_id):
    r = db.get(ResearchPeerReviewRecord, review_id)
    if r is None:
        raise ValueError("peer review not found.")
    return r

def _study(db, study_id):
    r = db.get(ResearchReplicationStudyRecord, study_id)
    if r is None:
        raise ValueError("replication study not found.")
    return r

def _rebuttal(db, rebuttal_id):
    r = db.get(ResearchRebuttalRecord, rebuttal_id)
    if r is None:
        raise ValueError("rebuttal not found.")
    return r

def create_review(db, publication_id, payload):
    _reject(payload); p = _publication(db, publication_id)
    key = str(payload.get("review_key") or "").strip(); typ = payload.get("review_type", "peer"); stage = payload.get("stage", "initial"); status = payload.get("status", "open"); rec = payload.get("declared_recommendation")
    if not key: raise ValueError("review_key is required.")
    if typ not in REVIEW_TYPES: raise ValueError("unsupported review_type: " + str(typ))
    if stage not in REVIEW_STAGES: raise ValueError("unsupported review stage: " + str(stage))
    if status not in REVIEW_STATUSES: raise ValueError("unsupported review status: " + str(status))
    if rec is not None and rec not in RECOMMENDATIONS: raise ValueError("unsupported declared_recommendation: " + str(rec))
    r = ResearchPeerReviewRecord(project_entity_id=p.project_entity_id, publication_id=publication_id, review_key=key, review_type=typ, stage=stage, status=status, reviewer_role=payload.get("reviewer_role"), reviewer_identity_json=payload.get("reviewer_identity", {}), summary_text=payload.get("summary_text"), declared_recommendation=rec, provenance_json=payload.get("provenance", {}), metadata_json=payload.get("metadata", {}), created_by=payload.get("created_by", "operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_comment(db, review_id, payload):
    _reject(payload); rv = _review(db, review_id); key = str(payload.get("comment_key") or "").strip(); text = str(payload.get("comment_text") or "").strip(); typ = payload.get("comment_type", "general"); pri = payload.get("priority", "unspecified")
    if not key or not text: raise ValueError("comment_key and comment_text are required.")
    if typ not in COMMENT_TYPES: raise ValueError("unsupported comment_type: " + str(typ))
    if pri not in PRIORITIES: raise ValueError("unsupported priority: " + str(pri))
    r = ResearchPeerReviewCommentRecord(project_entity_id=rv.project_entity_id, publication_id=rv.publication_id, review_id=review_id, comment_key=key, comment_type=typ, target_type=payload.get("target_type", "publication"), target_ref=payload.get("target_ref"), priority=pri, comment_text=text, response_required=bool(payload.get("response_required", True)), evidence_refs_json=payload.get("evidence_refs", []), provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by", "operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_response(db, comment_id, payload):
    _reject(payload); c = db.get(ResearchPeerReviewCommentRecord, comment_id)
    if c is None: raise ValueError("peer review comment not found.")
    key = str(payload.get("response_key") or "").strip(); text = str(payload.get("response_text") or "").strip(); disposition = payload.get("disposition", "responded")
    if not key or not text: raise ValueError("response_key and response_text are required.")
    if disposition not in RESPONSE_DISPOSITIONS: raise ValueError("unsupported response disposition: " + str(disposition))
    r = ResearchPeerReviewResponseRecord(project_entity_id=c.project_entity_id, publication_id=c.publication_id, review_id=c.review_id, comment_id=comment_id, response_key=key, response_text=text, disposition=disposition, change_refs_json=payload.get("change_refs", []), evidence_refs_json=payload.get("evidence_refs", []), provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by", "operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def create_replication_study(db, publication_id, payload):
    _reject(payload); p = _publication(db, publication_id); key = str(payload.get("study_key") or "").strip(); title = str(payload.get("title") or "").strip(); typ = payload.get("replication_type", "direct"); status = payload.get("status", "planned")
    if not key or not title: raise ValueError("study_key and title are required.")
    if typ not in REPLICATION_TYPES: raise ValueError("unsupported replication_type: " + str(typ))
    if status not in REPLICATION_STATUSES: raise ValueError("unsupported replication status: " + str(status))
    r = ResearchReplicationStudyRecord(project_entity_id=p.project_entity_id, publication_id=publication_id, study_key=key, title=title, replication_type=typ, status=status, protocol_ref=payload.get("protocol_ref"), preregistration_ref=payload.get("preregistration_ref"), independent_team_json=payload.get("independent_team", []), provenance_json=payload.get("provenance", {}), metadata_json=payload.get("metadata", {}), created_by=payload.get("created_by", "operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_replication_attempt(db, study_id, payload):
    _reject(payload); st = _study(db, study_id); key = str(payload.get("attempt_key") or "").strip(); outcome = payload.get("declared_outcome", "inconclusive")
    if not key: raise ValueError("attempt_key is required.")
    if outcome not in DECLARED_OUTCOMES: raise ValueError("unsupported declared_outcome: " + str(outcome))
    r = ResearchReplicationAttemptRecord(project_entity_id=st.project_entity_id, publication_id=st.publication_id, study_id=study_id, attempt_key=key, status=payload.get("status", "recorded"), method_ref=payload.get("method_ref"), dataset_refs_json=payload.get("dataset_refs", []), environment_refs_json=payload.get("environment_refs", []), execution_refs_json=payload.get("execution_refs", []), result_summary=payload.get("result_summary"), declared_outcome=outcome, provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by", "operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_replication_comparison(db, study_id, payload):
    _reject(payload); st = _study(db, study_id); key = str(payload.get("comparison_key") or "").strip(); original = str(payload.get("original_ref") or "").strip(); replication = str(payload.get("replication_ref") or "").strip(); relation = payload.get("declared_relation", "inconclusive")
    if not key or not original or not replication: raise ValueError("comparison_key, original_ref, and replication_ref are required.")
    if relation not in DECLARED_RELATIONS: raise ValueError("unsupported declared_relation: " + str(relation))
    r = ResearchReplicationComparisonRecord(project_entity_id=st.project_entity_id, publication_id=st.publication_id, study_id=study_id, comparison_key=key, original_ref=original, replication_ref=replication, metric_name=payload.get("metric_name"), original_value_json=payload.get("original_value", {}), replication_value_json=payload.get("replication_value", {}), declared_relation=relation, interpretation_text=payload.get("interpretation_text"), provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by", "operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def create_rebuttal(db, publication_id, payload):
    _reject(payload); p = _publication(db, publication_id); key = str(payload.get("rebuttal_key") or "").strip(); title = str(payload.get("title") or "").strip(); text = str(payload.get("rebuttal_text") or "").strip(); status = payload.get("status", "draft")
    if not key or not title or not text: raise ValueError("rebuttal_key, title, and rebuttal_text are required.")
    if status not in REBUTTAL_STATUSES: raise ValueError("unsupported rebuttal status: " + str(status))
    r = ResearchRebuttalRecord(project_entity_id=p.project_entity_id, publication_id=publication_id, rebuttal_key=key, title=title, status=status, target_type=payload.get("target_type", "publication"), target_ref=payload.get("target_ref"), rebuttal_text=text, author_identity_json=payload.get("author_identity", {}), provenance_json=payload.get("provenance", {}), metadata_json=payload.get("metadata", {}), created_by=payload.get("created_by", "operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_rebuttal_point(db, rebuttal_id, payload):
    _reject(payload); rb = _rebuttal(db, rebuttal_id); key = str(payload.get("point_key") or "").strip(); text = str(payload.get("point_text") or "").strip()
    if not key or not text: raise ValueError("point_key and point_text are required.")
    r = ResearchRebuttalPointRecord(project_entity_id=rb.project_entity_id, publication_id=rb.publication_id, rebuttal_id=rebuttal_id, point_key=key, point_text=text, target_ref=payload.get("target_ref"), evidence_refs_json=payload.get("evidence_refs", []), response_ref=payload.get("response_ref"), provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by", "operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def revise_review(db, review_id, payload):
    _reject(payload); rv = _review(db, review_id); prior = _ser(rv)
    for fld in ("stage", "status", "summary_text", "reviewer_role", "declared_recommendation"):
        if fld in payload:
            if fld == "stage" and payload[fld] not in REVIEW_STAGES: raise ValueError("unsupported review stage: " + str(payload[fld]))
            if fld == "status" and payload[fld] not in REVIEW_STATUSES: raise ValueError("unsupported review status: " + str(payload[fld]))
            if fld == "declared_recommendation" and payload[fld] is not None and payload[fld] not in RECOMMENDATIONS: raise ValueError("unsupported declared_recommendation: " + str(payload[fld]))
            setattr(rv, fld, payload[fld])
    for fld, attr in (("reviewer_identity", "reviewer_identity_json"), ("provenance", "provenance_json"), ("metadata", "metadata_json")):
        if fld in payload: setattr(rv, attr, payload[fld])
    n = db.scalar(select(func.max(ResearchPeerReviewRevisionRecord.revision)).where(ResearchPeerReviewRevisionRecord.review_id == review_id)) or 0
    revised = _ser(rv); h = _hash(revised)
    r = ResearchPeerReviewRevisionRecord(project_entity_id=rv.project_entity_id, publication_id=rv.publication_id, review_id=review_id, revision=int(n)+1, state_hash=h, prior_state_json=prior, revised_state_json=revised, change_summary=payload.get("change_summary"), provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by", "operator"))
    db.add(rv); db.add(r); db.commit(); db.refresh(r); return _ser(r)

def _rows(db, cls, publication_id):
    return [_ser(x) for x in db.scalars(select(cls).where(cls.publication_id == publication_id)).all()]

def descriptive_summary(db, publication_id, public=False):
    p = _publication(db, publication_id); project = _project(db, p.project_entity_id)
    if public and project.visibility != "public": raise ValueError("research project is not public.")
    reviews = db.scalars(select(ResearchPeerReviewRecord).where(ResearchPeerReviewRecord.publication_id == publication_id)).all()
    comments = db.scalars(select(ResearchPeerReviewCommentRecord).where(ResearchPeerReviewCommentRecord.publication_id == publication_id)).all()
    responses = db.scalars(select(ResearchPeerReviewResponseRecord).where(ResearchPeerReviewResponseRecord.publication_id == publication_id)).all()
    attempts = db.scalars(select(ResearchReplicationAttemptRecord).where(ResearchReplicationAttemptRecord.publication_id == publication_id)).all()
    comparisons = db.scalars(select(ResearchReplicationComparisonRecord).where(ResearchReplicationComparisonRecord.publication_id == publication_id)).all()
    return {
        "release": "2.82.0", "contract": CONTRACT, "publication_id": publication_id,
        "declared_reviewer_recommendations": dict(Counter((x.declared_recommendation or "none") for x in reviews)),
        "comment_priorities": dict(Counter(x.priority for x in comments)),
        "response_dispositions": dict(Counter(x.disposition for x in responses)),
        "declared_replication_outcomes": dict(Counter(x.declared_outcome for x in attempts)),
        "declared_comparison_relations": dict(Counter(x.declared_relation for x in comparisons)),
        "summary_is_descriptive_only": True, "quality_score_computed": False, "replication_success_inferred": False,
        "publication_decision_made_by_core": False, "truth_inferred_by_core": False,
    }

def lineage(db, publication_id, public=False):
    p = _publication(db, publication_id); project = _project(db, p.project_entity_id)
    if public and project.visibility != "public": raise ValueError("research project is not public.")
    reviews = _rows(db, ResearchPeerReviewRecord, publication_id); comments = _rows(db, ResearchPeerReviewCommentRecord, publication_id); responses = _rows(db, ResearchPeerReviewResponseRecord, publication_id); studies = _rows(db, ResearchReplicationStudyRecord, publication_id); attempts = _rows(db, ResearchReplicationAttemptRecord, publication_id); comparisons = _rows(db, ResearchReplicationComparisonRecord, publication_id); rebuttals = _rows(db, ResearchRebuttalRecord, publication_id); points = _rows(db, ResearchRebuttalPointRecord, publication_id)
    return {
        "release": "2.82.0", "contract": CONTRACT, "project_ref": p.project_entity_id, "publication": _ser(p),
        "review_comment_edges": [{"review_id": c["review_id"], "comment_id": c["id"], "target_ref": c.get("target_ref"), "evidence_refs": c.get("evidence_refs", [])} for c in comments],
        "comment_response_edges": [{"comment_id": r["comment_id"], "response_id": r["id"], "change_refs": r.get("change_refs", []), "evidence_refs": r.get("evidence_refs", [])} for r in responses],
        "replication_edges": [{"study_id": a["study_id"], "attempt_id": a["id"], "execution_refs": a.get("execution_refs", []), "declared_outcome": a["declared_outcome"]} for a in attempts],
        "replication_comparison_edges": [{"study_id": x["study_id"], "comparison_id": x["id"], "original_ref": x["original_ref"], "replication_ref": x["replication_ref"], "declared_relation": x["declared_relation"]} for x in comparisons],
        "rebuttal_edges": [{"rebuttal_id": q["rebuttal_id"], "point_id": q["id"], "target_ref": q.get("target_ref"), "evidence_refs": q.get("evidence_refs", [])} for q in points],
        "lineage_is_declared_not_inferred": True, "missing_links_inferred_by_core": False,
    }

def bundle(db, publication_id, public=False):
    p = _publication(db, publication_id); project = _project(db, p.project_entity_id)
    if public and project.visibility != "public": raise ValueError("research project is not public.")
    return {
        "release": "2.82.0", "contract": CONTRACT, "project": _ser(project), "publication": _ser(p),
        "reviews": _rows(db, ResearchPeerReviewRecord, publication_id),
        "review_comments": _rows(db, ResearchPeerReviewCommentRecord, publication_id),
        "review_responses": _rows(db, ResearchPeerReviewResponseRecord, publication_id),
        "replication_studies": _rows(db, ResearchReplicationStudyRecord, publication_id),
        "replication_attempts": _rows(db, ResearchReplicationAttemptRecord, publication_id),
        "replication_comparisons": _rows(db, ResearchReplicationComparisonRecord, publication_id),
        "rebuttals": _rows(db, ResearchRebuttalRecord, publication_id),
        "rebuttal_points": _rows(db, ResearchRebuttalPointRecord, publication_id),
        "review_revisions": _rows(db, ResearchPeerReviewRevisionRecord, publication_id),
        "snapshots": _rows(db, ResearchPeerReviewSnapshotRecord, publication_id),
        "descriptive_summary": descriptive_summary(db, publication_id, public),
        "lineage": lineage(db, publication_id, public), **boundaries()
    }

def snapshot(db, publication_id, payload):
    _reject(payload); p = _publication(db, publication_id); state = bundle(db, publication_id); state.pop("snapshots", None); h = _hash(state)
    prev = db.scalar(select(ResearchPeerReviewSnapshotRecord).where(ResearchPeerReviewSnapshotRecord.publication_id == publication_id).order_by(ResearchPeerReviewSnapshotRecord.revision.desc()).limit(1))
    rev = 1 if prev is None else prev.revision + 1
    r = ResearchPeerReviewSnapshotRecord(project_entity_id=p.project_entity_id, publication_id=publication_id, revision=rev, content_hash=h, previous_snapshot_hash=None if prev is None else prev.content_hash, state_json=state, provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by", "operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)
