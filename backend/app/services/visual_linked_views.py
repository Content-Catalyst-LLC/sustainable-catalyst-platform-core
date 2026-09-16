from __future__ import annotations
from datetime import datetime
import hashlib,json
from typing import Any
from sqlalchemy import func,select
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (
    VisualRuntimeSceneRecord,VisualRuntimeViewRecord,VisualViewCompositionRecord,VisualViewAssignmentRecord,VisualViewLinkGroupRecord,
    VisualGrammarSpecificationRecord,VisualGrammarDataBindingRecord,
    VisualLinkPolicyRecord,VisualSelectionSetRecord,VisualCrossFilterRecord,VisualBrushRangeRecord,
    VisualFocusHighlightRecord,VisualPropagationRecord,VisualLinkedViewSnapshotRecord,
)
CONTRACT='sc.visual-runtime.linked-views.v1'
CHANNELS={'selection','filter','brush','focus','highlight','time-window','viewport','layer-visibility','custom'}
SELECTION_KINDS={'point','multi','interval','set','predicate','custom'}
COMBINE_MODES={'and','or','replace'}
PROPAGATION_MODES={'declarative','one-way','two-way','broadcast','custom'}
EVENT_KINDS=CHANNELS
STATUSES={'declared','accepted','rejected','external-applied','external-failed'}
FORBIDDEN={'execute_query_by_core','filter_data_by_core','dispatch_ui_events_by_core','handle_brush_events_by_core','render_highlights_by_core','compute_selection_by_core','automatic_cross_filter_execution','visual_inference_by_core','automatic_visual_truth_promotion'}

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
    if bad:raise ValueError('Linked Views & Cross-Filtering is declarative; Core does not execute: '+', '.join(bad))

def boundaries():
    return {
      'link_policy_registry_by_core':True,'selection_set_registry_by_core':True,'cross_filter_predicate_registry_by_core':True,
      'brush_range_registry_by_core':True,'focus_highlight_state_registry_by_core':True,'propagation_evidence_registry_by_core':True,
      'immutable_linked_view_snapshots_by_core':True,'renderer_neutral_cross_filter_contract_by_core':True,
      'query_execution_by_core':False,'data_filtering_by_core':False,'ui_event_dispatch_by_core':False,
      'brush_event_execution_by_core':False,'highlight_rendering_by_core':False,'selection_computation_by_core':False,
      'automatic_cross_filter_execution':False,'visual_inference_by_core':False,'automatic_visual_truth_promotion':False,
    }

def readiness(db:Session):
    def c(cls):return db.scalar(select(func.count()).select_from(cls)) or 0
    return {'release':'2.64.0','contract':CONTRACT,'counts':{
      'link_policies':c(VisualLinkPolicyRecord),'selection_sets':c(VisualSelectionSetRecord),'cross_filters':c(VisualCrossFilterRecord),
      'brush_ranges':c(VisualBrushRangeRecord),'focus_highlights':c(VisualFocusHighlightRecord),'propagation_records':c(VisualPropagationRecord),
      'snapshots':c(VisualLinkedViewSnapshotRecord)},**boundaries()}

def _composition(db,cid):
    x=db.get(VisualViewCompositionRecord,cid)
    if not x:raise ValueError('View composition not found.')
    return x

def _assigned_view(db,cid,vid):
    v=db.get(VisualRuntimeViewRecord,vid)
    if not v:raise ValueError('view_id does not exist.')
    a=db.scalar(select(VisualViewAssignmentRecord).where(VisualViewAssignmentRecord.composition_id==cid,VisualViewAssignmentRecord.view_id==vid))
    if not a:raise ValueError('view_id must be assigned to the composition.')
    return v

def _views(db,cid,ids):
    out=[]
    for vid in ids or []:out.append(_assigned_view(db,cid,vid).id)
    return out

def _grammar(db,comp,spec_id,binding_id):
    spec=None
    if spec_id:
        spec=db.get(VisualGrammarSpecificationRecord,spec_id)
        if not spec or spec.scene_id!=comp.scene_id:raise ValueError('grammar_specification_id must belong to the composition scene.')
    if binding_id:
        b=db.get(VisualGrammarDataBindingRecord,binding_id)
        if not b:raise ValueError('data_binding_id does not exist.')
        if spec and b.specification_id!=spec.id:raise ValueError('data_binding_id must belong to grammar_specification_id.')
        if not spec:
            spec=db.get(VisualGrammarSpecificationRecord,b.specification_id)
            if not spec or spec.scene_id!=comp.scene_id:raise ValueError('data_binding_id must belong to the composition scene.')
    return spec

