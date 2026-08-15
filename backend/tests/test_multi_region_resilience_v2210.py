import os,tempfile
from dataclasses import replace
from fastapi.testclient import TestClient
from app.config import Settings
from app.database import Database,Base
from app.main import create_app
from app.migrations import MIGRATIONS,run_migrations,migration_status
from app.models import SchemaMigration
from app.services import resilience,certification

def db_and_settings(**kwargs):
    fd,path=tempfile.mkstemp(suffix='.db'); os.close(fd); d=Database('sqlite:///'+path); run_migrations(d); return d,path,replace(Settings(),database_url='sqlite:///'+path,**kwargs)
def seed(db,s,source_health='unavailable',target_replication='current',target_lag=5,target_write=True,degraded=True):
    resilience.upsert_region_status(db,region_key='us-east',role='primary',health_state=source_health,readiness_state='ready' if source_health=='healthy' else 'blocked',replication_state='current',read_eligible=True,write_eligible=True)
    resilience.upsert_region_status(db,region_key='us-west',role='standby',health_state='healthy',readiness_state='ready',replication_state=target_replication,replication_lag_seconds=target_lag,read_eligible=True,write_eligible=target_write)
    return resilience.create_group(db,s,group_key='core-prod',active_region='us-east',candidate_regions=['us-west'],degraded_read_only_allowed=degraded)

def test_readiness_and_migration_0024():
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
    try:
        app=create_app(Settings(database_url='sqlite:///'+p,observability_request_metrics_enabled=False)); c=TestClient(app); b=c.get('/v1/resilience/readiness').json(); assert b['release']=='2.21.0' and b['migration_0024_applied'] and b['automatic_failover_enabled'] is False and b['infrastructure_actuation_by_core'] is False
    finally: os.unlink(p)

def test_region_status_upsert_and_secret_scrub():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        a=resilience.upsert_region_status(db,region_key='r1',health_state='healthy',readiness_state='ready',metadata={'token':'x','safe':'y'}); b=resilience.upsert_region_status(db,region_key='r1',health_state='degraded',readiness_state='degraded'); assert a.id==b.id and b.health_state=='degraded'
    finally: os.unlink(p)

def test_healthy_primary_recommends_stay():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        g=seed(db,s,source_health='healthy'); a=resilience.assess_failover(db,g); assert a.recommendation=='stay' and a.target_region is None
    finally: os.unlink(p)

def test_replication_safe_target_recommends_write_failover():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        g=seed(db,s); a=resilience.assess_failover(db,g); assert a.recommendation=='failover' and a.target_region=='us-west' and a.replication_safe_for_write is True and a.read_only is False
    finally: os.unlink(p)

def test_lagging_target_downgrades_to_read_only():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        g=seed(db,s,target_replication='lagging',target_lag=999); a=resilience.assess_failover(db,g); assert a.recommendation=='failover-read-only' and a.read_only is True and not a.replication_safe_for_write
    finally: os.unlink(p)

def test_lagging_target_blocks_when_degraded_mode_disabled():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        g=seed(db,s,target_replication='lagging',target_lag=999,degraded=False); a=resilience.assess_failover(db,g); assert a.recommendation=='blocked' and a.target_region is None
    finally: os.unlink(p)

def test_failover_requires_acknowledgement_and_approval_before_execution_record():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        a=resilience.assess_failover(db,seed(db,s));
        try: resilience.decide_failover(db,a,state='executed',actor='ops')
        except ValueError: pass
        else: raise AssertionError('executed without approval')
        resilience.decide_failover(db,a,state='acknowledged',actor='ops'); resilience.decide_failover(db,a,state='approved',actor='reviewer'); resilience.decide_failover(db,a,state='executed',actor='ops'); assert a.automatic_execution is False and a.infrastructure_actuation_by_core is False
    finally: os.unlink(p)

def test_public_status_is_aggregate_only():
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
    try:
      app=create_app(Settings(database_url='sqlite:///'+p,observability_request_metrics_enabled=False)); c=TestClient(app); r=c.get('/api/v1/resilience/status'); assert r.status_code in (200,401,403)
      if r.status_code==200:
        data=r.json()['data']; assert data['region_endpoints_publicly_exposed'] is False and data['failover_evidence_publicly_exposed'] is False and 'items' not in data
    finally: os.unlink(p)

def test_certification_gate_is_opt_in_and_can_block():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        _,detail=certification.run_certification(db,d,s,{'release_ready':True,'required_blockers':[]}); assert 'multi_region_resilience' not in detail['blockers']
      with d.session_factory() as db:
        strict=replace(s,certification_require_multi_region_ready=True); _,detail=certification.run_certification(db,d,strict,{'release_ready':True,'required_blockers':[]}); assert 'multi_region_resilience' in detail['blockers']
    finally: os.unlink(p)

def test_internal_api_round_trip():
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
    try:
      app=create_app(Settings(database_url='sqlite:///'+p,observability_request_metrics_enabled=False)); c=TestClient(app)
      for payload in [dict(region_key='east',role='primary',health_state='unavailable',readiness_state='blocked',replication_state='current',read_eligible=True,write_eligible=True),dict(region_key='west',role='standby',health_state='healthy',readiness_state='ready',replication_state='current',replication_lag_seconds=1,read_eligible=True,write_eligible=True)]: assert c.post('/v1/resilience/regions',json=payload).status_code==200
      g=c.post('/v1/resilience/failover-groups',json={'group_key':'api','active_region':'east','candidate_regions':['west']}); assert g.status_code==200; a=c.post('/v1/resilience/failover-groups/'+g.json()['id']+'/assess',json={'reason':'test'}); assert a.status_code==200 and a.json()['recommendation']=='failover'
    finally: os.unlink(p)

def test_provider_specific_actuation_is_never_enabled():
    d,p,s=db_and_settings()
    try:
      with d.session_factory() as db:
        g=seed(db,s); st=resilience.readiness(db,s); assert st['provider_specific_failover_required'] is False and st['automatic_failover_enabled'] is False and st['infrastructure_actuation_by_core'] is False
    finally: os.unlink(p)

def test_migration_rehearsal_from_0023_applies_only_0024():
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd); d=Database('sqlite:///'+p)
    try:
      Base.metadata.create_all(d.engine)
      with d.session_factory() as db:
        for version,description in MIGRATIONS:
          if version<='0023': db.add(SchemaMigration(version=version,description=description))
        db.commit()
      assert run_migrations(d)==['0024'] and migration_status(d)['pending']==[]
    finally: os.unlink(p)
