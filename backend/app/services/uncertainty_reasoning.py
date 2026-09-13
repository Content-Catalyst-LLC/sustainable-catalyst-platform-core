from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Entity,
    ResearchModelRecord,
    ResearchModelVersionRecord,
    ResearchParameterRecord,
    ResearchVariableRecord,
    ResearchScenarioRecord,
    ResearchModelRunRecord,
    ResearchResultRecord,
    ScenarioComputePlanRecord,
    ScenarioComputeRequestRecord,
    UncertaintyDefinitionRecord,
    SensitivityStudyRecord,
    SensitivityFactorRecord,
    SensitivityMeasureRecord,
    EnsembleRecord,
    EnsembleMemberRecord,
    EnsembleStatisticRecord,
)

UNCERTAINTY_KINDS = {"aleatory", "epistemic", "mixed", "measurement", "model", "scenario", "unknown"}
DISTRIBUTION_FAMILIES = {"deterministic", "interval", "uniform", "normal", "lognormal", "triangular", "beta", "empirical", "custom"}
UNCERTAINTY_STATES = {"declared", "review", "validated", "deprecated"}
SENSITIVITY_METHODS = {"local", "one-at-a-time", "morris", "sobol", "monte-carlo", "correlation", "elasticity", "custom"}
STUDY_STATES = {"draft", "ready", "running", "completed", "review", "archived"}
MEASURE_KINDS = {"effect", "elasticity", "correlation", "first-order", "total-order", "mu-star", "sigma", "delta", "custom"}
ENSEMBLE_STATES = {"draft", "ready", "running", "complete", "review", "archived"}
MEMBER_STATES = {"declared", "requested", "running", "completed", "failed", "excluded"}
STATISTIC_KINDS = {"mean", "median", "minimum", "maximum", "stddev", "variance", "quantile", "interval", "probability", "custom"}
EXECUTION_PRODUCTS = {"lab", "workbench", "external"}


def _ser(row):
    out = {}
    for c in row.__table__.columns:
        v = getattr(row, c.name)
        if hasattr(v, "isoformat"):
            v = v.isoformat()
        out[c.name] = v
    return out


def _entity(db: Session, entity_id: str, entity_type: str | None = None, field: str = "entity_id") -> Entity:
    e = db.get(Entity, entity_id)
    if e is None or (entity_type is not None and e.entity_type != entity_type):
        suffix = f" {entity_type}" if entity_type else ""
        raise ValueError(f"{field} must reference a{suffix} entity.")
    return e


def _project(db: Session, project_entity_id: str) -> Entity:
    return _entity(db, project_entity_id, "research-project", "project_entity_id")


def _model_bundle(db: Session, model_entity_id: str, model_version_entity_id: str):
    _entity(db, model_entity_id, "model", "model_entity_id")
    model = db.get(ResearchModelRecord, model_entity_id)
    version = db.get(ResearchModelVersionRecord, model_version_entity_id)
    if model is None:
        raise ValueError("model_entity_id must reference a governed research model.")
    if version is None or version.model_entity_id != model_entity_id:
        raise ValueError("model_version_entity_id must reference a version of model_entity_id.")
    if not version.immutable:
        raise ValueError("model_version_entity_id must be immutable for uncertainty reasoning.")
    return model, version


def _require_uncertainty(db: Session, uncertainty_id: str, *, public_only: bool = False):
    row = db.get(UncertaintyDefinitionRecord, uncertainty_id)
    if row is None or (public_only and row.visibility != "public"):
        raise HTTPException(status_code=404, detail="Uncertainty definition not found.")
    return row


def _require_study(db: Session, study_id: str, *, public_only: bool = False):
    row = db.get(SensitivityStudyRecord, study_id)
    if row is None or (public_only and row.visibility != "public"):
        raise HTTPException(status_code=404, detail="Sensitivity study not found.")
    return row


def _require_ensemble(db: Session, ensemble_id: str, *, public_only: bool = False):
    row = db.get(EnsembleRecord, ensemble_id)
    if row is None or (public_only and row.visibility != "public"):
        raise HTTPException(status_code=404, detail="Ensemble not found.")
    return row


