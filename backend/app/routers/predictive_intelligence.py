from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import predictive_intelligence as svc

router=APIRouter(prefix="/v1/predictive-intelligence",tags=["Predictive Intelligence"])
public_router=APIRouter(prefix="/api/v1/predictive-intelligence",tags=["Public Predictive Intelligence"])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def bad(exc): return exc if isinstance(exc,HTTPException) else HTTPException(status_code=422,detail=str(exc))
def enabled(request):
    if not request.app.state.settings.predictive_intelligence_enabled: raise HTTPException(status_code=404,detail="Predictive Intelligence is disabled.")
def public_enabled(request):
    enabled(request)
    if not request.app.state.settings.predictive_intelligence_public_metadata_enabled: raise HTTPException(status_code=404,detail="Public Predictive Intelligence metadata is disabled.")
@router.get("/readiness",dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    enabled(request); data=svc.readiness(db); data.update({"release":request.app.state.settings.version,"enabled":True}); return data
@router.post("/models",dependencies=[Depends(require_write)])
def create_model(request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.create_model(db,payload.data)
    except Exception as exc:raise bad(exc)
@router.get("/models",dependencies=[Depends(require_read)])
def models(request:Request,project_entity_id:str|None=None,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    enabled(request); items,total=svc.list_models(db,project_entity_id=project_entity_id,limit=limit,offset=offset); return {"items":items,"total":total,"limit":limit,"offset":offset}
@router.get("/models/{model_id}/bundle",dependencies=[Depends(require_read)])
def bundle(model_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return svc.bundle(db,model_id)
@router.post("/models/{model_id}/targets",dependencies=[Depends(require_write)])
def target(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_target(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/features",dependencies=[Depends(require_write)])
def feature(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_feature(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/training-windows",dependencies=[Depends(require_write)])
def window(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_training_window(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/forecast-runs",dependencies=[Depends(require_write)])
def run(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_forecast_run(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/forecast-runs/{run_id}/observations",dependencies=[Depends(require_write)])
def observation(model_id:str,run_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_forecast_observation(db,model_id,run_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/evaluations",dependencies=[Depends(require_write)])
def evaluation(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_evaluation(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/handoffs",dependencies=[Depends(require_write)])
def handoff(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_handoff(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/snapshots",dependencies=[Depends(require_write)])
def snapshot(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.create_snapshot(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/time-series-datasets",dependencies=[Depends(require_write)])
def time_series_dataset(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_time_series_dataset(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/forecast-windows",dependencies=[Depends(require_write)])
def forecast_window(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_forecast_window(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/baselines",dependencies=[Depends(require_write)])
def baseline(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_baseline_model(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/backtest-plans",dependencies=[Depends(require_write)])
def backtest_plan(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.create_backtest_plan(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/backtest-plans/{plan_id}/folds",dependencies=[Depends(require_write)])
def backtest_fold(model_id:str,plan_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_backtest_fold(db,model_id,plan_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/backtest-plans/{plan_id}/folds/{fold_id}/observations",dependencies=[Depends(require_write)])
def backtest_observation(model_id:str,plan_id:str,fold_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_backtest_observation(db,model_id,plan_id,fold_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/backtest-plans/{plan_id}/evaluations",dependencies=[Depends(require_write)])
def backtest_evaluation(model_id:str,plan_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_backtest_evaluation(db,model_id,plan_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.get("/models/{model_id}/backtest-plans/{plan_id}/bundle",dependencies=[Depends(require_read)])
def backtest_bundle(model_id:str,plan_id:str,request:Request,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.backtest_bundle(db,model_id,plan_id)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/backtest-plans/{plan_id}/packages",dependencies=[Depends(require_write)])
def backtest_package(model_id:str,plan_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.create_backtest_package(db,model_id,plan_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/probabilistic-forecasts",dependencies=[Depends(require_write)])
def probabilistic_forecast(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_probabilistic_forecast(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/calibration-studies",dependencies=[Depends(require_write)])
def calibration_study(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.create_calibration_study(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/calibration-studies/{study_id}/bins",dependencies=[Depends(require_write)])
def calibration_bin(model_id:str,study_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_calibration_bin(db,model_id,study_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/calibration-studies/{study_id}/mappings",dependencies=[Depends(require_write)])
def calibration_mapping(model_id:str,study_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_calibration_mapping(db,model_id,study_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/probabilistic-evaluations",dependencies=[Depends(require_write)])
def probabilistic_evaluation(model_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_probabilistic_evaluation(db,model_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.get("/models/{model_id}/calibration-studies/{study_id}/bundle",dependencies=[Depends(require_read)])
def calibration_bundle(model_id:str,study_id:str,request:Request,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.calibration_bundle(db,model_id,study_id)
    except Exception as exc:raise bad(exc)
@router.post("/models/{model_id}/calibration-studies/{study_id}/packages",dependencies=[Depends(require_write)])
def calibration_package(model_id:str,study_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.create_calibration_package(db,model_id,study_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/ensembles",dependencies=[Depends(require_write)])
def ensemble_create(request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.create_ensemble(db,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/ensembles/{ensemble_id}/members",dependencies=[Depends(require_write)])
def ensemble_member(ensemble_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_ensemble_member(db,ensemble_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/ensembles/{ensemble_id}/forecasts",dependencies=[Depends(require_write)])
def ensemble_forecast(ensemble_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_ensemble_forecast(db,ensemble_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.get("/ensembles/{ensemble_id}/bundle",dependencies=[Depends(require_read)])
def ensemble_bundle(ensemble_id:str,request:Request,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.ensemble_bundle(db,ensemble_id)
    except Exception as exc:raise bad(exc)
@router.post("/comparison-studies",dependencies=[Depends(require_write)])
def comparison_study_create(request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.create_comparison_study(db,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/comparison-studies/{study_id}/candidates",dependencies=[Depends(require_write)])
def comparison_candidate(study_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_comparison_candidate(db,study_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/comparison-studies/{study_id}/evidence",dependencies=[Depends(require_write)])
def comparison_evidence(study_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_comparison_evidence(db,study_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/comparison-studies/{study_id}/pairwise-evidence",dependencies=[Depends(require_write)])
def pairwise_comparison(study_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_pairwise_comparison(db,study_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.get("/comparison-studies/{study_id}/bundle",dependencies=[Depends(require_read)])
def comparison_bundle(study_id:str,request:Request,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.comparison_bundle(db,study_id)
    except Exception as exc:raise bad(exc)
@router.post("/comparison-studies/{study_id}/packages",dependencies=[Depends(require_write)])
def comparison_package(study_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.create_comparison_package(db,study_id,payload.data)
    except Exception as exc:raise bad(exc)

@router.post("/monitoring-studies",dependencies=[Depends(require_write)])
def monitoring_study_create(request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.create_monitoring_study(db,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/monitoring-studies/{study_id}/rules",dependencies=[Depends(require_write)])
def monitoring_rule(study_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_detection_rule(db,study_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/monitoring-studies/{study_id}/anomalies",dependencies=[Depends(require_write)])
def monitoring_anomaly(study_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_anomaly_observation(db,study_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/monitoring-studies/{study_id}/change-points",dependencies=[Depends(require_write)])
def monitoring_change_point(study_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_change_point(db,study_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/monitoring-studies/{study_id}/early-warning-signals",dependencies=[Depends(require_write)])
def monitoring_early_warning(study_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_early_warning_signal(db,study_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.post("/monitoring-studies/{study_id}/episodes",dependencies=[Depends(require_write)])
def monitoring_episode(study_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.add_monitoring_episode(db,study_id,payload.data)
    except Exception as exc:raise bad(exc)
@router.get("/monitoring-studies/{study_id}/bundle",dependencies=[Depends(require_read)])
def monitoring_bundle(study_id:str,request:Request,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.monitoring_bundle(db,study_id)
    except Exception as exc:raise bad(exc)
@router.post("/monitoring-studies/{study_id}/packages",dependencies=[Depends(require_write)])
def monitoring_package(study_id:str,request:Request,payload:Payload,db:Session=Depends(get_session)):
    enabled(request)
    try:return svc.create_monitoring_package(db,study_id,payload.data)
    except Exception as exc:raise bad(exc)

@public_router.get("/readiness",response_model=PublicEnvelope)
def public_readiness(request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); data=svc.readiness(db); data.update({"release":request.app.state.settings.version,"enabled":True}); return PublicEnvelope(data=data,meta={"api_version":"v1","request_id":request.state.request_id})
@public_router.get("/models",response_model=PublicEnvelope)
def public_models(request:Request,project_entity_id:str|None=None,limit:int=Query(100,ge=1),offset:int=Query(0,ge=0),ctx:PublicApiContext=Depends(require_public_scope("data:read")),db:Session=Depends(get_session)):
    public_enabled(request); limit=min(limit,ctx.plan.max_page_size,request.app.state.settings.page_size_max); items,total=svc.list_models(db,project_entity_id=project_entity_id,public_only=True,limit=limit,offset=offset); return PublicEnvelope(data=items,meta={"api_version":"v1","request_id":request.state.request_id,"pagination":{"total":total,"limit":limit,"offset":offset}})
@public_router.get("/models/{model_id}/bundle",response_model=PublicEnvelope)
def public_bundle(model_id:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); return PublicEnvelope(data=svc.bundle(db,model_id,public_only=True),meta={"api_version":"v1","request_id":request.state.request_id})
@public_router.get("/models/{model_id}/calibration-studies/{study_id}/bundle",response_model=PublicEnvelope)
def public_calibration_bundle(model_id:str,study_id:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request)
    model=svc._model(db,model_id)
    if model.visibility!="public": raise HTTPException(status_code=404,detail="Predictive model not found.")
    return PublicEnvelope(data=svc.calibration_bundle(db,model_id,study_id),meta={"api_version":"v1","request_id":request.state.request_id})



@public_router.get("/ensembles/{ensemble_id}/bundle",response_model=PublicEnvelope)
def public_ensemble_bundle(ensemble_id:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); ensemble=svc._ensemble(db,ensemble_id)
    if ensemble.visibility!="public": raise HTTPException(status_code=404,detail="Predictive ensemble not found.")
    return PublicEnvelope(data=svc.ensemble_bundle(db,ensemble_id),meta={"api_version":"v1","request_id":request.state.request_id})

@public_router.get("/comparison-studies/{study_id}/bundle",response_model=PublicEnvelope)
def public_comparison_bundle(study_id:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); study=svc._comparison(db,study_id)
    if study.visibility!="public": raise HTTPException(status_code=404,detail="Predictive comparison study not found.")
    return PublicEnvelope(data=svc.comparison_bundle(db,study_id),meta={"api_version":"v1","request_id":request.state.request_id})


@public_router.get("/monitoring-studies/{study_id}/bundle",response_model=PublicEnvelope)
def public_monitoring_bundle(study_id:str,request:Request,db:Session=Depends(get_session),_ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); study=svc._monitoring_study(db,study_id)
    if study.visibility!="public": raise HTTPException(status_code=404,detail="Predictive monitoring study not found.")
    return PublicEnvelope(data=svc.monitoring_bundle(db,study_id),meta={"api_version":"v1","request_id":request.state.request_id})
