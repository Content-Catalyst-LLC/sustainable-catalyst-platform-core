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
    ResearchEvidenceSynthesisRecord, ResearchSynthesisStudyRecord, ResearchSynthesisOutcomeRecord,
    ResearchSynthesisEffectRecord, ResearchMetaAnalysisRecord, ResearchMetaResearchAssessmentRecord,
    ResearchSynthesisRelationRecord, ResearchEvidenceGapRecord,
    ResearchEvidenceSynthesisRevisionRecord, ResearchEvidenceSynthesisSnapshotRecord,
)

CONTRACT = "sc.research.cross-study-evidence-synthesis.v1"
SYNTHESIS_TYPES = {"systematic_review", "scoping_review", "meta_analysis", "umbrella_review", "evidence_map", "rapid_review", "narrative_synthesis", "living_review"}
SYNTHESIS_STATUSES = {"draft", "registered", "screening", "extraction", "synthesis", "completed", "archived"}
SOURCE_TYPES = {"publication", "preprint", "dataset", "report", "thesis", "registry", "replication", "other"}
INCLUSION_STATUSES = {"pending", "included", "excluded"}
DIRECTIONS = {"positive", "negative", "null", "mixed", "unspecified"}
MODEL_TYPES = {"fixed_effect", "random_effects", "multilevel", "network", "bayesian", "other"}
ASSESSMENT_DIMENSIONS = {"risk_of_bias", "publication_bias", "reporting_bias", "methodological_quality", "reproducibility", "transparency", "generalizability", "certainty", "other"}
RELATION_TYPES = {"consistent", "divergent", "mixed", "not_comparable", "context_dependent", "replicates", "challenges"}
GAP_TYPES = {"population", "intervention", "outcome", "method", "geography", "time", "data", "replication", "contradiction", "other"}
GAP_PRIORITIES = {"unspecified", "low", "medium", "high"}
GAP_STATUSES = {"open", "addressed", "deferred", "archived"}
FORBIDDEN = {
    "search_literature_by_core", "decide_study_inclusion_by_core", "compute_effect_size_by_core",
    "pool_estimates_by_core", "score_study_quality_by_core", "infer_bias_by_core",
    "rank_evidence_by_core", "infer_causality_by_core", "generate_synthesis_conclusion_by_core",
    "infer_truth_by_core",
}
CLASSES = [ResearchEvidenceSynthesisRecord, ResearchSynthesisStudyRecord, ResearchSynthesisOutcomeRecord, ResearchSynthesisEffectRecord, ResearchMetaAnalysisRecord, ResearchMetaResearchAssessmentRecord, ResearchSynthesisRelationRecord, ResearchEvidenceGapRecord, ResearchEvidenceSynthesisRevisionRecord, ResearchEvidenceSynthesisSnapshotRecord]
COUNT_NAMES = ["syntheses", "studies", "outcomes", "effects", "meta_analyses", "meta_research_assessments", "cross_study_relations", "evidence_gaps", "revisions", "snapshots"]

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
        raise ValueError("Core records declared cross-study evidence and externally computed synthesis results; it does not search literature, decide inclusion, compute or pool effects, score studies, infer bias/causality/truth, rank evidence, or generate conclusions: " + ", ".join(bad))

def boundaries():
    return {
        "evidence_synthesis_registry_by_core": True,
        "declared_study_inclusion_registry_by_core": True,
        "synthesis_outcome_registry_by_core": True,
        "declared_effect_evidence_registry_by_core": True,
        "externally_computed_meta_analysis_registry_by_core": True,
        "meta_research_assessment_registry_by_core": True,
        "cross_study_relation_registry_by_core": True,
        "evidence_gap_registry_by_core": True,
        "synthesis_revision_history_by_core": True,
        "cross_study_lineage_by_core": True,
        "immutable_synthesis_snapshots_by_core": True,
        "search_literature_by_core": False,
        "decide_study_inclusion_by_core": False,
        "compute_effect_size_by_core": False,
        "pool_estimates_by_core": False,
        "score_study_quality_by_core": False,
        "infer_bias_by_core": False,
        "rank_evidence_by_core": False,
        "infer_causality_by_core": False,
        "generate_synthesis_conclusion_by_core": False,
        "infer_truth_by_core": False,
    }

