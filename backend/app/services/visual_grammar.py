from __future__ import annotations

from datetime import datetime
import hashlib, json
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (
    VisualRuntimeSceneRecord, VisualRuntimeViewRecord, VisualViewCompositionRecord, VisualViewAssignmentRecord,
    VisualGrammarSpecificationRecord, VisualGrammarDataBindingRecord, VisualGrammarMarkRecord, VisualGrammarScaleRecord,
    VisualGrammarEncodingRecord, VisualGrammarTransformRecord, VisualGrammarGuideRecord, VisualGrammarSnapshotRecord,
)

CONTRACT='sc.visual-runtime.grammar.v1'
GRAMMAR_KINDS={'cartesian','polar','matrix','network','timeline','flow','geospatial','causal','layered','dashboard','custom'}
COORDINATE_SYSTEMS={'cartesian','polar','geographic','screen','abstract','custom'}
MARK_KINDS={'point','line','area','bar','rect','arc','text','rule','image','node','link','geoshape','trajectory','timeline-event','flow','band','interval','matrix-cell','custom'}
SCALE_KINDS={'linear','log','symlog','sqrt','pow','time','utc','ordinal','band','point','quantile','quantize','threshold','diverging','identity','custom'}
CHANNELS={'x','x2','y','y2','color','fill','stroke','size','shape','opacity','angle','radius','text','longitude','latitude','source','target','order','detail','tooltip','custom'}
TRANSFORM_KINDS={'filter','aggregate','bin','calculate','window','stack','normalize','sort','fold','pivot','lookup','density','regression','extent','sample','external','custom'}
GUIDE_KINDS={'axis','legend','title','annotation','grid','reference-line','reference-band','custom'}
VISIBILITIES={'private','workspace','public'}
FORBIDDEN={'transform_execute_by_core','aggregate_by_core','bin_by_core','scale_calculate_by_core','layout_by_core','draw_marks_by_core','gpu_execute_by_core','visual_inference_by_core','automatic_chart_generation_by_core','automatic_visual_truth_promotion'}

def _hash(v:Any)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()

def _ser(row):
    out={}
    for a in sa_inspect(row).mapper.column_attrs:
        v=getattr(row,a.key)
        if isinstance(v,datetime): v=v.isoformat()
        out[a.key]=v
    for key in list(out):
        if key.endswith('_json'): out[key[:-5]]=out.pop(key)
    return out

def _reject(p):
    bad=sorted(k for k in FORBIDDEN if p.get(k) not in (None,False))
    if bad: raise ValueError('Analytical Visualization Grammar is declarative; Core does not execute: '+', '.join(bad))

def boundaries():
    return {
        'grammar_specification_registry_by_core':True,'data_binding_registry_by_core':True,'mark_registry_by_core':True,
        'encoding_registry_by_core':True,'scale_registry_by_core':True,'transform_spec_registry_by_core':True,
        'guide_registry_by_core':True,'immutable_grammar_snapshots_by_core':True,'renderer_neutral_grammar_contract_by_core':True,
        'transform_execution_by_core':False,'aggregation_execution_by_core':False,'binning_execution_by_core':False,
        'scale_calculation_by_core':False,'layout_computation_by_core':False,'mark_drawing_by_core':False,
        'gpu_execution_by_core':False,'visual_inference_by_core':False,'automatic_chart_generation_by_core':False,
        'automatic_visual_truth_promotion':False,
    }

def readiness(db:Session):
    counts={}
    for name,cls in [('specifications',VisualGrammarSpecificationRecord),('data_bindings',VisualGrammarDataBindingRecord),('marks',VisualGrammarMarkRecord),('encodings',VisualGrammarEncodingRecord),('scales',VisualGrammarScaleRecord),('transforms',VisualGrammarTransformRecord),('guides',VisualGrammarGuideRecord),('snapshots',VisualGrammarSnapshotRecord)]:
        counts[name]=db.scalar(select(func.count()).select_from(cls)) or 0
    return {'release':'2.63.0','contract':CONTRACT,'counts':counts,**boundaries()}

def _spec(db,sid):
    row=db.get(VisualGrammarSpecificationRecord,sid)
    if not row: raise ValueError('specification_id does not exist.')
    return row

def _same_spec(db,cls,row_id,sid,label):
    if not row_id:return None
    row=db.get(cls,row_id)
    if not row or row.specification_id!=sid: raise ValueError(f'{label} must belong to the visualization grammar specification.')
    return row

