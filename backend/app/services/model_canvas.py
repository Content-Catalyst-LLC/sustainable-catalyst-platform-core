from __future__ import annotations
import hashlib
import json
from typing import Any
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Entity, ResearchModelRecord, ResearchModelVersionRecord, ResearchVariableRecord, ResearchParameterRecord,
    ResearchScenarioRecord, ResearchModelRunRecord, ResearchResultRecord,
    ModelCanvasRecord, ModelCanvasNodeRecord, ModelCanvasEdgeRecord, ModelCanvasControlRecord,
    ModelCanvasStateRecord, ModelCanvasViewRecord, VisualizationSpecificationRecord,
)
from . import visual_reasoning, visualization_registry

CANVAS_STATES={"draft","review","published","archived"}
INTERACTION_MODES={"inspect","inspect-configure","scenario-configure","review"}
NODE_KINDS={"model","component","input","parameter","variable","state","equation","scenario","run","result","output","note"}
EDGE_KINDS={"dependency","flow","causal","derived-from","parameterizes","produces","contains","requires","association"}
CONTROL_KINDS={"input","slider","select","toggle","scenario-selector","action-request"}
DATA_TYPES={"number","integer","boolean","string","category","json"}
SPEC_KINDS={"diagram","composite","network"}

def _ser(row):
    out={}
    for c in row.__table__.columns:
        v=getattr(row,c.name)
        if hasattr(v,'isoformat'):v=v.isoformat()
        out[c.name]=v
    return out

def _hash(value:Any)->str:
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),default=str).encode();return hashlib.sha256(raw).hexdigest()

def _require(db:Session,visual_entity_id:str)->ModelCanvasRecord:
    row=db.get(ModelCanvasRecord,visual_entity_id)
    if row is None:raise HTTPException(status_code=404,detail='Model canvas not found.')
    return row

def _public(db:Session,visual_entity_id:str):
    e=db.get(Entity,visual_entity_id)
    if e is None or e.visibility!='public':raise HTTPException(status_code=404,detail='Model canvas not found.')

def _project(db:Session,pid:str):
    e=db.get(Entity,pid)
    if e is None or e.entity_type!='research-project':raise ValueError('project_entity_id must reference a research-project.')

def _model(db:Session,mid:str,pid:str)->ResearchModelRecord:
    e=db.get(Entity,mid);m=db.get(ResearchModelRecord,mid)
    if e is None or e.entity_type!='model' or m is None:raise ValueError('model_entity_id must reference a research model.')
    if m.project_entity_id and m.project_entity_id!=pid:raise ValueError('model_entity_id belongs to a different research project.')
    return m

def _version(db:Session,vid:str|None,mid:str):
    if not vid:return
    e=db.get(Entity,vid);v=db.get(ResearchModelVersionRecord,vid)
    if e is None or e.entity_type!='model-version' or v is None or v.model_entity_id!=mid:raise ValueError('model_version_entity_id must reference a version of the canvas model.')

def readiness(db:Session)->dict[str,Any]:
    counts={'canvases':db.scalar(select(func.count()).select_from(ModelCanvasRecord)) or 0,'nodes':db.scalar(select(func.count()).select_from(ModelCanvasNodeRecord)) or 0,'edges':db.scalar(select(func.count()).select_from(ModelCanvasEdgeRecord)) or 0,'controls':db.scalar(select(func.count()).select_from(ModelCanvasControlRecord)) or 0,'states':db.scalar(select(func.count()).select_from(ModelCanvasStateRecord)) or 0,'views':db.scalar(select(func.count()).select_from(ModelCanvasViewRecord)) or 0}
    return {'counts':counts,'visual_kind':'model-canvas','research_models_reused':True,'model_versions_reused':True,'parameter_controls_governed':True,'immutable_interaction_states':True,'external_execution_handoff':True,'model_execution_by_core':False,'numerical_computation_by_core':False,'layout_execution_by_core':False,'automatic_truth_promotion':False}

