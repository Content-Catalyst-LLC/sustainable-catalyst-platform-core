from __future__ import annotations
import hashlib, json
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import (
    AnalyticalResultObjectRecord, StatisticalReasoningObjectRecord,
    UncertaintyEvidenceStudyRecord, UncertaintyDistributionEvidenceRecord,
    ProbabilisticSummaryEvidenceRecord, SensitivityIndexEvidenceRecord,
    UncertaintyEnsembleEvidenceRecord, UncertaintyEvidenceInterpretationRecord,
    UncertaintyEvidenceSnapshotRecord,
)
RELEASE="3.21.0"
CONTRACT="sc.core.uncertainty-probabilistic-evidence.v1"
SOURCE_CONTRACT="sc.analytics-r.uncertainty-sensitivity-runtime.v1"
ANALYTICS_R_VERSION="2.3.0"
WORKSPACE_ADAPTER_RELEASE="3.9.2"
METHODS={"monte_carlo","latin_hypercube","morris","sobol"}
FORBIDDEN=("execute_uncertainty_by_core","infer_causality_by_core","rank_parameters_by_core","select_policy_by_core","certify_scientific_validity_by_core","determine_truth_by_core")
def _canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),default=str)
def _hash(v): return hashlib.sha256(_canon(v).encode()).hexdigest()
def _ser(x):
    d={c.name:getattr(x,c.name) for c in x.__table__.columns}
    for k,v in list(d.items()):
        if hasattr(v,"isoformat"): d[k]=v.isoformat()
        if k.endswith("_json"): d[k[:-5]]=d.pop(k)
    return d
def _reject(p):
    for k in FORBIDDEN:
        if p.get(k) is True: raise ValueError(f"Core boundary forbids {k}")
def _study(db,ref):
    x=db.scalar(select(UncertaintyEvidenceStudyRecord).where(UncertaintyEvidenceStudyRecord.study_ref==ref))
    if not x: raise ValueError("uncertainty evidence study not found")
    return x
def readiness(db:Session):
    def n(cls): return len(db.scalars(select(cls.id)).all())
    out={"release":RELEASE,"contract":CONTRACT,"source_contract":SOURCE_CONTRACT,"migration_0108_applied":True,"analytics_r_target_version":ANALYTICS_R_VERSION,"workspace_adapter_target_release":WORKSPACE_ADAPTER_RELEASE,"methods":sorted(METHODS),"counts":{"studies":n(UncertaintyEvidenceStudyRecord),"distributions":n(UncertaintyDistributionEvidenceRecord),"probabilistic_summaries":n(ProbabilisticSummaryEvidenceRecord),"sensitivity_indices":n(SensitivityIndexEvidenceRecord),"ensembles":n(UncertaintyEnsembleEvidenceRecord),"interpretations":n(UncertaintyEvidenceInterpretationRecord),"snapshots":n(UncertaintyEvidenceSnapshotRecord)},"evidence_only":True,"human_review_required":True,"uncertainty_is_evidence_not_truth":True,"sensitivity_does_not_establish_causality":True}
    out.update({k:False for k in FORBIDDEN}); return out
def _snapshot_state(db,s):
    def rows(cls): return [_ser(x) for x in db.scalars(select(cls).where(cls.study_id==s.id).order_by(cls.created_at)).all()]
    return {"study":_ser(s),"distributions":rows(UncertaintyDistributionEvidenceRecord),"probabilistic_summaries":rows(ProbabilisticSummaryEvidenceRecord),"sensitivity_indices":rows(SensitivityIndexEvidenceRecord),"ensembles":rows(UncertaintyEnsembleEvidenceRecord),"interpretations":rows(UncertaintyEvidenceInterpretationRecord)}
def snapshot(db,study_ref,p=None):
    p=p or {}; _reject(p); s=_study(db,study_ref); state=_snapshot_state(db,s); h=_hash(state)
    old=db.scalar(select(UncertaintyEvidenceSnapshotRecord).where(UncertaintyEvidenceSnapshotRecord.study_id==s.id,UncertaintyEvidenceSnapshotRecord.snapshot_hash==h))
    if old:return {**_ser(old),"idempotent_replay":True}
    prev=db.scalar(select(UncertaintyEvidenceSnapshotRecord).where(UncertaintyEvidenceSnapshotRecord.study_id==s.id).order_by(UncertaintyEvidenceSnapshotRecord.created_at.desc()))
    x=UncertaintyEvidenceSnapshotRecord(snapshot_ref=p.get("snapshot_ref") or f"snapshot:{s.study_ref}:{h[:16]}",study_id=s.id,snapshot_hash=h,previous_snapshot_hash=prev.snapshot_hash if prev else None,state_json=state,provenance_json=p.get("provenance",{}),visibility=p.get("visibility",s.visibility),created_by=p.get("created_by","operator"));db.add(x);db.flush();return {**_ser(x),"idempotent_replay":False}
