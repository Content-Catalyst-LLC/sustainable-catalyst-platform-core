from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Entity, PredictiveModelRecord, PredictiveTargetRecord, PredictiveFeatureRecord, PredictiveTrainingWindowRecord,
    PredictiveForecastRunRecord, PredictiveForecastObservationRecord, PredictiveEvaluationRecord,
    PredictiveRuntimeHandoffRecord, PredictiveForecastSnapshotRecord,
    PredictiveTimeSeriesDatasetRecord, PredictiveForecastWindowRecord, PredictiveBaselineModelRecord, PredictiveBacktestPlanRecord,
    PredictiveBacktestFoldRecord, PredictiveBacktestObservationRecord, PredictiveBacktestEvaluationRecord, PredictiveBacktestPackageRecord,
)

MODEL_KINDS={"statistical","machine-learning","simulation","hybrid","rules-based","external","other"}
RUNTIME_PRODUCTS={"lab","workbench","site-intelligence","decision-studio","catalyst-data","external"}
FEATURE_ROLES={"predictor","lagged-predictor","exogenous","context","identifier","time-index","other"}
BACKTEST_STRATEGIES={"fixed","rolling","expanding"}
BASELINE_KINDS={"naive","seasonal-naive","drift","mean","median","external","other"}
COMPARATOR_KINDS={"model","baseline"}
FORBIDDEN_FIELDS={"fit_by_core","train_by_core","infer_by_core","execute_by_core","core_execute","probability_calibrated_by_core","winner","rank","verdict","truth_value","automatic_truth_promotion","model_selected_by_core","backtest_execute_by_core","metric_compute_by_core","resample_by_core"}

def _ser(row):
    out={}
    for c in row.__table__.columns:
        v=getattr(row,c.name)
        if hasattr(v,"isoformat"): v=v.isoformat()
        out[c.name]=v
    return out

def _reject(payload:dict[str,Any]):
    bad=sorted(k for k in payload if k in FORBIDDEN_FIELDS)
    if bad: raise ValueError(f"Predictive Core records forecast provenance but does not fit, execute, rank, determine truth, or promote models automatically; forbidden fields: {bad}")

def _parse_dt(value):
    if value in (None,""): return None
    if isinstance(value,datetime): return value
    s=str(value).replace("Z","+00:00")
    return datetime.fromisoformat(s)

def _sha256(value:dict)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def _digest(value):
    if value in (None,""): return None
    d=str(value).lower().strip()
    if len(d)!=64 or any(c not in "0123456789abcdef" for c in d): raise ValueError("hash fields must be 64-character SHA-256 hexadecimal digests")
    return d

def _model(db:Session, model_id:str)->PredictiveModelRecord:
    row=db.get(PredictiveModelRecord,model_id)
    if row is None: raise HTTPException(status_code=404,detail="Predictive model not found.")
    return row

def boundaries():
    return {
      "predictive_model_registry_by_core":True,"prediction_target_registry_by_core":True,"feature_provenance_registry_by_core":True,
      "training_window_manifest_by_core":True,"forecast_provenance_capture_by_core":True,"forecast_observation_binding_by_core":True,
      "descriptive_evaluation_evidence_by_core":True,"specialist_runtime_handoffs_by_core":True,"immutable_forecast_snapshots_by_core":True,
      "time_series_dataset_registry_by_core":True,"forecast_window_registry_by_core":True,"baseline_model_reference_registry_by_core":True,
      "rolling_expanding_backtest_semantics_by_core":True,"temporal_leakage_guardrails_by_core":True,"backtest_fold_provenance_by_core":True,
      "prediction_actual_pair_recording_by_core":True,"descriptive_backtest_evaluation_by_core":True,"reproducible_backtest_packages_by_core":True,
      "model_fitting_by_core":False,"forecast_inference_execution_by_core":False,"backtest_execution_by_core":False,"metric_computation_by_core":False,
      "time_series_resampling_by_core":False,"probabilistic_calibration_by_core":False,"ensemble_selection_by_core":False,
      "automatic_model_ranking_by_core":False,"automatic_truth_promotion":False,
    }

