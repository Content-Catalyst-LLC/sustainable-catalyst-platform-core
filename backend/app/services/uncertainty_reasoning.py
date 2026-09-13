from __future__ import annotations
from typing import Any
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Entity, ResearchModelRecord, ResearchModelVersionRecord, ResearchParameterRecord, ResearchScenarioRecord,
    ResearchModelRunRecord, ScenarioComputePlanRecord, ScenarioComputeCaseRecord, ScenarioComputeRequestRecord,
    UncertaintyDefinitionRecord, SensitivityStudyRecord, SensitivityFactorRecord, SensitivityResultRecord,
    EnsembleRecord, EnsembleMemberRecord, EnsembleStatisticRecord, VisualReasoningObjectRecord,
)
from . import visual_reasoning, visualization_registry

UNCERTAINTY_KINDS={"interval","distribution","empirical","categorical","qualitative"}
DISTRIBUTIONS={"normal","lognormal","uniform","triangular","beta","gamma","poisson","custom"}
STUDY_STATES={"draft","ready","running","completed","archived"}
STUDY_METHODS={"one-at-a-time","local-gradient","morris","sobol","variance-based","correlation","scenario-sweep","custom"}
SENSITIVITY_METRICS={"effect","elasticity","correlation","sobol-first","sobol-total","morris-mu-star","rank","custom"}
ENSEMBLE_STATES={"draft","ready","running","completed","archived"}
WEIGHTING_POLICIES={"equal","explicit","external","none"}
INCLUSION_STATES={"included","excluded","review"}
STATISTIC_KINDS={"mean","median","stddev","variance","quantile","min","max","probability","count","custom"}


def _ser(row):
    out={}
    for c in row.__table__.columns:
        v=getattr(row,c.name)
        if hasattr(v,"isoformat"): v=v.isoformat()
        out[c.name]=v
    return out


def _entity(db:Session, entity_id:str, expected:str|None=None):
    e=db.get(Entity,entity_id)
    if e is None or (expected and e.entity_type!=expected): raise ValueError(f"{expected or 'entity'} reference is invalid.")
    return e


def _model_version(db:Session, model_id:str, version_id:str):
    m=db.get(ResearchModelRecord,model_id); v=db.get(ResearchModelVersionRecord,version_id)
    if m is None or v is None: raise ValueError("model_entity_id/model_version_entity_id must reference research model records.")
    if v.model_entity_id!=model_id: raise ValueError("model_version_entity_id must belong to model_entity_id.")
    if not v.immutable: raise ValueError("model_version_entity_id must be immutable.")
    return m,v


def _public_visual(db:Session, visual_entity_id:str):
    e=db.get(Entity,visual_entity_id)
    if e is None or e.visibility!='public': raise HTTPException(status_code=404,detail='Reasoning object not found.')


def readiness(db:Session)->dict[str,Any]:
    return {
      'counts':{
        'uncertainty_definitions':db.scalar(select(func.count()).select_from(UncertaintyDefinitionRecord)) or 0,
        'sensitivity_studies':db.scalar(select(func.count()).select_from(SensitivityStudyRecord)) or 0,
        'sensitivity_factors':db.scalar(select(func.count()).select_from(SensitivityFactorRecord)) or 0,
        'sensitivity_results':db.scalar(select(func.count()).select_from(SensitivityResultRecord)) or 0,
        'ensembles':db.scalar(select(func.count()).select_from(EnsembleRecord)) or 0,
        'ensemble_members':db.scalar(select(func.count()).select_from(EnsembleMemberRecord)) or 0,
        'ensemble_statistics':db.scalar(select(func.count()).select_from(EnsembleStatisticRecord)) or 0,
      },
      'uncertainty_kinds':sorted(UNCERTAINTY_KINDS),'study_methods':sorted(STUDY_METHODS),'sensitivity_metrics':sorted(SENSITIVITY_METRICS),
      'weighting_policies':sorted(WEIGHTING_POLICIES),'statistic_kinds':sorted(STATISTIC_KINDS),
      'uncertainty_first_class':True,'sensitivity_reasoning':True,'ensemble_reasoning':True,
      'scenario_compute_integrated':True,'visual_reasoning_integrated':True,'visualization_registry_integrated':True,
      'sampling_execution_by_core':True,'monte_carlo_execution_by_core':True,'sensitivity_calculation_by_core':True,
      'ensemble_aggregation_by_core':True,'distribution_fitting_by_core':False,'numerical_computation_by_core':False,
      'automatic_probability_inference':False,'automatic_ranking':False,'automatic_truth_promotion':False,
    }


