from __future__ import annotations

from datetime import datetime
import hashlib, json
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (
    VisualRuntimeSceneRecord, VisualRuntimeViewRecord,
    VisualRendererProfileRecord, VisualViewCompositionRecord, VisualViewAssignmentRecord,
    VisualViewLinkGroupRecord, VisualInteractionStateRecord, VisualRendererResolutionRecord,
    VisualCompositionSnapshotRecord,
)

CONTRACT='sc.visual-runtime.composition.v1'
RENDERER_KINDS={'svg','canvas2d','webgl','dom','hybrid','external'}
COMPOSITION_KINDS={'single','split','grid','overlay','linked','dashboard','story','custom'}
STATE_KINDS={'selection','filter','hover','focus','time-window','viewport','layer-visibility','custom'}
VISIBILITIES={'private','workspace','public'}
FORBIDDEN={'render_by_core','layout_by_core','animate_by_core','hit_test_by_core','gpu_execute_by_core','visual_inference_by_core','automatic_renderer_execution','automatic_visual_truth_promotion'}

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
    if bad: raise ValueError('Interactive Renderer Core coordinates renderer-neutral view state and does not execute: '+', '.join(bad))

def boundaries():
    return {
        'renderer_profile_registry_by_core':True,'view_composition_registry_by_core':True,
        'view_renderer_assignment_registry_by_core':True,'linked_view_group_registry_by_core':True,
        'propagated_interaction_state_by_core':True,'renderer_capability_resolution_by_core':True,
        'immutable_composition_snapshots_by_core':True,'renderer_neutral_composition_contract_by_core':True,
        'layout_computation_by_core':False,'svg_canvas_webgl_drawing_by_core':False,'animation_execution_by_core':False,
        'hit_testing_by_core':False,'gpu_execution_by_core':False,'visual_inference_by_core':False,
        'automatic_renderer_execution':False,'automatic_visual_truth_promotion':False,
    }

def readiness(db:Session):
    def c(cls): return db.scalar(select(func.count()).select_from(cls)) or 0
    return {'release':'2.62.0','migration_0066_applied':True,'contract':CONTRACT,'counts':{
        'renderer_profiles':c(VisualRendererProfileRecord),'compositions':c(VisualViewCompositionRecord),
        'assignments':c(VisualViewAssignmentRecord),'link_groups':c(VisualViewLinkGroupRecord),
        'interaction_states':c(VisualInteractionStateRecord),'resolutions':c(VisualRendererResolutionRecord),
        'snapshots':c(VisualCompositionSnapshotRecord)},**boundaries()}

def _scene(db,scene_id):
    x=db.get(VisualRuntimeSceneRecord,scene_id)
    if not x: raise ValueError('scene_id does not reference an existing visual runtime scene.')
    return x

def _composition(db,cid):
    x=db.get(VisualViewCompositionRecord,cid)
    if not x: raise ValueError('View composition not found.')
    return x

