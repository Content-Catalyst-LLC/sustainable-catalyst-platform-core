from __future__ import annotations
from datetime import datetime, timedelta, timezone
from math import floor
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    DistributedQuotaPolicy, DistributedQuotaUsageBucket, WorkloadAdmissionDecision,
    WorkloadAdmissionLease, WorkloadClassRecord,
)
from . import capacity, observability

VALID_SCOPES = {"product", "tenant", "application", "service", "developer"}
VALID_ENFORCEMENT = {"enforce", "observe"}
VALID_DECISIONS = {"allow", "throttle", "reject"}


def now(): return datetime.now(timezone.utc)

def aware(value):
    if value is None: return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

def clean_meta(value):
    value = value or {}
    blocked = {"secret", "token", "password", "authorization", "api_key", "private_key"}
    return {str(k)[:120]: v for k, v in value.items() if str(k).lower() not in blocked}

def workload_class_dict(row):
    return {"id":row.id,"class_key":row.class_key,"name":row.name,"priority":row.priority,"queue_weight":row.queue_weight,
            "max_concurrent_leases":row.max_concurrent_leases,"max_request_units":row.max_request_units,
            "allow_when_slo_breached":row.allow_when_slo_breached,"allow_when_capacity_critical":row.allow_when_capacity_critical,
            "enabled":row.enabled,"public_summary":row.public_summary,"metadata":row.metadata_json}

def policy_dict(row):
    return {"id":row.id,"policy_key":row.policy_key,"name":row.name,"subject_scope":row.subject_scope,"subject_key":row.subject_key,
            "resource_type":row.resource_type,"workload_class_key":row.workload_class_key,"window_seconds":row.window_seconds,
            "limit_units":row.limit_units,"burst_units":row.burst_units,"enforcement_mode":row.enforcement_mode,"enabled":row.enabled,
            "public_summary":row.public_summary,"metadata":row.metadata_json}

def decision_dict(row):
    return {"id":row.id,"request_key":row.request_key,"subject_scope":row.subject_scope,"subject_key":row.subject_key,
            "resource_type":row.resource_type,"workload_class_key":row.workload_class_key,"requested_units":row.requested_units,
            "decision":row.decision,"reason":row.reason,"policy_id":row.policy_id,"quota_limit":row.quota_limit,
            "quota_used_before":row.quota_used_before,"quota_remaining_after":row.quota_remaining_after,
            "retry_after_seconds":row.retry_after_seconds,"capacity_state":row.capacity_state,"slo_state":row.slo_state,
            "hard_enforcement":row.hard_enforcement,"evidence":row.evidence_json,"created_at":row.created_at}

def lease_dict(row):
    return {"id":row.id,"lease_key":row.lease_key,"decision_id":row.decision_id,"subject_scope":row.subject_scope,
            "subject_key":row.subject_key,"workload_class_key":row.workload_class_key,"units":row.units,"state":row.state,
            "acquired_at":row.acquired_at,"expires_at":row.expires_at,"released_at":row.released_at,"metadata":row.metadata_json}


def upsert_workload_class(db: Session, *, class_key, name, priority=100, queue_weight=1.0, max_concurrent_leases=64,
                          max_request_units=1000.0, allow_when_slo_breached=False, allow_when_capacity_critical=False,
                          enabled=True, public_summary=True, metadata=None):
    key=class_key.strip()
    if not key: raise ValueError("class_key is required")
    if priority < 0 or priority > 1000: raise ValueError("priority must be between 0 and 1000")
    if queue_weight <= 0 or queue_weight > 1000: raise ValueError("queue_weight must be greater than 0 and at most 1000")
    if max_concurrent_leases < 1 or max_concurrent_leases > 1000000: raise ValueError("max_concurrent_leases out of range")
    if max_request_units <= 0: raise ValueError("max_request_units must be positive")
    row=db.scalar(select(WorkloadClassRecord).where(WorkloadClassRecord.class_key==key))
    values=dict(class_key=key,name=name.strip(),priority=int(priority),queue_weight=float(queue_weight),
                max_concurrent_leases=int(max_concurrent_leases),max_request_units=float(max_request_units),
                allow_when_slo_breached=bool(allow_when_slo_breached),allow_when_capacity_critical=bool(allow_when_capacity_critical),
                enabled=bool(enabled),public_summary=bool(public_summary),metadata_json=clean_meta(metadata))
    if row is None: row=WorkloadClassRecord(**values); db.add(row)
    else:
        for k,v in values.items(): setattr(row,k,v)
    db.commit(); db.refresh(row); return row


