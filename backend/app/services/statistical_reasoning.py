from __future__ import annotations
from datetime import datetime, timezone
import hashlib, json
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import (
    AnalyticalResultObjectRecord, AnalyticalRuntimeProviderRecord,
    StatisticalReasoningObjectRecord, StatisticalDiagnosticEvidenceRecord,
    StatisticalAssumptionRecordV330, StatisticalRobustnessEvidenceRecord,
    StatisticalModelComparisonRecord, StatisticalCoefficientRecord,
    StatisticalIntervalRecord, StatisticalInterpretationRecord,
    StatisticalReasoningSnapshotRecord,
)

RELEASE = "3.3.0"
CONTRACT = "sc.core.statistical-reasoning-object-model.v1"
SOURCE_CONTRACT = "sc.analytics-r.statistical-diagnostics-validation.v1"
CATALYST_R_VERSION = "2.2.0"
WORKSPACE_ADAPTER_RELEASE = "3.9.1"
ASSUMPTION_STATUSES = {"declared","supported","challenged","failed","not_assessed"}
DIAGNOSTIC_TYPES = {"fit_metric","residual","assumption_test","robustness","numerical","calibration","comparison"}
REVIEW_STATUSES = {"unreviewed","in_review","reviewed"}
FORBIDDEN = (
    "execute_analysis_by_core", "infer_statistical_significance_by_core",
    "certify_scientific_validity_by_core", "select_preferred_model_by_core",
    "infer_causality_by_core", "determine_truth_by_core", "rank_models_by_core",
)

def _canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str)
def _hash(v): return hashlib.sha256(_canon(v).encode()).hexdigest()
def _ser(x):
    d={c.name:getattr(x,c.name) for c in x.__table__.columns}
    for k,v in list(d.items()):
        if hasattr(v,"isoformat"): d[k]=v.isoformat()
    for k in list(d):
        if k.endswith("_json"): d[k[:-5]]=d.pop(k)
    return d

def _reject(p):
    for k in FORBIDDEN:
        if p.get(k) is True: raise ValueError(f"Core boundary forbids {k}")

def _strings(v,name):
    if v is None: return []
    if not isinstance(v,list) or any(not isinstance(x,str) or not x for x in v): raise ValueError(f"{name} must be an array of string references")
    return v

def _result(db,result_ref):
    r=db.get(AnalyticalResultObjectRecord,result_ref)
    if r is None: r=db.scalar(select(AnalyticalResultObjectRecord).where(AnalyticalResultObjectRecord.result_ref==result_ref))
    if r is None: raise ValueError("analytical result object not found")
    return r

def _reasoning(db,reasoning_ref):
    r=db.get(StatisticalReasoningObjectRecord,reasoning_ref)
    if r is None: r=db.scalar(select(StatisticalReasoningObjectRecord).where(StatisticalReasoningObjectRecord.reasoning_ref==reasoning_ref))
    if r is None: raise ValueError("statistical reasoning object not found")
    return r

def _scalar(v): return {} if v is None else {"value":v}

def readiness(db:Session):
    provider=db.scalar(select(AnalyticalRuntimeProviderRecord).where(AnalyticalRuntimeProviderRecord.provider_key=="catalystanalyticsr"))
    def count(cls): return len(db.scalars(select(cls.id)).all())
    out={
        "release":RELEASE,"contract":CONTRACT,"source_contract":SOURCE_CONTRACT,"migration_0105_applied":True,
        "catalyst_analytics_r_version":provider.provider_version if provider else None,
        "workspace_adapter_release":WORKSPACE_ADAPTER_RELEASE,
        "counts":{"reasoning_objects":count(StatisticalReasoningObjectRecord),"diagnostics":count(StatisticalDiagnosticEvidenceRecord),"assumptions":count(StatisticalAssumptionRecordV330),"robustness_evidence":count(StatisticalRobustnessEvidenceRecord),"model_comparisons":count(StatisticalModelComparisonRecord),"coefficients":count(StatisticalCoefficientRecord),"intervals":count(StatisticalIntervalRecord),"interpretations":count(StatisticalInterpretationRecord),"snapshots":count(StatisticalReasoningSnapshotRecord)},
        "diagnostic_evidence_objects":True,"assumption_objects":True,"robustness_evidence_objects":True,"model_comparison_evidence_objects":True,"coefficient_objects":True,"interval_objects":True,"researcher_interpretation_provenance":True,"immutable_reasoning_snapshots":True,"analytics_r_validation_ingestion":True,
        "evidence_only":True,"human_review_required":True,"p_values_are_evidence_not_validity":True,
    }
    out.update({k:False for k in FORBIDDEN}); return out

