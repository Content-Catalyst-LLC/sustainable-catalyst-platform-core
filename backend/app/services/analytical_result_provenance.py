from __future__ import annotations
from datetime import datetime, timezone
import hashlib, json, uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import (
    AnalyticalRuntimeProviderRecord, AnalyticalCapabilityRecord, AnalyticalExecutionRequestRecord,
    AnalyticalRuntimeEnvironmentRecord, AnalyticalExecutionResultRecord, AnalyticalArtifactRecord,
    StatisticalDiagnosticRecord, AnalyticalReproductionReferenceRecord,
    AnalyticalResultObjectRecord, AnalyticalEstimateRecord, AnalyticalUncertaintyObjectRecord,
    AnalyticalLineageBindingRecord, AnalyticalResultIngestionReceiptRecord, AnalyticalResultSnapshotRecord,
)

RELEASE = "3.3.0"
PROVIDER_CONTRACT = "sc.core.analytical-runtime-provider.v1"
RESULT_CONTRACT = "sc.core.analytical-result-provenance.v1"
CATALYST_R_RESULT_TYPE = "catalyst_analytics_r_core_result"
FORBIDDEN = (
    "execute_analysis_by_core", "execute_r_by_core", "execute_python_by_core", "execute_julia_by_core",
    "select_provider_autonomously_by_core", "infer_statistical_significance_by_core",
    "certify_scientific_validity_by_core", "determine_truth_by_core", "rank_results_by_core",
)
LINEAGE_TYPES = {"request_input","result_output","provider","environment","workspace_receipt","estimate","uncertainty","diagnostic","artifact","reproduction","external_execution","derived_from"}


def _now(): return datetime.now(timezone.utc)
def _canon(value): return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str)
def _hash(value): return hashlib.sha256(_canon(value).encode()).hexdigest()
def _ser(x):
    d={c.name:getattr(x,c.name) for c in x.__table__.columns}
    for k,v in list(d.items()):
        if hasattr(v,"isoformat"): d[k]=v.isoformat()
    for k in list(d):
        if k.endswith("_json"): d[k[:-5]]=d.pop(k)
    return d

def _reject(p):
    for key in FORBIDDEN:
        if p.get(key) is True: raise ValueError(f"Core boundary forbids {key}")

def _provider(db:Session, provider_ref:str):
    p=db.get(AnalyticalRuntimeProviderRecord,provider_ref)
    if p is None: p=db.scalar(select(AnalyticalRuntimeProviderRecord).where(AnalyticalRuntimeProviderRecord.provider_key==provider_ref))
    if p is None: raise ValueError("analytical provider not found")
    return p

def _request(db:Session,request_ref:str):
    r=db.get(AnalyticalExecutionRequestRecord,request_ref)
    if r is None: r=db.scalar(select(AnalyticalExecutionRequestRecord).where(AnalyticalExecutionRequestRecord.request_key==request_ref))
    if r is None: raise ValueError("analytical execution request not found")
    return r

def _result(db:Session,result_ref:str):
    r=db.get(AnalyticalResultObjectRecord,result_ref)
    if r is None: r=db.scalar(select(AnalyticalResultObjectRecord).where(AnalyticalResultObjectRecord.result_ref==result_ref))
    if r is None: raise ValueError("analytical result object not found")
    return r

def _strings(p,key):
    value=p.get(key,[])
    if not isinstance(value,list) or any(not isinstance(x,str) or not x for x in value): raise ValueError(f"{key} must be an array of string references")
    return value

def _completed_at(value):
    if not value: return None
    if isinstance(value,datetime): return value
    try: return datetime.fromisoformat(str(value).replace("Z","+00:00"))
    except ValueError as e: raise ValueError("completed_at must be ISO-8601") from e

