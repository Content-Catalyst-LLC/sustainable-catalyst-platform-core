from __future__ import annotations
from typing import Any
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Entity, ResearchScenarioRecord, ResearchParameterRecord, ResearchResultRecord, ResearchVariableRecord,
    ScenarioLandscapeRecord, ScenarioLandscapeScenarioRecord, ScenarioLandscapeDimensionRecord,
    ScenarioLandscapeValueRecord, ScenarioLandscapeViewRecord, VisualReasoningObjectRecord,
    VisualizationSpecificationRecord,
)
from . import visual_reasoning, visualization_registry

LANDSCAPE_STATES={"draft","review","published","archived"}
COMPARISON_MODES={"baseline-relative","peer","portfolio","envelope"}
DIMENSION_POLICIES={"explicit","source-bound","mixed"}
SCENARIO_ROLES={"baseline","alternative","reference","stress","sensitivity"}
DIMENSION_KINDS={"parameter","result","variable","metric","time","custom"}
PREFERENCE_DIRECTIONS={"higher-better","lower-better","target","neutral"}
SPEC_KINDS={"chart","composite","table"}


def _serialize(row):
    out={}
    for c in row.__table__.columns:
        v=getattr(row,c.name)
        if hasattr(v,'isoformat'): v=v.isoformat()
        out[c.name]=v
    return out


def _require(db:Session, visual_entity_id:str)->ScenarioLandscapeRecord:
    row=db.get(ScenarioLandscapeRecord,visual_entity_id)
    if row is None: raise HTTPException(status_code=404,detail="Scenario landscape not found.")
    return row


def _require_public(db:Session, visual_entity_id:str):
    e=db.get(Entity,visual_entity_id)
    if e is None or e.visibility!='public': raise HTTPException(status_code=404,detail="Scenario landscape not found.")


def _scenario_for_project(db:Session, scenario_id:str, project_id:str)->ResearchScenarioRecord:
    e=db.get(Entity,scenario_id); row=db.get(ResearchScenarioRecord,scenario_id)
    if e is None or e.entity_type!='scenario' or row is None: raise ValueError("scenario_entity_id must reference a research scenario.")
    if row.project_entity_id!=project_id: raise ValueError("scenario_entity_id must belong to the landscape research project.")
    return row


def readiness(db:Session)->dict[str,Any]:
    return {
      'counts':{
        'landscapes':db.scalar(select(func.count()).select_from(ScenarioLandscapeRecord)) or 0,
        'scenarios':db.scalar(select(func.count()).select_from(ScenarioLandscapeScenarioRecord)) or 0,
        'dimensions':db.scalar(select(func.count()).select_from(ScenarioLandscapeDimensionRecord)) or 0,
        'values':db.scalar(select(func.count()).select_from(ScenarioLandscapeValueRecord)) or 0,
        'views':db.scalar(select(func.count()).select_from(ScenarioLandscapeViewRecord)) or 0,
      },
      'comparison_modes':sorted(COMPARISON_MODES),'scenario_roles':sorted(SCENARIO_ROLES),
      'dimension_kinds':sorted(DIMENSION_KINDS),'visual_kind':'scenario-landscape',
      'research_scenarios_reused':True,'visual_reasoning_integrated':True,'visualization_registry_integrated':True,
      'renderer_neutral':True,'layout_engine_in_core':False,'scenario_execution_by_core':False,'model_execution_by_core':False,
      'unit_conversion_by_core':False,'ranking_by_core':False,'optimization_by_core':False,
      'automatic_truth_promotion':False,
    }


