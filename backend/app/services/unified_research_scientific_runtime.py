from __future__ import annotations
import hashlib,json
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from ..models import (UnifiedResearchRuntimeSessionRecord,UnifiedResearchRuntimeObjectBindingRecord,UnifiedResearchRuntimeProductBindingRecord,UnifiedResearchRuntimeExecutionBindingRecord,UnifiedResearchRuntimeInvestigationBindingRecord,UnifiedResearchRuntimeVisualBindingRecord,UnifiedResearchRuntimeValidationBindingRecord,UnifiedResearchRuntimePackageBindingRecord,UnifiedResearchRuntimeHandoffBindingRecord,UnifiedResearchRuntimeMilestoneRecord,UnifiedResearchRuntimeRevisionRecord,UnifiedResearchRuntimeSnapshotRecord)
CONTRACT="sc.research.unified-research-scientific-investigation-runtime.v1"
FORBIDDEN=("execute_scientific_work_by_core","execute_code_by_core","run_investigation_by_core","infer_findings_by_core","infer_causality_by_core","select_hypothesis_by_core","rank_evidence_by_core","render_visuals_by_core","publish_research_by_core","authorize_access_by_core","certify_scientific_validity_by_core","determine_truth_by_core")
TABLES=(UnifiedResearchRuntimeSessionRecord,UnifiedResearchRuntimeObjectBindingRecord,UnifiedResearchRuntimeProductBindingRecord,UnifiedResearchRuntimeExecutionBindingRecord,UnifiedResearchRuntimeInvestigationBindingRecord,UnifiedResearchRuntimeVisualBindingRecord,UnifiedResearchRuntimeValidationBindingRecord,UnifiedResearchRuntimePackageBindingRecord,UnifiedResearchRuntimeHandoffBindingRecord,UnifiedResearchRuntimeMilestoneRecord,UnifiedResearchRuntimeRevisionRecord,UnifiedResearchRuntimeSnapshotRecord)
def _vis(p): return p.get("visibility","internal")
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
def _get(db,cls,i,label):
 x=db.get(cls,i)
 if x is None: raise ValueError(f"{label} not found")
 return x
def _rows(db,cls,public,*where):
 q=select(cls)
 for w in where: q=q.where(w)
 if public and hasattr(cls,"visibility"): q=q.where(cls.visibility=="public")
 return [_ser(x) for x in db.scalars(q.order_by(cls.created_at.asc())).all()]