def _snapshot_state(db,r):
    def rows(cls,order): return [_ser(x) for x in db.scalars(select(cls).where(cls.reasoning_id==r.id).order_by(order)).all()]
    return {"reasoning":_ser(r),"diagnostics":rows(StatisticalDiagnosticEvidenceRecord,StatisticalDiagnosticEvidenceRecord.diagnostic_ref),"assumptions":rows(StatisticalAssumptionRecordV330,StatisticalAssumptionRecordV330.assumption_ref),"robustness_evidence":rows(StatisticalRobustnessEvidenceRecord,StatisticalRobustnessEvidenceRecord.robustness_ref),"model_comparisons":rows(StatisticalModelComparisonRecord,StatisticalModelComparisonRecord.comparison_ref),"coefficients":rows(StatisticalCoefficientRecord,StatisticalCoefficientRecord.coefficient_ref),"intervals":rows(StatisticalIntervalRecord,StatisticalIntervalRecord.interval_ref),"interpretations":rows(StatisticalInterpretationRecord,StatisticalInterpretationRecord.interpretation_ref)}

def create_snapshot(db,reasoning_ref,p=None):
    p=p or {}; _reject(p); r=_reasoning(db,reasoning_ref); state=_snapshot_state(db,r); h=_hash(state)
    existing=db.scalar(select(StatisticalReasoningSnapshotRecord).where(StatisticalReasoningSnapshotRecord.reasoning_id==r.id,StatisticalReasoningSnapshotRecord.snapshot_hash==h))
    if existing: return {**_ser(existing),"idempotent_replay":True}
    prev=db.scalar(select(StatisticalReasoningSnapshotRecord).where(StatisticalReasoningSnapshotRecord.reasoning_id==r.id).order_by(StatisticalReasoningSnapshotRecord.created_at.desc()))
    x=StatisticalReasoningSnapshotRecord(snapshot_ref=p.get("snapshot_ref") or f"snapshot:{r.reasoning_ref}:{h[:16]}",reasoning_id=r.id,snapshot_hash=h,previous_snapshot_hash=prev.snapshot_hash if prev else None,state_json=state,provenance_json=p.get("provenance",{}),visibility=p.get("visibility",r.visibility),created_by=p.get("created_by","operator"))
    db.add(x); db.flush(); return {**_ser(x),"idempotent_replay":False}