def create_uncertainty(db:Session,payload:dict[str,Any]):
    project_id=str(payload.get('project_entity_id') or ''); _entity(db,project_id,'research-project')
    target_id=str(payload.get('target_entity_id') or ''); target=_entity(db,target_id)
    allowed={'parameter','variable','result','scenario','model','model-version'}
    if target.entity_type not in allowed: raise ValueError('target_entity_id must reference a model, model-version, parameter, variable, scenario, or result.')
    model_id=payload.get('model_entity_id')
    if model_id: _entity(db,str(model_id),'model')
    kind=str(payload.get('uncertainty_kind') or 'interval')
    if kind not in UNCERTAINTY_KINDS: raise ValueError('Unsupported uncertainty_kind.')
    dist=payload.get('distribution_name')
    if dist and str(dist) not in DISTRIBUTIONS: raise ValueError('Unsupported distribution_name.')
    lower=payload.get('lower_bound'); upper=payload.get('upper_bound'); conf=payload.get('confidence_level')
    if lower is not None and upper is not None and float(lower)>float(upper): raise ValueError('lower_bound cannot exceed upper_bound.')
    if conf is not None and not 0<=float(conf)<=1: raise ValueError('confidence_level must be between 0 and 1.')
    if kind=='distribution' and not dist: raise ValueError('distribution uncertainty requires distribution_name.')
    if kind=='empirical' and not list(payload.get('empirical_values') or []): raise ValueError('empirical uncertainty requires empirical_values.')
    row=UncertaintyDefinitionRecord(uncertainty_key=str(payload.get('uncertainty_key') or ''),name=str(payload.get('name') or payload.get('uncertainty_key') or 'Uncertainty'),description=payload.get('description'),visibility=str(payload.get('visibility') or 'private'),project_entity_id=project_id,model_entity_id=model_id,target_entity_id=target_id,uncertainty_kind=kind,distribution_name=dist,unit=payload.get('unit'),lower_bound=lower,upper_bound=upper,confidence_level=conf,parameters_json=dict(payload.get('parameters') or {}),empirical_values_json=list(payload.get('empirical_values') or []),assumptions_json=list(payload.get('assumptions') or []),provenance_json=dict(payload.get('provenance') or {}),metadata_json=dict(payload.get('metadata') or {}),created_by=str(payload.get('created_by') or 'operator'))
    if not row.uncertainty_key: raise ValueError('uncertainty_key is required.')
    db.add(row)
    try: db.commit();db.refresh(row)
    except IntegrityError as exc: db.rollback();raise HTTPException(status_code=409,detail='Uncertainty key already exists for this project.') from exc
    return _ser(row)


def list_uncertainty(db:Session,*,public_only=False,limit=100,offset=0):
    stmt=select(UncertaintyDefinitionRecord); count=select(func.count()).select_from(UncertaintyDefinitionRecord)
    if public_only: stmt=stmt.where(UncertaintyDefinitionRecord.visibility=='public'); count=count.where(UncertaintyDefinitionRecord.visibility=='public')
    total=int(db.scalar(count) or 0); rows=db.scalars(stmt.order_by(UncertaintyDefinitionRecord.created_at.desc()).limit(limit).offset(offset)).all()
    return [_ser(r) for r in rows],total


