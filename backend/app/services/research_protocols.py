from __future__ import annotations
from collections import Counter
from datetime import datetime
import hashlib,json
from sqlalchemy import func,select
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (ScientificResearchProtocolRecord,ScientificProtocolObjectiveRecord,ScientificProtocolScopeUnitRecord,ScientificProtocolMeasureRecord,ScientificProtocolSourcePlanRecord,ScientificProtocolAcquisitionPlanRecord,ScientificProtocolMethodPlanRecord,ScientificProtocolAssumptionRecord,ScientificProtocolValidationPlanRecord,ScientificProtocolOutputPlanRecord,ScientificProtocolDeviationRecord,ScientificProtocolRevisionRecord,ScientificProtocolSnapshotRecord)
CONTRACT="sc.research.scientific-study-investigation-protocol.v1"
STUDY_TYPES={"experimental","observational","engineering_investigation","forensic_investigation","literature_review","systematic_review","mixed_method","simulation","case_study","other"}
STATUSES={"draft","registered","active","amended","completed","withdrawn","archived"}; VISIBILITIES={"private","internal","public"}
SCOPE_TYPES={"population","system","case","site","sample","document_corpus","dataset","jurisdiction","time_window","other"}
MEASURE_TYPES={"variable","outcome","exposure","intervention","covariate","confounder","parameter","measurement","indicator","other"}
INFERENCE_TYPES={"observation","descriptive","statistical","causal","predictive","interpretive","qualitative","forensic_reconstruction","engineering_analysis","none"}
FORBIDDEN={"execute_protocol_by_core","recruit_participants_by_core","randomize_by_core","collect_data_by_core","acquire_evidence_by_core","run_analysis_by_core","compute_results_by_core","infer_results_by_core","infer_causality_by_core","judge_method_quality_by_core","certify_ethics_by_core","approve_protocol_by_core","infer_truth_by_core"}
CLASSES=[ScientificResearchProtocolRecord,ScientificProtocolObjectiveRecord,ScientificProtocolScopeUnitRecord,ScientificProtocolMeasureRecord,ScientificProtocolSourcePlanRecord,ScientificProtocolAcquisitionPlanRecord,ScientificProtocolMethodPlanRecord,ScientificProtocolAssumptionRecord,ScientificProtocolValidationPlanRecord,ScientificProtocolOutputPlanRecord,ScientificProtocolDeviationRecord,ScientificProtocolRevisionRecord,ScientificProtocolSnapshotRecord]
COUNT_NAMES=["protocols","objectives","scope_units","measures","source_plans","acquisition_plans","method_plans","assumptions","validation_plans","output_plans","deviations","revisions","snapshots"]
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
 if bad: raise ValueError("Core records declared scientific/investigative protocols; it does not execute studies, recruit/randomize, collect data or evidence, run analyses, infer results/causality/truth, judge method quality, certify ethics, or approve protocols: "+", ".join(bad))
def _get(db,id):
 r=db.get(ScientificResearchProtocolRecord,id)
 if not r: raise ValueError("protocol not found")
 return r
def boundaries():
 return {"universal_protocol_registry_by_core":True,"protocol_objective_registry_by_core":True,"population_system_case_scope_registry_by_core":True,"variable_measure_registry_by_core":True,"source_data_plan_registry_by_core":True,"sampling_acquisition_plan_registry_by_core":True,"analytical_method_plan_registry_by_core":True,"assumption_registry_by_core":True,"validation_challenge_plan_registry_by_core":True,"planned_output_registry_by_core":True,"protocol_deviation_registry_by_core":True,"protocol_revision_history_by_core":True,"protocol_lineage_by_core":True,"immutable_protocol_snapshots_by_core":True,**{k:False for k in FORBIDDEN}}
def readiness(db):
 counts={n:db.scalar(select(func.count()).select_from(c)) or 0 for c,n in zip(CLASSES,COUNT_NAMES)}
 return {"release":"2.86.0","contract":CONTRACT,"study_types":sorted(STUDY_TYPES),"inference_types":sorted(INFERENCE_TYPES),"counts":counts,**boundaries()}
