from __future__ import annotations
from datetime import datetime
import hashlib, json
from sqlalchemy import func, select
from sqlalchemy.inspection import inspect as sa_inspect
from ..models import (
    ResearchIntegrationCertificationSuiteRecord, ResearchIntegrationCertificationProductRecord,
    ResearchIntegrationCertificationCaseRecord, ResearchIntegrationCertificationRunRecord,
    ResearchIntegrationCertificationCaseResultRecord, ResearchIntegrationCertificationExchangeCheckRecord,
    ResearchIntegrationCertificationTraceCheckRecord, ResearchIntegrationCertificationReproductionCheckRecord,
    ResearchIntegrationCertificationEvidenceRecord, ResearchIntegrationCertificationFindingRecord,
    ResearchIntegrationCertificationRevisionRecord, ResearchIntegrationCertificationSnapshotRecord,
)
CONTRACT="sc.research.platform-integration-certification.v1"
VISIBILITIES={"private","internal","public"}
RESULT_STATUSES={"pass","fail","blocked","not_run","not_applicable"}
FORBIDDEN={
    "invoke_product_by_core","execute_conformance_case_by_core","certify_scientific_validity_by_core",
    "certify_product_quality_by_core","authorize_product_by_certification_by_core","rank_products_by_core",
    "infer_missing_evidence_by_core","infer_reproducibility_by_core","resolve_failed_case_by_core",
    "determine_truth_by_core"
}
CLASSES=[ResearchIntegrationCertificationSuiteRecord,ResearchIntegrationCertificationProductRecord,ResearchIntegrationCertificationCaseRecord,ResearchIntegrationCertificationRunRecord,ResearchIntegrationCertificationCaseResultRecord,ResearchIntegrationCertificationExchangeCheckRecord,ResearchIntegrationCertificationTraceCheckRecord,ResearchIntegrationCertificationReproductionCheckRecord,ResearchIntegrationCertificationEvidenceRecord,ResearchIntegrationCertificationFindingRecord,ResearchIntegrationCertificationRevisionRecord,ResearchIntegrationCertificationSnapshotRecord]
COUNT_NAMES=["suites","products","cases","runs","case_results","exchange_checks","trace_checks","reproduction_checks","evidence","findings","revisions","snapshots"]

def _ser(r):
    o={}
    for a in sa_inspect(r).mapper.column_attrs:
        v=getattr(r,a.key); o[a.key]=v.isoformat() if isinstance(v,datetime) else v
    for k in list(o):
        if k.endswith("_json"): o[k[:-5]]=o.pop(k)
    return o

