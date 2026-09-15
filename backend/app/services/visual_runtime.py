from __future__ import annotations

from datetime import datetime
import hashlib
import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session

from ..models import (
    Entity, VisualReasoningObjectRecord, VisualReasoningElementRecord,
    VisualRuntimeSceneRecord, VisualRuntimeLayerRecord, VisualRuntimeNodeRecord,
    VisualRuntimeEdgeRecord, VisualRuntimeAnnotationRecord, VisualRuntimeViewRecord,
    VisualRuntimeBindingRecord, VisualRuntimeSnapshotRecord,
)

CONTRACT = "sc.visual-runtime.scene.v1"
SCENE_KINDS = {"semantic","system-map","flow-map","causal-map","evidence-map","timeline","spatial-temporal","model-canvas","decision-landscape","composite"}
COORDINATE_SPACES = {"abstract","cartesian","geographic","temporal","hybrid","none"}
VISIBILITIES = {"private","workspace","public"}
STATUSES = {"draft","reviewed","published","archived"}
DIRECTIONS = {"directed","undirected","bidirectional"}
FORBIDDEN = {
    "render_by_core","layout_by_core","animate_by_core","gpu_execute_by_core",
    "visual_inference_by_core","hit_test_by_core","renderer_execute_by_core",
    "automatic_visual_truth_promotion",
}


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",",":"), default=str).encode()).hexdigest()


def _ser(row):
    out={}
    for a in sa_inspect(row).mapper.column_attrs:
        v=getattr(row,a.key)
        if isinstance(v,datetime): v=v.isoformat()
        out[a.key]=v
    for key in list(out):
        if key.endswith("_json"):
            out[key[:-5]]=out.pop(key)
    return out


def _reject(payload: dict):
    bad=sorted(k for k in FORBIDDEN if payload.get(k) not in (None,False))
    if bad:
        raise ValueError("Visual Runtime Core stores renderer-neutral state and does not fit the requested Core-side execution fields: "+", ".join(bad))


def boundaries():
    return {
        "scene_registry_by_core":True,
        "scene_graph_node_registry_by_core":True,
        "scene_graph_edge_registry_by_core":True,
        "scene_layer_registry_by_core":True,
        "scene_annotation_registry_by_core":True,
        "viewport_selection_state_by_core":True,
        "cross_product_visual_bindings_by_core":True,
        "immutable_scene_snapshots_by_core":True,
        "renderer_neutral_scene_contract_by_core":True,
        "layout_computation_by_core":False,
        "canvas_svg_webgl_rendering_by_core":False,
        "animation_execution_by_core":False,
        "gpu_execution_by_core":False,
        "hit_testing_by_core":False,
        "visual_inference_by_core":False,
        "automatic_visual_truth_promotion":False,
    }


def readiness(db:Session):
    def c(cls): return db.scalar(select(func.count()).select_from(cls)) or 0
    return {
        "release":"2.61.0","migration_0065_applied":True,"contract":CONTRACT,
        "counts":{
            "scenes":c(VisualRuntimeSceneRecord),"layers":c(VisualRuntimeLayerRecord),
            "nodes":c(VisualRuntimeNodeRecord),"edges":c(VisualRuntimeEdgeRecord),
            "annotations":c(VisualRuntimeAnnotationRecord),"views":c(VisualRuntimeViewRecord),
            "bindings":c(VisualRuntimeBindingRecord),"snapshots":c(VisualRuntimeSnapshotRecord),
        }, **boundaries()
    }


def _scene(db:Session,scene_id:str,public_only=False):
    s=db.get(VisualRuntimeSceneRecord,scene_id)
    if not s or (public_only and s.visibility!="public"):
        raise ValueError("Visual runtime scene not found.")
    return s


def _same_scene(db:Session,cls,obj_id,scene_id,field):
    if obj_id is None: return None
    obj=db.get(cls,obj_id)
    if not obj or obj.scene_id!=scene_id: raise ValueError(f"{field} must reference an object in the same scene.")
    return obj


