from __future__ import annotations
from collections import Counter
from datetime import datetime
import hashlib,json
from sqlalchemy import func,select
from sqlalchemy.inspection import inspect as sa_inspect
from ..models import (
 ResearchContextEnvelopeRecord,ResearchContextObjectBindingRecord,ResearchContextProvenanceBindingRecord,ResearchContextStateMarkerRecord,
 ResearchHandoffProtocolRecord,ResearchHandoffPackageRecord,ResearchHandoffAcknowledgementRecord,ResearchHandoffConflictRecord,
 ResearchHandoffRevisionRecord,ResearchHandoffSnapshotRecord,
)
CONTRACT="sc.research.cross-product-context-handoff.v1"
PRODUCTS={"core","library","research_librarian","workspace","research_lab","workbench","site_intelligence","decision_studio","catalyst_data","external"}
STATUSES={"draft","active","frozen","archived"}
VISIBILITIES={"private","internal","public"}
HANDOFF_STATUSES={"planned","prepared","offered","received","acknowledged","completed","rejected","cancelled"}
TRANSFER_MODES={"reference","manifest","snapshot","mixed"}
ACK_STATUSES={"received","accepted","rejected","needs_review"}
CONFLICT_STATUSES={"open","acknowledged","resolved_declared","dismissed_declared"}
OBJECT_TYPES={"project","workflow","workflow_stage","question","source","evidence","protocol","dataset","method","execution","output","finding","claim","inference","hypothesis","argument","conclusion","audit","review","replication","publication","synthesis","notebook","visualization","forensic_object","predictive_object","other"}
FORBIDDEN={"auto_route_handoff_by_core","execute_handoff_by_core","dispatch_external_jobs_by_core","choose_target_product_by_core","mutate_source_objects_by_core","infer_missing_context_by_core","resolve_context_conflicts_by_core","authorize_access_by_core","infer_research_validity_by_core","determine_truth_by_core"}
CLASSES=[ResearchContextEnvelopeRecord,ResearchContextObjectBindingRecord,ResearchContextProvenanceBindingRecord,ResearchContextStateMarkerRecord,ResearchHandoffProtocolRecord,ResearchHandoffPackageRecord,ResearchHandoffAcknowledgementRecord,ResearchHandoffConflictRecord,ResearchHandoffRevisionRecord,ResearchHandoffSnapshotRecord]
COUNT_NAMES=["contexts","object_bindings","provenance_bindings","state_markers","protocols","packages","acknowledgements","conflicts","revisions","snapshots"]
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
 if bad: raise ValueError("Core preserves declared cross-product research context and handoff provenance; it does not auto-route, execute or dispatch handoffs, choose targets, mutate source objects, infer missing context, resolve conflicts, authorize access, infer validity, or determine truth: "+", ".join(bad))
def _get(db,i):
 r=db.get(ResearchContextEnvelopeRecord,i)
 if not r: raise ValueError("research context not found")
 return r
def _rows(db,cls,i): return [_ser(x) for x in db.scalars(select(cls).where(cls.context_id==i).order_by(cls.created_at,cls.id)).all()]
def boundaries(): return {"context_envelope_registry_by_core":True,"object_binding_registry_by_core":True,"provenance_binding_registry_by_core":True,"state_marker_registry_by_core":True,"handoff_protocol_registry_by_core":True,"handoff_package_manifest_by_core":True,"declared_contract_completeness_by_core":True,"package_integrity_verification_by_core":True,"acknowledgement_registry_by_core":True,"conflict_registry_by_core":True,"revision_history_by_core":True,"context_lineage_by_core":True,"immutable_context_snapshots_by_core":True,**{k:False for k in FORBIDDEN}}
def readiness(db):
 counts={n:db.scalar(select(func.count()).select_from(c)) or 0 for c,n in zip(CLASSES,COUNT_NAMES)}
 return {"release":"2.91.0","contract":CONTRACT,"products":sorted(PRODUCTS),"transfer_modes":sorted(TRANSFER_MODES),"counts":counts,**boundaries()}