def list_workload_classes(db: Session, enabled_only=False):
    q=select(WorkloadClassRecord).order_by(WorkloadClassRecord.priority,WorkloadClassRecord.class_key)
    if enabled_only: q=q.where(WorkloadClassRecord.enabled.is_(True))
    return list(db.scalars(q).all())


def upsert_policy(db: Session, settings, *, policy_key, name, subject_scope="product", subject_key="*", resource_type="requests",
                  workload_class_key=None, window_seconds=None, limit_units=1000.0, burst_units=0.0,
                  enforcement_mode="enforce", enabled=True, public_summary=False, metadata=None):
    if subject_scope not in VALID_SCOPES: raise ValueError("unsupported subject_scope")
    if enforcement_mode not in VALID_ENFORCEMENT: raise ValueError("enforcement_mode must be enforce or observe")
    if limit_units <= 0 or burst_units < 0: raise ValueError("quota limits must be positive and burst non-negative")
    window=int(window_seconds or settings.quota_default_window_seconds)
    if window < 1 or window > 86400: raise ValueError("window_seconds must be between 1 and 86400")
    if workload_class_key and db.scalar(select(WorkloadClassRecord).where(WorkloadClassRecord.class_key==workload_class_key)) is None:
        raise ValueError("workload class not found")
    key=policy_key.strip(); row=db.scalar(select(DistributedQuotaPolicy).where(DistributedQuotaPolicy.policy_key==key))
    values=dict(policy_key=key,name=name.strip(),subject_scope=subject_scope,subject_key=subject_key.strip() or "*",
                resource_type=resource_type.strip(),workload_class_key=workload_class_key,window_seconds=window,
                limit_units=float(limit_units),burst_units=float(burst_units),enforcement_mode=enforcement_mode,
                enabled=bool(enabled),public_summary=bool(public_summary),metadata_json=clean_meta(metadata))
    if row is None: row=DistributedQuotaPolicy(**values); db.add(row)
    else:
        for k,v in values.items(): setattr(row,k,v)
    db.commit(); db.refresh(row); return row


def list_policies(db: Session, enabled_only=False):
    q=select(DistributedQuotaPolicy).order_by(DistributedQuotaPolicy.subject_scope,DistributedQuotaPolicy.subject_key,DistributedQuotaPolicy.resource_type)
    if enabled_only: q=q.where(DistributedQuotaPolicy.enabled.is_(True))
    return list(db.scalars(q).all())


def _bucket_start(at: datetime, seconds: int):
    at=aware(at) or now(); epoch=int(at.timestamp()); return datetime.fromtimestamp(floor(epoch/seconds)*seconds,tz=timezone.utc)

def _policy_for(db, *, subject_scope, subject_key, resource_type, workload_class_key):
    q=select(DistributedQuotaPolicy).where(
        DistributedQuotaPolicy.enabled.is_(True), DistributedQuotaPolicy.subject_scope==subject_scope,
        DistributedQuotaPolicy.resource_type==resource_type,
        or_(DistributedQuotaPolicy.subject_key==subject_key, DistributedQuotaPolicy.subject_key=="*"),
        or_(DistributedQuotaPolicy.workload_class_key==workload_class_key, DistributedQuotaPolicy.workload_class_key.is_(None)),
    )
    rows=list(db.scalars(q).all())
    if not rows: return None
    rows.sort(key=lambda r:(r.subject_key!="*", r.workload_class_key is not None, -r.limit_units), reverse=True)
    return rows[0]

