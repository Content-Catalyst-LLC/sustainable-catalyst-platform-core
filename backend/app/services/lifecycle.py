
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..models import DataLifecyclePolicyRecord, PreservationArchiveRecord, LifecycleHoldRecord, LifecycleActionRecord

SECRET_KEYS={"password","secret","token","authorization","api_key","apikey","credential","credentials","access_key","secret_key"}
RETENTION_CLASSES={"transient","operational","institutional","permanent"}
HOLD_TYPES={"policy","legal","investigation","preservation"}

def _now(): return datetime.now(timezone.utc)
def _scrub(value):
    if isinstance(value,dict): return {str(k):("[redacted]" if str(k).lower() in SECRET_KEYS else _scrub(v)) for k,v in value.items()}
    if isinstance(value,list): return [_scrub(v) for v in value]
    return value

def _canonical(value): return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str).encode()
def _sha(value): return hashlib.sha256(_canonical(value)).hexdigest()

def create_policy(db:Session,settings,*,policy_key:str,subject_type:str="evidence-record",retention_class:str="institutional",minimum_retention_days:int|None=None,archive_after_days:int|None=None,tombstone_after_days:int|None=None,preserve_provenance:bool=True,hold_overrides_lifecycle:bool=True,metadata:dict|None=None):
    policy_key=policy_key.strip(); subject_type=subject_type.strip()
    if not policy_key or not subject_type: raise ValueError("policy_key and subject_type are required.")
    if retention_class not in RETENTION_CLASSES: raise ValueError("Unsupported retention_class.")
    existing=db.scalar(select(DataLifecyclePolicyRecord).where(DataLifecyclePolicyRecord.policy_key==policy_key))
    if existing: return existing
    minimum=settings.data_lifecycle_default_min_retention_days if minimum_retention_days is None else max(1,int(minimum_retention_days))
    archive_after=settings.data_lifecycle_default_archive_after_days if archive_after_days is None else max(0,int(archive_after_days))
    if tombstone_after_days is not None and int(tombstone_after_days)<minimum: raise ValueError("tombstone_after_days cannot be earlier than minimum_retention_days.")
    row=DataLifecyclePolicyRecord(policy_key=policy_key[:255],subject_type=subject_type[:120],retention_class=retention_class,minimum_retention_days=minimum,archive_after_days=archive_after,tombstone_after_days=tombstone_after_days,preserve_provenance=bool(preserve_provenance),hold_overrides_lifecycle=bool(hold_overrides_lifecycle),hard_delete_allowed=False,metadata_json=_scrub(metadata or {}))
    db.add(row); db.commit(); db.refresh(row); return row

def list_policies(db:Session): return db.scalars(select(DataLifecyclePolicyRecord).order_by(DataLifecyclePolicyRecord.policy_key)).all()

def place_hold(db:Session,*,hold_key:str,subject_type:str,subject_id:str,hold_type:str="policy",reason:str="",actor:str="operator",metadata:dict|None=None):
    if hold_type not in HOLD_TYPES: raise ValueError("Unsupported hold_type.")
    existing=db.scalar(select(LifecycleHoldRecord).where(LifecycleHoldRecord.hold_key==hold_key))
    if existing: return existing
    row=LifecycleHoldRecord(hold_key=hold_key[:255],subject_type=subject_type[:120],subject_id=subject_id[:255],hold_type=hold_type,reason=reason,actor=actor[:255],metadata_json=_scrub(metadata or {}))
    db.add(row); db.commit(); db.refresh(row); return row

def release_hold(db:Session,row:LifecycleHoldRecord,*,actor:str="operator"):
    row.state="released"; row.released_at=_now(); row.metadata_json={**(row.metadata_json or {}),"released_by":actor[:255]}; db.add(row); db.commit(); db.refresh(row); return row

def active_hold(db:Session,subject_type:str,subject_id:str):
    return db.scalar(select(LifecycleHoldRecord).where(LifecycleHoldRecord.subject_type==subject_type,LifecycleHoldRecord.subject_id==subject_id,LifecycleHoldRecord.state=="active").limit(1))