def create_renderer_profile(db:Session,p:dict):
    _reject(p); kind=p.get('renderer_kind','svg')
    if kind not in RENDERER_KINDS: raise ValueError('Unsupported renderer_kind.')
    row=VisualRendererProfileRecord(renderer_key=p['renderer_key'],name=p['name'],renderer_kind=kind,capabilities_json=p.get('capabilities',{}),supported_view_kinds_json=p.get('supported_view_kinds',[]),interaction_contract_json=p.get('interaction_contract',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def create_composition(db:Session,scene_id:str,p:dict):
    _reject(p); scene=_scene(db,scene_id); kind=p.get('composition_kind','single'); vis=p.get('visibility',scene.visibility)
    if kind not in COMPOSITION_KINDS: raise ValueError('Unsupported composition_kind.')
    if vis not in VISIBILITIES: raise ValueError('Unsupported visibility.')
    row=VisualViewCompositionRecord(scene_id=scene_id,composition_key=p['composition_key'],name=p['name'],composition_kind=kind,layout_spec_json=p.get('layout_spec',{}),shared_state_json=p.get('shared_state',{}),visibility=vis,metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def assign_view(db:Session,cid:str,p:dict):
    _reject(p); comp=_composition(db,cid); view=db.get(VisualRuntimeViewRecord,p['view_id'])
    if not view or view.scene_id!=comp.scene_id: raise ValueError('view_id must reference a view in the composition scene.')
    rp=None
    if p.get('renderer_profile_id'):
        rp=db.get(VisualRendererProfileRecord,p['renderer_profile_id'])
        if not rp: raise ValueError('renderer_profile_id does not exist.')
    row=VisualViewAssignmentRecord(composition_id=cid,view_id=view.id,renderer_profile_id=rp.id if rp else None,slot_key=p.get('slot_key','main'),order_index=int(p.get('order_index',0)),camera_state_json=p.get('camera_state',{}),layer_state_json=p.get('layer_state',{}),renderer_options_json=p.get('renderer_options',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def add_link_group(db:Session,cid:str,p:dict):
    _reject(p); comp=_composition(db,cid); ids=p.get('linked_view_ids',[])
    if len(ids)<2: raise ValueError('linked_view_ids must contain at least two views.')
    for vid in ids:
        v=db.get(VisualRuntimeViewRecord,vid)
        if not v or v.scene_id!=comp.scene_id: raise ValueError('Every linked view must belong to the composition scene.')
    row=VisualViewLinkGroupRecord(composition_id=cid,link_key=p['link_key'],name=p['name'],linked_view_ids_json=ids,propagation_policy_json=p.get('propagation_policy',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def add_interaction_state(db:Session,cid:str,p:dict):
    _reject(p); comp=_composition(db,cid); kind=p.get('state_kind','selection')
    if kind not in STATE_KINDS: raise ValueError('Unsupported state_kind.')
    vid=p.get('source_view_id')
    if vid:
        v=db.get(VisualRuntimeViewRecord,vid)
        if not v or v.scene_id!=comp.scene_id: raise ValueError('source_view_id must belong to the composition scene.')
    row=VisualInteractionStateRecord(composition_id=cid,source_view_id=vid,state_kind=kind,state_json=p.get('state',{}),propagation_json=p.get('propagation',{}),provenance_json=p.get('provenance',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def resolve_renderer(db:Session,cid:str,p:dict):
    _reject(p); comp=_composition(db,cid); view=db.get(VisualRuntimeViewRecord,p['view_id']); rp=db.get(VisualRendererProfileRecord,p['renderer_profile_id'])
    if not view or view.scene_id!=comp.scene_id: raise ValueError('view_id must belong to the composition scene.')
    if not rp: raise ValueError('renderer_profile_id does not exist.')
    supported=rp.supported_view_kinds_json or []
    status='compatible' if not supported or view.view_kind in supported else 'incompatible'
    row=VisualRendererResolutionRecord(composition_id=cid,view_id=view.id,renderer_profile_id=rp.id,resolution_status=status,capability_evidence_json={'view_kind':view.view_kind,'supported_view_kinds':supported,'core_executed_renderer':False},metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)

def composition_bundle(db:Session,cid:str):
    comp=_composition(db,cid)
    def rows(cls): return [_ser(x) for x in db.scalars(select(cls).where(cls.composition_id==cid)).all()]
    return {'contract':CONTRACT,'composition':_ser(comp),'assignments':rows(VisualViewAssignmentRecord),'link_groups':rows(VisualViewLinkGroupRecord),'interaction_states':rows(VisualInteractionStateRecord),'renderer_resolutions':rows(VisualRendererResolutionRecord),'snapshots':rows(VisualCompositionSnapshotRecord),'boundaries':boundaries()}

def create_snapshot(db:Session,cid:str,p:dict):
    _reject(p); state=composition_bundle(db,cid); state.pop('snapshots',None)
    prevs=db.scalars(select(VisualCompositionSnapshotRecord).where(VisualCompositionSnapshotRecord.composition_id==cid).order_by(VisualCompositionSnapshotRecord.revision.asc())).all(); rev=len(prevs)+1; prev=prevs[-1].content_hash if prevs else None
    h=_hash({'revision':rev,'previous_snapshot_hash':prev,'state':state})
    row=VisualCompositionSnapshotRecord(composition_id=cid,revision=rev,content_hash=h,previous_snapshot_hash=prev,state_json=state,provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'))
    db.add(row);db.commit();db.refresh(row);return _ser(row)