def _quota_bucket(db, policy, at):
    start=_bucket_start(at,policy.window_seconds)
    row=db.scalar(select(DistributedQuotaUsageBucket).where(DistributedQuotaUsageBucket.policy_id==policy.id,DistributedQuotaUsageBucket.bucket_start==start))
    if row is None:
        row=DistributedQuotaUsageBucket(policy_id=policy.id,bucket_start=start); db.add(row)
        try: db.flush()
        except IntegrityError:
            db.rollback(); row=db.scalar(select(DistributedQuotaUsageBucket).where(DistributedQuotaUsageBucket.policy_id==policy.id,DistributedQuotaUsageBucket.bucket_start==start))
    return row,start

def release_expired_leases(db: Session, at=None):
    at=aware(at) or now()
    rows=list(db.scalars(select(WorkloadAdmissionLease).where(WorkloadAdmissionLease.state=="active",WorkloadAdmissionLease.expires_at<=at)).all())
    for row in rows: row.state="expired"; row.released_at=at
    if rows: db.commit()
    return len(rows)

def active_leases(db: Session, class_key: str):
    release_expired_leases(db)
    return int(db.scalar(select(func.count()).select_from(WorkloadAdmissionLease).where(WorkloadAdmissionLease.workload_class_key==class_key,WorkloadAdmissionLease.state=="active")) or 0)

def _slo_state(db: Session, settings):
    if not settings.admission_slo_awareness_enabled: return "not-evaluated", []
    rows=observability.evaluate_all(db,"platform-core")
    if any(r["state"]=="breached" for r in rows): return "breached", rows
    if rows and all(r["state"]=="met" for r in rows): return "met", rows
    return "insufficient-data", rows

def _capacity_state(db: Session, settings):
    if not settings.admission_capacity_awareness_enabled: return "not-evaluated", {}
    snap=capacity.certification_snapshot(db,settings)
    if int(snap.get("critical_profiles",0))>0: return "critical",snap
    if int(snap.get("warning_profiles",0))>0: return "warning",snap
    return snap.get("state","stable"),snap