def create_landscape(db:Session,payload:dict[str,Any],*,release:str)->dict[str,Any]:
    project_id=str(payload.get('project_entity_id') or '')
    project=db.get(Entity,project_id)
    if project is None or project.entity_type!='research-project': raise ValueError('project_entity_id must reference a research-project.')
    state=str(payload.get('landscape_state') or 'draft'); mode=str(payload.get('comparison_mode') or 'baseline-relative'); policy=str(payload.get('dimension_policy') or 'explicit')
    if state not in LANDSCAPE_STATES: raise ValueError('Unsupported landscape_state.')
    if mode not in COMPARISON_MODES: raise ValueError('Unsupported comparison_mode.')
    if policy not in DIMENSION_POLICIES: raise ValueError('Unsupported dimension_policy.')
    baseline=payload.get('baseline_scenario_entity_id')
    if baseline: _scenario_for_project(db,str(baseline),project_id)
    visual=visual_reasoning.create_object(db,name=str(payload.get('name') or 'Scenario landscape'),slug=payload.get('slug'),description=payload.get('description'),entity_id=payload.get('entity_id'),visibility=str(payload.get('visibility') or 'public'),entity_status=str(payload.get('status') or 'active'),visual_kind='scenario-landscape',reasoning_purpose=str(payload.get('reasoning_purpose') or 'compare'),semantic_state=state,coordinate_space='abstract',project_entity_id=project_id,primary_subject_entity_id=payload.get('primary_subject_entity_id'),lens=dict(payload.get('lens') or {}),filters=dict(payload.get('filters') or {}),assumptions=list(payload.get('assumptions') or []),metadata={**dict(payload.get('metadata') or {}),'scenario_landscape_release':release},release=release)
    row=ScenarioLandscapeRecord(visual_entity_id=visual['id'],project_entity_id=project_id,baseline_scenario_entity_id=baseline,comparison_mode=mode,landscape_state=state,objective=payload.get('objective'),dimension_policy=policy,assumptions_json=list(payload.get('assumptions') or []),metadata_json=dict(payload.get('metadata') or {}),created_by=str(payload.get('created_by') or 'operator'))
    db.add(row); db.commit(); db.refresh(row)
    if baseline:
        add_scenario(db,row.visual_entity_id,{'scenario_entity_id':baseline,'scenario_role':'baseline','display_label':payload.get('baseline_label')})
    return read_landscape(db,row.visual_entity_id)


def read_landscape(db:Session,visual_entity_id:str,*,public_only:bool=False)->dict[str,Any]:
    row=_require(db,visual_entity_id)
    if public_only:_require_public(db,visual_entity_id)
    item=_serialize(row); e=db.get(Entity,visual_entity_id); v=db.get(VisualReasoningObjectRecord,visual_entity_id)
    item['entity']={'id':e.id,'name':e.name,'description':e.description,'visibility':e.visibility,'status':e.status} if e else None
    item['visual_reasoning']=_serialize(v) if v else None
    return item


def list_landscapes(db:Session,*,public_only=False,limit=100,offset=0):
    stmt=select(ScenarioLandscapeRecord).join(Entity,Entity.id==ScenarioLandscapeRecord.visual_entity_id); count=select(func.count()).select_from(ScenarioLandscapeRecord).join(Entity,Entity.id==ScenarioLandscapeRecord.visual_entity_id)
    if public_only: stmt=stmt.where(Entity.visibility=='public'); count=count.where(Entity.visibility=='public')
    total=int(db.scalar(count) or 0); rows=db.scalars(stmt.order_by(ScenarioLandscapeRecord.created_at.desc()).limit(limit).offset(offset)).all()
    return [read_landscape(db,r.visual_entity_id,public_only=public_only) for r in rows],total


def add_scenario(db:Session,visual_entity_id:str,payload:dict[str,Any])->dict[str,Any]:
    landscape=_require(db,visual_entity_id); sid=str(payload.get('scenario_entity_id') or ''); _scenario_for_project(db,sid,landscape.project_entity_id)
    role=str(payload.get('scenario_role') or 'alternative')
    if role not in SCENARIO_ROLES: raise ValueError('Unsupported scenario_role.')
    if role=='baseline':
        existing=db.scalar(select(ScenarioLandscapeScenarioRecord).where(ScenarioLandscapeScenarioRecord.visual_entity_id==visual_entity_id,ScenarioLandscapeScenarioRecord.scenario_role=='baseline'))
        if existing and existing.scenario_entity_id!=sid: raise ValueError('Scenario landscape can have only one baseline scenario.')
        landscape.baseline_scenario_entity_id=sid
    row=ScenarioLandscapeScenarioRecord(visual_entity_id=visual_entity_id,scenario_entity_id=sid,scenario_role=role,display_label=payload.get('display_label'),order_index=int(payload.get('order_index',0)),metadata_json=dict(payload.get('metadata') or {}))
    db.add(row)
    try: db.commit();db.refresh(row)
    except IntegrityError as exc: db.rollback();raise HTTPException(status_code=409,detail='Scenario already belongs to landscape.') from exc
    return _serialize(row)