def readiness(db):
    count = lambda cls: int(db.scalar(select(func.count()).select_from(cls)) or 0)
    return {
        "release": "2.83.0", "contract": CONTRACT,
        "synthesis_types": sorted(SYNTHESIS_TYPES), "synthesis_statuses": sorted(SYNTHESIS_STATUSES),
        "source_types": sorted(SOURCE_TYPES), "inclusion_statuses": sorted(INCLUSION_STATUSES),
        "declared_directions": sorted(DIRECTIONS), "meta_analysis_model_types": sorted(MODEL_TYPES),
        "assessment_dimensions": sorted(ASSESSMENT_DIMENSIONS), "relation_types": sorted(RELATION_TYPES),
        "gap_types": sorted(GAP_TYPES), "gap_priorities": sorted(GAP_PRIORITIES), "gap_statuses": sorted(GAP_STATUSES),
        "counts": dict(zip(COUNT_NAMES, [count(c) for c in CLASSES])), **boundaries(),
    }

def _project(db, project_id):
    r = db.get(UnifiedResearchProjectProfileRecord, project_id)
    if r is None: raise ValueError("research project not found.")
    return r

def _synthesis(db, synthesis_id):
    r = db.get(ResearchEvidenceSynthesisRecord, synthesis_id)
    if r is None: raise ValueError("evidence synthesis not found.")
    return r

def _study(db, study_id):
    r = db.get(ResearchSynthesisStudyRecord, study_id)
    if r is None: raise ValueError("synthesis study not found.")
    return r

def _outcome(db, outcome_id):
    if outcome_id is None: return None
    r = db.get(ResearchSynthesisOutcomeRecord, outcome_id)
    if r is None: raise ValueError("synthesis outcome not found.")
    return r

