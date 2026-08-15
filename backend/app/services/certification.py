from __future__ import annotations
from datetime import datetime, timezone, timedelta
import hashlib, json
from sqlalchemy import inspect, select, text, func
from sqlalchemy.orm import Session
from ..migrations import MIGRATIONS, migration_status
from ..models import ProductionCertificationRun, RecoveryReadinessCheckpoint
from .governance import verify_audit_chain

SCHEMA_HEAD=MIGRATIONS[-1][0]

def _now(): return datetime.now(timezone.utc)
def _stable(value): return json.dumps(value, sort_keys=True, separators=(",",":"), default=str).encode()
def _hash(value): return hashlib.sha256(_stable(value)).hexdigest()

def readiness(db: Session, settings) -> dict:
    return {"enabled":settings.production_certification_enabled,"schema_head":SCHEMA_HEAD,"recovery_checkpoint_enabled":settings.recovery_checkpoint_enabled,"zero_pending_migrations_required":settings.certification_require_zero_pending_migrations,"valid_audit_chain_required":settings.certification_require_valid_audit_chain,"gateway_release_ready_required":settings.certification_require_gateway_release_ready,"external_provider_health_release_blocking":False,"database_backup_embedded":False}

def migration_assurance(database) -> dict:
    st=migration_status(database)
    applied=list(st['applied']); pending=list(st['pending'])
    return {"schema_head":max(applied) if applied else None,"expected_head":SCHEMA_HEAD,"applied":applied,"pending":pending,"zero_pending":not pending,"head_matches":bool(applied and max(applied)==SCHEMA_HEAD),"forward_only_release_line":True}

def _table_inventory(session: Session):
    bind=session.get_bind(); names=sorted(inspect(bind).get_table_names())
    counts={}
    critical={"schema_migrations","entities","evidence_records","live_data_sources","operational_facilities","humanitarian_conditions","cross_product_exchange_packages","governance_audit_events","scale_processing_jobs","production_certification_runs","recovery_readiness_checkpoints","observability_metric_samples","service_level_objectives","production_deployment_markers","operations_incidents","operations_incident_events","change_control_records","rollback_coordination_records","backup_artifact_records","disaster_recovery_objectives","restore_rehearsal_records","region_service_status_records","failover_group_records","failover_assessment_records"}
    for name in names:
        if name in critical:
            try: counts[name]=int(session.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar_one())
            except Exception: counts[name]=None
    return names, counts

def create_recovery_checkpoint(session: Session, database, settings):
    if not settings.recovery_checkpoint_enabled: raise ValueError("Recovery checkpoints are disabled.")
    mig=migration_assurance(database); tables,counts=_table_inventory(session)
    contract={"checkpoint_kind":"metadata-and-integrity","database_backup_embedded":False,"external_backup_required_for_full_restore":True,"restore_target":"same-or-newer-compatible-core","destructive_down_migration_required":False,"source_database_mutated":False}
    payload={"release":settings.version,"schema_head":mig['schema_head'],"migration_inventory":mig['applied'],"table_inventory":tables,"row_counts":counts,"recovery_contract":contract}
    row=RecoveryReadinessCheckpoint(release=settings.version,schema_head=mig['schema_head'] or "",migration_inventory_json=mig['applied'],table_inventory_json=tables,row_counts_json=counts,recovery_contract_json=contract,checkpoint_hash=_hash(payload),expires_at=_now()+timedelta(hours=settings.recovery_checkpoint_retention_hours))
    session.add(row); session.commit(); session.refresh(row); return row

def verify_recovery_checkpoint(row: RecoveryReadinessCheckpoint) -> dict:
    payload={"release":row.release,"schema_head":row.schema_head,"migration_inventory":row.migration_inventory_json,"table_inventory":row.table_inventory_json,"row_counts":row.row_counts_json,"recovery_contract":row.recovery_contract_json}
    calculated=_hash(payload)
    return {"valid":calculated==row.checkpoint_hash,"checkpoint_id":row.id,"stored_hash":row.checkpoint_hash,"calculated_hash":calculated,"database_backup_embedded":False}