def add_dimension(db:Session,visual_entity_id:str,payload:dict[str,Any])->dict[str,Any]:
    _require(db,visual_entity_id); kind=str(payload.get('dimension_kind') or 'metric'); pref=str(payload.get('preference_direction') or 'neutral')
    if kind not in DIMENSION_KINDS: raise ValueError('Unsupported dimension_kind.')
    if pref not in PREFERENCE_DIRECTIONS: raise ValueError('Unsupported preference_direction.')
    src=payload.get('source_entity_id')
    if src:
        e=db.get(Entity,str(src)); allowed={'parameter','result','variable'}
        if e is None or e.entity_type not in allowed: raise ValueError('source_entity_id must reference a parameter, result, or variable.')
        if kind in {'parameter','result','variable'} and e.entity_type!=kind: raise ValueError('dimension_kind must match source entity type.')
    row=ScenarioLandscapeDimensionRecord(visual_entity_id=visual_entity_id,dimension_key=str(payload.get('dimension_key') or 'dimension'),dimension_kind=kind,source_entity_id=src,label=str(payload.get('label') or payload.get('dimension_key') or 'Dimension'),unit=payload.get('unit'),preference_direction=pref,order_index=int(payload.get('order_index',0)),metadata_json=dict(payload.get('metadata') or {}))
    db.add(row)
    try: db.commit();db.refresh(row)
    except IntegrityError as exc: db.rollback();raise HTTPException(status_code=409,detail='Scenario-landscape dimension key already exists.') from exc
    return _serialize(row)


def set_value(db:Session,visual_entity_id:str,payload:dict[str,Any])->dict[str,Any]:
    landscape=_require(db,visual_entity_id); sid=str(payload.get('scenario_entity_id') or ''); _scenario_for_project(db,sid,landscape.project_entity_id)
    member=db.scalar(select(ScenarioLandscapeScenarioRecord).where(ScenarioLandscapeScenarioRecord.visual_entity_id==visual_entity_id,ScenarioLandscapeScenarioRecord.scenario_entity_id==sid))
    if member is None: raise ValueError('scenario_entity_id must first be added to this landscape.')
    did=str(payload.get('dimension_id') or ''); dim=db.get(ScenarioLandscapeDimensionRecord,did)
    if dim is None or dim.visual_entity_id!=visual_entity_id: raise ValueError('dimension_id must belong to this landscape.')
    numeric=payload.get('numeric_value'); numeric=None if numeric is None else float(numeric)
    low=payload.get('lower_bound'); high=payload.get('upper_bound'); low=None if low is None else float(low); high=None if high is None else float(high)
    if low is not None and high is not None and low>high: raise ValueError('lower_bound cannot exceed upper_bound.')
    unit=payload.get('unit') or dim.unit
    existing=db.scalar(select(ScenarioLandscapeValueRecord).where(ScenarioLandscapeValueRecord.visual_entity_id==visual_entity_id,ScenarioLandscapeValueRecord.scenario_entity_id==sid,ScenarioLandscapeValueRecord.dimension_id==did))
    if existing:
        existing.numeric_value=numeric;existing.value_json=payload.get('value');existing.unit=unit;existing.lower_bound=low;existing.upper_bound=high;existing.uncertainty_json=dict(payload.get('uncertainty') or {});existing.provenance_json=dict(payload.get('provenance') or {});existing.metadata_json=dict(payload.get('metadata') or {});row=existing
    else:
        row=ScenarioLandscapeValueRecord(visual_entity_id=visual_entity_id,scenario_entity_id=sid,dimension_id=did,numeric_value=numeric,value_json=payload.get('value'),unit=unit,lower_bound=low,upper_bound=high,uncertainty_json=dict(payload.get('uncertainty') or {}),provenance_json=dict(payload.get('provenance') or {}),metadata_json=dict(payload.get('metadata') or {}));db.add(row)
    db.commit();db.refresh(row);return _serialize(row)


def add_view(db:Session,visual_entity_id:str,payload:dict[str,Any])->dict[str,Any]:
    _require(db,visual_entity_id); scenario_ids=[str(x) for x in payload.get('scenario_ids',[])]; dimension_ids=[str(x) for x in payload.get('dimension_ids',[])]
    for sid in scenario_ids:
        if db.scalar(select(ScenarioLandscapeScenarioRecord.id).where(ScenarioLandscapeScenarioRecord.visual_entity_id==visual_entity_id,ScenarioLandscapeScenarioRecord.scenario_entity_id==sid)) is None: raise ValueError('Every scenario_id must belong to this landscape.')
    for did in dimension_ids:
        d=db.get(ScenarioLandscapeDimensionRecord,did)
        if d is None or d.visual_entity_id!=visual_entity_id: raise ValueError('Every dimension_id must belong to this landscape.')
    spec_id=payload.get('specification_id')
    if spec_id:
        spec=db.get(VisualizationSpecificationRecord,str(spec_id))
        if spec is None or spec.visual_entity_id!=visual_entity_id: raise ValueError('specification_id must belong to this landscape.')
    row=ScenarioLandscapeViewRecord(visual_entity_id=visual_entity_id,view_key=str(payload.get('view_key') or 'view'),name=str(payload.get('name') or payload.get('view_key') or 'View'),scenario_ids_json=scenario_ids,dimension_ids_json=dimension_ids,filters_json=dict(payload.get('filters') or {}),layout_intent_json=dict(payload.get('layout_intent') or {}),specification_id=spec_id,metadata_json=dict(payload.get('metadata') or {}));db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Scenario-landscape view key already exists.') from exc
    return _serialize(row)