def ingest_validation_bundle(db:Session,p):
    _reject(p)
    result=_result(db,p["result_ref"]); evidence=p.get("evidence")
    if not isinstance(evidence,dict): raise ValueError("evidence must be an object")
    required=("schema_version","bundle_type","contract","id","analysis_ref","diagnostics","assumptions","robustness","comparisons","review_status","summary","provenance","boundary")
    miss=[k for k in required if k not in evidence]
    if miss: raise ValueError("statistical validation evidence missing fields: "+", ".join(miss))
    if evidence["schema_version"]!="1.0.0" or evidence["bundle_type"]!="statistical_validation_evidence" or evidence["contract"]!=SOURCE_CONTRACT: raise ValueError("unsupported statistical validation evidence contract")
    if evidence["review_status"] not in REVIEW_STATUSES: raise ValueError("unsupported statistical validation review status")
    b=evidence.get("boundary") or {}
    required_boundary=("evidence_only","no_automatic_scientific_validity_certification","no_automatic_significance_conclusion","no_automatic_model_selection","human_review_required")
    if any(b.get(k) is not True for k in required_boundary): raise ValueError("statistical validation evidence boundary is invalid")
    provider=db.get(AnalyticalRuntimeProviderRecord,result.provider_id)
    if not provider or provider.provider_key!="catalystanalyticsr" or provider.provider_version!=CATALYST_R_VERSION: raise ValueError("statistical validation ingestion requires Catalyst Analytics R 2.2.0 result provenance")
    package=(evidence.get("provenance") or {}).get("package") or {}
    if package.get("name") not in (None,"catalystanalyticsr") or package.get("version") not in (None,CATALYST_R_VERSION): raise ValueError("statistical validation provenance package/version mismatch")
    fingerprint=_hash(evidence); existing=db.scalar(select(StatisticalReasoningObjectRecord).where(StatisticalReasoningObjectRecord.source_bundle_ref==evidence["id"]))
    if existing:
        if existing.evidence_fingerprint!=fingerprint or existing.result_id!=result.id: raise ValueError("source statistical bundle already exists with different content or result binding")
        return {"release":RELEASE,"contract":CONTRACT,"reasoning":_ser(existing),"idempotent_replay":True,"evidence_fingerprint":fingerprint}
    visibility=p.get("visibility",result.visibility); reasoning_ref=p.get("reasoning_ref") or f"statistical-reasoning:{evidence['id']}"
    r=StatisticalReasoningObjectRecord(reasoning_ref=reasoning_ref,result_id=result.id,source_bundle_ref=evidence["id"],source_contract=SOURCE_CONTRACT,analysis_ref=evidence["analysis_ref"],model_ref=evidence.get("model_ref"),source_status=evidence.get("source_status"),review_status=evidence["review_status"],summary_json=evidence.get("summary",{}),limitations_json=_strings(evidence.get("limitations",[]),"limitations"),provenance_json=evidence.get("provenance",{}),evidence_fingerprint=fingerprint,visibility=visibility)
    db.add(r); db.flush()
    for d in evidence["diagnostics"]:
        if d.get("record_type")!="statistical_diagnostic" or d.get("diagnostic_type") not in DIAGNOSTIC_TYPES: raise ValueError("invalid statistical diagnostic record")
        pv=d.get("p_value")
        if pv is not None and not (0 <= float(pv) <= 1): raise ValueError("diagnostic p_value must be in [0,1]")
        db.add(StatisticalDiagnosticEvidenceRecord(reasoning_id=r.id,diagnostic_ref=d["id"],diagnostic_type=d["diagnostic_type"],name=d["name"],observed_json=_scalar(d.get("observed")),reference_json=_scalar(d.get("reference")),operator=d.get("operator"),p_value=float(pv) if pv is not None else None,method_ref=d.get("method_ref"),units=d.get("units"),evidence_refs_json=_strings(d.get("evidence_refs",[]),"diagnostic evidence_refs"),notes_json=_strings(d.get("notes",[]),"diagnostic notes"),boundary_json=d.get("boundary",{}),visibility=visibility))
    for a in evidence["assumptions"]:
        if a.get("record_type")!="statistical_assumption" or a.get("status") not in ASSUMPTION_STATUSES: raise ValueError("invalid statistical assumption record")
        db.add(StatisticalAssumptionRecordV330(reasoning_id=r.id,assumption_ref=a["id"],label=a.get("label",a["id"]),statement=a.get("statement",a.get("label",a["id"])),status=a["status"],evidence_refs_json=_strings(a.get("evidence_refs",[]),"assumption evidence_refs"),limitations_json=_strings(a.get("limitations",[]),"assumption limitations"),boundary_json=a.get("boundary",{}),visibility=visibility))
    for x in evidence["robustness"]:
        if x.get("record_type")!="robustness_evidence": raise ValueError("invalid robustness evidence record")
        db.add(StatisticalRobustnessEvidenceRecord(reasoning_id=r.id,robustness_ref=x["id"],method_ref=x["method_ref"],target_ref=x["target_ref"],result_json=x.get("result",{}),evidence_refs_json=_strings(x.get("evidence_refs",[]),"robustness evidence_refs"),limitations_json=_strings(x.get("limitations",[]),"robustness limitations"),boundary_json=x.get("boundary",{}),visibility=visibility))
    for x in evidence["comparisons"]:
        if x.get("record_type")!="model_comparison_evidence": raise ValueError("invalid model comparison record")
        refs=_strings(x.get("model_refs",[]),"model_refs")
        if len(refs)<2: raise ValueError("model comparison requires at least two model refs")
        db.add(StatisticalModelComparisonRecord(reasoning_id=r.id,comparison_ref=x["id"],model_refs_json=refs,criteria_json=x.get("criteria",{}),evidence_refs_json=_strings(x.get("evidence_refs",[]),"comparison evidence_refs"),notes_json=_strings(x.get("notes",[]),"comparison notes"),boundary_json=x.get("boundary",{}),visibility=visibility))
    db.flush(); snap=create_snapshot(db,r.reasoning_ref,{"visibility":visibility,"created_by":"analytics-r-diagnostics-ingest","provenance":{"source_contract":SOURCE_CONTRACT,"evidence_fingerprint":fingerprint}}); db.commit(); db.refresh(r)
    return {"release":RELEASE,"contract":CONTRACT,"reasoning":_ser(r),"snapshot":snap,"idempotent_replay":False,"evidence_fingerprint":fingerprint}

def record_coefficient(db,reasoning_ref,p):
    _reject(p); r=_reasoning(db,reasoning_ref); pv=p.get("p_value")
    if pv is not None and not (0 <= float(pv) <= 1): raise ValueError("coefficient p_value must be in [0,1]")
    existing=db.scalar(select(StatisticalCoefficientRecord).where(StatisticalCoefficientRecord.reasoning_id==r.id,StatisticalCoefficientRecord.coefficient_ref==p["coefficient_ref"]))
    if existing: return _ser(existing)
    x=StatisticalCoefficientRecord(reasoning_id=r.id,coefficient_ref=p["coefficient_ref"],term=p["term"],estimate=p.get("estimate"),standard_error=p.get("standard_error"),statistic=p.get("statistic"),p_value=pv,unit=p.get("unit"),interval_ref=p.get("interval_ref"),evidence_refs_json=_strings(p.get("evidence_refs",[]),"evidence_refs"),provenance_json=p.get("provenance",{}),visibility=p.get("visibility",r.visibility)); db.add(x); db.commit(); db.refresh(x); return _ser(x)

