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
    ResearchProgramRecord, ResearchProgramProjectRecord, ResearchProgramObjectiveRecord,
    ResearchProgramMilestoneRecord, ResearchLongitudinalNodeRecord, ResearchLongitudinalEdgeRecord,
    ResearchKnowledgeStateRecord, ResearchEvolutionEventRecord,
    ResearchProgramRevisionRecord, ResearchProgramSnapshotRecord,
)

CONTRACT = "sc.research.program-longitudinal-knowledge-graph.v1"
PROGRAM_STATUSES = {"draft", "active", "paused", "completed", "archived"}
VISIBILITIES = {"private", "internal", "public"}
MEMBERSHIP_ROLES = {"member", "lead", "supporting", "replication", "synthesis", "reference"}
MEMBERSHIP_STATUSES = {"active", "completed", "withdrawn", "archived"}
OBJECTIVE_STATUSES = {"proposed", "active", "completed", "deferred", "archived"}
MILESTONE_TYPES = {"research", "data", "method", "replication", "publication", "review", "synthesis", "governance", "other"}
MILESTONE_STATUSES = {"planned", "in_progress", "achieved", "missed", "deferred", "cancelled"}
RELATION_TYPES = {"extends", "supersedes", "replicates", "challenges", "supports", "contradicts", "qualifies", "depends_on", "derived_from", "related_to", "other"}
EVENT_TYPES = {"created", "updated", "supported", "challenged", "replicated", "superseded", "withdrawn", "published", "reviewed", "synthesized", "other"}
FORBIDDEN = {
    "prioritize_research_by_core", "allocate_funding_by_core", "rank_projects_by_core",
    "auto_link_knowledge_graph_by_core", "infer_research_direction_by_core",
    "infer_causality_by_core", "forecast_program_success_by_core",
    "resolve_evidence_gaps_by_core", "infer_knowledge_truth_by_core", "infer_truth_by_core",
}
CLASSES = [
    ResearchProgramRecord, ResearchProgramProjectRecord, ResearchProgramObjectiveRecord,
    ResearchProgramMilestoneRecord, ResearchLongitudinalNodeRecord, ResearchLongitudinalEdgeRecord,
    ResearchKnowledgeStateRecord, ResearchEvolutionEventRecord,
    ResearchProgramRevisionRecord, ResearchProgramSnapshotRecord,
]
COUNT_NAMES = [
    "programs", "project_memberships", "objectives", "milestones", "longitudinal_nodes",
    "longitudinal_edges", "knowledge_states", "evolution_events", "revisions", "snapshots",
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


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _reject(payload):
    bad = sorted(k for k in FORBIDDEN if payload.get(k) not in (None, False))
    if bad:
        raise ValueError(
            "Core preserves declared research-program and longitudinal knowledge records; it does not prioritize research, allocate funding, rank projects, auto-link graphs, infer direction/causality/truth, forecast program success, or resolve evidence gaps: "
            + ", ".join(bad)
        )


def boundaries():
    return {
        "research_program_registry_by_core": True,
        "program_project_membership_registry_by_core": True,
        "program_objective_registry_by_core": True,
        "program_milestone_registry_by_core": True,
        "longitudinal_knowledge_node_registry_by_core": True,
        "declared_longitudinal_edge_registry_by_core": True,
        "knowledge_state_history_by_core": True,
        "research_evolution_event_registry_by_core": True,
        "descriptive_longitudinal_timeline_by_core": True,
        "program_revision_history_by_core": True,
        "program_lineage_by_core": True,
        "immutable_program_snapshots_by_core": True,
        "prioritize_research_by_core": False,
        "allocate_funding_by_core": False,
        "rank_projects_by_core": False,
        "auto_link_knowledge_graph_by_core": False,
        "infer_research_direction_by_core": False,
        "infer_causality_by_core": False,
        "forecast_program_success_by_core": False,
        "resolve_evidence_gaps_by_core": False,
        "infer_knowledge_truth_by_core": False,
        "infer_truth_by_core": False,
    }


def readiness(db: Session):
    counts = {name: db.scalar(select(func.count()).select_from(cls)) or 0 for name, cls in zip(COUNT_NAMES, CLASSES)}
    return {"release": "2.84.0", "contract": CONTRACT, "counts": counts, **boundaries()}


def _program(db: Session, program_id: str):
    row = db.get(ResearchProgramRecord, program_id)
    if row is None:
        raise ValueError("research program not found.")
    return row


def _project(db: Session, project_id: str):
    row = db.get(UnifiedResearchProjectProfileRecord, project_id)
    if row is None:
        raise ValueError("unified research project not found.")
    return row


def create_program(db: Session, payload: dict):
    _reject(payload)
    key = str(payload.get("program_key") or "").strip()
    title = str(payload.get("title") or "").strip()
    status = payload.get("status", "active")
    visibility = payload.get("visibility", "private")
    if not key or not title:
        raise ValueError("program_key and title are required.")
    if status not in PROGRAM_STATUSES:
        raise ValueError("unsupported program status: " + str(status))
    if visibility not in VISIBILITIES:
        raise ValueError("unsupported visibility: " + str(visibility))
    row = ResearchProgramRecord(
        program_key=key, title=title, description_text=payload.get("description_text"), status=status,
        visibility=visibility, horizon_start=payload.get("horizon_start"), horizon_end=payload.get("horizon_end"),
        vision_text=payload.get("vision_text"), scope_json=payload.get("scope", {}), governance_json=payload.get("governance", {}),
        provenance_json=payload.get("provenance", {}), metadata_json=payload.get("metadata", {}), created_by=payload.get("created_by", "operator"),
    )
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_project(db: Session, program_id: str, payload: dict):
    _reject(payload); _program(db, program_id)
    project_id = str(payload.get("project_entity_id") or "").strip(); _project(db, project_id)
    key = str(payload.get("membership_key") or project_id).strip(); role = payload.get("role", "member"); status = payload.get("status", "active")
    if role not in MEMBERSHIP_ROLES: raise ValueError("unsupported membership role: " + str(role))
    if status not in MEMBERSHIP_STATUSES: raise ValueError("unsupported membership status: " + str(status))
    row = ResearchProgramProjectRecord(program_id=program_id, project_entity_id=project_id, membership_key=key, role=role, status=status,
        joined_at=payload.get("joined_at"), left_at=payload.get("left_at"), rationale_text=payload.get("rationale_text"), provenance_json=payload.get("provenance", {}), created_by=payload.get("created_by", "operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_objective(db: Session, program_id: str, payload: dict):
    _reject(payload); _program(db, program_id)
    key=str(payload.get("objective_key") or "").strip(); title=str(payload.get("title") or "").strip(); status=payload.get("status","active")
    if not key or not title: raise ValueError("objective_key and title are required.")
    if status not in OBJECTIVE_STATUSES: raise ValueError("unsupported objective status: "+str(status))
    row=ResearchProgramObjectiveRecord(program_id=program_id,objective_key=key,title=title,description_text=payload.get("description_text"),status=status,target_horizon=payload.get("target_horizon"),success_criteria_json=payload.get("success_criteria",[]),evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_milestone(db: Session, program_id: str, payload: dict):
    _reject(payload); _program(db, program_id)
    key=str(payload.get("milestone_key") or "").strip(); title=str(payload.get("title") or "").strip(); typ=payload.get("milestone_type","research"); status=payload.get("status","planned")
    if not key or not title: raise ValueError("milestone_key and title are required.")
    if typ not in MILESTONE_TYPES: raise ValueError("unsupported milestone_type: "+str(typ))
    if status not in MILESTONE_STATUSES: raise ValueError("unsupported milestone status: "+str(status))
    row=ResearchProgramMilestoneRecord(program_id=program_id,milestone_key=key,title=title,milestone_type=typ,status=status,target_at=payload.get("target_at"),achieved_at=payload.get("achieved_at"),related_refs_json=payload.get("related_refs",[]),evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_node(db: Session, program_id: str, payload: dict):
    _reject(payload); _program(db, program_id)
    key=str(payload.get("node_key") or "").strip(); typ=str(payload.get("object_type") or "").strip(); ref=str(payload.get("object_ref") or "").strip()
    if not key or not typ or not ref: raise ValueError("node_key, object_type, and object_ref are required.")
    row=ResearchLongitudinalNodeRecord(program_id=program_id,node_key=key,object_type=typ,object_ref=ref,label=payload.get("label"),first_observed_at=payload.get("first_observed_at"),last_observed_at=payload.get("last_observed_at"),state_json=payload.get("state",{}),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_edge(db: Session, program_id: str, payload: dict):
    _reject(payload); _program(db, program_id)
    key=str(payload.get("edge_key") or "").strip(); source=str(payload.get("source_node_id") or "").strip(); target=str(payload.get("target_node_id") or "").strip(); typ=payload.get("relation_type")
    if not key or not source or not target or not typ: raise ValueError("edge_key, source_node_id, target_node_id, and relation_type are required.")
    if typ not in RELATION_TYPES: raise ValueError("unsupported relation_type: "+str(typ))
    s=db.get(ResearchLongitudinalNodeRecord,source); t=db.get(ResearchLongitudinalNodeRecord,target)
    if s is None or t is None or s.program_id!=program_id or t.program_id!=program_id: raise ValueError("source and target nodes must exist in the same research program.")
    row=ResearchLongitudinalEdgeRecord(program_id=program_id,edge_key=key,source_node_id=source,target_node_id=target,relation_type=typ,valid_from=payload.get("valid_from"),valid_to=payload.get("valid_to"),rationale_text=payload.get("rationale_text"),evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_knowledge_state(db: Session, program_id: str, payload: dict):
    _reject(payload); _program(db, program_id)
    key=str(payload.get("state_key") or "").strip(); observed=str(payload.get("observed_at") or "").strip(); typ=str(payload.get("subject_type") or "").strip(); ref=str(payload.get("subject_ref") or "").strip()
    if not key or not observed or not typ or not ref: raise ValueError("state_key, observed_at, subject_type, and subject_ref are required.")
    row=ResearchKnowledgeStateRecord(program_id=program_id,state_key=key,observed_at=observed,subject_type=typ,subject_ref=ref,status=payload.get("status","declared"),summary_text=payload.get("summary_text"),attributes_json=payload.get("attributes",{}),evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def add_evolution_event(db: Session, program_id: str, payload: dict):
    _reject(payload); _program(db, program_id)
    key=str(payload.get("event_key") or "").strip(); occurred=str(payload.get("occurred_at") or "").strip(); ref=str(payload.get("subject_ref") or "").strip(); typ=payload.get("event_type")
    if not key or not occurred or not ref or not typ: raise ValueError("event_key, occurred_at, subject_ref, and event_type are required.")
    if typ not in EVENT_TYPES: raise ValueError("unsupported event_type: "+str(typ))
    row=ResearchEvolutionEventRecord(program_id=program_id,event_key=key,event_type=typ,occurred_at=occurred,subject_ref=ref,prior_state_ref=payload.get("prior_state_ref"),resulting_state_ref=payload.get("resulting_state_ref"),description_text=payload.get("description_text"),evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def revise_program(db: Session, program_id: str, payload: dict):
    _reject(payload); p=_program(db,program_id); prior=_ser(p)
    for fld in ("title","description_text","status","visibility","horizon_start","horizon_end","vision_text"):
        if fld in payload:
            if fld=="status" and payload[fld] not in PROGRAM_STATUSES: raise ValueError("unsupported program status: "+str(payload[fld]))
            if fld=="visibility" and payload[fld] not in VISIBILITIES: raise ValueError("unsupported visibility: "+str(payload[fld]))
            setattr(p,fld,payload[fld])
    for fld,attr in (("scope","scope_json"),("governance","governance_json"),("provenance","provenance_json"),("metadata","metadata_json")):
        if fld in payload: setattr(p,attr,payload[fld])
    n=db.scalar(select(func.max(ResearchProgramRevisionRecord.revision)).where(ResearchProgramRevisionRecord.program_id==program_id)) or 0
    revised=_ser(p); h=_hash(revised)
    row=ResearchProgramRevisionRecord(program_id=program_id,revision=int(n)+1,state_hash=h,prior_state_json=prior,revised_state_json=revised,change_summary=payload.get("change_summary"),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(p); db.add(row); db.commit(); db.refresh(row); return _ser(row)


def _rows(db, cls, program_id):
    return [_ser(x) for x in db.scalars(select(cls).where(cls.program_id==program_id)).all()]


def _public_program(db: Session, program_id: str):
    p=_program(db,program_id)
    if p.visibility!="public": raise ValueError("research program is not public.")
    return p


def descriptive_summary(db: Session, program_id: str, public: bool=False):
    p=_public_program(db,program_id) if public else _program(db,program_id)
    memberships=db.scalars(select(ResearchProgramProjectRecord).where(ResearchProgramProjectRecord.program_id==program_id)).all()
    objectives=db.scalars(select(ResearchProgramObjectiveRecord).where(ResearchProgramObjectiveRecord.program_id==program_id)).all()
    milestones=db.scalars(select(ResearchProgramMilestoneRecord).where(ResearchProgramMilestoneRecord.program_id==program_id)).all()
    edges=db.scalars(select(ResearchLongitudinalEdgeRecord).where(ResearchLongitudinalEdgeRecord.program_id==program_id)).all()
    states=db.scalars(select(ResearchKnowledgeStateRecord).where(ResearchKnowledgeStateRecord.program_id==program_id)).all()
    events=db.scalars(select(ResearchEvolutionEventRecord).where(ResearchEvolutionEventRecord.program_id==program_id)).all()
    return {
        "release":"2.84.0","contract":CONTRACT,"program_id":program_id,"program_status":p.status,
        "project_membership_roles":dict(Counter(x.role for x in memberships)),
        "objective_statuses":dict(Counter(x.status for x in objectives)),
        "milestone_statuses":dict(Counter(x.status for x in milestones)),
        "declared_relation_types":dict(Counter(x.relation_type for x in edges)),
        "knowledge_state_statuses":dict(Counter(x.status for x in states)),
        "evolution_event_types":dict(Counter(x.event_type for x in events)),
        "summary_is_descriptive_only":True,
        "research_priorities_ranked_by_core":False,"program_success_forecast_by_core":False,"knowledge_truth_inferred_by_core":False,
    }


def graph(db: Session, program_id: str, public: bool=False):
    if public: _public_program(db,program_id)
    else: _program(db,program_id)
    nodes=_rows(db,ResearchLongitudinalNodeRecord,program_id); edges=_rows(db,ResearchLongitudinalEdgeRecord,program_id)
    return {"release":"2.84.0","contract":CONTRACT,"program_id":program_id,"nodes":nodes,"edges":edges,"graph_is_declared_not_inferred":True,"automatic_entity_resolution_by_core":False,"automatic_edge_inference_by_core":False}


def timeline(db: Session, program_id: str, public: bool=False):
    if public: _public_program(db,program_id)
    else: _program(db,program_id)
    states=_rows(db,ResearchKnowledgeStateRecord,program_id); events=_rows(db,ResearchEvolutionEventRecord,program_id); milestones=_rows(db,ResearchProgramMilestoneRecord,program_id)
    entries=[]
    for x in states: entries.append({"kind":"knowledge_state","timestamp":x["observed_at"],"record":x})
    for x in events: entries.append({"kind":"evolution_event","timestamp":x["occurred_at"],"record":x})
    for x in milestones:
        ts=x.get("achieved_at") or x.get("target_at")
        if ts: entries.append({"kind":"milestone","timestamp":ts,"record":x})
    entries.sort(key=lambda x:(x.get("timestamp") or "",x["kind"],x["record"].get("id") or ""))
    return {"release":"2.84.0","contract":CONTRACT,"program_id":program_id,"entries":entries,"timeline_is_recorded_not_inferred":True}


def lineage(db: Session, program_id: str, public: bool=False):
    if public: _public_program(db,program_id)
    p=_program(db,program_id); memberships=_rows(db,ResearchProgramProjectRecord,program_id); objectives=_rows(db,ResearchProgramObjectiveRecord,program_id); milestones=_rows(db,ResearchProgramMilestoneRecord,program_id); states=_rows(db,ResearchKnowledgeStateRecord,program_id); events=_rows(db,ResearchEvolutionEventRecord,program_id); edges=_rows(db,ResearchLongitudinalEdgeRecord,program_id)
    return {
        "release":"2.84.0","contract":CONTRACT,"program":_ser(p),
        "project_membership_edges":[{"membership_id":x["id"],"project_entity_id":x["project_entity_id"],"role":x["role"]} for x in memberships],
        "objective_evidence_edges":[{"objective_id":x["id"],"evidence_refs":x.get("evidence_refs",[])} for x in objectives],
        "milestone_evidence_edges":[{"milestone_id":x["id"],"related_refs":x.get("related_refs",[]),"evidence_refs":x.get("evidence_refs",[])} for x in milestones],
        "longitudinal_edges":[{"edge_id":x["id"],"source_node_id":x["source_node_id"],"target_node_id":x["target_node_id"],"relation_type":x["relation_type"],"evidence_refs":x.get("evidence_refs",[])} for x in edges],
        "knowledge_state_evidence_edges":[{"state_id":x["id"],"subject_ref":x["subject_ref"],"evidence_refs":x.get("evidence_refs",[])} for x in states],
        "evolution_event_edges":[{"event_id":x["id"],"subject_ref":x["subject_ref"],"prior_state_ref":x.get("prior_state_ref"),"resulting_state_ref":x.get("resulting_state_ref"),"evidence_refs":x.get("evidence_refs",[])} for x in events],
        "lineage_is_declared_not_inferred":True,"missing_links_inferred_by_core":False,
    }


def bundle(db: Session, program_id: str, public: bool=False):
    p=_public_program(db,program_id) if public else _program(db,program_id)
    memberships=_rows(db,ResearchProgramProjectRecord,program_id)
    if public:
        public_ids={x.project_entity_id for x in db.scalars(select(UnifiedResearchProjectProfileRecord).where(UnifiedResearchProjectProfileRecord.visibility=="public")).all()}
        memberships=[x for x in memberships if x["project_entity_id"] in public_ids]
    return {
        "release":"2.84.0","contract":CONTRACT,"program":_ser(p),"project_memberships":memberships,
        "objectives":_rows(db,ResearchProgramObjectiveRecord,program_id),"milestones":_rows(db,ResearchProgramMilestoneRecord,program_id),
        "longitudinal_nodes":_rows(db,ResearchLongitudinalNodeRecord,program_id),"longitudinal_edges":_rows(db,ResearchLongitudinalEdgeRecord,program_id),
        "knowledge_states":_rows(db,ResearchKnowledgeStateRecord,program_id),"evolution_events":_rows(db,ResearchEvolutionEventRecord,program_id),
        "revisions":_rows(db,ResearchProgramRevisionRecord,program_id),"snapshots":_rows(db,ResearchProgramSnapshotRecord,program_id),
        "descriptive_summary":descriptive_summary(db,program_id,public),"graph":graph(db,program_id,public),"timeline":timeline(db,program_id,public),"lineage":lineage(db,program_id,public),**boundaries(),
    }


def snapshot(db: Session, program_id: str, payload: dict):
    _reject(payload); _program(db,program_id); state=bundle(db,program_id); state.pop("snapshots",None); h=_hash(state)
    prev=db.scalar(select(ResearchProgramSnapshotRecord).where(ResearchProgramSnapshotRecord.program_id==program_id).order_by(ResearchProgramSnapshotRecord.revision.desc()).limit(1)); rev=1 if prev is None else prev.revision+1
    row=ResearchProgramSnapshotRecord(program_id=program_id,revision=rev,content_hash=h,previous_snapshot_hash=None if prev is None else prev.content_hash,state_json=state,provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)
