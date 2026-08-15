from __future__ import annotations
from datetime import datetime, timedelta, timezone
import hashlib, json
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..models import ScaleProcessingJob, ScaleProcessingPartition, ScaleStorageObject
from .reliability import emit_event, sanitize_queue_parameters

def now(): return datetime.now(timezone.utc)
def stable_bytes(value): return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()

def readiness(db: Session, settings):
    active = db.scalar(select(func.count()).select_from(ScaleProcessingJob).where(ScaleProcessingJob.state.in_(["queued","running"]))) or 0
    queued = db.scalar(select(func.count()).select_from(ScaleProcessingPartition).where(ScaleProcessingPartition.state=="queued")) or 0
    claimed = db.scalar(select(func.count()).select_from(ScaleProcessingPartition).where(ScaleProcessingPartition.state=="claimed")) or 0
    storage = db.scalar(select(func.count()).select_from(ScaleStorageObject).where(ScaleStorageObject.retention_state=="active")) or 0
    backpressure = queued >= settings.scale_queue_backpressure_threshold or active >= settings.scale_max_active_jobs
    return {"enabled": settings.scale_control_plane_enabled, "active_jobs": active, "queued_partitions": queued, "claimed_partitions": claimed, "active_storage_objects": storage, "backpressure": backpressure, "backpressure_threshold": settings.scale_queue_backpressure_threshold, "max_active_jobs": settings.scale_max_active_jobs, "max_partitions_per_job": settings.scale_max_partitions_per_job, "storage_classes":["inline","external-reference"], "external_blob_provider_required": False}

def create_job(db: Session, settings, *, job_type, origin_product="platform-core", idempotency_key, partitions, priority=100, parameters=None, metadata=None):
    if not settings.scale_control_plane_enabled: raise ValueError("Scale control plane is disabled.")
    if len(partitions)<1 or len(partitions)>settings.scale_max_partitions_per_job: raise ValueError("Partition count exceeds configured limit.")
    state=readiness(db, settings)
    if state["active_jobs"] >= settings.scale_max_active_jobs: raise ValueError("Backpressure: active-job limit reached.")
    existing=db.scalar(select(ScaleProcessingJob).where(ScaleProcessingJob.job_type==job_type, ScaleProcessingJob.idempotency_key==idempotency_key))
    if existing: return existing
    job=ScaleProcessingJob(job_type=job_type, origin_product=origin_product, idempotency_key=idempotency_key, priority=max(0,min(int(priority),1000)), partition_count=len(partitions), parameters_json=sanitize_queue_parameters(parameters or {}), metadata_json=sanitize_queue_parameters(metadata or {}))
    db.add(job); db.flush()
    seen=set()
    for i, part in enumerate(partitions):
        key=str(part.get("key") or i)
        if key in seen: raise ValueError("Partition keys must be unique within a job.")
        seen.add(key)
        db.add(ScaleProcessingPartition(job_id=job.id, partition_key=key, payload_json=sanitize_queue_parameters(part.get("payload") or {}), max_attempts=max(1,min(int(part.get("max_attempts",3)),20))))
    db.commit(); db.refresh(job)
    emit_event(db,"scale.job.created","scale_processing_job",job.id,{"job_type":job.job_type,"partition_count":job.partition_count},public=False)
    return job

def release_expired(db: Session, at=None):
    at=at or now(); rows=db.scalars(select(ScaleProcessingPartition).where(ScaleProcessingPartition.state=="claimed", ScaleProcessingPartition.lease_expires_at.is_not(None), ScaleProcessingPartition.lease_expires_at<at)).all()
    for r in rows: r.state="queued"; r.lease_owner=None; r.lease_expires_at=None; r.updated_at=at; db.add(r)
    if rows: db.commit()
    return len(rows)

def claim_partition(db: Session, settings, worker_id):
    release_expired(db); at=now()
    if readiness(db, settings)["queued_partitions"] >= settings.scale_queue_backpressure_threshold:
        # Backpressure is visible, but workers must be able to drain the queue.
        pass
    row=db.scalar(select(ScaleProcessingPartition).where(ScaleProcessingPartition.state=="queued", ScaleProcessingPartition.available_at<=at).order_by(ScaleProcessingPartition.created_at).limit(1))
    if not row: return None
    row.state="claimed"; row.attempt_count+=1; row.lease_owner=worker_id; row.lease_expires_at=at+timedelta(seconds=settings.scale_partition_lease_seconds); row.updated_at=at
    job=db.get(ScaleProcessingJob,row.job_id)
    if job and job.state=="queued": job.state="running"; job.started_at=at; db.add(job)
    db.add(row); db.commit(); db.refresh(row); return row

