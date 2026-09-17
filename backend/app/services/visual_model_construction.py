from __future__ import annotations
import hashlib,json
from datetime import datetime
from sqlalchemy import func,select,inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (
    ModelCanvasRecord, VisualModelConstructionRecord, VisualModelComponentRecord, VisualModelRelationshipRecord,
    VisualModelAssumptionRecord, VisualModelConstraintRecord, VisualModelInterventionRecord, VisualModelHandoffRecord, VisualModelSnapshotRecord,
)
CONTRACT="sc.visual-runtime.model-construction.v1"
COMPONENT_KINDS={"variable","parameter","constant","state","input","output","stock","flow","decision","indicator","custom"}
RELATIONSHIP_KINDS={"equation","causal","flow","dependency","identity","logical","lookup","aggregation","transition","custom"}
HANDOFF_TARGETS={"Lab","Workbench","Decision Studio","Site Intelligence","Catalyst Data","external"}
FORBIDDEN={"solve_by_core","equation_execution_by_core","constraint_optimization_by_core","simulation_execution_by_core","model_execution_by_core","automatic_parameter_estimation","automatic_model_inference"}

def _ser(row):
    out={}
    for a in sa_inspect(row).mapper.column_attrs:
        v=getattr(row,a.key)
        if isinstance(v,datetime):v=v.isoformat()
        out[a.key]=v
    for k in list(out):
        if k.endswith('_json'):out[k[:-5]]=out.pop(k)
    return out