def create_sensitivity_study(db:Session,payload:dict[str,Any],*,release:str):
    project_id=str(payload.get('project_entity_id') or ''); _entity(db,project_id,'research-project')
    model_id=str(payload.get('model_entity_id') or ''); version_id=str(payload.get('model_version_entity_id') or ''); _model_version(db,model_id,version_id)
    plan_id=payload.get('compute_plan_id')
    if plan_id:
        plan=db.get(ScenarioComputePlanRecord,str(plan_id))
        if plan is None or plan.project_entity_id!=project_id or plan.model_entity_id!=model_id or plan.model_version_entity_id!=version_id: raise ValueError('compute_plan_id must match the study project/model/version.')
    state=str(payload.get('study_state') or 'draft'); method=str(payload.get('method') or 'one-at-a-time')
    if state not in STUDY_STATES: raise ValueError('Unsupported study_state.')
    if method not in STUDY_METHODS: raise ValueError('Unsupported sensitivity method.')
    visual=visual_reasoning.create_object(db,name=str(payload.get('name') or 'Sensitivity study'),slug=payload.get('slug'),description=payload.get('description'),entity_id=payload.get('entity_id'),visibility=str(payload.get('visibility') or 'private'),entity_status='active',visual_kind='sensitivity-map',reasoning_purpose='diagnose',semantic_state='draft' if state=='ready' else ('published' if state=='completed' else state if state in {'draft','archived'} else 'reviewed'),coordinate_space='abstract',project_entity_id=project_id,primary_subject_entity_id=model_id,lens={'method':method,'output_key':payload.get('output_key')},filters={},assumptions=list(payload.get('assumptions') or []),metadata={**dict(payload.get('metadata') or {}),'sensitivity_release':release},release=release)
    row=SensitivityStudyRecord(visual_entity_id=visual['id'],study_key=str(payload.get('study_key') or ''),project_entity_id=project_id,model_entity_id=model_id,model_version_entity_id=version_id,compute_plan_id=plan_id,study_state=state,method=method,output_key=payload.get('output_key'),sampling_contract_json=dict(payload.get('sampling_contract') or {}),execution_product=str(payload.get('execution_product') or 'lab'),assumptions_json=list(payload.get('assumptions') or []),metadata_json=dict(payload.get('metadata') or {}),created_by=str(payload.get('created_by') or 'operator'))
    if not row.study_key: raise ValueError('study_key is required.')
    db.add(row)
    try: db.commit();db.refresh(row)
    except IntegrityError as exc: db.rollback();raise HTTPException(status_code=409,detail='Sensitivity study key already exists for this project.') from exc
    return read_sensitivity_study(db,row.visual_entity_id)


def read_sensitivity_study(db:Session,visual_id:str,*,public_only=False):
    row=db.get(SensitivityStudyRecord,visual_id)
    if row is None: raise HTTPException(status_code=404,detail='Sensitivity study not found.')
    if public_only:_public_visual(db,visual_id)
    item=_ser(row); e=db.get(Entity,visual_id); item['entity']={'id':e.id,'name':e.name,'visibility':e.visibility} if e else None
    return item


def list_sensitivity_studies(db:Session,*,public_only=False,limit=100,offset=0):
    stmt=select(SensitivityStudyRecord).join(Entity,Entity.id==SensitivityStudyRecord.visual_entity_id); count=select(func.count()).select_from(SensitivityStudyRecord).join(Entity,Entity.id==SensitivityStudyRecord.visual_entity_id)
    if public_only: stmt=stmt.where(Entity.visibility=='public');count=count.where(Entity.visibility=='public')
    total=int(db.scalar(count) or 0);rows=db.scalars(stmt.order_by(SensitivityStudyRecord.created_at.desc()).limit(limit).offset(offset)).all()
    return [read_sensitivity_study(db,r.visual_entity_id,public_only=public_only) for r in rows],total


