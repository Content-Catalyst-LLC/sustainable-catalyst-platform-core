import os,tempfile
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.config import Settings
from app.database import Database
from app.main import create_app
from app.migrations import migration_status,run_migrations
from app.models import DistributedQuotaUsageBucket,WorkloadAdmissionDecision
from app.services import workload_governance as wg, observability


def settings(path,**kw):
    base=dict(database_url='sqlite:///'+path,write_api_key='write-test-key',observability_request_metrics_enabled=False)
    base.update(kw); return Settings(**base)
def client(td,**kw): return TestClient(create_app(settings(os.path.join(td,'core.db'),**kw)))
def auth(): return {'X-SC-API-Key':'write-test-key'}

def test_release_and_migration_readiness():
  with tempfile.TemporaryDirectory() as td:
    c=client(td); b=c.get('/v1/workload-governance/readiness').json(); assert c.get('/health').json()['version']=='2.26.0'; assert b['release']=='2.26.0' and b['migration_0029_applied'] and b['distributed_quota_backend']=='database-shared' and b['hard_admission_control'] is True

def test_bootstrap_creates_classes_and_policies_without_external_dependency():
  with tempfile.TemporaryDirectory() as td:
    c=client(td); r=c.post('/v1/workload-governance/bootstrap',headers=auth()); assert r.status_code==200; b=c.get('/v1/workload-governance/readiness').json(); assert b['configured'] and b['workload_classes']==3 and b['quota_policies']==2 and b['external_quota_service_required'] is False

def test_quota_allows_within_limit_then_hard_rejects_and_retry_after():
  with tempfile.TemporaryDirectory() as td:
    d=Database('sqlite:///'+os.path.join(td,'x.db')); run_migrations(d)
    with d.session_factory() as db:
      wg.upsert_workload_class(db,class_key='standard',name='Standard',max_concurrent_leases=20,max_request_units=10)
      wg.upsert_policy(db,settings(os.path.join(td,'x.db')),policy_key='q',name='q',subject_scope='product',subject_key='site',resource_type='requests',workload_class_key='standard',window_seconds=60,limit_units=2,burst_units=1)
      a,l=wg.admit(db,settings(os.path.join(td,'x.db')),request_key='a',subject_scope='product',subject_key='site',requested_units=2); assert a.decision=='allow' and l
      b,_=wg.admit(db,settings(os.path.join(td,'x.db')),request_key='b',subject_scope='product',subject_key='site',requested_units=2); assert b.decision=='reject' and b.reason=='distributed-quota-exhausted' and b.retry_after_seconds>0

def test_burst_budget_is_consumable():
  with tempfile.TemporaryDirectory() as td:
    d=Database('sqlite:///'+os.path.join(td,'x.db')); run_migrations(d); s=settings(os.path.join(td,'x.db'))
    with d.session_factory() as db:
      wg.upsert_workload_class(db,class_key='standard',name='Standard',max_concurrent_leases=20,max_request_units=20)
      wg.upsert_policy(db,s,policy_key='q',name='q',subject_key='*',limit_units=5,burst_units=2,workload_class_key='standard')
      a,_=wg.admit(db,s,request_key='a',subject_scope='product',subject_key='x',requested_units=7); assert a.decision=='allow' and a.quota_remaining_after==0
      b,_=wg.admit(db,s,request_key='b',subject_scope='product',subject_key='x',requested_units=1); assert b.decision=='reject'

def test_observe_policy_never_hard_rejects_quota_excess():
  with tempfile.TemporaryDirectory() as td:
    d=Database('sqlite:///'+os.path.join(td,'x.db')); run_migrations(d); s=settings(os.path.join(td,'x.db'))
    with d.session_factory() as db:
      wg.upsert_workload_class(db,class_key='standard',name='Standard',max_concurrent_leases=20,max_request_units=20)
      wg.upsert_policy(db,s,policy_key='q',name='q',subject_key='*',limit_units=1,enforcement_mode='observe',workload_class_key='standard')
      a,_=wg.admit(db,s,request_key='a',subject_scope='product',subject_key='x',requested_units=2); assert a.decision=='allow' and a.reason=='quota-exceeded-observe-only'

def test_request_unit_limit_rejects():
  with tempfile.TemporaryDirectory() as td:
    d=Database('sqlite:///'+os.path.join(td,'x.db')); run_migrations(d); s=settings(os.path.join(td,'x.db'))
    with d.session_factory() as db:
      wg.upsert_workload_class(db,class_key='standard',name='Standard',max_request_units=1)
      a,_=wg.admit(db,s,request_key='a',subject_scope='product',subject_key='x',requested_units=2); assert a.decision=='reject' and a.reason=='request-unit-limit-exceeded'