def create_synthesis(db, project_id, payload):
    _reject(payload); p=_project(db, project_id)
    key=str(payload.get("synthesis_key") or "").strip(); title=str(payload.get("title") or "").strip(); typ=payload.get("synthesis_type","systematic_review"); status=payload.get("status","draft")
    if not key or not title: raise ValueError("synthesis_key and title are required.")
    if typ not in SYNTHESIS_TYPES: raise ValueError("unsupported synthesis_type: "+str(typ))
    if status not in SYNTHESIS_STATUSES: raise ValueError("unsupported synthesis status: "+str(status))
    r=ResearchEvidenceSynthesisRecord(project_entity_id=p.project_entity_id, synthesis_key=key, title=title, synthesis_type=typ, status=status, research_question_ref=payload.get("research_question_ref"), protocol_ref=payload.get("protocol_ref"), eligibility_json=payload.get("eligibility",{}), search_manifest_json=payload.get("search_manifest",{}), provenance_json=payload.get("provenance",{}), metadata_json=payload.get("metadata",{}), created_by=payload.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_study(db, synthesis_id, payload):
    _reject(payload); s=_synthesis(db,synthesis_id)
    key=str(payload.get("study_key") or "").strip(); ref=str(payload.get("source_ref") or "").strip(); typ=payload.get("source_type","publication"); inc=payload.get("inclusion_status","pending"); pub_id=payload.get("publication_id")
    if not key or not ref: raise ValueError("study_key and source_ref are required.")
    if typ not in SOURCE_TYPES: raise ValueError("unsupported source_type: "+str(typ))
    if inc not in INCLUSION_STATUSES: raise ValueError("unsupported inclusion_status: "+str(inc))
    if pub_id is not None and db.get(ResearchPublicationRecord,pub_id) is None: raise ValueError("publication_id must reference a v2.81 research publication.")
    r=ResearchSynthesisStudyRecord(project_entity_id=s.project_entity_id,synthesis_id=synthesis_id,study_key=key,source_type=typ,source_ref=ref,publication_id=pub_id,title=payload.get("title"),inclusion_status=inc,inclusion_reason=payload.get("inclusion_reason"),population_json=payload.get("population",{}),intervention_json=payload.get("intervention",{}),comparator_json=payload.get("comparator",{}),outcome_refs_json=payload.get("outcome_refs",[]),evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_outcome(db,synthesis_id,payload):
    _reject(payload); s=_synthesis(db,synthesis_id); key=str(payload.get("outcome_key") or "").strip(); label=str(payload.get("label") or "").strip()
    if not key or not label: raise ValueError("outcome_key and label are required.")
    r=ResearchSynthesisOutcomeRecord(project_entity_id=s.project_entity_id,synthesis_id=synthesis_id,outcome_key=key,label=label,construct=payload.get("construct"),measure=payload.get("measure"),unit=payload.get("unit"),timepoint=payload.get("timepoint"),definition_text=payload.get("definition_text"),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_effect(db,synthesis_id,payload):
    _reject(payload); s=_synthesis(db,synthesis_id); st=_study(db,payload.get("study_id")); outcome=_outcome(db,payload.get("outcome_id")); key=str(payload.get("effect_key") or "").strip(); measure=str(payload.get("effect_measure") or "").strip(); direction=payload.get("declared_direction","unspecified")
    if st.synthesis_id != synthesis_id: raise ValueError("study_id must belong to synthesis_id.")
    if outcome is not None and outcome.synthesis_id != synthesis_id: raise ValueError("outcome_id must belong to synthesis_id.")
    if not key or not measure: raise ValueError("effect_key and effect_measure are required.")
    if direction not in DIRECTIONS: raise ValueError("unsupported declared_direction: "+str(direction))
    if payload.get("externally_computed",True) is not True: raise ValueError("effect estimates must be supplied as externally computed or source-reported evidence; Core does not compute effect sizes.")
    r=ResearchSynthesisEffectRecord(project_entity_id=s.project_entity_id,synthesis_id=synthesis_id,study_id=st.id,outcome_id=None if outcome is None else outcome.id,effect_key=key,effect_measure=measure,estimate_json=payload.get("estimate",{}),uncertainty_json=payload.get("uncertainty",{}),sample_size_json=payload.get("sample_size",{}),declared_direction=direction,source_ref=payload.get("source_ref"),externally_computed=True,provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_meta_analysis(db,synthesis_id,payload):
    _reject(payload); s=_synthesis(db,synthesis_id); outcome=_outcome(db,payload.get("outcome_id")); key=str(payload.get("analysis_key") or "").strip(); method=str(payload.get("method_ref") or "").strip(); measure=str(payload.get("effect_measure") or "").strip(); model=payload.get("model_type","random_effects")
    if outcome is not None and outcome.synthesis_id != synthesis_id: raise ValueError("outcome_id must belong to synthesis_id.")
    if not key or not method or not measure: raise ValueError("analysis_key, method_ref, and effect_measure are required.")
    if model not in MODEL_TYPES: raise ValueError("unsupported model_type: "+str(model))
    if payload.get("externally_computed",True) is not True: raise ValueError("meta-analysis results must be externally computed; Core does not pool estimates.")
    r=ResearchMetaAnalysisRecord(project_entity_id=s.project_entity_id,synthesis_id=synthesis_id,outcome_id=None if outcome is None else outcome.id,analysis_key=key,method_ref=method,model_type=model,effect_measure=measure,pooled_estimate_json=payload.get("pooled_estimate",{}),heterogeneity_json=payload.get("heterogeneity",{}),prediction_interval_json=payload.get("prediction_interval",{}),study_refs_json=payload.get("study_refs",[]),execution_refs_json=payload.get("execution_refs",[]),interpretation_text=payload.get("interpretation_text"),externally_computed=True,provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_assessment(db,synthesis_id,payload):
    _reject(payload); s=_synthesis(db,synthesis_id); key=str(payload.get("assessment_key") or "").strip(); target_type=str(payload.get("target_type") or "").strip(); target_ref=str(payload.get("target_ref") or "").strip(); dim=payload.get("dimension"); judgment=str(payload.get("declared_judgment") or "").strip()
    if not key or not target_type or not target_ref or not dim or not judgment: raise ValueError("assessment_key, target_type, target_ref, dimension, and declared_judgment are required.")
    if dim not in ASSESSMENT_DIMENSIONS: raise ValueError("unsupported assessment dimension: "+str(dim))
    r=ResearchMetaResearchAssessmentRecord(project_entity_id=s.project_entity_id,synthesis_id=synthesis_id,assessment_key=key,target_type=target_type,target_ref=target_ref,dimension=dim,framework_ref=payload.get("framework_ref"),declared_judgment=judgment,rationale_text=payload.get("rationale_text"),evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_relation(db,synthesis_id,payload):
    _reject(payload); s=_synthesis(db,synthesis_id); key=str(payload.get("relation_key") or "").strip(); source=str(payload.get("source_ref") or "").strip(); target=str(payload.get("target_ref") or "").strip(); typ=payload.get("relation_type")
    if not key or not source or not target or not typ: raise ValueError("relation_key, source_ref, target_ref, and relation_type are required.")
    if typ not in RELATION_TYPES: raise ValueError("unsupported relation_type: "+str(typ))
    r=ResearchSynthesisRelationRecord(project_entity_id=s.project_entity_id,synthesis_id=synthesis_id,relation_key=key,source_ref=source,target_ref=target,relation_type=typ,rationale_text=payload.get("rationale_text"),evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_gap(db,synthesis_id,payload):
    _reject(payload); s=_synthesis(db,synthesis_id); key=str(payload.get("gap_key") or "").strip(); desc=str(payload.get("description_text") or "").strip(); typ=payload.get("gap_type","other"); priority=payload.get("declared_priority","unspecified"); status=payload.get("status","open")
    if not key or not desc: raise ValueError("gap_key and description_text are required.")
    if typ not in GAP_TYPES: raise ValueError("unsupported gap_type: "+str(typ))
    if priority not in GAP_PRIORITIES: raise ValueError("unsupported declared_priority: "+str(priority))
    if status not in GAP_STATUSES: raise ValueError("unsupported gap status: "+str(status))
    r=ResearchEvidenceGapRecord(project_entity_id=s.project_entity_id,synthesis_id=synthesis_id,gap_key=key,gap_type=typ,description_text=desc,declared_priority=priority,status=status,evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def revise_synthesis(db,synthesis_id,payload):
    _reject(payload); s=_synthesis(db,synthesis_id); prior=_ser(s)
    for fld in ("title","synthesis_type","status","research_question_ref","protocol_ref"):
        if fld in payload:
            if fld=="synthesis_type" and payload[fld] not in SYNTHESIS_TYPES: raise ValueError("unsupported synthesis_type: "+str(payload[fld]))
            if fld=="status" and payload[fld] not in SYNTHESIS_STATUSES: raise ValueError("unsupported synthesis status: "+str(payload[fld]))
            setattr(s,fld,payload[fld])
    for fld,attr in (("eligibility","eligibility_json"),("search_manifest","search_manifest_json"),("provenance","provenance_json"),("metadata","metadata_json")):
        if fld in payload: setattr(s,attr,payload[fld])
    n=db.scalar(select(func.max(ResearchEvidenceSynthesisRevisionRecord.revision)).where(ResearchEvidenceSynthesisRevisionRecord.synthesis_id==synthesis_id)) or 0
    revised=_ser(s); h=_hash(revised)
    r=ResearchEvidenceSynthesisRevisionRecord(project_entity_id=s.project_entity_id,synthesis_id=synthesis_id,revision=int(n)+1,state_hash=h,prior_state_json=prior,revised_state_json=revised,change_summary=payload.get("change_summary"),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(s); db.add(r); db.commit(); db.refresh(r); return _ser(r)

def _rows(db,cls,synthesis_id):
    return [_ser(x) for x in db.scalars(select(cls).where(cls.synthesis_id==synthesis_id)).all()]

def descriptive_summary(db,synthesis_id,public=False):
    s=_synthesis(db,synthesis_id); p=_project(db,s.project_entity_id)
    if public and p.visibility!="public": raise ValueError("research project is not public.")
    studies=db.scalars(select(ResearchSynthesisStudyRecord).where(ResearchSynthesisStudyRecord.synthesis_id==synthesis_id)).all()
    effects=db.scalars(select(ResearchSynthesisEffectRecord).where(ResearchSynthesisEffectRecord.synthesis_id==synthesis_id)).all()
    analyses=db.scalars(select(ResearchMetaAnalysisRecord).where(ResearchMetaAnalysisRecord.synthesis_id==synthesis_id)).all()
    assessments=db.scalars(select(ResearchMetaResearchAssessmentRecord).where(ResearchMetaResearchAssessmentRecord.synthesis_id==synthesis_id)).all()
    relations=db.scalars(select(ResearchSynthesisRelationRecord).where(ResearchSynthesisRelationRecord.synthesis_id==synthesis_id)).all()
    gaps=db.scalars(select(ResearchEvidenceGapRecord).where(ResearchEvidenceGapRecord.synthesis_id==synthesis_id)).all()
    return {
        "release":"2.83.0","contract":CONTRACT,"synthesis_id":synthesis_id,
        "declared_inclusion_statuses":dict(Counter(x.inclusion_status for x in studies)),
        "declared_effect_directions":dict(Counter(x.declared_direction for x in effects)),
        "meta_analysis_model_types":dict(Counter(x.model_type for x in analyses)),
        "assessment_dimensions":dict(Counter(x.dimension for x in assessments)),
        "declared_cross_study_relations":dict(Counter(x.relation_type for x in relations)),
        "evidence_gap_types":dict(Counter(x.gap_type for x in gaps)),
        "summary_is_descriptive_only":True,"pooled_estimate_computed_by_core":False,"study_quality_scored_by_core":False,"bias_inferred_by_core":False,"causality_inferred_by_core":False,"truth_inferred_by_core":False,
    }

def lineage(db,synthesis_id,public=False):
    s=_synthesis(db,synthesis_id); p=_project(db,s.project_entity_id)
    if public and p.visibility!="public": raise ValueError("research project is not public.")
    studies=_rows(db,ResearchSynthesisStudyRecord,synthesis_id); effects=_rows(db,ResearchSynthesisEffectRecord,synthesis_id); analyses=_rows(db,ResearchMetaAnalysisRecord,synthesis_id); assessments=_rows(db,ResearchMetaResearchAssessmentRecord,synthesis_id); relations=_rows(db,ResearchSynthesisRelationRecord,synthesis_id); gaps=_rows(db,ResearchEvidenceGapRecord,synthesis_id)
    return {
        "release":"2.83.0","contract":CONTRACT,"project_ref":s.project_entity_id,"synthesis":_ser(s),
        "study_source_edges":[{"study_id":x["id"],"source_ref":x["source_ref"],"publication_id":x.get("publication_id"),"evidence_refs":x.get("evidence_refs",[])} for x in studies],
        "effect_edges":[{"effect_id":x["id"],"study_id":x["study_id"],"outcome_id":x.get("outcome_id"),"source_ref":x.get("source_ref")} for x in effects],
        "meta_analysis_edges":[{"analysis_id":x["id"],"outcome_id":x.get("outcome_id"),"study_refs":x.get("study_refs",[]),"execution_refs":x.get("execution_refs",[])} for x in analyses],
        "assessment_edges":[{"assessment_id":x["id"],"target_type":x["target_type"],"target_ref":x["target_ref"],"evidence_refs":x.get("evidence_refs",[])} for x in assessments],
        "declared_relation_edges":[{"relation_id":x["id"],"source_ref":x["source_ref"],"target_ref":x["target_ref"],"relation_type":x["relation_type"]} for x in relations],
        "gap_evidence_edges":[{"gap_id":x["id"],"evidence_refs":x.get("evidence_refs",[])} for x in gaps],
        "lineage_is_declared_not_inferred":True,"missing_links_inferred_by_core":False,
    }

def bundle(db,synthesis_id,public=False):
    s=_synthesis(db,synthesis_id); p=_project(db,s.project_entity_id)
    if public and p.visibility!="public": raise ValueError("research project is not public.")
    return {
        "release":"2.83.0","contract":CONTRACT,"project":_ser(p),"synthesis":_ser(s),
        "studies":_rows(db,ResearchSynthesisStudyRecord,synthesis_id),
        "outcomes":_rows(db,ResearchSynthesisOutcomeRecord,synthesis_id),
        "effects":_rows(db,ResearchSynthesisEffectRecord,synthesis_id),
        "meta_analyses":_rows(db,ResearchMetaAnalysisRecord,synthesis_id),
        "meta_research_assessments":_rows(db,ResearchMetaResearchAssessmentRecord,synthesis_id),
        "cross_study_relations":_rows(db,ResearchSynthesisRelationRecord,synthesis_id),
        "evidence_gaps":_rows(db,ResearchEvidenceGapRecord,synthesis_id),
        "revisions":_rows(db,ResearchEvidenceSynthesisRevisionRecord,synthesis_id),
        "snapshots":_rows(db,ResearchEvidenceSynthesisSnapshotRecord,synthesis_id),
        "descriptive_summary":descriptive_summary(db,synthesis_id,public),"lineage":lineage(db,synthesis_id,public),**boundaries(),
    }

def snapshot(db,synthesis_id,payload):
    _reject(payload); s=_synthesis(db,synthesis_id); state=bundle(db,synthesis_id); state.pop("snapshots",None); h=_hash(state)
    prev=db.scalar(select(ResearchEvidenceSynthesisSnapshotRecord).where(ResearchEvidenceSynthesisSnapshotRecord.synthesis_id==synthesis_id).order_by(ResearchEvidenceSynthesisSnapshotRecord.revision.desc()).limit(1)); rev=1 if prev is None else prev.revision+1
    r=ResearchEvidenceSynthesisSnapshotRecord(project_entity_id=s.project_entity_id,synthesis_id=synthesis_id,revision=rev,content_hash=h,previous_snapshot_hash=None if prev is None else prev.content_hash,state_json=state,provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)