def comparison_summary(db:Session,visual_entity_id:str,*,public_only=False)->dict[str,Any]:
    landscape=_require(db,visual_entity_id)
    if public_only:_require_public(db,visual_entity_id)
    members=db.scalars(select(ScenarioLandscapeScenarioRecord).where(ScenarioLandscapeScenarioRecord.visual_entity_id==visual_entity_id)).all();dims=db.scalars(select(ScenarioLandscapeDimensionRecord).where(ScenarioLandscapeDimensionRecord.visual_entity_id==visual_entity_id)).all();values=db.scalars(select(ScenarioLandscapeValueRecord).where(ScenarioLandscapeValueRecord.visual_entity_id==visual_entity_id)).all()
    baseline=landscape.baseline_scenario_entity_id
    by={(v.scenario_entity_id,v.dimension_id):v for v in values}; matrix={}; deltas={}
    for m in members:
        matrix[m.scenario_entity_id]={}
        for d in dims:
            v=by.get((m.scenario_entity_id,d.id)); matrix[m.scenario_entity_id][d.dimension_key]=None if not v else {'numeric_value':v.numeric_value,'value':v.value_json,'unit':v.unit,'lower_bound':v.lower_bound,'upper_bound':v.upper_bound,'uncertainty':v.uncertainty_json}
            if baseline and m.scenario_entity_id!=baseline and v and v.numeric_value is not None:
                b=by.get((baseline,d.id))
                if b and b.numeric_value is not None and (b.unit or d.unit)==(v.unit or d.unit): deltas.setdefault(m.scenario_entity_id,{})[d.dimension_key]={'absolute_delta':v.numeric_value-b.numeric_value,'unit':v.unit or d.unit}
    return {'visual_entity_id':visual_entity_id,'baseline_scenario_entity_id':baseline,'matrix':matrix,'baseline_deltas':deltas,'scenario_count':len(members),'dimension_count':len(dims),'value_count':len(values),'direct_numeric_comparison_only':True,'unit_conversion_performed':False,'ranking_performed':False,'optimization_performed':False,'scenario_execution_performed':False}


def validate_structure(db:Session,visual_entity_id:str,*,public_only=False)->dict[str,Any]:
    landscape=_require(db,visual_entity_id)
    if public_only:_require_public(db,visual_entity_id)
    members=db.scalars(select(ScenarioLandscapeScenarioRecord).where(ScenarioLandscapeScenarioRecord.visual_entity_id==visual_entity_id)).all();dims=db.scalars(select(ScenarioLandscapeDimensionRecord).where(ScenarioLandscapeDimensionRecord.visual_entity_id==visual_entity_id)).all();values=db.scalars(select(ScenarioLandscapeValueRecord).where(ScenarioLandscapeValueRecord.visual_entity_id==visual_entity_id)).all();errors=[];warnings=[]
    if not members:warnings.append('landscape_has_no_scenarios')
    if not dims:warnings.append('landscape_has_no_dimensions')
    if landscape.comparison_mode=='baseline-relative' and not landscape.baseline_scenario_entity_id:warnings.append('baseline_relative_without_baseline')
    member_ids={m.scenario_entity_id for m in members};dim_ids={d.id for d in dims}
    if landscape.baseline_scenario_entity_id and landscape.baseline_scenario_entity_id not in member_ids:errors.append('baseline_not_in_landscape')
    for v in values:
        if v.scenario_entity_id not in member_ids or v.dimension_id not in dim_ids:errors.append(f'orphan_value:{v.id}')
        if v.lower_bound is not None and v.upper_bound is not None and v.lower_bound>v.upper_bound:errors.append(f'invalid_uncertainty_bounds:{v.id}')
    return {'valid':not errors,'counts':{'scenarios':len(members),'dimensions':len(dims),'values':len(values)},'errors':errors,'warnings':sorted(set(warnings)),'structural_only':True,'scenario_execution_performed':False,'model_execution_performed':False,'unit_conversion_performed':False,'ranking_performed':False,'optimization_performed':False,'truth_promotion_performed':False}