def readiness(db:Session):
    provider=db.scalar(select(AnalyticalRuntimeProviderRecord).where(AnalyticalRuntimeProviderRecord.provider_key=="catalystanalyticsr"))
    def count(cls): return len(db.scalars(select(cls.id)).all())
    out={
        "release":RELEASE,"contract":RESULT_CONTRACT,"provider_contract":PROVIDER_CONTRACT,"migration_0104_applied":True,
        "catalyst_analytics_r_registered":provider is not None,"catalyst_analytics_r_version":provider.provider_version if provider else None,
        "workspace_adapter_release":"3.9.1","workspace_is_execution_host":True,
        "counts":{"results":count(AnalyticalResultObjectRecord),"estimates":count(AnalyticalEstimateRecord),"uncertainty_objects":count(AnalyticalUncertaintyObjectRecord),"lineage_bindings":count(AnalyticalLineageBindingRecord),"ingestion_receipts":count(AnalyticalResultIngestionReceiptRecord),"snapshots":count(AnalyticalResultSnapshotRecord)},
        "first_class_result_objects":True,"estimate_objects":True,"uncertainty_objects":True,"lineage_bindings":True,"immutable_result_snapshots":True,"idempotent_workspace_ingestion":True,
        "core_records_results_but_does_not_execute":True,"human_review_required":True,"scientific_validity_not_certified_by_core":True,
    }
    out.update({k:False for k in FORBIDDEN}); return out

def _ensure_lineage(db,result,binding_type,source_ref,target_ref,visibility,content_hash=None,provenance=None):
    if binding_type not in LINEAGE_TYPES: raise ValueError("unsupported analytical lineage binding type")
    existing=db.scalar(select(AnalyticalLineageBindingRecord).where(AnalyticalLineageBindingRecord.result_id==result.id,AnalyticalLineageBindingRecord.binding_type==binding_type,AnalyticalLineageBindingRecord.source_ref==source_ref,AnalyticalLineageBindingRecord.target_ref==target_ref))
    if existing: return existing
    r=AnalyticalLineageBindingRecord(result_id=result.id,binding_type=binding_type,source_ref=source_ref,target_ref=target_ref,content_hash=content_hash,provenance_json=provenance or {},visibility=visibility)
    db.add(r); db.flush(); return r

def _snapshot_state(db,result):
    estimates=[_ser(x) for x in db.scalars(select(AnalyticalEstimateRecord).where(AnalyticalEstimateRecord.result_id==result.id).order_by(AnalyticalEstimateRecord.estimate_ref)).all()]
    uncertainty=[_ser(x) for x in db.scalars(select(AnalyticalUncertaintyObjectRecord).where(AnalyticalUncertaintyObjectRecord.result_id==result.id).order_by(AnalyticalUncertaintyObjectRecord.uncertainty_ref)).all()]
    lineage=[_ser(x) for x in db.scalars(select(AnalyticalLineageBindingRecord).where(AnalyticalLineageBindingRecord.result_id==result.id).order_by(AnalyticalLineageBindingRecord.binding_type,AnalyticalLineageBindingRecord.source_ref)).all()]
    return {"result":_ser(result),"estimates":estimates,"uncertainty_objects":uncertainty,"lineage":lineage}

def create_snapshot(db:Session,result_ref:str,p=None):
    p=p or {}; _reject(p); result=_result(db,result_ref); state=_snapshot_state(db,result); h=_hash(state)
    existing=db.scalar(select(AnalyticalResultSnapshotRecord).where(AnalyticalResultSnapshotRecord.result_id==result.id,AnalyticalResultSnapshotRecord.snapshot_hash==h))
    if existing: return {**_ser(existing),"idempotent_replay":True}
    prev=db.scalar(select(AnalyticalResultSnapshotRecord).where(AnalyticalResultSnapshotRecord.result_id==result.id).order_by(AnalyticalResultSnapshotRecord.created_at.desc()))
    r=AnalyticalResultSnapshotRecord(snapshot_ref=p.get("snapshot_ref") or f"snapshot:{result.result_ref}:{h[:16]}",result_id=result.id,snapshot_hash=h,previous_snapshot_hash=prev.snapshot_hash if prev else None,state_json=state,provenance_json=p.get("provenance",{}),visibility=p.get("visibility",result.visibility),created_by=p.get("created_by","operator"))
    db.add(r); db.flush(); return {**_ser(r),"idempotent_replay":False}

