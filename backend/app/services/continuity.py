from __future__ import annotations
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse, unquote
import hashlib, os, sqlite3, tempfile, time
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..models import BackupArtifactRecord, DisasterRecoveryObjective, RestoreRehearsalRecord

SECRET_KEYS={"password","secret","token","authorization","api_key","apikey","credential","credentials","access_key","secret_key"}
VALID_ENGINES={"sqlite","postgresql","mysql","other"}
VALID_STORAGE={"filesystem","operator-managed","database-native","snapshot"}
ELIGIBLE_BACKUP_STATES={"verified","attested"}

def _now(): return datetime.now(timezone.utc)
def _aware(value):
    if value is None: return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
def _scrub(value):
    if isinstance(value,dict): return {str(k):("[redacted]" if str(k).lower() in SECRET_KEYS else _scrub(v)) for k,v in value.items()}
    if isinstance(value,list): return [_scrub(v) for v in value]
    return value

def _sha256_file(path:Path):
    h=hashlib.sha256(); size=0
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            size += len(chunk); h.update(chunk)
    return h.hexdigest(),size

def _filesystem_path(row:BackupArtifactRecord, settings) -> Path:
    if row.storage_kind!="filesystem": raise ValueError("Backup is not a filesystem artifact.")
    if not settings.backup_filesystem_verification_enabled: raise ValueError("Filesystem backup verification is disabled.")
    root=(settings.backup_filesystem_root or "").strip()
    if not root: raise ValueError("SC_CORE_BACKUP_FILESYSTEM_ROOT must be configured before Core reads backup files.")
    uri=row.storage_uri
    if uri.startswith("file://"):
        parsed=urlparse(uri)
        raw=unquote(parsed.path)
    else: raw=uri
    candidate=Path(raw).expanduser().resolve(); allowed=Path(root).expanduser().resolve()
    try: candidate.relative_to(allowed)
    except ValueError: raise ValueError("Backup path is outside the configured backup filesystem root.")
    return candidate

def register_backup(db:Session, *, backup_key:str, environment:str="production", database_engine:str="postgresql", storage_kind:str="operator-managed", storage_uri:str, checksum_sha256:str|None=None, size_bytes:int|None=None, backup_started_at:datetime|None=None, backup_completed_at:datetime|None=None, metadata:dict|None=None):
    backup_key=backup_key.strip()
    if not backup_key: raise ValueError("backup_key is required.")
    if database_engine not in VALID_ENGINES: raise ValueError("Unsupported database_engine.")
    if storage_kind not in VALID_STORAGE: raise ValueError("Unsupported storage_kind.")
    if checksum_sha256 and (len(checksum_sha256)!=64 or any(c not in '0123456789abcdefABCDEF' for c in checksum_sha256)): raise ValueError("checksum_sha256 must be a 64-character hexadecimal SHA-256 digest.")
    existing=db.scalar(select(BackupArtifactRecord).where(BackupArtifactRecord.backup_key==backup_key))
    if existing: return existing
    row=BackupArtifactRecord(backup_key=backup_key,environment=environment[:40],database_engine=database_engine,storage_kind=storage_kind,storage_uri=storage_uri[:2000],checksum_sha256=checksum_sha256.lower() if checksum_sha256 else None,size_bytes=size_bytes,backup_started_at=backup_started_at,backup_completed_at=backup_completed_at or _now(),metadata_json=_scrub(metadata or {}))
    db.add(row); db.commit(); db.refresh(row); return row

def verify_backup(db:Session,row:BackupArtifactRecord,settings):
    details={"core_file_read":False,"storage_kind":row.storage_kind,"credentials_persisted":False}
    if row.storage_kind!="filesystem":
        raise ValueError("Core can independently checksum only filesystem backups. Use an external verification attestation for operator-managed backups.")
    try:
        path=_filesystem_path(row,settings)
        if not path.is_file():
            row.verification_state="missing"; details["reason"]="backup_file_missing"
        else:
            digest,size=_sha256_file(path); details.update({"core_file_read":True,"observed_sha256":digest,"observed_size_bytes":size})
            if row.checksum_sha256 and digest!=row.checksum_sha256.lower(): row.verification_state="mismatch"
            else:
                row.verification_state="verified"; row.checksum_sha256=row.checksum_sha256 or digest; row.size_bytes=size; row.verified_at=_now()
    except ValueError:
        raise
    row.verification_details_json=_scrub(details); db.add(row); db.commit(); db.refresh(row); return row

def attest_backup_verification(db:Session,row:BackupArtifactRecord,*, actor:str, observed_checksum_sha256:str, observed_size_bytes:int|None=None, evidence:dict|None=None):
    if len(observed_checksum_sha256)!=64 or any(c not in '0123456789abcdefABCDEF' for c in observed_checksum_sha256): raise ValueError("observed_checksum_sha256 must be a SHA-256 digest.")
    observed=observed_checksum_sha256.lower(); expected=(row.checksum_sha256 or observed).lower()
    if observed!=expected:
        row.verification_state="mismatch"; row.verification_details_json={"external_attestation":True,"actor":actor[:255],"checksum_match":False,"credentials_persisted":False}
    else:
        row.checksum_sha256=expected; row.size_bytes=row.size_bytes or observed_size_bytes; row.verification_state="attested"; row.verified_at=_now(); row.verification_details_json=_scrub({"external_attestation":True,"actor":actor[:255],"checksum_match":True,"evidence":evidence or {},"credentials_persisted":False})
    db.add(row); db.commit(); db.refresh(row); return row

