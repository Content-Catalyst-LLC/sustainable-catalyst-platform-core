from __future__ import annotations
from datetime import datetime
import hashlib, json
from sqlalchemy import func, select
from sqlalchemy.inspection import inspect as sa_inspect
from ..models import (
    ResearchRuntimeContractRecord, ResearchRuntimeObjectTypeRecord, ResearchRuntimeOperationRecord,
    ResearchRuntimeCapabilityRecord, ResearchRuntimeProductBindingRecord, ResearchRuntimeExchangeEnvelopeRecord,
    ResearchRuntimeInvocationRecord, ResearchRuntimeResultBindingRecord, ResearchRuntimeCompatibilityAssertionRecord,
    ResearchRuntimeRevisionRecord, ResearchRuntimeSnapshotRecord,
)
CONTRACT="sc.research.unified-runtime-contract.v1"
VISIBILITIES={"private","internal","public"}
OPERATIONS={"create","read","update","link","version","snapshot","trace","handoff","package","validate_external","list"}
CAPABILITIES={
    "object:create","object:read","object:update","object:link","object:version","object:snapshot",
    "provenance:trace","context:handoff","package:export","validation:record","workflow:state","public:read"
}
FORBIDDEN={
    "execute_specialist_work_by_core","auto_route_requests_by_core","infer_object_schema_by_core",
    "mutate_specialist_state_by_core","authorize_product_by_contract_by_core","validate_scientific_result_by_core",
    "resolve_semantic_conflict_by_core","certify_reproducibility_by_core","invoke_external_runtime_by_core",
    "determine_truth_by_core"
}
CLASSES=[ResearchRuntimeContractRecord,ResearchRuntimeObjectTypeRecord,ResearchRuntimeOperationRecord,ResearchRuntimeCapabilityRecord,ResearchRuntimeProductBindingRecord,ResearchRuntimeExchangeEnvelopeRecord,ResearchRuntimeInvocationRecord,ResearchRuntimeResultBindingRecord,ResearchRuntimeCompatibilityAssertionRecord,ResearchRuntimeRevisionRecord,ResearchRuntimeSnapshotRecord]
COUNT_NAMES=["contracts","object_types","operations","capabilities","product_bindings","exchanges","invocations","results","compatibility_assertions","revisions","snapshots"]

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
    if bad: raise ValueError("Core standardizes declared research runtime interfaces; it does not execute specialist work, auto-route, infer schemas, mutate specialist state, authorize products, validate scientific results, resolve semantic conflicts, certify reproducibility, invoke external runtimes, or determine truth: "+", ".join(bad))
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
        "runtime_contract_registry_by_core":True,
        "runtime_object_type_registry_by_core":True,
        "runtime_operation_registry_by_core":True,
        "runtime_capability_registry_by_core":True,
        "product_binding_registry_by_core":True,
        "exchange_envelope_registry_by_core":True,
        "invocation_lineage_registry_by_core":True,
        "result_binding_registry_by_core":True,
        "compatibility_assertion_registry_by_core":True,
        "revision_history_by_core":True,
        "immutable_runtime_snapshots_by_core":True,
        "contract_semantics_declared_not_inferred":True,
        **{k:False for k in FORBIDDEN},
    }

def readiness(db):
    counts={n:db.scalar(select(func.count()).select_from(c)) or 0 for c,n in zip(CLASSES,COUNT_NAMES)}
    return {"release":"2.96.0","contract":CONTRACT,"operations":sorted(OPERATIONS),"capability_vocabulary":sorted(CAPABILITIES),"counts":counts,"migration_0100_applied":True,**boundaries()}

