from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..models import RegionServiceStatusRecord, FailoverGroupRecord, FailoverAssessmentRecord

SECRET_KEYS={"password","secret","token","authorization","api_key","apikey","credential","credentials","access_key","secret_key"}
HEALTH={"healthy","degraded","unavailable","maintenance","unknown"}
READINESS={"ready","degraded","blocked","unknown"}
REPLICATION={"current","lagging","unknown","not-applicable"}
ROLES={"primary","secondary","standby","edge"}
STRATEGIES={"operator-coordinated","manual","read-only-degraded"}
DECISION_STATES={"acknowledged","approved","rejected","executed"}

def _now(): return datetime.now(timezone.utc)
def _scrub(value):
    if isinstance(value,dict): return {str(k):("[redacted]" if str(k).lower() in SECRET_KEYS else _scrub(v)) for k,v in value.items()}
    if isinstance(value,list): return [_scrub(v) for v in value]
    return value

def upsert_region_status(db:Session,*,region_key:str,service:str="platform-core",environment:str="production",role:str="standby",health_state:str="unknown",readiness_state:str="unknown",replication_state:str="unknown",replication_lag_seconds:int|None=None,read_eligible:bool=False,write_eligible:bool=False,recovery_priority:int=100,endpoint_ref:str|None=None,metadata:dict|None=None):
    region_key=region_key.strip(); service=service.strip()
    if not region_key or not service: raise ValueError("region_key and service are required.")
    if role not in ROLES or health_state not in HEALTH or readiness_state not in READINESS or replication_state not in REPLICATION: raise ValueError("Unsupported region status value.")
    if replication_lag_seconds is not None and replication_lag_seconds<0: raise ValueError("replication_lag_seconds must be non-negative.")
    row=db.scalar(select(RegionServiceStatusRecord).where(RegionServiceStatusRecord.service==service,RegionServiceStatusRecord.environment==environment,RegionServiceStatusRecord.region_key==region_key))
    data=dict(role=role,health_state=health_state,readiness_state=readiness_state,replication_state=replication_state,replication_lag_seconds=replication_lag_seconds,read_eligible=read_eligible,write_eligible=write_eligible,recovery_priority=max(0,recovery_priority),endpoint_ref=(endpoint_ref[:500] if endpoint_ref else None),metadata_json=_scrub(metadata or {}),observed_at=_now())
    if row:
        for k,v in data.items(): setattr(row,k,v)
    else: row=RegionServiceStatusRecord(region_key=region_key[:100],service=service[:100],environment=environment[:40],**data); db.add(row)
    db.commit(); db.refresh(row); return row

def create_group(db:Session,settings,*,group_key:str,active_region:str,candidate_regions:list[str],service:str="platform-core",environment:str="production",strategy:str="operator-coordinated",degraded_read_only_allowed:bool|None=None,max_replication_lag_seconds:int|None=None,metadata:dict|None=None):
    group_key=group_key.strip(); active_region=active_region.strip(); candidates=[]
    for item in candidate_regions:
        item=str(item).strip()
        if item and item!=active_region and item not in candidates: candidates.append(item)
    if not group_key or not active_region or not candidates: raise ValueError("group_key, active_region, and at least one distinct candidate region are required.")
    if strategy not in STRATEGIES: raise ValueError("Unsupported failover strategy.")
    existing=db.scalar(select(FailoverGroupRecord).where(FailoverGroupRecord.group_key==group_key))
    if existing: return existing
    row=FailoverGroupRecord(group_key=group_key[:255],service=service[:100],environment=environment[:40],active_region=active_region[:100],candidate_regions_json=candidates,strategy=strategy,degraded_read_only_allowed=settings.multi_region_degraded_read_only_enabled if degraded_read_only_allowed is None else bool(degraded_read_only_allowed),max_replication_lag_seconds=settings.multi_region_default_max_replication_lag_seconds if max_replication_lag_seconds is None else max(0,max_replication_lag_seconds),automatic_failover=False,metadata_json=_scrub(metadata or {}))
    db.add(row); db.commit(); db.refresh(row); return row

def list_regions(db:Session,service:str|None=None,environment:str|None=None):
    q=select(RegionServiceStatusRecord)
    if service: q=q.where(RegionServiceStatusRecord.service==service)
    if environment: q=q.where(RegionServiceStatusRecord.environment==environment)
    return db.scalars(q.order_by(RegionServiceStatusRecord.recovery_priority,RegionServiceStatusRecord.region_key)).all()

def list_groups(db:Session,environment:str|None=None):
    q=select(FailoverGroupRecord)
    if environment: q=q.where(FailoverGroupRecord.environment==environment)
    return db.scalars(q.order_by(FailoverGroupRecord.group_key)).all()

def _region(db,group,region):
    return db.scalar(select(RegionServiceStatusRecord).where(RegionServiceStatusRecord.service==group.service,RegionServiceStatusRecord.environment==group.environment,RegionServiceStatusRecord.region_key==region))

