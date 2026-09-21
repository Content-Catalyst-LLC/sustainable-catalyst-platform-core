from __future__ import annotations
from collections import Counter
from datetime import datetime,timezone
import hashlib,json
from sqlalchemy import func,select
from sqlalchemy.inspection import inspect as sa_inspect
from ..models import (
 ResearchProjectStateRecord,ResearchProjectStateVersionRecord,ResearchProjectStateBindingRecord,ResearchProjectStateDependencyRecord,
 ResearchProjectStateEnvironmentRecord,ResearchProjectStateCheckpointRecord,ResearchProjectReconstructionPlanRecord,
 ResearchProjectReconstructionVerificationRecord,ResearchProjectStateRevisionRecord,ResearchProjectStateSnapshotRecord,
)
CONTRACT="sc.research.project-state-versioning-reproducibility.v1"
PRODUCTS={"core","library","research_librarian","workspace","research_lab","workbench","site_intelligence","decision_studio","catalyst_data","external"}
STATUSES={"draft","active","archived"}; VERSION_STATUSES={"draft","frozen","superseded"}; VISIBILITIES={"private","internal","public"}
OBJECT_TYPES={"project","question","source","evidence","protocol","dataset","method","execution","parameter","assumption","output","finding","claim","inference","hypothesis","argument","conclusion","audit","review","replication","publication","synthesis","notebook","visualization","workflow","handoff","forensic_object","predictive_object","other"}
ENVIRONMENT_TYPES={"software","python","r","julia","ml","container","notebook","workbench","database","operating_system","external_service","other"}
CHECKPOINT_TYPES={"milestone","analysis","review","replication","publication","handoff","archive","other"}
VERIFICATION_STATUSES={"unverified","passed","failed","partial","needs_review"}
FORBIDDEN={"restore_project_state_by_core","replay_executions_by_core","fetch_external_objects_by_core","mutate_historical_state_by_core","infer_missing_versions_by_core","infer_reproducibility_by_core","certify_reproducibility_by_core","validate_scientific_results_by_core","choose_canonical_state_by_core","determine_truth_by_core"}
CLASSES=[ResearchProjectStateRecord,ResearchProjectStateVersionRecord,ResearchProjectStateBindingRecord,ResearchProjectStateDependencyRecord,ResearchProjectStateEnvironmentRecord,ResearchProjectStateCheckpointRecord,ResearchProjectReconstructionPlanRecord,ResearchProjectReconstructionVerificationRecord,ResearchProjectStateRevisionRecord,ResearchProjectStateSnapshotRecord]
COUNT_NAMES=["states","versions","bindings","dependencies","environments","checkpoints","reconstruction_plans","verifications","revisions","snapshots"]
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
 if bad: raise ValueError("Core preserves declared historical research state and reconstruction evidence; it does not restore projects, replay executions, fetch external objects, mutate history, infer missing versions or reproducibility, certify reproducibility, validate scientific results, choose canonical state, or determine truth: "+", ".join(bad))
def boundaries(): return {"project_state_registry_by_core":True,"immutable_version_registry_by_core":True,"versioned_object_binding_registry_by_core":True,"dependency_graph_registry_by_core":True,"environment_binding_registry_by_core":True,"named_checkpoint_registry_by_core":True,"reconstruction_plan_registry_by_core":True,"external_verification_evidence_registry_by_core":True,"historical_state_reconstruction_manifest_by_core":True,"integrity_hash_chaining_by_core":True,"revision_history_by_core":True,"immutable_project_snapshots_by_core":True,**{k:False for k in FORBIDDEN}}
def readiness(db):
 counts={n:db.scalar(select(func.count()).select_from(c)) or 0 for c,n in zip(CLASSES,COUNT_NAMES)}
 return {"release":"2.92.0","contract":CONTRACT,"products":sorted(PRODUCTS),"object_types":sorted(OBJECT_TYPES),"environment_types":sorted(ENVIRONMENT_TYPES),"counts":counts,**boundaries()}
def _state(db,i):
 r=db.get(ResearchProjectStateRecord,i)
 if not r: raise ValueError("research project state not found")
 return r