def readiness(db: Session) -> dict[str, Any]:
    count = lambda model: int(db.scalar(select(func.count()).select_from(model)) or 0)
    return {
        "counts": {
            "uncertainty_definitions": count(UncertaintyDefinitionRecord),
            "sensitivity_studies": count(SensitivityStudyRecord),
            "sensitivity_factors": count(SensitivityFactorRecord),
            "sensitivity_measures": count(SensitivityMeasureRecord),
            "ensembles": count(EnsembleRecord),
            "ensemble_members": count(EnsembleMemberRecord),
            "ensemble_statistics": count(EnsembleStatisticRecord),
        },
        "uncertainty_kinds": sorted(UNCERTAINTY_KINDS),
        "distribution_families": sorted(DISTRIBUTION_FAMILIES),
        "sensitivity_methods": sorted(SENSITIVITY_METHODS),
        "measure_kinds": sorted(MEASURE_KINDS),
        "statistic_kinds": sorted(STATISTIC_KINDS),
        "research_objects_reused": True,
        "scenario_compute_integrated": True,
        "lab_workbench_handoff": True,
        "sampling_by_core": False,
        "sensitivity_algorithm_execution_by_core": False,
        "ensemble_aggregation_by_core": False,
        "model_execution_by_core": False,
        "numerical_computation_by_core": False,
        "automatic_probability_generation": False,
        "automatic_truth_promotion": False,
    }