def create_archive(db:Session,*,archive_key:str,subject_type:str,subject_id:str,snapshot:dict,storage_kind:str="core-manifest",storage_uri:str|None=None,metadata:dict|None=None):
    existing=db.scalar(select(PreservationArchiveRecord).where(PreservationArchiveRecord.archive_key==archive_key))
    if existing: return existing
    clean=_scrub(snapshot or {}); meta=_scrub(metadata or {}); content_sha=_sha(clean)
    manifest={"archive_key":archive_key,"subject_type":subject_type,"subject_id":subject_id,"storage_kind":storage_kind,"storage_uri":storage_uri,"content_sha256":content_sha,"provenance_preserved":True}
    row=PreservationArchiveRecord(archive_key=archive_key[:255],subject_type=subject_type[:120],subject_id=subject_id[:255],storage_kind=storage_kind[:40],storage_uri=storage_uri,snapshot_json=clean,content_sha256=content_sha,manifest_sha256=_sha(manifest),verification_state="verified",provenance_preserved=True,metadata_json=meta,verified_at=_now())
    db.add(row); db.commit(); db.refresh(row)
    db.add(LifecycleActionRecord(subject_type=row.subject_type,subject_id=row.subject_id,action_type="archive",state="recorded",archive_id=row.id,actor="operator",automatic_execution=False,source_record_deleted=False,provenance_preserved=True,evidence_json={"content_sha256":row.content_sha256,"manifest_sha256":row.manifest_sha256})); db.commit(); return row

def verify_archive(db:Session,row:PreservationArchiveRecord):
    content_sha=_sha(row.snapshot_json or {}); manifest={"archive_key":row.archive_key,"subject_type":row.subject_type,"subject_id":row.subject_id,"storage_kind":row.storage_kind,"storage_uri":row.storage_uri,"content_sha256":row.content_sha256,"provenance_preserved":True}; ok=content_sha==row.content_sha256 and _sha(manifest)==row.manifest_sha256
    row.verification_state="verified" if ok else "mismatch"; row.verified_at=_now(); db.add(row); db.commit(); db.refresh(row); return {"valid":ok,"content_sha256":content_sha,"stored_content_sha256":row.content_sha256,"manifest_sha256":row.manifest_sha256,"state":row.verification_state}

def request_tombstone(db:Session,*,subject_type:str,subject_id:str,actor:str="operator",reason:str="retention-policy"):
    hold=active_hold(db,subject_type,subject_id)
    state="blocked-by-hold" if hold else "tombstoned"
    row=LifecycleActionRecord(subject_type=subject_type[:120],subject_id=subject_id[:255],action_type="tombstone",state=state,actor=actor[:255],automatic_execution=False,source_record_deleted=False,provenance_preserved=True,evidence_json={"reason":reason,"active_hold_id":hold.id if hold else None,"hard_delete_enabled":False})
    db.add(row); db.commit(); db.refresh(row); return row

def restore_archive(db:Session,row:PreservationArchiveRecord,*,actor:str="operator",reason:str="operator-request"):
    check=verify_archive(db,row)
    if not check["valid"]: raise ValueError("Archive integrity verification failed.")
    row.state="restored"; row.restored_at=_now(); db.add(row)
    action=LifecycleActionRecord(subject_type=row.subject_type,subject_id=row.subject_id,action_type="restore-reference",state="recorded",archive_id=row.id,actor=actor[:255],automatic_execution=False,source_record_deleted=False,provenance_preserved=True,evidence_json={"reason":reason,"archive_integrity_verified":True,"automatic_source_overwrite":False})
    db.add(action); db.commit(); db.refresh(action); return action

def readiness(db:Session,settings):
    policies=db.scalar(select(func.count()).select_from(DataLifecyclePolicyRecord)) or 0; archives=db.scalar(select(func.count()).select_from(PreservationArchiveRecord)) or 0; mismatches=db.scalar(select(func.count()).select_from(PreservationArchiveRecord).where(PreservationArchiveRecord.verification_state=="mismatch")) or 0; holds=db.scalar(select(func.count()).select_from(LifecycleHoldRecord).where(LifecycleHoldRecord.state=="active")) or 0
    state="disabled" if not settings.data_lifecycle_preservation_enabled else ("attention" if mismatches else "ready")
    return {"enabled":settings.data_lifecycle_preservation_enabled,"state":state,"policies":policies,"archives":archives,"integrity_mismatches":mismatches,"active_holds":holds,"hard_delete_enabled":False,"automatic_lifecycle_deletion":False,"holds_override_lifecycle":True,"provenance_preservation_required":True,"restoration_is_reference_first":True,"evidence_semantics_unchanged":True}

def public_status(db:Session,settings):
    s=readiness(db,settings); return {"state":s["state"],"policies":s["policies"],"archives":s["archives"],"integrity_mismatches":s["integrity_mismatches"],"active_holds":s["active_holds"],"hard_delete_enabled":False,"archive_contents_publicly_exposed":False,"hold_reasons_publicly_exposed":False,"evidence_semantics_unchanged":True}

def certification_snapshot(db:Session,settings):
    s=readiness(db,settings); return {"state":s["state"],"preservation_ready":s["state"]=="ready","integrity_mismatches":s["integrity_mismatches"],"hard_delete_enabled":False}
