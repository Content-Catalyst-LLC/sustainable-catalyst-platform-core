
import os,tempfile
from dataclasses import replace
from fastapi.testclient import TestClient
from app.config import Settings
from app.database import Database,Base
from app.main import create_app
from app.migrations import MIGRATIONS,run_migrations,migration_status
from app.models import SchemaMigration
from app.services import lifecycle,certification

def db_and_settings(**kwargs):
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd); d=Database('sqlite:///'+p); run_migrations(d); return d,p,replace(Settings(),database_url='sqlite:///'+p,**kwargs)

def test_readiness_and_migration_0025():
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
    try:
      c=TestClient(create_app(Settings(database_url='sqlite:///'+p,observability_request_metrics_enabled=False))); b=c.get('/v1/lifecycle/readiness').json(); assert b['release']=='2.23.0' and b['migration_0025_applied'] and b['hard_delete_enabled'] is False
    finally: os.unlink(p)

def test_policy_defaults_to_provenance_preserving_no_hard_delete():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        row=lifecycle.create_policy(db,s,policy_key='evidence',subject_type='evidence-record'); assert row.preserve_provenance and not row.hard_delete_allowed and row.minimum_retention_days==365
    finally: os.unlink(p)

def test_policy_rejects_tombstone_before_minimum_retention():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        try:lifecycle.create_policy(db,s,policy_key='bad',minimum_retention_days=365,tombstone_after_days=30)
        except ValueError: pass
        else: raise AssertionError('invalid retention policy accepted')
    finally: os.unlink(p)

def test_archive_integrity_and_secret_scrub():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        row=lifecycle.create_archive(db,archive_key='a1',subject_type='evidence-record',subject_id='e1',snapshot={'value':42,'token':'secret'}); assert row.snapshot_json['token']=='[redacted]' and lifecycle.verify_archive(db,row)['valid']
    finally: os.unlink(p)

def test_archive_tamper_is_detected():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        row=lifecycle.create_archive(db,archive_key='a2',subject_type='claim',subject_id='c1',snapshot={'value':'original'}); row.snapshot_json={'value':'tampered'}; db.add(row); db.commit(); assert lifecycle.verify_archive(db,row)['valid'] is False and row.verification_state=='mismatch'
    finally: os.unlink(p)

def test_hold_blocks_tombstone_until_released():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        h=lifecycle.place_hold(db,hold_key='h1',subject_type='claim',subject_id='c1',hold_type='legal',reason='preserve'); a=lifecycle.request_tombstone(db,subject_type='claim',subject_id='c1'); assert a.state=='blocked-by-hold' and not a.source_record_deleted
        lifecycle.release_hold(db,h); b=lifecycle.request_tombstone(db,subject_type='claim',subject_id='c1'); assert b.state=='tombstoned' and not b.source_record_deleted and b.provenance_preserved
    finally: os.unlink(p)

def test_restore_is_reference_first_and_does_not_overwrite_source():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        row=lifecycle.create_archive(db,archive_key='a3',subject_type='dataset',subject_id='d1',snapshot={'x':1}); action=lifecycle.restore_archive(db,row,actor='ops'); assert action.action_type=='restore-reference' and not action.source_record_deleted and action.evidence_json['automatic_source_overwrite'] is False
    finally: os.unlink(p)

def test_certification_gate_is_opt_in_and_can_block_on_integrity_mismatch():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        _,detail=certification.run_certification(db,d,s,{'release_ready':True,'required_blockers':[]}); assert 'data_lifecycle_preservation' not in detail['blockers']
        row=lifecycle.create_archive(db,archive_key='a4',subject_type='claim',subject_id='c4',snapshot={'x':1}); row.snapshot_json={'x':2}; db.add(row); db.commit(); lifecycle.verify_archive(db,row)
      with d.session_factory() as db:
        strict=replace(s,certification_require_preservation_ready=True); _,detail=certification.run_certification(db,d,strict,{'release_ready':True,'required_blockers':[]}); assert 'data_lifecycle_preservation' in detail['blockers']
    finally: os.unlink(p)

def test_public_status_is_aggregate_only():
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
    try:
      c=TestClient(create_app(Settings(database_url='sqlite:///'+p,observability_request_metrics_enabled=False))); r=c.get('/api/v1/lifecycle/status'); assert r.status_code in (200,401,403)
      if r.status_code==200:
        data=r.json()['data']; assert data['archive_contents_publicly_exposed'] is False and data['hold_reasons_publicly_exposed'] is False and 'items' not in data
    finally: os.unlink(p)

def test_internal_api_round_trip():
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
    try:
      c=TestClient(create_app(Settings(database_url='sqlite:///'+p,observability_request_metrics_enabled=False))); assert c.post('/v1/lifecycle/policies',json={'policy_key':'api','subject_type':'claim'}).status_code==200; a=c.post('/v1/lifecycle/archives',json={'archive_key':'api-a','subject_type':'claim','subject_id':'c1','snapshot':{'x':1}}); assert a.status_code==200; assert c.post('/v1/lifecycle/archives/'+a.json()['id']+'/verify').json()['valid'] is True
    finally: os.unlink(p)

def test_hard_delete_cannot_be_enabled_from_environment_settings():
    s=Settings.from_env(); assert s.data_lifecycle_hard_delete_enabled is False

def test_migration_rehearsal_from_0024_applies_current_head():
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd); d=Database('sqlite:///'+p)
    try:
      Base.metadata.create_all(d.engine)
      with d.session_factory() as db:
        for version,description in MIGRATIONS:
          if version<='0024': db.add(SchemaMigration(version=version,description=description))
        db.commit()
      expected=[version for version,_ in MIGRATIONS if version>'0024']; assert run_migrations(d)==expected and migration_status(d)['pending']==[]
    finally: os.unlink(p)