def get_or_create_objective(db:Session,settings,environment="production"):
    row=db.scalar(select(DisasterRecoveryObjective).where(DisasterRecoveryObjective.environment==environment))
    if row: return row
    row=DisasterRecoveryObjective(environment=environment,rpo_minutes=settings.dr_default_rpo_minutes,rto_minutes=settings.dr_default_rto_minutes,max_backup_age_minutes=settings.dr_max_backup_age_minutes,restore_rehearsal_max_age_hours=settings.dr_restore_rehearsal_max_age_hours,metadata_json={"seed":"platform-core-v2.20.0"})
    db.add(row); db.commit(); db.refresh(row); return row

def upsert_objective(db:Session,settings,*,environment:str,rpo_minutes:int,rto_minutes:int,max_backup_age_minutes:int,restore_rehearsal_max_age_hours:int,require_verified_backup:bool=True,require_restore_rehearsal:bool=True,metadata:dict|None=None):
    if min(rpo_minutes,rto_minutes,max_backup_age_minutes,restore_rehearsal_max_age_hours)<=0: raise ValueError("Recovery objective durations must be positive.")
    row=get_or_create_objective(db,settings,environment)
    row.rpo_minutes=rpo_minutes; row.rto_minutes=rto_minutes; row.max_backup_age_minutes=max_backup_age_minutes; row.restore_rehearsal_max_age_hours=restore_rehearsal_max_age_hours; row.require_verified_backup=require_verified_backup; row.require_restore_rehearsal=require_restore_rehearsal; row.metadata_json=_scrub(metadata or {})
    db.add(row); db.commit(); db.refresh(row); return row

def _schema_head_sqlite(con):
    try:
        row=con.execute("SELECT MAX(version) FROM schema_migrations").fetchone(); return row[0] if row and row[0] else None
    except sqlite3.Error: return None

def run_sqlite_restore_rehearsal(db:Session,row:BackupArtifactRecord,settings,*,environment:str|None=None,actor:str="operator"):
    if row.database_engine!="sqlite": raise ValueError("Core-isolated restore rehearsal currently supports SQLite backup artifacts only.")
    if row.verification_state!="verified": raise ValueError("SQLite restore rehearsal requires a Core-verified backup checksum.")
    path=_filesystem_path(row,settings); started=_now(); t0=time.perf_counter()
    fd,tmp=tempfile.mkstemp(prefix='sc-core-restore-rehearsal-',suffix='.db'); os.close(fd)
    checks={}; schema_head=None; state="failed"
    try:
        src=sqlite3.connect(f"file:{path}?mode=ro",uri=True); dst=sqlite3.connect(tmp)
        try:
            src_integrity=src.execute("PRAGMA integrity_check").fetchone()[0]; src.backup(dst); dst.commit(); dst_integrity=dst.execute("PRAGMA integrity_check").fetchone()[0]; schema_head=_schema_head_sqlite(dst)
            checks={"source_integrity":src_integrity,"restored_integrity":dst_integrity,"isolated_copy_created":True,"source_opened_read_only":True,"schema_migration_head":schema_head}
            state="passed" if src_integrity=="ok" and dst_integrity=="ok" else "failed"
        finally: src.close(); dst.close()
    finally:
        try: os.remove(tmp)
        except OSError: pass
    duration=max(1,int((time.perf_counter()-t0)*1000))
    rehearsal=RestoreRehearsalRecord(backup_id=row.id,environment=(environment or row.environment)[:40],state=state,execution_mode="core-isolated-sqlite",operator_actor=actor[:255],schema_head=schema_head,duration_ms=duration,integrity_checks_json=checks,evidence_json={"backup_checksum":row.checksum_sha256,"temporary_restore_removed":True},isolated_target=True,source_database_mutated=False,automatic_restore=False,started_at=started,completed_at=_now())
    db.add(rehearsal); db.commit(); db.refresh(rehearsal); return rehearsal

def record_external_restore_rehearsal(db:Session,row:BackupArtifactRecord,*,state:str,operator_actor:str,schema_head:str|None,duration_ms:int,integrity_checks:dict|None=None,evidence:dict|None=None,environment:str|None=None):
    if state not in {"passed","failed"}: raise ValueError("External restore rehearsal state must be passed or failed.")
    if duration_ms<0: raise ValueError("duration_ms must be non-negative.")
    rehearsal=RestoreRehearsalRecord(backup_id=row.id,environment=(environment or row.environment)[:40],state=state,execution_mode="external-operator",operator_actor=operator_actor[:255],schema_head=schema_head,duration_ms=duration_ms,integrity_checks_json=_scrub(integrity_checks or {}),evidence_json=_scrub(evidence or {}),isolated_target=True,source_database_mutated=False,automatic_restore=False,started_at=_now()-timedelta(milliseconds=duration_ms),completed_at=_now())
    db.add(rehearsal); db.commit(); db.refresh(rehearsal); return rehearsal