def create_canvas(db:Session,payload:dict[str,Any],*,release:str)->dict[str,Any]:
    pid=str(payload.get('project_entity_id') or '');mid=str(payload.get('model_entity_id') or '')
    _project(db,pid);_model(db,mid,pid);_version(db,payload.get('model_version_entity_id'),mid)
    state=str(payload.get('canvas_state') or 'draft');mode=str(payload.get('interaction_mode') or 'inspect-configure')
    if state not in CANVAS_STATES:raise ValueError('Unsupported canvas_state.')
    if mode not in INTERACTION_MODES:raise ValueError('Unsupported interaction_mode.')
    visual=visual_reasoning.create_object(db,name=str(payload.get('name') or 'Model canvas'),slug=payload.get('slug'),description=payload.get('description'),entity_id=payload.get('entity_id'),visibility=str(payload.get('visibility') or 'public'),entity_status=str(payload.get('status') or 'active'),visual_kind='model-canvas',reasoning_purpose=str(payload.get('reasoning_purpose') or 'explore'),semantic_state='draft' if state=='draft' else ('reviewed' if state=='review' else ('published' if state=='published' else 'archived')),coordinate_space='abstract',project_entity_id=pid,primary_subject_entity_id=mid,lens=dict(payload.get('lens') or {}),filters=dict(payload.get('filters') or {}),assumptions=list(payload.get('assumptions') or []),metadata={**dict(payload.get('metadata') or {}),'interactive_model_canvas':'v2.34.0'},release=release)
    row=ModelCanvasRecord(visual_entity_id=visual['id'],project_entity_id=pid,model_entity_id=mid,model_version_entity_id=payload.get('model_version_entity_id'),canvas_state=state,interaction_mode=mode,execution_target=str(payload.get('execution_target') or 'external'),assumptions_json=list(payload.get('assumptions') or []),metadata_json=dict(payload.get('metadata') or {}),created_by=str(payload.get('created_by') or 'operator'))
    db.add(row);db.commit();db.refresh(row)
    # Seed a model node to make the canvas immediately meaningful.
    if not db.scalar(select(ModelCanvasNodeRecord).where(ModelCanvasNodeRecord.visual_entity_id==visual['id'],ModelCanvasNodeRecord.node_key=='model')):
        db.add(ModelCanvasNodeRecord(visual_entity_id=visual['id'],node_key='model',node_kind='model',semantic_role='model',bound_entity_id=mid,label=visual.get('name') or 'Model',metadata_json={'seeded':True}));db.commit()
    return read_canvas(db,visual['id'])

def list_canvases(db:Session,*,public_only=False,limit=100,offset=0):
    q=select(ModelCanvasRecord).join(Entity,Entity.id==ModelCanvasRecord.visual_entity_id);cq=select(func.count()).select_from(ModelCanvasRecord).join(Entity,Entity.id==ModelCanvasRecord.visual_entity_id)
    if public_only:q=q.where(Entity.visibility=='public');cq=cq.where(Entity.visibility=='public')
    total=int(db.scalar(cq) or 0);rows=db.scalars(q.order_by(ModelCanvasRecord.created_at.desc()).limit(limit).offset(offset)).all();return [_ser(x) for x in rows],total

def read_canvas(db:Session,visual_entity_id:str,*,public_only=False):
    row=_require(db,visual_entity_id)
    if public_only:_public(db,visual_entity_id)
    out=_ser(row);e=db.get(Entity,visual_entity_id);out['name']=e.name if e else None;out['visibility']=e.visibility if e else None;return out

def _bound_allowed(db:Session,canvas:ModelCanvasRecord,eid:str|None):
    if not eid:return
    e=db.get(Entity,eid)
    if e is None:raise ValueError('bound_entity_id must reference an existing Core entity.')
    if e.entity_type=='model' and eid!=canvas.model_entity_id:raise ValueError('Canvas nodes cannot bind a different model.')
    if e.entity_type=='model-version':_version(db,eid,canvas.model_entity_id)
    if e.entity_type=='variable':
        r=db.get(ResearchVariableRecord,eid)
        if r is None or r.model_entity_id!=canvas.model_entity_id:raise ValueError('Variable belongs to a different model.')
    if e.entity_type=='parameter':
        r=db.get(ResearchParameterRecord,eid)
        if r is None or r.model_entity_id!=canvas.model_entity_id:raise ValueError('Parameter belongs to a different model.')
    if e.entity_type=='scenario':
        r=db.get(ResearchScenarioRecord,eid)
        if r is None or r.project_entity_id!=canvas.project_entity_id:raise ValueError('Scenario belongs to a different project.')

