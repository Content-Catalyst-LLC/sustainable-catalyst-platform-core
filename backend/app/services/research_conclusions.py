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
    ResearchConclusionRecord,
    ResearchConclusionEvidenceBindingRecord,
    ResearchConclusionCaveatRecord,
    ResearchConclusionDissentRecord,
    ResearchDecisionTraceRecord,
    ResearchConclusionReviewRecord,
    ResearchConclusionRevisionRecord,
    ResearchConclusionSnapshotRecord,
)

CONTRACT = "sc.research.decision-trace-conclusion-governance.v1"

CONCLUSION_TYPES = {"interpretive", "empirical", "methodological", "causal", "comparative", "decision_record"}
CONCLUSION_STATUSES = {"draft", "active", "qualified", "superseded", "withdrawn", "archived"}
SOURCE_TYPES = {"evidence", "finding", "interpretation", "claim", "hypothesis", "argument", "synthesis", "counterargument", "tension", "method", "result"}
EVIDENCE_ROLES = {"supports", "contradicts", "qualifies", "context", "limitation", "unresolved"}
CAVEAT_TYPES = {"limitation", "uncertainty", "scope", "assumption", "conflict", "generalizability", "data_quality"}
CAVEAT_STATUSES = {"open", "addressed", "accepted", "external"}
DISSENT_STATUSES = {"recorded", "open", "addressed", "withdrawn"}
TRACE_TYPES = {"reviewed", "considered", "excluded", "revised", "accepted_by_researcher", "qualified_by_researcher", "superseded", "withdrawn"}
REVIEW_TYPES = {"researcher_review", "peer_review", "advisor_review", "editorial_review", "external_review"}
REVIEW_DISPOSITIONS = {"noted", "concurred", "dissented", "changes_requested", "accepted_with_caveats"}

FORBIDDEN = {
    "generate_conclusion_by_core", "choose_conclusion_by_core", "score_conclusion_by_core",
    "rank_conclusions_by_core", "certify_conclusion_by_core", "resolve_dissent_by_core",
    "infer_truth_by_core", "publish_by_core", "auto_accept_review_by_core",
}

CLASSES = [
    ResearchConclusionRecord, ResearchConclusionEvidenceBindingRecord, ResearchConclusionCaveatRecord,
    ResearchConclusionDissentRecord, ResearchDecisionTraceRecord, ResearchConclusionReviewRecord,
    ResearchConclusionRevisionRecord, ResearchConclusionSnapshotRecord,
]
COUNT_NAMES = ["conclusions", "evidence_bindings", "caveats", "dissent_records", "decision_trace_steps", "reviews", "revisions", "snapshots"]


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
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _reject(payload: dict) -> None:
    bad = sorted(key for key in FORBIDDEN if payload.get(key) not in (None, False))
    if bad:
        raise ValueError(
            "Research Decision Trace & Conclusion Governance records researcher-authored judgment; Core does not generate, choose, score, rank, certify, resolve dissent, infer truth, auto-accept review, or publish: "
            + ", ".join(bad)
        )


def boundaries() -> dict:
    return {
        "researcher_authored_conclusion_registry_by_core": True,
        "declared_evidence_binding_registry_by_core": True,
        "caveat_registry_by_core": True,
        "dissent_registry_by_core": True,
        "decision_trace_registry_by_core": True,
        "review_registry_by_core": True,
        "descriptive_governance_summary_by_core": True,
        "conclusion_version_history_by_core": True,
        "immutable_conclusion_snapshots_by_core": True,
        "generate_conclusion_by_core": False,
        "choose_conclusion_by_core": False,
        "score_conclusion_by_core": False,
        "rank_conclusions_by_core": False,
        "certify_conclusion_by_core": False,
        "resolve_dissent_by_core": False,
        "auto_accept_review_by_core": False,
        "infer_truth_by_core": False,
        "publish_by_core": False,
    }