def create_scene(db:Session,p:dict):
    _reject(p)
    project=db.get(Entity,p.get("project_entity_id"))
    if not project: raise ValueError("project_entity_id does not reference an existing Core entity.")
    vis=p.get("visibility","private"); kind=p.get("scene_kind","semantic"); cs=p.get("coordinate_space","abstract"); status=p.get("status","draft")
    if vis not in VISIBILITIES: raise ValueError("Unsupported visibility.")
    if kind not in SCENE_KINDS: raise ValueError("Unsupported scene_kind.")
    if cs not in COORDINATE_SPACES: raise ValueError("Unsupported coordinate_space.")
    if status not in STATUSES: raise ValueError("Unsupported status.")
    source=p.get("source_visual_entity_id")
    if source and not db.get(VisualReasoningObjectRecord,source): raise ValueError("source_visual_entity_id must reference a Visual Reasoning object.")
    row=VisualRuntimeSceneRecord(project_entity_id=project.id,source_visual_entity_id=source,scene_key=p["scene_key"],name=p["name"],description=p.get("description"),scene_kind=kind,coordinate_space=cs,status=status,visibility=vis,scene_metadata_json=p.get("scene_metadata",{}),provenance_json=p.get("provenance",{}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def list_scenes(db:Session,project_entity_id=None,limit=100,offset=0,public_only=False):
    q=select(VisualRuntimeSceneRecord)
    if project_entity_id:q=q.where(VisualRuntimeSceneRecord.project_entity_id==project_entity_id)
    if public_only:q=q.where(VisualRuntimeSceneRecord.visibility=="public")
    total=db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows=db.scalars(q.order_by(VisualRuntimeSceneRecord.created_at.desc()).limit(limit).offset(offset)).all()
    return [_ser(x) for x in rows],total


def add_layer(db:Session,scene_id:str,p:dict):
    _reject(p); _scene(db,scene_id)
    row=VisualRuntimeLayerRecord(scene_id=scene_id,layer_key=p["layer_key"],name=p["name"],layer_kind=p.get("layer_kind","semantic"),order_index=int(p.get("order_index",0)),visible_by_default=bool(p.get("visible_by_default",True)),locked_by_default=bool(p.get("locked_by_default",False)),style_hints_json=p.get("style_hints",{}),metadata_json=p.get("metadata",{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)


def add_node(db:Session,scene_id:str,p:dict):
    _reject(p); scene=_scene(db,scene_id)
    layer=p.get("layer_id"); _same_scene(db,VisualRuntimeLayerRecord,layer,scene_id,"layer_id")
    ent=p.get("source_entity_id")
    if ent and not db.get(Entity,ent): raise ValueError("source_entity_id does not reference an existing Core entity.")
    ve=p.get("source_visual_element_id")
    if ve:
        elem=db.get(VisualReasoningElementRecord,ve)
        if not elem: raise ValueError("source_visual_element_id does not exist.")
        if scene.source_visual_entity_id and elem.visual_entity_id!=scene.source_visual_entity_id: raise ValueError("source_visual_element_id belongs to another Visual Reasoning object.")
    row=VisualRuntimeNodeRecord(scene_id=scene_id,layer_id=layer,node_key=p["node_key"],node_kind=p.get("node_kind","node"),semantic_role=p.get("semantic_role","context"),label=p["label"],source_entity_id=ent,source_visual_element_id=ve,position_json=p.get("position",{}),geometry_json=p.get("geometry",{}),value_json=p.get("value"),uncertainty_json=p.get("uncertainty",{}),style_hints_json=p.get("style_hints",{}),provenance_json=p.get("provenance",{}),metadata_json=p.get("metadata",{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)


def add_edge(db:Session,scene_id:str,p:dict):
    _reject(p);_scene(db,scene_id)
    _same_scene(db,VisualRuntimeNodeRecord,p.get("source_node_id"),scene_id,"source_node_id"); _same_scene(db,VisualRuntimeNodeRecord,p.get("target_node_id"),scene_id,"target_node_id")
    layer=p.get("layer_id");_same_scene(db,VisualRuntimeLayerRecord,layer,scene_id,"layer_id")
    direction=p.get("direction","directed")
    if direction not in DIRECTIONS: raise ValueError("Unsupported direction.")
    row=VisualRuntimeEdgeRecord(scene_id=scene_id,layer_id=layer,edge_key=p["edge_key"],source_node_id=p["source_node_id"],target_node_id=p["target_node_id"],edge_kind=p.get("edge_kind","relation"),semantic_role=p.get("semantic_role","association"),direction=direction,label=p.get("label"),weight=p.get("weight"),confidence=p.get("confidence"),geometry_json=p.get("geometry",{}),style_hints_json=p.get("style_hints",{}),provenance_json=p.get("provenance",{}),metadata_json=p.get("metadata",{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)


def add_annotation(db:Session,scene_id:str,p:dict):
    _reject(p);_scene(db,scene_id)
    node=p.get("node_id"); edge=p.get("edge_id")
    _same_scene(db,VisualRuntimeNodeRecord,node,scene_id,"node_id");_same_scene(db,VisualRuntimeEdgeRecord,edge,scene_id,"edge_id")
    row=VisualRuntimeAnnotationRecord(scene_id=scene_id,node_id=node,edge_id=edge,annotation_kind=p.get("annotation_kind","note"),text=p["text"],anchor_json=p.get("anchor",{}),evidence_ref=p.get("evidence_ref"),metadata_json=p.get("metadata",{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)


def add_view(db:Session,scene_id:str,p:dict):
    _reject(p);_scene(db,scene_id)
    row=VisualRuntimeViewRecord(scene_id=scene_id,view_key=p["view_key"],name=p["name"],view_kind=p.get("view_kind","canvas"),viewport_json=p.get("viewport",{}),selection_json=p.get("selection",{}),filter_json=p.get("filter",{}),layer_state_json=p.get("layer_state",{}),interaction_state_json=p.get("interaction_state",{}),renderer_hints_json=p.get("renderer_hints",{}),metadata_json=p.get("metadata",{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)


def add_binding(db:Session,scene_id:str,p:dict):
    _reject(p);_scene(db,scene_id)
    node=p.get("node_id");edge=p.get("edge_id")
    _same_scene(db,VisualRuntimeNodeRecord,node,scene_id,"node_id");_same_scene(db,VisualRuntimeEdgeRecord,edge,scene_id,"edge_id")
    if node is None and edge is None: raise ValueError("A binding must target a scene node or edge.")
    product=p["source_product"]
    if product=="core" and p.get("source_kind")=="entity" and not db.get(Entity,p["source_ref"]): raise ValueError("Core entity binding source_ref does not exist.")
    row=VisualRuntimeBindingRecord(scene_id=scene_id,node_id=node,edge_id=edge,binding_key=p["binding_key"],source_product=product,source_kind=p["source_kind"],source_ref=p["source_ref"],binding_role=p.get("binding_role","context"),contract_version=p.get("contract_version"),projection_json=p.get("projection",{}),provenance_json=p.get("provenance",{}),metadata_json=p.get("metadata",{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)


def scene_bundle(db:Session,scene_id:str,public_only=False):
    s=_scene(db,scene_id,public_only=public_only)
    def rows(cls): return [_ser(x) for x in db.scalars(select(cls).where(cls.scene_id==scene_id)).all()]
    return {"contract":CONTRACT,"scene":_ser(s),"layers":rows(VisualRuntimeLayerRecord),"nodes":rows(VisualRuntimeNodeRecord),"edges":rows(VisualRuntimeEdgeRecord),"annotations":rows(VisualRuntimeAnnotationRecord),"views":rows(VisualRuntimeViewRecord),"bindings":rows(VisualRuntimeBindingRecord),"snapshots":rows(VisualRuntimeSnapshotRecord),"boundaries":boundaries()}


def create_snapshot(db:Session,scene_id:str,p:dict):
    _reject(p);_scene(db,scene_id)
    state=scene_bundle(db,scene_id)
    state.pop("snapshots",None)
    existing=db.scalars(select(VisualRuntimeSnapshotRecord).where(VisualRuntimeSnapshotRecord.scene_id==scene_id).order_by(VisualRuntimeSnapshotRecord.revision.asc())).all()
    rev=len(existing)+1; prev=existing[-1].content_hash if existing else None
    content_hash=_hash({"revision":rev,"previous_snapshot_hash":prev,"state":state})
    row=VisualRuntimeSnapshotRecord(scene_id=scene_id,revision=rev,content_hash=content_hash,previous_snapshot_hash=prev,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator"))
    db.add(row);db.commit();db.refresh(row);return _ser(row)
