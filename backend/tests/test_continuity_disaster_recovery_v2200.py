import hashlib, os, sqlite3, tempfile
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.config import Settings
from app.database import Database, Base
from app.main import create_app
from app.migrations import run_migrations, migration_status
from app.models import BackupArtifactRecord
from app.services import continuity, certification

def settings_for(dburl,root=''):
    return Settings(database_url=dburl,backup_filesystem_root=root)

def make_backup(root):
    p=os.path.join(root,'backup.db'); con=sqlite3.connect(p); con.execute('create table schema_migrations(version text primary key, description text, applied_at text)'); con.execute("insert into schema_migrations values('0023','test',datetime('now'))"); con.execute('create table sample(id integer primary key, value text)'); con.execute("insert into sample(value) values('ok')"); con.commit(); con.close(); data=open(p,'rb').read(); return p,hashlib.sha256(data).hexdigest(),len(data)

def test_migration_and_readiness_surface():
    with tempfile.TemporaryDirectory() as td:
        p=os.path.join(td,'core.db'); app=create_app(settings_for('sqlite:///'+p,td)); c=TestClient(app); b=c.get('/v1/continuity/readiness').json(); assert b['release']=='2.21.0' and b['migration_0023_applied'] is True and b['database_backup_embedded'] is False and b['automatic_database_restore_enabled'] is False

def test_backup_registration_idempotent_and_secret_scrubbed():
    with tempfile.TemporaryDirectory() as td:
        d=Database('sqlite:///'+os.path.join(td,'core.db')); run_migrations(d)
        with d.session_factory() as db:
            a=continuity.register_backup(db,backup_key='b1',storage_uri='s3://example/backup',metadata={'token':'secret','nested':{'password':'x'}}); b=continuity.register_backup(db,backup_key='b1',storage_uri='other'); assert a.id==b.id and a.metadata_json['token']=='[redacted]' and a.metadata_json['nested']['password']=='[redacted]'

def test_core_filesystem_checksum_verification_and_path_boundary():
    with tempfile.TemporaryDirectory() as td:
        path,digest,size=make_backup(td); d=Database('sqlite:///'+os.path.join(td,'core.db')); run_migrations(d); s=settings_for('sqlite:///'+os.path.join(td,'core.db'),td)
        with d.session_factory() as db:
            row=continuity.register_backup(db,backup_key='b2',database_engine='sqlite',storage_kind='filesystem',storage_uri=path,checksum_sha256=digest,size_bytes=size); continuity.verify_backup(db,row,s); assert row.verification_state=='verified' and row.verified_at
            other=tempfile.NamedTemporaryFile(delete=False); other.write(b'x'); other.close(); bad=continuity.register_backup(db,backup_key='outside',database_engine='sqlite',storage_kind='filesystem',storage_uri=other.name)
            try: continuity.verify_backup(db,bad,s); assert False
            except ValueError as e: assert 'outside' in str(e)
            os.remove(other.name)

def test_checksum_mismatch_is_not_eligible():
    with tempfile.TemporaryDirectory() as td:
        path,_,_=make_backup(td); d=Database('sqlite:///'+os.path.join(td,'core.db')); run_migrations(d); s=settings_for('sqlite:///'+os.path.join(td,'core.db'),td)
        with d.session_factory() as db:
            row=continuity.register_backup(db,backup_key='mismatch',database_engine='sqlite',storage_kind='filesystem',storage_uri=path,checksum_sha256='0'*64); continuity.verify_backup(db,row,s); assert row.verification_state=='mismatch'; st=continuity.continuity_status(db,s); assert st['eligible_backup_present'] is False

def test_external_attestation_preserves_operator_boundary():
    with tempfile.TemporaryDirectory() as td:
        d=Database('sqlite:///'+os.path.join(td,'core.db')); run_migrations(d); s=settings_for('sqlite:///'+os.path.join(td,'core.db'))
        with d.session_factory() as db:
            row=continuity.register_backup(db,backup_key='pg1',database_engine='postgresql',storage_kind='operator-managed',storage_uri='operator://backup/pg1',checksum_sha256='a'*64); continuity.attest_backup_verification(db,row,actor='ops',observed_checksum_sha256='a'*64,evidence={'token':'nope'}); assert row.verification_state=='attested' and row.verification_details_json['evidence']['token']=='[redacted]'
            drill=continuity.record_external_restore_rehearsal(db,row,state='passed',operator_actor='ops',schema_head='0023',duration_ms=2000,integrity_checks={'row_counts':'match'},evidence={'credential':'x'}); assert drill.execution_mode=='external-operator' and drill.automatic_restore is False and drill.source_database_mutated is False and drill.evidence_json['credential']=='[redacted]'