def add_factor(db:Session,visual_id:str,payload:dict[str,Any]):
    study=db.get(SensitivityStudyRecord,visual_id)
    if study is None: raise HTTPException(status_code=404,detail='Sensitivity study not found.')
    pid=str(payload.get('parameter_entity_id') or ''); param=db.get(ResearchParameterRecord,pid)
    if param is None or param.model_entity_id!=study.model_entity_id: raise ValueError('parameter_entity_id must reference a parameter belonging to the study model.')
    uid=payload.get('uncertainty_definition_id')
    if uid:
        u=db.get(UncertaintyDefinitionRecord,str(uid))
        if u is None or u.target_entity_id!=pid: raise ValueError('uncertainty_definition_id must target the factor parameter.')
    lower=payload.get('lower_bound');upper=payload.get('upper_bound')
    if lower is not None and upper is not None and float(lower)>float(upper): raise ValueError('lower_bound cannot exceed upper_bound.')
    row=SensitivityFactorRecord(visual_entity_id=visual_id,factor_key=str(payload.get('factor_key') or ''),parameter_entity_id=pid,uncertainty_definition_id=uid,label=str(payload.get('label') or param.name),baseline_value_json=dict(payload.get('baseline_value') or param.default_value_json or {}),lower_bound=lower,upper_bound=upper,unit=payload.get('unit') or param.unit,variation_policy_json=dict(payload.get('variation_policy') or {}),order_index=int(payload.get('order_index',0)),metadata_json=dict(payload.get('metadata') or {}))
    if not row.factor_key: raise ValueError('factor_key is required.')
    db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Sensitivity factor key already exists.') from exc
    return _ser(row)


def add_sensitivity_result(db:Session,visual_id:str,payload:dict[str,Any]):
    study=db.get(SensitivityStudyRecord,visual_id)
    if study is None: raise HTTPException(status_code=404,detail='Sensitivity study not found.')
    fid=str(payload.get('factor_id') or '');factor=db.get(SensitivityFactorRecord,fid)
    if factor is None or factor.visual_entity_id!=visual_id: raise ValueError('factor_id must belong to the sensitivity study.')
    metric=str(payload.get('metric_kind') or 'effect')
    if metric not in SENSITIVITY_METRICS: raise ValueError('Unsupported sensitivity metric_kind.')
    src=dict(payload.get('source_execution') or {})
    if src.get('calculated_by_core') is True: raise ValueError('Sensitivity metrics cannot claim calculation by Core.')
    lower=payload.get('lower_bound');upper=payload.get('upper_bound')
    if lower is not None and upper is not None and float(lower)>float(upper): raise ValueError('lower_bound cannot exceed upper_bound.')
    row=SensitivityResultRecord(visual_entity_id=visual_id,factor_id=fid,metric_kind=metric,output_key=str(payload.get('output_key') or study.output_key or 'output'),value_json=dict(payload.get('value') or {}),unit=payload.get('unit'),lower_bound=lower,upper_bound=upper,rank_position=payload.get('rank_position'),source_execution_json=src,provenance_json=dict(payload.get('provenance') or {}),metadata_json=dict(payload.get('metadata') or {}))
    db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Sensitivity metric already exists for this factor/output.') from exc
    return _ser(row)


def validate_sensitivity(db:Session,visual_id:str):
    study=db.get(SensitivityStudyRecord,visual_id)
    if study is None: raise HTTPException(status_code=404,detail='Sensitivity study not found.')
    factors=db.scalars(select(SensitivityFactorRecord).where(SensitivityFactorRecord.visual_entity_id==visual_id)).all();results=db.scalars(select(SensitivityResultRecord).where(SensitivityResultRecord.visual_entity_id==visual_id)).all()
    warnings=[]
    if not factors:warnings.append('study_has_no_factors')
    if not results:warnings.append('study_has_no_external_results')
    return {'valid':True,'counts':{'factors':len(factors),'results':len(results)},'warnings':warnings,'sampling_plan_governed':True,'sampling_execution_performed':False,'sensitivity_calculation_performed':False,'numerical_computation_performed':False,'automatic_ranking_performed':False}