def create_protocol(db,p):
 _reject(p); st=p.get("study_type");
 if st not in STUDY_TYPES: raise ValueError("unsupported study_type")
 if p.get("status","draft") not in STATUSES or p.get("visibility","private") not in VISIBILITIES: raise ValueError("invalid status or visibility")
 r=ScientificResearchProtocolRecord(protocol_key=p["protocol_key"],title=p["title"],study_type=st,status=p.get("status","draft"),visibility=p.get("visibility","private"),project_ref=p.get("project_ref"),research_question_text=p.get("research_question_text"),protocol_version=p.get("protocol_version","1.0"),preregistration_uri=p.get("preregistration_uri"),rationale_text=p.get("rationale_text"),scope_json=p.get("scope",{}),ethics_governance_json=p.get("ethics_governance",{}),reproducibility_requirements_json=p.get("reproducibility_requirements",[]),provenance_json=p.get("provenance",{}),metadata_json=p.get("metadata",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def _add(db,protocol_id,p,cls,key_field,extra):
 _reject(p); _get(db,protocol_id); kwargs={"protocol_id":protocol_id,key_field:p[key_field],"provenance_json":p.get("provenance",{}),"created_by":p.get("created_by","operator")}; kwargs.update(extra(p)); r=cls(**kwargs); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_objective(db,i,p): return _add(db,i,p,ScientificProtocolObjectiveRecord,"objective_key",lambda p:{"objective_type":p.get("objective_type","primary"),"statement_text":p["statement_text"],"hypothesis_or_question_ref":p.get("hypothesis_or_question_ref"),"success_criteria_json":p.get("success_criteria",[])})
def add_scope(db,i,p):
 if p.get("scope_type") not in SCOPE_TYPES: raise ValueError("unsupported scope_type")
 return _add(db,i,p,ScientificProtocolScopeUnitRecord,"scope_key",lambda p:{"scope_type":p["scope_type"],"label":p["label"],"inclusion_criteria_json":p.get("inclusion_criteria",[]),"exclusion_criteria_json":p.get("exclusion_criteria",[]),"boundary_json":p.get("boundary",{})})
def add_measure(db,i,p):
 if p.get("measure_type") not in MEASURE_TYPES: raise ValueError("unsupported measure_type")
 return _add(db,i,p,ScientificProtocolMeasureRecord,"measure_key",lambda p:{"measure_type":p["measure_type"],"name":p["name"],"operational_definition_text":p.get("operational_definition_text"),"unit":p.get("unit"),"role":p.get("role"),"measurement_plan_json":p.get("measurement_plan",{})})
def add_source(db,i,p): return _add(db,i,p,ScientificProtocolSourcePlanRecord,"source_key",lambda p:{"source_type":p["source_type"],"source_ref":p.get("source_ref"),"version_or_date":p.get("version_or_date"),"access_plan_text":p.get("access_plan_text"),"selection_criteria_json":p.get("selection_criteria",[])})
def add_acquisition(db,i,p): return _add(db,i,p,ScientificProtocolAcquisitionPlanRecord,"acquisition_key",lambda p:{"acquisition_type":p["acquisition_type"],"procedure_text":p["procedure_text"],"sampling_strategy_json":p.get("sampling_strategy",{}),"timing_json":p.get("timing",{}),"quality_controls_json":p.get("quality_controls",[])})
def add_method(db,i,p):
 it=p.get("planned_inference_type")
 if it is not None and it not in INFERENCE_TYPES: raise ValueError("unsupported planned_inference_type")
 return _add(db,i,p,ScientificProtocolMethodPlanRecord,"method_key",lambda p:{"method_type":p["method_type"],"method_ref":p.get("method_ref"),"procedure_text":p.get("procedure_text"),"parameters_json":p.get("parameters",{}),"software_environment_json":p.get("software_environment",{}),"planned_inference_type":p.get("planned_inference_type")})
def add_assumption(db,i,p): return _add(db,i,p,ScientificProtocolAssumptionRecord,"assumption_key",lambda p:{"assumption_type":p.get("assumption_type","methodological"),"statement_text":p["statement_text"],"sensitivity_plan_text":p.get("sensitivity_plan_text"),"evidence_refs_json":p.get("evidence_refs",[])})
def add_validation(db,i,p): return _add(db,i,p,ScientificProtocolValidationPlanRecord,"validation_key",lambda p:{"validation_type":p["validation_type"],"procedure_text":p["procedure_text"],"acceptance_criteria_json":p.get("acceptance_criteria",[]),"challenge_refs_json":p.get("challenge_refs",[])})
def add_output(db,i,p): return _add(db,i,p,ScientificProtocolOutputPlanRecord,"output_key",lambda p:{"output_type":p["output_type"],"label":p["label"],"target_ref":p.get("target_ref"),"requirements_json":p.get("requirements",[])})
def add_deviation(db,i,p): return _add(db,i,p,ScientificProtocolDeviationRecord,"deviation_key",lambda p:{"occurred_at":p.get("occurred_at"),"deviation_type":p.get("deviation_type","protocol_change"),"description_text":p["description_text"],"rationale_text":p.get("rationale_text"),"affected_refs_json":p.get("affected_refs",[]),"impact_assessment_text":p.get("impact_assessment_text")})
def revise_protocol(db,i,p):
 _reject(p); r=_get(db,i); prior=_ser(r); allowed={"title":"title","status":"status","visibility":"visibility","research_question_text":"research_question_text","protocol_version":"protocol_version","preregistration_uri":"preregistration_uri","rationale_text":"rationale_text","scope":"scope_json","ethics_governance":"ethics_governance_json","reproducibility_requirements":"reproducibility_requirements_json","metadata":"metadata_json"}
 for k,a in allowed.items():
  if k in p: setattr(r,a,p[k])
 db.flush(); revised=_ser(r); rev=(db.scalar(select(func.max(ScientificProtocolRevisionRecord.revision)).where(ScientificProtocolRevisionRecord.protocol_id==i)) or 0)+1; h=_hash(revised); rr=ScientificProtocolRevisionRecord(protocol_id=i,revision=rev,state_hash=h,prior_state_json=prior,revised_state_json=revised,change_summary=p.get("change_summary"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(rr); db.commit(); db.refresh(rr); return _ser(rr)
def bundle(db,i,public=False):
 p=_get(db,i)
 if public and p.visibility!="public": raise ValueError("protocol is not public")
 def rows(cls): return [_ser(x) for x in db.scalars(select(cls).where(cls.protocol_id==i).order_by(cls.created_at)).all()]
 out={"protocol":_ser(p),"objectives":rows(ScientificProtocolObjectiveRecord),"scope_units":rows(ScientificProtocolScopeUnitRecord),"measures":rows(ScientificProtocolMeasureRecord),"source_plans":rows(ScientificProtocolSourcePlanRecord),"acquisition_plans":rows(ScientificProtocolAcquisitionPlanRecord),"method_plans":rows(ScientificProtocolMethodPlanRecord),"assumptions":rows(ScientificProtocolAssumptionRecord),"validation_plans":rows(ScientificProtocolValidationPlanRecord),"output_plans":rows(ScientificProtocolOutputPlanRecord),"deviations":rows(ScientificProtocolDeviationRecord),"revisions":rows(ScientificProtocolRevisionRecord),"snapshots":rows(ScientificProtocolSnapshotRecord),**boundaries()}
 return out
def descriptive_summary(db,i,public=False):
 b=bundle(db,i,public); return {"protocol":b["protocol"],"counts":{k:len(b[k]) for k in ("objectives","scope_units","measures","source_plans","acquisition_plans","method_plans","assumptions","validation_plans","output_plans","deviations","revisions","snapshots")},"method_types":dict(Counter(x["method_type"] for x in b["method_plans"])),"planned_inference_types":dict(Counter(x["planned_inference_type"] for x in b["method_plans"] if x.get("planned_inference_type"))),"summary_is_descriptive_only":True,**boundaries()}
def lineage(db,i,public=False):
 b=bundle(db,i,public); pid=i; edges=[]
 for name,key in (("objectives","id"),("scope_units","id"),("measures","id"),("source_plans","id"),("acquisition_plans","id"),("method_plans","id"),("assumptions","id"),("validation_plans","id"),("output_plans","id"),("deviations","id")):
  edges += [{"from":"protocol:"+pid,"to":name[:-1]+":"+x[key],"relation":"declares"} for x in b[name]]
 return {"protocol_id":pid,"edges":edges,"edge_count":len(edges),"lineage_is_declared_not_inferred":True,**boundaries()}
def snapshot(db,i,p):
 _reject(p); state=bundle(db,i,False); state.pop("snapshots",None); prior=db.scalar(select(ScientificProtocolSnapshotRecord).where(ScientificProtocolSnapshotRecord.protocol_id==i).order_by(ScientificProtocolSnapshotRecord.revision.desc()).limit(1)); rev=(prior.revision if prior else 0)+1; h=_hash(state); r=ScientificProtocolSnapshotRecord(protocol_id=i,revision=rev,content_hash=h,previous_snapshot_hash=prior.content_hash if prior else None,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
