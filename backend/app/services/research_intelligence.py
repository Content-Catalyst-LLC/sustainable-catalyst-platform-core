from __future__ import annotations
from datetime import datetime
import hashlib,json
from sqlalchemy import select,func
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (
    UnifiedResearchProjectProfileRecord,
    ResearchFindingRecord,ResearchFindingRevisionRecord,ResearchInterpretationRecord,
    ResearchClaimRecord,ResearchClaimRevisionRecord,ResearchEvidenceLinkRecord,
    ResearchDerivationLinkRecord,ResearchContradictionRecord,ResearchIntelligenceSnapshotRecord,
)

CONTRACT='sc.research.finding-claim-evidence.v1'
FINDING_TYPES={'observation','result','pattern','anomaly','estimate','model_output','synthesis','negative_result','limitation'}
FINDING_STATUSES={'proposed','recorded','revised','superseded','withdrawn'}
INTERPRETATION_STATUSES={'proposed','qualified','revised','superseded','withdrawn'}
CLAIM_TYPES={'descriptive','interpretive','causal','comparative','predictive','normative','methodological'}
CLAIM_STATUSES={'proposed','supported','contested','qualified','superseded','withdrawn','unresolved'}
POLARITIES={'affirmed','denied','uncertain','not_applicable'}
EVIDENCE_RELATIONS={'supports','contradicts','qualifies','is_insufficient_for','contextualizes','derived_from'}
TARGET_TYPES={'finding','interpretation','claim'}
DERIVATION_RELATIONSHIPS={'interpreted_as','supports_interpretation','derived_from','supports_claim','qualifies_claim','contextualizes'}
CONTRADICTION_STATUSES={'candidate','recorded','unresolved','qualified','resolved_externally','superseded','withdrawn'}
FORBIDDEN={
 'infer_truth_by_core','rank_claims_by_core','generate_claim_by_core','generate_finding_by_core',
 'judge_evidence_by_core','semantic_contradiction_inference_by_core','resolve_contradiction_by_core',
 'publish_by_core','alter_source_artifacts_by_core'
}
CLASSES=[ResearchFindingRecord,ResearchFindingRevisionRecord,ResearchInterpretationRecord,ResearchClaimRecord,ResearchClaimRevisionRecord,ResearchEvidenceLinkRecord,ResearchDerivationLinkRecord,ResearchContradictionRecord,ResearchIntelligenceSnapshotRecord]
NAMES=['findings','finding_revisions','interpretations','claims','claim_revisions','evidence_links','derivation_links','contradictions','snapshots']
OPPOSITE={('affirmed','denied'),('denied','affirmed')}

def _ser(r):
 out={}
 for a in sa_inspect(r).mapper.column_attrs:
  v=getattr(r,a.key);out[a.key]=v.isoformat() if isinstance(v,datetime) else v
 for k in list(out):
  if k.endswith('_json'):out[k[:-5]]=out.pop(k)
 return out