def readiness(db:Session):
    def count(m): return int(db.scalar(select(func.count()).select_from(m)) or 0)
    return {"migration_0056_applied":True,"migration_0057_applied":True,"contract":"sc.predictive.model.v1","forecast_contract":"sc.predictive.forecast-provenance.v1","handoff_contract":"sc.predictive.runtime-handoff.v1","backtest_contract":"sc.predictive.backtest-plan.v1","backtest_package_contract":"sc.predictive.backtest-package.v1","counts":{
      "models":count(PredictiveModelRecord),"targets":count(PredictiveTargetRecord),"features":count(PredictiveFeatureRecord),"training_windows":count(PredictiveTrainingWindowRecord),
      "forecast_runs":count(PredictiveForecastRunRecord),"forecast_observations":count(PredictiveForecastObservationRecord),"evaluations":count(PredictiveEvaluationRecord),"handoffs":count(PredictiveRuntimeHandoffRecord),"snapshots":count(PredictiveForecastSnapshotRecord),
      "time_series_datasets":count(PredictiveTimeSeriesDatasetRecord),"forecast_windows":count(PredictiveForecastWindowRecord),"baseline_models":count(PredictiveBaselineModelRecord),"backtest_plans":count(PredictiveBacktestPlanRecord),
      "backtest_folds":count(PredictiveBacktestFoldRecord),"backtest_observations":count(PredictiveBacktestObservationRecord),"backtest_evaluations":count(PredictiveBacktestEvaluationRecord),"backtest_packages":count(PredictiveBacktestPackageRecord)},**boundaries()}

def create_model(db:Session,payload:dict):
    _reject(payload); project=str(payload.get("project_entity_id") or "").strip(); ent=db.get(Entity,project)
    if ent is None: raise ValueError("project_entity_id must reference an existing Core entity")
    kind=str(payload.get("model_kind") or "external"); runtime=str(payload.get("runtime_product") or "external")
    if kind not in MODEL_KINDS: raise ValueError(f"model_kind must be one of {sorted(MODEL_KINDS)}")
    if runtime not in RUNTIME_PRODUCTS: raise ValueError(f"runtime_product must be one of {sorted(RUNTIME_PRODUCTS)}")
    vis=str(payload.get("visibility") or "private");
    if vis not in {"private","public"}: raise ValueError("visibility must be private or public")
    row=PredictiveModelRecord(project_entity_id=project,model_key=str(payload.get("model_key") or "").strip(),name=str(payload.get("name") or "").strip(),description=payload.get("description"),model_kind=kind,runtime_product=runtime,runtime_model_ref=payload.get("runtime_model_ref"),model_version_ref=payload.get("model_version_ref"),lifecycle_state=str(payload.get("lifecycle_state") or "draft"),visibility=vis,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}),created_by=str(payload.get("created_by") or "operator"))
    if not row.model_key or not row.name: raise ValueError("model_key and name are required")
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("model_key must be unique within project_entity_id") from exc
    db.refresh(row); return _ser(row)

def list_models(db:Session,project_entity_id=None,public_only=False,limit=100,offset=0):
    stmt=select(PredictiveModelRecord); cnt=select(func.count()).select_from(PredictiveModelRecord)
    if project_entity_id: stmt=stmt.where(PredictiveModelRecord.project_entity_id==project_entity_id); cnt=cnt.where(PredictiveModelRecord.project_entity_id==project_entity_id)
    if public_only: stmt=stmt.where(PredictiveModelRecord.visibility=="public"); cnt=cnt.where(PredictiveModelRecord.visibility=="public")
    rows=db.scalars(stmt.order_by(PredictiveModelRecord.created_at.desc()).limit(limit).offset(offset)).all(); return [_ser(r) for r in rows],int(db.scalar(cnt) or 0)