def _write_safe(row,max_lag):
    if not row or row.health_state!="healthy" or row.readiness_state!="ready" or not row.write_eligible: return False
    if row.replication_state=="not-applicable": return True
    if row.replication_state!="current": return False
    return row.replication_lag_seconds is None or row.replication_lag_seconds<=max_lag

def assess_failover(db:Session,group:FailoverGroupRecord,*,reason:str="operator-request"):
    source=_region(db,group,group.active_region)
    source_ok=bool(source and source.health_state=="healthy" and source.readiness_state=="ready")
    recommendation="stay"; target=None; read_only=False; write_safe=False; assessment_reason="active_region_healthy" if source_ok else "no_safe_target"
    if not source_ok:
        for region in group.candidate_regions_json or []:
            row=_region(db,group,region)
            if not row or row.health_state not in {"healthy","degraded"} or row.readiness_state not in {"ready","degraded"} or not row.read_eligible: continue
            target=region; write_safe=_write_safe(row,group.max_replication_lag_seconds)
            if write_safe:
                recommendation="failover"; assessment_reason="healthy_replication_safe_target"; break
            if group.degraded_read_only_allowed:
                recommendation="failover-read-only"; read_only=True; assessment_reason="read_eligible_target_write_safety_not_proven"; break
            target=None
        if target is None: recommendation="blocked"
    evidence={"requested_reason":reason,"source_health":source.health_state if source else "unknown","source_readiness":source.readiness_state if source else "unknown","target_replication_safe_for_write":write_safe,"automatic_failover_enabled":False,"infrastructure_actuation_by_core":False}
    row=FailoverAssessmentRecord(group_id=group.id,source_region=group.active_region,target_region=target,recommendation=recommendation,state="proposed",reason=assessment_reason,read_only=read_only,automatic_execution=False,infrastructure_actuation_by_core=False,replication_safe_for_write=write_safe,evidence_json=_scrub(evidence))
    db.add(row); db.commit(); db.refresh(row); return row

def decide_failover(db:Session,row:FailoverAssessmentRecord,*,state:str,actor:str):
    if state not in DECISION_STATES: raise ValueError("Unsupported failover decision state.")
    if state=="approved" and not row.acknowledged_by: raise ValueError("Failover must be acknowledged before approval.")
    if state=="executed" and not row.approved_by: raise ValueError("Failover must be explicitly approved before execution is recorded.")
    if state=="executed" and row.recommendation not in {"failover","failover-read-only"}: raise ValueError("Only an actionable failover recommendation can be recorded as executed.")
    if state=="acknowledged": row.acknowledged_by=actor[:255]
    elif state=="approved": row.approved_by=actor[:255]
    elif state=="executed": row.executed_by=actor[:255]
    row.state=state; row.automatic_execution=False; row.infrastructure_actuation_by_core=False; db.add(row); db.commit(); db.refresh(row); return row

def readiness(db:Session,settings,environment="production"):
    groups=list_groups(db,environment); regions=list_regions(db,environment=environment)
    blocked=0; degraded=0; ready_groups=0
    for group in groups:
        src=_region(db,group,group.active_region)
        if src and src.health_state=="healthy" and src.readiness_state=="ready": ready_groups+=1; continue
        candidates=[_region(db,group,r) for r in group.candidate_regions_json or []]
        if any(_write_safe(r,group.max_replication_lag_seconds) for r in candidates): degraded+=1
        elif group.degraded_read_only_allowed and any(r and r.read_eligible and r.health_state in {"healthy","degraded"} and r.readiness_state in {"ready","degraded"} for r in candidates): degraded+=1
        else: blocked+=1
    state="unconfigured" if not groups else ("blocked" if blocked else ("degraded" if degraded else "ready"))
    return {"enabled":settings.multi_region_resilience_enabled,"environment":environment,"state":state,"regions":len(regions),"failover_groups":len(groups),"ready_groups":ready_groups,"degraded_groups":degraded,"blocked_groups":blocked,"automatic_failover_enabled":False,"infrastructure_actuation_by_core":False,"degraded_read_only_supported":settings.multi_region_degraded_read_only_enabled,"write_failover_requires_replication_safety":True,"default_max_replication_lag_seconds":settings.multi_region_default_max_replication_lag_seconds,"provider_specific_failover_required":False,"evidence_semantics_unchanged":True}

def certification_snapshot(db:Session,settings,environment="production"):
    s=readiness(db,settings,environment); return {"state":s["state"],"multi_region_ready":s["state"] in {"ready","degraded"},"automatic_failover_enabled":False,"infrastructure_actuation_by_core":False}

def public_status(db:Session,settings,environment="production"):
    s=readiness(db,settings,environment)
    return {k:s[k] for k in ["enabled","environment","state","regions","failover_groups","ready_groups","degraded_groups","blocked_groups","automatic_failover_enabled","degraded_read_only_supported","write_failover_requires_replication_safety"]} | {"region_endpoints_publicly_exposed":False,"failover_evidence_publicly_exposed":False,"operator_identities_publicly_exposed":False}