def readiness(db: Session) -> dict:
    count = lambda cls: int(db.scalar(select(func.count()).select_from(cls)) or 0)
    return {
        "release": "2.80.0", "contract": CONTRACT,
        "conclusion_types": sorted(CONCLUSION_TYPES), "conclusion_statuses": sorted(CONCLUSION_STATUSES),
        "source_types": sorted(SOURCE_TYPES), "evidence_roles": sorted(EVIDENCE_ROLES),
        "caveat_types": sorted(CAVEAT_TYPES), "trace_types": sorted(TRACE_TYPES),
        "review_types": sorted(REVIEW_TYPES), "review_dispositions": sorted(REVIEW_DISPOSITIONS),
        "counts": dict(zip(COUNT_NAMES, [count(cls) for cls in CLASSES])),
        **boundaries(),
    }


def _project(db: Session, project_id: str):
    record = db.get(UnifiedResearchProjectProfileRecord, project_id)
    if record is None: raise ValueError("project_entity_id must reference a v2.72 unified research project profile.")
    return record


def _argument(db: Session, argument_id: str):
    record = db.get(ResearchArgumentRecord, argument_id)
    if record is None: raise ValueError("research argument not found.")
    return record


def _conclusion(db: Session, conclusion_id: str):
    record = db.get(ResearchConclusionRecord, conclusion_id)
    if record is None: raise ValueError("research conclusion not found.")
    return record