def ingest_result(db:Session,p):
    _reject(p)
    required=("schema_version","result_type","core_contract","request_ref","result_ref","provider_ref","provider_version","runtime","execution_host","analysis_type","status","output_refs","estimate_refs","uncertainty_refs","diagnostic_refs","artifact_refs","provenance","boundary")
    missing=[k for k in required if k not in p]
    if missing: raise ValueError("analytical result missing fields: "+", ".join(missing))
    if p["schema_version"]!="1.0.0": raise ValueError("unsupported analytical result schema_version")
    if p["core_contract"]!=PROVIDER_CONTRACT: raise ValueError("analytical result Core provider contract mismatch")
    if p["status"] not in {"recorded","completed","failed"}: raise ValueError("unsupported analytical result status")
    if not isinstance(p.get("provenance"),dict): raise ValueError("provenance must be an object")
    boundary=p.get("boundary") or {}
    if not (boundary.get("core_records_result_but_does_not_execute") is True and boundary.get("workspace_execution_required") is True and boundary.get("human_review_required") is True): raise ValueError("analytical result boundary is invalid")
    req=_request(db,p["request_ref"]); provider=_provider(db,p["provider_ref"])
    if req.provider_id!=provider.id: raise ValueError("result provider does not match request provider")
    if req.analysis_type!=p["analysis_type"]: raise ValueError("result analysis_type does not match request")
    if req.runtime!=p["runtime"] or req.execution_host!=p["execution_host"]: raise ValueError("result runtime/execution host does not match request")
    if p["provider_version"]!=provider.provider_version: raise ValueError("result provider_version does not match registered provider")
    if provider.provider_key=="catalystanalyticsr" and p["result_type"]!=CATALYST_R_RESULT_TYPE: raise ValueError("Catalyst Analytics R result_type mismatch")
    refs={k:_strings(p,k) for k in ("output_refs","estimate_refs","uncertainty_refs","diagnostic_refs","artifact_refs")}
    warnings=_strings(p,"warnings") if "warnings" in p else []; errors=_strings(p,"errors") if "errors" in p else []
    payload_hash=_hash(p); provenance_hash=_hash(p["provenance"])
    existing=db.scalar(select(AnalyticalResultObjectRecord).where(AnalyticalResultObjectRecord.result_ref==p["result_ref"]))
    if existing:
        if existing.result_fingerprint!=payload_hash: raise ValueError("result_ref already exists with a different payload fingerprint")
        return {"release":RELEASE,"contract":RESULT_CONTRACT,"result":_ser(existing),"idempotent_replay":True,"result_fingerprint":payload_hash}
    visibility=p.get("visibility",req.visibility)
    result=AnalyticalResultObjectRecord(result_ref=p["result_ref"],request_id=req.id,provider_id=provider.id,provider_version=p["provider_version"],core_contract=p["core_contract"],analysis_type=p["analysis_type"],method_ref=p.get("method_ref") or req.method_ref,external_execution_ref=p.get("external_execution_ref") or req.external_execution_ref,workspace_receipt_ref=p.get("workspace_receipt_ref"),environment_ref=p.get("environment_ref"),status=p["status"],output_refs_json=refs["output_refs"],estimate_refs_json=refs["estimate_refs"],uncertainty_refs_json=refs["uncertainty_refs"],diagnostic_refs_json=refs["diagnostic_refs"],artifact_refs_json=refs["artifact_refs"],warnings_json=warnings,errors_json=errors,native_summary_json=p.get("native_result",{}) if isinstance(p.get("native_result",{}),dict) else {"value":p.get("native_result")},provenance_json=p["provenance"],provenance_hash=provenance_hash,result_fingerprint=payload_hash,visibility=visibility,completed_at=_completed_at(p.get("completed_at")))
    db.add(result); db.flush()
    # Backward-compatible v3.1 execution-result record.
    if db.scalar(select(AnalyticalExecutionResultRecord).where(AnalyticalExecutionResultRecord.result_ref==p["result_ref"])) is None:
        db.add(AnalyticalExecutionResultRecord(request_id=req.id,result_ref=p["result_ref"],external_execution_ref=result.external_execution_ref,environment_ref=result.environment_ref,status=result.status,output_refs_json=refs["output_refs"],estimate_refs_json=refs["estimate_refs"],uncertainty_refs_json=refs["uncertainty_refs"],diagnostic_refs_json=refs["diagnostic_refs"],artifact_refs_json=refs["artifact_refs"],visibility=visibility,provenance_json=p["provenance"]))
    # Automatic declared lineage.
    for ref in req.input_refs_json or []: _ensure_lineage(db,result,"request_input",ref,result.result_ref,visibility)
    _ensure_lineage(db,result,"provider",provider.provider_key,result.result_ref,visibility)
    if result.environment_ref: _ensure_lineage(db,result,"environment",result.environment_ref,result.result_ref,visibility)
    if result.workspace_receipt_ref: _ensure_lineage(db,result,"workspace_receipt",result.workspace_receipt_ref,result.result_ref,visibility)
    if result.external_execution_ref: _ensure_lineage(db,result,"external_execution",result.external_execution_ref,result.result_ref,visibility)
    for kind,key in (("result_output","output_refs"),("estimate","estimate_refs"),("uncertainty","uncertainty_refs"),("diagnostic","diagnostic_refs"),("artifact","artifact_refs")):
        for ref in refs[key]: _ensure_lineage(db,result,kind,result.result_ref,ref,visibility)
    repros=db.scalars(select(AnalyticalReproductionReferenceRecord).where(AnalyticalReproductionReferenceRecord.request_id==req.id)).all()
    for r in repros: _ensure_lineage(db,result,"reproduction",r.reproduction_ref,result.result_ref,visibility)
    receipt_key=p.get("ingestion_receipt_key") or f"ingest:{result.result_ref}:{payload_hash[:16]}"
    receipt=AnalyticalResultIngestionReceiptRecord(receipt_key=receipt_key,result_id=result.id,workspace_receipt_ref=result.workspace_receipt_ref,external_execution_ref=result.external_execution_ref,payload_hash=payload_hash,outcome="recorded",visibility=visibility,metadata_json={"result_type":p["result_type"],"provider_ref":provider.provider_key})
    db.add(receipt); db.flush()
    snap=create_snapshot(db,result.result_ref,{"visibility":visibility,"created_by":p.get("created_by","workspace-ingest"),"provenance":{"source":"analytical-result-ingest","payload_hash":payload_hash}})
    db.commit(); db.refresh(result)
    return {"release":RELEASE,"contract":RESULT_CONTRACT,"result":_ser(result),"ingestion_receipt":_ser(receipt),"snapshot":snap,"idempotent_replay":False,"result_fingerprint":payload_hash}

