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
    PredictiveProbabilisticForecastRecord, PredictiveCalibrationStudyRecord, PredictiveCalibrationBinRecord, PredictiveCalibrationMappingRecord,
    PredictiveProbabilisticEvaluationRecord, PredictiveCalibrationPackageRecord,
    PredictiveEnsembleRecord, PredictiveEnsembleMemberRecord, PredictiveEnsembleForecastRecord,
    PredictiveComparisonStudyRecord, PredictiveComparisonCandidateRecord, PredictiveComparisonEvidenceRecord,
    PredictivePairwiseComparisonRecord, PredictiveComparisonPackageRecord,
    PredictiveMonitoringStudyRecord, PredictiveDetectionRuleRecord, PredictiveAnomalyObservationRecord,
    PredictiveChangePointRecord, PredictiveEarlyWarningSignalRecord, PredictiveMonitoringEpisodeRecord, PredictiveMonitoringPackageRecord,
    PredictiveSpatialTemporalStudyRecord, PredictiveSpatialUnitRecord, PredictiveSpatialTemporalForecastRecord, PredictiveSpatialTemporalObservationRecord,
    PredictiveSpatialPropagationEvidenceRecord, PredictiveSpatialHotspotEvidenceRecord, PredictiveSpatialTemporalEvaluationRecord, PredictiveSpatialTemporalPackageRecord,
    CausalGraphRecord, CausalVariableRecord, CausalInterventionRecord, CausalIdentificationRecord, CausalEstimateRecord,
    PredictiveCausalStudyRecord, PredictiveCausalVariableBindingRecord, PredictiveInterventionScenarioRecord,
    PredictiveCounterfactualForecastRecord, PredictiveCausalEffectEvidenceRecord, PredictiveCausalEvaluationRecord,
    PredictiveCausalHandoffRecord, PredictiveCausalPackageRecord,
)

MODEL_KINDS={"statistical","machine-learning","simulation","hybrid","rules-based","external","other"}
RUNTIME_PRODUCTS={"lab","workbench","site-intelligence","decision-studio","catalyst-data","external"}
FEATURE_ROLES={"predictor","lagged-predictor","exogenous","context","identifier","time-index","other"}
BACKTEST_STRATEGIES={"fixed","rolling","expanding"}
BASELINE_KINDS={"naive","seasonal-naive","drift","mean","median","external","other"}
COMPARATOR_KINDS={"model","baseline"}
PROBABILISTIC_REPRESENTATIONS={"binary-event","categorical","quantile","interval","parametric-distribution","empirical-samples","ensemble-distribution"}
CALIBRATION_ASSESSMENTS={"reliability","coverage","quantile-coverage","pit","rank-histogram","categorical-reliability","threshold-reliability","other"}
CALIBRATION_METHODS={"platt","isotonic","temperature","beta","histogram","conformal","external","other"}
PROBABILISTIC_METRIC_FAMILIES={"proper-scoring-rule","calibration","coverage","sharpness","distribution-diagnostic","other"}
ENSEMBLE_KINDS={"weighted-average","stacking","bagging","boosting","mixture","voting","external","other"}
ENSEMBLE_MEMBER_ROLES={"member","base-learner","meta-learner","expert","reference","other"}
COMPARISON_CANDIDATE_KINDS={"model","ensemble","baseline","external"}
COMPARISON_METRIC_FAMILIES={"point-error","proper-scoring-rule","calibration","coverage","sharpness","classification","ranking-diagnostic","resource","robustness","other"}
PAIRWISE_COMPARISON_KINDS={"metric-difference","loss-difference","skill-difference","paired-test","bootstrap-contrast","bayesian-contrast","other"}
MONITORING_KINDS={"anomaly","change-point","early-warning","multi-signal","external","other"}
DETECTION_RULE_KINDS={"anomaly-threshold","change-point","early-warning","composite","external","other"}
ANOMALY_KINDS={"point","contextual","collective","distribution-shift","residual","forecast-error","external","other"}
EARLY_WARNING_SIGNAL_KINDS={"threshold-proximity","trend-acceleration","variance-change","autocorrelation-change","critical-slowing","forecast-risk","external","other"}
SPATIAL_UNIT_KINDS={"point","grid-cell","region","administrative-area","watershed","corridor","network-node","external","other"}
SPATIAL_FORECAST_REPRESENTATIONS={"point","probability","quantile","interval","distribution","categorical","field","external","other"}
CAUSAL_PREDICTIVE_INTEGRATION_KINDS={"causal-forecast","intervention-forecast","counterfactual-forecast","effect-informed-forecast","causal-feature-governance","external","other"}
CAUSAL_BINDING_ROLES={"target","predictor","treatment","outcome","confounder","mediator","effect-modifier","context","other"}
FORBIDDEN_FIELDS={"fit_by_core","train_by_core","infer_by_core","execute_by_core","core_execute","probability_calibrated_by_core","winner","rank","verdict","truth_value","automatic_truth_promotion","model_selected_by_core","backtest_execute_by_core","metric_compute_by_core","resample_by_core","probabilistic_infer_by_core","calibration_fit_by_core","recalibration_apply_by_core","scoring_rule_compute_by_core","calibration_metric_compute_by_core","ensemble_construct_by_core","ensemble_execute_by_core","ensemble_weight_optimize_by_core","comparison_metric_compute_by_core","significance_compute_by_core","rank_models_by_core","select_model_by_core","automatic_model_selection","anomaly_detect_by_core","change_point_detect_by_core","early_warning_compute_by_core","threshold_optimize_by_core","alert_dispatch_by_core","causal_attribution_by_core","automatic_intervention_by_core","spatial_interpolate_by_core","spatial_infer_by_core","trajectory_predict_by_core","propagation_model_by_core","hotspot_detect_by_core","spatial_metric_compute_by_core","causal_structure_learn_by_core","causal_identify_by_core","causal_effect_estimate_by_core","counterfactual_execute_by_core","intervention_simulate_by_core","causal_predictive_metric_compute_by_core","decision_optimize_by_core"}

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
      "probabilistic_forecast_registry_by_core":True,"uncertainty_distribution_registry_by_core":True,"calibration_study_registry_by_core":True,
      "calibration_bin_evidence_by_core":True,"external_calibration_mapping_registry_by_core":True,"proper_scoring_evidence_registry_by_core":True,
      "reproducible_calibration_packages_by_core":True,
      "ensemble_registry_by_core":True,"ensemble_member_registry_by_core":True,"ensemble_forecast_provenance_by_core":True,
      "model_comparison_study_registry_by_core":True,"comparison_candidate_registry_by_core":True,"comparative_metric_evidence_by_core":True,
      "pairwise_comparison_evidence_by_core":True,"reproducible_model_comparison_packages_by_core":True,
      "monitoring_study_registry_by_core":True,"detection_rule_registry_by_core":True,"anomaly_evidence_registry_by_core":True,
      "change_point_evidence_registry_by_core":True,"early_warning_signal_registry_by_core":True,"monitoring_episode_registry_by_core":True,"reproducible_monitoring_packages_by_core":True,
      "spatial_temporal_study_registry_by_core":True,"spatial_unit_registry_by_core":True,"spatial_temporal_forecast_provenance_by_core":True,
      "spatial_temporal_observation_registry_by_core":True,"propagation_evidence_registry_by_core":True,"hotspot_evidence_registry_by_core":True,
      "spatial_temporal_evaluation_evidence_by_core":True,"reproducible_spatial_temporal_packages_by_core":True,
      "causal_predictive_study_registry_by_core":True,"causal_variable_binding_registry_by_core":True,"intervention_scenario_registry_by_core":True,
      "counterfactual_forecast_provenance_by_core":True,"causal_effect_evidence_registry_by_core":True,"causal_predictive_evaluation_evidence_by_core":True,
      "causal_predictive_handoff_registry_by_core":True,"reproducible_causal_predictive_packages_by_core":True,
      "model_fitting_by_core":False,"forecast_inference_execution_by_core":False,"backtest_execution_by_core":False,"metric_computation_by_core":False,
      "time_series_resampling_by_core":False,"probabilistic_calibration_by_core":False,"ensemble_selection_by_core":False,
      "probabilistic_inference_execution_by_core":False,"calibration_mapping_fitting_by_core":False,"calibration_mapping_application_by_core":False,
      "proper_scoring_rule_computation_by_core":False,"calibration_metric_computation_by_core":False,"probabilistic_model_ranking_by_core":False,
      "ensemble_construction_by_core":False,"ensemble_weight_optimization_by_core":False,"ensemble_forecast_execution_by_core":False,
      "model_comparison_metric_computation_by_core":False,"statistical_significance_computation_by_core":False,"model_ranking_by_core":False,"automatic_model_selection":False,
      "anomaly_detection_by_core":False,"change_point_detection_by_core":False,"early_warning_computation_by_core":False,"threshold_optimization_by_core":False,
      "alert_dispatch_by_core":False,"causal_attribution_by_core":False,"automatic_intervention_by_core":False,
      "spatial_interpolation_by_core":False,"spatial_inference_execution_by_core":False,"trajectory_prediction_by_core":False,"propagation_modeling_by_core":False,
      "hotspot_detection_by_core":False,"spatial_temporal_metric_computation_by_core":False,
      "causal_structure_learning_by_core":False,"causal_identification_by_core":False,"causal_effect_estimation_by_core":False,
      "counterfactual_execution_by_core":False,"intervention_simulation_by_core":False,"causal_predictive_metric_computation_by_core":False,"decision_optimization_by_core":False,
      "automatic_model_ranking_by_core":False,"automatic_truth_promotion":False,
    }