def add_node(db:Session,visual_entity_id:str,p:dict[str,Any]):
    canvas=_require(db,visual_entity_id);kind=str(p.get('node_kind') or 'component')
    if kind not in NODE_KINDS:raise ValueError('Unsupported node_kind.')
    bound=p.get('bound_entity_id');_bound_allowed(db,canvas,bound)
    row=ModelCanvasNodeRecord(visual_entity_id=visual_entity_id,node_key=str(p.get('node_key') or kind),node_kind=kind,semantic_role=str(p.get('semantic_role') or ('parameter' if kind=='parameter' else ('variable' if kind=='variable' else 'context'))),bound_entity_id=bound,label=str(p.get('label') or p.get('node_key') or kind),unit=p.get('unit'),position_hint_json=dict(p.get('position_hint') or {}),interaction_json=dict(p.get('interaction') or {}),metadata_json=dict(p.get('metadata') or {}));db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Canvas node key already exists.') from exc
    return _ser(row)

def add_edge(db:Session,visual_entity_id:str,p:dict[str,Any]):
    _require(db,visual_entity_id);src=db.get(ModelCanvasNodeRecord,str(p.get('source_node_id') or ''));dst=db.get(ModelCanvasNodeRecord,str(p.get('target_node_id') or ''))
    if src is None or dst is None or src.visual_entity_id!=visual_entity_id or dst.visual_entity_id!=visual_entity_id:raise ValueError('Canvas edge endpoints must belong to this canvas.')
    kind=str(p.get('edge_kind') or 'dependency')
    if kind not in EDGE_KINDS:raise ValueError('Unsupported edge_kind.')
    row=ModelCanvasEdgeRecord(visual_entity_id=visual_entity_id,source_node_id=src.id,target_node_id=dst.id,edge_kind=kind,directed=bool(p.get('directed',True)),label=p.get('label'),bound_relation_id=p.get('bound_relation_id'),metadata_json=dict(p.get('metadata') or {}));db.add(row);db.commit();db.refresh(row);return _ser(row)

def add_control(db:Session,visual_entity_id:str,p:dict[str,Any]):
    canvas=_require(db,visual_entity_id);kind=str(p.get('control_kind') or 'input')
    if kind not in CONTROL_KINDS:raise ValueError('Unsupported control_kind.')
    dtype=str(p.get('data_type') or 'number')
    if dtype not in DATA_TYPES:raise ValueError('Unsupported data_type.')
    nid=p.get('node_id')
    if nid:
        n=db.get(ModelCanvasNodeRecord,nid)
        if n is None or n.visual_entity_id!=visual_entity_id:raise ValueError('node_id must reference a node in this canvas.')
    bound=p.get('bound_entity_id');_bound_allowed(db,canvas,bound)
    handoff=dict(p.get('handoff') or {})
    if handoff.get('execute_by_core') is True:raise ValueError('Platform Core cannot execute model-canvas controls.')
    row=ModelCanvasControlRecord(visual_entity_id=visual_entity_id,control_key=str(p.get('control_key') or kind),control_kind=kind,node_id=nid,bound_entity_id=bound,label=str(p.get('label') or p.get('control_key') or kind),data_type=dtype,unit=p.get('unit'),default_value_json=p.get('default_value'),bounds_json=dict(p.get('bounds') or {}),allowed_values_json=list(p.get('allowed_values') or []),handoff_json=handoff,metadata_json=dict(p.get('metadata') or {}));db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Canvas control key already exists.') from exc
    return _ser(row)

