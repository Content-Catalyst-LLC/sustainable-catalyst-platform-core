from __future__ import annotations
import hashlib, json
from datetime import datetime
from sqlalchemy import func, select, inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import *
CONTRACT="sc.visual-runtime.unified-reasoning.v1"
LAYERS={"scene","composition","grammar","linked-views","query","model","predictive","forensics","decision"}
FORBIDDEN={"render_by_core","layout_computation_by_core","query_execution_by_core","model_execution_by_core","forecast_execution_by_core","forensic_inference_by_core","decision_ranking_by_core","recommendation_generation_by_core","automatic_visual_inference","automatic_truth_promotion"}
def _ser(row):
 out={}
 for a in sa_inspect(row).mapper.column_attrs:
  v=getattr(row,a.key);out[a.key]=v.isoformat() if isinstance(v,datetime) else v
 for k in list(out):
  if k.endswith("_json"):out[k[:-5]]=out.pop(k)
 return out
def _hash(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def _reject(p):
 bad=sorted(k for k in FORBIDDEN if p.get(k) not in (None,False))
 if bad:raise ValueError("Unified Visual Reasoning Engine is declarative; Core does not execute: "+", ".join(bad))
def boundaries():return {"unified_visual_reasoning_workspace_registry_by_core":True,"cross_layer_binding_registry_by_core":True,"reasoning_path_registry_by_core":True,"cross_layer_state_bridge_registry_by_core":True,"evidence_chain_registry_by_core":True,"specialist_runtime_handoff_registry_by_core":True,"reproducibility_package_binding_registry_by_core":True,"replay_state_registry_by_core":True,"immutable_unified_visual_snapshots_by_core":True,"render_by_core":False,"layout_computation_by_core":False,"query_execution_by_core":False,"model_execution_by_core":False,"forecast_execution_by_core":False,"forensic_inference_by_core":False,"decision_ranking_by_core":False,"recommendation_generation_by_core":False,"automatic_visual_inference":False,"automatic_truth_promotion":False}
CLASSES=[UnifiedVisualReasoningWorkspaceRecord,UnifiedVisualLayerBindingRecord,UnifiedVisualReasoningPathRecord,UnifiedVisualStateBridgeRecord,UnifiedVisualEvidenceChainRecord,UnifiedVisualRuntimeHandoffRecord,UnifiedVisualPackageBindingRecord,UnifiedVisualReplayStateRecord,UnifiedVisualReasoningSnapshotRecord]
def readiness(db):
 c=lambda x:db.scalar(select(func.count()).select_from(x)) or 0
 names=["workspaces","layer_bindings","reasoning_paths","state_bridges","evidence_chains","runtime_handoffs","package_bindings","replay_states","snapshots"]
 return {"release":"2.70.0","contract":CONTRACT,"layers":sorted(LAYERS),"counts":dict(zip(names,[c(x) for x in CLASSES])),**boundaries()}
def _get(db,cls,id,label):
 x=db.get(cls,id) if id else None
 if not x:raise ValueError(label+" not found.")
 return x
def _workspace(db,wid):return _get(db,UnifiedVisualReasoningWorkspaceRecord,wid,"unified visual reasoning workspace")
def _views(db,cid,ids):
 allowed={r.view_id for r in db.scalars(select(VisualViewAssignmentRecord).where(VisualViewAssignmentRecord.composition_id==cid)).all()}
 bad=[x for x in ids if x not in allowed]
 if bad:raise ValueError("target views must belong to the workspace composition: "+", ".join(bad))
def create_workspace(db,composition_id,p):
 _reject(p);_get(db,VisualViewCompositionRecord,composition_id,"view composition")
 r=UnifiedVisualReasoningWorkspaceRecord(composition_id=composition_id,workspace_key=p["workspace_key"],name=p["name"],purpose=p.get("purpose"),status=p.get("status","draft"),visibility=p.get("visibility","private"),settings_json=p.get("settings",{}),provenance_json=p.get("provenance",{}),metadata_json=p.get("metadata",{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def layer_binding(db,wid,p):
 _reject(p);w=_workspace(db,wid);_views(db,w.composition_id,p.get("view_ids",[]))
 r=UnifiedVisualLayerBindingRecord(workspace_id=wid,binding_key=p["binding_key"],scene_ids_json=p.get("scene_ids",[]),view_ids_json=p.get("view_ids",[]),grammar_specification_ids_json=p.get("grammar_specification_ids",[]),link_policy_ids_json=p.get("link_policy_ids",[]),exploration_session_ids_json=p.get("exploration_session_ids",[]),model_construction_ids_json=p.get("model_construction_ids",[]),predictive_workspace_ids_json=p.get("predictive_workspace_ids",[]),forensics_workspace_ids_json=p.get("forensics_workspace_ids",[]),decision_workspace_ids_json=p.get("decision_workspace_ids",[]),display_contract_json=p.get("display_contract",{}),provenance_json=p.get("provenance",{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def reasoning_path(db,wid,p):
 _reject(p);w=_workspace(db,wid);_views(db,w.composition_id,p.get("target_view_ids",[]));stages=p.get("stages",[])
 if not stages or any((not isinstance(x,dict)) or x.get("layer") not in LAYERS for x in stages):raise ValueError("reasoning path stages must declare supported layers")
 r=UnifiedVisualReasoningPathRecord(workspace_id=wid,path_key=p["path_key"],stages_json=stages,transitions_json=p.get("transitions",[]),target_view_ids_json=p.get("target_view_ids",[]),provenance_json=p.get("provenance",{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def state_bridge(db,wid,p):
 _reject(p);_workspace(db,wid);src=p["source_layer"];dst=p["target_layer"]
 if src not in LAYERS or dst not in LAYERS:raise ValueError("state bridge layers are unsupported")
 r=UnifiedVisualStateBridgeRecord(workspace_id=wid,bridge_key=p["bridge_key"],source_layer=src,target_layer=dst,source_refs_json=p.get("source_refs",[]),target_refs_json=p.get("target_refs",[]),state_contract_json=p.get("state_contract",{}),propagation_evidence_json=p.get("propagation_evidence",{}),provenance_json=p.get("provenance",{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def evidence_chain(db,wid,p):
 _reject(p);w=_workspace(db,wid);_views(db,w.composition_id,p.get("target_view_ids",[]));r=UnifiedVisualEvidenceChainRecord(workspace_id=wid,chain_key=p["chain_key"],evidence_refs_json=p.get("evidence_refs",[]),reasoning_refs_json=p.get("reasoning_refs",[]),provenance_links_json=p.get("provenance_links",[]),uncertainty_context_json=p.get("uncertainty_context",{}),target_view_ids_json=p.get("target_view_ids",[]));db.add(r);db.commit();db.refresh(r);return _ser(r)
def handoff(db,wid,p):
 _reject(p);_workspace(db,wid);r=UnifiedVisualRuntimeHandoffRecord(workspace_id=wid,handoff_key=p["handoff_key"],target_product=p.get("target_product","workbench"),request_contract_json=p.get("request_contract",{}),result_refs_json=p.get("result_refs",[]),status=p.get("status","declared"),provenance_json=p.get("provenance",{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def package_binding(db,wid,p):
 _reject(p);_workspace(db,wid);r=UnifiedVisualPackageBindingRecord(workspace_id=wid,binding_key=p["binding_key"],visual_package_refs_json=p.get("visual_package_refs",[]),predictive_package_refs_json=p.get("predictive_package_refs",[]),forensic_package_refs_json=p.get("forensic_package_refs",[]),investigation_package_refs_json=p.get("investigation_package_refs",[]),verification_refs_json=p.get("verification_refs",[]),provenance_json=p.get("provenance",{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def replay_state(db,wid,p):
 _reject(p);_workspace(db,wid);r=UnifiedVisualReplayStateRecord(workspace_id=wid,replay_key=p["replay_key"],state_manifest_json=p.get("state_manifest",{}),environment_refs_json=p.get("environment_refs",[]),external_execution_contract_json=p.get("external_execution_contract",{}),verification_json=p.get("verification",{}),provenance_json=p.get("provenance",{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def bundle(db,wid,public_only=False):
 w=_workspace(db,wid)
 if public_only and w.visibility!="public":raise ValueError("unified visual reasoning workspace is not public.")
 out={"contract":CONTRACT,"workspace":_ser(w),"layers":sorted(LAYERS),"boundaries":boundaries()}
 for name,cls in zip(["layer_bindings","reasoning_paths","state_bridges","evidence_chains","runtime_handoffs","package_bindings","replay_states"],CLASSES[1:8]):out[name]=[_ser(x) for x in db.scalars(select(cls).where(cls.workspace_id==wid)).all()]
 out["snapshots"]=[_ser(x) for x in db.scalars(select(UnifiedVisualReasoningSnapshotRecord).where(UnifiedVisualReasoningSnapshotRecord.workspace_id==wid)).all()];return out
def snapshot(db,wid,p):
 _reject(p);state=bundle(db,wid);state.pop("snapshots",None);prev=db.scalars(select(UnifiedVisualReasoningSnapshotRecord).where(UnifiedVisualReasoningSnapshotRecord.workspace_id==wid).order_by(UnifiedVisualReasoningSnapshotRecord.revision.asc())).all();rev=len(prev)+1;ph=prev[-1].content_hash if prev else None;h=_hash({"revision":rev,"previous_snapshot_hash":ph,"state":state});r=UnifiedVisualReasoningSnapshotRecord(workspace_id=wid,revision=rev,content_hash=h,previous_snapshot_hash=ph,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator"));db.add(r);db.commit();db.refresh(r);return _ser(r)
