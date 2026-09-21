from __future__ import annotations
from collections import Counter
from datetime import datetime
import hashlib,json
from sqlalchemy import func,select
from sqlalchemy.inspection import inspect as sa_inspect
from ..models import ComputationExecutionRecord,ComputationExecutionInputRecord,ComputationExecutionParameterRecord,ComputationExecutionAssumptionRecord,ComputationExecutionEnvironmentRecord,ComputationExecutionStepRecord,ComputationExecutionOutputRecord,ComputationResearchBindingRecord,ComputationExecutionDependencyRecord,ComputationExecutionVerificationRecord,ComputationExecutionRevisionRecord,ComputationExecutionSnapshotRecord
CONTRACT="sc.research.computation-analysis-execution-lineage.v1"
EXECUTION_TYPES={"data_preparation","statistical_analysis","causal_analysis","simulation","engineering_calculation","forensic_reconstruction","ml_training","ml_inference","forecasting","optimization","visualization_transform","notebook","workflow_step","other"}
RUNTIME_KINDS={"python","r","julia","sql","workbench","ml_runtime","container","external_service","manual","other"}
STATUSES={"planned","recorded","running","completed","failed","cancelled","archived"}; VISIBILITIES={"private","internal","public"}
INPUT_TYPES={"dataset","file","research_object","source","model","parameter_set","evidence","artifact","other"}
OUTPUT_TYPES={"dataset","table","model","statistic","prediction","forecast","figure","visualization","report","artifact","log","result_bundle","other"}
TARGET_TYPES={"finding","claim","conclusion","publication","evidence","visualization","hypothesis","decision","protocol","research_object","other"}
FORBIDDEN={"execute_code_by_core","run_python_by_core","run_r_by_core","run_julia_by_core","run_workbench_by_core","train_ml_by_core","transform_data_by_core","compute_statistics_by_core","fit_models_by_core","generate_outputs_by_core","infer_findings_by_core","infer_claims_by_core","validate_results_by_core","infer_reproducibility_by_core","infer_truth_by_core"}
CLASSES=[ComputationExecutionRecord,ComputationExecutionInputRecord,ComputationExecutionParameterRecord,ComputationExecutionAssumptionRecord,ComputationExecutionEnvironmentRecord,ComputationExecutionStepRecord,ComputationExecutionOutputRecord,ComputationResearchBindingRecord,ComputationExecutionDependencyRecord,ComputationExecutionVerificationRecord,ComputationExecutionRevisionRecord,ComputationExecutionSnapshotRecord]
COUNT_NAMES=["executions","inputs","parameters","assumptions","environments","steps","outputs","research_bindings","dependencies","verifications","revisions","snapshots"]
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
 if bad: raise ValueError("Core records externally executed computation and analysis lineage; it does not execute code/runtimes, transform data, compute statistics, fit/train models, generate outputs, infer findings/claims, validate results, infer reproducibility, or infer truth: "+", ".join(bad))
def _get(db,i):
 r=db.get(ComputationExecutionRecord,i)
 if not r: raise ValueError("execution not found")
 return r
def boundaries(): return {"execution_registry_by_core":True,"versioned_input_binding_by_core":True,"parameter_binding_by_core":True,"assumption_binding_by_core":True,"software_environment_capture_by_core":True,"execution_step_registry_by_core":True,"output_binding_by_core":True,"research_object_binding_by_core":True,"cross_execution_dependency_registry_by_core":True,"verification_evidence_registry_by_core":True,"execution_revision_history_by_core":True,"execution_lineage_by_core":True,"immutable_execution_snapshots_by_core":True,**{k:False for k in FORBIDDEN}}
def readiness(db):
 counts={n:db.scalar(select(func.count()).select_from(c)) or 0 for c,n in zip(CLASSES,COUNT_NAMES)}
 return {"release":"2.87.0","contract":CONTRACT,"execution_types":sorted(EXECUTION_TYPES),"runtime_kinds":sorted(RUNTIME_KINDS),"counts":counts,**boundaries()}
