from __future__ import annotations
from datetime import datetime, timedelta, timezone
from math import ceil
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..models import ObservabilityMetricSample, ProductionDeploymentMarker, ServiceLevelObjective

VALID_INDICATORS={"availability_percent","error_rate_percent","latency_p95_ms"}
VALID_COMPARISONS={">=","<="}
VALID_DEPLOYMENT_STATES={"started","deployed","failed","rollback","rolled_back"}

def _now(): return datetime.now(timezone.utc)
def _status_class(code:int|None):
    if code is None: return None
    return f"{int(code)//100}xx"
def record_metric(session:Session, *, service:str="platform-core", metric_name:str, value:float, unit:str="count", method:str|None=None, route:str|None=None, status_code:int|None=None, request_id:str|None=None, labels:dict|None=None, observed_at:datetime|None=None):
    row=ObservabilityMetricSample(service=(service or "platform-core")[:100],metric_name=metric_name[:120],value=float(value),unit=(unit or "count")[:40],method=(method or "")[:16] or None,route=(route or "")[:600] or None,status_code=status_code,status_class=_status_class(status_code),request_id=(request_id or "")[:128] or None,labels_json=labels or {},observed_at=observed_at or _now())
    session.add(row); session.commit(); session.refresh(row); return row

def record_request(session:Session, *, service:str="platform-core", method:str, route:str, status_code:int, duration_ms:float, request_id:str|None=None):
    # One row per request keeps the local-first implementation auditable and portable.
    return record_metric(session,service=service,metric_name="http_request_duration_ms",value=duration_ms,unit="ms",method=method,route=route,status_code=status_code,request_id=request_id,labels={"request":True})

def _window_rows(session:Session, service:str, window_minutes:int):
    cutoff=_now()-timedelta(minutes=window_minutes)
    return session.scalars(select(ObservabilityMetricSample).where(ObservabilityMetricSample.service==service,ObservabilityMetricSample.metric_name=="http_request_duration_ms",ObservabilityMetricSample.observed_at>=cutoff).order_by(ObservabilityMetricSample.observed_at.asc())).all()

def _p95(values:list[float]):
    if not values: return None
    values=sorted(values); idx=max(0,min(len(values)-1,ceil(len(values)*.95)-1)); return round(float(values[idx]),2)

def summary(session:Session, service:str="platform-core", window_minutes:int=60):
    rows=_window_rows(session,service,window_minutes); total=len(rows); errors=sum(1 for r in rows if (r.status_code or 0)>=500); success=total-errors
    return {"service":service,"window_minutes":window_minutes,"sample_count":total,"availability_percent":round(success*100/total,4) if total else None,"error_rate_percent":round(errors*100/total,4) if total else None,"latency_p95_ms":_p95([r.value for r in rows]),"http_5xx_count":errors,"no_samples":total==0}

def create_slo(session:Session, *, service:str="platform-core", name:str, indicator:str, target:float, comparison:str|None=None, window_minutes:int=60, minimum_samples:int=1, metadata:dict|None=None, enabled:bool=True):
    if indicator not in VALID_INDICATORS: raise ValueError("Unsupported SLO indicator.")
    comp=comparison or (">=" if indicator=="availability_percent" else "<=")
    if comp not in VALID_COMPARISONS: raise ValueError("Unsupported SLO comparison.")
    if window_minutes<1 or minimum_samples<1: raise ValueError("SLO window and minimum samples must be positive.")
    if indicator.endswith("percent") and not 0<=target<=100: raise ValueError("Percentage SLO target must be between 0 and 100.")
    row=ServiceLevelObjective(service=service,name=name,indicator=indicator,target=float(target),comparison=comp,window_minutes=window_minutes,minimum_samples=minimum_samples,metadata_json=metadata or {},enabled=enabled)
    session.add(row)
    try: session.commit()
    except IntegrityError:
        session.rollback(); raise ValueError("An SLO with this service and name already exists.")
    session.refresh(row); return row

def list_slos(session:Session, service:str|None=None):
    q=select(ServiceLevelObjective).order_by(ServiceLevelObjective.service,ServiceLevelObjective.name)
    if service: q=q.where(ServiceLevelObjective.service==service)
    return session.scalars(q).all()

def evaluate_slo(session:Session, row:ServiceLevelObjective):
    s=summary(session,row.service,row.window_minutes); value=s.get(row.indicator); enough=s["sample_count"]>=row.minimum_samples
    met=None if not enough or value is None else (value>=row.target if row.comparison==">=" else value<=row.target)
    if met is None: state="insufficient_data"
    else: state="met" if met else "breached"
    # Burn ratio is direction-aware and descriptive, not an alerting substitute.
    burn=None
    if enough and value is not None:
        if row.indicator=="availability_percent":
            budget=max(0.0001,100-row.target); burn=round(max(0.0,100-value)/budget,4)
        elif row.indicator=="error_rate_percent": burn=round(value/max(0.0001,row.target),4)
        elif row.indicator=="latency_p95_ms": burn=round(value/max(0.0001,row.target),4)
    return {"id":row.id,"service":row.service,"name":row.name,"indicator":row.indicator,"target":row.target,"comparison":row.comparison,"window_minutes":row.window_minutes,"minimum_samples":row.minimum_samples,"sample_count":s["sample_count"],"value":value,"state":state,"burn_ratio":burn}

def evaluate_all(session:Session, service:str|None=None): return [evaluate_slo(session,x) for x in list_slos(session,service) if x.enabled]

def create_deployment_marker(session:Session, *, release:str, environment:str, state:str="deployed", commit_sha:str|None=None, actor:str="operator", metadata:dict|None=None):
    if state not in VALID_DEPLOYMENT_STATES: raise ValueError("Unsupported deployment state.")
    row=ProductionDeploymentMarker(release=release,environment=environment,state=state,commit_sha=(commit_sha or "")[:128] or None,actor=(actor or "operator")[:255],metadata_json=metadata or {})
    session.add(row); session.commit(); session.refresh(row); return row

def list_deployments(session:Session, limit:int=100): return session.scalars(select(ProductionDeploymentMarker).order_by(ProductionDeploymentMarker.created_at.desc()).limit(limit)).all()
def compact_metrics(session:Session, retention_hours:int):
    cutoff=_now()-timedelta(hours=retention_hours); result=session.execute(delete(ObservabilityMetricSample).where(ObservabilityMetricSample.observed_at<cutoff)); session.commit(); return int(result.rowcount or 0)

def readiness(session:Session, settings):
    slo_count=session.scalar(select(func.count()).select_from(ServiceLevelObjective).where(ServiceLevelObjective.enabled.is_(True))) or 0
    metric_count=session.scalar(select(func.count()).select_from(ObservabilityMetricSample)) or 0
    latest=session.scalars(select(ProductionDeploymentMarker).order_by(ProductionDeploymentMarker.created_at.desc()).limit(1)).first()
    return {"enabled":settings.observability_control_plane_enabled,"request_metrics_enabled":settings.observability_request_metrics_enabled,"public_status_enabled":settings.observability_public_status_enabled,"retention_hours":settings.observability_retention_hours,"default_window_minutes":settings.observability_default_window_minutes,"active_slos":int(slo_count),"metric_samples":int(metric_count),"latest_deployment_release":latest.release if latest else None,"latest_deployment_state":latest.state if latest else None,"external_monitoring_provider_required":False,"paid_monitoring_provider_required":False,"evidence_semantics_unchanged":True}