def record_estimate(db:Session,result_ref:str,p):
    _reject(p); result=_result(db,result_ref); ref=p["estimate_ref"]
    if ref not in (result.estimate_refs_json or []): raise ValueError("estimate_ref was not declared by analytical result")
    existing=db.scalar(select(AnalyticalEstimateRecord).where(AnalyticalEstimateRecord.estimate_ref==ref))
    if existing: return _ser(existing)
    value=p.get("value",{}); value=value if isinstance(value,dict) else {"value":value}
    r=AnalyticalEstimateRecord(result_id=result.id,estimate_ref=ref,estimate_type=p["estimate_type"],name=p.get("name"),value_json=value,unit=p.get("unit"),uncertainty_ref=p.get("uncertainty_ref"),status=p.get("status","recorded"),visibility=p.get("visibility",result.visibility),metadata_json=p.get("metadata",{})); db.add(r); _ensure_lineage(db,result,"estimate",result.result_ref,ref,r.visibility); db.commit(); db.refresh(r); return _ser(r)

def record_uncertainty(db:Session,result_ref:str,p):
    _reject(p); result=_result(db,result_ref); ref=p["uncertainty_ref"]
    if ref not in (result.uncertainty_refs_json or []): raise ValueError("uncertainty_ref was not declared by analytical result")
    existing=db.scalar(select(AnalyticalUncertaintyObjectRecord).where(AnalyticalUncertaintyObjectRecord.uncertainty_ref==ref))
    if existing: return _ser(existing)
    level=p.get("level")
    if level is not None and not (0 < float(level) <= 1): raise ValueError("uncertainty level must be in (0,1]")
    r=AnalyticalUncertaintyObjectRecord(result_id=result.id,uncertainty_ref=ref,uncertainty_type=p["uncertainty_type"],distribution_ref=p.get("distribution_ref"),level=float(level) if level is not None else None,summary_json=p.get("summary",{}),parameters_json=p.get("parameters",{}),status=p.get("status","recorded"),visibility=p.get("visibility",result.visibility),metadata_json=p.get("metadata",{})); db.add(r); _ensure_lineage(db,result,"uncertainty",result.result_ref,ref,r.visibility); db.commit(); db.refresh(r); return _ser(r)