def create_execution(db,p):
 _reject(p)
 if p.get("execution_type") not in EXECUTION_TYPES: raise ValueError("unsupported execution_type")
 if p.get("runtime_kind") not in RUNTIME_KINDS: raise ValueError("unsupported runtime_kind")
 if p.get("status","recorded") not in STATUSES or p.get("visibility","private") not in VISIBILITIES: raise ValueError("invalid status or visibility")
 r=ComputationExecutionRecord(execution_key=p["execution_key"],title=p["title"],execution_type=p["execution_type"],runtime_kind=p["runtime_kind"],status=p.get("status","recorded"),visibility=p.get("visibility","private"),project_ref=p.get("project_ref"),protocol_id=p.get("protocol_id"),method_plan_ref=p.get("method_plan_ref"),external_run_ref=p.get("external_run_ref"),command_or_entrypoint=p.get("command_or_entrypoint"),code_ref=p.get("code_ref"),source_revision=p.get("source_revision"),started_at=p.get("started_at"),finished_at=p.get("finished_at"),provenance_json=p.get("provenance",{}),metadata_json=p.get("metadata",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def _add(db,i,p,cls,key,extra):
 _reject(p); _get(db,i); kw={"execution_id":i,key:p[key],"provenance_json":p.get("provenance",{}),"created_by":p.get("created_by","operator")}; kw.update(extra(p)); r=cls(**kw); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_input(db,i,p):
 if p.get("input_type") not in INPUT_TYPES: raise ValueError("unsupported input_type")
 return _add(db,i,p,ComputationExecutionInputRecord,"input_key",lambda p:{"input_type":p["input_type"],"object_ref":p["object_ref"],"version_ref":p.get("version_ref"),"content_hash":p.get("content_hash"),"role":p.get("role"),"selector_json":p.get("selector",{})})
def add_parameter(db,i,p): return _add(db,i,p,ComputationExecutionParameterRecord,"parameter_key",lambda p:{"value_json":p.get("value",{}),"unit":p.get("unit"),"source_ref":p.get("source_ref"),"sensitivity_role":p.get("sensitivity_role")})
def add_assumption(db,i,p): return _add(db,i,p,ComputationExecutionAssumptionRecord,"assumption_key",lambda p:{"statement_text":p["statement_text"],"protocol_assumption_ref":p.get("protocol_assumption_ref"),"evidence_refs_json":p.get("evidence_refs",[])})
def add_environment(db,i,p): return _add(db,i,p,ComputationExecutionEnvironmentRecord,"environment_key",lambda p:{"environment_type":p["environment_type"],"runtime_name":p.get("runtime_name"),"runtime_version":p.get("runtime_version"),"os_arch":p.get("os_arch"),"container_image":p.get("container_image"),"environment_hash":p.get("environment_hash"),"dependency_manifest_ref":p.get("dependency_manifest_ref"),"packages_json":p.get("packages",[]),"hardware_json":p.get("hardware",{})})
def add_step(db,i,p): return _add(db,i,p,ComputationExecutionStepRecord,"step_key",lambda p:{"sequence":int(p.get("sequence",0)),"step_type":p["step_type"],"tool_ref":p.get("tool_ref"),"operation_text":p.get("operation_text"),"code_ref":p.get("code_ref"),"input_refs_json":p.get("input_refs",[]),"output_refs_json":p.get("output_refs",[]),"parameters_json":p.get("parameters",{})})
def add_output(db,i,p):
 if p.get("output_type") not in OUTPUT_TYPES: raise ValueError("unsupported output_type")
 return _add(db,i,p,ComputationExecutionOutputRecord,"output_key",lambda p:{"output_type":p["output_type"],"object_ref":p.get("object_ref"),"version_ref":p.get("version_ref"),"content_hash":p.get("content_hash"),"schema_json":p.get("schema",{}),"metadata_json":p.get("metadata",{})})
def add_research_binding(db,i,p):
 if p.get("target_type") not in TARGET_TYPES: raise ValueError("unsupported target_type")
 return _add(db,i,p,ComputationResearchBindingRecord,"binding_key",lambda p:{"source_output_ref":p.get("source_output_ref"),"target_type":p["target_type"],"target_ref":p["target_ref"],"relation":p["relation"],"binding_role":p.get("binding_role")})
def add_dependency(db,i,p): return _add(db,i,p,ComputationExecutionDependencyRecord,"dependency_key",lambda p:{"upstream_execution_ref":p["upstream_execution_ref"],"upstream_output_ref":p.get("upstream_output_ref"),"relation":p["relation"]})
def add_verification(db,i,p): return _add(db,i,p,ComputationExecutionVerificationRecord,"verification_key",lambda p:{"verification_type":p["verification_type"],"status":p.get("status","recorded"),"evidence_json":p.get("evidence",{}),"performed_by":p.get("performed_by"),"observed_at":p.get("observed_at")})
def revise_execution(db,i,p):
 _reject(p); r=_get(db,i); prior=_ser(r); allowed={"title":"title","status":"status","visibility":"visibility","external_run_ref":"external_run_ref","command_or_entrypoint":"command_or_entrypoint","code_ref":"code_ref","source_revision":"source_revision","started_at":"started_at","finished_at":"finished_at","metadata":"metadata_json"}
 for k,a in allowed.items():
  if k in p: setattr(r,a,p[k])
 db.flush(); revised=_ser(r); rev=(db.scalar(select(func.max(ComputationExecutionRevisionRecord.revision)).where(ComputationExecutionRevisionRecord.execution_id==i)) or 0)+1; rr=ComputationExecutionRevisionRecord(execution_id=i,revision=rev,state_hash=_hash(revised),prior_state_json=prior,revised_state_json=revised,change_summary=p.get("change_summary"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(rr); db.commit(); db.refresh(rr); return _ser(rr)
def bundle(db,i,public=False):
 e=_get(db,i)
 if public and e.visibility!="public": raise ValueError("execution is not public")
 def rows(cls): return [_ser(x) for x in db.scalars(select(cls).where(cls.execution_id==i).order_by(cls.created_at)).all()]
 return {"execution":_ser(e),"inputs":rows(ComputationExecutionInputRecord),"parameters":rows(ComputationExecutionParameterRecord),"assumptions":rows(ComputationExecutionAssumptionRecord),"environments":rows(ComputationExecutionEnvironmentRecord),"steps":rows(ComputationExecutionStepRecord),"outputs":rows(ComputationExecutionOutputRecord),"research_bindings":rows(ComputationResearchBindingRecord),"dependencies":rows(ComputationExecutionDependencyRecord),"verifications":rows(ComputationExecutionVerificationRecord),"revisions":rows(ComputationExecutionRevisionRecord),"snapshots":rows(ComputationExecutionSnapshotRecord),**boundaries()}
def descriptive_summary(db,i,public=False):
 b=bundle(db,i,public); return {"execution":b["execution"],"counts":{k:len(b[k]) for k in ("inputs","parameters","assumptions","environments","steps","outputs","research_bindings","dependencies","verifications","revisions","snapshots")},"output_types":dict(Counter(x["output_type"] for x in b["outputs"])),"target_types":dict(Counter(x["target_type"] for x in b["research_bindings"])),"summary_is_descriptive_only":True,**boundaries()}
def lineage(db,i,public=False):
 b=bundle(db,i,public); x="execution:"+i; edges=[]
 for name in ("inputs","parameters","assumptions","environments","steps","outputs","verifications"):
  edges += [{"from":name[:-1]+":"+r["id"],"to":x,"relation":"recorded_for"} if name in ("inputs","parameters","assumptions","environments") else {"from":x,"to":name[:-1]+":"+r["id"],"relation":"produces_or_records"} for r in b[name]]
 edges += [{"from":x,"to":r["target_type"]+":"+r["target_ref"],"relation":r["relation"],"source_output_ref":r.get("source_output_ref")} for r in b["research_bindings"]]
 edges += [{"from":"execution:"+r["upstream_execution_ref"],"to":x,"relation":r["relation"],"upstream_output_ref":r.get("upstream_output_ref")} for r in b["dependencies"]]
 if b["execution"].get("protocol_id"): edges.append({"from":"protocol:"+b["execution"]["protocol_id"],"to":x,"relation":"governs_execution"})
 return {"execution_id":i,"edges":edges,"edge_count":len(edges),"lineage_is_declared_not_inferred":True,**boundaries()}
def snapshot(db,i,p):
 _reject(p); state=bundle(db,i,False); state.pop("snapshots",None); prior=db.scalar(select(ComputationExecutionSnapshotRecord).where(ComputationExecutionSnapshotRecord.execution_id==i).order_by(ComputationExecutionSnapshotRecord.revision.desc()).limit(1)); rev=(prior.revision if prior else 0)+1; r=ComputationExecutionSnapshotRecord(execution_id=i,revision=rev,content_hash=_hash(state),previous_snapshot_hash=prior.content_hash if prior else None,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