def add_target(db:Session,model_id:str,payload:dict):
    _reject(payload); _model(db,model_id); row=PredictiveTargetRecord(model_id=model_id,target_key=str(payload.get("target_key") or "").strip(),label=str(payload.get("label") or "").strip(),value_kind=str(payload.get("value_kind") or "numeric"),unit=payload.get("unit"),horizon_json=dict(payload.get("horizon") or {}),source_ref=payload.get("source_ref"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.target_key or not row.label: raise ValueError("target_key and label are required")
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_feature(db:Session,model_id:str,payload:dict):
    _reject(payload); _model(db,model_id); role=str(payload.get("feature_role") or "predictor"); product=str(payload.get("source_product") or "external")
    if role not in FEATURE_ROLES: raise ValueError(f"feature_role must be one of {sorted(FEATURE_ROLES)}")
    if product not in RUNTIME_PRODUCTS|{"platform-core","knowledge-library","research-librarian"}: raise ValueError("unsupported source_product")
    source_ref=str(payload.get("source_ref") or "").strip();
    if not source_ref: raise ValueError("source_ref is required")
    row=PredictiveFeatureRecord(model_id=model_id,feature_key=str(payload.get("feature_key") or "").strip(),label=str(payload.get("label") or "").strip(),feature_role=role,value_kind=str(payload.get("value_kind") or "numeric"),unit=payload.get("unit"),source_product=product,source_ref=source_ref,lag_json=dict(payload.get("lag") or {}),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.feature_key or not row.label: raise ValueError("feature_key and label are required")
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_training_window(db:Session,model_id:str,payload:dict):
    _reject(payload); _model(db,model_id); dataset_ref=str(payload.get("dataset_ref") or "").strip();
    if not dataset_ref: raise ValueError("dataset_ref is required")
    row=PredictiveTrainingWindowRecord(model_id=model_id,window_key=str(payload.get("window_key") or "").strip(),start_time=_parse_dt(payload.get("start_time")),end_time=_parse_dt(payload.get("end_time")),cutoff_time=_parse_dt(payload.get("cutoff_time")),dataset_ref=dataset_ref,input_manifest_hash=_digest(payload.get("input_manifest_hash")),split_strategy_json=dict(payload.get("split_strategy") or {}),provenance_json=dict(payload.get("provenance") or {}))
    if not row.window_key: raise ValueError("window_key is required")
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_forecast_run(db:Session,model_id:str,payload:dict):
    _reject(payload); model=_model(db,model_id); tw=payload.get("training_window_id")
    if tw:
        win=db.get(PredictiveTrainingWindowRecord,tw)
        if win is None or win.model_id!=model_id: raise ValueError("training_window_id must belong to model_id")
    runtime=str(payload.get("runtime_product") or model.runtime_product)
    if runtime not in RUNTIME_PRODUCTS: raise ValueError("unsupported runtime_product")
    row=PredictiveForecastRunRecord(model_id=model_id,training_window_id=tw,run_key=str(payload.get("run_key") or "").strip(),issued_at=_parse_dt(payload.get("issued_at")) or datetime.now(timezone.utc),horizon_start=_parse_dt(payload.get("horizon_start")),horizon_end=_parse_dt(payload.get("horizon_end")),runtime_product=runtime,runtime_run_ref=payload.get("runtime_run_ref"),model_version_ref=payload.get("model_version_ref") or model.model_version_ref,input_manifest_hash=_digest(payload.get("input_manifest_hash")),status=str(payload.get("status") or "recorded"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.run_key: raise ValueError("run_key is required")
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_forecast_observation(db:Session,model_id:str,run_id:str,payload:dict):
    _reject(payload); _model(db,model_id); run=db.get(PredictiveForecastRunRecord,run_id)
    if run is None or run.model_id!=model_id: raise ValueError("forecast_run_id must belong to model_id")
    target_id=str(payload.get("target_id") or ""); target=db.get(PredictiveTargetRecord,target_id)
    if target is None or target.model_id!=model_id: raise ValueError("target_id must belong to model_id")
    fv=payload.get("forecast_value")
    if fv is None: raise ValueError("forecast_value is required")
    row=PredictiveForecastObservationRecord(forecast_run_id=run_id,target_id=target_id,valid_time=_parse_dt(payload.get("valid_time")),forecast_value_json=fv if isinstance(fv,dict) else {"value":fv},unit=payload.get("unit") or target.unit,observed_value_json=(payload.get("observed_value") if isinstance(payload.get("observed_value"),dict) else ({"value":payload.get("observed_value")} if payload.get("observed_value") is not None else None)),observation_source_ref=payload.get("observation_source_ref"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_evaluation(db:Session,model_id:str,payload:dict):
    _reject(payload); _model(db,model_id); run_id=payload.get("forecast_run_id")
    if run_id:
        run=db.get(PredictiveForecastRunRecord,run_id)
        if run is None or run.model_id!=model_id: raise ValueError("forecast_run_id must belong to model_id")
    mv=payload.get("metric_value")
    if mv is None: raise ValueError("metric_value is required")
    row=PredictiveEvaluationRecord(model_id=model_id,forecast_run_id=run_id,evaluation_key=str(payload.get("evaluation_key") or "").strip(),metric_name=str(payload.get("metric_name") or "").strip(),metric_value_json=mv if isinstance(mv,dict) else {"value":mv},evaluation_window_json=dict(payload.get("evaluation_window") or {}),evidence_ref=payload.get("evidence_ref"),externally_computed=True,provenance_json=dict(payload.get("provenance") or {}))
    if not row.evaluation_key or not row.metric_name: raise ValueError("evaluation_key and metric_name are required")
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_handoff(db:Session,model_id:str,payload:dict):
    _reject(payload); _model(db,model_id); target=str(payload.get("target_product") or "external")
    if target not in RUNTIME_PRODUCTS: raise ValueError("unsupported target_product")
    key=str(payload.get("handoff_key") or "").strip();
    if not key: raise ValueError("handoff_key is required")
    manifest=dict(payload.get("manifest") or {}); manifest.update({"contract":"sc.predictive.runtime-handoff.v1","model_id":model_id,"target_product":target,"core_executes":False,"automatic_model_selection":False})
    row=PredictiveRuntimeHandoffRecord(model_id=model_id,handoff_key=key,target_product=target,manifest_json=manifest,external_ref=payload.get("external_ref"),status=str(payload.get("status") or "prepared"),provenance_json=dict(payload.get("provenance") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


def _chronology(train_start,train_end,cutoff,test_start,test_end):
    vals={"train_start":_parse_dt(train_start),"train_end":_parse_dt(train_end),"cutoff_time":_parse_dt(cutoff),"test_start":_parse_dt(test_start),"test_end":_parse_dt(test_end)}
    if vals["train_start"] and vals["train_end"] and vals["train_start"]>vals["train_end"]: raise ValueError("train_start must not be after train_end")
    if vals["train_end"] and vals["cutoff_time"] and vals["train_end"]>vals["cutoff_time"]: raise ValueError("train_end must not be after cutoff_time")
    if vals["cutoff_time"] and vals["test_start"] and vals["test_start"]<=vals["cutoff_time"]: raise ValueError("test_start must be after cutoff_time to prevent temporal leakage")
    if vals["test_start"] and vals["test_end"] and vals["test_start"]>vals["test_end"]: raise ValueError("test_start must not be after test_end")
    return vals

def add_time_series_dataset(db:Session,model_id:str,payload:dict):
    _reject(payload); _model(db,model_id); source_product=str(payload.get("source_product") or "external"); source_ref=str(payload.get("source_ref") or "").strip(); time_field=str(payload.get("time_field") or "").strip(); key=str(payload.get("dataset_key") or "").strip()
    if source_product not in RUNTIME_PRODUCTS|{"platform-core","knowledge-library","research-librarian"}: raise ValueError("unsupported source_product")
    if not key or not source_ref or not time_field: raise ValueError("dataset_key, source_ref, and time_field are required")
    row=PredictiveTimeSeriesDatasetRecord(model_id=model_id,dataset_key=key,source_product=source_product,source_ref=source_ref,time_field=time_field,frequency=payload.get("frequency"),timezone_name=payload.get("timezone"),availability_start=_parse_dt(payload.get("availability_start")),availability_end=_parse_dt(payload.get("availability_end")),target_keys_json=list(payload.get("target_keys") or []),schema_json=dict(payload.get("schema") or {}),manifest_hash=_digest(payload.get("manifest_hash")),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_forecast_window(db:Session,model_id:str,payload:dict):
    _reject(payload); _model(db,model_id); strategy=str(payload.get("strategy") or "fixed")
    if strategy not in BACKTEST_STRATEGIES: raise ValueError(f"strategy must be one of {sorted(BACKTEST_STRATEGIES)}")
    t=_chronology(payload.get("train_start"),payload.get("train_end"),payload.get("cutoff_time"),payload.get("test_start"),payload.get("test_end")); key=str(payload.get("window_key") or "").strip()
    if not key: raise ValueError("window_key is required")
    row=PredictiveForecastWindowRecord(model_id=model_id,window_key=key,strategy=strategy,train_start=t["train_start"],train_end=t["train_end"],cutoff_time=t["cutoff_time"],test_start=t["test_start"],test_end=t["test_end"],horizon_json=dict(payload.get("horizon") or {}),step_json=dict(payload.get("step") or {}),leakage_policy_json=dict(payload.get("leakage_policy") or {}),provenance_json=dict(payload.get("provenance") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_baseline_model(db:Session,model_id:str,payload:dict):
    _reject(payload); _model(db,model_id); kind=str(payload.get("baseline_kind") or "naive"); runtime=str(payload.get("runtime_product") or "external"); key=str(payload.get("baseline_key") or "").strip()
    if kind not in BASELINE_KINDS: raise ValueError(f"baseline_kind must be one of {sorted(BASELINE_KINDS)}")
    if runtime not in RUNTIME_PRODUCTS: raise ValueError("unsupported runtime_product")
    if not key: raise ValueError("baseline_key is required")
    row=PredictiveBaselineModelRecord(model_id=model_id,baseline_key=key,baseline_kind=kind,runtime_product=runtime,runtime_model_ref=payload.get("runtime_model_ref"),parameters_json=dict(payload.get("parameters") or {}),status=str(payload.get("status") or "reference"),provenance_json=dict(payload.get("provenance") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def create_backtest_plan(db:Session,model_id:str,payload:dict):
    _reject(payload); model=_model(db,model_id); dataset=db.get(PredictiveTimeSeriesDatasetRecord,str(payload.get("dataset_id") or "")); target=db.get(PredictiveTargetRecord,str(payload.get("target_id") or "")); strategy=str(payload.get("strategy") or "rolling")
    if dataset is None or dataset.model_id!=model_id: raise ValueError("dataset_id must belong to model_id")
    if target is None or target.model_id!=model_id: raise ValueError("target_id must belong to model_id")
    if strategy not in BACKTEST_STRATEGIES: raise ValueError(f"strategy must be one of {sorted(BACKTEST_STRATEGIES)}")
    baseline_ids=list(payload.get("baseline_ids") or [])
    for bid in baseline_ids:
        b=db.get(PredictiveBaselineModelRecord,bid)
        if b is None or b.model_id!=model_id: raise ValueError("all baseline_ids must belong to model_id")
    runtime=str(payload.get("runtime_product") or model.runtime_product)
    if runtime not in RUNTIME_PRODUCTS: raise ValueError("unsupported runtime_product")
    key=str(payload.get("plan_key") or "").strip();
    if not key: raise ValueError("plan_key is required")
    leakage=dict(payload.get("leakage_controls") or {}); leakage.setdefault("strict_temporal_cutoff",True); leakage.setdefault("future_actuals_forbidden_in_inputs",True)
    row=PredictiveBacktestPlanRecord(model_id=model_id,dataset_id=dataset.id,target_id=target.id,plan_key=key,strategy=strategy,initial_train_window_json=dict(payload.get("initial_train_window") or {}),forecast_horizon_json=dict(payload.get("forecast_horizon") or {}),step_json=dict(payload.get("step") or {}),baseline_ids_json=baseline_ids,leakage_controls_json=leakage,runtime_product=runtime,runtime_plan_ref=payload.get("runtime_plan_ref"),status=str(payload.get("status") or "planned"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def _plan(db:Session,model_id:str,plan_id:str)->PredictiveBacktestPlanRecord:
    row=db.get(PredictiveBacktestPlanRecord,plan_id)
    if row is None or row.model_id!=model_id: raise ValueError("backtest_plan_id must belong to model_id")
    return row

def add_backtest_fold(db:Session,model_id:str,plan_id:str,payload:dict):
    _reject(payload); plan=_plan(db,model_id,plan_id); t=_chronology(payload.get("train_start"),payload.get("train_end"),payload.get("cutoff_time"),payload.get("test_start"),payload.get("test_end")); key=str(payload.get("fold_key") or "").strip(); idx=int(payload.get("fold_index",0))
    if not key: raise ValueError("fold_key is required")
    if idx<0: raise ValueError("fold_index must be >= 0")
    leakage={"strict_temporal_cutoff":True,"passed":True,"train_end_lte_cutoff":True,"test_start_gt_cutoff":True}
    row=PredictiveBacktestFoldRecord(backtest_plan_id=plan.id,fold_key=key,fold_index=idx,train_start=t["train_start"],train_end=t["train_end"],cutoff_time=t["cutoff_time"],test_start=t["test_start"],test_end=t["test_end"],runtime_run_ref=payload.get("runtime_run_ref"),input_manifest_hash=_digest(payload.get("input_manifest_hash")),leakage_check_json=leakage,status=str(payload.get("status") or "recorded"),provenance_json=dict(payload.get("provenance") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_backtest_observation(db:Session,model_id:str,plan_id:str,fold_id:str,payload:dict):
    _reject(payload); plan=_plan(db,model_id,plan_id); fold=db.get(PredictiveBacktestFoldRecord,fold_id)
    if fold is None or fold.backtest_plan_id!=plan.id: raise ValueError("backtest_fold_id must belong to backtest_plan_id")
    target=db.get(PredictiveTargetRecord,str(payload.get("target_id") or plan.target_id));
    if target is None or target.model_id!=model_id: raise ValueError("target_id must belong to model_id")
    ck=str(payload.get("comparator_kind") or "model")
    if ck not in COMPARATOR_KINDS: raise ValueError("comparator_kind must be model or baseline")
    pred=payload.get("prediction"); actual=payload.get("actual")
    if pred is None or actual is None: raise ValueError("prediction and actual are required")
    row=PredictiveBacktestObservationRecord(backtest_fold_id=fold.id,target_id=target.id,valid_time=_parse_dt(payload.get("valid_time")),comparator_kind=ck,comparator_ref=payload.get("comparator_ref"),prediction_json=pred if isinstance(pred,dict) else {"value":pred},actual_json=actual if isinstance(actual,dict) else {"value":actual},unit=payload.get("unit") or target.unit,error_json=dict(payload.get("error") or {}),actual_source_ref=payload.get("actual_source_ref"),provenance_json=dict(payload.get("provenance") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_backtest_evaluation(db:Session,model_id:str,plan_id:str,payload:dict):
    _reject(payload); plan=_plan(db,model_id,plan_id); fold_id=payload.get("backtest_fold_id")
    if fold_id:
        fold=db.get(PredictiveBacktestFoldRecord,fold_id)
        if fold is None or fold.backtest_plan_id!=plan.id: raise ValueError("backtest_fold_id must belong to backtest_plan_id")
    ck=str(payload.get("comparator_kind") or "model")
    if ck not in COMPARATOR_KINDS: raise ValueError("comparator_kind must be model or baseline")
    mv=payload.get("metric_value"); key=str(payload.get("evaluation_key") or "").strip(); metric=str(payload.get("metric_name") or "").strip()
    if not key or not metric or mv is None: raise ValueError("evaluation_key, metric_name, and metric_value are required")
    row=PredictiveBacktestEvaluationRecord(backtest_plan_id=plan.id,backtest_fold_id=fold_id,evaluation_key=key,comparator_kind=ck,comparator_ref=payload.get("comparator_ref"),metric_name=metric,metric_value_json=mv if isinstance(mv,dict) else {"value":mv},aggregation_json=dict(payload.get("aggregation") or {}),evidence_ref=payload.get("evidence_ref"),externally_computed=True,provenance_json=dict(payload.get("provenance") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def backtest_bundle(db:Session,model_id:str,plan_id:str):
    plan=_plan(db,model_id,plan_id); dataset=db.get(PredictiveTimeSeriesDatasetRecord,plan.dataset_id); target=db.get(PredictiveTargetRecord,plan.target_id)
    folds=[_ser(x) for x in db.scalars(select(PredictiveBacktestFoldRecord).where(PredictiveBacktestFoldRecord.backtest_plan_id==plan.id).order_by(PredictiveBacktestFoldRecord.fold_index.asc())).all()]
    fold_ids=[x["id"] for x in folds]; observations=[]
    if fold_ids: observations=[_ser(x) for x in db.scalars(select(PredictiveBacktestObservationRecord).where(PredictiveBacktestObservationRecord.backtest_fold_id.in_(fold_ids)).order_by(PredictiveBacktestObservationRecord.valid_time.asc())).all()]
    evaluations=[_ser(x) for x in db.scalars(select(PredictiveBacktestEvaluationRecord).where(PredictiveBacktestEvaluationRecord.backtest_plan_id==plan.id).order_by(PredictiveBacktestEvaluationRecord.created_at.asc())).all()]
    packages=[_ser(x) for x in db.scalars(select(PredictiveBacktestPackageRecord).where(PredictiveBacktestPackageRecord.backtest_plan_id==plan.id).order_by(PredictiveBacktestPackageRecord.revision.asc())).all()]
    baselines=[]
    for bid in plan.baseline_ids_json or []:
        b=db.get(PredictiveBaselineModelRecord,bid)
        if b is not None: baselines.append(_ser(b))
    return {"contract":"sc.predictive.backtest-package.v1","plan":_ser(plan),"dataset":_ser(dataset),"target":_ser(target),"baselines":baselines,"folds":folds,"observations":observations,"evaluations":evaluations,"packages":packages,"boundaries":boundaries()}

def create_backtest_package(db:Session,model_id:str,plan_id:str,payload:dict):
    _reject(payload); state=backtest_bundle(db,model_id,plan_id); state.pop("packages",None); digest=_sha256(state); last=db.scalar(select(PredictiveBacktestPackageRecord).where(PredictiveBacktestPackageRecord.backtest_plan_id==plan_id).order_by(PredictiveBacktestPackageRecord.revision.desc())); rev=(last.revision+1) if last else 1
    row=PredictiveBacktestPackageRecord(backtest_plan_id=plan_id,revision=rev,content_hash=digest,previous_package_hash=(last.content_hash if last else None),state_json=state,environment_json=dict(payload.get("environment") or {}),provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)

def bundle(db:Session,model_id:str,public_only=False):
    model=_model(db,model_id)
    if public_only and model.visibility!="public": raise HTTPException(status_code=404,detail="Predictive model not found.")
    q=lambda m: [_ser(x) for x in db.scalars(select(m).where(m.model_id==model_id).order_by(m.created_at.asc())).all()]
    targets=q(PredictiveTargetRecord); features=q(PredictiveFeatureRecord); windows=q(PredictiveTrainingWindowRecord); runs=q(PredictiveForecastRunRecord); evals=q(PredictiveEvaluationRecord); handoffs=q(PredictiveRuntimeHandoffRecord); snaps=q(PredictiveForecastSnapshotRecord)
    ts_datasets=q(PredictiveTimeSeriesDatasetRecord); forecast_windows=q(PredictiveForecastWindowRecord); baselines=q(PredictiveBaselineModelRecord); backtest_plans=q(PredictiveBacktestPlanRecord)
    observations=[]
    runids=[r["id"] for r in runs]
    if runids: observations=[_ser(x) for x in db.scalars(select(PredictiveForecastObservationRecord).where(PredictiveForecastObservationRecord.forecast_run_id.in_(runids)).order_by(PredictiveForecastObservationRecord.created_at.asc())).all()]
    return {"contract":"sc.predictive.forecast-provenance.v1","model":_ser(model),"targets":targets,"features":features,"training_windows":windows,"forecast_runs":runs,"forecast_observations":observations,"evaluations":evals,"handoffs":handoffs,"snapshots":snaps,"time_series_datasets":ts_datasets,"forecast_windows":forecast_windows,"baseline_models":baselines,"backtest_plans":backtest_plans,"boundaries":boundaries()}

def create_snapshot(db:Session,model_id:str,payload:dict):
    _reject(payload); state=bundle(db,model_id); state.pop("snapshots",None); digest=_sha256(state); last=db.scalar(select(PredictiveForecastSnapshotRecord).where(PredictiveForecastSnapshotRecord.model_id==model_id).order_by(PredictiveForecastSnapshotRecord.revision.desc()))
    rev=(last.revision+1) if last else 1; row=PredictiveForecastSnapshotRecord(model_id=model_id,revision=rev,content_hash=digest,previous_snapshot_hash=(last.content_hash if last else None),state_json=state,provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)
