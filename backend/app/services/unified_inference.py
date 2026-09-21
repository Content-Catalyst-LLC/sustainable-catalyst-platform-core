from __future__ import annotations
from collections import Counter
from datetime import datetime
import hashlib,json
from sqlalchemy import func,select
from sqlalchemy.inspection import inspect as sa_inspect
from ..models import (
 ResearchInferenceRecord,ResearchInferenceClassificationRecord,ResearchInferenceBasisRecord,
 ResearchInferenceAssumptionRecord,ResearchInferenceUncertaintyRecord,ResearchInferenceRelationRecord,
 ResearchInferenceChallengeRecord,ResearchInferenceRevisionRecord,ResearchInferenceSnapshotRecord,
)
CONTRACT="sc.research.unified-findings-claims-inference.v1"
INFERENCE_TYPES={"observation","measurement","descriptive_finding","statistical_association","statistical_inference","causal_inference","model_derived_result","prediction","forecast","interpretation","expert_judgment","hypothesis","speculation","conclusion"}
STATUSES={"proposed","recorded","supported","challenged","qualified","superseded","withdrawn","archived"}
VISIBILITIES={"private","internal","public"}
OBJECT_TYPES={"finding","interpretation","claim","conclusion","hypothesis","argument","computation_output","evidence","dataset","protocol","publication","replication","synthesis","observation","measurement","other"}
BASIS_TYPES={"observation","measurement","evidence","source","dataset","computation_output","finding","claim","conclusion","hypothesis","publication","replication","synthesis","method","other"}
BASIS_RELATIONS={"observed_from","measured_from","computed_from","derived_from","supported_by","contradicted_by","qualified_by","contextualized_by","depends_on"}
RELATIONS={"supports","contradicts","qualifies","extends","alternative_to","depends_on","derived_from","refines"}
CHALLENGE_TYPES={"alternative_explanation","counterevidence","methodological","statistical","causal","uncertainty","reproducibility","scope","reviewer","other"}
CHALLENGE_STATUSES={"open","responded","resolved_by_author","unresolved","withdrawn","archived"}
FORBIDDEN={"classify_automatically_by_core","generate_inferences_by_core","infer_findings_by_core","infer_claims_by_core","infer_causality_by_core","compute_statistics_by_core","score_confidence_by_core","rank_evidence_by_core","resolve_contradictions_by_core","validate_inference_by_core","promote_speculation_by_core","determine_truth_by_core"}
CLASSES=[ResearchInferenceRecord,ResearchInferenceClassificationRecord,ResearchInferenceBasisRecord,ResearchInferenceAssumptionRecord,ResearchInferenceUncertaintyRecord,ResearchInferenceRelationRecord,ResearchInferenceChallengeRecord,ResearchInferenceRevisionRecord,ResearchInferenceSnapshotRecord]
COUNT_NAMES=["inferences","classifications","basis_bindings","assumptions","uncertainties","relations","challenges","revisions","snapshots"]
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
 if bad: raise ValueError("Core records researcher-declared inference semantics and provenance; it does not classify automatically, generate inferences/findings/claims, infer causality, compute statistics, score confidence, rank evidence, resolve contradictions, validate inferences, promote speculation, or determine truth: "+", ".join(bad))
def _get(db,i):
 r=db.get(ResearchInferenceRecord,i)
 if not r: raise ValueError("inference not found")
 return r
def boundaries(): return {"inference_registry_by_core":True,"existing_research_object_classification_by_core":True,"inference_basis_binding_by_core":True,"inference_assumption_registry_by_core":True,"inference_uncertainty_registry_by_core":True,"inference_relation_registry_by_core":True,"inference_challenge_registry_by_core":True,"inference_revision_history_by_core":True,"inference_lineage_by_core":True,"immutable_inference_snapshots_by_core":True,**{k:False for k in FORBIDDEN}}
def readiness(db):
 counts={n:db.scalar(select(func.count()).select_from(c)) or 0 for c,n in zip(CLASSES,COUNT_NAMES)}
 return {"release":"2.88.0","contract":CONTRACT,"inference_types":sorted(INFERENCE_TYPES),"basis_relations":sorted(BASIS_RELATIONS),"challenge_types":sorted(CHALLENGE_TYPES),"counts":counts,**boundaries()}