def _hash(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def _reject(p):
    bad=sorted(k for k in FORBIDDEN if p.get(k) not in (None,False))
    if bad: raise ValueError("Core records platform integration conformance evidence; it does not invoke products, execute conformance cases, certify scientific validity or product quality, authorize/rank products, infer missing evidence or reproducibility, resolve failures, or determine truth: "+", ".join(bad))
def _vis(p):
    v=p.get("visibility","internal")
    if v not in VISIBILITIES: raise ValueError("unsupported visibility")
    return v
def _get(db,cls,i,label):
    r=db.get(cls,i)
    if not r: raise ValueError(label+" not found")
    return r
def _rows(db,cls,public=False,where=None):
    q=select(cls)
    if where is not None: q=q.where(where)
    if public and hasattr(cls,"visibility"): q=q.where(cls.visibility=="public")
    return [_ser(x) for x in db.scalars(q.order_by(cls.created_at,cls.id)).all()]

def boundaries():
    return {
        "certification_suite_registry_by_core":True,"certification_product_registry_by_core":True,
        "conformance_case_registry_by_core":True,"conformance_run_registry_by_core":True,
        "conformance_result_registry_by_core":True,"exchange_check_registry_by_core":True,
        "trace_check_registry_by_core":True,"reproduction_check_registry_by_core":True,
        "certification_evidence_registry_by_core":True,"certification_finding_registry_by_core":True,
        "revision_history_by_core":True,"immutable_certification_snapshots_by_core":True,
        "certification_means_runtime_contract_conformance_not_scientific_validity":True,
        **{k:False for k in FORBIDDEN},
    }

def readiness(db):
    counts={n:db.scalar(select(func.count()).select_from(c)) or 0 for c,n in zip(CLASSES,COUNT_NAMES)}
    return {"release":"2.97.0","contract":CONTRACT,"result_statuses":sorted(RESULT_STATUSES),"counts":counts,"migration_0101_applied":True,**boundaries()}

def create_suite(db,p):
    _reject(p); r=ResearchIntegrationCertificationSuiteRecord(suite_key=p["suite_key"],title=p["title"],contract_ref=p.get("contract_ref","sc.research.unified-runtime-contract.v1"),contract_version=p.get("contract_version","1.0"),status=p.get("status","active"),required_operations_json=p.get("required_operations",[]),required_capabilities_json=p.get("required_capabilities",[]),visibility=_vis(p),metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_product(db,p):
    _reject(p); _get(db,ResearchIntegrationCertificationSuiteRecord,p["suite_id"],"suite"); r=ResearchIntegrationCertificationProductRecord(product_key=p["product_key"],suite_id=p["suite_id"],product_ref=p["product_ref"],product_version=p.get("product_version"),runtime_binding_ref=p.get("runtime_binding_ref"),declared_capabilities_json=p.get("declared_capabilities",[]),declared_object_types_json=p.get("declared_object_types",[]),visibility=_vis(p),metadata_json=p.get("metadata",{})); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_case(db,p):
    _reject(p); _get(db,ResearchIntegrationCertificationSuiteRecord,p["suite_id"],"suite"); r=ResearchIntegrationCertificationCaseRecord(case_key=p["case_key"],suite_id=p["suite_id"],operation=p["operation"],object_type=p.get("object_type"),requirement=p["requirement"],required=bool(p.get("required",True)),expected_evidence_json=p.get("expected_evidence",[]),visibility=_vis(p),metadata_json=p.get("metadata",{})); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def create_run(db,p):
    _reject(p); _get(db,ResearchIntegrationCertificationSuiteRecord,p["suite_id"],"suite"); _get(db,ResearchIntegrationCertificationProductRecord,p["product_id"],"product"); r=ResearchIntegrationCertificationRunRecord(run_key=p["run_key"],suite_id=p["suite_id"],product_id=p["product_id"],executed_by=p["executed_by"],environment_ref=p.get("environment_ref"),started_at_text=p.get("started_at"),completed_at_text=p.get("completed_at"),status=p.get("status","recorded"),visibility=_vis(p),metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{})); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def record_case_result(db,p):
    _reject(p); _get(db,ResearchIntegrationCertificationRunRecord,p["run_id"],"run"); _get(db,ResearchIntegrationCertificationCaseRecord,p["case_id"],"case"); status=p["status"]; 
    if status not in RESULT_STATUSES: raise ValueError("unsupported result status")
    r=ResearchIntegrationCertificationCaseResultRecord(run_id=p["run_id"],case_id=p["case_id"],status=status,observed_behavior=p.get("observed_behavior"),evidence_refs_json=p.get("evidence_refs",[]),executed_by=p["executed_by"],visibility=_vis(p),metadata_json=p.get("metadata",{})); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def record_exchange_check(db,p):
    _reject(p); _get(db,ResearchIntegrationCertificationRunRecord,p["run_id"],"run"); r=ResearchIntegrationCertificationExchangeCheckRecord(run_id=p["run_id"],source_product_ref=p["source_product_ref"],target_product_ref=p["target_product_ref"],exchange_ref=p["exchange_ref"],object_refs_json=p.get("object_refs",[]),status=p["status"],evidence_refs_json=p.get("evidence_refs",[]),visibility=_vis(p)); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def record_trace_check(db,p):
    _reject(p); _get(db,ResearchIntegrationCertificationRunRecord,p["run_id"],"run"); r=ResearchIntegrationCertificationTraceCheckRecord(run_id=p["run_id"],object_ref=p["object_ref"],trace_type=p.get("trace_type","provenance"),expected_refs_json=p.get("expected_refs",[]),observed_refs_json=p.get("observed_refs",[]),status=p["status"],evidence_refs_json=p.get("evidence_refs",[]),visibility=_vis(p)); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def record_reproduction_check(db,p):
    _reject(p); _get(db,ResearchIntegrationCertificationRunRecord,p["run_id"],"run"); r=ResearchIntegrationCertificationReproductionCheckRecord(run_id=p["run_id"],project_ref=p["project_ref"],state_version_ref=p.get("state_version_ref"),reconstruction_plan_ref=p.get("reconstruction_plan_ref"),status=p["status"],evidence_refs_json=p.get("evidence_refs",[]),notes=p.get("notes"),visibility=_vis(p)); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_evidence(db,p):
    _reject(p); _get(db,ResearchIntegrationCertificationRunRecord,p["run_id"],"run"); r=ResearchIntegrationCertificationEvidenceRecord(evidence_key=p["evidence_key"],run_id=p["run_id"],evidence_type=p["evidence_type"],evidence_ref=p["evidence_ref"],content_hash=p.get("content_hash"),captured_by=p["captured_by"],visibility=_vis(p),metadata_json=p.get("metadata",{})); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_finding(db,p):
    _reject(p); _get(db,ResearchIntegrationCertificationRunRecord,p["run_id"],"run"); r=ResearchIntegrationCertificationFindingRecord(finding_key=p["finding_key"],run_id=p["run_id"],severity=p.get("severity","info"),category=p["category"],statement=p["statement"],evidence_refs_json=p.get("evidence_refs",[]),status=p.get("status","open"),visibility=_vis(p)); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def revise(db,p):
    _reject(p); sid=p["suite_id"]; _get(db,ResearchIntegrationCertificationSuiteRecord,sid,"suite"); rev=(db.scalar(select(func.max(ResearchIntegrationCertificationRevisionRecord.revision)).where(ResearchIntegrationCertificationRevisionRecord.suite_id==sid)) or 0)+1; r=ResearchIntegrationCertificationRevisionRecord(suite_id=sid,revision=rev,prior_state_json=p.get("prior_state",{}),revised_state_json=p.get("revised_state",{}),reason=p.get("reason"),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def snapshot(db,p):
    _reject(p); sid=p["suite_id"]; _get(db,ResearchIntegrationCertificationSuiteRecord,sid,"suite"); prev=db.scalar(select(ResearchIntegrationCertificationSnapshotRecord).where(ResearchIntegrationCertificationSnapshotRecord.suite_id==sid).order_by(ResearchIntegrationCertificationSnapshotRecord.revision.desc())); rev=(prev.revision if prev else 0)+1; state=suite_bundle(db,sid,False); h=_hash({"suite_id":sid,"revision":rev,"previous":prev.content_hash if prev else None,"state":state}); r=ResearchIntegrationCertificationSnapshotRecord(suite_id=sid,revision=rev,content_hash=h,previous_snapshot_hash=prev.content_hash if prev else None,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def run_report(db,run_id,public=False):
    run=_get(db,ResearchIntegrationCertificationRunRecord,run_id,"run")
    if public and run.visibility!="public": raise ValueError("run not public")
    results=_rows(db,ResearchIntegrationCertificationCaseResultRecord,public,ResearchIntegrationCertificationCaseResultRecord.run_id==run_id)
    case_ids=[x["id"] for x in _rows(db,ResearchIntegrationCertificationCaseRecord,False,ResearchIntegrationCertificationCaseRecord.suite_id==run.suite_id) if x["required"]]
    by_case={x["case_id"]:x["status"] for x in results}
    missing=[x for x in case_ids if x not in by_case]; failed=[x for x in case_ids if by_case.get(x)!="pass" and x in by_case]
    return {"release":"2.97.0","contract":CONTRACT,"run":_ser(run),"case_results":results,"exchange_checks":_rows(db,ResearchIntegrationCertificationExchangeCheckRecord,public,ResearchIntegrationCertificationExchangeCheckRecord.run_id==run_id),"trace_checks":_rows(db,ResearchIntegrationCertificationTraceCheckRecord,public,ResearchIntegrationCertificationTraceCheckRecord.run_id==run_id),"reproduction_checks":_rows(db,ResearchIntegrationCertificationReproductionCheckRecord,public,ResearchIntegrationCertificationReproductionCheckRecord.run_id==run_id),"evidence":_rows(db,ResearchIntegrationCertificationEvidenceRecord,public,ResearchIntegrationCertificationEvidenceRecord.run_id==run_id),"findings":_rows(db,ResearchIntegrationCertificationFindingRecord,public,ResearchIntegrationCertificationFindingRecord.run_id==run_id),"declared_conformance":not missing and not failed,"missing_required_case_ids":missing,"nonpassing_required_case_ids":failed,"conformance_is_runtime_contract_evidence_not_scientific_or_quality_certification":True}
def suite_bundle(db,suite_id,public=False):
    suite=_get(db,ResearchIntegrationCertificationSuiteRecord,suite_id,"suite")
    if public and suite.visibility!="public": raise ValueError("suite not public")
    return {"release":"2.97.0","contract":CONTRACT,"suite":_ser(suite),"products":_rows(db,ResearchIntegrationCertificationProductRecord,public,ResearchIntegrationCertificationProductRecord.suite_id==suite_id),"cases":_rows(db,ResearchIntegrationCertificationCaseRecord,public,ResearchIntegrationCertificationCaseRecord.suite_id==suite_id),"runs":_rows(db,ResearchIntegrationCertificationRunRecord,public,ResearchIntegrationCertificationRunRecord.suite_id==suite_id),"revisions":[] if public else _rows(db,ResearchIntegrationCertificationRevisionRecord,False,ResearchIntegrationCertificationRevisionRecord.suite_id==suite_id),"snapshots":[] if public else _rows(db,ResearchIntegrationCertificationSnapshotRecord,False,ResearchIntegrationCertificationSnapshotRecord.suite_id==suite_id),"certification_scope":"platform_runtime_contract_conformance_only"}