def compile_sensitivity_spec(db:Session,visual_id:str,payload:dict[str,Any]):
    study=read_sensitivity_study(db,visual_id);factors=[_ser(r) for r in db.scalars(select(SensitivityFactorRecord).where(SensitivityFactorRecord.visual_entity_id==visual_id).order_by(SensitivityFactorRecord.order_index)).all()];results=[_ser(r) for r in db.scalars(select(SensitivityResultRecord).where(SensitivityResultRecord.visual_entity_id==visual_id)).all()]
    spec=visualization_registry.create_specification(db,{'visual_entity_id':visual_id,'spec_key':str(payload.get('spec_key') or 'sensitivity'),'revision':int(payload.get('revision',1)),'spec_kind':'chart','title':payload.get('title') or 'Sensitivity analysis','preferred_renderer_key':payload.get('preferred_renderer_key') or 'contract.vega-lite','renderer_policy':'compatible','encoding':{'study':study,'factors':factors,'results':results,'calculated_by_core':False},'interaction':{'factor_selection':True,'output_selection':True},'layout_constraints':{'layout_execution_by_core':False},'metadata':{'v236_sensitivity':True,'external_metrics_required':True},'created_by':payload.get('created_by','operator')})
    resolution=visualization_registry.resolve_renderer(db,spec['id'],created_by=str(payload.get('created_by') or 'operator'))
    return {'specification':spec,'renderer_resolution':resolution,'renderer_execution_performed':False,'sensitivity_calculation_performed':False}


def create_ensemble(db:Session,payload:dict[str,Any],*,release:str):
    project_id=str(payload.get('project_entity_id') or '');_entity(db,project_id,'research-project')
    model_id=str(payload.get('model_entity_id') or '');version_id=str(payload.get('model_version_entity_id') or '');_model_version(db,model_id,version_id)
    plan_id=payload.get('compute_plan_id')
    if plan_id:
        plan=db.get(ScenarioComputePlanRecord,str(plan_id))
        if plan is None or plan.project_entity_id!=project_id or plan.model_entity_id!=model_id or plan.model_version_entity_id!=version_id: raise ValueError('compute_plan_id must match the ensemble project/model/version.')
    state=str(payload.get('ensemble_state') or 'draft');weighting=str(payload.get('weighting_policy') or 'equal')
    if state not in ENSEMBLE_STATES:raise ValueError('Unsupported ensemble_state.')
    if weighting not in WEIGHTING_POLICIES:raise ValueError('Unsupported weighting_policy.')
    visual=visual_reasoning.create_object(db,name=str(payload.get('name') or 'Ensemble'),slug=payload.get('slug'),description=payload.get('description'),entity_id=payload.get('entity_id'),visibility=str(payload.get('visibility') or 'private'),entity_status='active',visual_kind='ensemble-view',reasoning_purpose='compare',semantic_state='draft' if state=='ready' else ('published' if state=='completed' else state if state in {'draft','archived'} else 'reviewed'),coordinate_space='abstract',project_entity_id=project_id,primary_subject_entity_id=model_id,lens={'weighting_policy':weighting},filters={},assumptions=list(payload.get('assumptions') or []),metadata={**dict(payload.get('metadata') or {}),'ensemble_release':release},release=release)
    row=EnsembleRecord(visual_entity_id=visual['id'],ensemble_key=str(payload.get('ensemble_key') or ''),project_entity_id=project_id,model_entity_id=model_id,model_version_entity_id=version_id,compute_plan_id=plan_id,ensemble_state=state,weighting_policy=weighting,aggregation_contract_json=dict(payload.get('aggregation_contract') or {}),assumptions_json=list(payload.get('assumptions') or []),metadata_json=dict(payload.get('metadata') or {}),created_by=str(payload.get('created_by') or 'operator'))
    if not row.ensemble_key:raise ValueError('ensemble_key is required.')
    db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Ensemble key already exists for this project.') from exc
    return read_ensemble(db,row.visual_entity_id)


def read_ensemble(db:Session,visual_id:str,*,public_only=False):
    row=db.get(EnsembleRecord,visual_id)
    if row is None:raise HTTPException(status_code=404,detail='Ensemble not found.')
    if public_only:_public_visual(db,visual_id)
    item=_ser(row);e=db.get(Entity,visual_id);item['entity']={'id':e.id,'name':e.name,'visibility':e.visibility} if e else None;return item