def readiness(db:Session):
    def count(m): return int(db.scalar(select(func.count()).select_from(m)) or 0)
    return {"migration_0056_applied":True,"migration_0057_applied":True,"migration_0058_applied":True,"migration_0059_applied":True,"migration_0060_applied":True,"migration_0061_applied":True,"migration_0062_applied":True,"contract":"sc.predictive.model.v1","forecast_contract":"sc.predictive.forecast-provenance.v1","handoff_contract":"sc.predictive.runtime-handoff.v1","backtest_contract":"sc.predictive.backtest-plan.v1","backtest_package_contract":"sc.predictive.backtest-package.v1","probabilistic_forecast_contract":"sc.predictive.probabilistic-forecast.v1","calibration_study_contract":"sc.predictive.calibration-study.v1","calibration_package_contract":"sc.predictive.calibration-package.v1","ensemble_contract":"sc.predictive.ensemble.v1","model_comparison_contract":"sc.predictive.model-comparison.v1","model_comparison_package_contract":"sc.predictive.model-comparison-package.v1","monitoring_study_contract":"sc.predictive.monitoring-study.v1","monitoring_package_contract":"sc.predictive.monitoring-package.v1","spatial_temporal_study_contract":"sc.predictive.spatial-temporal-study.v1","spatial_temporal_package_contract":"sc.predictive.spatial-temporal-package.v1","causal_predictive_study_contract":"sc.predictive.causal-study.v1","causal_predictive_package_contract":"sc.predictive.causal-package.v1","counts":{
      "models":count(PredictiveModelRecord),"targets":count(PredictiveTargetRecord),"features":count(PredictiveFeatureRecord),"training_windows":count(PredictiveTrainingWindowRecord),
      "forecast_runs":count(PredictiveForecastRunRecord),"forecast_observations":count(PredictiveForecastObservationRecord),"evaluations":count(PredictiveEvaluationRecord),"handoffs":count(PredictiveRuntimeHandoffRecord),"snapshots":count(PredictiveForecastSnapshotRecord),
      "time_series_datasets":count(PredictiveTimeSeriesDatasetRecord),"forecast_windows":count(PredictiveForecastWindowRecord),"baseline_models":count(PredictiveBaselineModelRecord),"backtest_plans":count(PredictiveBacktestPlanRecord),
      "backtest_folds":count(PredictiveBacktestFoldRecord),"backtest_observations":count(PredictiveBacktestObservationRecord),"backtest_evaluations":count(PredictiveBacktestEvaluationRecord),"backtest_packages":count(PredictiveBacktestPackageRecord),
      "probabilistic_forecasts":count(PredictiveProbabilisticForecastRecord),"calibration_studies":count(PredictiveCalibrationStudyRecord),"calibration_bins":count(PredictiveCalibrationBinRecord),
      "calibration_mappings":count(PredictiveCalibrationMappingRecord),"probabilistic_evaluations":count(PredictiveProbabilisticEvaluationRecord),"calibration_packages":count(PredictiveCalibrationPackageRecord),
      "ensembles":count(PredictiveEnsembleRecord),"ensemble_members":count(PredictiveEnsembleMemberRecord),"ensemble_forecasts":count(PredictiveEnsembleForecastRecord),
      "comparison_studies":count(PredictiveComparisonStudyRecord),"comparison_candidates":count(PredictiveComparisonCandidateRecord),"comparison_evidence":count(PredictiveComparisonEvidenceRecord),"pairwise_comparisons":count(PredictivePairwiseComparisonRecord),"comparison_packages":count(PredictiveComparisonPackageRecord),
      "monitoring_studies":count(PredictiveMonitoringStudyRecord),"detection_rules":count(PredictiveDetectionRuleRecord),"anomaly_observations":count(PredictiveAnomalyObservationRecord),
      "change_points":count(PredictiveChangePointRecord),"early_warning_signals":count(PredictiveEarlyWarningSignalRecord),"monitoring_episodes":count(PredictiveMonitoringEpisodeRecord),"monitoring_packages":count(PredictiveMonitoringPackageRecord),
      "spatial_temporal_studies":count(PredictiveSpatialTemporalStudyRecord),"spatial_units":count(PredictiveSpatialUnitRecord),"spatial_temporal_forecasts":count(PredictiveSpatialTemporalForecastRecord),
      "spatial_temporal_observations":count(PredictiveSpatialTemporalObservationRecord),"spatial_propagation_evidence":count(PredictiveSpatialPropagationEvidenceRecord),"spatial_hotspot_evidence":count(PredictiveSpatialHotspotEvidenceRecord),
      "spatial_temporal_evaluations":count(PredictiveSpatialTemporalEvaluationRecord),"spatial_temporal_packages":count(PredictiveSpatialTemporalPackageRecord),
      "causal_predictive_studies":count(PredictiveCausalStudyRecord),"causal_variable_bindings":count(PredictiveCausalVariableBindingRecord),"intervention_scenarios":count(PredictiveInterventionScenarioRecord),
      "counterfactual_forecasts":count(PredictiveCounterfactualForecastRecord),"causal_effect_evidence":count(PredictiveCausalEffectEvidenceRecord),"causal_predictive_evaluations":count(PredictiveCausalEvaluationRecord),
      "causal_predictive_handoffs":count(PredictiveCausalHandoffRecord),"causal_predictive_packages":count(PredictiveCausalPackageRecord)},**boundaries()}

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
    probabilistic_forecasts=q(PredictiveProbabilisticForecastRecord); calibration_studies=q(PredictiveCalibrationStudyRecord); probabilistic_evaluations=q(PredictiveProbabilisticEvaluationRecord)
    ensemble_memberships=[_ser(x) for x in db.scalars(select(PredictiveEnsembleMemberRecord).where(PredictiveEnsembleMemberRecord.model_id==model_id).order_by(PredictiveEnsembleMemberRecord.created_at.asc())).all()]
    monitoring_studies=[_ser(x) for x in db.scalars(select(PredictiveMonitoringStudyRecord).where(PredictiveMonitoringStudyRecord.model_id==model_id).order_by(PredictiveMonitoringStudyRecord.created_at.asc())).all()]
    spatial_temporal_studies=[_ser(x) for x in db.scalars(select(PredictiveSpatialTemporalStudyRecord).where(PredictiveSpatialTemporalStudyRecord.model_id==model_id).order_by(PredictiveSpatialTemporalStudyRecord.created_at.asc())).all()]
    causal_predictive_studies=[_ser(x) for x in db.scalars(select(PredictiveCausalStudyRecord).where(PredictiveCausalStudyRecord.predictive_model_id==model_id).order_by(PredictiveCausalStudyRecord.created_at.asc())).all()]
    observations=[]
    runids=[r["id"] for r in runs]
    if runids: observations=[_ser(x) for x in db.scalars(select(PredictiveForecastObservationRecord).where(PredictiveForecastObservationRecord.forecast_run_id.in_(runids)).order_by(PredictiveForecastObservationRecord.created_at.asc())).all()]
    return {"contract":"sc.predictive.forecast-provenance.v1","model":_ser(model),"targets":targets,"features":features,"training_windows":windows,"forecast_runs":runs,"forecast_observations":observations,"evaluations":evals,"handoffs":handoffs,"snapshots":snaps,"time_series_datasets":ts_datasets,"forecast_windows":forecast_windows,"baseline_models":baselines,"backtest_plans":backtest_plans,"probabilistic_forecasts":probabilistic_forecasts,"calibration_studies":calibration_studies,"probabilistic_evaluations":probabilistic_evaluations,"ensemble_memberships":ensemble_memberships,"monitoring_studies":monitoring_studies,"spatial_temporal_studies":spatial_temporal_studies,"causal_predictive_studies":causal_predictive_studies,"boundaries":boundaries()}

def create_snapshot(db:Session,model_id:str,payload:dict):
    _reject(payload); state=bundle(db,model_id); state.pop("snapshots",None); digest=_sha256(state); last=db.scalar(select(PredictiveForecastSnapshotRecord).where(PredictiveForecastSnapshotRecord.model_id==model_id).order_by(PredictiveForecastSnapshotRecord.revision.desc()))
    rev=(last.revision+1) if last else 1; row=PredictiveForecastSnapshotRecord(model_id=model_id,revision=rev,content_hash=digest,previous_snapshot_hash=(last.content_hash if last else None),state_json=state,provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)

def _probability(value,name="probability"):
    try: v=float(value)
    except (TypeError,ValueError) as exc: raise ValueError(f"{name} must be numeric") from exc
    if not 0.0<=v<=1.0: raise ValueError(f"{name} must be between 0 and 1")
    return v