def admit(db: Session, settings, *, request_key, subject_scope, subject_key, resource_type="requests", workload_class_key="standard",
          requested_units=1.0, lease_key=None, lease_seconds=None, metadata=None):
    if not settings.workload_governance_enabled: raise ValueError("workload governance is disabled")
    if subject_scope not in VALID_SCOPES: raise ValueError("unsupported subject_scope")
    if requested_units <= 0: raise ValueError("requested_units must be positive")
    existing=db.scalar(select(WorkloadAdmissionDecision).where(WorkloadAdmissionDecision.request_key==request_key))
    if existing:
        lease=db.scalar(select(WorkloadAdmissionLease).where(WorkloadAdmissionLease.decision_id==existing.id))
        return existing,lease
    klass=db.scalar(select(WorkloadClassRecord).where(WorkloadClassRecord.class_key==workload_class_key,WorkloadClassRecord.enabled.is_(True)))
    if klass is None: raise ValueError("enabled workload class not found")
    at=now(); cap_state,cap_evidence=_capacity_state(db,settings); slo_state,slo_evidence=_slo_state(db,settings)
    policy=_policy_for(db,subject_scope=subject_scope,subject_key=subject_key,resource_type=resource_type,workload_class_key=workload_class_key)
    decision="allow"; reason="within-governed-workload-limits"; retry=None; used_before=None; remaining=None; quota_limit=None; bucket=None
    hard=bool(settings.admission_hard_enforcement_enabled)
    if requested_units > klass.max_request_units:
        decision="reject" if hard else "throttle"; reason="request-unit-limit-exceeded"
    concurrent=active_leases(db,workload_class_key)
    if decision=="allow" and concurrent >= klass.max_concurrent_leases:
        decision="throttle"; reason="workload-class-concurrency-limit"; retry=max(1,int(lease_seconds or settings.admission_default_lease_seconds))
    if decision=="allow" and cap_state=="critical" and not klass.allow_when_capacity_critical:
        decision="throttle"; reason="capacity-critical"; retry=max(1,int(lease_seconds or settings.admission_default_lease_seconds))
    if decision=="allow" and slo_state=="breached" and not klass.allow_when_slo_breached:
        decision="throttle"; reason="slo-breached"; retry=max(1,int(lease_seconds or settings.admission_default_lease_seconds))
    if policy is not None:
        bucket,start=_quota_bucket(db,policy,at); used_before=float(bucket.used_units); quota_limit=float(policy.limit_units+policy.burst_units); remaining=max(0.0,quota_limit-used_before)
        if decision=="allow" and used_before+requested_units>quota_limit:
            retry=max(1,int(policy.window_seconds-(at-start).total_seconds()))
            if policy.enforcement_mode=="enforce" and hard: decision="reject"; reason="distributed-quota-exhausted"
            elif policy.enforcement_mode=="enforce": decision="throttle"; reason="distributed-quota-exhausted-observe-hard-disabled"
            else: reason="quota-exceeded-observe-only"
    row=WorkloadAdmissionDecision(request_key=request_key.strip(),subject_scope=subject_scope,subject_key=subject_key.strip(),resource_type=resource_type.strip(),
        workload_class_key=workload_class_key,requested_units=float(requested_units),decision=decision,reason=reason,policy_id=policy.id if policy else None,
        quota_limit=quota_limit,quota_used_before=used_before,quota_remaining_after=(max(0.0,(quota_limit or 0)-(used_before or 0)-requested_units) if quota_limit is not None and decision=="allow" else remaining),
        retry_after_seconds=retry,capacity_state=cap_state,slo_state=slo_state,hard_enforcement=hard,
        evidence_json={"active_class_leases":concurrent,"class_priority":klass.priority,"queue_weight":klass.queue_weight,
                       "capacity":{"state":cap_state,"critical_profiles":cap_evidence.get("critical_profiles",0)},
                       "slo":{"state":slo_state,"evaluated":len(slo_evidence)},"metadata":clean_meta(metadata)})
    db.add(row); db.flush()
    lease=None
    if bucket is not None:
        if decision=="allow": bucket.used_units=float(bucket.used_units)+float(requested_units); bucket.admitted_requests+=1
        elif decision=="reject": bucket.rejected_requests+=1
        else: bucket.throttled_requests+=1
    if decision=="allow":
        secs=max(1,min(int(lease_seconds or settings.admission_default_lease_seconds),86400))
        lease=WorkloadAdmissionLease(lease_key=(lease_key or f"admission:{request_key}")[:255],decision_id=row.id,subject_scope=subject_scope,subject_key=subject_key,
            workload_class_key=workload_class_key,units=float(requested_units),state="active",expires_at=at+timedelta(seconds=secs),metadata_json=clean_meta(metadata))
        db.add(lease)
    db.commit(); db.refresh(row)
    if lease: db.refresh(lease)
    return row,lease

def release_lease(db: Session, lease_id: str):
    row=db.get(WorkloadAdmissionLease,lease_id)
    if row is None: raise ValueError("lease not found")
    if row.state=="active": row.state="released"; row.released_at=now(); db.commit(); db.refresh(row)
    return row

def list_decisions(db: Session, limit=200):
    return list(db.scalars(select(WorkloadAdmissionDecision).order_by(WorkloadAdmissionDecision.created_at.desc()).limit(limit)).all())

def list_leases(db: Session, state=None, limit=200):
    release_expired_leases(db); q=select(WorkloadAdmissionLease).order_by(WorkloadAdmissionLease.acquired_at.desc()).limit(limit)
    if state: q=q.where(WorkloadAdmissionLease.state==state)
    return list(db.scalars(q).all())

def compact(db: Session, settings):
    cutoff=now()-timedelta(hours=settings.quota_usage_retention_hours)
    q=db.execute(delete(DistributedQuotaUsageBucket).where(DistributedQuotaUsageBucket.bucket_start<cutoff));
    dcut=now()-timedelta(hours=settings.admission_decision_retention_hours)
    # decisions with leases are retained by FK; cleanup is intentionally conservative.
    db.commit(); return {"quota_buckets_deleted":int(q.rowcount or 0),"decision_cleanup":"conservative"}

