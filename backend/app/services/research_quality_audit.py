from __future__ import annotations
from collections import Counter
from datetime import datetime
import hashlib,json
from sqlalchemy import func,select
from sqlalchemy.inspection import inspect as sa_inspect
from ..models import (
 ResearchQualityAuditRecord,ResearchQualityAuditSubjectRecord,ResearchQualityAuditCheckRecord,
 ResearchQualityAuditFindingRecord,ResearchQualityAuditEvidenceRecord,ResearchQualityBiasAssessmentRecord,
 ResearchQualityMethodAssessmentRecord,ResearchQualityAuditResponseRecord,ResearchQualityAuditRevisionRecord,ResearchQualityAuditSnapshotRecord,
)
CONTRACT="sc.research.quality-bias-methodological-audit.v1"
STATUSES={"planned","in_progress","completed","reopened","archived"}
VISIBILITIES={"private","internal","public"}
OBJECT_TYPES={"project","protocol","execution","dataset","source","evidence","finding","claim","inference","hypothesis","argument","conclusion","publication","replication","synthesis","model","method","notebook","other"}
CHECK_TYPES={"confounding","selection_bias","measurement_bias","missing_data","unsupported_causal_claim","statistical_method","multiple_testing","uncertainty","sensitivity_robustness","citation_support","evidence_traceability","contradictory_finding","protocol_deviation","reproducibility","software_environment","data_versioning","sampling","model_specification","external_validity","publication_bias","other"}
CHECK_STATUSES={"not_assessed","satisfied","concern","indeterminate","not_applicable"}
FINDING_TYPES={"concern","gap","strength","observation"}
FINDING_STATUSES={"open","addressed","accepted","contested","resolved","withdrawn","archived"}
CONCERN_LEVELS={"none","low","medium","high","unknown"}
BIAS_TYPES={"confounding","selection","measurement","information","attrition","reporting","publication","observer","model","sampling","missing_data","other"}
ASSESSMENT_STATUSES=CHECK_STATUSES
EVIDENCE_TYPES={"source","evidence","dataset","protocol","execution","output","finding","claim","inference","publication","replication","synthesis","review","other"}
EVIDENCE_RELATIONS={"supports","contradicts","documents","qualifies","contextualizes","demonstrates_gap","responds_to"}
METHOD_ASSESSMENT_TYPES={"design","sampling","measurement","statistical","causal","predictive","computational","sensitivity","uncertainty","reproducibility","citation","other"}
RESPONSE_TYPES={"clarification","correction","additional_analysis","sensitivity_analysis","additional_evidence","protocol_amendment","citation_update","accepted_limitation","rebuttal","other"}
RESPONSE_STATUSES={"recorded","planned","in_progress","completed","declined","superseded","archived"}
FORBIDDEN={"infer_bias_by_core","score_research_quality_by_core","rank_studies_by_core","determine_method_validity_by_core","infer_confounding_by_core","determine_causal_validity_by_core","resolve_contradictions_by_core","verify_citation_support_by_core","certify_reproducibility_by_core","certify_ethics_by_core","reject_research_by_core","determine_truth_by_core"}
CLASSES=[ResearchQualityAuditRecord,ResearchQualityAuditSubjectRecord,ResearchQualityAuditCheckRecord,ResearchQualityAuditFindingRecord,ResearchQualityAuditEvidenceRecord,ResearchQualityBiasAssessmentRecord,ResearchQualityMethodAssessmentRecord,ResearchQualityAuditResponseRecord,ResearchQualityAuditRevisionRecord,ResearchQualityAuditSnapshotRecord]
COUNT_NAMES=["audits","subjects","checks","findings","evidence_bindings","bias_assessments","method_assessments","responses","revisions","snapshots"]
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
 if bad: raise ValueError("Core records declared/external methodological-audit evidence and responses; it does not infer bias/confounding, score quality, rank studies, determine method or causal validity, resolve contradictions, verify citation support, certify reproducibility/ethics, reject research, or determine truth: "+", ".join(bad))
def _get(db,i):
 r=db.get(ResearchQualityAuditRecord,i)
 if not r: raise ValueError("research quality audit not found")
 return r
def boundaries(): return {"quality_audit_registry_by_core":True,"audit_subject_registry_by_core":True,"systematic_audit_check_registry_by_core":True,"audit_finding_registry_by_core":True,"audit_evidence_binding_by_core":True,"declared_bias_assessment_registry_by_core":True,"method_assessment_registry_by_core":True,"audit_response_registry_by_core":True,"audit_coverage_summary_by_core":True,"audit_revision_history_by_core":True,"audit_lineage_by_core":True,"immutable_audit_snapshots_by_core":True,**{k:False for k in FORBIDDEN}}
def readiness(db):
 counts={n:db.scalar(select(func.count()).select_from(c)) or 0 for c,n in zip(CLASSES,COUNT_NAMES)}
 return {"release":"2.89.0","contract":CONTRACT,"check_types":sorted(CHECK_TYPES),"bias_types":sorted(BIAS_TYPES),"method_assessment_types":sorted(METHOD_ASSESSMENT_TYPES),"counts":counts,**boundaries()}
