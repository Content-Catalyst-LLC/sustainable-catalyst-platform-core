from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import (
    AnalyticalRuntimeProviderRecord, AnalyticalCapabilityRecord, AnalyticalExecutionRequestRecord,
    AnalyticalRuntimeEnvironmentRecord, AnalyticalExecutionResultRecord, AnalyticalArtifactRecord,
    StatisticalDiagnosticRecord, AnalyticalReproductionReferenceRecord,
)

RELEASE = "3.3.0"
CONTRACT = "sc.core.analytical-runtime-provider.v1"
FORBIDDEN = (
    "execute_analysis_by_core", "execute_r_by_core", "execute_python_by_core", "execute_julia_by_core",
    "select_provider_autonomously_by_core", "infer_statistical_significance_by_core",
    "certify_scientific_validity_by_core", "determine_truth_by_core",
)

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
    if p is None:
        p=db.scalar(select(AnalyticalRuntimeProviderRecord).where(AnalyticalRuntimeProviderRecord.provider_key==provider_ref))
    if p is None: raise ValueError("analytical provider not found")
    return p

def readiness(db:Session):
    providers=db.scalars(select(AnalyticalRuntimeProviderRecord)).all()
    caps=db.scalars(select(AnalyticalCapabilityRecord)).all()
    requests=db.scalars(select(AnalyticalExecutionRequestRecord)).all()
    results=db.scalars(select(AnalyticalExecutionResultRecord)).all()
    seeded=next((p for p in providers if p.provider_key=="catalystanalyticsr"),None)
    out={
        "release":RELEASE,"contract":CONTRACT,"migration_0103_applied":True,
        "counts":{"providers":len(providers),"capabilities":len(caps),"requests":len(requests),"results":len(results)},
        "runtime_neutral_provider_contract_by_core":True,"capability_registry_by_core":True,
        "execution_request_contract_by_core":True,"execution_result_binding_by_core":True,
        "runtime_environment_provenance_by_core":True,"diagnostic_reference_binding_by_core":True,
        "reproduction_reference_binding_by_core":True,"workspace_is_execution_host":True,
        "catalyst_analytics_r_registered":bool(seeded),
        "catalyst_analytics_r_version":seeded.provider_version if seeded else None,
    }
    out.update({k:False for k in FORBIDDEN}); return out

def list_providers(db:Session, public=False):
    q=select(AnalyticalRuntimeProviderRecord).order_by(AnalyticalRuntimeProviderRecord.provider_key.asc())
    if public: q=q.where(AnalyticalRuntimeProviderRecord.visibility=="public")
    return [_ser(x) for x in db.scalars(q).all()]

def provider_bundle(db:Session, provider_ref:str, public=False):
    p=_provider(db,provider_ref)
    if public and p.visibility!="public": raise ValueError("provider not public")
    q=select(AnalyticalCapabilityRecord).where(AnalyticalCapabilityRecord.provider_id==p.id).order_by(AnalyticalCapabilityRecord.capability_key.asc())
    if public: q=q.where(AnalyticalCapabilityRecord.visibility=="public")
    return {"release":RELEASE,"contract":CONTRACT,"provider":_ser(p),"capabilities":[_ser(x) for x in db.scalars(q).all()],"core_executes_provider":False,"execution_host":p.execution_host}