def record_interval(db,reasoning_ref,p):
    _reject(p); r=_reasoning(db,reasoning_ref); level=p.get("level")
    if level is not None and not (0 < float(level) <= 1): raise ValueError("interval level must be in (0,1]")
    lo,hi=p.get("lower"),p.get("upper")
    if lo is not None and hi is not None and float(lo)>float(hi): raise ValueError("interval lower must not exceed upper")
    existing=db.scalar(select(StatisticalIntervalRecord).where(StatisticalIntervalRecord.reasoning_id==r.id,StatisticalIntervalRecord.interval_ref==p["interval_ref"]))
    if existing: return _ser(existing)
    x=StatisticalIntervalRecord(reasoning_id=r.id,interval_ref=p["interval_ref"],interval_type=p["interval_type"],level=float(level) if level is not None else None,lower=lo,upper=hi,method_ref=p.get("method_ref"),unit=p.get("unit"),target_ref=p.get("target_ref"),evidence_refs_json=_strings(p.get("evidence_refs",[]),"evidence_refs"),provenance_json=p.get("provenance",{}),visibility=p.get("visibility",r.visibility)); db.add(x); db.commit(); db.refresh(x); return _ser(x)

def record_interpretation(db,reasoning_ref,p):
    _reject(p); r=_reasoning(db,reasoning_ref)
    if p.get("human_authored") is not True: raise ValueError("statistical interpretations must be explicitly human-authored")
    if not p.get("author_ref") or not p.get("statement"): raise ValueError("author_ref and statement are required")
    existing=db.scalar(select(StatisticalInterpretationRecord).where(StatisticalInterpretationRecord.reasoning_id==r.id,StatisticalInterpretationRecord.interpretation_ref==p["interpretation_ref"]))
    if existing: return _ser(existing)
    x=StatisticalInterpretationRecord(reasoning_id=r.id,interpretation_ref=p["interpretation_ref"],interpretation_type=p.get("interpretation_type","researcher_interpretation"),statement=p["statement"],author_ref=p["author_ref"],evidence_refs_json=_strings(p.get("evidence_refs",[]),"evidence_refs"),limitations_json=_strings(p.get("limitations",[]),"limitations"),provenance_json=p.get("provenance",{}),human_authored=True,visibility=p.get("visibility",r.visibility)); db.add(x); db.commit(); db.refresh(x); return _ser(x)

def reasoning_bundle(db,reasoning_ref,public=False):
    r=_reasoning(db,reasoning_ref)
    if public and r.visibility!="public": raise ValueError("statistical reasoning object not public")
    result=db.get(AnalyticalResultObjectRecord,r.result_id)
    def rows(cls,order):
        q=select(cls).where(cls.reasoning_id==r.id).order_by(order)
        if public and hasattr(cls,"visibility"): q=q.where(cls.visibility=="public")
        return [_ser(x) for x in db.scalars(q).all()]
    return {"release":RELEASE,"contract":CONTRACT,"source_contract":SOURCE_CONTRACT,"reasoning":_ser(r),"analytical_result":_ser(result) if result else None,"diagnostics":rows(StatisticalDiagnosticEvidenceRecord,StatisticalDiagnosticEvidenceRecord.created_at),"assumptions":rows(StatisticalAssumptionRecordV330,StatisticalAssumptionRecordV330.created_at),"robustness_evidence":rows(StatisticalRobustnessEvidenceRecord,StatisticalRobustnessEvidenceRecord.created_at),"model_comparisons":rows(StatisticalModelComparisonRecord,StatisticalModelComparisonRecord.created_at),"coefficients":rows(StatisticalCoefficientRecord,StatisticalCoefficientRecord.created_at),"intervals":rows(StatisticalIntervalRecord,StatisticalIntervalRecord.created_at),"interpretations":rows(StatisticalInterpretationRecord,StatisticalInterpretationRecord.created_at),"snapshots":rows(StatisticalReasoningSnapshotRecord,StatisticalReasoningSnapshotRecord.created_at),"evidence_only":True,"human_review_required":True,"core_certifies_scientific_validity":False,"core_infers_statistical_significance":False,"core_selects_preferred_model":False}