def _hash(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()

def _reject(p):
 bad=sorted(k for k in FORBIDDEN if p.get(k) not in (None,False))
 if bad:raise ValueError('Finding/Claim/Evidence Intelligence is provenance-aware and non-determinative; Core does not generate findings or claims, judge truth/evidence, rank claims, semantically infer or resolve contradictions, publish, or alter source artifacts: '+', '.join(bad))

def boundaries():
 return {
  'finding_registry_by_core':True,'interpretation_registry_by_core':True,'claim_registry_by_core':True,
  'evidence_link_registry_by_core':True,'declared_evidence_strength_metadata_by_core':True,
  'finding_claim_version_history_by_core':True,'derivation_lineage_registry_by_core':True,
  'deterministic_structured_contradiction_candidates_by_core':True,'immutable_research_intelligence_snapshots_by_core':True,
  'infer_truth_by_core':False,'rank_claims_by_core':False,'generate_claim_by_core':False,'generate_finding_by_core':False,
  'judge_evidence_by_core':False,'semantic_contradiction_inference_by_core':False,'resolve_contradiction_by_core':False,
  'publish_by_core':False,'alter_source_artifacts_by_core':False,
 }

def readiness(db):
 c=lambda cls:int(db.scalar(select(func.count()).select_from(cls)) or 0)
 return {'release':'2.77.0','contract':CONTRACT,'finding_types':sorted(FINDING_TYPES),'claim_types':sorted(CLAIM_TYPES),'claim_statuses':sorted(CLAIM_STATUSES),'evidence_relations':sorted(EVIDENCE_RELATIONS),'polarities':sorted(POLARITIES),'counts':dict(zip(NAMES,[c(x) for x in CLASSES])),**boundaries()}

def _project(db,pid):
 r=db.get(UnifiedResearchProjectProfileRecord,pid)
 if r is None:raise ValueError('project_entity_id must reference a v2.72 unified research project profile.')
 return r

def _finding(db,i):
 r=db.get(ResearchFindingRecord,i)
 if r is None:raise ValueError('research finding not found.')
 return r

def _interpretation(db,i):
 r=db.get(ResearchInterpretationRecord,i)
 if r is None:raise ValueError('research interpretation not found.')
 return r

def _claim(db,i):
 r=db.get(ResearchClaimRecord,i)
 if r is None:raise ValueError('research claim not found.')
 return r

def _typed(db,t,i):
 if t=='finding':return _finding(db,i)
 if t=='interpretation':return _interpretation(db,i)
 if t=='claim':return _claim(db,i)
 raise ValueError('unsupported research object type: '+str(t))

def _same_project(r,pid):
 if r.project_entity_id!=pid:raise ValueError('referenced research object must belong to the same project.')
 return r

def create_finding(db,pid,p):
 _reject(p);_project(db,pid)
 t=p.get('finding_type','result');s=p.get('status','proposed')
 if t not in FINDING_TYPES:raise ValueError('unsupported finding_type: '+t)
 if s not in FINDING_STATUSES:raise ValueError('unsupported finding status: '+s)
 if not str(p.get('title') or '').strip() or not str(p.get('statement') or '').strip():raise ValueError('title and statement are required.')
 r=ResearchFindingRecord(project_entity_id=pid,finding_key=p['finding_key'],title=p['title'],statement=p['statement'],finding_type=t,status=s,method_ref=p.get('method_ref'),analysis_run_ref=p.get('analysis_run_ref'),notebook_ref=p.get('notebook_ref'),reproducibility_package_ref=p.get('reproducibility_package_ref'),source_refs_json=p.get('source_refs',[]),uncertainty_json=p.get('uncertainty',{}),limitations_json=p.get('limitations',[]),metadata_json=p.get('metadata',{}),provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(r);db.commit();db.refresh(r);return _ser(r)

def create_interpretation(db,pid,p):
 _reject(p);_project(db,pid);s=p.get('status','proposed')
 if s not in INTERPRETATION_STATUSES:raise ValueError('unsupported interpretation status: '+s)
 if not str(p.get('title') or '').strip() or not str(p.get('interpretation_text') or '').strip():raise ValueError('title and interpretation_text are required.')
 r=ResearchInterpretationRecord(project_entity_id=pid,interpretation_key=p['interpretation_key'],title=p['title'],interpretation_text=p['interpretation_text'],status=s,assumptions_json=p.get('assumptions',[]),uncertainty_json=p.get('uncertainty',{}),limitations_json=p.get('limitations',[]),metadata_json=p.get('metadata',{}),provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(r);db.commit();db.refresh(r);return _ser(r)

def create_claim(db,pid,p):
 _reject(p);_project(db,pid);t=p.get('claim_type','interpretive');s=p.get('status','proposed');pol=p.get('polarity','not_applicable')
 if t not in CLAIM_TYPES:raise ValueError('unsupported claim_type: '+t)
 if s not in CLAIM_STATUSES:raise ValueError('unsupported claim status: '+s)
 if pol not in POLARITIES:raise ValueError('unsupported polarity: '+pol)
 if not str(p.get('claim_text') or '').strip():raise ValueError('claim_text is required.')
 triple=[p.get('subject_ref'),p.get('predicate'),p.get('object_ref')]
 if any(x not in (None,'') for x in triple) and not all(str(x or '').strip() for x in triple):raise ValueError('subject_ref, predicate, and object_ref must be supplied together for a structured claim.')
 if pol in {'affirmed','denied'} and not all(str(x or '').strip() for x in triple):raise ValueError('affirmed/denied polarity requires a complete structured subject/predicate/object claim.')
 r=ResearchClaimRecord(project_entity_id=pid,claim_key=p['claim_key'],claim_text=p['claim_text'],claim_type=t,status=s,subject_ref=p.get('subject_ref'),predicate=p.get('predicate'),object_ref=p.get('object_ref'),polarity=pol,scope_json=p.get('scope',{}),uncertainty_json=p.get('uncertainty',{}),qualifications_json=p.get('qualifications',[]),metadata_json=p.get('metadata',{}),provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(r);db.commit();db.refresh(r);return _ser(r)

def add_evidence_link(db,pid,p):
 _reject(p);_project(db,pid);t=p['target_type'];rel=p['relation']
 if t not in TARGET_TYPES:raise ValueError('unsupported target_type: '+t)
 if rel not in EVIDENCE_RELATIONS:raise ValueError('unsupported evidence relation: '+rel)
 _same_project(_typed(db,t,p['target_id']),pid)
 if not str(p.get('evidence_ref') or '').strip():raise ValueError('evidence_ref is required.')
 r=ResearchEvidenceLinkRecord(project_entity_id=pid,evidence_link_key=p['evidence_link_key'],evidence_ref=p['evidence_ref'],evidence_kind=p.get('evidence_kind','source'),target_type=t,target_id=p['target_id'],relation=rel,locator=p.get('locator'),declared_strength=p.get('declared_strength'),assessment_basis=p.get('assessment_basis'),assessment_json=p.get('assessment',{}),uncertainty_json=p.get('uncertainty',{}),metadata_json=p.get('metadata',{}),provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(r);db.commit();db.refresh(r);return _ser(r)

def add_derivation_link(db,pid,p):
 _reject(p);_project(db,pid);st=p['source_type'];tt=p['target_type'];rel=p.get('relationship','derived_from')
 if st not in TARGET_TYPES or tt not in TARGET_TYPES:raise ValueError('source_type and target_type must be finding, interpretation, or claim.')
 if rel not in DERIVATION_RELATIONSHIPS:raise ValueError('unsupported derivation relationship: '+rel)
 _same_project(_typed(db,st,p['source_id']),pid);_same_project(_typed(db,tt,p['target_id']),pid)
 if st==tt and p['source_id']==p['target_id']:raise ValueError('a research object cannot derive from itself.')
 r=ResearchDerivationLinkRecord(project_entity_id=pid,derivation_key=p['derivation_key'],source_type=st,source_id=p['source_id'],target_type=tt,target_id=p['target_id'],relationship=rel,rationale=p.get('rationale'),provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(r);db.commit();db.refresh(r);return _ser(r)

def _structured_key(c):
 if not c.subject_ref or not c.predicate or not c.object_ref:return None
 return (c.subject_ref.strip(),c.predicate.strip(),c.object_ref.strip())

def contradiction_candidates(db,pid,public=False):
 p=_project(db,pid)
 if public and p.visibility!='public':raise ValueError('research project is not public.')
 claims=list(db.scalars(select(ResearchClaimRecord).where(ResearchClaimRecord.project_entity_id==pid)).all())
 out=[]
 for i,a in enumerate(claims):
  if a.status in {'withdrawn','superseded'}:continue
  ka=_structured_key(a)
  if ka is None:continue
  for b in claims[i+1:]:
   if b.status in {'withdrawn','superseded'}:continue
   if ka==_structured_key(b) and (a.polarity,b.polarity) in OPPOSITE:
    out.append({'claim_a_id':a.id,'claim_b_id':b.id,'subject_ref':ka[0],'predicate':ka[1],'object_ref':ka[2],'claim_a_polarity':a.polarity,'claim_b_polarity':b.polarity,'candidate_basis':'exact_structured_triple_opposite_declared_polarity','determinative':False})
 return {'release':'2.77.0','contract':CONTRACT,'project_entity_id':pid,'candidates':out,'semantic_inference_performed':False,'truth_determination_performed':False}

def create_contradiction(db,pid,p):
 _reject(p);_project(db,pid);a=_same_project(_claim(db,p['claim_a_id']),pid);b=_same_project(_claim(db,p['claim_b_id']),pid)
 if a.id==b.id:raise ValueError('claim_a_id and claim_b_id must be different.')
 s=p.get('status','unresolved')
 if s not in CONTRADICTION_STATUSES:raise ValueError('unsupported contradiction status: '+s)
 ka,kb=_structured_key(a),_structured_key(b);det={}
 if ka and ka==kb and (a.polarity,b.polarity) in OPPOSITE:det={'candidate':True,'basis':'exact_structured_triple_opposite_declared_polarity'}
 r=ResearchContradictionRecord(project_entity_id=pid,contradiction_key=p['contradiction_key'],claim_a_id=a.id,claim_b_id=b.id,contradiction_type=p.get('contradiction_type','declared'),status=s,basis_refs_json=p.get('basis_refs',[]),rationale=p.get('rationale'),deterministic_match_json=det,provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(r);db.commit();db.refresh(r);return _ser(r)

def _finding_state(r):return _ser(r)
def _claim_state(r):return _ser(r)

def revise_finding(db,fid,p):
 _reject(p);r=_finding(db,fid);prior=_finding_state(r)
 allowed={'title','statement','finding_type','status','method_ref','analysis_run_ref','notebook_ref','reproducibility_package_ref','source_refs','uncertainty','limitations','metadata','provenance'}
 for k in p:
  if k not in allowed|{'change_summary','created_by'} and k not in FORBIDDEN:raise ValueError('unsupported finding revision field: '+k)
 if 'finding_type' in p and p['finding_type'] not in FINDING_TYPES:raise ValueError('unsupported finding_type: '+p['finding_type'])
 if 'status' in p and p['status'] not in FINDING_STATUSES:raise ValueError('unsupported finding status: '+p['status'])
 mapping={'source_refs':'source_refs_json','uncertainty':'uncertainty_json','limitations':'limitations_json','metadata':'metadata_json','provenance':'provenance_json'}
 for k in allowed:
  if k in p:setattr(r,mapping.get(k,k),p[k])
 db.flush();revised=_finding_state(r);h=_hash(revised);prev=db.scalar(select(ResearchFindingRevisionRecord).where(ResearchFindingRevisionRecord.finding_id==fid).order_by(ResearchFindingRevisionRecord.revision.desc()).limit(1));rev=1 if prev is None else prev.revision+1
 rr=ResearchFindingRevisionRecord(finding_id=fid,project_entity_id=r.project_entity_id,revision=rev,state_hash=h,prior_state_json=prior,revised_state_json=revised,change_summary=p.get('change_summary'),provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(rr);db.commit();db.refresh(rr);return _ser(rr)

def revise_claim(db,cid,p):
 _reject(p);r=_claim(db,cid);prior=_claim_state(r)
 allowed={'claim_text','claim_type','status','subject_ref','predicate','object_ref','polarity','scope','uncertainty','qualifications','metadata','provenance'}
 for k in p:
  if k not in allowed|{'change_summary','created_by'} and k not in FORBIDDEN:raise ValueError('unsupported claim revision field: '+k)
 if 'claim_type' in p and p['claim_type'] not in CLAIM_TYPES:raise ValueError('unsupported claim_type: '+p['claim_type'])
 if 'status' in p and p['status'] not in CLAIM_STATUSES:raise ValueError('unsupported claim status: '+p['status'])
 if 'polarity' in p and p['polarity'] not in POLARITIES:raise ValueError('unsupported polarity: '+p['polarity'])
 mapping={'scope':'scope_json','uncertainty':'uncertainty_json','qualifications':'qualifications_json','metadata':'metadata_json','provenance':'provenance_json'}
 for k in allowed:
  if k in p:setattr(r,mapping.get(k,k),p[k])
 triple=[r.subject_ref,r.predicate,r.object_ref]
 if any(x not in (None,'') for x in triple) and not all(str(x or '').strip() for x in triple):raise ValueError('subject_ref, predicate, and object_ref must be supplied together for a structured claim.')
 if r.polarity in {'affirmed','denied'} and not all(str(x or '').strip() for x in triple):raise ValueError('affirmed/denied polarity requires a complete structured subject/predicate/object claim.')
 db.flush();revised=_claim_state(r);h=_hash(revised);prev=db.scalar(select(ResearchClaimRevisionRecord).where(ResearchClaimRevisionRecord.claim_id==cid).order_by(ResearchClaimRevisionRecord.revision.desc()).limit(1));rev=1 if prev is None else prev.revision+1
 rr=ResearchClaimRevisionRecord(claim_id=cid,project_entity_id=r.project_entity_id,revision=rev,state_hash=h,prior_state_json=prior,revised_state_json=revised,change_summary=p.get('change_summary'),provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(rr);db.commit();db.refresh(rr);return _ser(rr)

def bundle(db,pid,public=False):
 p=_project(db,pid)
 if public and p.visibility!='public':raise ValueError('research project is not public.')
 def rows(cls):return [_ser(x) for x in db.scalars(select(cls).where(cls.project_entity_id==pid)).all()]
 return {'release':'2.77.0','contract':CONTRACT,'project':_ser(p),'findings':rows(ResearchFindingRecord),'finding_revisions':rows(ResearchFindingRevisionRecord),'interpretations':rows(ResearchInterpretationRecord),'claims':rows(ResearchClaimRecord),'claim_revisions':rows(ResearchClaimRevisionRecord),'evidence_links':rows(ResearchEvidenceLinkRecord),'derivation_links':rows(ResearchDerivationLinkRecord),'contradictions':rows(ResearchContradictionRecord),'snapshots':rows(ResearchIntelligenceSnapshotRecord),**boundaries()}

def _state(db,pid):
 s=bundle(db,pid);s.pop('snapshots',None);return s

def snapshot(db,pid,p):
 _reject(p);_project(db,pid);state=_state(db,pid);h=_hash(state);prev=db.scalar(select(ResearchIntelligenceSnapshotRecord).where(ResearchIntelligenceSnapshotRecord.project_entity_id==pid).order_by(ResearchIntelligenceSnapshotRecord.revision.desc()).limit(1));rev=1 if prev is None else prev.revision+1
 r=ResearchIntelligenceSnapshotRecord(project_entity_id=pid,revision=rev,content_hash=h,previous_snapshot_hash=None if prev is None else prev.content_hash,state_json=state,provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(r);db.commit();db.refresh(r);return _ser(r)