def record_lineage(db:Session,result_ref:str,p):
    _reject(p); result=_result(db,result_ref); b=_ensure_lineage(db,result,p["binding_type"],p["source_ref"],p["target_ref"],p.get("visibility",result.visibility),p.get("content_hash"),p.get("provenance",{})); db.commit(); db.refresh(b); return _ser(b)

def result_bundle(db:Session,result_ref:str,public=False):
    result=_result(db,result_ref)
    if public and result.visibility!="public": raise ValueError("result not public")
    req=db.get(AnalyticalExecutionRequestRecord,result.request_id); provider=db.get(AnalyticalRuntimeProviderRecord,result.provider_id)
    def rows(cls,order):
        q=select(cls).where(cls.result_id==result.id).order_by(order)
        if public and hasattr(cls,"visibility"): q=q.where(cls.visibility=="public")
        return [_ser(x) for x in db.scalars(q).all()]
    env=None
    if result.environment_ref:
        q=select(AnalyticalRuntimeEnvironmentRecord).where(AnalyticalRuntimeEnvironmentRecord.environment_ref==result.environment_ref)
        if public: q=q.where(AnalyticalRuntimeEnvironmentRecord.visibility=="public")
        e=db.scalar(q); env=_ser(e) if e else None
    req_id=req.id if req else None
    def request_rows(cls):
        if not req_id: return []
        q=select(cls).where(cls.request_id==req_id).order_by(cls.created_at.asc())
        if public: q=q.where(cls.visibility=="public")
        return [_ser(x) for x in db.scalars(q).all()]
    return {"release":RELEASE,"contract":RESULT_CONTRACT,"result":_ser(result),"request":_ser(req) if req else None,"provider":_ser(provider) if provider else None,"environment":env,"estimates":rows(AnalyticalEstimateRecord,AnalyticalEstimateRecord.created_at.asc()),"uncertainty_objects":rows(AnalyticalUncertaintyObjectRecord,AnalyticalUncertaintyObjectRecord.created_at.asc()),"lineage":rows(AnalyticalLineageBindingRecord,AnalyticalLineageBindingRecord.created_at.asc()),"ingestion_receipts":rows(AnalyticalResultIngestionReceiptRecord,AnalyticalResultIngestionReceiptRecord.created_at.asc()),"snapshots":rows(AnalyticalResultSnapshotRecord,AnalyticalResultSnapshotRecord.created_at.asc()),"artifacts":request_rows(AnalyticalArtifactRecord),"diagnostics":request_rows(StatisticalDiagnosticRecord),"reproduction_references":request_rows(AnalyticalReproductionReferenceRecord),"core_executes_analysis":False,"human_review_required":True}

def result_lineage(db:Session,result_ref:str,public=False):
    b=result_bundle(db,result_ref,public)
    return {"release":RELEASE,"contract":RESULT_CONTRACT,"result_ref":b["result"]["result_ref"],"request_ref":b["request"]["request_key"] if b["request"] else None,"provider_ref":b["provider"]["provider_key"] if b["provider"] else None,"environment_ref":b["result"].get("environment_ref"),"external_execution_ref":b["result"].get("external_execution_ref"),"workspace_receipt_ref":b["result"].get("workspace_receipt_ref"),"bindings":b["lineage"],"result_fingerprint":b["result"]["result_fingerprint"],"provenance_hash":b["result"]["provenance_hash"],"snapshots":[{"snapshot_ref":x["snapshot_ref"],"snapshot_hash":x["snapshot_hash"],"previous_snapshot_hash":x["previous_snapshot_hash"]} for x in b["snapshots"]]}