def create_context(db,p):
 _reject(p); st=p.get("status","draft"); vis=p.get("visibility","private"); src=p.get("source_product")
 if st not in STATUSES or vis not in VISIBILITIES or src not in PRODUCTS: raise ValueError("invalid context status, visibility, or source_product")
 r=ResearchContextEnvelopeRecord(context_key=p["context_key"],title=p["title"],status=st,visibility=vis,schema_version=p.get("schema_version","1.0"),source_product=src,project_ref=p.get("project_ref"),workflow_ref=p.get("workflow_ref"),workflow_stage_ref=p.get("workflow_stage_ref"),protocol_ref=p.get("protocol_ref"),research_state_json=p.get("research_state",{}),metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def _add(db,i,p,cls,key,extra):
 _reject(p); _get(db,i); kw={"context_id":i,key:p[key],"provenance_json":p.get("provenance",{}),"created_by":p.get("created_by","operator")}; kw.update(extra(p)); r=cls(**kw); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_object_binding(db,i,p):
 if p.get("product_key") not in PRODUCTS or p.get("object_type") not in OBJECT_TYPES or p.get("visibility","internal") not in VISIBILITIES: raise ValueError("unsupported object binding product/type/visibility")
 return _add(db,i,p,ResearchContextObjectBindingRecord,"binding_key",lambda p:{"product_key":p["product_key"],"object_type":p["object_type"],"object_ref":p["object_ref"],"role":p.get("role","context"),"version_ref":p.get("version_ref"),"visibility":p.get("visibility","internal"),"metadata_json":p.get("metadata",{})})
def add_provenance_binding(db,i,p):
 if not any(p.get(k) for k in ("activity_ref","agent_ref","source_ref")): raise ValueError("at least one provenance reference is required")
 return _add(db,i,p,ResearchContextProvenanceBindingRecord,"provenance_key",lambda p:{"relation":p["relation"],"activity_ref":p.get("activity_ref"),"agent_ref":p.get("agent_ref"),"source_ref":p.get("source_ref"),"details_json":p.get("details",{})})
def add_state_marker(db,i,p):
 if p.get("product_key") not in PRODUCTS or p.get("visibility","internal") not in VISIBILITIES: raise ValueError("unsupported state marker product/visibility")
 return _add(db,i,p,ResearchContextStateMarkerRecord,"state_key",lambda p:{"namespace":p["namespace"],"product_key":p["product_key"],"visibility":p.get("visibility","internal"),"value_json":p.get("value",{})})
def add_protocol(db,i,p):
 if p.get("from_product") not in PRODUCTS or p.get("to_product") not in PRODUCTS or p.get("status","planned") not in HANDOFF_STATUSES or p.get("transfer_mode","reference") not in TRANSFER_MODES: raise ValueError("unsupported handoff protocol")
 return _add(db,i,p,ResearchHandoffProtocolRecord,"handoff_key",lambda p:{"from_product":p["from_product"],"to_product":p["to_product"],"status":p.get("status","planned"),"transfer_mode":p.get("transfer_mode","reference"),"required_bindings_json":p.get("required_bindings",[]),"required_state_keys_json":p.get("required_state_keys",[]),"requested_capabilities_json":p.get("requested_capabilities",[]),"redaction_policy_json":p.get("redaction_policy",{}),"integrity_policy_json":p.get("integrity_policy",{})})
def _protocol(db,i,key):
 r=db.scalar(select(ResearchHandoffProtocolRecord).where(ResearchHandoffProtocolRecord.context_id==i,ResearchHandoffProtocolRecord.handoff_key==key))
 if not r: raise ValueError("handoff protocol not found")
 return r
def contract_diagnostics(db,i,handoff_key):
 _get(db,i); p=_protocol(db,i,handoff_key); bindings={x.binding_key for x in db.scalars(select(ResearchContextObjectBindingRecord).where(ResearchContextObjectBindingRecord.context_id==i)).all()}; states={x.state_key for x in db.scalars(select(ResearchContextStateMarkerRecord).where(ResearchContextStateMarkerRecord.context_id==i)).all()}; missing_bindings=sorted(set(p.required_bindings_json or [])-bindings); missing_states=sorted(set(p.required_state_keys_json or [])-states); return {"context_id":i,"handoff_key":handoff_key,"required_bindings":p.required_bindings_json or [],"required_state_keys":p.required_state_keys_json or [],"missing_bindings":missing_bindings,"missing_state_keys":missing_states,"declared_contract_complete":not missing_bindings and not missing_states,"diagnostic_is_structural_not_scientific_judgment":True,**boundaries()}
def _manifest_state(db,i,protocol):
 c=_ser(_get(db,i)); bindings=_rows(db,ResearchContextObjectBindingRecord,i); provenance=_rows(db,ResearchContextProvenanceBindingRecord,i); states=_rows(db,ResearchContextStateMarkerRecord,i)
 return {"context":{"id":c["id"],"context_key":c["context_key"],"schema_version":c["schema_version"],"project_ref":c.get("project_ref"),"workflow_ref":c.get("workflow_ref"),"workflow_stage_ref":c.get("workflow_stage_ref"),"protocol_ref":c.get("protocol_ref"),"research_state":c.get("research_state",{})},"handoff_protocol":{"id":protocol.id,"handoff_key":protocol.handoff_key,"from_product":protocol.from_product,"to_product":protocol.to_product,"transfer_mode":protocol.transfer_mode},"object_bindings":bindings,"provenance_bindings":provenance,"state_markers":states}
def create_package(db,i,p):
 _reject(p); protocol=_protocol(db,i,p["handoff_key"]); diag=contract_diagnostics(db,i,protocol.handoff_key)
 if p.get("require_complete",False) and not diag["declared_contract_complete"]: raise ValueError("declared handoff requirements are incomplete")
 state=_manifest_state(db,i,protocol); source_hash=_hash(state); manifest={"contract":CONTRACT,"generated_from_declared_context":True,"source_context_hash":source_hash,"state":state,"supplement":p.get("supplement",{})}; ch=_hash(manifest)
 r=ResearchHandoffPackageRecord(context_id=i,protocol_id=protocol.id,package_key=p["package_key"],status=p.get("status","prepared"),manifest_json=manifest,content_hash=ch,source_context_hash=source_hash,missing_requirements_json={"missing_bindings":diag["missing_bindings"],"missing_state_keys":diag["missing_state_keys"]},provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def _package(db,i,key):
 r=db.scalar(select(ResearchHandoffPackageRecord).where(ResearchHandoffPackageRecord.context_id==i,ResearchHandoffPackageRecord.package_key==key))
 if not r: raise ValueError("handoff package not found")
 return r
def acknowledge_package(db,i,package_key,p):
 _reject(p); pkg=_package(db,i,package_key); product=p.get("product_key")
 if product not in PRODUCTS or p.get("status","received") not in ACK_STATUSES: raise ValueError("unsupported acknowledgement")
 received=p.get("received_hash"); match=(received==pkg.content_hash) if received else None
 r=ResearchHandoffAcknowledgementRecord(context_id=i,package_id=pkg.id,ack_key=p["ack_key"],product_key=product,status=p.get("status","received"),received_hash=received,integrity_match=match,notes=p.get("notes"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_conflict(db,i,p):
 if p.get("status","open") not in CONFLICT_STATUSES: raise ValueError("unsupported conflict status")
 pkg=None
 if p.get("package_key"): pkg=_package(db,i,p["package_key"])
 return _add(db,i,p,ResearchHandoffConflictRecord,"conflict_key",lambda p:{"package_id":pkg.id if pkg else None,"conflict_type":p["conflict_type"],"status":p.get("status","open"),"source_ref":p.get("source_ref"),"target_ref":p.get("target_ref"),"details_json":p.get("details",{}),"declared_resolution_json":p.get("declared_resolution",{})})
def bundle(db,i,public=False):
 c=_get(db,i)
 if public and c.visibility!="public": raise ValueError("research context is not public")
 rows={"object_bindings":_rows(db,ResearchContextObjectBindingRecord,i),"provenance_bindings":_rows(db,ResearchContextProvenanceBindingRecord,i),"state_markers":_rows(db,ResearchContextStateMarkerRecord,i),"protocols":_rows(db,ResearchHandoffProtocolRecord,i),"packages":_rows(db,ResearchHandoffPackageRecord,i),"acknowledgements":_rows(db,ResearchHandoffAcknowledgementRecord,i),"conflicts":_rows(db,ResearchHandoffConflictRecord,i),"revisions":_rows(db,ResearchHandoffRevisionRecord,i),"snapshots":_rows(db,ResearchHandoffSnapshotRecord,i)}
 if public:
  rows["object_bindings"]=[x for x in rows["object_bindings"] if x.get("visibility")=="public"]
  rows["state_markers"]=[x for x in rows["state_markers"] if x.get("visibility")=="public"]
  rows["provenance_bindings"]=[]; rows["packages"]=[]; rows["acknowledgements"]=[]; rows["conflicts"]=[]
 return {"context":_ser(c),**rows,**boundaries()}
def descriptive_summary(db,i,public=False):
 b=bundle(db,i,public); return {"context":b["context"],"binding_products":dict(Counter(x["product_key"] for x in b["object_bindings"])),"object_types":dict(Counter(x["object_type"] for x in b["object_bindings"])),"handoff_statuses":dict(Counter(x["status"] for x in b["protocols"])),"package_count":len(b["packages"]),"open_conflicts":sum(1 for x in b["conflicts"] if x["status"]=="open"),"summary_is_descriptive_not_research_judgment":True,**boundaries()}
def lineage(db,i,public=False):
 b=bundle(db,i,public); c=b["context"]; node="context:"+i; edges=[]
 for f,t in (("project_ref","project"),("workflow_ref","workflow"),("workflow_stage_ref","workflow_stage"),("protocol_ref","protocol")):
  if c.get(f): edges.append({"from":t+":"+c[f],"to":node,"relation":"context_anchor"})
 edges += [{"from":x["product_key"]+":"+x["object_ref"],"to":node,"relation":x["role"],"binding_key":x["binding_key"]} for x in b["object_bindings"]]
 edges += [{"from":"product:"+x["from_product"],"to":"product:"+x["to_product"],"relation":"declared_handoff_protocol","handoff_key":x["handoff_key"]} for x in b["protocols"]]
 edges += [{"from":node,"to":"package:"+x["package_key"],"relation":"context_package","content_hash":x["content_hash"]} for x in b["packages"]]
 return {"context_id":i,"edges":edges,"edge_count":len(edges),"lineage_is_declared_not_inferred":True,**boundaries()}
def revise_context(db,i,p):
 _reject(p); c=_get(db,i); prior=_ser(c)
 for k in ("title","status","visibility","workflow_ref","workflow_stage_ref","protocol_ref"):
  if k in p: setattr(c,k,p[k])
 if "research_state" in p: c.research_state_json=p["research_state"]
 if c.status not in STATUSES or c.visibility not in VISIBILITIES: raise ValueError("invalid context status or visibility")
 prev=db.scalar(select(func.max(ResearchHandoffRevisionRecord.revision)).where(ResearchHandoffRevisionRecord.context_id==i)) or 0; db.commit(); db.refresh(c); revised=_ser(c); r=ResearchHandoffRevisionRecord(context_id=i,revision=prev+1,state_hash=_hash(revised),prior_state_json=prior,revised_state_json=revised,change_summary=p.get("change_summary"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def snapshot(db,i,p):
 _reject(p); state=bundle(db,i,False); state.pop("snapshots",None); prior=db.scalar(select(ResearchHandoffSnapshotRecord).where(ResearchHandoffSnapshotRecord.context_id==i).order_by(ResearchHandoffSnapshotRecord.revision.desc()).limit(1)); rev=(prior.revision if prior else 0)+1; r=ResearchHandoffSnapshotRecord(context_id=i,revision=rev,content_hash=_hash(state),previous_snapshot_hash=prior.content_hash if prior else None,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