def _version(db,i,version):
 r=db.scalar(select(ResearchProjectStateVersionRecord).where(ResearchProjectStateVersionRecord.state_id==i,ResearchProjectStateVersionRecord.version==int(version)))
 if not r: raise ValueError("research project state version not found")
 return r
def _draft(v):
 if v.status!="draft" or v.content_hash: raise ValueError("frozen historical versions are immutable")
def _rows(db,cls,field,value): return [_ser(x) for x in db.scalars(select(cls).where(getattr(cls,field)==value).order_by(cls.created_at,cls.id)).all()]
def create_state(db,p):
 _reject(p); st=p.get("status","active"); vis=p.get("visibility","private")
 if st not in STATUSES or vis not in VISIBILITIES: raise ValueError("invalid project state status or visibility")
 r=ResearchProjectStateRecord(state_key=p["state_key"],project_ref=p["project_ref"],title=p["title"],status=st,visibility=vis,metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def create_version(db,i,p):
 _reject(p); _state(db,i); n=p.get("version") or ((db.scalar(select(func.max(ResearchProjectStateVersionRecord.version)).where(ResearchProjectStateVersionRecord.state_id==i)) or 0)+1); status=p.get("status","draft")
 if status!="draft": raise ValueError("new project state versions must begin as draft")
 r=ResearchProjectStateVersionRecord(state_id=i,version=int(n),label=p.get("label"),status="draft",summary=p.get("summary"),metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_binding(db,i,version,p):
 _reject(p); v=_version(db,i,version); _draft(v)
 if p.get("product_key") not in PRODUCTS or p.get("object_type") not in OBJECT_TYPES or p.get("visibility","internal") not in VISIBILITIES: raise ValueError("unsupported product/object_type/visibility")
 r=ResearchProjectStateBindingRecord(version_id=v.id,binding_key=p["binding_key"],product_key=p["product_key"],object_type=p["object_type"],object_ref=p["object_ref"],object_version_ref=p.get("object_version_ref"),content_hash=p.get("content_hash"),role=p.get("role","project_state"),visibility=p.get("visibility","internal"),metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_dependency(db,i,version,p):
 _reject(p); v=_version(db,i,version); _draft(v); keys={x.binding_key for x in db.scalars(select(ResearchProjectStateBindingRecord).where(ResearchProjectStateBindingRecord.version_id==v.id)).all()}
 if p["from_binding_key"] not in keys or p["to_binding_key"] not in keys: raise ValueError("dependency endpoints must reference bindings in this version")
 r=ResearchProjectStateDependencyRecord(version_id=v.id,dependency_key=p["dependency_key"],from_binding_key=p["from_binding_key"],to_binding_key=p["to_binding_key"],relation=p["relation"],details_json=p.get("details",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_environment(db,i,version,p):
 _reject(p); v=_version(db,i,version); _draft(v)
 if p.get("environment_type") not in ENVIRONMENT_TYPES or p.get("visibility","internal") not in VISIBILITIES: raise ValueError("unsupported environment type/visibility")
 r=ResearchProjectStateEnvironmentRecord(version_id=v.id,environment_key=p["environment_key"],environment_type=p["environment_type"],environment_ref=p["environment_ref"],version_ref=p.get("version_ref"),content_hash=p.get("content_hash"),visibility=p.get("visibility","internal"),details_json=p.get("details",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def _version_manifest(db,v,public=False):
 bindings=_rows(db,ResearchProjectStateBindingRecord,"version_id",v.id); envs=_rows(db,ResearchProjectStateEnvironmentRecord,"version_id",v.id); deps=_rows(db,ResearchProjectStateDependencyRecord,"version_id",v.id)
 if public:
  bindings=[x for x in bindings if x["visibility"]=="public"]; envs=[x for x in envs if x["visibility"]=="public"]; keep={x["binding_key"] for x in bindings}; deps=[x for x in deps if x["from_binding_key"] in keep and x["to_binding_key"] in keep]
 return {"version":_ser(v),"bindings":bindings,"dependencies":deps,"environments":envs}
def freeze_version(db,i,version,p):
 _reject(p); st=_state(db,i); v=_version(db,i,version); _draft(v); manifest=_version_manifest(db,v,False); manifest["version"]["content_hash"]=None; manifest["version"]["previous_version_hash"]=None; manifest["version"]["frozen_at"]=None
 prior=db.scalar(select(ResearchProjectStateVersionRecord).where(ResearchProjectStateVersionRecord.state_id==i,ResearchProjectStateVersionRecord.status=="frozen",ResearchProjectStateVersionRecord.version<v.version).order_by(ResearchProjectStateVersionRecord.version.desc()).limit(1)); v.previous_version_hash=prior.content_hash if prior else None; v.content_hash=_hash(manifest); v.status="frozen"; v.frozen_at=datetime.now(timezone.utc); st.current_version=v.version; st.latest_version_hash=v.content_hash; db.commit(); db.refresh(v); db.refresh(st); return _ser(v)
def historical_manifest(db,i,version,public=False):
 st=_state(db,i); v=_version(db,i,version)
 if public and st.visibility!="public": raise ValueError("project state is not public")
 if v.status!="frozen": raise ValueError("historical reconstruction requires a frozen version")
 m=_version_manifest(db,v,public); return {"state":{"id":st.id,"state_key":st.state_key,"project_ref":st.project_ref,"title":st.title,"visibility":st.visibility},**m,"manifest_is_reference_first_not_restored_execution":True,"historical_state_is_declared_not_inferred":True,**boundaries()}
def add_checkpoint(db,i,p):
 _reject(p); _state(db,i); v=_version(db,i,p["version"])
 if v.status!="frozen": raise ValueError("checkpoint requires a frozen version")
 if p.get("checkpoint_type") not in CHECKPOINT_TYPES: raise ValueError("unsupported checkpoint type")
 r=ResearchProjectStateCheckpointRecord(state_id=i,version_id=v.id,checkpoint_key=p["checkpoint_key"],checkpoint_type=p["checkpoint_type"],title=p["title"],status=p.get("status","declared"),notes=p.get("notes"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def create_reconstruction_plan(db,i,p):
 _reject(p); _state(db,i); v=_version(db,i,p["version"])
 if v.status!="frozen": raise ValueError("reconstruction plan requires a frozen version")
 bindings={x.binding_key for x in db.scalars(select(ResearchProjectStateBindingRecord).where(ResearchProjectStateBindingRecord.version_id==v.id)).all()}; envs={x.environment_key for x in db.scalars(select(ResearchProjectStateEnvironmentRecord).where(ResearchProjectStateEnvironmentRecord.version_id==v.id)).all()}; rb=p.get("required_binding_keys",sorted(bindings)); re=p.get("required_environment_keys",sorted(envs)); missing_b=sorted(set(rb)-bindings); missing_e=sorted(set(re)-envs)
 r=ResearchProjectReconstructionPlanRecord(state_id=i,version_id=v.id,plan_key=p["plan_key"],status=p.get("status","declared"),required_binding_keys_json=rb,required_environment_keys_json=re,steps_json=p.get("steps",[]),notes=p.get("notes"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); out=_ser(r); out["missing_binding_keys"]=missing_b; out["missing_environment_keys"]=missing_e; out["declared_requirements_complete"]=not missing_b and not missing_e; out["plan_does_not_execute_reconstruction"]=True; return out
def _plan(db,i,key):
 r=db.scalar(select(ResearchProjectReconstructionPlanRecord).where(ResearchProjectReconstructionPlanRecord.state_id==i,ResearchProjectReconstructionPlanRecord.plan_key==key))
 if not r: raise ValueError("reconstruction plan not found")
 return r
def add_verification(db,i,plan_key,p):
 _reject(p); plan=_plan(db,i,plan_key); status=p.get("status","unverified")
 if status not in VERIFICATION_STATUSES: raise ValueError("unsupported verification status")
 r=ResearchProjectReconstructionVerificationRecord(state_id=i,plan_id=plan.id,version_id=plan.version_id,verification_key=p["verification_key"],status=status,verifier_ref=p.get("verifier_ref"),checks_json=p.get("checks",[]),evidence_refs_json=p.get("evidence_refs",[]),notes=p.get("notes"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); out=_ser(r); out["verification_is_attributed_evidence_not_core_certification"]=True; return out
def revise_state(db,i,p):
 _reject(p); st=_state(db,i); prior=_ser(st)
 for k in ("title","status","visibility"):
  if k in p: setattr(st,k,p[k])
 if "metadata" in p: st.metadata_json=p["metadata"]
 if st.status not in STATUSES or st.visibility not in VISIBILITIES: raise ValueError("invalid project state status or visibility")
 prev=db.scalar(select(func.max(ResearchProjectStateRevisionRecord.revision)).where(ResearchProjectStateRevisionRecord.state_id==i)) or 0; db.commit(); db.refresh(st); revised=_ser(st); r=ResearchProjectStateRevisionRecord(state_id=i,revision=prev+1,state_hash=_hash(revised),prior_state_json=prior,revised_state_json=revised,change_summary=p.get("change_summary"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def bundle(db,i,public=False):
 st=_state(db,i)
 if public and st.visibility!="public": raise ValueError("project state is not public")
 versions=[_ser(x) for x in db.scalars(select(ResearchProjectStateVersionRecord).where(ResearchProjectStateVersionRecord.state_id==i).order_by(ResearchProjectStateVersionRecord.version)).all()]
 manifests=[]
 for vdata in versions:
  if vdata["status"]=="frozen": manifests.append(historical_manifest(db,i,vdata["version"],public))
 checkpoints=_rows(db,ResearchProjectStateCheckpointRecord,"state_id",i); plans=_rows(db,ResearchProjectReconstructionPlanRecord,"state_id",i); verifications=_rows(db,ResearchProjectReconstructionVerificationRecord,"state_id",i); revisions=_rows(db,ResearchProjectStateRevisionRecord,"state_id",i); snapshots=_rows(db,ResearchProjectStateSnapshotRecord,"state_id",i)
 if public: plans=[]; verifications=[]; revisions=[]; snapshots=[]
 return {"state":_ser(st),"versions":versions,"historical_manifests":manifests,"checkpoints":checkpoints,"reconstruction_plans":plans,"verifications":verifications,"revisions":revisions,"snapshots":snapshots,**boundaries()}
def descriptive_summary(db,i,public=False):
 b=bundle(db,i,public); return {"state":b["state"],"version_count":len(b["versions"]),"frozen_version_count":sum(1 for x in b["versions"] if x["status"]=="frozen"),"checkpoint_types":dict(Counter(x["checkpoint_type"] for x in b["checkpoints"])),"reconstruction_plan_count":len(b["reconstruction_plans"]),"verification_statuses":dict(Counter(x["status"] for x in b["verifications"])),"summary_is_descriptive_not_reproducibility_certification":True,**boundaries()}
def lineage(db,i,public=False):
 b=bundle(db,i,public); edges=[]; state_node="project_state:"+i
 for m in b["historical_manifests"]:
  v=m["version"]; vn=f"project_state_version:{i}:{v['version']}"; edges.append({"from":state_node,"to":vn,"relation":"has_frozen_version","content_hash":v.get("content_hash")})
  for x in m["bindings"]: edges.append({"from":x["product_key"]+":"+x["object_ref"],"to":vn,"relation":x["role"],"binding_key":x["binding_key"],"object_version_ref":x.get("object_version_ref")})
  for x in m["dependencies"]: edges.append({"from":vn+":"+x["from_binding_key"],"to":vn+":"+x["to_binding_key"],"relation":x["relation"]})
  for x in m["environments"]: edges.append({"from":"environment:"+x["environment_ref"],"to":vn,"relation":"declared_runtime_environment","environment_key":x["environment_key"]})
 return {"state_id":i,"edges":edges,"edge_count":len(edges),"lineage_is_declared_not_inferred":True,**boundaries()}
def snapshot(db,i,p):
 _reject(p); state=bundle(db,i,False); state.pop("snapshots",None); prior=db.scalar(select(ResearchProjectStateSnapshotRecord).where(ResearchProjectStateSnapshotRecord.state_id==i).order_by(ResearchProjectStateSnapshotRecord.revision.desc()).limit(1)); rev=(prior.revision if prior else 0)+1; r=ResearchProjectStateSnapshotRecord(state_id=i,revision=rev,content_hash=_hash(state),previous_snapshot_hash=prior.content_hash if prior else None,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
