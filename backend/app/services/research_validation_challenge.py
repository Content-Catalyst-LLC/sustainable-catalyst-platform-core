from __future__ import annotations
from datetime import datetime
import hashlib, json
from sqlalchemy import func, select
from sqlalchemy.inspection import inspect as sa_inspect
from ..models import (
 ResearchValidationChallengeRecord,ResearchValidationTargetRecord,ResearchAlternativeHypothesisRecord,
 ResearchContradictionTestRecord,ResearchCounterevidenceRecord,ResearchSensitivityCheckRecord,
 ResearchRobustnessCheckRecord,ResearchReplicationAttemptV294Record,ResearchReviewerChallengeRecord,
 ResearchChallengeResponseRecord,ResearchValidationRevisionRecord,ResearchValidationSnapshotRecord,
)
CONTRACT="sc.research.validation-challenge.v1"
CHALLENGE_TYPES={"alternative_hypothesis","contradiction","counterevidence","sensitivity","robustness","replication","reviewer_challenge","methodological_challenge","uncertainty_challenge","other"}
VISIBILITIES={"private","internal","public"}
STATUSES={"open","recorded","responded","revised","closed","withdrawn"}
FORBIDDEN={"resolve_hypotheses_by_core","rank_hypotheses_by_core","declare_winner_by_core","certify_validity_by_core","certify_replication_by_core","infer_contradiction_by_core","infer_counterevidence_by_core","execute_sensitivity_by_core","execute_robustness_by_core","execute_replication_by_core","dismiss_challenges_by_core","determine_truth_by_core"}
CLASSES=[ResearchValidationChallengeRecord,ResearchValidationTargetRecord,ResearchAlternativeHypothesisRecord,ResearchContradictionTestRecord,ResearchCounterevidenceRecord,ResearchSensitivityCheckRecord,ResearchRobustnessCheckRecord,ResearchReplicationAttemptV294Record,ResearchReviewerChallengeRecord,ResearchChallengeResponseRecord,ResearchValidationRevisionRecord,ResearchValidationSnapshotRecord]
COUNT_NAMES=["challenges","targets","alternative_hypotheses","contradiction_tests","counterevidence","sensitivity_checks","robustness_checks","replication_attempts","reviewer_challenges","responses","revisions","snapshots"]
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
 if bad: raise ValueError("Core records declared challenges and adversarial evidence; it does not resolve or rank hypotheses, certify validity or replication, infer contradictions/counterevidence, execute tests, dismiss challenges, or determine truth: "+", ".join(bad))
def boundaries(): return {"validation_challenge_registry_by_core":True,"target_binding_registry_by_core":True,"alternative_hypothesis_registry_by_core":True,"contradiction_test_registry_by_core":True,"counterevidence_registry_by_core":True,"sensitivity_check_registry_by_core":True,"robustness_check_registry_by_core":True,"replication_attempt_registry_by_core":True,"reviewer_challenge_registry_by_core":True,"challenge_response_registry_by_core":True,"revision_history_by_core":True,"immutable_validation_snapshots_by_core":True,"challenge_state_is_declared_not_core_decided":True,**{k:False for k in FORBIDDEN}}
def readiness(db):
 counts={n:db.scalar(select(func.count()).select_from(c)) or 0 for c,n in zip(CLASSES,COUNT_NAMES)}
 return {"release":"2.94.0","contract":CONTRACT,"challenge_types":sorted(CHALLENGE_TYPES),"counts":counts,"migration_0098_applied":True,**boundaries()}
def _get(db,cls,i,label):
 r=db.get(cls,i)
 if not r: raise ValueError(label+" not found")
 return r