def save_state(db:Session,visual_entity_id:str,p:dict[str,Any]):
    canvas=_require(db,visual_entity_id);sid=p.get('scenario_entity_id');rid=p.get('model_run_entity_id')
    if sid:_bound_allowed(db,canvas,sid)
    if rid:
        e=db.get(Entity,rid);run=db.get(ResearchModelRunRecord,rid)
        if e is None or e.entity_type!='model-run' or run is None:raise ValueError('model_run_entity_id must reference a research model run.')
    values=dict(p.get('values') or {});canonical={'scenario_entity_id':sid,'model_run_entity_id':rid,'values':values,'provenance':dict(p.get('provenance') or {})}
    row=ModelCanvasStateRecord(visual_entity_id=visual_entity_id,state_key=str(p.get('state_key') or 'state'),name=str(p.get('name') or p.get('state_key') or 'State'),scenario_entity_id=sid,model_run_entity_id=rid,values_json=values,provenance_json=dict(p.get('provenance') or {}),state_hash=_hash(canonical),immutable=True,created_by=str(p.get('created_by') or 'operator'));db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Canvas state key already exists; states are immutable.') from exc
    return _ser(row)

def add_view(db:Session,visual_entity_id:str,p:dict[str,Any]):
    _require(db,visual_entity_id)
    def ids_ok(model,ids):return all((r:=db.get(model,x)) is not None and r.visual_entity_id==visual_entity_id for x in ids)
    nodes=list(p.get('node_ids') or []);edges=list(p.get('edge_ids') or []);controls=list(p.get('control_ids') or [])
    if not ids_ok(ModelCanvasNodeRecord,nodes) or not ids_ok(ModelCanvasEdgeRecord,edges) or not ids_ok(ModelCanvasControlRecord,controls):raise ValueError('Saved-view references must belong to this canvas.')
    row=ModelCanvasViewRecord(visual_entity_id=visual_entity_id,view_key=str(p.get('view_key') or 'default'),name=str(p.get('name') or 'Canvas view'),node_ids_json=nodes,edge_ids_json=edges,control_ids_json=controls,filters_json=dict(p.get('filters') or {}),layout_intent_json=dict(p.get('layout_intent') or {}),metadata_json=dict(p.get('metadata') or {}));db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Canvas view key already exists.') from exc
    return _ser(row)

def validate_structure(db:Session,visual_entity_id:str,*,public_only=False):
    canvas=_require(db,visual_entity_id)
    if public_only:_public(db,visual_entity_id)
    nodes=db.scalars(select(ModelCanvasNodeRecord).where(ModelCanvasNodeRecord.visual_entity_id==visual_entity_id)).all();edges=db.scalars(select(ModelCanvasEdgeRecord).where(ModelCanvasEdgeRecord.visual_entity_id==visual_entity_id)).all();controls=db.scalars(select(ModelCanvasControlRecord).where(ModelCanvasControlRecord.visual_entity_id==visual_entity_id)).all();states=db.scalars(select(ModelCanvasStateRecord).where(ModelCanvasStateRecord.visual_entity_id==visual_entity_id)).all();errors=[];warnings=[]
    if not nodes:warnings.append('canvas_has_no_nodes')
    node_ids={x.id for x in nodes}
    for e in edges:
        if e.source_node_id not in node_ids or e.target_node_id not in node_ids:errors.append(f'cross_canvas_or_orphan_edge:{e.id}')
    for c in controls:
        if c.node_id and c.node_id not in node_ids:errors.append(f'orphan_control_node:{c.id}')
        if (c.handoff_json or {}).get('execute_by_core') is True:errors.append(f'forbidden_core_execution:{c.id}')
    return {'valid':not errors,'counts':{'nodes':len(nodes),'edges':len(edges),'controls':len(controls),'states':len(states)},'errors':errors,'warnings':sorted(set(warnings)),'structural_only':True,'model_execution_performed':False,'numerical_computation_performed':False,'layout_execution_performed':False,'truth_promotion_performed':False}