def create_specification(db:Session,p:dict):
    _reject(p)
    scene=db.get(VisualRuntimeSceneRecord,p['scene_id'])
    if not scene: raise ValueError('scene_id does not exist.')
    comp_id=p.get('composition_id'); view_id=p.get('view_id')
    if comp_id:
        comp=db.get(VisualViewCompositionRecord,comp_id)
        if not comp or comp.scene_id!=scene.id: raise ValueError('composition_id must belong to scene_id.')
    if view_id:
        view=db.get(VisualRuntimeViewRecord,view_id)
        if not view or view.scene_id!=scene.id: raise ValueError('view_id must belong to scene_id.')
        if comp_id:
            assigned=db.scalar(select(func.count()).select_from(VisualViewAssignmentRecord).where(VisualViewAssignmentRecord.composition_id==comp_id,VisualViewAssignmentRecord.view_id==view_id)) or 0
            if not assigned: raise ValueError('view_id must be assigned to composition_id.')
    kind=p.get('grammar_kind','cartesian'); coord=p.get('coordinate_system','cartesian'); vis=p.get('visibility','private')
    if kind not in GRAMMAR_KINDS: raise ValueError('unsupported grammar_kind.')
    if coord not in COORDINATE_SYSTEMS: raise ValueError('unsupported coordinate_system.')
    if vis not in VISIBILITIES: raise ValueError('unsupported visibility.')
    row=VisualGrammarSpecificationRecord(scene_id=scene.id,composition_id=comp_id,view_id=view_id,grammar_key=p['grammar_key'],name=p['name'],grammar_kind=kind,coordinate_system=coord,data_policy_json=p.get('data_policy',{}),interaction_policy_json=p.get('interaction_policy',{}),visibility=vis,metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def add_data_binding(db:Session,sid:str,p:dict):
    _reject(p);_spec(db,sid)
    row=VisualGrammarDataBindingRecord(specification_id=sid,binding_key=p['binding_key'],source_kind=p.get('source_kind','scene'),source_ref=p['source_ref'],fields_json=p.get('fields',[]),schema_json=p.get('schema',{}),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def add_mark(db:Session,sid:str,p:dict):
    _reject(p);_spec(db,sid);kind=p['mark_kind']
    if kind not in MARK_KINDS: raise ValueError('unsupported mark_kind.')
    bid=p.get('data_binding_id');_same_spec(db,VisualGrammarDataBindingRecord,bid,sid,'data_binding_id')
    row=VisualGrammarMarkRecord(specification_id=sid,mark_key=p['mark_key'],mark_kind=kind,data_binding_id=bid,semantic_role=p.get('semantic_role','data'),order_index=int(p.get('order_index',0)),mark_spec_json=p.get('mark_spec',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def add_scale(db:Session,sid:str,p:dict):
    _reject(p);_spec(db,sid);kind=p.get('scale_kind','linear')
    if kind not in SCALE_KINDS: raise ValueError('unsupported scale_kind.')
    row=VisualGrammarScaleRecord(specification_id=sid,scale_key=p['scale_key'],scale_kind=kind,domain_json=p.get('domain'),range_json=p.get('range'),clamp=bool(p.get('clamp',False)),nice=bool(p.get('nice',False)),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def add_encoding(db:Session,sid:str,p:dict):
    _reject(p);_spec(db,sid);channel=p['channel']
    if channel not in CHANNELS: raise ValueError('unsupported channel.')
    mark_id=p.get('mark_id');scale_id=p.get('scale_id')
    _same_spec(db,VisualGrammarMarkRecord,mark_id,sid,'mark_id');_same_spec(db,VisualGrammarScaleRecord,scale_id,sid,'scale_id')
    row=VisualGrammarEncodingRecord(specification_id=sid,mark_id=mark_id,scale_id=scale_id,channel=channel,field_name=p.get('field_name'),data_type=p.get('data_type'),aggregate=p.get('aggregate'),value_json=p.get('value'),bin_json=p.get('bin',{}),condition_json=p.get('condition',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def add_transform(db:Session,sid:str,p:dict):
    _reject(p);_spec(db,sid);kind=p['transform_kind']
    if kind not in TRANSFORM_KINDS: raise ValueError('unsupported transform_kind.')
    bid=p.get('input_binding_id');_same_spec(db,VisualGrammarDataBindingRecord,bid,sid,'input_binding_id')
    row=VisualGrammarTransformRecord(specification_id=sid,transform_key=p['transform_key'],transform_kind=kind,input_binding_id=bid,output_binding_key=p.get('output_binding_key'),order_index=int(p.get('order_index',0)),parameters_json=p.get('parameters',{}),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def add_guide(db:Session,sid:str,p:dict):
    _reject(p);_spec(db,sid);kind=p.get('guide_kind','axis')
    if kind not in GUIDE_KINDS: raise ValueError('unsupported guide_kind.')
    scale_id=p.get('scale_id');_same_spec(db,VisualGrammarScaleRecord,scale_id,sid,'scale_id')
    row=VisualGrammarGuideRecord(specification_id=sid,guide_key=p['guide_key'],guide_kind=kind,channel=p.get('channel'),scale_id=scale_id,title=p.get('title'),order_index=int(p.get('order_index',0)),guide_spec_json=p.get('guide_spec',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def specification_bundle(db:Session,sid:str,public_only:bool=False):
    spec=_spec(db,sid)
    if public_only:
        scene=db.get(VisualRuntimeSceneRecord,spec.scene_id)
        if spec.visibility!='public' or not scene or scene.visibility!='public': raise ValueError('visualization grammar specification is not public.')
    def rows(cls): return [_ser(x) for x in db.scalars(select(cls).where(cls.specification_id==sid)).all()]
    return {'contract':CONTRACT,'specification':_ser(spec),'data_bindings':rows(VisualGrammarDataBindingRecord),'marks':rows(VisualGrammarMarkRecord),'encodings':rows(VisualGrammarEncodingRecord),'scales':rows(VisualGrammarScaleRecord),'transforms':rows(VisualGrammarTransformRecord),'guides':rows(VisualGrammarGuideRecord),'snapshots':rows(VisualGrammarSnapshotRecord),'boundaries':boundaries()}

def create_snapshot(db:Session,sid:str,p:dict):
    _reject(p);state=specification_bundle(db,sid);state.pop('snapshots',None)
    prevs=db.scalars(select(VisualGrammarSnapshotRecord).where(VisualGrammarSnapshotRecord.specification_id==sid).order_by(VisualGrammarSnapshotRecord.revision.asc())).all();rev=len(prevs)+1;prev=prevs[-1].content_hash if prevs else None
    h=_hash({'revision':rev,'previous_snapshot_hash':prev,'state':state})
    row=VisualGrammarSnapshotRecord(specification_id=sid,revision=rev,content_hash=h,previous_snapshot_hash=prev,state_json=state,provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'))
    db.add(row);db.commit();db.refresh(row);return _ser(row)