def run_certification(session: Session, database, settings, gateway_snapshot: dict | None=None):
    mig=migration_assurance(database)
    audit=verify_audit_chain(session)
    gateway=gateway_snapshot or {"release_ready":True,"required_blockers":[]}
    try:
        session.execute(text("SELECT 1")).scalar_one(); db_roundtrip=True
    except Exception: db_roundtrip=False
    checkpoint=create_recovery_checkpoint(session,database,settings) if settings.recovery_checkpoint_enabled else None
    checkpoint_check=verify_recovery_checkpoint(checkpoint) if checkpoint else {"valid":False}
    from .continuity import certification_snapshot
    continuity=certification_snapshot(session,settings) if settings.continuity_disaster_recovery_enabled else {"state":"disabled","recent_verified_backup":False,"recent_restore_rehearsal":False,"rpo_met":False,"rto_met":False,"database_backup_embedded":False,"automatic_database_restore_enabled":False}
    from .resilience import certification_snapshot as resilience_certification_snapshot
    resilience=resilience_certification_snapshot(session,settings) if settings.multi_region_resilience_enabled else {"state":"disabled","multi_region_ready":False,"automatic_failover_enabled":False,"infrastructure_actuation_by_core":False}
    from .lifecycle import certification_snapshot as lifecycle_certification_snapshot
    preservation=lifecycle_certification_snapshot(session,settings) if settings.data_lifecycle_preservation_enabled else {"state":"disabled","preservation_ready":False,"integrity_mismatches":0,"hard_delete_enabled":False}
    checks={"database_roundtrip":db_roundtrip,"migration_head_matches":mig['head_matches'],"zero_pending_migrations":mig['zero_pending'],"governance_audit_chain_valid":bool(audit.get('valid')),"recovery_checkpoint_valid":bool(checkpoint_check.get('valid')) if settings.recovery_checkpoint_enabled else True,"gateway_release_ready":bool(gateway.get('release_ready',False)),"recent_verified_backup":bool(continuity.get('recent_verified_backup')),"recent_restore_rehearsal":bool(continuity.get('recent_restore_rehearsal')),"rpo_met":bool(continuity.get('rpo_met')),"rto_met":bool(continuity.get('rto_met')),"multi_region_ready":bool(resilience.get('multi_region_ready')),"preservation_ready":bool(preservation.get('preservation_ready')),"external_provider_health_release_blocking":False}
    blockers=[]
    if not settings.production_certification_enabled: blockers.append("production_certification_disabled")
    if not db_roundtrip: blockers.append("database_roundtrip")
    if not mig['head_matches']: blockers.append("migration_head")
    if settings.certification_require_zero_pending_migrations and not mig['zero_pending']: blockers.append("pending_migrations")
    if settings.certification_require_valid_audit_chain and not audit.get('valid'): blockers.append("governance_audit_chain")
    if settings.recovery_checkpoint_enabled and not checkpoint_check.get('valid'): blockers.append("recovery_checkpoint_integrity")
    if settings.certification_require_gateway_release_ready and not gateway.get('release_ready',False): blockers.append("required_first_party_services")
    if settings.certification_require_recent_verified_backup and not continuity.get('recent_verified_backup'): blockers.append("recent_verified_backup")
    if settings.certification_require_recent_restore_rehearsal and not continuity.get('recent_restore_rehearsal'): blockers.append("recent_restore_rehearsal")
    if settings.certification_require_multi_region_ready and not resilience.get('multi_region_ready'): blockers.append("multi_region_resilience")
    if settings.certification_require_preservation_ready and not preservation.get('preservation_ready'): blockers.append("data_lifecycle_preservation")
    state="certified" if not blockers else "blocked"
    recovery={"checkpoint_id":checkpoint.id if checkpoint else None,"checkpoint_valid":checkpoint_check.get('valid',False),"database_backup_embedded":False,"external_backup_required_for_full_restore":True,"disaster_recovery":continuity,"multi_region_resilience":resilience,"data_lifecycle_preservation":preservation}
    core={"release":settings.version,"state":state,"migration_head":mig['schema_head'],"pending_migrations":mig['pending'],"checks":checks,"blockers":blockers,"gateway":{"release_ready":gateway.get('release_ready',False),"required_blockers":gateway.get('required_blockers',[])},"recovery":recovery}
    row=ProductionCertificationRun(release=settings.version,state=state,migration_head=mig['schema_head'] or "",pending_migrations_json=mig['pending'],checks_json=checks,blockers_json=blockers,gateway_json=core['gateway'],recovery_json=recovery,certification_hash=_hash(core),completed_at=_now())
    session.add(row); session.commit(); session.refresh(row); return row,core

def list_runs(session: Session, limit=100): return session.scalars(select(ProductionCertificationRun).order_by(ProductionCertificationRun.created_at.desc()).limit(limit)).all()
def list_checkpoints(session: Session, limit=100): return session.scalars(select(RecoveryReadinessCheckpoint).order_by(RecoveryReadinessCheckpoint.created_at.desc()).limit(limit)).all()