def compile_specification(db:Session,visual_entity_id:str,p:dict[str,Any]):
    canvas=_require(db,visual_entity_id);kind=str(p.get('spec_kind') or 'diagram')
    if kind not in SPEC_KINDS:raise ValueError('Model-canvas spec_kind must be diagram, composite, or network.')
    key=str(p.get('spec_key') or 'model-canvas-default');existing=db.scalars(select(VisualizationSpecificationRecord).where(VisualizationSpecificationRecord.visual_entity_id==visual_entity_id,VisualizationSpecificationRecord.spec_key==key)).all();rev=int(p.get('revision') or (max([x.revision for x in existing],default=0)+1))
    nodes=db.scalars(select(ModelCanvasNodeRecord).where(ModelCanvasNodeRecord.visual_entity_id==visual_entity_id).order_by(ModelCanvasNodeRecord.created_at)).all();edges=db.scalars(select(ModelCanvasEdgeRecord).where(ModelCanvasEdgeRecord.visual_entity_id==visual_entity_id).order_by(ModelCanvasEdgeRecord.created_at)).all();controls=db.scalars(select(ModelCanvasControlRecord).where(ModelCanvasControlRecord.visual_entity_id==visual_entity_id).order_by(ModelCanvasControlRecord.created_at)).all()
    return visualization_registry.create_specification(db,{'visual_entity_id':visual_entity_id,'spec_key':key,'revision':rev,'spec_version':'1.0','spec_kind':kind,'title':p.get('title') or 'Interactive model canvas','preferred_renderer_key':p.get('preferred_renderer_key'),'renderer_policy':str(p.get('renderer_policy') or 'compatible'),'encoding':{'model_entity_id':canvas.model_entity_id,'model_version_entity_id':canvas.model_version_entity_id,'nodes':[{'id':n.id,'key':n.node_key,'kind':n.node_kind,'role':n.semantic_role,'bound_entity_id':n.bound_entity_id,'label':n.label,'unit':n.unit,'position_hint':n.position_hint_json} for n in nodes],'edges':[{'id':e.id,'source':e.source_node_id,'target':e.target_node_id,'kind':e.edge_kind,'directed':e.directed,'label':e.label} for e in edges],'controls':[{'id':c.id,'key':c.control_key,'kind':c.control_kind,'bound_entity_id':c.bound_entity_id,'data_type':c.data_type,'unit':c.unit,'bounds':c.bounds_json,'handoff':c.handoff_json} for c in controls]},'interaction':{'inspect':True,'configure_external_execution_request':True,'saved_states':True,'controls_are_intents_not_execution':True},'accessibility':{'text_summary_required':True,'node_labels_required':True,'control_labels_required':True},'layout_constraints':{'runtime_owns_layout':True,'core_coordinates_required':False,'canvas_layout':'interactive-runtime',**dict(p.get('layout_constraints') or {})},'export':{'semantic_bundle':True,'state_hashes':True,'external_execution_handoff':True},'metadata':{'interactive_model_canvas_v234':True,'model_execution_by_core':False,'numerical_computation_by_core':False,'layout_execution_by_core':False,**dict(p.get('metadata') or {})},'created_by':str(p.get('created_by') or 'operator')})

def bundle(db:Session,visual_entity_id:str,*,public_only=False):
    return {'canvas':read_canvas(db,visual_entity_id,public_only=public_only),'visual_reasoning':visual_reasoning.bundle(db,visual_entity_id,public_only=public_only),'nodes':[_ser(x) for x in db.scalars(select(ModelCanvasNodeRecord).where(ModelCanvasNodeRecord.visual_entity_id==visual_entity_id).order_by(ModelCanvasNodeRecord.created_at)).all()],'edges':[_ser(x) for x in db.scalars(select(ModelCanvasEdgeRecord).where(ModelCanvasEdgeRecord.visual_entity_id==visual_entity_id).order_by(ModelCanvasEdgeRecord.created_at)).all()],'controls':[_ser(x) for x in db.scalars(select(ModelCanvasControlRecord).where(ModelCanvasControlRecord.visual_entity_id==visual_entity_id).order_by(ModelCanvasControlRecord.created_at)).all()],'states':[_ser(x) for x in db.scalars(select(ModelCanvasStateRecord).where(ModelCanvasStateRecord.visual_entity_id==visual_entity_id).order_by(ModelCanvasStateRecord.created_at)).all()],'views':[_ser(x) for x in db.scalars(select(ModelCanvasViewRecord).where(ModelCanvasViewRecord.visual_entity_id==visual_entity_id).order_by(ModelCanvasViewRecord.created_at)).all()],'specifications':visualization_registry.list_specifications(db,visual_entity_id=visual_entity_id,public_only=public_only,limit=1000,offset=0)[0],'validation':validate_structure(db,visual_entity_id,public_only=public_only)}