def create_contract(db,p):
    _reject(p)
    r=ResearchRuntimeContractRecord(contract_key=p["contract_key"],title=p["title"],contract_version=p.get("contract_version","1.0"),status=p.get("status","active"),schema_version=p.get("schema_version","1.0"),description=p.get("description"),required_capabilities_json=p.get("required_capabilities",[]),visibility=_vis(p),metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_object_type(db,p):
    _reject(p); _get(db,ResearchRuntimeContractRecord,p["contract_id"],"contract")
    r=ResearchRuntimeObjectTypeRecord(object_type_key=p["object_type_key"],contract_id=p["contract_id"],object_family=p["object_family"],schema_ref=p.get("schema_ref"),canonical_api_ref=p.get("canonical_api_ref"),versioning_mode=p.get("versioning_mode","explicit"),provenance_required=bool(p.get("provenance_required",True)),visibility=_vis(p),metadata_json=p.get("metadata",{}))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_operation(db,p):
    _reject(p); _get(db,ResearchRuntimeContractRecord,p["contract_id"],"contract")
    op=p["operation"]
    if op not in OPERATIONS: raise ValueError("unsupported runtime operation")
    r=ResearchRuntimeOperationRecord(operation_key=p["operation_key"],contract_id=p["contract_id"],operation=op,object_type_ref=p.get("object_type_ref"),method=p.get("method"),path_template=p.get("path_template"),input_schema_ref=p.get("input_schema_ref"),output_schema_ref=p.get("output_schema_ref"),idempotent=bool(p.get("idempotent",False)),provenance_required=bool(p.get("provenance_required",True)),visibility=_vis(p),metadata_json=p.get("metadata",{}))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_capability(db,p):
    _reject(p); _get(db,ResearchRuntimeContractRecord,p["contract_id"],"contract")
    cap=p["capability"]
    if cap not in CAPABILITIES and not cap.startswith("custom:"): raise ValueError("unsupported capability")
    r=ResearchRuntimeCapabilityRecord(capability_key=p["capability_key"],contract_id=p["contract_id"],capability=cap,level=p.get("level","supported"),description=p.get("description"),visibility=_vis(p),metadata_json=p.get("metadata",{}))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def bind_product(db,p):
    _reject(p); _get(db,ResearchRuntimeContractRecord,p["contract_id"],"contract")
    r=ResearchRuntimeProductBindingRecord(binding_key=p["binding_key"],contract_id=p["contract_id"],product_ref=p["product_ref"],product_version=p.get("product_version"),adapter_ref=p.get("adapter_ref"),supported_capabilities_json=p.get("supported_capabilities",[]),supported_object_types_json=p.get("supported_object_types",[]),status=p.get("status","declared"),visibility=_vis(p),metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def create_exchange(db,p):
    _reject(p); _get(db,ResearchRuntimeContractRecord,p["contract_id"],"contract")
    op=p["operation"]
    if op not in OPERATIONS: raise ValueError("unsupported runtime operation")
    canonical={"contract_id":p["contract_id"],"project_ref":p["project_ref"],"source_product_ref":p["source_product_ref"],"target_product_ref":p["target_product_ref"],"operation":op,"object_refs":p.get("object_refs",[]),"context_ref":p.get("context_ref"),"workflow_ref":p.get("workflow_ref"),"provenance_refs":p.get("provenance_refs",[])}
    r=ResearchRuntimeExchangeEnvelopeRecord(exchange_key=p["exchange_key"],contract_id=p["contract_id"],project_ref=p["project_ref"],source_product_ref=p["source_product_ref"],target_product_ref=p["target_product_ref"],operation=op,object_refs_json=p.get("object_refs",[]),context_ref=p.get("context_ref"),workflow_ref=p.get("workflow_ref"),provenance_refs_json=p.get("provenance_refs",[]),envelope_hash=_hash(canonical),status=p.get("status","declared"),visibility=_vis(p),metadata_json=p.get("metadata",{}))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def record_invocation(db,p):
    _reject(p); _get(db,ResearchRuntimeContractRecord,p["contract_id"],"contract")
    if p.get("exchange_id"): _get(db,ResearchRuntimeExchangeEnvelopeRecord,p["exchange_id"],"exchange")
    op=p["operation"]
    if op not in OPERATIONS: raise ValueError("unsupported runtime operation")
    r=ResearchRuntimeInvocationRecord(invocation_key=p["invocation_key"],contract_id=p["contract_id"],project_ref=p["project_ref"],exchange_id=p.get("exchange_id"),caller_ref=p["caller_ref"],operation=op,input_refs_json=p.get("input_refs",[]),runtime_ref=p.get("runtime_ref"),status=p.get("status","recorded"),visibility=_vis(p),provenance_json=p.get("provenance",{}))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def bind_result(db,p):
    _reject(p); _get(db,ResearchRuntimeInvocationRecord,p["invocation_id"],"invocation")
    r=ResearchRuntimeResultBindingRecord(result_key=p["result_key"],invocation_id=p["invocation_id"],project_ref=p["project_ref"],result_type=p["result_type"],object_ref=p["object_ref"],object_version_ref=p.get("object_version_ref"),content_hash=p.get("content_hash"),status=p.get("status","declared"),visibility=_vis(p),provenance_json=p.get("provenance",{}))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def record_compatibility(db,p):
    _reject(p); c=_get(db,ResearchRuntimeContractRecord,p["contract_id"],"contract"); b=_get(db,ResearchRuntimeProductBindingRecord,p["product_binding_id"],"product binding")
    if b.contract_id != c.id: raise ValueError("product binding belongs to another contract")
    r=ResearchRuntimeCompatibilityAssertionRecord(assertion_key=p["assertion_key"],contract_id=p["contract_id"],product_binding_id=p["product_binding_id"],asserted_by=p["asserted_by"],status=p.get("status","declared"),checks_json=p.get("checks",[]),evidence_refs_json=p.get("evidence_refs",[]),report_ref=p.get("report_ref"),visibility=_vis(p),provenance_json=p.get("provenance",{}))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def compatibility_report(db,contract_id,product_binding_id):
    c=_get(db,ResearchRuntimeContractRecord,contract_id,"contract"); b=_get(db,ResearchRuntimeProductBindingRecord,product_binding_id,"product binding")
    if b.contract_id != c.id: raise ValueError("product binding belongs to another contract")
    required=set(c.required_capabilities_json or []); supported=set(b.supported_capabilities_json or [])
    return {"contract_id":contract_id,"product_binding_id":product_binding_id,"required_capabilities":sorted(required),"declared_supported_capabilities":sorted(supported),"missing_declared_capabilities":sorted(required-supported),"declared_compatibility":required.issubset(supported),"compatibility_is_deterministic_from_declared_capabilities_not_certification":True}

def revise(db,p):
    _reject(p); _get(db,ResearchRuntimeContractRecord,p["contract_id"],"contract")
    rev=(db.scalar(select(func.max(ResearchRuntimeRevisionRecord.revision)).where(ResearchRuntimeRevisionRecord.contract_id==p["contract_id"])) or 0)+1
    r=ResearchRuntimeRevisionRecord(contract_id=p["contract_id"],revision=rev,prior_state_json=p.get("prior_state",{}),revised_state_json=p.get("revised_state",{}),reason=p.get("reason"),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)

def _contract_state(db,contract_id,public=False):
    c=_get(db,ResearchRuntimeContractRecord,contract_id,"contract")
    if public and c.visibility!="public": raise ValueError("contract not public")
    pred=lambda cls: cls.contract_id==contract_id
    return {"contract":_ser(c),"object_types":_rows(db,ResearchRuntimeObjectTypeRecord,public,pred(ResearchRuntimeObjectTypeRecord)),"operations":_rows(db,ResearchRuntimeOperationRecord,public,pred(ResearchRuntimeOperationRecord)),"capabilities":_rows(db,ResearchRuntimeCapabilityRecord,public,pred(ResearchRuntimeCapabilityRecord)),"product_bindings":_rows(db,ResearchRuntimeProductBindingRecord,public,pred(ResearchRuntimeProductBindingRecord)),"compatibility_assertions":_rows(db,ResearchRuntimeCompatibilityAssertionRecord,public,pred(ResearchRuntimeCompatibilityAssertionRecord))}

def snapshot(db,p):
    _reject(p); cid=p["contract_id"]; state=_contract_state(db,cid,False)
    rev=(db.scalar(select(func.max(ResearchRuntimeSnapshotRecord.revision)).where(ResearchRuntimeSnapshotRecord.contract_id==cid)) or 0)+1
    prev=db.scalar(select(ResearchRuntimeSnapshotRecord).where(ResearchRuntimeSnapshotRecord.contract_id==cid).order_by(ResearchRuntimeSnapshotRecord.revision.desc()).limit(1))
    h=_hash(state)
    r=ResearchRuntimeSnapshotRecord(contract_id=cid,revision=rev,content_hash=h,previous_snapshot_hash=prev.content_hash if prev else None,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)

def contract_bundle(db,contract_id,public=False):
    state=_contract_state(db,contract_id,public)
    state["revisions"]=[] if public else [_ser(x) for x in db.scalars(select(ResearchRuntimeRevisionRecord).where(ResearchRuntimeRevisionRecord.contract_id==contract_id).order_by(ResearchRuntimeRevisionRecord.revision)).all()]
    state["snapshots"]=[] if public else [_ser(x) for x in db.scalars(select(ResearchRuntimeSnapshotRecord).where(ResearchRuntimeSnapshotRecord.contract_id==contract_id).order_by(ResearchRuntimeSnapshotRecord.revision)).all()]
    return {"release":"2.96.0","contract_schema":CONTRACT,**state,"contract_semantics_declared_not_inferred":True}

def project_bundle(db,project_ref,public=False):
    exchanges=_rows(db,ResearchRuntimeExchangeEnvelopeRecord,public,ResearchRuntimeExchangeEnvelopeRecord.project_ref==project_ref)
    invocations=_rows(db,ResearchRuntimeInvocationRecord,public,ResearchRuntimeInvocationRecord.project_ref==project_ref)
    results=_rows(db,ResearchRuntimeResultBindingRecord,public,ResearchRuntimeResultBindingRecord.project_ref==project_ref)
    return {"release":"2.96.0","contract":CONTRACT,"project_ref":project_ref,"exchanges":exchanges,"invocations":invocations,"results":results,"lineage_is_declared_not_inferred":True}