def register_provider(db:Session,p):
    _reject(p)
    r=AnalyticalRuntimeProviderRecord(provider_key=p["provider_key"],name=p["name"],provider_version=p["provider_version"],runtime=p["runtime"],execution_host=p["execution_host"],status=p.get("status","active"),contract_ref=p.get("contract_ref",CONTRACT),transport_mode=p.get("transport_mode","hosted"),invocation_mode=p.get("invocation_mode","workspace-managed"),visibility=p.get("visibility","internal"),metadata_json=p.get("metadata",{}))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def register_capability(db:Session,p):
    _reject(p); provider=_provider(db,p["provider_ref"])
    r=AnalyticalCapabilityRecord(provider_id=provider.id,capability_key=p["capability_key"],category=p.get("category","analysis"),method_refs_json=p.get("method_refs",[]),input_types_json=p.get("input_types",[]),output_types_json=p.get("output_types",[]),status=p.get("status","active"),visibility=p.get("visibility","internal"),metadata_json=p.get("metadata",{}))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def create_request(db:Session,p):
    _reject(p); provider=_provider(db,p["provider_ref"])
    if provider.status!="active": raise ValueError("analytical provider is not active")
    requested_runtime=p.get("runtime",provider.runtime); requested_host=p.get("execution_host",provider.execution_host)
    if requested_runtime!=provider.runtime: raise ValueError("request runtime does not match provider runtime")
    if requested_host!=provider.execution_host: raise ValueError("request execution_host does not match provider execution host")
    cap=p.get("analysis_type")
    exists=db.scalar(select(AnalyticalCapabilityRecord).where(AnalyticalCapabilityRecord.provider_id==provider.id,AnalyticalCapabilityRecord.capability_key==cap,AnalyticalCapabilityRecord.status=="active"))
    if exists is None: raise ValueError("provider does not declare requested analytical capability")
    r=AnalyticalExecutionRequestRecord(request_key=p["request_key"],provider_id=provider.id,session_ref=p.get("session_ref"),analysis_type=cap,method_ref=p.get("method_ref"),runtime=requested_runtime,execution_host=requested_host,input_refs_json=p.get("input_refs",[]),parameters_json=p.get("parameters",{}),reproducibility_json=p.get("reproducibility",{}),external_execution_ref=p.get("external_execution_ref"),status=p.get("status","declared"),visibility=p.get("visibility","internal"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def record_environment(db:Session,p):
    _reject(p); provider=_provider(db,p["provider_ref"])
    r=AnalyticalRuntimeEnvironmentRecord(environment_ref=p["environment_ref"],provider_id=provider.id,runtime=p.get("runtime",provider.runtime),runtime_version=p.get("runtime_version"),package_manifest_json=p.get("package_manifest",{}),container_ref=p.get("container_ref"),lockfile_ref=p.get("lockfile_ref"),content_hash=p.get("content_hash"),visibility=p.get("visibility","internal"),metadata_json=p.get("metadata",{}))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def _request(db:Session,request_ref:str):
    r=db.get(AnalyticalExecutionRequestRecord,request_ref)
    if r is None: r=db.scalar(select(AnalyticalExecutionRequestRecord).where(AnalyticalExecutionRequestRecord.request_key==request_ref))
    if r is None: raise ValueError("analytical execution request not found")
    return r

def record_result(db:Session,p):
    _reject(p); req=_request(db,p["request_ref"])
    r=AnalyticalExecutionResultRecord(request_id=req.id,result_ref=p["result_ref"],external_execution_ref=p.get("external_execution_ref",req.external_execution_ref),environment_ref=p.get("environment_ref"),status=p.get("status","recorded"),output_refs_json=p.get("output_refs",[]),estimate_refs_json=p.get("estimate_refs",[]),uncertainty_refs_json=p.get("uncertainty_refs",[]),diagnostic_refs_json=p.get("diagnostic_refs",[]),artifact_refs_json=p.get("artifact_refs",[]),visibility=p.get("visibility",req.visibility),provenance_json=p.get("provenance",{}))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def record_artifact(db:Session,p):
    _reject(p); req=_request(db,p["request_ref"]); r=AnalyticalArtifactRecord(request_id=req.id,artifact_ref=p["artifact_ref"],artifact_type=p["artifact_type"],media_type=p.get("media_type"),storage_ref=p.get("storage_ref"),content_hash=p.get("content_hash"),visibility=p.get("visibility",req.visibility),metadata_json=p.get("metadata",{})); db.add(r); db.commit(); db.refresh(r); return _ser(r)

def record_diagnostic(db:Session,p):
    _reject(p); req=_request(db,p["request_ref"]); r=StatisticalDiagnosticRecord(request_id=req.id,diagnostic_ref=p["diagnostic_ref"],diagnostic_type=p["diagnostic_type"],status=p.get("status","recorded"),metrics_json=p.get("metrics",{}),messages_json=p.get("messages",[]),visibility=p.get("visibility",req.visibility),metadata_json=p.get("metadata",{})); db.add(r); db.commit(); db.refresh(r); return _ser(r)

def record_reproduction(db:Session,p):
    _reject(p); req=_request(db,p["request_ref"]); r=AnalyticalReproductionReferenceRecord(request_id=req.id,reproduction_ref=p["reproduction_ref"],environment_ref=p.get("environment_ref"),code_ref=p.get("code_ref"),random_seed=str(p["random_seed"]) if p.get("random_seed") is not None else None,input_snapshot_refs_json=p.get("input_snapshot_refs",[]),status=p.get("status","declared"),visibility=p.get("visibility",req.visibility),metadata_json=p.get("metadata",{})); db.add(r); db.commit(); db.refresh(r); return _ser(r)

def request_bundle(db:Session,request_ref:str,public=False):
    req=_request(db,request_ref)
    if public and req.visibility!="public": raise ValueError("request not public")
    def rows(cls):
        q=select(cls).where(cls.request_id==req.id).order_by(cls.created_at.asc())
        if public: q=q.where(cls.visibility=="public")
        return [_ser(x) for x in db.scalars(q).all()]
    provider=db.get(AnalyticalRuntimeProviderRecord,req.provider_id)
    env=[]
    if provider:
        q=select(AnalyticalRuntimeEnvironmentRecord).where(AnalyticalRuntimeEnvironmentRecord.provider_id==provider.id).order_by(AnalyticalRuntimeEnvironmentRecord.created_at.asc())
        if public: q=q.where(AnalyticalRuntimeEnvironmentRecord.visibility=="public")
        env=[_ser(x) for x in db.scalars(q).all()]
    return {"release":RELEASE,"contract":CONTRACT,"request":_ser(req),"provider":_ser(provider) if provider else None,"results":rows(AnalyticalExecutionResultRecord),"artifacts":rows(AnalyticalArtifactRecord),"diagnostics":rows(StatisticalDiagnosticRecord),"reproduction_references":rows(AnalyticalReproductionReferenceRecord),"provider_environments":env,"execution_occurs_outside_core":True}
