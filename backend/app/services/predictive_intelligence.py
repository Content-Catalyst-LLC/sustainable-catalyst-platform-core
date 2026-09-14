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
)

MODEL_KINDS={"statistical","machine-learning","simulation","hybrid","rules-based","external","other"}
RUNTIME_PRODUCTS={"lab","workbench","site-intelligence","decision-studio","catalyst-data","external"}
FEATURE_ROLES={"predictor","lagged-predictor","exogenous","context","identifier","time-index","other"}
FORBIDDEN_FIELDS={"fit_by_core","train_by_core","infer_by_core","execute_by_core","core_execute","probability_calibrated_by_core","winner","rank","verdict","truth_value","automatic_truth_promotion","model_selected_by_core"}

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
      "model_fitting_by_core":False,"forecast_inference_execution_by_core":False,"probabilistic_calibration_by_core":False,
      "ensemble_selection_by_core":False,"automatic_model_ranking_by_core":False,"automatic_truth_promotion":False,
    }

def readiness(db:Session):
    def count(m): return int(db.scalar(select(func.count()).select_from(m)) or 0)
    return {"migration_0056_applied":True,"contract":"sc.predictive.model.v1","forecast_contract":"sc.predictive.forecast-provenance.v1","handoff_contract":"sc.predictive.runtime-handoff.v1","counts":{
      "models":count(PredictiveModelRecord),"targets":count(PredictiveTargetRecord),"features":count(PredictiveFeatureRecord),"training_windows":count(PredictiveTrainingWindowRecord),
      "forecast_runs":count(PredictiveForecastRunRecord),"forecast_observations":count(PredictiveForecastObservationRecord),"evaluations":count(PredictiveEvaluationRecord),"handoffs":count(PredictiveRuntimeHandoffRecord),"snapshots":count(PredictiveForecastSnapshotRecord)},**boundaries()}

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

def bundle(db:Session,model_id:str,public_only=False):
    model=_model(db,model_id)
    if public_only and model.visibility!="public": raise HTTPException(status_code=404,detail="Predictive model not found.")
    q=lambda m: [_ser(x) for x in db.scalars(select(m).where(m.model_id==model_id).order_by(m.created_at.asc())).all()]
    targets=q(PredictiveTargetRecord); features=q(PredictiveFeatureRecord); windows=q(PredictiveTrainingWindowRecord); runs=q(PredictiveForecastRunRecord); evals=q(PredictiveEvaluationRecord); handoffs=q(PredictiveRuntimeHandoffRecord); snaps=q(PredictiveForecastSnapshotRecord)
    observations=[]
    runids=[r["id"] for r in runs]
    if runids: observations=[_ser(x) for x in db.scalars(select(PredictiveForecastObservationRecord).where(PredictiveForecastObservationRecord.forecast_run_id.in_(runids)).order_by(PredictiveForecastObservationRecord.created_at.asc())).all()]
    return {"contract":"sc.predictive.forecast-provenance.v1","model":_ser(model),"targets":targets,"features":features,"training_windows":windows,"forecast_runs":runs,"forecast_observations":observations,"evaluations":evals,"handoffs":handoffs,"snapshots":snaps,"boundaries":boundaries()}

def create_snapshot(db:Session,model_id:str,payload:dict):
    _reject(payload); state=bundle(db,model_id); state.pop("snapshots",None); digest=_sha256(state); last=db.scalar(select(PredictiveForecastSnapshotRecord).where(PredictiveForecastSnapshotRecord.model_id==model_id).order_by(PredictiveForecastSnapshotRecord.revision.desc()))
    rev=(last.revision+1) if last else 1; row=PredictiveForecastSnapshotRecord(model_id=model_id,revision=rev,content_hash=digest,previous_snapshot_hash=(last.content_hash if last else None),state_json=state,provenance_json=dict(payload.get("provenance") or {}),created_by=str(payload.get("created_by") or "operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)