def create_uncertainty(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    project_id = str(payload.get("project_entity_id") or "")
    subject_id = str(payload.get("subject_entity_id") or "")
    _project(db, project_id)
    subject = _entity(db, subject_id, field="subject_entity_id")
    if subject.entity_type not in {"parameter", "variable", "scenario", "model", "model-version", "result"}:
        raise ValueError("subject_entity_id must reference a parameter, variable, scenario, model, model-version, or result.")
    kind = str(payload.get("uncertainty_kind") or "epistemic")
    family = str(payload.get("distribution_family") or "interval")
    state = str(payload.get("state") or "declared")
    if kind not in UNCERTAINTY_KINDS:
        raise ValueError("Unsupported uncertainty_kind.")
    if family not in DISTRIBUTION_FAMILIES:
        raise ValueError("Unsupported distribution_family.")
    if state not in UNCERTAINTY_STATES:
        raise ValueError("Unsupported uncertainty state.")
    lower = payload.get("lower_bound")
    upper = payload.get("upper_bound")
    if lower is not None and upper is not None and float(lower) > float(upper):
        raise ValueError("lower_bound must not exceed upper_bound.")
    confidence = payload.get("confidence_level")
    if confidence is not None and not (0 < float(confidence) <= 1):
        raise ValueError("confidence_level must be greater than 0 and at most 1.")
    if subject.entity_type == "parameter":
        p = db.get(ResearchParameterRecord, subject_id)
        model = db.get(ResearchModelRecord, p.model_entity_id) if p else None
        if model and model.project_entity_id and model.project_entity_id != project_id:
            raise ValueError("subject parameter must belong to the uncertainty project.")
    if subject.entity_type == "variable":
        v = db.get(ResearchVariableRecord, subject_id)
        model = db.get(ResearchModelRecord, v.model_entity_id) if v else None
        if model and model.project_entity_id and model.project_entity_id != project_id:
            raise ValueError("subject variable must belong to the uncertainty project.")
    if subject.entity_type == "scenario":
        s = db.get(ResearchScenarioRecord, subject_id)
        if s and s.project_entity_id != project_id:
            raise ValueError("subject scenario must belong to the uncertainty project.")
    row = UncertaintyDefinitionRecord(
        uncertainty_key=str(payload.get("uncertainty_key") or "uncertainty"),
        name=str(payload.get("name") or payload.get("uncertainty_key") or "Uncertainty"),
        description=payload.get("description"), visibility=str(payload.get("visibility") or "private"),
        project_entity_id=project_id, subject_entity_id=subject_id, uncertainty_kind=kind,
        distribution_family=family, parameters_json=dict(payload.get("parameters") or {}),
        lower_bound=float(lower) if lower is not None else None, upper_bound=float(upper) if upper is not None else None,
        unit=payload.get("unit"), confidence_level=float(confidence) if confidence is not None else None,
        source_json=dict(payload.get("source") or {}), provenance_json=dict(payload.get("provenance") or {}),
        assumptions_json=list(payload.get("assumptions") or []), state=state,
        metadata_json=dict(payload.get("metadata") or {}), created_by=str(payload.get("created_by") or "operator"),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Uncertainty key already exists in project.") from exc
    return _ser(row)


def read_uncertainty(db: Session, uncertainty_id: str, *, public_only: bool = False):
    return _ser(_require_uncertainty(db, uncertainty_id, public_only=public_only))


def list_uncertainties(db: Session, *, public_only: bool = False, limit=100, offset=0):
    stmt = select(UncertaintyDefinitionRecord); count = select(func.count()).select_from(UncertaintyDefinitionRecord)
    if public_only:
        stmt = stmt.where(UncertaintyDefinitionRecord.visibility == "public"); count = count.where(UncertaintyDefinitionRecord.visibility == "public")
    total = int(db.scalar(count) or 0)
    rows = db.scalars(stmt.order_by(UncertaintyDefinitionRecord.created_at.desc()).limit(limit).offset(offset)).all()
    return [_ser(x) for x in rows], total


def create_study(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    project_id = str(payload.get("project_entity_id") or ""); model_id = str(payload.get("model_entity_id") or ""); version_id = str(payload.get("model_version_entity_id") or "")
    _project(db, project_id); model, _version = _model_bundle(db, model_id, version_id)
    if model.project_entity_id and model.project_entity_id != project_id:
        raise ValueError("model_entity_id must belong to project_entity_id.")
    plan_id = payload.get("compute_plan_id")
    if plan_id:
        plan = db.get(ScenarioComputePlanRecord, str(plan_id))
        if plan is None or plan.project_entity_id != project_id or plan.model_version_entity_id != version_id:
            raise ValueError("compute_plan_id must reference a compatible Scenario Compute plan.")
    method = str(payload.get("method") or "local"); state = str(payload.get("study_state") or "draft"); execution_product = str(payload.get("execution_product") or "lab")
    if method not in SENSITIVITY_METHODS: raise ValueError("Unsupported sensitivity method.")
    if state not in STUDY_STATES: raise ValueError("Unsupported study_state.")
    if execution_product not in EXECUTION_PRODUCTS: raise ValueError("Unsupported execution_product.")
    row = SensitivityStudyRecord(
        study_key=str(payload.get("study_key") or "study"), name=str(payload.get("name") or "Sensitivity study"),
        description=payload.get("description"), visibility=str(payload.get("visibility") or "private"), project_entity_id=project_id,
        model_entity_id=model_id, model_version_entity_id=version_id, compute_plan_id=plan_id, method=method,
        output_metric=payload.get("output_metric"), study_state=state, execution_product=execution_product,
        configuration_json=dict(payload.get("configuration") or {}), assumptions_json=list(payload.get("assumptions") or []),
        metadata_json=dict(payload.get("metadata") or {}), created_by=str(payload.get("created_by") or "operator"),
    )
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Sensitivity study key already exists in project.") from exc
    return _ser(row)


def add_factor(db: Session, study_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    study = _require_study(db, study_id)
    pid = str(payload.get("parameter_entity_id") or "")
    _entity(db, pid, "parameter", "parameter_entity_id")
    parameter = db.get(ResearchParameterRecord, pid)
    if parameter is None or parameter.model_entity_id != study.model_entity_id:
        raise ValueError("parameter_entity_id must belong to the study model.")
    lower = payload.get("lower_bound"); upper = payload.get("upper_bound")
    if lower is not None and upper is not None and float(lower) > float(upper): raise ValueError("lower_bound must not exceed upper_bound.")
    uid = payload.get("uncertainty_definition_id")
    if uid:
        ud = _require_uncertainty(db, str(uid))
        if ud.subject_entity_id != pid:
            raise ValueError("uncertainty_definition_id must describe parameter_entity_id.")
    row = SensitivityFactorRecord(
        study_id=study_id, factor_key=str(payload.get("factor_key") or parameter.name), parameter_entity_id=pid,
        lower_bound=float(lower) if lower is not None else None, upper_bound=float(upper) if upper is not None else None,
        unit=payload.get("unit") or parameter.unit, uncertainty_definition_id=uid, order_index=int(payload.get("order_index", 0)),
        metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Sensitivity factor already exists in study.") from exc
    return _ser(row)


def add_measure(db: Session, study_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _require_study(db, study_id)
    factor_id = str(payload.get("factor_id") or ""); factor = db.get(SensitivityFactorRecord, factor_id)
    if factor is None or factor.study_id != study_id: raise ValueError("factor_id must belong to the sensitivity study.")
    kind = str(payload.get("measure_kind") or "effect")
    if kind not in MEASURE_KINDS: raise ValueError("Unsupported measure_kind.")
    value = payload.get("measure_value")
    if value is None: raise ValueError("measure_value is required and must be externally supplied.")
    lower = payload.get("lower_bound"); upper = payload.get("upper_bound")
    if lower is not None and upper is not None and float(lower) > float(upper): raise ValueError("lower_bound must not exceed upper_bound.")
    result_id = payload.get("result_entity_id")
    if result_id: _entity(db, str(result_id), "result", "result_entity_id")
    row = SensitivityMeasureRecord(
        study_id=study_id, factor_id=factor_id, output_key=str(payload.get("output_key") or "output"), result_entity_id=result_id,
        measure_kind=kind, measure_value=float(value), lower_bound=float(lower) if lower is not None else None,
        upper_bound=float(upper) if upper is not None else None,
        confidence_level=float(payload["confidence_level"]) if payload.get("confidence_level") is not None else None,
        unit=payload.get("unit"), provenance_json=dict(payload.get("provenance") or {}), metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Sensitivity measure already exists for factor/output/kind.") from exc
    return _ser(row)


def sensitivity_summary(db: Session, study_id: str, *, public_only: bool = False) -> dict[str, Any]:
    study = _require_study(db, study_id, public_only=public_only)
    factors = db.scalars(select(SensitivityFactorRecord).where(SensitivityFactorRecord.study_id == study_id)).all()
    measures = db.scalars(select(SensitivityMeasureRecord).where(SensitivityMeasureRecord.study_id == study_id)).all()
    factor_by_id = {x.id: x for x in factors}
    rankings = defaultdict(list)
    for m in measures:
        f = factor_by_id.get(m.factor_id)
        rankings[(m.output_key, m.measure_kind)].append({
            "factor_id": m.factor_id, "factor_key": f.factor_key if f else None,
            "parameter_entity_id": f.parameter_entity_id if f else None, "measure_value": m.measure_value,
            "absolute_measure": abs(m.measure_value), "unit": m.unit,
        })
    ranked = []
    for (output_key, kind), values in sorted(rankings.items()):
        values.sort(key=lambda x: (-x["absolute_measure"], x.get("factor_key") or ""))
        for idx, item in enumerate(values, start=1): item["descriptive_rank"] = idx
        ranked.append({"output_key": output_key, "measure_kind": kind, "factors": values})
    return {
        "study": _ser(study), "factor_count": len(factors), "measure_count": len(measures), "rankings": ranked,
        "ranking_basis": "absolute externally supplied measure values", "ranking_is_descriptive": True,
        "sensitivity_algorithm_executed_by_core": False, "sampling_by_core": False, "model_execution_by_core": False,
    }


def sensitivity_bundle(db: Session, study_id: str, *, public_only: bool = False):
    study = _require_study(db, study_id, public_only=public_only)
    factors = db.scalars(select(SensitivityFactorRecord).where(SensitivityFactorRecord.study_id == study_id).order_by(SensitivityFactorRecord.order_index, SensitivityFactorRecord.factor_key)).all()
    measures = db.scalars(select(SensitivityMeasureRecord).where(SensitivityMeasureRecord.study_id == study_id).order_by(SensitivityMeasureRecord.output_key, SensitivityMeasureRecord.measure_kind)).all()
    return {"study": _ser(study), "factors": [_ser(x) for x in factors], "measures": [_ser(x) for x in measures], "summary": sensitivity_summary(db, study_id, public_only=public_only)}


def list_studies(db: Session, *, public_only=False, limit=100, offset=0):
    stmt=select(SensitivityStudyRecord); count=select(func.count()).select_from(SensitivityStudyRecord)
    if public_only: stmt=stmt.where(SensitivityStudyRecord.visibility=="public"); count=count.where(SensitivityStudyRecord.visibility=="public")
    total=int(db.scalar(count) or 0); rows=db.scalars(stmt.order_by(SensitivityStudyRecord.created_at.desc()).limit(limit).offset(offset)).all()
    return [_ser(x) for x in rows], total


def create_ensemble(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    project_id=str(payload.get("project_entity_id") or ""); model_id=str(payload.get("model_entity_id") or ""); version_id=str(payload.get("model_version_entity_id") or "")
    _project(db,project_id); model,_version=_model_bundle(db,model_id,version_id)
    if model.project_entity_id and model.project_entity_id!=project_id: raise ValueError("model_entity_id must belong to project_entity_id.")
    plan_id=payload.get("compute_plan_id")
    if plan_id:
        plan=db.get(ScenarioComputePlanRecord,str(plan_id))
        if plan is None or plan.project_entity_id!=project_id or plan.model_version_entity_id!=version_id: raise ValueError("compute_plan_id must reference a compatible Scenario Compute plan.")
    state=str(payload.get("ensemble_state") or "draft")
    if state not in ENSEMBLE_STATES: raise ValueError("Unsupported ensemble_state.")
    row=EnsembleRecord(ensemble_key=str(payload.get("ensemble_key") or "ensemble"),name=str(payload.get("name") or "Ensemble"),description=payload.get("description"),visibility=str(payload.get("visibility") or "private"),project_entity_id=project_id,model_entity_id=model_id,model_version_entity_id=version_id,compute_plan_id=plan_id,ensemble_state=state,combination_policy_json=dict(payload.get("combination_policy") or {}),assumptions_json=list(payload.get("assumptions") or []),metadata_json=dict(payload.get("metadata") or {}),created_by=str(payload.get("created_by") or "operator"))
    db.add(row)
    try: db.commit();db.refresh(row)
    except IntegrityError as exc: db.rollback();raise HTTPException(status_code=409,detail="Ensemble key already exists in project.") from exc
    return _ser(row)


def add_member(db: Session, ensemble_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    ensemble=_require_ensemble(db,ensemble_id); scenario_id=payload.get("scenario_entity_id"); request_id=payload.get("compute_request_id"); run_id=payload.get("model_run_entity_id")
    if not any([scenario_id,request_id,run_id]): raise ValueError("Ensemble member must bind a scenario, compute request, or model run.")
    if scenario_id:
        _entity(db,str(scenario_id),"scenario","scenario_entity_id"); s=db.get(ResearchScenarioRecord,str(scenario_id))
        if s and s.project_entity_id!=ensemble.project_entity_id: raise ValueError("scenario_entity_id must belong to ensemble project.")
    if request_id:
        req=db.get(ScenarioComputeRequestRecord,str(request_id))
        if req is None: raise ValueError("compute_request_id must reference a Scenario Compute request.")
        plan=db.get(ScenarioComputePlanRecord,req.plan_id)
        if plan is None or plan.model_version_entity_id!=ensemble.model_version_entity_id: raise ValueError("compute_request_id must use the ensemble model version.")
    if run_id:
        _entity(db,str(run_id),"model-run","model_run_entity_id"); run=db.get(ResearchModelRunRecord,str(run_id))
        if run is None or run.model_version_entity_id!=ensemble.model_version_entity_id: raise ValueError("model_run_entity_id must use the ensemble model version.")
    state=str(payload.get("member_state") or "declared")
    if state not in MEMBER_STATES: raise ValueError("Unsupported member_state.")
    weight=payload.get("weight")
    if weight is not None and float(weight)<0: raise ValueError("weight must be nonnegative.")
    row=EnsembleMemberRecord(ensemble_id=ensemble_id,member_key=str(payload.get("member_key") or "member"),scenario_entity_id=scenario_id,compute_request_id=request_id,model_run_entity_id=run_id,member_state=state,weight=float(weight) if weight is not None else None,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit();db.refresh(row)
    except IntegrityError as exc: db.rollback();raise HTTPException(status_code=409,detail="Ensemble member key already exists.") from exc
    return _ser(row)


def add_statistic(db: Session, ensemble_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _require_ensemble(db,ensemble_id); kind=str(payload.get("statistic_kind") or "mean")
    if kind not in STATISTIC_KINDS: raise ValueError("Unsupported statistic_kind.")
    value=payload.get("statistic_value")
    if value is None: raise ValueError("statistic_value is required and must be externally supplied.")
    q=payload.get("quantile")
    if q is not None and not (0 <= float(q) <= 1): raise ValueError("quantile must be between 0 and 1.")
    lower=payload.get("lower_bound");upper=payload.get("upper_bound")
    if lower is not None and upper is not None and float(lower)>float(upper): raise ValueError("lower_bound must not exceed upper_bound.")
    row=EnsembleStatisticRecord(ensemble_id=ensemble_id,output_key=str(payload.get("output_key") or "output"),statistic_kind=kind,statistic_value=float(value),unit=payload.get("unit"),quantile=float(q) if q is not None else None,lower_bound=float(lower) if lower is not None else None,upper_bound=float(upper) if upper is not None else None,confidence_level=float(payload["confidence_level"]) if payload.get("confidence_level") is not None else None,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit();db.refresh(row)
    except IntegrityError as exc: db.rollback();raise HTTPException(status_code=409,detail="Ensemble statistic already exists.") from exc
    return _ser(row)


def ensemble_summary(db: Session, ensemble_id: str, *, public_only=False) -> dict[str, Any]:
    ensemble=_require_ensemble(db,ensemble_id,public_only=public_only)
    members=db.scalars(select(EnsembleMemberRecord).where(EnsembleMemberRecord.ensemble_id==ensemble_id)).all();stats=db.scalars(select(EnsembleStatisticRecord).where(EnsembleStatisticRecord.ensemble_id==ensemble_id)).all()
    states=Counter(x.member_state for x in members); weights=[x.weight for x in members if x.weight is not None]
    return {"ensemble":_ser(ensemble),"member_count":len(members),"member_states":dict(sorted(states.items())),"weighted_member_count":len(weights),"declared_weight_total":sum(weights) if weights else None,"weights_normalized_by_core":False,"statistics":[_ser(x) for x in stats],"statistics_are_externally_supplied":True,"ensemble_aggregation_by_core":False,"sampling_by_core":False,"model_execution_by_core":False}


def ensemble_bundle(db: Session, ensemble_id: str, *, public_only=False):
    ensemble=_require_ensemble(db,ensemble_id,public_only=public_only);members=db.scalars(select(EnsembleMemberRecord).where(EnsembleMemberRecord.ensemble_id==ensemble_id).order_by(EnsembleMemberRecord.created_at)).all();stats=db.scalars(select(EnsembleStatisticRecord).where(EnsembleStatisticRecord.ensemble_id==ensemble_id).order_by(EnsembleStatisticRecord.output_key,EnsembleStatisticRecord.statistic_kind)).all()
    return {"ensemble":_ser(ensemble),"members":[_ser(x) for x in members],"statistics":[_ser(x) for x in stats],"summary":ensemble_summary(db,ensemble_id,public_only=public_only)}


def list_ensembles(db: Session, *, public_only=False, limit=100, offset=0):
    stmt=select(EnsembleRecord);count=select(func.count()).select_from(EnsembleRecord)
    if public_only:stmt=stmt.where(EnsembleRecord.visibility=="public");count=count.where(EnsembleRecord.visibility=="public")
    total=int(db.scalar(count) or 0);rows=db.scalars(stmt.order_by(EnsembleRecord.created_at.desc()).limit(limit).offset(offset)).all();return [_ser(x) for x in rows],total
