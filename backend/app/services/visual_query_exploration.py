from __future__ import annotations
from datetime import datetime
import hashlib,json
from typing import Any
from sqlalchemy import func,select
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (
    VisualRuntimeViewRecord,VisualViewCompositionRecord,VisualViewAssignmentRecord,
    VisualGrammarSpecificationRecord,VisualGrammarDataBindingRecord,
    VisualExplorationSessionRecord,VisualQueryTargetRecord,VisualQueryRequestRecord,VisualQueryPredicateRecord,
    VisualTraversalRequestRecord,VisualQueryResultBindingRecord,VisualExplorationStateRecord,VisualQuerySnapshotRecord,
)
CONTRACT='sc.visual-runtime.visual-query.v1'
SESSION_STATUSES={'active','paused','closed','archived'}
QUERY_KINDS={'filter','lookup','compare','path','subgraph','neighborhood','temporal-window','spatial-window','evidence-trace','provenance-trace','aggregate-request','custom'}
TARGET_KINDS={'scene','view','grammar','data-binding','node','edge','layer','annotation','selection','cross-filter','entity','evidence','predictive','forensic','custom'}
TRAVERSAL_KINDS={'path','shortest-path-request','subgraph','neighborhood','ancestors','descendants','provenance','causal','temporal','spatial','custom'}
QUERY_STATUSES={'declared','submitted','external-running','external-complete','external-failed','cancelled'}
RESULT_STATUSES={'external-result','verified','rejected','superseded'}
FORBIDDEN={'execute_query_by_core','traverse_graph_by_core','retrieve_data_by_core','filter_data_by_core','aggregate_data_by_core','rank_results_by_core','recommend_results_by_core','automatic_query_execution','visual_inference_by_core','automatic_visual_truth_promotion'}

