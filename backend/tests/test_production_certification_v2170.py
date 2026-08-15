import os,tempfile
from dataclasses import replace
from fastapi.testclient import TestClient
from sqlalchemy import update
from app.config import Settings
from app.database import Database
from app.main import create_app
from app.migrations import MIGRATIONS,run_migrations,migration_status
from app.models import RecoveryReadinessCheckpoint,SchemaMigration
from app.services import certification

def db():
 fd,path=tempfile.mkstemp(suffix='.db'); os.close(fd); d=Database('sqlite:///'+path); run_migrations(d); return d,path

def test_migration_head_and_readiness():
 d,p=db()
 try:
  s=Settings(database_url='sqlite:///'+p); m=certification.migration_assurance(d); assert m['schema_head']=='0024' and m['zero_pending'] and m['head_matches']
  with d.session_factory() as session:
   r=certification.readiness(session,s); assert r['enabled'] and r['database_backup_embedded'] is False and r['external_provider_health_release_blocking'] is False
 finally: os.unlink(p)

def test_upgrade_from_recorded_0019_state_applies_current_head():
 fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd); d=Database('sqlite:///'+p)
 try:
  from app.database import Base; Base.metadata.create_all(d.engine)
  with d.session_factory() as session:
   # Model a real v2.16.0 / migration-0019 state. Do not pre-record
   # migrations introduced after 0019; the current migration engine must
   # discover and apply every later migration in order.
   for version,description in MIGRATIONS:
    if version <= '0019':
     session.add(SchemaMigration(version=version,description=description))
   session.commit()
  expected=[version for version,_ in MIGRATIONS if version>'0019']; assert run_migrations(d)==expected; assert migration_status(d)['pending']==[]
 finally: os.unlink(p)

def test_recovery_checkpoint_integrity_and_contract():
 d,p=db()
 try:
  s=Settings(database_url='sqlite:///'+p)
  with d.session_factory() as session:
   row=certification.create_recovery_checkpoint(session,d,s); check=certification.verify_recovery_checkpoint(row); assert check['valid']; assert row.recovery_contract_json['database_backup_embedded'] is False; assert row.recovery_contract_json['external_backup_required_for_full_restore'] is True
 finally: os.unlink(p)

def test_checkpoint_tamper_is_detected():
 d,p=db()
 try:
  s=Settings(database_url='sqlite:///'+p)
  with d.session_factory() as session:
   row=certification.create_recovery_checkpoint(session,d,s); row.row_counts_json={'tampered':999}; session.add(row); session.commit(); assert certification.verify_recovery_checkpoint(row)['valid'] is False
 finally: os.unlink(p)

def test_certification_passes_without_transient_provider_dependency():
 d,p=db()
 try:
  s=Settings(database_url='sqlite:///'+p, certification_require_gateway_release_ready=False)
  with d.session_factory() as session:
   row,detail=certification.run_certification(session,d,s,{'release_ready':False,'required_blockers':['site-intelligence']}); assert row.state=='certified'; assert detail['checks']['external_provider_health_release_blocking'] is False
 finally: os.unlink(p)

def test_certification_can_require_first_party_gateway_readiness():
 d,p=db()
 try:
  s=Settings(database_url='sqlite:///'+p, certification_require_gateway_release_ready=True)
  with d.session_factory() as session:
   row,detail=certification.run_certification(session,d,s,{'release_ready':False,'required_blockers':['site-intelligence']}); assert row.state=='blocked'; assert 'required_first_party_services' in detail['blockers']
 finally: os.unlink(p)

def test_public_readiness_does_not_expose_records():
 fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
 try:
  app=create_app(Settings(database_url='sqlite:///'+p)); c=TestClient(app); r=c.get('/api/v1/certification/readiness'); assert r.status_code in (200,401,403); internal=c.get('/v1/certification/readiness'); assert internal.status_code==200; body=internal.json(); assert body['release']=='2.21.0'; assert body['migration_assurance']['schema_head']=='0024'; assert body['database_backup_embedded'] is False
 finally: os.unlink(p)

def test_internal_api_creates_and_verifies_checkpoint():
 fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
 try:
  app=create_app(Settings(database_url='sqlite:///'+p)); c=TestClient(app); r=c.post('/v1/certification/recovery/checkpoints'); assert r.status_code==200; cid=r.json()['id']; v=c.post(f'/v1/certification/recovery/checkpoints/{cid}/verify'); assert v.status_code==200 and v.json()['valid'] is True
 finally: os.unlink(p)