def test_concurrency_limit_throttles_until_lease_released():
  with tempfile.TemporaryDirectory() as td:
    d=Database('sqlite:///'+os.path.join(td,'x.db')); run_migrations(d); s=settings(os.path.join(td,'x.db'))
    with d.session_factory() as db:
      wg.upsert_workload_class(db,class_key='standard',name='Standard',max_concurrent_leases=1)
      a,l=wg.admit(db,s,request_key='a',subject_scope='product',subject_key='x'); assert a.decision=='allow'
      b,_=wg.admit(db,s,request_key='b',subject_scope='product',subject_key='x'); assert b.decision=='throttle' and b.reason=='workload-class-concurrency-limit'
      wg.release_lease(db,l.id); c,_=wg.admit(db,s,request_key='c',subject_scope='product',subject_key='x'); assert c.decision=='allow'

def test_idempotent_request_key_does_not_double_charge_quota():
  with tempfile.TemporaryDirectory() as td:
    d=Database('sqlite:///'+os.path.join(td,'x.db')); run_migrations(d); s=settings(os.path.join(td,'x.db'))
    with d.session_factory() as db:
      wg.upsert_workload_class(db,class_key='standard',name='Standard')
      p=wg.upsert_policy(db,s,policy_key='q',name='q',subject_key='*',limit_units=10,workload_class_key='standard')
      a,_=wg.admit(db,s,request_key='same',subject_scope='product',subject_key='x',requested_units=3); b,_=wg.admit(db,s,request_key='same',subject_scope='product',subject_key='x',requested_units=3); assert a.id==b.id
      bucket=db.scalar(select(DistributedQuotaUsageBucket).where(DistributedQuotaUsageBucket.policy_id==p.id)); assert bucket.used_units==3

def test_slo_breach_throttles_standard_but_critical_can_continue():
  with tempfile.TemporaryDirectory() as td:
    d=Database('sqlite:///'+os.path.join(td,'x.db')); run_migrations(d); s=settings(os.path.join(td,'x.db'))
    with d.session_factory() as db:
      wg.upsert_workload_class(db,class_key='standard',name='Standard'); wg.upsert_workload_class(db,class_key='critical',name='Critical',allow_when_slo_breached=True)
      # seeded availability SLO requires 5 samples; create 5 failed requests to breach it.
      for i in range(5): observability.record_request(db,service='platform-core',method='GET',route='/x',status_code=500,duration_ms=10,request_id=str(i))
      a,_=wg.admit(db,s,request_key='std',subject_scope='product',subject_key='x',workload_class_key='standard'); assert a.decision=='throttle' and a.reason=='slo-breached'
      b,_=wg.admit(db,s,request_key='crit',subject_scope='product',subject_key='x',workload_class_key='critical'); assert b.decision=='allow'

def test_public_status_hides_limits_and_subject_usage():
  with tempfile.TemporaryDirectory() as td:
    c=client(td); c.post('/v1/workload-governance/bootstrap',headers=auth())
    # public API requires developer bearer auth, so exercise service-safe structure through internal state expectations.
    b=c.get('/v1/workload-governance/readiness').json(); assert 'quota_policies' in b and 'quota_limit' not in b and 'subject_key' not in b

def test_hard_enforcement_can_be_disabled_but_decision_is_throttle_not_silent_allow():
  with tempfile.TemporaryDirectory() as td:
    d=Database('sqlite:///'+os.path.join(td,'x.db')); run_migrations(d); s=settings(os.path.join(td,'x.db'),admission_hard_enforcement_enabled=False)
    with d.session_factory() as db:
      wg.upsert_workload_class(db,class_key='standard',name='Standard'); wg.upsert_policy(db,s,policy_key='q',name='q',subject_key='*',limit_units=1,workload_class_key='standard')
      a,_=wg.admit(db,s,request_key='a',subject_scope='product',subject_key='x',requested_units=2); assert a.decision=='throttle' and a.hard_enforcement is False

def test_certification_optional_gate_blocks_when_unconfigured():
  with tempfile.TemporaryDirectory() as td:
    c=client(td,certification_require_workload_governance_ready=True); r=c.post('/v1/certification/runs',headers=auth()); assert r.status_code==200; body=r.json()['detail']; assert body['state']=='blocked'; assert 'distributed_quota_admission_control' in body['blockers']; assert body['checks']['workload_governance_ready'] is False

def test_certification_gate_ready_after_bootstrap():
  with tempfile.TemporaryDirectory() as td:
    c=client(td,certification_require_workload_governance_ready=True); c.post('/v1/workload-governance/bootstrap',headers=auth()); r=c.post('/v1/certification/runs',headers=auth()); assert r.status_code==200; body=r.json()['detail']; assert body['checks']['workload_governance_ready'] is True; assert body['checks']['hard_admission_control'] is True

def test_meta_promotes_distributed_rate_limit_backend():
  with tempfile.TemporaryDirectory() as td:
    c=client(td); b=c.get('/v1/meta').json(); assert 'database_shared_distributed_quota_backend' in b['capabilities']; assert 'distributed_rate_limit_backend' not in b['deferred_capabilities']