def test_actual_sqlite_restore_rehearsal_is_isolated_and_non_destructive():
    with tempfile.TemporaryDirectory() as td:
        path,digest,size=make_backup(td); before=open(path,'rb').read(); d=Database('sqlite:///'+os.path.join(td,'core.db')); run_migrations(d); s=settings_for('sqlite:///'+os.path.join(td,'core.db'),td)
        with d.session_factory() as db:
            row=continuity.register_backup(db,backup_key='sqlite-drill',database_engine='sqlite',storage_kind='filesystem',storage_uri=path,checksum_sha256=digest,size_bytes=size); continuity.verify_backup(db,row,s); drill=continuity.run_sqlite_restore_rehearsal(db,row,s); assert drill.state=='passed' and drill.execution_mode=='core-isolated-sqlite' and drill.schema_head=='0023' and drill.isolated_target is True and drill.source_database_mutated is False and drill.automatic_restore is False
        assert open(path,'rb').read()==before

def test_rpo_rto_and_staleness_evaluation():
    with tempfile.TemporaryDirectory() as td:
        d=Database('sqlite:///'+os.path.join(td,'core.db')); run_migrations(d); s=settings_for('sqlite:///'+os.path.join(td,'core.db'))
        with d.session_factory() as db:
            row=continuity.register_backup(db,backup_key='old',storage_uri='operator://old',checksum_sha256='b'*64,backup_completed_at=datetime.now(timezone.utc)-timedelta(days=3)); continuity.attest_backup_verification(db,row,actor='ops',observed_checksum_sha256='b'*64); continuity.record_external_restore_rehearsal(db,row,state='passed',operator_actor='ops',schema_head='0023',duration_ms=60_000); st=continuity.continuity_status(db,s); assert st['backup_recent'] is False and st['rpo_met'] is False and 'recent_verified_backup' in st['blockers'] and st['rto_met'] is True

def test_objective_upsert_changes_recovery_targets():
    with tempfile.TemporaryDirectory() as td:
        d=Database('sqlite:///'+os.path.join(td,'core.db')); run_migrations(d); s=settings_for('sqlite:///'+os.path.join(td,'core.db'))
        with d.session_factory() as db:
            obj=continuity.upsert_objective(db,s,environment='production',rpo_minutes=30,rto_minutes=15,max_backup_age_minutes=45,restore_rehearsal_max_age_hours=24); assert obj.rpo_minutes==30 and obj.rto_minutes==15 and obj.max_backup_age_minutes==45

def test_certification_gates_are_opt_in_and_can_block():
    with tempfile.TemporaryDirectory() as td:
        d=Database('sqlite:///'+os.path.join(td,'core.db')); run_migrations(d)
        with d.session_factory() as db:
            s=Settings(database_url='sqlite:///'+os.path.join(td,'core.db')); row,detail=certification.run_certification(db,d,s,{'release_ready':True,'required_blockers':[]}); assert detail['state']=='certified' and 'recent_verified_backup' not in detail['blockers']
        with d.session_factory() as db:
            s=Settings(database_url='sqlite:///'+os.path.join(td,'core.db'),certification_require_recent_verified_backup=True); row,detail=certification.run_certification(db,d,s,{'release_ready':True,'required_blockers':[]}); assert detail['state']=='blocked' and 'recent_verified_backup' in detail['blockers']

def test_public_status_is_aggregate_only():
    with tempfile.TemporaryDirectory() as td:
        p=os.path.join(td,'core.db'); app=create_app(settings_for('sqlite:///'+p)); c=TestClient(app); internal=c.get('/v1/continuity/readiness').json(); assert 'filesystem_backup_root_configured' in internal
        r=c.get('/api/v1/continuity/status'); assert r.status_code in (200,401,403)
        if r.status_code==200:
            data=r.json()['data']; assert data['backup_locations_publicly_exposed'] is False and data['backup_identifiers_publicly_exposed'] is False and 'storage_uri' not in data

def test_internal_api_backup_attestation_and_external_drill_roundtrip():
    with tempfile.TemporaryDirectory() as td:
        app=create_app(settings_for('sqlite:///'+os.path.join(td,'core.db'))); c=TestClient(app); payload={'backup_key':'api-pg','database_engine':'postgresql','storage_kind':'operator-managed','storage_uri':'operator://pg/api','checksum_sha256':'c'*64}; r=c.post('/v1/continuity/backups',json=payload); assert r.status_code==200; bid=r.json()['id']; a=c.post(f'/v1/continuity/backups/{bid}/attest-verification',json={'actor':'ops','observed_checksum_sha256':'c'*64,'evidence':{}}); assert a.status_code==200 and a.json()['verification_state']=='attested'; drill=c.post(f'/v1/continuity/backups/{bid}/restore-rehearsals/external',json={'state':'passed','operator_actor':'ops','schema_head':'0023','duration_ms':1000,'integrity_checks':{'ok':True},'evidence':{}}); assert drill.status_code==200 and drill.json()['automatic_restore'] is False

def test_migration_rehearsal_from_0022_applies_current_head():
    with tempfile.TemporaryDirectory() as td:
        p=os.path.join(td,'core.db'); d=Database('sqlite:///'+p); Base.metadata.create_all(d.engine)
        from app.models import SchemaMigration
        from app.migrations import MIGRATIONS
        with d.session_factory() as db:
            for version,description in MIGRATIONS:
                if version<='0022': db.add(SchemaMigration(version=version,description=description))
            db.commit()
        expected=[version for version,_ in MIGRATIONS if version>'0022']; assert run_migrations(d)==expected; assert migration_status(d)['pending']==[]