def create_inference(db,p):
 _reject(p); t=p.get("inference_type"); st=p.get("status","proposed"); vis=p.get("visibility","private")
 if t not in INFERENCE_TYPES: raise ValueError("unsupported inference_type")
 if st not in STATUSES or vis not in VISIBILITIES: raise ValueError("invalid status or visibility")
 if t=="causal_inference" and not str(p.get("method_ref") or "").strip(): raise ValueError("causal_inference requires a declared method_ref; Core does not determine whether the method establishes causality")
 r=ResearchInferenceRecord(inference_key=p["inference_key"],title=p["title"],statement_text=p["statement_text"],inference_type=t,status=st,visibility=vis,project_ref=p.get("project_ref"),protocol_ref=p.get("protocol_ref"),execution_ref=p.get("execution_ref"),method_ref=p.get("method_ref"),source_object_type=p.get("source_object_type"),source_object_ref=p.get("source_object_ref"),scope_json=p.get("scope",{}),confidence_declaration_json=p.get("confidence_declaration",{}),qualifications_json=p.get("qualifications",[]),provenance_json=p.get("provenance",{}),metadata_json=p.get("metadata",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def _add(db,i,p,cls,key,extra):
 _reject(p); _get(db,i); kw={"inference_id":i,key:p[key],"provenance_json":p.get("provenance",{}),"created_by":p.get("created_by","operator")}; kw.update(extra(p)); r=cls(**kw); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_classification(db,i,p):
 if p.get("object_type") not in OBJECT_TYPES: raise ValueError("unsupported object_type")
 if p.get("inference_type") not in INFERENCE_TYPES: raise ValueError("unsupported inference_type")
 return _add(db,i,p,ResearchInferenceClassificationRecord,"classification_key",lambda p:{"object_type":p["object_type"],"object_ref":p["object_ref"],"inference_type":p["inference_type"],"classification_basis":p.get("classification_basis"),"declared_by":p.get("declared_by")})
def add_basis(db,i,p):
 if p.get("basis_type") not in BASIS_TYPES: raise ValueError("unsupported basis_type")
 if p.get("relation") not in BASIS_RELATIONS: raise ValueError("unsupported basis relation")
 return _add(db,i,p,ResearchInferenceBasisRecord,"basis_key",lambda p:{"basis_type":p["basis_type"],"basis_ref":p["basis_ref"],"relation":p["relation"],"locator":p.get("locator"),"declared_strength":p.get("declared_strength"),"rationale":p.get("rationale")})
def add_assumption(db,i,p): return _add(db,i,p,ResearchInferenceAssumptionRecord,"assumption_key",lambda p:{"statement_text":p["statement_text"],"assumption_type":p.get("assumption_type","declared"),"source_ref":p.get("source_ref")})
def add_uncertainty(db,i,p): return _add(db,i,p,ResearchInferenceUncertaintyRecord,"uncertainty_key",lambda p:{"uncertainty_type":p["uncertainty_type"],"description":p["description"],"quantitative_json":p.get("quantitative",{}),"source_ref":p.get("source_ref")})
def add_relation(db,i,p):
 if p.get("relation") not in RELATIONS: raise ValueError("unsupported inference relation")
 if p.get("target_inference_ref")==i: raise ValueError("an inference cannot relate to itself")
 return _add(db,i,p,ResearchInferenceRelationRecord,"relation_key",lambda p:{"target_inference_ref":p["target_inference_ref"],"relation":p["relation"],"rationale":p.get("rationale")})
def add_challenge(db,i,p):
 if p.get("challenge_type") not in CHALLENGE_TYPES: raise ValueError("unsupported challenge_type")
 if p.get("status","open") not in CHALLENGE_STATUSES: raise ValueError("unsupported challenge status")
 return _add(db,i,p,ResearchInferenceChallengeRecord,"challenge_key",lambda p:{"challenge_type":p["challenge_type"],"statement_text":p["statement_text"],"status":p.get("status","open"),"evidence_refs_json":p.get("evidence_refs",[]),"raised_by":p.get("raised_by")})
def revise_inference(db,i,p):
 _reject(p); r=_get(db,i); prior=_ser(r); mapping={"title":"title","statement_text":"statement_text","inference_type":"inference_type","status":"status","visibility":"visibility","project_ref":"project_ref","protocol_ref":"protocol_ref","execution_ref":"execution_ref","method_ref":"method_ref","source_object_type":"source_object_type","source_object_ref":"source_object_ref","scope":"scope_json","confidence_declaration":"confidence_declaration_json","qualifications":"qualifications_json","metadata":"metadata_json"}
 if "inference_type" in p and p["inference_type"] not in INFERENCE_TYPES: raise ValueError("unsupported inference_type")
 if "status" in p and p["status"] not in STATUSES: raise ValueError("unsupported status")
 if "visibility" in p and p["visibility"] not in VISIBILITIES: raise ValueError("unsupported visibility")
 for k,a in mapping.items():
  if k in p: setattr(r,a,p[k])
 if r.inference_type=="causal_inference" and not str(r.method_ref or "").strip(): raise ValueError("causal_inference requires a declared method_ref")
 db.flush(); revised=_ser(r); rev=(db.scalar(select(func.max(ResearchInferenceRevisionRecord.revision)).where(ResearchInferenceRevisionRecord.inference_id==i)) or 0)+1; rr=ResearchInferenceRevisionRecord(inference_id=i,revision=rev,state_hash=_hash(revised),prior_state_json=prior,revised_state_json=revised,change_summary=p.get("change_summary"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(rr); db.commit(); db.refresh(rr); return _ser(rr)
def bundle(db,i,public=False):
 inf=_get(db,i)
 if public and inf.visibility!="public": raise ValueError("inference is not public")
 def rows(cls): return [_ser(x) for x in db.scalars(select(cls).where(cls.inference_id==i).order_by(cls.created_at)).all()]
 return {"inference":_ser(inf),"classifications":rows(ResearchInferenceClassificationRecord),"basis_bindings":rows(ResearchInferenceBasisRecord),"assumptions":rows(ResearchInferenceAssumptionRecord),"uncertainties":rows(ResearchInferenceUncertaintyRecord),"relations":rows(ResearchInferenceRelationRecord),"challenges":rows(ResearchInferenceChallengeRecord),"revisions":rows(ResearchInferenceRevisionRecord),"snapshots":rows(ResearchInferenceSnapshotRecord),**boundaries()}
def descriptive_summary(db,i,public=False):
 b=bundle(db,i,public); return {"inference":b["inference"],"counts":{k:len(b[k]) for k in ("classifications","basis_bindings","assumptions","uncertainties","relations","challenges","revisions","snapshots")},"basis_types":dict(Counter(x["basis_type"] for x in b["basis_bindings"])),"challenge_types":dict(Counter(x["challenge_type"] for x in b["challenges"])),"summary_is_descriptive_only":True,"confidence_is_researcher_declared_not_scored":True,**boundaries()}
def lineage(db,i,public=False):
 b=bundle(db,i,public); x="inference:"+i; edges=[]
 inf=b["inference"]
 if inf.get("source_object_type") and inf.get("source_object_ref"): edges.append({"from":inf["source_object_type"]+":"+inf["source_object_ref"],"to":x,"relation":"classified_or_interpreted_as"})
 if inf.get("execution_ref"): edges.append({"from":"execution:"+inf["execution_ref"],"to":x,"relation":"execution_context"})
 if inf.get("protocol_ref"): edges.append({"from":"protocol:"+inf["protocol_ref"],"to":x,"relation":"protocol_context"})
 edges += [{"from":r["basis_type"]+":"+r["basis_ref"],"to":x,"relation":r["relation"]} for r in b["basis_bindings"]]
 edges += [{"from":x,"to":"inference:"+r["target_inference_ref"],"relation":r["relation"]} for r in b["relations"]]
 edges += [{"from":r["object_type"]+":"+r["object_ref"],"to":x,"relation":"declared_classification","inference_type":r["inference_type"]} for r in b["classifications"]]
 return {"inference_id":i,"edges":edges,"edge_count":len(edges),"lineage_is_declared_not_inferred":True,**boundaries()}
def snapshot(db,i,p):
 _reject(p); state=bundle(db,i,False); state.pop("snapshots",None); prior=db.scalar(select(ResearchInferenceSnapshotRecord).where(ResearchInferenceSnapshotRecord.inference_id==i).order_by(ResearchInferenceSnapshotRecord.revision.desc()).limit(1)); rev=(prior.revision if prior else 0)+1; r=ResearchInferenceSnapshotRecord(inference_id=i,revision=rev,content_hash=_hash(state),previous_snapshot_hash=prior.content_hash if prior else None,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
