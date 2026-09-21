from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import hashlib, json
from sqlalchemy import func, select
from sqlalchemy.inspection import inspect as sa_inspect
from ..models import (
 ResearchWorkflowRecord,ResearchWorkflowStageRecord,ResearchWorkflowTransitionRecord,ResearchWorkflowContextBindingRecord,
 ResearchWorkflowHandoffRecord,ResearchWorkflowCheckpointRecord,ResearchWorkflowEventRecord,ResearchWorkflowPolicyRecord,
 ResearchWorkflowRevisionRecord,ResearchWorkflowSnapshotRecord,
)
CONTRACT="sc.research.workflow-orchestration.v1"
STATUSES={"draft","active","paused","completed","archived"}
VISIBILITIES={"private","internal","public"}
WORKFLOW_TYPES={"research_lifecycle","scientific_study","investigation","systematic_review","engineering_analysis","forensic_investigation","publication_pipeline","replication","custom"}
STAGE_TYPES={"question","search","source_screening","evidence","protocol","data_acquisition","analysis","finding","claim","inference","challenge","revision","peer_review","replication","publication","synthesis","decision","archive","custom"}
STAGE_STATUSES={"pending","ready","in_progress","blocked","completed","skipped","archived"}
TRANSITION_STATUSES={"declared","approved","applied","rejected","cancelled"}
TRIGGER_TYPES={"manual","external_event","evidence_available","protocol_ready","analysis_complete","challenge_recorded","review_recorded","replication_recorded","publication_ready","custom"}
HANDOFF_STATUSES={"planned","ready","dispatched","acknowledged","completed","failed","cancelled"}
PRODUCTS={"core","library","research_librarian","workspace","research_lab","workbench","site_intelligence","decision_studio","catalyst_data","external"}
CHECKPOINT_TYPES={"review","approval","data_ready","method_ready","audit_ready","evidence_ready","replication_ready","publication_ready","handoff_ready","custom"}
CHECKPOINT_STATUSES={"pending","satisfied","waived","failed"}
EVENT_TYPES={"workflow_created","workflow_updated","stage_ready","stage_started","stage_completed","stage_blocked","transition_declared","transition_applied","handoff_planned","handoff_acknowledged","checkpoint_recorded","challenge_recorded","revision_recorded","publication_recorded","custom"}
POLICY_SCOPES={"workflow","stage","transition","handoff","checkpoint"}
RULE_TYPES={"allowed_transition","required_checkpoint","required_binding","required_product","visibility","manual_approval","other"}
OBJECT_TYPES={"project","question","source","evidence","protocol","dataset","method","execution","output","finding","claim","inference","hypothesis","argument","conclusion","audit","review","replication","publication","synthesis","notebook","visualization","other"}
FORBIDDEN={"choose_research_path_by_core","autonomously_advance_workflow_by_core","execute_specialist_work_by_core","dispatch_external_handoff_by_core","infer_stage_completion_by_core","generate_findings_by_core","generate_claims_by_core","approve_scientific_validity_by_core","resolve_challenges_by_core","rank_research_paths_by_core","determine_truth_by_core"}
CLASSES=[ResearchWorkflowRecord,ResearchWorkflowStageRecord,ResearchWorkflowTransitionRecord,ResearchWorkflowContextBindingRecord,ResearchWorkflowHandoffRecord,ResearchWorkflowCheckpointRecord,ResearchWorkflowEventRecord,ResearchWorkflowPolicyRecord,ResearchWorkflowRevisionRecord,ResearchWorkflowSnapshotRecord]
COUNT_NAMES=["workflows","stages","transitions","context_bindings","handoffs","checkpoints","events","policies","revisions","snapshots"]
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
 if bad: raise ValueError("Core coordinates explicitly declared research workflow state and handoffs; it does not choose research paths, advance autonomously, execute specialist work, dispatch external jobs, infer completion, generate findings/claims, approve scientific validity, resolve challenges, rank paths, or determine truth: "+", ".join(bad))
def _get(db,i):
 r=db.get(ResearchWorkflowRecord,i)
 if not r: raise ValueError("research workflow not found")
 return r