def readiness(db: Session, settings):
    classes=int(db.scalar(select(func.count()).select_from(WorkloadClassRecord).where(WorkloadClassRecord.enabled.is_(True))) or 0)
    policies=int(db.scalar(select(func.count()).select_from(DistributedQuotaPolicy).where(DistributedQuotaPolicy.enabled.is_(True))) or 0)
    active=int(db.scalar(select(func.count()).select_from(WorkloadAdmissionLease).where(WorkloadAdmissionLease.state=="active")) or 0)
    rejected=int(db.scalar(select(func.count()).select_from(WorkloadAdmissionDecision).where(WorkloadAdmissionDecision.decision=="reject")) or 0)
    throttled=int(db.scalar(select(func.count()).select_from(WorkloadAdmissionDecision).where(WorkloadAdmissionDecision.decision=="throttle")) or 0)
    configured=classes>0 and policies>0
    return {"enabled":settings.workload_governance_enabled,"distributed_quota_backend":"database-shared","shared_state":True,
            "workload_classes":classes,"quota_policies":policies,"active_leases":active,"rejected_decisions":rejected,"throttled_decisions":throttled,
            "configured":configured,"hard_admission_control":bool(settings.admission_hard_enforcement_enabled),
            "slo_aware":bool(settings.admission_slo_awareness_enabled),"capacity_aware":bool(settings.admission_capacity_awareness_enabled),
            "automatic_scaling":False,"automatic_infrastructure_purchase":False,"automatic_deployment_mutation":False,
            "fairness_model":"per-subject-quota-plus-workload-class","external_quota_service_required":False}

def certification_snapshot(db: Session, settings):
    body=readiness(db,settings)
    body["workload_governance_ready"]=bool(body["enabled"] and body["configured"] and body["hard_admission_control"] and body["shared_state"])
    body["state"]="ready" if body["workload_governance_ready"] else ("unconfigured" if body["enabled"] else "disabled")
    return body

def public_status(db: Session, settings):
    body=readiness(db,settings)
    if not settings.workload_governance_public_status_enabled: return {"enabled":body["enabled"],"public_status_enabled":False}
    return {"enabled":body["enabled"],"public_status_enabled":True,"configured":body["configured"],"state":"ready" if body["configured"] else "unconfigured",
            "distributed_quota_backend":body["distributed_quota_backend"],"shared_state":body["shared_state"],"hard_admission_control":body["hard_admission_control"],
            "slo_aware":body["slo_aware"],"capacity_aware":body["capacity_aware"],"workload_classes":body["workload_classes"],"quota_policies":body["quota_policies"],
            "automatic_scaling":False,"automatic_infrastructure_purchase":False,"quota_limits_exposed":False,"subject_usage_exposed":False}

def bootstrap_defaults(db: Session, settings):
    classes=[
        upsert_workload_class(db,class_key="critical",name="Critical platform work",priority=10,queue_weight=4.0,max_concurrent_leases=32,max_request_units=1000,allow_when_slo_breached=True,allow_when_capacity_critical=True,public_summary=True),
        upsert_workload_class(db,class_key="standard",name="Standard platform work",priority=100,queue_weight=1.0,max_concurrent_leases=64,max_request_units=500,public_summary=True),
        upsert_workload_class(db,class_key="batch",name="Batch and background work",priority=500,queue_weight=0.5,max_concurrent_leases=16,max_request_units=5000,public_summary=True),
    ]
    policies=[
        upsert_policy(db,settings,policy_key="platform-standard-requests",name="Platform standard request quota",subject_scope="product",subject_key="*",resource_type="requests",workload_class_key="standard",window_seconds=60,limit_units=1000,burst_units=200,enforcement_mode="enforce"),
        upsert_policy(db,settings,policy_key="platform-batch-units",name="Platform batch work quota",subject_scope="product",subject_key="*",resource_type="work-units",workload_class_key="batch",window_seconds=300,limit_units=10000,burst_units=1000,enforcement_mode="enforce"),
    ]
    return classes,policies