def compile_specification(db:Session,visual_entity_id:str,payload:dict[str,Any])->dict[str,Any]:
    landscape=_require(db,visual_entity_id);kind=str(payload.get('spec_kind') or 'chart')
    if kind not in SPEC_KINDS:raise ValueError('Scenario-landscape spec_kind must be chart, composite, or table.')
    key=str(payload.get('spec_key') or 'scenario-landscape-default');existing=db.scalars(select(VisualizationSpecificationRecord).where(VisualizationSpecificationRecord.visual_entity_id==visual_entity_id,VisualizationSpecificationRecord.spec_key==key)).all();revision=int(payload.get('revision') or (max([x.revision for x in existing],default=0)+1));dims=db.scalars(select(ScenarioLandscapeDimensionRecord).where(ScenarioLandscapeDimensionRecord.visual_entity_id==visual_entity_id).order_by(ScenarioLandscapeDimensionRecord.order_index)).all()
    return visualization_registry.create_specification(db,{'visual_entity_id':visual_entity_id,'spec_key':key,'revision':revision,'spec_version':'1.0','spec_kind':kind,'title':payload.get('title') or 'Scenario landscape','preferred_renderer_key':payload.get('preferred_renderer_key'),'renderer_policy':str(payload.get('renderer_policy') or 'compatible'),'encoding':{'scenario_source':'scenario_landscape_scenarios','value_source':'scenario_landscape_values','baseline_scenario_entity_id':landscape.baseline_scenario_entity_id,'dimensions':[{'id':d.id,'key':d.dimension_key,'kind':d.dimension_kind,'label':d.label,'unit':d.unit,'preference_direction':d.preference_direction} for d in dims],'uncertainty_fields':['lower_bound','upper_bound','uncertainty_json']},'interaction':{'inspect':True,'compare':True,'filter_scenarios':True,'filter_dimensions':True},'accessibility':{'text_summary_required':True,'scenario_labels_required':True,'uncertainty_text_required':True},'layout_constraints':{'runtime_owns_layout':True,'core_coordinates_required':False,'scenario_landscape_layout':'runtime-selectable',**dict(payload.get('layout_constraints') or {})},'export':{'semantic_bundle':True,'comparison_summary_available':True,'snapshot_compatible':True},'metadata':{'scenario_landscape_v233':True,'comparison_mode':landscape.comparison_mode,'scenario_execution_by_core':False,'ranking_by_core':False,'optimization_by_core':False,**dict(payload.get('metadata') or {})},'created_by':str(payload.get('created_by') or 'operator')})


def bundle(db:Session,visual_entity_id:str,*,public_only=False)->dict[str,Any]:
    base=read_landscape(db,visual_entity_id,public_only=public_only)
    return {'landscape':base,'visual_reasoning':visual_reasoning.bundle(db,visual_entity_id,public_only=public_only),'scenarios':[_serialize(x) for x in db.scalars(select(ScenarioLandscapeScenarioRecord).where(ScenarioLandscapeScenarioRecord.visual_entity_id==visual_entity_id).order_by(ScenarioLandscapeScenarioRecord.order_index,ScenarioLandscapeScenarioRecord.created_at)).all()],'dimensions':[_serialize(x) for x in db.scalars(select(ScenarioLandscapeDimensionRecord).where(ScenarioLandscapeDimensionRecord.visual_entity_id==visual_entity_id).order_by(ScenarioLandscapeDimensionRecord.order_index,ScenarioLandscapeDimensionRecord.created_at)).all()],'values':[_serialize(x) for x in db.scalars(select(ScenarioLandscapeValueRecord).where(ScenarioLandscapeValueRecord.visual_entity_id==visual_entity_id).order_by(ScenarioLandscapeValueRecord.created_at)).all()],'views':[_serialize(x) for x in db.scalars(select(ScenarioLandscapeViewRecord).where(ScenarioLandscapeViewRecord.visual_entity_id==visual_entity_id).order_by(ScenarioLandscapeViewRecord.created_at)).all()],'specifications':visualization_registry.list_specifications(db,visual_entity_id=visual_entity_id,public_only=public_only,limit=1000,offset=0)[0],'comparison_summary':comparison_summary(db,visual_entity_id,public_only=public_only),'validation':validate_structure(db,visual_entity_id,public_only=public_only)}