def _hash(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def readiness(db:Session):
 counts={c.__tablename__:len(db.scalars(select(c.id)).all()) for c in TABLES}
 out={"release":"3.0.0","contract":CONTRACT,"migration_0102_applied":True,"counts":counts,"reference_first_runtime_by_core":True,"unified_session_registry_by_core":True,"research_object_binding_by_core":True,"product_context_binding_by_core":True,"computation_execution_binding_by_core":True,"investigation_binding_by_core":True,"visual_reasoning_binding_by_core":True,"validation_challenge_binding_by_core":True,"research_package_binding_by_core":True,"cross_product_handoff_binding_by_core":True,"milestone_registry_by_core":True,"revision_history_by_core":True,"immutable_runtime_snapshots_by_core":True,"underlying_objects_remain_authoritative_in_specialist_layers":True}
 out.update({k:False for k in FORBIDDEN}); return out
def create_session(db,p):
 _reject(p); r=UnifiedResearchRuntimeSessionRecord(session_key=p["session_key"],title=p["title"],project_ref=p["project_ref"],status=p.get("status","active"),workflow_ref=p.get("workflow_ref"),project_state_ref=p.get("project_state_ref"),runtime_contract_ref=p.get("runtime_contract_ref","sc.research.unified-runtime-contract.v1"),certification_suite_ref=p.get("certification_suite_ref"),visibility=_vis(p),metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def _add(db,cls,p,fields):
 _reject(p); _get(db,UnifiedResearchRuntimeSessionRecord,p["session_id"],"session"); kw={k:p[k] for k in fields if k in p}; kw["visibility"]=_vis(p); kw["metadata_json"]=p.get("metadata",{});
 for k,v in list(kw.items()):
  if k.endswith("_json") and k[:-5] in p: kw[k]=p[k[:-5]]
 r=cls(**kw); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_object_binding(db,p): return _add(db,UnifiedResearchRuntimeObjectBindingRecord,p,("session_id","object_type","object_ref","version_ref","content_hash","role"))
def add_product_binding(db,p):
 p=dict(p); p["declared_capabilities_json"]=p.get("declared_capabilities",[]); return _add(db,UnifiedResearchRuntimeProductBindingRecord,p,("session_id","product_ref","product_version","runtime_binding_ref","context_ref","declared_capabilities_json"))
def add_execution_binding(db,p):
 p=dict(p); p["input_refs_json"]=p.get("input_refs",[]); p["output_refs_json"]=p.get("output_refs",[]); return _add(db,UnifiedResearchRuntimeExecutionBindingRecord,p,("session_id","execution_ref","runtime","environment_ref","method_ref","input_refs_json","output_refs_json"))
def add_investigation_binding(db,p):
 p=dict(p); p["evidence_refs_json"]=p.get("evidence_refs",[]); p["claim_refs_json"]=p.get("claim_refs",[]); p["hypothesis_refs_json"]=p.get("hypothesis_refs",[]); return _add(db,UnifiedResearchRuntimeInvestigationBindingRecord,p,("session_id","investigation_ref","investigation_type","evidence_refs_json","claim_refs_json","hypothesis_refs_json"))
def add_visual_binding(db,p):
 p=dict(p); p["source_refs_json"]=p.get("source_refs",[]); return _add(db,UnifiedResearchRuntimeVisualBindingRecord,p,("session_id","visual_ref","visual_type","scene_ref","view_ref","source_refs_json"))
def add_validation_binding(db,p):
 p=dict(p); p["target_refs_json"]=p.get("target_refs",[]); p["evidence_refs_json"]=p.get("evidence_refs",[]); return _add(db,UnifiedResearchRuntimeValidationBindingRecord,p,("session_id","validation_ref","validation_type","target_refs_json","evidence_refs_json","status"))
def add_package_binding(db,p):
 p=dict(p); p["member_refs_json"]=p.get("member_refs",[]); return _add(db,UnifiedResearchRuntimePackageBindingRecord,p,("session_id","package_ref","package_type","version_ref","content_hash","member_refs_json"))
def add_handoff_binding(db,p): return _add(db,UnifiedResearchRuntimeHandoffBindingRecord,p,("session_id","handoff_ref","source_product_ref","target_product_ref","context_ref","status"))
def add_milestone(db,p):
 p=dict(p); p["object_refs_json"]=p.get("object_refs",[]); return _add(db,UnifiedResearchRuntimeMilestoneRecord,p,("session_id","milestone_key","milestone_type","state_ref","object_refs_json","note"))
def revise(db,p):
 _reject(p); sid=p["session_id"]; _get(db,UnifiedResearchRuntimeSessionRecord,sid,"session"); rev=(db.scalar(select(func.max(UnifiedResearchRuntimeRevisionRecord.revision)).where(UnifiedResearchRuntimeRevisionRecord.session_id==sid)) or 0)+1; r=UnifiedResearchRuntimeRevisionRecord(session_id=sid,revision=rev,prior_state_json=p.get("prior_state",{}),revised_state_json=p.get("revised_state",{}),reason=p.get("reason"),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def bundle(db,sid,public=False):
 s=_get(db,UnifiedResearchRuntimeSessionRecord,sid,"session")
 if public and s.visibility!="public": raise ValueError("session not public")
 q=lambda cls:_rows(db,cls,public,cls.session_id==sid)
 return {"release":"3.0.0","contract":CONTRACT,"session":_ser(s),"object_bindings":q(UnifiedResearchRuntimeObjectBindingRecord),"product_bindings":q(UnifiedResearchRuntimeProductBindingRecord),"execution_bindings":q(UnifiedResearchRuntimeExecutionBindingRecord),"investigation_bindings":q(UnifiedResearchRuntimeInvestigationBindingRecord),"visual_bindings":q(UnifiedResearchRuntimeVisualBindingRecord),"validation_bindings":q(UnifiedResearchRuntimeValidationBindingRecord),"package_bindings":q(UnifiedResearchRuntimePackageBindingRecord),"handoff_bindings":q(UnifiedResearchRuntimeHandoffBindingRecord),"milestones":q(UnifiedResearchRuntimeMilestoneRecord),"revisions":[] if public else q(UnifiedResearchRuntimeRevisionRecord),"snapshots":[] if public else q(UnifiedResearchRuntimeSnapshotRecord),"reference_first":True,"underlying_objects_remain_authoritative":True}
def summary(db,sid,public=False):
 b=bundle(db,sid,public); return {"release":"3.0.0","contract":CONTRACT,"session":b["session"],"counts":{k:len(v) for k,v in b.items() if isinstance(v,list)},"reference_first":True,"core_executes_specialist_work":False}
def lineage(db,sid,public=False):
 b=bundle(db,sid,public); edges=[]
 for name in ("object_bindings","execution_bindings","investigation_bindings","visual_bindings","validation_bindings","package_bindings","handoff_bindings"):
  for x in b[name]:
   ref=x.get("object_ref") or x.get("execution_ref") or x.get("investigation_ref") or x.get("visual_ref") or x.get("validation_ref") or x.get("package_ref") or x.get("handoff_ref")
   edges.append({"from":b["session"]["project_ref"],"to":ref,"relation":name.removesuffix("_bindings")})
 return {"release":"3.0.0","contract":CONTRACT,"session_id":sid,"edges":edges,"lineage_is_declared_not_inferred":True}
def snapshot(db,p):
 _reject(p); sid=p["session_id"]; _get(db,UnifiedResearchRuntimeSessionRecord,sid,"session"); prev=db.scalar(select(UnifiedResearchRuntimeSnapshotRecord).where(UnifiedResearchRuntimeSnapshotRecord.session_id==sid).order_by(UnifiedResearchRuntimeSnapshotRecord.revision.desc())); rev=(prev.revision if prev else 0)+1; state=bundle(db,sid,False); h=_hash({"session_id":sid,"revision":rev,"previous":prev.content_hash if prev else None,"state":state}); r=UnifiedResearchRuntimeSnapshotRecord(session_id=sid,revision=rev,content_hash=h,previous_snapshot_hash=prev.content_hash if prev else None,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