def _rows(db,cls,project): return [_ser(x) for x in db.scalars(select(cls).where(cls.project_ref==project).order_by(cls.created_at,cls.id)).all()]
def create_challenge(db,p):
 _reject(p); typ=p.get("challenge_type","other"); vis=p.get("visibility","internal"); status=p.get("status","open")
 if typ not in CHALLENGE_TYPES or vis not in VISIBILITIES or status not in STATUSES: raise ValueError("unsupported challenge type/visibility/status")
 r=ResearchValidationChallengeRecord(challenge_key=p["challenge_key"],project_ref=p["project_ref"],challenge_type=typ,title=p["title"],description=p.get("description"),status=status,source_ref=p.get("source_ref"),raised_by_ref=p.get("raised_by_ref"),visibility=vis,metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def bind_target(db,p):
 _reject(p); _get(db,ResearchValidationChallengeRecord,p["challenge_id"],"challenge"); vis=p.get("visibility","internal")
 if vis not in VISIBILITIES: raise ValueError("unsupported visibility")
 r=ResearchValidationTargetRecord(target_key=p["target_key"],challenge_id=p["challenge_id"],project_ref=p["project_ref"],target_type=p["target_type"],target_ref=p["target_ref"],target_version_ref=p.get("target_version_ref"),relation=p.get("relation","challenges"),visibility=vis,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_alternative_hypothesis(db,p):
 _reject(p); _get(db,ResearchValidationChallengeRecord,p["challenge_id"],"challenge"); vis=p.get("visibility","internal")
 if vis not in VISIBILITIES: raise ValueError("unsupported visibility")
 r=ResearchAlternativeHypothesisRecord(hypothesis_key=p["hypothesis_key"],challenge_id=p["challenge_id"],project_ref=p["project_ref"],existing_hypothesis_ref=p.get("existing_hypothesis_ref"),statement=p["statement"],rationale=p.get("rationale"),distinguishing_evidence_json=p.get("distinguishing_evidence",[]),status=p.get("status","declared"),visibility=vis,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def record_contradiction_test(db,p):
 _reject(p); _get(db,ResearchValidationChallengeRecord,p["challenge_id"],"challenge")
 r=ResearchContradictionTestRecord(test_key=p["test_key"],challenge_id=p["challenge_id"],project_ref=p["project_ref"],assertion_a_ref=p["assertion_a_ref"],assertion_b_ref=p["assertion_b_ref"],test_method_ref=p.get("test_method_ref"),result_status=p.get("result_status","recorded"),evidence_json=p.get("evidence",[]),notes=p.get("notes"),visibility=p.get("visibility","internal"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def record_counterevidence(db,p):
 _reject(p); _get(db,ResearchValidationChallengeRecord,p["challenge_id"],"challenge")
 r=ResearchCounterevidenceRecord(counterevidence_key=p["counterevidence_key"],challenge_id=p["challenge_id"],project_ref=p["project_ref"],evidence_ref=p["evidence_ref"],challenges_ref=p["challenges_ref"],relationship=p.get("relationship","counterevidence"),statement=p.get("statement"),visibility=p.get("visibility","internal"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def record_sensitivity_check(db,p):
 _reject(p); _get(db,ResearchValidationChallengeRecord,p["challenge_id"],"challenge")
 r=ResearchSensitivityCheckRecord(check_key=p["check_key"],challenge_id=p["challenge_id"],project_ref=p["project_ref"],target_ref=p["target_ref"],factor_ref=p.get("factor_ref"),method_ref=p.get("method_ref"),execution_ref=p.get("execution_ref"),result_ref=p.get("result_ref"),outcome=p.get("outcome","recorded"),evidence_json=p.get("evidence",[]),visibility=p.get("visibility","internal"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def record_robustness_check(db,p):
 _reject(p); _get(db,ResearchValidationChallengeRecord,p["challenge_id"],"challenge")
 r=ResearchRobustnessCheckRecord(check_key=p["check_key"],challenge_id=p["challenge_id"],project_ref=p["project_ref"],target_ref=p["target_ref"],variant_type=p["variant_type"],method_ref=p.get("method_ref"),execution_ref=p.get("execution_ref"),result_ref=p.get("result_ref"),outcome=p.get("outcome","recorded"),evidence_json=p.get("evidence",[]),visibility=p.get("visibility","internal"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def record_replication_attempt(db,p):
 _reject(p); _get(db,ResearchValidationChallengeRecord,p["challenge_id"],"challenge")
 r=ResearchReplicationAttemptV294Record(attempt_key=p["attempt_key"],challenge_id=p["challenge_id"],project_ref=p["project_ref"],target_ref=p["target_ref"],protocol_ref=p.get("protocol_ref"),execution_ref=p.get("execution_ref"),package_ref=p.get("package_ref"),result_status=p.get("result_status","recorded"),evidence_json=p.get("evidence",[]),visibility=p.get("visibility","internal"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def record_reviewer_challenge(db,p):
 _reject(p); _get(db,ResearchValidationChallengeRecord,p["challenge_id"],"challenge")
 r=ResearchReviewerChallengeRecord(review_challenge_key=p["review_challenge_key"],challenge_id=p["challenge_id"],project_ref=p["project_ref"],reviewer_ref=p["reviewer_ref"],review_ref=p.get("review_ref"),target_ref=p["target_ref"],challenge_statement=p["challenge_statement"],severity_label=p.get("severity_label"),status=p.get("status","open"),visibility=p.get("visibility","internal"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def respond(db,p):
 _reject(p); _get(db,ResearchValidationChallengeRecord,p["challenge_id"],"challenge")
 r=ResearchChallengeResponseRecord(response_key=p["response_key"],challenge_id=p["challenge_id"],project_ref=p["project_ref"],responder_ref=p["responder_ref"],response_type=p.get("response_type","response"),statement=p["statement"],evidence_json=p.get("evidence",[]),revised_object_ref=p.get("revised_object_ref"),status=p.get("status","recorded"),visibility=p.get("visibility","internal"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def revise(db,p):
 _reject(p); project=p["project_ref"]; n=(db.scalar(select(func.max(ResearchValidationRevisionRecord.revision)).where(ResearchValidationRevisionRecord.project_ref==project)) or 0)+1
 if p.get("challenge_id"): _get(db,ResearchValidationChallengeRecord,p["challenge_id"],"challenge")
 r=ResearchValidationRevisionRecord(project_ref=project,revision=n,challenge_id=p.get("challenge_id"),change_type=p.get("change_type","challenge_revision"),prior_state_json=p.get("prior_state",{}),revised_state_json=p.get("revised_state",{}),change_summary=p.get("change_summary"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def _bundle(db,project,public=False):
 data={"project_ref":project,"challenges":_rows(db,ResearchValidationChallengeRecord,project),"targets":_rows(db,ResearchValidationTargetRecord,project),"alternative_hypotheses":_rows(db,ResearchAlternativeHypothesisRecord,project),"contradiction_tests":_rows(db,ResearchContradictionTestRecord,project),"counterevidence":_rows(db,ResearchCounterevidenceRecord,project),"sensitivity_checks":_rows(db,ResearchSensitivityCheckRecord,project),"robustness_checks":_rows(db,ResearchRobustnessCheckRecord,project),"replication_attempts":_rows(db,ResearchReplicationAttemptV294Record,project),"reviewer_challenges":_rows(db,ResearchReviewerChallengeRecord,project),"responses":_rows(db,ResearchChallengeResponseRecord,project),"revisions":_rows(db,ResearchValidationRevisionRecord,project),"snapshots":_rows(db,ResearchValidationSnapshotRecord,project)}
 if public:
  for k in list(data):
   if isinstance(data[k],list): data[k]=[x for x in data[k] if x.get("visibility")=="public"] if k not in {"revisions","snapshots"} else []
  allowed={x["id"] for x in data["challenges"]}
  for k in ("targets","alternative_hypotheses","contradiction_tests","counterevidence","sensitivity_checks","robustness_checks","replication_attempts","reviewer_challenges","responses"): data[k]=[x for x in data[k] if x.get("challenge_id") in allowed]
 return data
def snapshot(db,p):
 _reject(p); project=p["project_ref"]; state=_bundle(db,project,False); state["snapshots"]=[]; n=(db.scalar(select(func.max(ResearchValidationSnapshotRecord.revision)).where(ResearchValidationSnapshotRecord.project_ref==project)) or 0)+1; prev=db.scalar(select(ResearchValidationSnapshotRecord).where(ResearchValidationSnapshotRecord.project_ref==project).order_by(ResearchValidationSnapshotRecord.revision.desc()).limit(1)); r=ResearchValidationSnapshotRecord(project_ref=project,revision=n,content_hash=_hash(state),previous_snapshot_hash=prev.content_hash if prev else None,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def descriptive_summary(db,project,public=False):
 b=_bundle(db,project,public); return {"release":"2.94.0","contract":CONTRACT,"project_ref":project,"counts":{k:len(v) for k,v in b.items() if isinstance(v,list)},"summary_is_descriptive_not_validation_verdict":True,**boundaries()}
def lineage(db,project,public=False):
 b=_bundle(db,project,public); nodes=[]; edges=[]
 for c in b["challenges"]: nodes.append({"id":"challenge:"+c["id"],"type":"challenge","challenge_type":c["challenge_type"],"title":c["title"]})
 for t in b["targets"]: nodes.append({"id":"target:"+t["id"],"type":"target","target_ref":t["target_ref"]}); edges.append({"from":"challenge:"+t["challenge_id"],"to":"target:"+t["id"],"relation":t["relation"]})
 for h in b["alternative_hypotheses"]: nodes.append({"id":"alternative:"+h["id"],"type":"alternative_hypothesis"}); edges.append({"from":"challenge:"+h["challenge_id"],"to":"alternative:"+h["id"],"relation":"declares_alternative"})
 for x in b["counterevidence"]: edges.append({"from":"challenge:"+x["challenge_id"],"to":x["evidence_ref"],"relation":"declared_counterevidence"})
 for x in b["responses"]: edges.append({"from":"challenge:"+x["challenge_id"],"to":"response:"+x["id"],"relation":"has_response"})
 return {"release":"2.94.0","contract":CONTRACT,"project_ref":project,"nodes":nodes,"edges":edges,"lineage_is_declared_not_inferred":True}
def bundle(db,project,public=False):
 b=_bundle(db,project,public); b.update({"release":"2.94.0","contract":CONTRACT,"summary":descriptive_summary(db,project,public),"lineage":lineage(db,project,public),"challenge_state_is_declared_not_core_decided":True}); return b