def create_conclusion(db: Session, argument_id: str, payload: dict) -> dict:
    _reject(payload); argument = _argument(db, argument_id); _project(db, argument.project_entity_id)
    key = str(payload.get("conclusion_key") or "").strip(); title = str(payload.get("title") or "").strip(); text = str(payload.get("conclusion_text") or "").strip()
    if not key or not title or not text: raise ValueError("conclusion_key, title, and conclusion_text are required.")
    ctype = payload.get("conclusion_type", "interpretive"); status = payload.get("status", "draft")
    if ctype not in CONCLUSION_TYPES: raise ValueError("unsupported conclusion_type: " + ctype)
    if status not in CONCLUSION_STATUSES: raise ValueError("unsupported conclusion status: " + status)
    record = ResearchConclusionRecord(project_entity_id=argument.project_entity_id, argument_id=argument_id, conclusion_key=key, title=title,
        conclusion_text=text, conclusion_type=ctype, status=status, scope_json=payload.get("scope", {}), uncertainty_json=payload.get("uncertainty", {}),
        limitations_json=payload.get("limitations", []), metadata_json=payload.get("metadata", {}), provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by", "operator"))
    db.add(record); db.commit(); db.refresh(record); return _ser(record)


def add_evidence_binding(db: Session, conclusion_id: str, payload: dict) -> dict:
    _reject(payload); c = _conclusion(db, conclusion_id)
    source_type = payload.get("source_type"); role = payload.get("role")
    if source_type not in SOURCE_TYPES: raise ValueError("unsupported source_type: " + str(source_type))
    if role not in EVIDENCE_ROLES: raise ValueError("unsupported evidence role: " + str(role))
    if not str(payload.get("binding_key") or "").strip() or not str(payload.get("source_ref") or "").strip(): raise ValueError("binding_key and source_ref are required.")
    r=ResearchConclusionEvidenceBindingRecord(project_entity_id=c.project_entity_id, conclusion_id=conclusion_id, binding_key=payload["binding_key"], source_type=source_type,
        source_ref=payload["source_ref"], role=role, researcher_assessment=payload.get("researcher_assessment"), rationale=payload.get("rationale"),
        metadata_json=payload.get("metadata", {}), provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by", "operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)


def add_caveat(db: Session, conclusion_id: str, payload: dict) -> dict:
    _reject(payload); c=_conclusion(db, conclusion_id); typ=payload.get("caveat_type"); status=payload.get("status", "open")
    if typ not in CAVEAT_TYPES: raise ValueError("unsupported caveat_type: " + str(typ))
    if status not in CAVEAT_STATUSES: raise ValueError("unsupported caveat status: " + status)
    if not str(payload.get("caveat_key") or "").strip() or not str(payload.get("statement_text") or "").strip(): raise ValueError("caveat_key and statement_text are required.")
    r=ResearchConclusionCaveatRecord(project_entity_id=c.project_entity_id, conclusion_id=conclusion_id, caveat_key=payload["caveat_key"], caveat_type=typ,
        statement_text=payload["statement_text"], status=status, source_refs_json=payload.get("source_refs", []), metadata_json=payload.get("metadata", {}),
        provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by", "operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)


def add_dissent(db: Session, conclusion_id: str, payload: dict) -> dict:
    _reject(payload); c=_conclusion(db, conclusion_id); status=payload.get("status", "recorded")
    if status not in DISSENT_STATUSES: raise ValueError("unsupported dissent status: " + status)
    if not str(payload.get("dissent_key") or "").strip() or not str(payload.get("statement_text") or "").strip(): raise ValueError("dissent_key and statement_text are required.")
    r=ResearchConclusionDissentRecord(project_entity_id=c.project_entity_id, conclusion_id=conclusion_id, dissent_key=payload["dissent_key"], statement_text=payload["statement_text"],
        source_ref=payload.get("source_ref"), evidence_refs_json=payload.get("evidence_refs", []), status=status, response_text=payload.get("response_text"),
        metadata_json=payload.get("metadata", {}), provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by", "operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)


def add_trace_step(db: Session, conclusion_id: str, payload: dict) -> dict:
    _reject(payload); c=_conclusion(db, conclusion_id); typ=payload.get("step_type")
    if typ not in TRACE_TYPES: raise ValueError("unsupported trace step_type: " + str(typ))
    if not str(payload.get("trace_key") or "").strip() or not str(payload.get("action_text") or "").strip(): raise ValueError("trace_key and action_text are required.")
    r=ResearchDecisionTraceRecord(project_entity_id=c.project_entity_id, conclusion_id=conclusion_id, trace_key=payload["trace_key"], step_index=int(payload.get("step_index",0)),
        step_type=typ, source_ref=payload.get("source_ref"), action_text=payload["action_text"], rationale=payload.get("rationale"), metadata_json=payload.get("metadata", {}),
        provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by", "operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)


def add_review(db: Session, conclusion_id: str, payload: dict) -> dict:
    _reject(payload); c=_conclusion(db, conclusion_id); typ=payload.get("review_type", "researcher_review"); disp=payload.get("disposition", "noted")
    if typ not in REVIEW_TYPES: raise ValueError("unsupported review_type: " + typ)
    if disp not in REVIEW_DISPOSITIONS: raise ValueError("unsupported review disposition: " + disp)
    if not str(payload.get("review_key") or "").strip(): raise ValueError("review_key is required.")
    r=ResearchConclusionReviewRecord(project_entity_id=c.project_entity_id, conclusion_id=conclusion_id, review_key=payload["review_key"], review_type=typ,
        reviewer_ref=payload.get("reviewer_ref"), disposition=disp, review_text=payload.get("review_text"), caveat_refs_json=payload.get("caveat_refs", []),
        provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by", "operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)


def revise_conclusion(db: Session, conclusion_id: str, payload: dict) -> dict:
    _reject(payload); c=_conclusion(db, conclusion_id); prior=_ser(c)
    for fld in ("title", "conclusion_text", "conclusion_type", "status"):
        if fld in payload:
            if fld == "conclusion_type" and payload[fld] not in CONCLUSION_TYPES: raise ValueError("unsupported conclusion_type: " + payload[fld])
            if fld == "status" and payload[fld] not in CONCLUSION_STATUSES: raise ValueError("unsupported conclusion status: " + payload[fld])
            setattr(c, fld, payload[fld])
    for fld, attr in (("scope","scope_json"),("uncertainty","uncertainty_json"),("limitations","limitations_json"),("metadata","metadata_json"),("provenance","provenance_json")):
        if fld in payload: setattr(c, attr, payload[fld])
    prior_rev=db.scalar(select(func.max(ResearchConclusionRevisionRecord.revision)).where(ResearchConclusionRevisionRecord.conclusion_id==conclusion_id)) or 0
    revised=_ser(c); state_hash=_hash(revised)
    rev=ResearchConclusionRevisionRecord(conclusion_id=conclusion_id, project_entity_id=c.project_entity_id, revision=int(prior_rev)+1, state_hash=state_hash,
        prior_state_json=prior, revised_state_json=revised, change_summary=payload.get("change_summary"), provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by","operator"))
    db.add(c); db.add(rev); db.commit(); db.refresh(rev); return _ser(rev)


def governance_summary(db: Session, conclusion_id: str, public: bool=False) -> dict:
    c=_conclusion(db, conclusion_id); project=_project(db, c.project_entity_id)
    if public and project.visibility != "public": raise ValueError("research project is not public.")
    bindings=list(db.scalars(select(ResearchConclusionEvidenceBindingRecord).where(ResearchConclusionEvidenceBindingRecord.conclusion_id==conclusion_id)).all())
    caveats=list(db.scalars(select(ResearchConclusionCaveatRecord).where(ResearchConclusionCaveatRecord.conclusion_id==conclusion_id)).all())
    dissent=list(db.scalars(select(ResearchConclusionDissentRecord).where(ResearchConclusionDissentRecord.conclusion_id==conclusion_id)).all())
    traces=list(db.scalars(select(ResearchDecisionTraceRecord).where(ResearchDecisionTraceRecord.conclusion_id==conclusion_id).order_by(ResearchDecisionTraceRecord.step_index, ResearchDecisionTraceRecord.created_at)).all())
    reviews=list(db.scalars(select(ResearchConclusionReviewRecord).where(ResearchConclusionReviewRecord.conclusion_id==conclusion_id)).all())
    return {"release":"2.80.0","contract":CONTRACT,"conclusion":_ser(c),
        "descriptive_governance":{
            "evidence_role_counts":dict(sorted(Counter(x.role for x in bindings).items())),
            "source_type_counts":dict(sorted(Counter(x.source_type for x in bindings).items())),
            "caveat_type_counts":dict(sorted(Counter(x.caveat_type for x in caveats).items())),
            "open_caveat_count":sum(1 for x in caveats if x.status=="open"),
            "dissent_status_counts":dict(sorted(Counter(x.status for x in dissent).items())),
            "trace_step_type_counts":dict(sorted(Counter(x.step_type for x in traces).items())),
            "review_disposition_counts":dict(sorted(Counter(x.disposition for x in reviews).items())),
        },
        "governance_summary_is_descriptive_only":True,"conclusion_score_computed":False,"conclusion_ranking_computed":False,"truth_determination_performed":False}


def bundle(db: Session, conclusion_id: str, public: bool=False) -> dict:
    c=_conclusion(db, conclusion_id); project=_project(db,c.project_entity_id); argument=_argument(db,c.argument_id)
    if public and project.visibility != "public": raise ValueError("research project is not public.")
    def rows(cls): return [_ser(x) for x in db.scalars(select(cls).where(cls.conclusion_id==conclusion_id)).all()]
    return {"release":"2.80.0","contract":CONTRACT,"project":_ser(project),"argument":_ser(argument),"conclusion":_ser(c),
        "evidence_bindings":rows(ResearchConclusionEvidenceBindingRecord),"caveats":rows(ResearchConclusionCaveatRecord),"dissent_records":rows(ResearchConclusionDissentRecord),
        "decision_trace_steps":rows(ResearchDecisionTraceRecord),"reviews":rows(ResearchConclusionReviewRecord),"revisions":rows(ResearchConclusionRevisionRecord),
        "snapshots":rows(ResearchConclusionSnapshotRecord),"governance_summary":governance_summary(db, conclusion_id, public),**boundaries()}


def _state(db: Session, conclusion_id: str) -> dict:
    state=bundle(db, conclusion_id); state.pop("snapshots",None); return state


def snapshot(db: Session, conclusion_id: str, payload: dict) -> dict:
    _reject(payload); c=_conclusion(db, conclusion_id); state=_state(db, conclusion_id); content_hash=_hash(state)
    previous=db.scalar(select(ResearchConclusionSnapshotRecord).where(ResearchConclusionSnapshotRecord.conclusion_id==conclusion_id).order_by(ResearchConclusionSnapshotRecord.revision.desc()).limit(1))
    revision=1 if previous is None else previous.revision+1
    r=ResearchConclusionSnapshotRecord(project_entity_id=c.project_entity_id, conclusion_id=conclusion_id, revision=revision, content_hash=content_hash,
        previous_snapshot_hash=None if previous is None else previous.content_hash, state_json=state, provenance_json=payload.get("provenance",{}), created_by=payload.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)