def _hash(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def _reject(p):
    bad=sorted(k for k in FORBIDDEN if p.get(k) not in (None,False))
    if bad:raise ValueError('Visual Model Construction is declarative; Core does not execute: '+', '.join(bad))
def boundaries():return {
 'visual_model_construction_registry_by_core':True,'visual_model_component_registry_by_core':True,'visual_model_relationship_registry_by_core':True,
 'visual_model_assumption_registry_by_core':True,'visual_model_constraint_registry_by_core':True,'visual_model_intervention_registry_by_core':True,
 'visual_model_handoff_registry_by_core':True,'immutable_visual_model_snapshots_by_core':True,
 'equation_execution_by_core':False,'constraint_optimization_by_core':False,'simulation_execution_by_core':False,'model_execution_by_core':False,
 'automatic_parameter_estimation':False,'automatic_model_inference':False,'automatic_visual_truth_promotion':False}
def readiness(db):
    c=lambda cls:db.scalar(select(func.count()).select_from(cls)) or 0
    return {'release':'2.66.0','contract':CONTRACT,'counts':{'constructions':c(VisualModelConstructionRecord),'components':c(VisualModelComponentRecord),'relationships':c(VisualModelRelationshipRecord),'assumptions':c(VisualModelAssumptionRecord),'constraints':c(VisualModelConstraintRecord),'interventions':c(VisualModelInterventionRecord),'handoffs':c(VisualModelHandoffRecord),'snapshots':c(VisualModelSnapshotRecord)},**boundaries()}
def _construction(db,cid):
    x=db.get(VisualModelConstructionRecord,cid)
    if not x:raise ValueError('Visual model construction not found.')
    return x
def create_construction(db:Session,canvas_id:str,p:dict):
    _reject(p);canvas=db.get(ModelCanvasRecord,canvas_id)
    if not canvas:raise ValueError('Model canvas not found.')
    row=VisualModelConstructionRecord(canvas_visual_entity_id=canvas_id,construction_key=p['construction_key'],name=p['name'],model_kind=p.get('model_kind','system'),purpose=p.get('purpose'),status=p.get('status','draft'),visibility=p.get('visibility','private'),specification_json=p.get('specification',{}),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)
def create_component(db,cid,p):
    _reject(p);_construction(db,cid);kind=p['component_kind']
    if kind not in COMPONENT_KINDS:raise ValueError('unsupported component_kind.')
    row=VisualModelComponentRecord(construction_id=cid,component_key=p['component_key'],component_kind=kind,label=p['label'],symbol=p.get('symbol'),unit=p.get('unit'),bound_entity_id=p.get('bound_entity_id'),role=p.get('role','state'),default_value_json=p.get('default_value'),domain_json=p.get('domain',{}),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)
def _component(db,cid,xid):
    x=db.get(VisualModelComponentRecord,xid)
    if not x or x.construction_id!=cid:raise ValueError('component must belong to the construction.')
    return x
def create_relationship(db,cid,p):
    _reject(p);_construction(db,cid);kind=p['relationship_kind']
    if kind not in RELATIONSHIP_KINDS:raise ValueError('unsupported relationship_kind.')
    s=p.get('source_component_id');t=p.get('target_component_id')
    if s:_component(db,cid,s)
    if t:_component(db,cid,t)
    if not p.get('expression') and not p.get('relationship_spec'):raise ValueError('relationship requires expression or relationship_spec.')
    row=VisualModelRelationshipRecord(construction_id=cid,relationship_key=p['relationship_key'],relationship_kind=kind,source_component_id=s,target_component_id=t,expression=p.get('expression'),relationship_spec_json=p.get('relationship_spec',{}),provenance_json=p.get('provenance',{}))
    db.add(row);db.commit();db.refresh(row);return _ser(row)
def create_assumption(db,cid,p):
    _reject(p);_construction(db,cid);row=VisualModelAssumptionRecord(construction_id=cid,assumption_key=p['assumption_key'],statement=p['statement'],scope_json=p.get('scope',{}),evidence_json=p.get('evidence',{}),provenance_json=p.get('provenance',{}));db.add(row);db.commit();db.refresh(row);return _ser(row)
def create_constraint(db,cid,p):
    _reject(p);_construction(db,cid)
    if not p.get('expression') and not p.get('constraint_spec'):raise ValueError('constraint requires expression or constraint_spec.')
    row=VisualModelConstraintRecord(construction_id=cid,constraint_key=p['constraint_key'],constraint_kind=p.get('constraint_kind','bound'),expression=p.get('expression'),constraint_spec_json=p.get('constraint_spec',{}),provenance_json=p.get('provenance',{}));db.add(row);db.commit();db.refresh(row);return _ser(row)
def create_intervention(db,cid,p):
    _reject(p);_construction(db,cid);ids=p.get('target_component_ids',[])
    for x in ids:_component(db,cid,x)
    row=VisualModelInterventionRecord(construction_id=cid,intervention_key=p['intervention_key'],name=p['name'],target_component_ids_json=ids,intervention_spec_json=p.get('intervention_spec',{}),provenance_json=p.get('provenance',{}));db.add(row);db.commit();db.refresh(row);return _ser(row)
def create_handoff(db,cid,p):
    _reject(p);_construction(db,cid);target=p['target_product']
    if target not in HANDOFF_TARGETS:raise ValueError('unsupported target_product.')
    if p.get('externally_executed',True) is not True:raise ValueError('model handoffs must remain externally executed.')
    row=VisualModelHandoffRecord(construction_id=cid,target_product=target,purpose=p['purpose'],request_json=p.get('request',{}),response_ref=p.get('response_ref'),status=p.get('status','prepared'),externally_executed=True,provenance_json=p.get('provenance',{}));db.add(row);db.commit();db.refresh(row);return _ser(row)
def construction_bundle(db,cid,public_only=False):
    x=_construction(db,cid)
    if public_only and x.visibility!='public':raise ValueError('visual model construction is not public.')
    def rows(cls):return [_ser(r) for r in db.scalars(select(cls).where(cls.construction_id==cid)).all()]
    return {'contract':CONTRACT,'construction':_ser(x),'components':rows(VisualModelComponentRecord),'relationships':rows(VisualModelRelationshipRecord),'assumptions':rows(VisualModelAssumptionRecord),'constraints':rows(VisualModelConstraintRecord),'interventions':rows(VisualModelInterventionRecord),'handoffs':rows(VisualModelHandoffRecord),'snapshots':rows(VisualModelSnapshotRecord),'boundaries':boundaries()}
def create_snapshot(db,cid,p):
    _reject(p);state=construction_bundle(db,cid);state.pop('snapshots',None)
    prevs=db.scalars(select(VisualModelSnapshotRecord).where(VisualModelSnapshotRecord.construction_id==cid).order_by(VisualModelSnapshotRecord.revision.asc())).all();rev=len(prevs)+1;prev=prevs[-1].content_hash if prevs else None
    h=_hash({'revision':rev,'previous_snapshot_hash':prev,'state':state})
    row=VisualModelSnapshotRecord(construction_id=cid,revision=rev,content_hash=h,previous_snapshot_hash=prev,state_json=state,provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(row);db.commit();db.refresh(row);return _ser(row)