def create_link_policy(db:Session,cid:str,p:dict):
    _reject(p);comp=_composition(db,cid);lgid=p.get('link_group_id')
    if lgid:
        lg=db.get(VisualViewLinkGroupRecord,lgid)
        if not lg or lg.composition_id!=cid:raise ValueError('link_group_id must belong to the composition.')
    src=_views(db,cid,p.get('source_view_ids',[]));tgt=_views(db,cid,p.get('target_view_ids',[]))
    chans=p.get('channels',[])
    if not chans or any(x not in CHANNELS for x in chans):raise ValueError('channels must contain supported interaction channels.')
    mode=p.get('propagation_mode','declarative')
    if mode not in PROPAGATION_MODES:raise ValueError('unsupported propagation_mode.')
    row=VisualLinkPolicyRecord(composition_id=cid,link_group_id=lgid,policy_key=p['policy_key'],name=p['name'],source_view_ids_json=src,target_view_ids_json=tgt,channels_json=chans,propagation_mode=mode,policy_json=p.get('policy',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def create_selection_set(db:Session,cid:str,p:dict):
    _reject(p);comp=_composition(db,cid);src=_assigned_view(db,cid,p['source_view_id']);_grammar(db,comp,p.get('grammar_specification_id'),p.get('data_binding_id'));kind=p.get('selection_kind','set')
    if kind not in SELECTION_KINDS:raise ValueError('unsupported selection_kind.')
    row=VisualSelectionSetRecord(composition_id=cid,source_view_id=src.id,grammar_specification_id=p.get('grammar_specification_id'),data_binding_id=p.get('data_binding_id'),selection_key=p['selection_key'],selection_kind=kind,selected_refs_json=p.get('selected_refs',[]),field_values_json=p.get('field_values',{}),target_view_ids_json=_views(db,cid,p.get('target_view_ids',[])),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def create_cross_filter(db:Session,cid:str,p:dict):
    _reject(p);comp=_composition(db,cid);src=_assigned_view(db,cid,p['source_view_id']);_grammar(db,comp,p.get('grammar_specification_id'),p.get('data_binding_id'));mode=p.get('combine_mode','and')
    if mode not in COMBINE_MODES:raise ValueError('unsupported combine_mode.')
    pred=p.get('predicate',{})
    if not isinstance(pred,dict) or not pred:raise ValueError('predicate must be a non-empty declarative object.')
    row=VisualCrossFilterRecord(composition_id=cid,source_view_id=src.id,grammar_specification_id=p.get('grammar_specification_id'),data_binding_id=p.get('data_binding_id'),filter_key=p['filter_key'],predicate_json=pred,target_view_ids_json=_views(db,cid,p.get('target_view_ids',[])),combine_mode=mode,empty_policy=p.get('empty_policy','show-all'),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def create_brush_range(db:Session,cid:str,p:dict):
    _reject(p);comp=_composition(db,cid);src=_assigned_view(db,cid,p['source_view_id']);_grammar(db,comp,p.get('grammar_specification_id'),p.get('data_binding_id'));rng=p.get('range',{})
    if not isinstance(rng,dict) or not rng:raise ValueError('range must be a non-empty declarative object.')
    row=VisualBrushRangeRecord(composition_id=cid,source_view_id=src.id,grammar_specification_id=p.get('grammar_specification_id'),data_binding_id=p.get('data_binding_id'),brush_key=p['brush_key'],field_name=p.get('field_name'),channel=p.get('channel'),range_json=rng,target_view_ids_json=_views(db,cid,p.get('target_view_ids',[])),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def create_focus_highlight(db:Session,cid:str,p:dict):
    _reject(p);_composition(db,cid);src=_assigned_view(db,cid,p['source_view_id'])
    row=VisualFocusHighlightRecord(composition_id=cid,source_view_id=src.id,state_key=p['state_key'],focused_refs_json=p.get('focused_refs',[]),highlighted_refs_json=p.get('highlighted_refs',[]),target_view_ids_json=_views(db,cid,p.get('target_view_ids',[])),style_contract_json=p.get('style_contract',{}),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def record_propagation(db:Session,cid:str,p:dict):
    _reject(p);_composition(db,cid);src=_assigned_view(db,cid,p['source_view_id']);tgt=_assigned_view(db,cid,p['target_view_id']);kind=p['event_kind'];status=p.get('status','declared')
    if kind not in EVENT_KINDS:raise ValueError('unsupported event_kind.')
    if status not in STATUSES:raise ValueError('unsupported status.')
    polid=p.get('link_policy_id')
    if polid:
        pol=db.get(VisualLinkPolicyRecord,polid)
        if not pol or pol.composition_id!=cid:raise ValueError('link_policy_id must belong to the composition.')
    row=VisualPropagationRecord(composition_id=cid,link_policy_id=polid,source_view_id=src.id,target_view_id=tgt.id,event_kind=kind,source_record_kind=p.get('source_record_kind'),source_record_id=p.get('source_record_id'),propagated_state_json=p.get('propagated_state',{}),status=status,evidence_json=p.get('evidence',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def composition_bundle(db:Session,cid:str,public_only:bool=False):
    comp=_composition(db,cid)
    if public_only:
        scene=db.get(VisualRuntimeSceneRecord,comp.scene_id)
        if comp.visibility!='public' or not scene or scene.visibility!='public':raise ValueError('linked-view composition is not public.')
    def rows(cls):return [_ser(x) for x in db.scalars(select(cls).where(cls.composition_id==cid)).all()]
    return {'contract':CONTRACT,'composition':_ser(comp),'link_policies':rows(VisualLinkPolicyRecord),'selection_sets':rows(VisualSelectionSetRecord),'cross_filters':rows(VisualCrossFilterRecord),'brush_ranges':rows(VisualBrushRangeRecord),'focus_highlights':rows(VisualFocusHighlightRecord),'propagation_records':rows(VisualPropagationRecord),'snapshots':rows(VisualLinkedViewSnapshotRecord),'boundaries':boundaries()}

def create_snapshot(db:Session,cid:str,p:dict):
    _reject(p);state=composition_bundle(db,cid);state.pop('snapshots',None)
    prevs=db.scalars(select(VisualLinkedViewSnapshotRecord).where(VisualLinkedViewSnapshotRecord.composition_id==cid).order_by(VisualLinkedViewSnapshotRecord.revision.asc())).all();rev=len(prevs)+1;prev=prevs[-1].content_hash if prevs else None
    h=_hash({'revision':rev,'previous_snapshot_hash':prev,'state':state})
    row=VisualLinkedViewSnapshotRecord(composition_id=cid,revision=rev,content_hash=h,previous_snapshot_hash=prev,state_json=state,provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'))
    db.add(row);db.commit();db.refresh(row);return _ser(row)