def _hash(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def _ser(row):
    out={}
    for a in sa_inspect(row).mapper.column_attrs:
        v=getattr(row,a.key)
        if isinstance(v,datetime):v=v.isoformat()
        out[a.key]=v
    for k in list(out):
        if k.endswith('_json'):out[k[:-5]]=out.pop(k)
    return out

def _reject(p):
    bad=sorted(k for k in FORBIDDEN if p.get(k) not in (None,False))
    if bad:raise ValueError('Visual Query & Exploration is declarative; Core does not execute: '+', '.join(bad))

def boundaries():
    return {
      'visual_exploration_session_registry_by_core':True,'visual_query_target_registry_by_core':True,
      'visual_query_request_registry_by_core':True,'visual_query_predicate_registry_by_core':True,
      'visual_traversal_request_registry_by_core':True,'visual_query_result_evidence_binding_by_core':True,
      'saved_visual_exploration_state_by_core':True,'immutable_visual_query_snapshots_by_core':True,
      'query_execution_by_core':False,'graph_traversal_by_core':False,'data_retrieval_by_core':False,
      'data_filtering_by_core':False,'aggregation_execution_by_core':False,'result_ranking_by_core':False,
      'result_recommendation_by_core':False,'automatic_query_execution':False,'visual_inference_by_core':False,
      'automatic_visual_truth_promotion':False,
    }

def readiness(db:Session):
    def c(cls):return db.scalar(select(func.count()).select_from(cls)) or 0
    return {'release':'2.65.0','contract':CONTRACT,'counts':{
      'sessions':c(VisualExplorationSessionRecord),'targets':c(VisualQueryTargetRecord),'queries':c(VisualQueryRequestRecord),
      'predicates':c(VisualQueryPredicateRecord),'traversals':c(VisualTraversalRequestRecord),'results':c(VisualQueryResultBindingRecord),
      'saved_states':c(VisualExplorationStateRecord),'snapshots':c(VisualQuerySnapshotRecord)},**boundaries()}

def _composition(db,cid):
    x=db.get(VisualViewCompositionRecord,cid)
    if not x:raise ValueError('View composition not found.')
    return x

def _session(db,sid):
    x=db.get(VisualExplorationSessionRecord,sid)
    if not x:raise ValueError('Exploration session not found.')
    return x

def _query(db,qid,sid=None):
    q=db.get(VisualQueryRequestRecord,qid)
    if not q:raise ValueError('Query request not found.')
    if sid and q.session_id!=sid:raise ValueError('query_id must belong to the exploration session.')
    return q

def _assigned_view(db,cid,vid):
    v=db.get(VisualRuntimeViewRecord,vid)
    if not v:raise ValueError('view_id does not exist.')
    a=db.scalar(select(VisualViewAssignmentRecord).where(VisualViewAssignmentRecord.composition_id==cid,VisualViewAssignmentRecord.view_id==vid))
    if not a:raise ValueError('view_id must be assigned to the session composition.')
    return v

def create_session(db:Session,cid:str,p:dict):
    _reject(p);_composition(db,cid);status=p.get('status','active')
    if status not in SESSION_STATUSES:raise ValueError('unsupported session status.')
    row=VisualExplorationSessionRecord(composition_id=cid,session_key=p['session_key'],name=p['name'],purpose=p.get('purpose'),visibility=p.get('visibility','private'),status=status,context_json=p.get('context',{}),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def create_target(db:Session,sid:str,p:dict):
    _reject(p);ses=_session(db,sid);comp=_composition(db,ses.composition_id);kind=p['target_kind']
    if kind not in TARGET_KINDS:raise ValueError('unsupported target_kind.')
    vid=p.get('view_id');gid=p.get('grammar_specification_id');bid=p.get('data_binding_id')
    if vid:_assigned_view(db,comp.id,vid)
    if gid:
        g=db.get(VisualGrammarSpecificationRecord,gid)
        if not g or g.scene_id!=comp.scene_id:raise ValueError('grammar_specification_id must belong to the composition scene.')
    if bid:
        b=db.get(VisualGrammarDataBindingRecord,bid)
        if not b:raise ValueError('data_binding_id does not exist.')
        g=db.get(VisualGrammarSpecificationRecord,b.specification_id)
        if not g or g.scene_id!=comp.scene_id:raise ValueError('data_binding_id must belong to the composition scene.')
        if gid and b.specification_id!=gid:raise ValueError('data_binding_id must belong to grammar_specification_id.')
    row=VisualQueryTargetRecord(session_id=sid,target_key=p['target_key'],target_kind=kind,target_ref=p.get('target_ref'),view_id=vid,grammar_specification_id=gid,data_binding_id=bid,target_spec_json=p.get('target_spec',{}),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def create_query(db:Session,sid:str,p:dict):
    _reject(p);_session(db,sid);kind=p['query_kind'];status=p.get('status','declared')
    if kind not in QUERY_KINDS:raise ValueError('unsupported query_kind.')
    if status not in QUERY_STATUSES:raise ValueError('unsupported query status.')
    tids=p.get('target_ids',[])
    for tid in tids:
        t=db.get(VisualQueryTargetRecord,tid)
        if not t or t.session_id!=sid:raise ValueError('target_ids must belong to the exploration session.')
    spec=p.get('query_spec',{})
    if not isinstance(spec,dict) or not spec:raise ValueError('query_spec must be a non-empty declarative object.')
    row=VisualQueryRequestRecord(session_id=sid,query_key=p['query_key'],name=p['name'],query_kind=kind,target_ids_json=tids,query_spec_json=spec,expected_result_kind=p.get('expected_result_kind'),runtime_product=p.get('runtime_product'),status=status,provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def create_predicate(db:Session,qid:str,p:dict):
    _reject(p);_query(db,qid)
    pred=p.get('predicate',{})
    if not isinstance(pred,dict) or (not pred and p.get('value') is None):raise ValueError('predicate or value must define declarative query intent.')
    row=VisualQueryPredicateRecord(query_id=qid,predicate_key=p['predicate_key'],predicate_kind=p.get('predicate_kind','filter'),field_name=p.get('field_name'),operator=p.get('operator'),value_json=p.get('value'),predicate_json=pred,provenance_json=p.get('provenance',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def create_traversal(db:Session,qid:str,p:dict):
    _reject(p);_query(db,qid);kind=p.get('traversal_kind','path')
    if kind not in TRAVERSAL_KINDS:raise ValueError('unsupported traversal_kind.')
    depth=p.get('max_depth')
    if depth is not None and (not isinstance(depth,int) or depth<1 or depth>100):raise ValueError('max_depth must be an integer from 1 to 100.')
    row=VisualTraversalRequestRecord(query_id=qid,traversal_key=p['traversal_key'],traversal_kind=kind,start_refs_json=p.get('start_refs',[]),end_refs_json=p.get('end_refs',[]),relation_kinds_json=p.get('relation_kinds',[]),max_depth=depth,constraints_json=p.get('constraints',{}),provenance_json=p.get('provenance',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def create_result_binding(db:Session,qid:str,p:dict):
    _reject(p);_query(db,qid);status=p.get('status','external-result')
    if status not in RESULT_STATUSES:raise ValueError('unsupported result status.')
    if p.get('externally_computed',True) is not True:raise ValueError('Visual query results must be externally computed or supplied.')
    row=VisualQueryResultBindingRecord(query_id=qid,result_kind=p['result_kind'],result_ref=p.get('result_ref'),result_summary_json=p.get('result_summary',{}),evidence_json=p.get('evidence',{}),runtime_product=p.get('runtime_product'),runtime_ref=p.get('runtime_ref'),status=status,externally_computed=True,provenance_json=p.get('provenance',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def create_saved_state(db:Session,sid:str,p:dict):
    _reject(p);_session(db,sid);qids=p.get('active_query_ids',[])
    for qid in qids:_query(db,qid,sid)
    row=VisualExplorationStateRecord(session_id=sid,state_key=p['state_key'],active_query_ids_json=qids,selected_refs_json=p.get('selected_refs',[]),filter_state_json=p.get('filter_state',{}),view_state_json=p.get('view_state',{}),notes_json=p.get('notes',[]),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def session_bundle(db:Session,sid:str,public_only:bool=False):
    ses=_session(db,sid);comp=_composition(db,ses.composition_id)
    if public_only:
        if ses.visibility!='public' or comp.visibility!='public':raise ValueError('visual exploration session is not public.')
    def rows(cls,field='session_id'):return [_ser(x) for x in db.scalars(select(cls).where(getattr(cls,field)==sid)).all()]
    targets=rows(VisualQueryTargetRecord); queries=rows(VisualQueryRequestRecord)
    qids=[q['id'] for q in queries]
    def byq(cls):return [_ser(x) for x in db.scalars(select(cls).where(cls.query_id.in_(qids))).all()] if qids else []
    return {'contract':CONTRACT,'session':_ser(ses),'targets':targets,'queries':queries,'predicates':byq(VisualQueryPredicateRecord),'traversals':byq(VisualTraversalRequestRecord),'results':byq(VisualQueryResultBindingRecord),'saved_states':rows(VisualExplorationStateRecord),'snapshots':rows(VisualQuerySnapshotRecord),'boundaries':boundaries()}

def create_snapshot(db:Session,sid:str,p:dict):
    _reject(p);state=session_bundle(db,sid);state.pop('snapshots',None)
    prevs=db.scalars(select(VisualQuerySnapshotRecord).where(VisualQuerySnapshotRecord.session_id==sid).order_by(VisualQuerySnapshotRecord.revision.asc())).all();rev=len(prevs)+1;prev=prevs[-1].content_hash if prevs else None
    h=_hash({'revision':rev,'previous_snapshot_hash':prev,'state':state})
    row=VisualQuerySnapshotRecord(session_id=sid,revision=rev,content_hash=h,previous_snapshot_hash=prev,state_json=state,provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'))
    db.add(row);db.commit();db.refresh(row);return _ser(row)