def boundaries(): return {"workflow_registry_by_core":True,"stage_registry_by_core":True,"declared_transition_registry_by_core":True,"apply_declared_transition_by_core":True,"cross_product_context_binding_by_core":True,"handoff_state_registry_by_core":True,"checkpoint_registry_by_core":True,"workflow_event_timeline_by_core":True,"workflow_policy_registry_by_core":True,"workflow_revision_history_by_core":True,"workflow_lineage_by_core":True,"immutable_workflow_snapshots_by_core":True,**{k:False for k in FORBIDDEN}}
def readiness(db):
 counts={n:db.scalar(select(func.count()).select_from(c)) or 0 for c,n in zip(CLASSES,COUNT_NAMES)}
 return {"release":"2.90.0","contract":CONTRACT,"workflow_types":sorted(WORKFLOW_TYPES),"stage_types":sorted(STAGE_TYPES),"products":sorted(PRODUCTS),"counts":counts,**boundaries()}
def create_workflow(db,p):
 _reject(p); st=p.get("status","draft"); vis=p.get("visibility","private"); wt=p.get("workflow_type","research_lifecycle")
 if st not in STATUSES or vis not in VISIBILITIES or wt not in WORKFLOW_TYPES: raise ValueError("invalid workflow type, status, or visibility")
 r=ResearchWorkflowRecord(workflow_key=p["workflow_key"],title=p["title"],workflow_type=wt,status=st,visibility=vis,project_ref=p.get("project_ref"),protocol_ref=p.get("protocol_ref"),program_ref=p.get("program_ref"),current_stage_key=p.get("current_stage_key"),orchestration_mode="governed",metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def _add(db,i,p,cls,key,extra):
 _reject(p); _get(db,i); kw={"workflow_id":i,key:p[key],"provenance_json":p.get("provenance",{}),"created_by":p.get("created_by","operator")}; kw.update(extra(p)); r=cls(**kw); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_stage(db,i,p):
 if p.get("stage_type") not in STAGE_TYPES or p.get("status","pending") not in STAGE_STATUSES: raise ValueError("unsupported stage type or status")
 if p.get("responsible_product") not in (None,*PRODUCTS): raise ValueError("unsupported responsible_product")
 r=_add(db,i,p,ResearchWorkflowStageRecord,"stage_key",lambda p:{"stage_type":p["stage_type"],"ordinal":int(p.get("ordinal",0)),"status":p.get("status","pending"),"responsible_product":p.get("responsible_product"),"object_ref":p.get("object_ref"),"entry_criteria_json":p.get("entry_criteria",{}),"exit_criteria_json":p.get("exit_criteria",{})})
 w=_get(db,i)
 if w.current_stage_key is None and p.get("status") in {"ready","in_progress"}: w.current_stage_key=p["stage_key"]; db.commit()
 return r
def add_transition(db,i,p):
 if p.get("status","declared") not in TRANSITION_STATUSES or p.get("trigger_type","manual") not in TRIGGER_TYPES: raise ValueError("unsupported transition status or trigger")
 stages={x.stage_key for x in db.scalars(select(ResearchWorkflowStageRecord).where(ResearchWorkflowStageRecord.workflow_id==i)).all()}
 if p["from_stage_key"] not in stages or p["to_stage_key"] not in stages: raise ValueError("transition stages must already exist in workflow")
 return _add(db,i,p,ResearchWorkflowTransitionRecord,"transition_key",lambda p:{"from_stage_key":p["from_stage_key"],"to_stage_key":p["to_stage_key"],"status":p.get("status","declared"),"trigger_type":p.get("trigger_type","manual"),"condition_json":p.get("condition",{}),"rationale":p.get("rationale"),"declared_by":p.get("declared_by")})
def apply_transition(db,i,transition_key,p):
 _reject(p); w=_get(db,i); t=db.scalar(select(ResearchWorkflowTransitionRecord).where(ResearchWorkflowTransitionRecord.workflow_id==i,ResearchWorkflowTransitionRecord.transition_key==transition_key));
 if not t: raise ValueError("workflow transition not found")
 if t.status in {"rejected","cancelled"}: raise ValueError("transition cannot be applied")
 declared=bool(p.get("declared_complete",False))
 if not declared: raise ValueError("declared_complete=true is required; Core does not infer stage completion")
 source=db.scalar(select(ResearchWorkflowStageRecord).where(ResearchWorkflowStageRecord.workflow_id==i,ResearchWorkflowStageRecord.stage_key==t.from_stage_key)); target=db.scalar(select(ResearchWorkflowStageRecord).where(ResearchWorkflowStageRecord.workflow_id==i,ResearchWorkflowStageRecord.stage_key==t.to_stage_key))
 if not source or not target: raise ValueError("transition stage is missing")
 source.status=p.get("source_status","completed"); target.status=p.get("target_status","in_progress")
 if source.status not in STAGE_STATUSES or target.status not in STAGE_STATUSES: raise ValueError("unsupported stage status")
 t.status="applied"; t.applied_at=datetime.now(timezone.utc); w.current_stage_key=target.stage_key; w.status="active" if w.status=="draft" else w.status
 ev=ResearchWorkflowEventRecord(workflow_id=i,event_key=p.get("event_key",f"transition:{transition_key}:{t.id}"),event_type="transition_applied",stage_key=target.stage_key,actor_ref=p.get("actor_ref"),details_json={"transition_key":transition_key,"from_stage_key":source.stage_key,"to_stage_key":target.stage_key},provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(ev); db.commit(); db.refresh(t)
 return {"transition":_ser(t),"current_stage_key":w.current_stage_key,"source_stage":_ser(source),"target_stage":_ser(target),"autonomous":False}
def add_binding(db,i,p):
 if p.get("object_type") not in OBJECT_TYPES: raise ValueError("unsupported workflow object_type")
 if p.get("product_key") not in (None,*PRODUCTS): raise ValueError("unsupported product_key")
 return _add(db,i,p,ResearchWorkflowContextBindingRecord,"binding_key",lambda p:{"stage_key":p.get("stage_key"),"product_key":p.get("product_key"),"object_type":p["object_type"],"object_ref":p["object_ref"],"relation":p.get("relation","context"),"context_json":p.get("context",{})})
def add_handoff(db,i,p):
 if p.get("from_product") not in PRODUCTS or p.get("to_product") not in PRODUCTS: raise ValueError("unsupported handoff product")
 if p.get("status","planned") not in HANDOFF_STATUSES: raise ValueError("unsupported handoff status")
 return _add(db,i,p,ResearchWorkflowHandoffRecord,"handoff_key",lambda p:{"stage_key":p.get("stage_key"),"from_product":p["from_product"],"to_product":p["to_product"],"status":p.get("status","planned"),"context_json":p.get("context",{}),"external_handoff_ref":p.get("external_handoff_ref"),"acknowledged_by":p.get("acknowledged_by")})
def add_checkpoint(db,i,p):
 if p.get("checkpoint_type") not in CHECKPOINT_TYPES or p.get("status","pending") not in CHECKPOINT_STATUSES: raise ValueError("unsupported checkpoint type or status")
 return _add(db,i,p,ResearchWorkflowCheckpointRecord,"checkpoint_key",lambda p:{"stage_key":p.get("stage_key"),"checkpoint_type":p["checkpoint_type"],"status":p.get("status","pending"),"statement_text":p["statement_text"],"evidence_refs_json":p.get("evidence_refs",[]),"declared_by":p.get("declared_by")})
def add_event(db,i,p):
 if p.get("event_type") not in EVENT_TYPES: raise ValueError("unsupported workflow event_type")
 obs=p.get("observed_at"); dt=datetime.fromisoformat(obs.replace("Z","+00:00")) if isinstance(obs,str) else datetime.now(timezone.utc)
 return _add(db,i,p,ResearchWorkflowEventRecord,"event_key",lambda p:{"event_type":p["event_type"],"stage_key":p.get("stage_key"),"actor_ref":p.get("actor_ref"),"details_json":p.get("details",{}),"observed_at":dt})
def add_policy(db,i,p):
 if p.get("scope") not in POLICY_SCOPES or p.get("rule_type") not in RULE_TYPES: raise ValueError("unsupported workflow policy")
 return _add(db,i,p,ResearchWorkflowPolicyRecord,"policy_key",lambda p:{"scope":p["scope"],"rule_type":p["rule_type"],"rule_json":p.get("rule",{}),"active":bool(p.get("active",True))})
def bundle(db,i,public=False):
 w=_get(db,i)
 if public and w.visibility!="public": raise ValueError("workflow is not public")
 def rows(cls): return [_ser(x) for x in db.scalars(select(cls).where(cls.workflow_id==i).order_by(cls.created_at,cls.id)).all()]
 return {"workflow":_ser(w),"stages":rows(ResearchWorkflowStageRecord),"transitions":rows(ResearchWorkflowTransitionRecord),"context_bindings":rows(ResearchWorkflowContextBindingRecord),"handoffs":rows(ResearchWorkflowHandoffRecord),"checkpoints":rows(ResearchWorkflowCheckpointRecord),"events":rows(ResearchWorkflowEventRecord),"policies":rows(ResearchWorkflowPolicyRecord),"revisions":rows(ResearchWorkflowRevisionRecord),"snapshots":rows(ResearchWorkflowSnapshotRecord),**boundaries()}
def descriptive_summary(db,i,public=False):
 b=bundle(db,i,public); return {"workflow":b["workflow"],"stage_statuses":dict(Counter(x["status"] for x in b["stages"])),"stage_types":dict(Counter(x["stage_type"] for x in b["stages"])),"handoff_statuses":dict(Counter(x["status"] for x in b["handoffs"])),"checkpoint_statuses":dict(Counter(x["status"] for x in b["checkpoints"])),"current_stage_key":b["workflow"].get("current_stage_key"),"summary_is_descriptive_not_research_judgment":True,**boundaries()}
def timeline(db,i,public=False):
 b=bundle(db,i,public); items=[]
 for s in b["stages"]: items.append({"kind":"stage","key":s["stage_key"],"stage_type":s["stage_type"],"status":s["status"],"ordinal":s["ordinal"],"observed_at":s["created_at"]})
 for e in b["events"]: items.append({"kind":"event","key":e["event_key"],"event_type":e["event_type"],"stage_key":e.get("stage_key"),"observed_at":e["observed_at"]})
 return {"workflow_id":i,"items":sorted(items,key=lambda x:(x.get("ordinal",10**9),x.get("observed_at") or "")),"timeline_is_recorded_not_inferred":True,**boundaries()}
def lineage(db,i,public=False):
 b=bundle(db,i,public); w=b["workflow"]; node="workflow:"+i; edges=[]
 for field,typ in (("project_ref","project"),("protocol_ref","protocol"),("program_ref","program")):
  if w.get(field): edges.append({"from":typ+":"+w[field],"to":node,"relation":"workflow_context"})
 edges += [{"from":node,"to":"stage:"+x["stage_key"],"relation":"contains_stage"} for x in b["stages"]]
 edges += [{"from":"stage:"+x["from_stage_key"],"to":"stage:"+x["to_stage_key"],"relation":"declared_transition","transition_key":x["transition_key"]} for x in b["transitions"]]
 edges += [{"from":x["object_type"]+":"+x["object_ref"],"to":"stage:"+(x.get("stage_key") or "unscoped"),"relation":x["relation"],"product_key":x.get("product_key")} for x in b["context_bindings"]]
 edges += [{"from":"product:"+x["from_product"],"to":"product:"+x["to_product"],"relation":"workflow_handoff","stage_key":x.get("stage_key"),"handoff_key":x["handoff_key"]} for x in b["handoffs"]]
 return {"workflow_id":i,"edges":edges,"edge_count":len(edges),"lineage_is_declared_not_inferred":True,**boundaries()}
def revise_workflow(db,i,p):
 _reject(p); w=_get(db,i); prior=_ser(w)
 for k in ("title","status","visibility","current_stage_key"):
  if k in p: setattr(w,k,p[k])
 if w.status not in STATUSES or w.visibility not in VISIBILITIES: raise ValueError("invalid workflow status or visibility")
 prev=db.scalar(select(func.max(ResearchWorkflowRevisionRecord.revision)).where(ResearchWorkflowRevisionRecord.workflow_id==i)) or 0; db.commit(); db.refresh(w); revised=_ser(w); r=ResearchWorkflowRevisionRecord(workflow_id=i,revision=prev+1,state_hash=_hash(revised),prior_state_json=prior,revised_state_json=revised,change_summary=p.get("change_summary"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def snapshot(db,i,p):
 _reject(p); state=bundle(db,i,False); state.pop("snapshots",None); prior=db.scalar(select(ResearchWorkflowSnapshotRecord).where(ResearchWorkflowSnapshotRecord.workflow_id==i).order_by(ResearchWorkflowSnapshotRecord.revision.desc()).limit(1)); rev=(prior.revision if prior else 0)+1; r=ResearchWorkflowSnapshotRecord(workflow_id=i,revision=rev,content_hash=_hash(state),previous_snapshot_hash=prior.content_hash if prior else None,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