def create_audit(db,p):
 _reject(p); st=p.get("status","planned"); vis=p.get("visibility","private")
 if st not in STATUSES or vis not in VISIBILITIES: raise ValueError("invalid audit status or visibility")
 r=ResearchQualityAuditRecord(audit_key=p["audit_key"],title=p["title"],status=st,visibility=vis,project_ref=p.get("project_ref"),protocol_ref=p.get("protocol_ref"),execution_ref=p.get("execution_ref"),inference_ref=p.get("inference_ref"),publication_ref=p.get("publication_ref"),assessment_framework=p.get("assessment_framework"),auditor_ref=p.get("auditor_ref"),scope_json=p.get("scope",{}),provenance_json=p.get("provenance",{}),metadata_json=p.get("metadata",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def _add(db,i,p,cls,key,extra):
 _reject(p); _get(db,i); kw={"audit_id":i,key:p[key],"provenance_json":p.get("provenance",{}),"created_by":p.get("created_by","operator")}; kw.update(extra(p)); r=cls(**kw); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_subject(db,i,p):
 if p.get("object_type") not in OBJECT_TYPES: raise ValueError("unsupported audit subject object_type")
 return _add(db,i,p,ResearchQualityAuditSubjectRecord,"subject_key",lambda p:{"object_type":p["object_type"],"object_ref":p["object_ref"],"role":p.get("role"),"rationale":p.get("rationale")})
def add_check(db,i,p):
 if p.get("check_type") not in CHECK_TYPES: raise ValueError("unsupported check_type")
 if p.get("status","not_assessed") not in CHECK_STATUSES: raise ValueError("unsupported check status")
 return _add(db,i,p,ResearchQualityAuditCheckRecord,"check_key",lambda p:{"check_type":p["check_type"],"status":p.get("status","not_assessed"),"statement_text":p["statement_text"],"assessment_method":p.get("assessment_method"),"affected_object_ref":p.get("affected_object_ref"),"result_details_json":p.get("result_details",{}),"declared_by":p.get("declared_by")})
def add_finding(db,i,p):
 if p.get("category") not in CHECK_TYPES: raise ValueError("unsupported audit finding category")
 if p.get("finding_type","concern") not in FINDING_TYPES: raise ValueError("unsupported audit finding type")
 if p.get("status","open") not in FINDING_STATUSES: raise ValueError("unsupported audit finding status")
 if p.get("declared_concern_level") not in (None,*CONCERN_LEVELS): raise ValueError("unsupported declared concern level")
 return _add(db,i,p,ResearchQualityAuditFindingRecord,"finding_key",lambda p:{"category":p["category"],"finding_type":p.get("finding_type","concern"),"status":p.get("status","open"),"statement_text":p["statement_text"],"affected_object_type":p.get("affected_object_type"),"affected_object_ref":p.get("affected_object_ref"),"declared_concern_level":p.get("declared_concern_level"),"rationale":p.get("rationale")})
def add_evidence(db,i,p):
 if p.get("evidence_type") not in EVIDENCE_TYPES: raise ValueError("unsupported audit evidence_type")
 if p.get("relation") not in EVIDENCE_RELATIONS: raise ValueError("unsupported audit evidence relation")
 return _add(db,i,p,ResearchQualityAuditEvidenceRecord,"evidence_key",lambda p:{"finding_ref":p.get("finding_ref"),"evidence_type":p["evidence_type"],"evidence_ref":p["evidence_ref"],"relation":p["relation"],"locator":p.get("locator"),"rationale":p.get("rationale")})
def add_bias_assessment(db,i,p):
 if p.get("bias_type") not in BIAS_TYPES: raise ValueError("unsupported bias_type")
 if p.get("status","not_assessed") not in ASSESSMENT_STATUSES: raise ValueError("unsupported bias assessment status")
 return _add(db,i,p,ResearchQualityBiasAssessmentRecord,"bias_key",lambda p:{"bias_type":p["bias_type"],"status":p.get("status","not_assessed"),"statement_text":p["statement_text"],"direction":p.get("direction"),"affected_object_ref":p.get("affected_object_ref"),"mitigation_ref":p.get("mitigation_ref"),"residual_uncertainty":p.get("residual_uncertainty")})
def add_method_assessment(db,i,p):
 if p.get("assessment_type") not in METHOD_ASSESSMENT_TYPES: raise ValueError("unsupported method assessment_type")
 if p.get("status","not_assessed") not in ASSESSMENT_STATUSES: raise ValueError("unsupported method assessment status")
 return _add(db,i,p,ResearchQualityMethodAssessmentRecord,"method_assessment_key",lambda p:{"method_ref":p["method_ref"],"assessment_type":p["assessment_type"],"status":p.get("status","not_assessed"),"statement_text":p["statement_text"],"protocol_ref":p.get("protocol_ref"),"execution_ref":p.get("execution_ref"),"evidence_refs_json":p.get("evidence_refs",[])})
def add_response(db,i,p):
 if p.get("response_type") not in RESPONSE_TYPES: raise ValueError("unsupported response_type")
 if p.get("status","recorded") not in RESPONSE_STATUSES: raise ValueError("unsupported response status")
 return _add(db,i,p,ResearchQualityAuditResponseRecord,"response_key",lambda p:{"finding_ref":p.get("finding_ref"),"response_type":p["response_type"],"status":p.get("status","recorded"),"statement_text":p["statement_text"],"evidence_refs_json":p.get("evidence_refs",[]),"responder_ref":p.get("responder_ref")})
def revise_audit(db,i,p):
 _reject(p); r=_get(db,i); prior=_ser(r); mapping={"title":"title","status":"status","visibility":"visibility","project_ref":"project_ref","protocol_ref":"protocol_ref","execution_ref":"execution_ref","inference_ref":"inference_ref","publication_ref":"publication_ref","assessment_framework":"assessment_framework","auditor_ref":"auditor_ref","scope":"scope_json","metadata":"metadata_json"}
 if "status" in p and p["status"] not in STATUSES: raise ValueError("unsupported audit status")
 if "visibility" in p and p["visibility"] not in VISIBILITIES: raise ValueError("unsupported visibility")
 for k,a in mapping.items():
  if k in p: setattr(r,a,p[k])
 db.flush(); revised=_ser(r); rev=(db.scalar(select(func.max(ResearchQualityAuditRevisionRecord.revision)).where(ResearchQualityAuditRevisionRecord.audit_id==i)) or 0)+1; rr=ResearchQualityAuditRevisionRecord(audit_id=i,revision=rev,state_hash=_hash(revised),prior_state_json=prior,revised_state_json=revised,change_summary=p.get("change_summary"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(rr); db.commit(); db.refresh(rr); return _ser(rr)
def bundle(db,i,public=False):
 a=_get(db,i)
 if public and a.visibility!="public": raise ValueError("audit is not public")
 def rows(cls): return [_ser(x) for x in db.scalars(select(cls).where(cls.audit_id==i).order_by(cls.created_at,cls.id)).all()]
 return {"audit":_ser(a),"subjects":rows(ResearchQualityAuditSubjectRecord),"checks":rows(ResearchQualityAuditCheckRecord),"findings":rows(ResearchQualityAuditFindingRecord),"evidence_bindings":rows(ResearchQualityAuditEvidenceRecord),"bias_assessments":rows(ResearchQualityBiasAssessmentRecord),"method_assessments":rows(ResearchQualityMethodAssessmentRecord),"responses":rows(ResearchQualityAuditResponseRecord),"revisions":rows(ResearchQualityAuditRevisionRecord),"snapshots":rows(ResearchQualityAuditSnapshotRecord),**boundaries()}
def descriptive_summary(db,i,public=False):
 b=bundle(db,i,public); a=b["audit"]; checks=Counter(x["check_type"] for x in b["checks"]); statuses=Counter(x["status"] for x in b["checks"]); cats=Counter(x["category"] for x in b["findings"]); biases=Counter(x["bias_type"] for x in b["bias_assessments"]); covered=set(checks); missing=sorted(CHECK_TYPES-covered-{"other"})
 return {"audit_id":i,"title":a["title"],"status":a["status"],"visibility":a["visibility"],"check_types":dict(sorted(checks.items())),"check_statuses":dict(sorted(statuses.items())),"finding_categories":dict(sorted(cats.items())),"bias_types":dict(sorted(biases.items())),"unrepresented_check_types":missing,"coverage_is_descriptive_not_a_quality_score":True,"assessments_are_declared_or_external_not_inferred_by_core":True,**boundaries()}
def lineage(db,i,public=False):
 b=bundle(db,i,public); a=b["audit"]; node="audit:"+i; edges=[]
 for field,typ in (("project_ref","project"),("protocol_ref","protocol"),("execution_ref","execution"),("inference_ref","inference"),("publication_ref","publication")):
  if a.get(field): edges.append({"from":typ+":"+a[field],"to":node,"relation":"audit_context"})
 edges += [{"from":s["object_type"]+":"+s["object_ref"],"to":node,"relation":s.get("role") or "audit_subject"} for s in b["subjects"]]
 edges += [{"from":e["evidence_type"]+":"+e["evidence_ref"],"to":node,"relation":e["relation"],"finding_ref":e.get("finding_ref")} for e in b["evidence_bindings"]]
 edges += [{"from":node,"to":"method:"+m["method_ref"],"relation":"assesses_method"} for m in b["method_assessments"]]
 return {"audit_id":i,"edges":edges,"edge_count":len(edges),"lineage_is_declared_not_inferred":True,**boundaries()}
def snapshot(db,i,p):
 _reject(p); state=bundle(db,i,False); state.pop("snapshots",None); prior=db.scalar(select(ResearchQualityAuditSnapshotRecord).where(ResearchQualityAuditSnapshotRecord.audit_id==i).order_by(ResearchQualityAuditSnapshotRecord.revision.desc()).limit(1)); rev=(prior.revision if prior else 0)+1; r=ResearchQualityAuditSnapshotRecord(audit_id=i,revision=rev,content_hash=_hash(state),previous_snapshot_hash=prior.content_hash if prior else None,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