def list_backups(db:Session,environment:str|None=None,limit=100):
    q=select(BackupArtifactRecord)
    if environment: q=q.where(BackupArtifactRecord.environment==environment)
    return db.scalars(q.order_by(BackupArtifactRecord.backup_completed_at.desc()).limit(limit)).all()

def list_rehearsals(db:Session,environment:str|None=None,limit=100):
    q=select(RestoreRehearsalRecord)
    if environment: q=q.where(RestoreRehearsalRecord.environment==environment)
    return db.scalars(q.order_by(RestoreRehearsalRecord.completed_at.desc()).limit(limit)).all()

def continuity_status(db:Session,settings,environment="production"):
    objective=get_or_create_objective(db,settings,environment); now=_now()
    eligible=db.scalars(select(BackupArtifactRecord).where(BackupArtifactRecord.environment==environment,BackupArtifactRecord.verification_state.in_(ELIGIBLE_BACKUP_STATES)).order_by(BackupArtifactRecord.backup_completed_at.desc())).all()
    backup=eligible[0] if eligible else None
    age_minutes=None if not backup else max(0.0,(now-_aware(backup.backup_completed_at)).total_seconds()/60)
    backup_recent=bool(backup and age_minutes<=objective.max_backup_age_minutes)
    rpo_met=bool(backup and age_minutes<=objective.rpo_minutes)
    rehearsal=db.scalar(select(RestoreRehearsalRecord).where(RestoreRehearsalRecord.environment==environment,RestoreRehearsalRecord.state=="passed").order_by(RestoreRehearsalRecord.completed_at.desc()).limit(1))
    rehearsal_age_hours=None if not rehearsal or not rehearsal.completed_at else max(0.0,(now-_aware(rehearsal.completed_at)).total_seconds()/3600)
    rehearsal_recent=bool(rehearsal and rehearsal_age_hours<=objective.restore_rehearsal_max_age_hours)
    rto_met=bool(rehearsal and rehearsal.duration_ms is not None and rehearsal.duration_ms <= objective.rto_minutes*60*1000)
    blockers=[]
    if objective.require_verified_backup and not backup_recent: blockers.append("recent_verified_backup")
    if objective.require_restore_rehearsal and not rehearsal_recent: blockers.append("recent_restore_rehearsal")
    if backup and not rpo_met: blockers.append("rpo")
    if rehearsal and not rto_met: blockers.append("rto")
    return {"enabled":settings.continuity_disaster_recovery_enabled,"environment":environment,"state":"ready" if not blockers else "attention","rpo_minutes":objective.rpo_minutes,"rto_minutes":objective.rto_minutes,"max_backup_age_minutes":objective.max_backup_age_minutes,"restore_rehearsal_max_age_hours":objective.restore_rehearsal_max_age_hours,"eligible_backup_present":bool(backup),"latest_backup_age_minutes":round(age_minutes,2) if age_minutes is not None else None,"latest_backup_verification_state":backup.verification_state if backup else None,"backup_recent":backup_recent,"rpo_met":rpo_met,"passed_restore_rehearsal_present":bool(rehearsal),"latest_restore_rehearsal_age_hours":round(rehearsal_age_hours,2) if rehearsal_age_hours is not None else None,"latest_restore_duration_ms":rehearsal.duration_ms if rehearsal else None,"restore_rehearsal_recent":rehearsal_recent,"rto_met":rto_met,"blockers":blockers,"database_backup_embedded":False,"external_backup_required_for_full_restore":True,"automatic_database_restore_enabled":False,"arbitrary_restore_commands_enabled":False,"filesystem_backup_root_configured":bool(settings.backup_filesystem_root),"evidence_semantics_unchanged":True}

def certification_snapshot(db:Session,settings,environment="production"):
    s=continuity_status(db,settings,environment)
    return {"environment":environment,"recent_verified_backup":bool(s["backup_recent"]),"rpo_met":bool(s["rpo_met"]),"recent_restore_rehearsal":bool(s["restore_rehearsal_recent"]),"rto_met":bool(s["rto_met"]),"database_backup_embedded":False,"automatic_database_restore_enabled":False,"state":s["state"]}

def public_status(db:Session,settings,environment="production"):
    s=continuity_status(db,settings,environment)
    return {k:s[k] for k in ["enabled","environment","state","rpo_minutes","rto_minutes","eligible_backup_present","backup_recent","rpo_met","passed_restore_rehearsal_present","restore_rehearsal_recent","rto_met","database_backup_embedded","external_backup_required_for_full_restore","automatic_database_restore_enabled"]} | {"backup_locations_publicly_exposed":False,"backup_identifiers_publicly_exposed":False,"restore_evidence_publicly_exposed":False}