def list_ensembles(db:Session,*,public_only=False,limit=100,offset=0):
    stmt=select(EnsembleRecord).join(Entity,Entity.id==EnsembleRecord.visual_entity_id);count=select(func.count()).select_from(EnsembleRecord).join(Entity,Entity.id==EnsembleRecord.visual_entity_id)
    if public_only:stmt=stmt.where(Entity.visibility=='public');count=count.where(Entity.visibility=='public')
    total=int(db.scalar(count) or 0);rows=db.scalars(stmt.order_by(EnsembleRecord.created_at.desc()).limit(limit).offset(offset)).all();return [read_ensemble(db,r.visual_entity_id,public_only=public_only) for r in rows],total


def add_ensemble_member(db:Session,visual_id:str,payload:dict[str,Any]):
    ensemble=db.get(EnsembleRecord,visual_id)
    if ensemble is None:raise HTTPException(status_code=404,detail='Ensemble not found.')
    scenario_id=payload.get('scenario_entity_id');case_id=payload.get('compute_case_id');req_id=payload.get('compute_request_id');run_id=payload.get('model_run_entity_id')
    if not any([scenario_id,case_id,req_id,run_id]):raise ValueError('Ensemble member requires at least one scenario/case/request/run reference.')
    if scenario_id:
        s=db.get(ResearchScenarioRecord,str(scenario_id))
        if s is None or s.project_entity_id!=ensemble.project_entity_id:raise ValueError('scenario_entity_id must belong to the ensemble project.')
    if case_id:
        c=db.get(ScenarioComputeCaseRecord,str(case_id));plan=db.get(ScenarioComputePlanRecord,c.plan_id) if c else None
        if c is None or plan is None or plan.model_version_entity_id!=ensemble.model_version_entity_id:raise ValueError('compute_case_id must belong to a compatible compute plan.')
    if req_id:
        r=db.get(ScenarioComputeRequestRecord,str(req_id));plan=db.get(ScenarioComputePlanRecord,r.plan_id) if r else None
        if r is None or plan is None or plan.model_version_entity_id!=ensemble.model_version_entity_id:raise ValueError('compute_request_id must belong to a compatible compute plan.')
    if run_id:
        run=db.get(ResearchModelRunRecord,str(run_id))
        if run is None or run.model_version_entity_id!=ensemble.model_version_entity_id:raise ValueError('model_run_entity_id must use the ensemble model version.')
    state=str(payload.get('inclusion_state') or 'included')
    if state not in INCLUSION_STATES:raise ValueError('Unsupported inclusion_state.')
    weight=payload.get('weight')
    if weight is not None and float(weight)<0:raise ValueError('weight cannot be negative.')
    row=EnsembleMemberRecord(visual_entity_id=visual_id,member_key=str(payload.get('member_key') or ''),label=str(payload.get('label') or payload.get('member_key') or 'Member'),scenario_entity_id=scenario_id,compute_case_id=case_id,compute_request_id=req_id,model_run_entity_id=run_id,weight=weight,inclusion_state=state,provenance_json=dict(payload.get('provenance') or {}),metadata_json=dict(payload.get('metadata') or {}))
    if not row.member_key:raise ValueError('member_key is required.')
    db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Ensemble member key already exists.') from exc
    return _ser(row)


def add_ensemble_statistic(db:Session,visual_id:str,payload:dict[str,Any]):
    ensemble=db.get(EnsembleRecord,visual_id)
    if ensemble is None:raise HTTPException(status_code=404,detail='Ensemble not found.')
    kind=str(payload.get('statistic_kind') or 'mean')
    if kind not in STATISTIC_KINDS:raise ValueError('Unsupported statistic_kind.')
    src=dict(payload.get('source_execution') or {})
    if src.get('calculated_by_core') is True:raise ValueError('Ensemble statistics cannot claim calculation by Core.')
    prob=payload.get('probability')
    if prob is not None and not 0<=float(prob)<=1:raise ValueError('probability must be between 0 and 1.')
    lower=payload.get('lower_bound');upper=payload.get('upper_bound')
    if lower is not None and upper is not None and float(lower)>float(upper):raise ValueError('lower_bound cannot exceed upper_bound.')
    row=EnsembleStatisticRecord(visual_entity_id=visual_id,statistic_key=str(payload.get('statistic_key') or ''),output_key=str(payload.get('output_key') or 'output'),statistic_kind=kind,value_json=dict(payload.get('value') or {}),unit=payload.get('unit'),lower_bound=lower,upper_bound=upper,probability=prob,source_execution_json=src,provenance_json=dict(payload.get('provenance') or {}),metadata_json=dict(payload.get('metadata') or {}))
    if not row.statistic_key:raise ValueError('statistic_key is required.')
    db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Ensemble statistic key already exists.') from exc
    return _ser(row)