def store_result(db: Session, settings, value, *, subject_type=None, subject_id=None, provenance=None, external_uri=None, content_type="application/json"):
    raw=stable_bytes(value); digest=hashlib.sha256(raw).hexdigest()
    if len(raw)>settings.scale_inline_result_max_bytes and not external_uri: raise ValueError("Result exceeds inline storage limit; external_uri is required.")
    storage_class="external-reference" if external_uri else "inline"
    existing=db.scalar(select(ScaleStorageObject).where(ScaleStorageObject.content_hash==digest, ScaleStorageObject.storage_class==storage_class))
    if existing: return existing
    row=ScaleStorageObject(storage_class=storage_class, content_type=content_type, byte_size=len(raw), content_hash=digest, inline_json={} if external_uri else value, external_uri=external_uri, subject_type=subject_type, subject_id=subject_id, provenance_json=sanitize_queue_parameters(provenance or {}), expires_at=now()+timedelta(hours=settings.scale_completed_retention_hours))
    db.add(row); db.commit(); db.refresh(row); return row

def complete_partition(db: Session, settings, partition_id, *, result=None, external_uri=None, provenance=None):
    row=db.get(ScaleProcessingPartition,partition_id)
    if not row or row.state!="claimed": raise ValueError("Partition must be claimed before completion.")
    obj=store_result(db,settings,result or {},subject_type="scale-processing-partition",subject_id=row.id,provenance=provenance,external_uri=external_uri)
    row.state="completed"; row.storage_object_id=obj.id; row.completed_at=now(); row.lease_owner=None; row.lease_expires_at=None; row.updated_at=now(); db.add(row)
    job=db.get(ScaleProcessingJob,row.job_id); job.completed_partitions+=1
    if job.completed_partitions+job.failed_partitions>=job.partition_count: job.state="completed" if job.failed_partitions==0 else "completed-with-errors"; job.completed_at=now()
    db.add(job); db.commit(); emit_event(db,"scale.partition.completed","scale_processing_partition",row.id,{"job_id":job.id,"storage_object_id":obj.id},public=False); return row,obj

def fail_partition(db: Session, partition_id, error):
    row=db.get(ScaleProcessingPartition,partition_id)
    if not row or row.state!="claimed": raise ValueError("Partition must be claimed before failure.")
    row.last_error=str(error)[:8000]; row.lease_owner=None; row.lease_expires_at=None; row.updated_at=now(); job=db.get(ScaleProcessingJob,row.job_id)
    if row.attempt_count>=row.max_attempts: row.state="failed"; row.completed_at=now(); job.failed_partitions+=1
    else: row.state="queued"; row.available_at=now()+timedelta(seconds=5)
    if job.completed_partitions+job.failed_partitions>=job.partition_count: job.state="completed-with-errors"; job.completed_at=now()
    db.add(row); db.add(job); db.commit(); return row

def compact_expired_storage(db: Session, at=None):
    at=at or now(); rows=db.scalars(select(ScaleStorageObject).where(ScaleStorageObject.retention_state=="active", ScaleStorageObject.expires_at.is_not(None), ScaleStorageObject.expires_at<at)).all()
    for r in rows: r.inline_json={}; r.retention_state="compacted"; db.add(r)
    if rows: db.commit()
    return len(rows)

def job_detail(db: Session, job_id):
    job=db.get(ScaleProcessingJob,job_id)
    if not job: raise ValueError("Processing job not found.")
    parts=db.scalars(select(ScaleProcessingPartition).where(ScaleProcessingPartition.job_id==job_id).order_by(ScaleProcessingPartition.created_at)).all()
    return {"id":job.id,"job_type":job.job_type,"origin_product":job.origin_product,"state":job.state,"priority":job.priority,"partition_count":job.partition_count,"completed_partitions":job.completed_partitions,"failed_partitions":job.failed_partitions,"partitions":[{"id":p.id,"partition_key":p.partition_key,"state":p.state,"attempt_count":p.attempt_count,"storage_object_id":p.storage_object_id,"last_error":p.last_error} for p in parts]}