def ingest(db:Session,p:dict):
    _reject(p); result=db.scalar(select(AnalyticalResultObjectRecord).where(AnalyticalResultObjectRecord.result_ref==p["result_ref"]))
    if not result: raise ValueError("analytical result object not found")
    e=p.get("evidence") or {}
    if e.get("contract")!=SOURCE_CONTRACT: raise ValueError("unsupported uncertainty/sensitivity source contract")
    if e.get("method") not in METHODS: raise ValueError("unsupported uncertainty/sensitivity method")
    b=e.get("boundary") or {}
    required=("uncertainty_is_evidence_not_truth","sensitivity_does_not_establish_causality","no_automatic_policy_preference","no_automatic_scientific_validity_certification","human_review_required")
    if any(b.get(k) is not True for k in required): raise ValueError("source boundary flags must remain true")
    fp=_hash(e)
    old=db.scalar(select(UncertaintyEvidenceStudyRecord).where(UncertaintyEvidenceStudyRecord.source_fingerprint==fp))
    if old:return {"release":RELEASE,"contract":CONTRACT,"study":_ser(old),"idempotent_replay":True,"source_fingerprint":fp}
    sr=None
    if p.get("statistical_reasoning_ref"):
        sr=db.scalar(select(StatisticalReasoningObjectRecord).where(StatisticalReasoningObjectRecord.reasoning_ref==p["statistical_reasoning_ref"]))
        if not sr: raise ValueError("statistical reasoning object not found")
    s=UncertaintyEvidenceStudyRecord(study_ref=p.get("study_ref") or f"uncertainty:{e.get('analysis_ref')}:{fp[:16]}",result_id=result.id,statistical_reasoning_id=sr.id if sr else None,analysis_ref=e.get("analysis_ref") or result.result_ref,method=e["method"],source_contract=SOURCE_CONTRACT,source_fingerprint=fp,source_refs_json=e.get("source_refs",[]),limitations_json=e.get("limitations",[]),provenance_json=e.get("provenance",{}),boundary_json=b,review_status=p.get("review_status","unreviewed"),visibility=p.get("visibility","internal"));db.add(s);db.flush()
    for i,x in enumerate(e.get("summary",[]) or []):
        target=x.get("target") or x.get("target_ref") or f"summary:{i}"
        db.add(ProbabilisticSummaryEvidenceRecord(study_id=s.id,summary_ref=x.get("id") or f"summary:{s.study_ref}:{i}",target_ref=target,metric=x.get("metric"),statistics_json={k:v for k,v in x.items() if k not in {"id","target","target_ref","metric","probability","n"}},probability_json=x.get("probability",{}) if isinstance(x.get("probability",{}),dict) else {"value":x.get("probability")},sample_size=x.get("n"),provenance_json=e.get("provenance",{})))
    for i,x in enumerate(e.get("sensitivity",[]) or []):
        db.add(SensitivityIndexEvidenceRecord(study_id=s.id,sensitivity_ref=x.get("id") or f"sensitivity:{s.study_ref}:{i}",target_ref=x.get("target") or f"factor:{i}",metric=x.get("metric"),first_order=x.get("first_order"),total_order=x.get("total_order"),elementary_effect_mean=x.get("mean"),elementary_effect_abs_mean=x.get("mu_star"),elementary_effect_sd=x.get("sigma"),variance=x.get("variance"),sample_size=x.get("n"),estimator_json={k:v for k,v in x.items() if "estimator" in k},evidence_refs_json=e.get("source_refs",[]),provenance_json=e.get("provenance",{})))
    for i,x in enumerate(p.get("distributions",[]) or []): db.add(UncertaintyDistributionEvidenceRecord(study_id=s.id,distribution_ref=x.get("distribution_ref") or f"distribution:{s.study_ref}:{i}",target_ref=x["target_ref"],distribution_type=x.get("distribution_type"),parameters_json=x.get("parameters",{}),summary_json=x.get("summary",{}),unit=x.get("unit"),provenance_json=x.get("provenance",{})))
    for i,x in enumerate(p.get("ensembles",[]) or []): db.add(UncertaintyEnsembleEvidenceRecord(study_id=s.id,ensemble_ref=x.get("ensemble_ref") or f"ensemble:{s.study_ref}:{i}",member_refs_json=x.get("member_refs",[]),weights_json=x.get("weights",{}),statistics_json=x.get("statistics",{}),provenance_json=x.get("provenance",{})))
    db.flush(); snap=snapshot(db,s.study_ref,{"created_by":"analytics-r-2.3-ingest","provenance":{"source_contract":SOURCE_CONTRACT,"source_fingerprint":fp}}); db.commit(); db.refresh(s)
    return {"release":RELEASE,"contract":CONTRACT,"study":_ser(s),"snapshot":snap,"idempotent_replay":False,"source_fingerprint":fp}
def interpret(db,study_ref,p):
    _reject(p); s=_study(db,study_ref)
    if p.get("human_authored") is not True: raise ValueError("uncertainty interpretation must be explicitly human-authored")
    if not p.get("author_ref") or not p.get("statement"): raise ValueError("author_ref and statement are required")
    x=UncertaintyEvidenceInterpretationRecord(study_id=s.id,interpretation_ref=p["interpretation_ref"],statement=p["statement"],author_ref=p["author_ref"],evidence_refs_json=p.get("evidence_refs",[]),limitations_json=p.get("limitations",[]),human_authored=True);db.add(x);db.commit();db.refresh(x);return _ser(x)
def bundle(db,study_ref):
    s=_study(db,study_ref); return {"release":RELEASE,"contract":CONTRACT,"source_contract":SOURCE_CONTRACT,**_snapshot_state(db,s),"snapshots":[_ser(x) for x in db.scalars(select(UncertaintyEvidenceSnapshotRecord).where(UncertaintyEvidenceSnapshotRecord.study_id==s.id).order_by(UncertaintyEvidenceSnapshotRecord.created_at)).all()],"evidence_only":True,"human_review_required":True,"core_infers_causality":False,"core_ranks_parameters":False,"core_selects_policy":False}