def _validate_probabilistic_payload(representation:str, forecast:dict):
    if representation=="binary-event":
        if "probability" not in forecast: raise ValueError("binary-event forecast requires probability")
        _probability(forecast["probability"])
    elif representation=="categorical":
        probs=forecast.get("probabilities")
        if not isinstance(probs,dict) or not probs: raise ValueError("categorical forecast requires non-empty probabilities object")
        vals=[_probability(v,f"probability[{k}]") for k,v in probs.items()]
        if abs(sum(vals)-1.0)>1e-6: raise ValueError("categorical probabilities must sum to 1")
    elif representation=="quantile":
        qs=forecast.get("quantiles")
        if not isinstance(qs,dict) or not qs: raise ValueError("quantile forecast requires non-empty quantiles object")
        pairs=[]
        for q,v in qs.items():
            qq=_probability(q,f"quantile[{q}]"); pairs.append((qq,float(v)))
        pairs.sort()
        if any(pairs[i][1]>pairs[i+1][1] for i in range(len(pairs)-1)): raise ValueError("quantile forecast values must be nondecreasing with quantile")
    elif representation=="interval":
        intervals=forecast.get("intervals")
        if not isinstance(intervals,list) or not intervals: raise ValueError("interval forecast requires non-empty intervals array")
        for item in intervals:
            level=_probability(item.get("level"),"interval level")
            if level in (0.0,1.0): raise ValueError("interval level must be strictly between 0 and 1")
            lo=float(item.get("lower")); hi=float(item.get("upper"))
            if lo>hi: raise ValueError("interval lower must not exceed upper")
    elif representation in {"parametric-distribution","ensemble-distribution"}:
        if not str(forecast.get("family") or "").strip(): raise ValueError("distribution forecast requires family")
        if not isinstance(forecast.get("parameters"),dict): raise ValueError("distribution forecast requires parameters object")
    elif representation=="empirical-samples":
        if not str(forecast.get("sample_ref") or "").strip(): raise ValueError("empirical-samples forecast requires sample_ref")
    return forecast

