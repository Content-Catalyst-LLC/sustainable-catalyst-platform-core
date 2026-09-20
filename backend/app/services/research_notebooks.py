from __future__ import annotations
import hashlib,json
from datetime import datetime
from sqlalchemy import func,select,inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (UnifiedResearchProjectProfileRecord,ResearchNotebookRecord,ResearchNotebookSectionRecord,ResearchNotebookEntryRecord,ResearchNotebookBindingRecord,ResearchNotebookCitationRecord,ResearchAnalyticalNarrativeRecord,ResearchAnalyticalNarrativeBlockRecord,ResearchNotebookRevisionRecord,ResearchNotebookSnapshotRecord)
CONTRACT='sc.research.notebook-narrative.v1'
NOTEBOOK_TYPES={'analytical','literature','experimental','computational','field','investigative','mixed'}
ENTRY_TYPES={'narrative','method','code_reference','equation','dataset','evidence','analysis_run','result','finding','visualization','limitation','question','note','citation_context'}
BINDING_TYPES={'project_component','methodology','methodology_version','analysis_run','analysis_input','analysis_output','dataset','evidence','finding','visualization','reproducibility_package','lineage_graph','external'}
BLOCK_TYPES={'context','question','method','evidence','result','interpretation','limitation','uncertainty','conclusion','transition'}
FORBIDDEN={'execute_code_by_core','execute_analysis_by_core','generate_narrative_by_core','fabricate_citation_by_core','infer_conclusion_by_core','publish_by_core','alter_bound_artifacts_by_core'}
CLASSES=[ResearchNotebookRecord,ResearchNotebookSectionRecord,ResearchNotebookEntryRecord,ResearchNotebookBindingRecord,ResearchNotebookCitationRecord,ResearchAnalyticalNarrativeRecord,ResearchAnalyticalNarrativeBlockRecord,ResearchNotebookRevisionRecord,ResearchNotebookSnapshotRecord]
NAMES=['notebooks','sections','entries','bindings','citations','narratives','narrative_blocks','revisions','snapshots']
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
 if bad:raise ValueError('Research notebooks are declarative; Core does not execute, generate, fabricate, infer, publish, or alter bound artifacts: '+', '.join(bad))
def boundaries():
 return {'notebook_registry_by_core':True,'ordered_section_entry_registry_by_core':True,'cross_research_binding_registry_by_core':True,'citation_registry_by_core':True,'analytical_narrative_registry_by_core':True,'narrative_block_registry_by_core':True,'revision_registry_by_core':True,'immutable_notebook_snapshots_by_core':True,'execute_code_by_core':False,'execute_analysis_by_core':False,'generate_narrative_by_core':False,'fabricate_citation_by_core':False,'infer_conclusion_by_core':False,'publish_by_core':False,'alter_bound_artifacts_by_core':False}
def readiness(db):
 c=lambda cls:int(db.scalar(select(func.count()).select_from(cls)) or 0)
 return {'release':'2.76.0','contract':CONTRACT,'notebook_types':sorted(NOTEBOOK_TYPES),'entry_types':sorted(ENTRY_TYPES),'binding_types':sorted(BINDING_TYPES),'narrative_block_types':sorted(BLOCK_TYPES),'counts':dict(zip(NAMES,[c(x) for x in CLASSES])),**boundaries()}
def _project(db,pid):
 r=db.get(UnifiedResearchProjectProfileRecord,pid)
 if r is None:raise ValueError('project_entity_id must reference a v2.72 unified research project profile.')
 return r
def _notebook(db,nid):
 r=db.get(ResearchNotebookRecord,nid)
 if r is None:raise ValueError('research notebook not found.')
 return r
def _section(db,sid):
 r=db.get(ResearchNotebookSectionRecord,sid)
 if r is None:raise ValueError('notebook section not found.')
 return r
def _entry(db,eid):
 r=db.get(ResearchNotebookEntryRecord,eid)
 if r is None:raise ValueError('notebook entry not found.')
 return r
def _narrative(db,nid):
 r=db.get(ResearchAnalyticalNarrativeRecord,nid)
 if r is None:raise ValueError('analytical narrative not found.')
 return r
