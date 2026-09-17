from __future__ import annotations
import hashlib,json
from datetime import datetime
from sqlalchemy import func,select,inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import *
CONTRACT="sc.visual-runtime.decision-intelligence.v1"
FORBIDDEN={"utility_computation_by_core","option_ranking_by_core","recommendation_generation_by_core","objective_optimization_by_core","policy_selection_by_core","decision_execution_by_core","automatic_visual_inference"}
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
 if bad:raise ValueError("Visual Decision Intelligence is declarative; Core does not execute: "+", ".join(bad))
def boundaries():return {"visual_decision_workspace_registry_by_core":True,"visual_decision_alternative_registry_by_core":True,"visual_decision_criterion_registry_by_core":True,"visual_decision_evidence_registry_by_core":True,"visual_decision_scenario_registry_by_core":True,"visual_decision_risk_registry_by_core":True,"visual_decision_tradeoff_registry_by_core":True,"visual_decision_rationale_registry_by_core":True,"visual_decision_handoff_registry_by_core":True,"immutable_visual_decision_snapshots_by_core":True,"utility_computation_by_core":False,"option_ranking_by_core":False,"recommendation_generation_by_core":False,"objective_optimization_by_core":False,"policy_selection_by_core":False,"decision_execution_by_core":False,"automatic_visual_inference":False,"automatic_visual_truth_promotion":False}
CLASSES=[VisualDecisionWorkspaceRecord,VisualDecisionAlternativeRecord,VisualDecisionCriterionRecord,VisualDecisionEvidenceBindingRecord,VisualDecisionScenarioBindingRecord,VisualDecisionRiskOverlayRecord,VisualDecisionTradeoffRecord,VisualDecisionRationaleRecord,VisualDecisionHandoffRecord,VisualDecisionSnapshotRecord]
def readiness(db):
 c=lambda x:db.scalar(select(func.count()).select_from(x)) or 0
 names=["workspaces","alternatives","criteria","evidence_bindings","scenario_bindings","risk_overlays","tradeoffs","rationales","handoffs","snapshots"]
 return {"release":"2.69.0","contract":CONTRACT,"counts":dict(zip(names,[c(x) for x in CLASSES])),**boundaries()}
def _get(db,cls,id,label):
 x=db.get(cls,id) if id else None
 if not x:raise ValueError(label+" not found.")
 return x
def _workspace(db,wid):return _get(db,VisualDecisionWorkspaceRecord,wid,"visual decision workspace")
def _views(db,cid,ids):
 allowed={r.view_id for r in db.scalars(select(VisualViewAssignmentRecord).where(VisualViewAssignmentRecord.composition_id==cid)).all()}
 bad=[x for x in ids if x not in allowed]
 if bad:raise ValueError("target views must belong to the workspace composition: "+", ".join(bad))
def create_workspace(db,composition_id,p):
 _reject(p);_get(db,VisualViewCompositionRecord,composition_id,"view composition")
 r=VisualDecisionWorkspaceRecord(composition_id=composition_id,workspace_key=p["workspace_key"],name=p["name"],decision_kind=p.get("decision_kind","evidence-informed"),purpose=p.get("purpose"),status=p.get("status","draft"),visibility=p.get("visibility","private"),settings_json=p.get("settings",{}),provenance_json=p.get("provenance",{}),metadata_json=p.get("metadata",{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def _child(db,wid,p,cls,key,fields):
 _reject(p);w=_workspace(db,wid);_views(db,w.composition_id,p.get("target_view_ids",[]));kw={"workspace_id":wid,key:p[key],"provenance_json":p.get("provenance",{})}
 for f,d in fields:
  if f=="target_view_ids":kw[f+"_json"]=p.get(f,d)
  elif f in {"name","target_product","status"}:kw[f]=p.get(f,d)
  else:kw[f+"_json"]=p.get(f,d)
 r=cls(**kw);db.add(r);db.commit();db.refresh(r);return _ser(r)
def alternative(db,w,p):return _child(db,w,p,VisualDecisionAlternativeRecord,"alternative_key",[("name","Alternative"),("action",{}),("feasibility",{}),("target_view_ids",[]),("metadata",{})])
def criterion(db,w,p):return _child(db,w,p,VisualDecisionCriterionRecord,"criterion_key",[("name","Criterion"),("objective",{}),("measure",{}),("constraints",[]),("target_view_ids",[])])
def evidence(db,w,p):return _child(db,w,p,VisualDecisionEvidenceBindingRecord,"binding_key",[("evidence_refs",[]),("predictive_refs",[]),("causal_refs",[]),("forensic_refs",[]),("target_view_ids",[]),("display_contract",{})])
def scenario(db,w,p):return _child(db,w,p,VisualDecisionScenarioBindingRecord,"binding_key",[("scenario_refs",[]),("intervention_refs",[]),("forecast_refs",[]),("target_view_ids",[]),("display_contract",{})])
def risk(db,w,p):return _child(db,w,p,VisualDecisionRiskOverlayRecord,"overlay_key",[("risk_refs",[]),("consequence_refs",[]),("uncertainty_refs",[]),("target_view_ids",[]),("display_contract",{})])
def tradeoff(db,w,p):return _child(db,w,p,VisualDecisionTradeoffRecord,"tradeoff_key",[("alternative_ids",[]),("criterion_ids",[]),("comparison_evidence",{}),("target_view_ids",[])])
def rationale(db,w,p):return _child(db,w,p,VisualDecisionRationaleRecord,"rationale_key",[("assumptions",[]),("rationale",{}),("evidence_refs",[])])
def handoff(db,w,p):return _child(db,w,p,VisualDecisionHandoffRecord,"handoff_key",[("target_product","decision-studio"),("request_contract",{}),("result_refs",[]),("status","declared")])
def bundle(db,wid,public_only=False):
 w=_workspace(db,wid)
 if public_only and w.visibility!="public":raise ValueError("visual decision workspace is not public.")
 out={"contract":CONTRACT,"workspace":_ser(w),"boundaries":boundaries()}
 for name,cls in zip(["alternatives","criteria","evidence_bindings","scenario_bindings","risk_overlays","tradeoffs","rationales","handoffs"],CLASSES[1:9]):out[name]=[_ser(x) for x in db.scalars(select(cls).where(cls.workspace_id==wid)).all()]
 out["snapshots"]=[_ser(x) for x in db.scalars(select(VisualDecisionSnapshotRecord).where(VisualDecisionSnapshotRecord.workspace_id==wid)).all()];return out
def snapshot(db,wid,p):
 _reject(p);state=bundle(db,wid);state.pop("snapshots",None);prev=db.scalars(select(VisualDecisionSnapshotRecord).where(VisualDecisionSnapshotRecord.workspace_id==wid).order_by(VisualDecisionSnapshotRecord.revision.asc())).all();rev=len(prev)+1;ph=prev[-1].content_hash if prev else None;h=_hash({"revision":rev,"previous_snapshot_hash":ph,"state":state});r=VisualDecisionSnapshotRecord(workspace_id=wid,revision=rev,content_hash=h,previous_snapshot_hash=ph,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator"));db.add(r);db.commit();db.refresh(r);return _ser(r)