def add_probabilistic_forecast(db:Session,model_id:str,payload:dict):
    _reject(payload); _model(db,model_id)
    target=db.get(PredictiveTargetRecord,str(payload.get("target_id") or ""))
    if target is None or target.model_id!=model_id: raise ValueError("target_id must belong to model_id")
    run_id=payload.get("forecast_run_id"); fold_id=payload.get("backtest_fold_id")
    if bool(run_id)==bool(fold_id): raise ValueError("exactly one of forecast_run_id or backtest_fold_id is required")
    if run_id:
        run=db.get(PredictiveForecastRunRecord,run_id)
        if run is None or run.model_id!=model_id: raise ValueError("forecast_run_id must belong to model_id")
    if fold_id:
        fold=db.get(PredictiveBacktestFoldRecord,fold_id)
        if fold is None: raise ValueError("backtest_fold_id is invalid")
        plan=db.get(PredictiveBacktestPlanRecord,fold.backtest_plan_id)
        if plan is None or plan.model_id!=model_id: raise ValueError("backtest_fold_id must belong to model_id")
    rep=str(payload.get("representation") or "").strip()
    if rep not in PROBABILISTIC_REPRESENTATIONS: raise ValueError(f"representation must be one of {sorted(PROBABILISTIC_REPRESENTATIONS)}")
    forecast=payload.get("forecast")
    if not isinstance(forecast,dict): raise ValueError("forecast must be an object")
    _validate_probabilistic_payload(rep,forecast)
    mapping_id=payload.get("calibration_mapping_id")
    if mapping_id:
        mapping=db.get(PredictiveCalibrationMappingRecord,mapping_id)
        if mapping is None: raise ValueError("calibration_mapping_id is invalid")
        study=db.get(PredictiveCalibrationStudyRecord,mapping.calibration_study_id)
        if study is None or study.model_id!=model_id: raise ValueError("calibration_mapping_id must belong to model_id")
    row=PredictiveProbabilisticForecastRecord(model_id=model_id,target_id=target.id,forecast_run_id=run_id,backtest_fold_id=fold_id,valid_time=_parse_dt(payload.get("valid_time")),representation=rep,forecast_json=forecast,calibration_mapping_id=mapping_id,source_ref=payload.get("source_ref"),externally_generated=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def create_calibration_study(db:Session,model_id:str,payload:dict):
    _reject(payload); _model(db,model_id)
    target=db.get(PredictiveTargetRecord,str(payload.get("target_id") or ""))
    if target is None or target.model_id!=model_id: raise ValueError("target_id must belong to model_id")
    key=str(payload.get("study_key") or "").strip(); kind=str(payload.get("assessment_kind") or "reliability")
    if not key: raise ValueError("study_key is required")
    if kind not in CALIBRATION_ASSESSMENTS: raise ValueError(f"assessment_kind must be one of {sorted(CALIBRATION_ASSESSMENTS)}")
    row=PredictiveCalibrationStudyRecord(model_id=model_id,target_id=target.id,study_key=key,assessment_kind=kind,scope_json=dict(payload.get("scope") or {}),expected_calibration_json=dict(payload.get("expected_calibration") or {}),actual_outcome_source_ref=payload.get("actual_outcome_source_ref"),status=str(payload.get("status") or "recorded"),externally_computed=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("study_key must be unique within model_id") from exc
    db.refresh(row); return _ser(row)

def _study(db:Session,model_id:str,study_id:str)->PredictiveCalibrationStudyRecord:
    row=db.get(PredictiveCalibrationStudyRecord,study_id)
    if row is None or row.model_id!=model_id: raise ValueError("calibration_study_id must belong to model_id")
    return row

def add_calibration_bin(db:Session,model_id:str,study_id:str,payload:dict):
    _reject(payload); _study(db,model_id,study_id); idx=int(payload.get("bin_index",0))
    if idx<0: raise ValueError("bin_index must be >= 0")
    vals={k:(None if payload.get(k) is None else _probability(payload.get(k),k)) for k in ("lower_bound","upper_bound","mean_forecast","observed_frequency")}
    if vals["lower_bound"] is not None and vals["upper_bound"] is not None and vals["lower_bound"]>vals["upper_bound"]: raise ValueError("lower_bound must not exceed upper_bound")
    n=int(payload.get("sample_count",0))
    if n<0: raise ValueError("sample_count must be >= 0")
    row=PredictiveCalibrationBinRecord(calibration_study_id=study_id,bin_index=idx,lower_bound=vals["lower_bound"],upper_bound=vals["upper_bound"],mean_forecast=vals["mean_forecast"],observed_frequency=vals["observed_frequency"],sample_count=n,expected_json=dict(payload.get("expected") or {}),metadata_json=dict(payload.get("metadata") or {}),provenance_json=dict(payload.get("provenance") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_calibration_mapping(db:Session,model_id:str,study_id:str,payload:dict):
    _reject(payload); _study(db,model_id,study_id); key=str(payload.get("mapping_key") or "").strip(); method=str(payload.get("method") or "external")
    if not key: raise ValueError("mapping_key is required")
    if method not in CALIBRATION_METHODS: raise ValueError(f"method must be one of {sorted(CALIBRATION_METHODS)}")
    row=PredictiveCalibrationMappingRecord(calibration_study_id=study_id,mapping_key=key,method=method,parameters_json=dict(payload.get("parameters") or {}),fit_evidence_ref=payload.get("fit_evidence_ref"),source_forecast_contract=str(payload.get("source_forecast_contract") or "sc.predictive.probabilistic-forecast.v1"),output_contract=str(payload.get("output_contract") or "sc.predictive.probabilistic-forecast.v1"),externally_fitted=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_probabilistic_evaluation(db:Session,model_id:str,payload:dict):
    _reject(payload); _model(db,model_id); study_id=payload.get("calibration_study_id"); forecast_id=payload.get("probabilistic_forecast_id")
    if study_id: _study(db,model_id,study_id)
    if forecast_id:
        f=db.get(PredictiveProbabilisticForecastRecord,forecast_id)
        if f is None or f.model_id!=model_id: raise ValueError("probabilistic_forecast_id must belong to model_id")
    family=str(payload.get("metric_family") or "other"); key=str(payload.get("evaluation_key") or "").strip(); metric=str(payload.get("metric_name") or "").strip(); mv=payload.get("metric_value")
    if family not in PROBABILISTIC_METRIC_FAMILIES: raise ValueError(f"metric_family must be one of {sorted(PROBABILISTIC_METRIC_FAMILIES)}")
    if not key or not metric or mv is None: raise ValueError("evaluation_key, metric_name, and metric_value are required")
    row=PredictiveProbabilisticEvaluationRecord(model_id=model_id,calibration_study_id=study_id,probabilistic_forecast_id=forecast_id,evaluation_key=key,metric_family=family,metric_name=metric,metric_value_json=mv if isinstance(mv,dict) else {"value":mv},aggregation_json=dict(payload.get("aggregation") or {}),evidence_ref=payload.get("evidence_ref"),externally_computed=True,provenance_json=dict(payload.get("provenance") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def calibration_bundle(db:Session,model_id:str,study_id:str):
    study=_study(db,model_id,study_id); target=db.get(PredictiveTargetRecord,study.target_id)
    bins=[_ser(x) for x in db.scalars(select(PredictiveCalibrationBinRecord).where(PredictiveCalibrationBinRecord.calibration_study_id==study_id).order_by(PredictiveCalibrationBinRecord.bin_index.asc())).all()]
    mappings=[_ser(x) for x in db.scalars(select(PredictiveCalibrationMappingRecord).where(PredictiveCalibrationMappingRecord.calibration_study_id==study_id).order_by(PredictiveCalibrationMappingRecord.created_at.asc())).all()]
    evaluations=[_ser(x) for x in db.scalars(select(PredictiveProbabilisticEvaluationRecord).where(PredictiveProbabilisticEvaluationRecord.calibration_study_id==study_id).order_by(PredictiveProbabilisticEvaluationRecord.created_at.asc())).all()]
    packages=[_ser(x) for x in db.scalars(select(PredictiveCalibrationPackageRecord).where(PredictiveCalibrationPackageRecord.calibration_study_id==study_id).order_by(PredictiveCalibrationPackageRecord.revision.asc())).all()]
    return {"contract":"sc.predictive.calibration-package.v1","study":_ser(study),"target":_ser(target),"bins":bins,"mappings":mappings,"evaluations":evaluations,"packages":packages,"boundaries":boundaries()}

def create_calibration_package(db:Session,model_id:str,study_id:str,payload:dict):
    _reject(payload); state=calibration_bundle(db,model_id,study_id); state.pop("packages",None); digest=_sha256(state)
    last=db.scalar(select(PredictiveCalibrationPackageRecord).where(PredictiveCalibrationPackageRecord.calibration_study_id==study_id).order_by(PredictiveCalibrationPackageRecord.revision.desc())); rev=(last.revision+1) if last else 1
    row=PredictiveCalibrationPackageRecord(calibration_study_id=study_id,revision=rev,content_hash=digest,previous_package_hash=(last.content_hash if last else None),state_json=state,environment_json=dict(payload.get("environment") or {}),provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def create_ensemble(db:Session,payload:dict):
    _reject(payload)
    project=str(payload.get("project_entity_id") or "").strip(); ent=db.get(Entity,project)
    if ent is None: raise ValueError("project_entity_id must reference an existing Core entity")
    key=str(payload.get("ensemble_key") or "").strip(); name=str(payload.get("name") or "").strip(); kind=str(payload.get("ensemble_kind") or "external")
    if not key or not name: raise ValueError("ensemble_key and name are required")
    if kind not in ENSEMBLE_KINDS: raise ValueError(f"ensemble_kind must be one of {sorted(ENSEMBLE_KINDS)}")
    vis=str(payload.get("visibility") or "private")
    if vis not in {"private","public"}: raise ValueError("visibility must be private or public")
    row=PredictiveEnsembleRecord(project_entity_id=project,ensemble_key=key,name=name,description=payload.get("description"),ensemble_kind=kind,target_semantics_json=dict(payload.get("target_semantics") or {}),combination_rule_json=dict(payload.get("combination_rule") or {}),status=str(payload.get("status") or "draft"),visibility=vis,externally_defined=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("ensemble_key must be unique within project_entity_id") from exc
    db.refresh(row); return _ser(row)

def _ensemble(db:Session,ensemble_id:str)->PredictiveEnsembleRecord:
    row=db.get(PredictiveEnsembleRecord,ensemble_id)
    if row is None: raise HTTPException(status_code=404,detail="Predictive ensemble not found.")
    return row

def add_ensemble_member(db:Session,ensemble_id:str,payload:dict):
    _reject(payload); ensemble=_ensemble(db,ensemble_id)
    model=db.get(PredictiveModelRecord,str(payload.get("model_id") or ""))
    if model is None: raise ValueError("model_id must reference an existing predictive model")
    if model.project_entity_id!=ensemble.project_entity_id: raise ValueError("ensemble members must belong to the ensemble project")
    key=str(payload.get("member_key") or "").strip(); role=str(payload.get("role") or "member")
    if not key: raise ValueError("member_key is required")
    if role not in ENSEMBLE_MEMBER_ROLES: raise ValueError(f"role must be one of {sorted(ENSEMBLE_MEMBER_ROLES)}")
    weight=payload.get("weight")
    if weight is not None: weight=float(weight)
    row=PredictiveEnsembleMemberRecord(ensemble_id=ensemble.id,model_id=model.id,member_key=key,role=role,weight=weight,runtime_ref=payload.get("runtime_ref"),forecast_contract=payload.get("forecast_contract"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("member_key must be unique within ensemble_id") from exc
    db.refresh(row); return _ser(row)

def add_ensemble_forecast(db:Session,ensemble_id:str,payload:dict):
    _reject(payload); _ensemble(db,ensemble_id)
    rep=str(payload.get("representation") or "").strip(); forecast=payload.get("forecast")
    if rep not in PROBABILISTIC_REPRESENTATIONS|{"point"}: raise ValueError("representation must be point or a supported probabilistic representation")
    if not isinstance(forecast,dict): raise ValueError("forecast must be an object")
    if rep!="point": _validate_probabilistic_payload(rep,forecast)
    elif "value" not in forecast: raise ValueError("point ensemble forecast requires value")
    refs=payload.get("member_forecast_refs") or []
    if not isinstance(refs,list): raise ValueError("member_forecast_refs must be an array")
    row=PredictiveEnsembleForecastRecord(ensemble_id=ensemble_id,valid_time=_parse_dt(payload.get("valid_time")),representation=rep,forecast_json=forecast,member_forecast_refs_json=refs,source_ref=payload.get("source_ref"),externally_generated=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def ensemble_bundle(db:Session,ensemble_id:str):
    ensemble=_ensemble(db,ensemble_id)
    members=[_ser(x) for x in db.scalars(select(PredictiveEnsembleMemberRecord).where(PredictiveEnsembleMemberRecord.ensemble_id==ensemble_id).order_by(PredictiveEnsembleMemberRecord.created_at.asc())).all()]
    forecasts=[_ser(x) for x in db.scalars(select(PredictiveEnsembleForecastRecord).where(PredictiveEnsembleForecastRecord.ensemble_id==ensemble_id).order_by(PredictiveEnsembleForecastRecord.created_at.asc())).all()]
    return {"contract":"sc.predictive.ensemble.v1","ensemble":_ser(ensemble),"members":members,"forecasts":forecasts,"boundaries":boundaries()}

def create_comparison_study(db:Session,payload:dict):
    _reject(payload)
    project=str(payload.get("project_entity_id") or "").strip(); ent=db.get(Entity,project)
    if ent is None: raise ValueError("project_entity_id must reference an existing Core entity")
    key=str(payload.get("comparison_key") or "").strip(); name=str(payload.get("name") or "").strip(); vis=str(payload.get("visibility") or "private")
    if not key or not name: raise ValueError("comparison_key and name are required")
    if vis not in {"private","public"}: raise ValueError("visibility must be private or public")
    row=PredictiveComparisonStudyRecord(project_entity_id=project,comparison_key=key,name=name,target_semantics_json=dict(payload.get("target_semantics") or {}),evaluation_scope_json=dict(payload.get("evaluation_scope") or {}),status=str(payload.get("status") or "recorded"),visibility=vis,externally_computed=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("comparison_key must be unique within project_entity_id") from exc
    db.refresh(row); return _ser(row)

def _comparison(db:Session,study_id:str)->PredictiveComparisonStudyRecord:
    row=db.get(PredictiveComparisonStudyRecord,study_id)
    if row is None: raise HTTPException(status_code=404,detail="Predictive comparison study not found.")
    return row

def add_comparison_candidate(db:Session,study_id:str,payload:dict):
    _reject(payload); study=_comparison(db,study_id)
    key=str(payload.get("candidate_key") or "").strip(); kind=str(payload.get("candidate_kind") or "model"); ref=str(payload.get("candidate_ref") or "").strip(); label=str(payload.get("label") or "").strip()
    if not key or not ref or not label: raise ValueError("candidate_key, candidate_ref, and label are required")
    if kind not in COMPARISON_CANDIDATE_KINDS: raise ValueError(f"candidate_kind must be one of {sorted(COMPARISON_CANDIDATE_KINDS)}")
    if kind=="model":
        model=db.get(PredictiveModelRecord,ref)
        if model is None or model.project_entity_id!=study.project_entity_id: raise ValueError("model candidate_ref must reference a model in the comparison project")
    elif kind=="ensemble":
        ensemble=db.get(PredictiveEnsembleRecord,ref)
        if ensemble is None or ensemble.project_entity_id!=study.project_entity_id: raise ValueError("ensemble candidate_ref must reference an ensemble in the comparison project")
    row=PredictiveComparisonCandidateRecord(comparison_study_id=study_id,candidate_key=key,candidate_kind=kind,candidate_ref=ref,label=label,role=str(payload.get("role") or "candidate"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("candidate_key must be unique within comparison_study_id") from exc
    db.refresh(row); return _ser(row)

def _candidate(db:Session,study_id:str,candidate_id:str)->PredictiveComparisonCandidateRecord:
    row=db.get(PredictiveComparisonCandidateRecord,candidate_id)
    if row is None or row.comparison_study_id!=study_id: raise ValueError("candidate_id must belong to comparison_study_id")
    return row

def add_comparison_evidence(db:Session,study_id:str,payload:dict):
    _reject(payload); _comparison(db,study_id); candidate=_candidate(db,study_id,str(payload.get("candidate_id") or ""))
    key=str(payload.get("evidence_key") or "").strip(); family=str(payload.get("metric_family") or "other"); metric=str(payload.get("metric_name") or "").strip(); value=payload.get("metric_value")
    if not key or not metric or value is None: raise ValueError("evidence_key, metric_name, and metric_value are required")
    if family not in COMPARISON_METRIC_FAMILIES: raise ValueError(f"metric_family must be one of {sorted(COMPARISON_METRIC_FAMILIES)}")
    row=PredictiveComparisonEvidenceRecord(comparison_study_id=study_id,candidate_id=candidate.id,evidence_key=key,metric_family=family,metric_name=metric,metric_value_json=value if isinstance(value,dict) else {"value":value},aggregation_json=dict(payload.get("aggregation") or {}),uncertainty_json=dict(payload.get("uncertainty") or {}),evidence_ref=payload.get("evidence_ref"),externally_computed=True,provenance_json=dict(payload.get("provenance") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_pairwise_comparison(db:Session,study_id:str,payload:dict):
    _reject(payload); _comparison(db,study_id); left=_candidate(db,study_id,str(payload.get("left_candidate_id") or "")); right=_candidate(db,study_id,str(payload.get("right_candidate_id") or ""))
    if left.id==right.id: raise ValueError("left_candidate_id and right_candidate_id must differ")
    kind=str(payload.get("comparison_kind") or "metric-difference")
    if kind not in PAIRWISE_COMPARISON_KINDS: raise ValueError(f"comparison_kind must be one of {sorted(PAIRWISE_COMPARISON_KINDS)}")
    statistic=payload.get("statistic")
    if not isinstance(statistic,dict) or not statistic: raise ValueError("statistic must be a non-empty object")
    row=PredictivePairwiseComparisonRecord(comparison_study_id=study_id,left_candidate_id=left.id,right_candidate_id=right.id,comparison_kind=kind,statistic_json=statistic,uncertainty_json=dict(payload.get("uncertainty") or {}),evidence_ref=payload.get("evidence_ref"),externally_computed=True,provenance_json=dict(payload.get("provenance") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def comparison_bundle(db:Session,study_id:str):
    study=_comparison(db,study_id)
    candidates=[_ser(x) for x in db.scalars(select(PredictiveComparisonCandidateRecord).where(PredictiveComparisonCandidateRecord.comparison_study_id==study_id).order_by(PredictiveComparisonCandidateRecord.created_at.asc())).all()]
    evidence=[_ser(x) for x in db.scalars(select(PredictiveComparisonEvidenceRecord).where(PredictiveComparisonEvidenceRecord.comparison_study_id==study_id).order_by(PredictiveComparisonEvidenceRecord.created_at.asc())).all()]
    pairwise=[_ser(x) for x in db.scalars(select(PredictivePairwiseComparisonRecord).where(PredictivePairwiseComparisonRecord.comparison_study_id==study_id).order_by(PredictivePairwiseComparisonRecord.created_at.asc())).all()]
    packages=[_ser(x) for x in db.scalars(select(PredictiveComparisonPackageRecord).where(PredictiveComparisonPackageRecord.comparison_study_id==study_id).order_by(PredictiveComparisonPackageRecord.revision.asc())).all()]
    return {"contract":"sc.predictive.model-comparison-package.v1","study":_ser(study),"candidates":candidates,"evidence":evidence,"pairwise_evidence":pairwise,"packages":packages,"boundaries":boundaries()}

def create_comparison_package(db:Session,study_id:str,payload:dict):
    _reject(payload); state=comparison_bundle(db,study_id); state.pop("packages",None); digest=_sha256(state)
    last=db.scalar(select(PredictiveComparisonPackageRecord).where(PredictiveComparisonPackageRecord.comparison_study_id==study_id).order_by(PredictiveComparisonPackageRecord.revision.desc())); rev=(last.revision+1) if last else 1
    row=PredictiveComparisonPackageRecord(comparison_study_id=study_id,revision=rev,content_hash=digest,previous_package_hash=(last.content_hash if last else None),state_json=state,environment_json=dict(payload.get("environment") or {}),provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)



# v2.56.0 — Anomaly, Change-Point & Early-Warning Intelligence

def create_monitoring_study(db:Session,payload:dict):
    _reject(payload)
    project=str(payload.get("project_entity_id") or "").strip(); ent=db.get(Entity,project)
    if ent is None: raise ValueError("project_entity_id must reference an existing Core entity")
    model_id=payload.get("model_id"); target_id=payload.get("target_id"); dataset_id=payload.get("dataset_id")
    if model_id:
        model=db.get(PredictiveModelRecord,str(model_id))
        if model is None or model.project_entity_id!=project: raise ValueError("model_id must reference a predictive model in project_entity_id")
    if target_id:
        target=db.get(PredictiveTargetRecord,str(target_id))
        if target is None or not model_id or target.model_id!=str(model_id): raise ValueError("target_id must belong to model_id")
    if dataset_id:
        dataset=db.get(PredictiveTimeSeriesDatasetRecord,str(dataset_id))
        if dataset is None or not model_id or dataset.model_id!=str(model_id): raise ValueError("dataset_id must belong to model_id")
    key=str(payload.get("study_key") or "").strip(); name=str(payload.get("name") or "").strip(); kind=str(payload.get("monitoring_kind") or "multi-signal"); vis=str(payload.get("visibility") or "private")
    if not key or not name: raise ValueError("study_key and name are required")
    if kind not in MONITORING_KINDS: raise ValueError(f"monitoring_kind must be one of {sorted(MONITORING_KINDS)}")
    if vis not in {"private","public"}: raise ValueError("visibility must be private or public")
    row=PredictiveMonitoringStudyRecord(project_entity_id=project,model_id=str(model_id) if model_id else None,target_id=str(target_id) if target_id else None,dataset_id=str(dataset_id) if dataset_id else None,study_key=key,name=name,monitoring_kind=kind,monitoring_scope_json=dict(payload.get("monitoring_scope") or {}),baseline_json=dict(payload.get("baseline") or {}),status=str(payload.get("status") or "recorded"),visibility=vis,externally_computed=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("study_key must be unique within project_entity_id") from exc
    db.refresh(row); return _ser(row)

def _monitoring_study(db:Session,study_id:str)->PredictiveMonitoringStudyRecord:
    row=db.get(PredictiveMonitoringStudyRecord,study_id)
    if row is None: raise HTTPException(status_code=404,detail="Predictive monitoring study not found.")
    return row

def _monitoring_rule(db:Session,study_id:str,rule_id:str|None):
    if not rule_id: return None
    row=db.get(PredictiveDetectionRuleRecord,rule_id)
    if row is None or row.monitoring_study_id!=study_id: raise ValueError("detection_rule_id must belong to monitoring_study_id")
    return row

def add_detection_rule(db:Session,study_id:str,payload:dict):
    _reject(payload); _monitoring_study(db,study_id)
    key=str(payload.get("rule_key") or "").strip(); kind=str(payload.get("rule_kind") or "external"); method=str(payload.get("method") or "").strip(); runtime=str(payload.get("runtime_product") or "external")
    if not key or not method: raise ValueError("rule_key and method are required")
    if kind not in DETECTION_RULE_KINDS: raise ValueError(f"rule_kind must be one of {sorted(DETECTION_RULE_KINDS)}")
    if runtime not in RUNTIME_PRODUCTS: raise ValueError("unsupported runtime_product")
    row=PredictiveDetectionRuleRecord(monitoring_study_id=study_id,rule_key=key,rule_kind=kind,method=method,parameters_json=dict(payload.get("parameters") or {}),threshold_json=dict(payload.get("threshold") or {}),runtime_product=runtime,runtime_ref=payload.get("runtime_ref"),externally_defined=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("rule_key must be unique within monitoring_study_id") from exc
    db.refresh(row); return _ser(row)

def add_anomaly_observation(db:Session,study_id:str,payload:dict):
    _reject(payload); _monitoring_study(db,study_id); rule=_monitoring_rule(db,study_id,payload.get("detection_rule_id"))
    key=str(payload.get("observation_key") or "").strip(); kind=str(payload.get("anomaly_kind") or "point"); score=payload.get("score")
    if not key or not isinstance(score,dict) or not score: raise ValueError("observation_key and non-empty score object are required")
    if kind not in ANOMALY_KINDS: raise ValueError(f"anomaly_kind must be one of {sorted(ANOMALY_KINDS)}")
    row=PredictiveAnomalyObservationRecord(monitoring_study_id=study_id,detection_rule_id=(rule.id if rule else None),observation_key=key,observed_at=_parse_dt(payload.get("observed_at")),anomaly_kind=kind,score_json=score,threshold_json=dict(payload.get("threshold") or {}),source_observation_ref=payload.get("source_observation_ref"),evidence_ref=payload.get("evidence_ref"),externally_detected=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("observation_key must be unique within monitoring_study_id") from exc
    db.refresh(row); return _ser(row)

def add_change_point(db:Session,study_id:str,payload:dict):
    _reject(payload); _monitoring_study(db,study_id); rule=_monitoring_rule(db,study_id,payload.get("detection_rule_id"))
    key=str(payload.get("change_key") or "").strip(); method=str(payload.get("method") or "").strip(); statistic=payload.get("statistic")
    ct=_parse_dt(payload.get("change_time")); start=_parse_dt(payload.get("interval_start")); end=_parse_dt(payload.get("interval_end"))
    if not key or not method or not isinstance(statistic,dict) or not statistic: raise ValueError("change_key, method, and non-empty statistic object are required")
    if ct is None and start is None and end is None: raise ValueError("change_time or an interval bound is required")
    if start and end and start>end: raise ValueError("interval_start must be <= interval_end")
    row=PredictiveChangePointRecord(monitoring_study_id=study_id,detection_rule_id=(rule.id if rule else None),change_key=key,change_time=ct,interval_start=start,interval_end=end,method=method,statistic_json=statistic,uncertainty_json=dict(payload.get("uncertainty") or {}),before_state_json=dict(payload.get("before_state") or {}),after_state_json=dict(payload.get("after_state") or {}),evidence_ref=payload.get("evidence_ref"),externally_detected=True,provenance_json=dict(payload.get("provenance") or {}))
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("change_key must be unique within monitoring_study_id") from exc
    db.refresh(row); return _ser(row)

def add_early_warning_signal(db:Session,study_id:str,payload:dict):
    _reject(payload); _monitoring_study(db,study_id); rule=_monitoring_rule(db,study_id,payload.get("detection_rule_id"))
    key=str(payload.get("signal_key") or "").strip(); kind=str(payload.get("signal_kind") or "external"); indicator=payload.get("indicator")
    if not key or not isinstance(indicator,dict) or not indicator: raise ValueError("signal_key and non-empty indicator object are required")
    if kind not in EARLY_WARNING_SIGNAL_KINDS: raise ValueError(f"signal_kind must be one of {sorted(EARLY_WARNING_SIGNAL_KINDS)}")
    row=PredictiveEarlyWarningSignalRecord(monitoring_study_id=study_id,detection_rule_id=(rule.id if rule else None),signal_key=key,signal_kind=kind,observed_at=_parse_dt(payload.get("observed_at")),indicator_json=indicator,threshold_json=dict(payload.get("threshold") or {}),lead_time_json=dict(payload.get("lead_time") or {}),state=str(payload.get("state") or "observed"),evidence_ref=payload.get("evidence_ref"),externally_detected=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("signal_key must be unique within monitoring_study_id") from exc
    db.refresh(row); return _ser(row)

def add_monitoring_episode(db:Session,study_id:str,payload:dict):
    _reject(payload); _monitoring_study(db,study_id)
    key=str(payload.get("episode_key") or "").strip(); refs=payload.get("evidence_refs") or []
    if not key: raise ValueError("episode_key is required")
    if not isinstance(refs,list): raise ValueError("evidence_refs must be an array")
    start=_parse_dt(payload.get("start_time")); end=_parse_dt(payload.get("end_time"))
    if start and end and start>end: raise ValueError("start_time must be <= end_time")
    row=PredictiveMonitoringEpisodeRecord(monitoring_study_id=study_id,episode_key=key,episode_kind=str(payload.get("episode_kind") or "monitoring-event"),start_time=start,end_time=end,evidence_refs_json=refs,descriptive_summary_json=dict(payload.get("descriptive_summary") or {}),status=str(payload.get("status") or "recorded"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("episode_key must be unique within monitoring_study_id") from exc
    db.refresh(row); return _ser(row)

def monitoring_bundle(db:Session,study_id:str):
    study=_monitoring_study(db,study_id)
    def rows(model): return [_ser(x) for x in db.scalars(select(model).where(model.monitoring_study_id==study_id).order_by(model.created_at.asc())).all()]
    return {"contract":"sc.predictive.monitoring-package.v1","study":_ser(study),"detection_rules":rows(PredictiveDetectionRuleRecord),"anomaly_observations":rows(PredictiveAnomalyObservationRecord),"change_points":rows(PredictiveChangePointRecord),"early_warning_signals":rows(PredictiveEarlyWarningSignalRecord),"monitoring_episodes":rows(PredictiveMonitoringEpisodeRecord),"packages":rows(PredictiveMonitoringPackageRecord),"boundaries":boundaries()}

def create_monitoring_package(db:Session,study_id:str,payload:dict):
    _reject(payload); state=monitoring_bundle(db,study_id); state.pop("packages",None); digest=_sha256(state)
    last=db.scalar(select(PredictiveMonitoringPackageRecord).where(PredictiveMonitoringPackageRecord.monitoring_study_id==study_id).order_by(PredictiveMonitoringPackageRecord.revision.desc())); rev=(last.revision+1) if last else 1
    row=PredictiveMonitoringPackageRecord(monitoring_study_id=study_id,revision=rev,content_hash=digest,previous_package_hash=(last.content_hash if last else None),state_json=state,environment_json=dict(payload.get("environment") or {}),provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)


# v2.57.0 — Spatial-Temporal Predictive Intelligence
def _spatial_temporal_study(db:Session,study_id:str)->PredictiveSpatialTemporalStudyRecord:
    row=db.get(PredictiveSpatialTemporalStudyRecord,study_id)
    if row is None: raise HTTPException(status_code=404,detail="Predictive spatial-temporal study not found.")
    return row

def _spatial_unit(db:Session,study_id:str,unit_id:str|None):
    if not unit_id: return None
    row=db.get(PredictiveSpatialUnitRecord,unit_id)
    if row is None or row.spatial_temporal_study_id!=study_id: raise ValueError("spatial_unit_id must belong to spatial_temporal_study_id")
    return row

def create_spatial_temporal_study(db:Session,payload:dict):
    _reject(payload); project=str(payload.get("project_entity_id") or "").strip(); ent=db.get(Entity,project)
    if ent is None: raise ValueError("project_entity_id must reference an existing Core entity")
    model_id=payload.get("model_id")
    if model_id: _model(db,model_id)
    target_id=payload.get("target_id")
    if target_id:
        target=db.get(PredictiveTargetRecord,target_id)
        if target is None or (model_id and target.model_id!=model_id): raise ValueError("target_id must reference the study model when model_id is supplied")
    dataset_id=payload.get("dataset_id")
    if dataset_id:
        dataset=db.get(PredictiveTimeSeriesDatasetRecord,dataset_id)
        if dataset is None or (model_id and dataset.model_id!=model_id): raise ValueError("dataset_id must reference the study model when model_id is supplied")
    vis=str(payload.get("visibility") or "private")
    if vis not in {"private","public"}: raise ValueError("visibility must be private or public")
    row=PredictiveSpatialTemporalStudyRecord(project_entity_id=project,model_id=model_id,target_id=target_id,dataset_id=dataset_id,study_key=str(payload.get("study_key") or "").strip(),name=str(payload.get("name") or "").strip(),spatial_reference=str(payload.get("spatial_reference") or "EPSG:4326"),temporal_reference=str(payload.get("temporal_reference") or "UTC"),spatial_scope_json=dict(payload.get("spatial_scope") or {}),temporal_scope_json=dict(payload.get("temporal_scope") or {}),forecast_horizon_json=dict(payload.get("forecast_horizon") or {}),status=str(payload.get("status") or "recorded"),visibility=vis,externally_computed=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.study_key or not row.name: raise ValueError("study_key and name are required")
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("study_key must be unique within project_entity_id") from exc
    db.refresh(row); return _ser(row)

def add_spatial_unit(db:Session,study_id:str,payload:dict):
    _reject(payload); _spatial_temporal_study(db,study_id); kind=str(payload.get("unit_kind") or "region")
    if kind not in SPATIAL_UNIT_KINDS: raise ValueError(f"unit_kind must be one of {sorted(SPATIAL_UNIT_KINDS)}")
    parent=payload.get("parent_unit_id")
    if parent: _spatial_unit(db,study_id,parent)
    row=PredictiveSpatialUnitRecord(spatial_temporal_study_id=study_id,unit_key=str(payload.get("unit_key") or "").strip(),unit_kind=kind,label=str(payload.get("label") or "").strip(),geometry_json=dict(payload.get("geometry") or {}),bbox_json=list(payload.get("bbox") or []),source_ref=payload.get("source_ref"),parent_unit_id=parent,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.unit_key or not row.label: raise ValueError("unit_key and label are required")
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("unit_key must be unique within spatial_temporal_study_id") from exc
    db.refresh(row); return _ser(row)

def add_spatial_temporal_forecast(db:Session,study_id:str,payload:dict):
    _reject(payload); _spatial_temporal_study(db,study_id); unit=_spatial_unit(db,study_id,payload.get("spatial_unit_id")); rep=str(payload.get("representation") or "point")
    if rep not in SPATIAL_FORECAST_REPRESENTATIONS: raise ValueError(f"representation must be one of {sorted(SPATIAL_FORECAST_REPRESENTATIONS)}")
    runtime=str(payload.get("runtime_product") or "external")
    if runtime not in RUNTIME_PRODUCTS: raise ValueError("unsupported runtime_product")
    forecast=payload.get("forecast")
    if not isinstance(forecast,dict) or not forecast: raise ValueError("forecast object is required")
    row=PredictiveSpatialTemporalForecastRecord(spatial_temporal_study_id=study_id,spatial_unit_id=(unit.id if unit else None),forecast_key=str(payload.get("forecast_key") or "").strip(),issued_at=_parse_dt(payload.get("issued_at")),valid_time=_parse_dt(payload.get("valid_time")),valid_start=_parse_dt(payload.get("valid_start")),valid_end=_parse_dt(payload.get("valid_end")),representation=rep,forecast_json=forecast,uncertainty_json=dict(payload.get("uncertainty") or {}),source_forecast_ref=payload.get("source_forecast_ref"),runtime_product=runtime,runtime_ref=payload.get("runtime_ref"),externally_computed=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.forecast_key: raise ValueError("forecast_key is required")
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_spatial_temporal_observation(db:Session,study_id:str,payload:dict):
    _reject(payload); _spatial_temporal_study(db,study_id); unit=_spatial_unit(db,study_id,payload.get("spatial_unit_id")); value=payload.get("value")
    if not isinstance(value,dict) or not value: raise ValueError("value object is required")
    row=PredictiveSpatialTemporalObservationRecord(spatial_temporal_study_id=study_id,spatial_unit_id=(unit.id if unit else None),observation_key=str(payload.get("observation_key") or "").strip(),observed_at=_parse_dt(payload.get("observed_at")),value_json=value,uncertainty_json=dict(payload.get("uncertainty") or {}),source_ref=payload.get("source_ref"),evidence_ref=payload.get("evidence_ref"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.observation_key: raise ValueError("observation_key is required")
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_spatial_propagation_evidence(db:Session,study_id:str,payload:dict):
    _reject(payload); _spatial_temporal_study(db,study_id); source=_spatial_unit(db,study_id,payload.get("source_unit_id")); target=_spatial_unit(db,study_id,payload.get("target_unit_id")); statistic=payload.get("statistic")
    if not isinstance(statistic,dict) or not statistic: raise ValueError("statistic object is required")
    row=PredictiveSpatialPropagationEvidenceRecord(spatial_temporal_study_id=study_id,evidence_key=str(payload.get("evidence_key") or "").strip(),source_unit_id=(source.id if source else None),target_unit_id=(target.id if target else None),evidence_kind=str(payload.get("evidence_kind") or "propagation"),lag_json=dict(payload.get("lag") or {}),statistic_json=statistic,uncertainty_json=dict(payload.get("uncertainty") or {}),evidence_ref=payload.get("evidence_ref"),externally_computed=True,provenance_json=dict(payload.get("provenance") or {}))
    if not row.evidence_key: raise ValueError("evidence_key is required")
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_spatial_hotspot_evidence(db:Session,study_id:str,payload:dict):
    _reject(payload); _spatial_temporal_study(db,study_id); unit=_spatial_unit(db,study_id,payload.get("spatial_unit_id")); score=payload.get("score")
    if not isinstance(score,dict) or not score: raise ValueError("score object is required")
    row=PredictiveSpatialHotspotEvidenceRecord(spatial_temporal_study_id=study_id,spatial_unit_id=(unit.id if unit else None),hotspot_key=str(payload.get("hotspot_key") or "").strip(),observed_at=_parse_dt(payload.get("observed_at")),hotspot_kind=str(payload.get("hotspot_kind") or "external"),score_json=score,threshold_json=dict(payload.get("threshold") or {}),geometry_json=dict(payload.get("geometry") or {}),evidence_ref=payload.get("evidence_ref"),externally_detected=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.hotspot_key: raise ValueError("hotspot_key is required")
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_spatial_temporal_evaluation(db:Session,study_id:str,payload:dict):
    _reject(payload); _spatial_temporal_study(db,study_id); evidence=payload.get("metric_evidence")
    if not isinstance(evidence,dict) or not evidence: raise ValueError("metric_evidence object is required")
    row=PredictiveSpatialTemporalEvaluationRecord(spatial_temporal_study_id=study_id,evaluation_key=str(payload.get("evaluation_key") or "").strip(),evaluation_kind=str(payload.get("evaluation_kind") or "spatial-temporal"),window_json=dict(payload.get("window") or {}),metric_evidence_json=evidence,strata_json=dict(payload.get("strata") or {}),evidence_ref=payload.get("evidence_ref"),externally_computed=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.evaluation_key: raise ValueError("evaluation_key is required")
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def spatial_temporal_bundle(db:Session,study_id:str):
    study=_spatial_temporal_study(db,study_id)
    def rows(model): return [_ser(x) for x in db.scalars(select(model).where(model.spatial_temporal_study_id==study_id).order_by(model.created_at.asc())).all()]
    return {"contract":"sc.predictive.spatial-temporal-package.v1","study":_ser(study),"spatial_units":rows(PredictiveSpatialUnitRecord),"forecasts":rows(PredictiveSpatialTemporalForecastRecord),"observations":rows(PredictiveSpatialTemporalObservationRecord),"propagation_evidence":rows(PredictiveSpatialPropagationEvidenceRecord),"hotspot_evidence":rows(PredictiveSpatialHotspotEvidenceRecord),"evaluations":rows(PredictiveSpatialTemporalEvaluationRecord),"packages":rows(PredictiveSpatialTemporalPackageRecord),"boundaries":boundaries()}

def create_spatial_temporal_package(db:Session,study_id:str,payload:dict):
    _reject(payload); state=spatial_temporal_bundle(db,study_id); state.pop("packages",None); digest=_sha256(state)
    last=db.scalar(select(PredictiveSpatialTemporalPackageRecord).where(PredictiveSpatialTemporalPackageRecord.spatial_temporal_study_id==study_id).order_by(PredictiveSpatialTemporalPackageRecord.revision.desc())); rev=(last.revision+1) if last else 1
    row=PredictiveSpatialTemporalPackageRecord(spatial_temporal_study_id=study_id,revision=rev,content_hash=digest,previous_package_hash=(last.content_hash if last else None),state_json=state,environment_json=dict(payload.get("environment") or {}),provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

# v2.58.0 — Causal-Predictive Integration

def _causal_predictive_study(db:Session, study_id:str)->PredictiveCausalStudyRecord:
    row=db.get(PredictiveCausalStudyRecord,study_id)
    if row is None: raise ValueError("causal_predictive_study_id not found")
    return row

def _causal_intervention_scenario(db:Session,study_id:str,scenario_id:str|None)->PredictiveInterventionScenarioRecord|None:
    if not scenario_id: return None
    row=db.get(PredictiveInterventionScenarioRecord,scenario_id)
    if row is None or row.causal_predictive_study_id!=study_id: raise ValueError("intervention_scenario_id must belong to causal_predictive_study_id")
    return row

def create_causal_predictive_study(db:Session,payload:dict):
    _reject(payload)
    project=str(payload.get("project_entity_id") or "").strip(); ent=db.get(Entity,project)
    if ent is None: raise ValueError("project_entity_id must reference an existing Core entity")
    model_id=str(payload.get("predictive_model_id") or "").strip(); model=_model(db,model_id)
    if model.project_entity_id!=project: raise ValueError("predictive_model_id must belong to project_entity_id")
    graph_id=str(payload.get("causal_graph_id") or "").strip(); graph=db.get(CausalGraphRecord,graph_id)
    if graph is None: raise ValueError("causal_graph_id must reference an existing causal graph")
    if graph.project_entity_id!=project: raise ValueError("causal_graph_id must belong to project_entity_id")
    target_id=payload.get("target_id")
    if target_id:
        target=db.get(PredictiveTargetRecord,target_id)
        if target is None or target.model_id!=model_id: raise ValueError("target_id must belong to predictive_model_id")
    kind=str(payload.get("integration_kind") or "causal-forecast")
    if kind not in CAUSAL_PREDICTIVE_INTEGRATION_KINDS: raise ValueError(f"integration_kind must be one of {sorted(CAUSAL_PREDICTIVE_INTEGRATION_KINDS)}")
    vis=str(payload.get("visibility") or "private")
    if vis not in {"private","public"}: raise ValueError("visibility must be private or public")
    row=PredictiveCausalStudyRecord(project_entity_id=project,predictive_model_id=model_id,causal_graph_id=graph_id,target_id=target_id,study_key=str(payload.get("study_key") or "").strip(),name=str(payload.get("name") or "").strip(),integration_kind=kind,estimand_scope_json=dict(payload.get("estimand_scope") or {}),temporal_scope_json=dict(payload.get("temporal_scope") or {}),status=str(payload.get("status") or "recorded"),visibility=vis,externally_computed=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.study_key or not row.name: raise ValueError("study_key and name are required")
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("study_key must be unique within project_entity_id") from exc
    db.refresh(row); return _ser(row)

def add_causal_variable_binding(db:Session,study_id:str,payload:dict):
    _reject(payload); study=_causal_predictive_study(db,study_id)
    variable_id=str(payload.get("causal_variable_id") or "").strip(); variable=db.get(CausalVariableRecord,variable_id)
    if variable is None or variable.graph_id!=study.causal_graph_id: raise ValueError("causal_variable_id must belong to the study causal graph")
    target_id=payload.get("predictive_target_id"); feature_id=payload.get("predictive_feature_id")
    if not target_id and not feature_id: raise ValueError("predictive_target_id or predictive_feature_id is required")
    if target_id:
        target=db.get(PredictiveTargetRecord,target_id)
        if target is None or target.model_id!=study.predictive_model_id: raise ValueError("predictive_target_id must belong to the study predictive model")
    if feature_id:
        feature=db.get(PredictiveFeatureRecord,feature_id)
        if feature is None or feature.model_id!=study.predictive_model_id: raise ValueError("predictive_feature_id must belong to the study predictive model")
    role=str(payload.get("binding_role") or "predictor")
    if role not in CAUSAL_BINDING_ROLES: raise ValueError(f"binding_role must be one of {sorted(CAUSAL_BINDING_ROLES)}")
    row=PredictiveCausalVariableBindingRecord(causal_predictive_study_id=study_id,binding_key=str(payload.get("binding_key") or "").strip(),causal_variable_id=variable_id,predictive_target_id=target_id,predictive_feature_id=feature_id,binding_role=role,transformation_json=dict(payload.get("transformation") or {}),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.binding_key: raise ValueError("binding_key is required")
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("binding_key must be unique within causal_predictive_study_id") from exc
    db.refresh(row); return _ser(row)

def add_intervention_scenario(db:Session,study_id:str,payload:dict):
    _reject(payload); study=_causal_predictive_study(db,study_id)
    causal_intervention_id=payload.get("causal_intervention_id")
    if causal_intervention_id:
        intervention=db.get(CausalInterventionRecord,causal_intervention_id)
        if intervention is None or intervention.graph_id!=study.causal_graph_id: raise ValueError("causal_intervention_id must belong to the study causal graph")
    intervention_json=payload.get("intervention")
    if not isinstance(intervention_json,dict) or not intervention_json: raise ValueError("intervention object is required")
    assumptions=payload.get("assumptions") or []
    if not isinstance(assumptions,list): raise ValueError("assumptions must be an array")
    row=PredictiveInterventionScenarioRecord(causal_predictive_study_id=study_id,scenario_key=str(payload.get("scenario_key") or "").strip(),name=str(payload.get("name") or "").strip(),causal_intervention_id=causal_intervention_id,intervention_json=intervention_json,baseline_json=dict(payload.get("baseline") or {}),assumptions_json=assumptions,horizon_json=dict(payload.get("horizon") or {}),source_ref=payload.get("source_ref"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.scenario_key or not row.name: raise ValueError("scenario_key and name are required")
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("scenario_key must be unique within causal_predictive_study_id") from exc
    db.refresh(row); return _ser(row)

def add_counterfactual_forecast(db:Session,study_id:str,payload:dict):
    _reject(payload); _causal_predictive_study(db,study_id); scenario=_causal_intervention_scenario(db,study_id,payload.get("intervention_scenario_id"))
    cf=payload.get("counterfactual_forecast")
    if not isinstance(cf,dict) or not cf: raise ValueError("counterfactual_forecast object is required")
    factual=payload.get("factual_forecast") or {}
    if not isinstance(factual,dict): raise ValueError("factual_forecast must be an object")
    runtime=str(payload.get("runtime_product") or "external")
    if runtime not in RUNTIME_PRODUCTS: raise ValueError("unsupported runtime_product")
    row=PredictiveCounterfactualForecastRecord(causal_predictive_study_id=study_id,intervention_scenario_id=(scenario.id if scenario else None),forecast_key=str(payload.get("forecast_key") or "").strip(),issued_at=_parse_dt(payload.get("issued_at")),horizon_json=dict(payload.get("horizon") or {}),factual_forecast_json=factual,counterfactual_forecast_json=cf,contrast_json=dict(payload.get("contrast") or {}),uncertainty_json=dict(payload.get("uncertainty") or {}),runtime_product=runtime,runtime_ref=payload.get("runtime_ref"),externally_computed=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.forecast_key: raise ValueError("forecast_key is required")
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("forecast_key must be unique within causal_predictive_study_id") from exc
    db.refresh(row); return _ser(row)

def add_causal_effect_evidence(db:Session,study_id:str,payload:dict):
    _reject(payload); study=_causal_predictive_study(db,study_id)
    identification_id=payload.get("causal_identification_id")
    if identification_id:
        ident=db.get(CausalIdentificationRecord,identification_id)
        if ident is None or ident.graph_id!=study.causal_graph_id: raise ValueError("causal_identification_id must belong to the study causal graph")
    estimate_id=payload.get("causal_estimate_id")
    if estimate_id:
        estimate=db.get(CausalEstimateRecord,estimate_id)
        if estimate is None or estimate.graph_id!=study.causal_graph_id: raise ValueError("causal_estimate_id must belong to the study causal graph")
    effect=payload.get("effect")
    if not isinstance(effect,dict) or not effect: raise ValueError("effect object is required")
    assumptions=payload.get("assumptions") or []
    if not isinstance(assumptions,list): raise ValueError("assumptions must be an array")
    row=PredictiveCausalEffectEvidenceRecord(causal_predictive_study_id=study_id,evidence_key=str(payload.get("evidence_key") or "").strip(),causal_identification_id=identification_id,causal_estimate_id=estimate_id,estimand=str(payload.get("estimand") or "effect"),effect_json=effect,uncertainty_json=dict(payload.get("uncertainty") or {}),assumptions_json=assumptions,evidence_ref=payload.get("evidence_ref"),externally_computed=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.evidence_key: raise ValueError("evidence_key is required")
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("evidence_key must be unique within causal_predictive_study_id") from exc
    db.refresh(row); return _ser(row)

def add_causal_predictive_evaluation(db:Session,study_id:str,payload:dict):
    _reject(payload); _causal_predictive_study(db,study_id); metrics=payload.get("metric_evidence")
    if not isinstance(metrics,dict) or not metrics: raise ValueError("metric_evidence object is required")
    diagnostics=payload.get("diagnostic_evidence") or {}
    if not isinstance(diagnostics,dict): raise ValueError("diagnostic_evidence must be an object")
    row=PredictiveCausalEvaluationRecord(causal_predictive_study_id=study_id,evaluation_key=str(payload.get("evaluation_key") or "").strip(),evaluation_kind=str(payload.get("evaluation_kind") or "causal-predictive"),metric_evidence_json=metrics,diagnostic_evidence_json=diagnostics,comparison_scope_json=dict(payload.get("comparison_scope") or {}),evidence_ref=payload.get("evidence_ref"),externally_computed=True,provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    if not row.evaluation_key: raise ValueError("evaluation_key is required")
    db.add(row)
    try: db.commit()
    except IntegrityError as exc: db.rollback(); raise ValueError("evaluation_key must be unique within causal_predictive_study_id") from exc
    db.refresh(row); return _ser(row)

def add_causal_predictive_handoff(db:Session,study_id:str,payload:dict):
    _reject(payload); _causal_predictive_study(db,study_id); product=str(payload.get("target_product") or "").strip()
    if product not in RUNTIME_PRODUCTS-{"external"}: raise ValueError("target_product must be a supported specialist runtime")
    request=payload.get("request") or {}
    if not isinstance(request,dict): raise ValueError("request must be an object")
    row=PredictiveCausalHandoffRecord(causal_predictive_study_id=study_id,target_product=product,purpose=str(payload.get("purpose") or "external-causal-predictive-compute"),request_json=request,response_ref=payload.get("response_ref"),status=str(payload.get("status") or "recorded"),provenance_json=dict(payload.get("provenance") or {}),metadata_json=dict(payload.get("metadata") or {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def causal_predictive_bundle(db:Session,study_id:str):
    study=_causal_predictive_study(db,study_id)
    def rows(model): return [_ser(x) for x in db.scalars(select(model).where(model.causal_predictive_study_id==study_id).order_by(model.created_at.asc())).all()]
    graph=db.get(CausalGraphRecord,study.causal_graph_id)
    return {"contract":"sc.predictive.causal-package.v1","study":_ser(study),"causal_graph":(_ser(graph) if graph else None),"variable_bindings":rows(PredictiveCausalVariableBindingRecord),"intervention_scenarios":rows(PredictiveInterventionScenarioRecord),"counterfactual_forecasts":rows(PredictiveCounterfactualForecastRecord),"causal_effect_evidence":rows(PredictiveCausalEffectEvidenceRecord),"evaluations":rows(PredictiveCausalEvaluationRecord),"handoffs":rows(PredictiveCausalHandoffRecord),"packages":rows(PredictiveCausalPackageRecord),"boundaries":boundaries()}

def create_causal_predictive_package(db:Session,study_id:str,payload:dict):
    _reject(payload); state=causal_predictive_bundle(db,study_id); state.pop("packages",None); digest=_sha256(state)
    last=db.scalar(select(PredictiveCausalPackageRecord).where(PredictiveCausalPackageRecord.causal_predictive_study_id==study_id).order_by(PredictiveCausalPackageRecord.revision.desc())); rev=(last.revision+1) if last else 1
    row=PredictiveCausalPackageRecord(causal_predictive_study_id=study_id,revision=rev,content_hash=digest,previous_package_hash=(last.content_hash if last else None),state_json=state,environment_json=dict(payload.get("environment") or {}),provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)