def create_notebook(db,pid,p):
 _reject(p);_project(db,pid);t=p.get('notebook_type','analytical')
 if t not in NOTEBOOK_TYPES:raise ValueError('unsupported notebook_type: '+t)
 if not str(p.get('title') or '').strip():raise ValueError('title is required.')
 r=ResearchNotebookRecord(project_entity_id=pid,notebook_key=p['notebook_key'],title=p['title'],purpose=p.get('purpose'),notebook_type=t,status=p.get('status','draft'),visibility=p.get('visibility','private'),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_section(db,nid,p):
 _reject(p);n=_notebook(db,nid);r=ResearchNotebookSectionRecord(notebook_id=nid,project_entity_id=n.project_entity_id,section_key=p['section_key'],heading=p['heading'],section_type=p.get('section_type','analysis'),sequence=int(p.get('sequence',0)),purpose=p.get('purpose'),provenance_json=p.get('provenance',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_entry(db,nid,p):
 _reject(p);n=_notebook(db,nid);t=p['entry_type']
 if t not in ENTRY_TYPES:raise ValueError('unsupported entry_type: '+t)
 sid=p.get('section_id')
 if sid and _section(db,sid).notebook_id!=nid:raise ValueError('section_id must belong to the notebook.')
 r=ResearchNotebookEntryRecord(notebook_id=nid,project_entity_id=n.project_entity_id,section_id=sid,entry_key=p['entry_key'],entry_type=t,sequence=int(p.get('sequence',0)),title=p.get('title'),body_text=p.get('body_text'),content_json=p.get('content',{}),language=p.get('language'),status=p.get('status','draft'),created_by=p.get('created_by','operator'),provenance_json=p.get('provenance',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_binding(db,eid,p):
 _reject(p);e=_entry(db,eid);t=p['binding_type']
 if t not in BINDING_TYPES:raise ValueError('unsupported binding_type: '+t)
 r=ResearchNotebookBindingRecord(entry_id=eid,notebook_id=e.notebook_id,project_entity_id=e.project_entity_id,binding_key=p['binding_key'],binding_type=t,target_ref=p['target_ref'],relationship=p.get('relationship','references'),version_ref=p.get('version_ref'),content_hash=p.get('content_hash'),metadata_json=p.get('metadata',{}),provenance_json=p.get('provenance',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_citation(db,eid,p):
 _reject(p);e=_entry(db,eid);r=ResearchNotebookCitationRecord(entry_id=eid,notebook_id=e.notebook_id,project_entity_id=e.project_entity_id,citation_key=p['citation_key'],source_ref=p['source_ref'],locator=p.get('locator'),citation_text=p.get('citation_text'),citation_data_json=p.get('citation_data',{}),provenance_json=p.get('provenance',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def create_narrative(db,nid,p):
 _reject(p);n=_notebook(db,nid)
 if not str(p.get('title') or '').strip():raise ValueError('title is required.')
 r=ResearchAnalyticalNarrativeRecord(notebook_id=nid,project_entity_id=n.project_entity_id,narrative_key=p['narrative_key'],title=p['title'],purpose=p.get('purpose'),status=p.get('status','draft'),scope_json=p.get('scope',{}),provenance_json=p.get('provenance',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_narrative_block(db,narrative_id,p):
 _reject(p);n=_narrative(db,narrative_id);t=p['block_type']
 if t not in BLOCK_TYPES:raise ValueError('unsupported block_type: '+t)
 r=ResearchAnalyticalNarrativeBlockRecord(narrative_id=narrative_id,notebook_id=n.notebook_id,project_entity_id=n.project_entity_id,block_key=p['block_key'],block_type=t,sequence=int(p.get('sequence',0)),text=p.get('text'),support_refs_json=p.get('support_refs',[]),uncertainty_json=p.get('uncertainty',{}),provenance_json=p.get('provenance',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def bundle(db,nid,public=False):
 n=_notebook(db,nid)
 if public and n.visibility!='public':raise ValueError('research notebook is not public.')
 def rows(cls,field='notebook_id'):return [_ser(x) for x in db.scalars(select(cls).where(getattr(cls,field)==nid)).all()]
 narratives=rows(ResearchAnalyticalNarrativeRecord);nids=[x['id'] for x in narratives]
 blocks=[_ser(x) for x in db.scalars(select(ResearchAnalyticalNarrativeBlockRecord).where(ResearchAnalyticalNarrativeBlockRecord.narrative_id.in_(nids))).all()] if nids else []
 return {'release':'2.76.0','contract':CONTRACT,'notebook':_ser(n),'sections':rows(ResearchNotebookSectionRecord),'entries':rows(ResearchNotebookEntryRecord),'bindings':rows(ResearchNotebookBindingRecord),'citations':rows(ResearchNotebookCitationRecord),'narratives':narratives,'narrative_blocks':blocks,'revisions':rows(ResearchNotebookRevisionRecord),'snapshots':rows(ResearchNotebookSnapshotRecord),**boundaries()}
def _state(db,nid):
 s=bundle(db,nid);s.pop('revisions',None);s.pop('snapshots',None);return s
def add_revision(db,nid,p):
 _reject(p);n=_notebook(db,nid);state=_state(db,nid);h=_hash(state);prev=db.scalar(select(ResearchNotebookRevisionRecord).where(ResearchNotebookRevisionRecord.notebook_id==nid).order_by(ResearchNotebookRevisionRecord.revision.desc()).limit(1));rev=1 if prev is None else prev.revision+1
 r=ResearchNotebookRevisionRecord(notebook_id=nid,project_entity_id=n.project_entity_id,revision=rev,state_hash=h,change_summary=p.get('change_summary'),change_set_json=p.get('change_set',{}),created_by=p.get('created_by','operator'),provenance_json=p.get('provenance',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def snapshot(db,nid,p):
 _reject(p);n=_notebook(db,nid);state=_state(db,nid);h=_hash(state);prev=db.scalar(select(ResearchNotebookSnapshotRecord).where(ResearchNotebookSnapshotRecord.notebook_id==nid).order_by(ResearchNotebookSnapshotRecord.revision.desc()).limit(1));rev=1 if prev is None else prev.revision+1
 r=ResearchNotebookSnapshotRecord(notebook_id=nid,project_entity_id=n.project_entity_id,revision=rev,content_hash=h,previous_snapshot_hash=None if prev is None else prev.content_hash,state_json=state,provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(r);db.commit();db.refresh(r);return _ser(r)