def validate_ensemble(db:Session,visual_id:str):
    ensemble=db.get(EnsembleRecord,visual_id)
    if ensemble is None:raise HTTPException(status_code=404,detail='Ensemble not found.')
    members=db.scalars(select(EnsembleMemberRecord).where(EnsembleMemberRecord.visual_entity_id==visual_id)).all();stats=db.scalars(select(EnsembleStatisticRecord).where(EnsembleStatisticRecord.visual_entity_id==visual_id)).all();warnings=[]
    if not members:warnings.append('ensemble_has_no_members')
    if not stats:warnings.append('ensemble_has_no_external_statistics')
    if ensemble.weighting_policy=='explicit' and any(m.inclusion_state=='included' and m.weight is None for m in members):warnings.append('explicit_weighting_has_unweighted_members')
    return {'valid':True,'counts':{'members':len(members),'statistics':len(stats)},'warnings':warnings,'membership_governed':True,'aggregation_performed':False,'probability_inference_performed':False,'numerical_computation_performed':False,'automatic_ranking_performed':False}


def compile_ensemble_spec(db:Session,visual_id:str,payload:dict[str,Any]):
    ensemble=read_ensemble(db,visual_id);members=[_ser(r) for r in db.scalars(select(EnsembleMemberRecord).where(EnsembleMemberRecord.visual_entity_id==visual_id)).all()];stats=[_ser(r) for r in db.scalars(select(EnsembleStatisticRecord).where(EnsembleStatisticRecord.visual_entity_id==visual_id)).all()]
    spec=visualization_registry.create_specification(db,{'visual_entity_id':visual_id,'spec_key':str(payload.get('spec_key') or 'ensemble'),'revision':int(payload.get('revision',1)),'spec_kind':'chart','title':payload.get('title') or 'Ensemble reasoning','preferred_renderer_key':payload.get('preferred_renderer_key') or 'contract.plotly','renderer_policy':'compatible','encoding':{'ensemble':ensemble,'members':members,'statistics':stats,'aggregation_by_core':False},'interaction':{'member_selection':True,'statistic_selection':True},'layout_constraints':{'layout_execution_by_core':False},'metadata':{'v236_ensemble':True,'external_statistics_required':True},'created_by':payload.get('created_by','operator')})
    resolution=visualization_registry.resolve_renderer(db,spec['id'],created_by=str(payload.get('created_by') or 'operator'))
    return {'specification':spec,'renderer_resolution':resolution,'renderer_execution_performed':False,'ensemble_aggregation_performed':False}


def sensitivity_bundle(db:Session,visual_id:str,*,public_only=False):
    study=read_sensitivity_study(db,visual_id,public_only=public_only)
    return {'study':study,'factors':[_ser(r) for r in db.scalars(select(SensitivityFactorRecord).where(SensitivityFactorRecord.visual_entity_id==visual_id).order_by(SensitivityFactorRecord.order_index)).all()],'results':[_ser(r) for r in db.scalars(select(SensitivityResultRecord).where(SensitivityResultRecord.visual_entity_id==visual_id)).all()]}


def ensemble_bundle(db:Session,visual_id:str,*,public_only=False):
    ensemble=read_ensemble(db,visual_id,public_only=public_only)
    return {'ensemble':ensemble,'members':[_ser(r) for r in db.scalars(select(EnsembleMemberRecord).where(EnsembleMemberRecord.visual_entity_id==visual_id)).all()],'statistics':[_ser(r) for r in db.scalars(select(EnsembleStatisticRecord).where(EnsembleStatisticRecord.visual_entity_id==visual_id)).all()]}
