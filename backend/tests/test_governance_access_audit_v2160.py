from __future__ import annotations
from sqlalchemy import select
from app.config import Settings
from app.database import Database
from app.migrations import migration_status,run_migrations
from app.models import GovernanceAuditEvent,GovernanceDecision
from app.services.governance import bind_role,create_policy,create_retention_policy,evaluate_access,readiness,verify_audit_chain

def setup(tmp_path):
 s=Settings(environment='test',database_url=f"sqlite:///{tmp_path/'gov.db'}")
 db=Database(s.database_url); run_migrations(db); return s,db

def test_migration_and_readiness(tmp_path):
 s,db=setup(tmp_path); st=migration_status(db); assert '0019' in st['applied'] and not st['pending']; r=readiness(s); assert r['enabled']; assert r['default_private_access']=='deny'; assert not r['secret_values_persisted_in_audit']

def test_public_read_fallback_private_default_deny(tmp_path):
 s,db=setup(tmp_path)
 with db.session_factory() as session:
  a=evaluate_access(session,s,principal_type='user',principal_id='u1',resource_type='evidence',action='read',requested_visibility='public')
  b=evaluate_access(session,s,principal_type='user',principal_id='u1',resource_type='evidence',action='read',requested_visibility='private')
  assert a['allowed'] is True and b['allowed'] is False

def test_explicit_policy_allow_and_deny_tie_deny_wins(tmp_path):
 s,db=setup(tmp_path)
 with db.session_factory() as session:
  create_policy(session,name='allow',effect='allow',principal_type='service',principal_id='site-intelligence',resource_type='facility',action='read',visibility_ceiling='internal',priority=10)
  create_policy(session,name='deny',effect='deny',principal_type='service',principal_id='site-intelligence',resource_type='facility',action='read',priority=10)
  d=evaluate_access(session,s,principal_type='service',principal_id='site-intelligence',resource_type='facility',action='read',requested_visibility='internal')
  assert d['decision']=='deny' and d['reason'].startswith('policy:')

def test_admin_role_allows_restricted_action(tmp_path):
 s,db=setup(tmp_path)
 with db.session_factory() as session:
  bind_role(session,principal_type='user',principal_id='admin1',role='admin')
  d=evaluate_access(session,s,principal_type='user',principal_id='admin1',resource_type='governance-policy',action='manage',requested_visibility='restricted')
  assert d['allowed'] is True and d['reason']=='role:admin'

def test_product_scoped_role_does_not_escape_scope(tmp_path):
 s,db=setup(tmp_path)
 with db.session_factory() as session:
  bind_role(session,principal_type='service',principal_id='workspace',role='service',product_scope='workspace')
  good=evaluate_access(session,s,principal_type='service',principal_id='workspace',product='workspace',resource_type='exchange-package',action='create',requested_visibility='internal')
  bad=evaluate_access(session,s,principal_type='service',principal_id='workspace',product='site-intelligence',resource_type='exchange-package',action='create',requested_visibility='internal')
  assert good['allowed'] and not bad['allowed']

def test_visibility_ceiling_blocks_allow_policy(tmp_path):
 s,db=setup(tmp_path)
 with db.session_factory() as session:
  create_policy(session,name='internal-only',effect='allow',principal_type='user',principal_id='u2',resource_type='evidence',action='read',visibility_ceiling='internal')
  d=evaluate_access(session,s,principal_type='user',principal_id='u2',resource_type='evidence',action='read',requested_visibility='private')
  assert not d['allowed']

def test_secret_context_is_redacted_from_audit_and_decision_stores_hash_only(tmp_path):
 s,db=setup(tmp_path)
 with db.session_factory() as session:
  d=evaluate_access(session,s,principal_type='service',principal_id='lab',resource_type='dataset',action='read',requested_visibility='public',context={'api_token':'topsecret','nested':{'password':'hidden'},'purpose':'model'})
  decision=session.get(GovernanceDecision,d['decision_id']); assert decision and len(decision.context_hash)==64
  event=session.scalar(select(GovernanceAuditEvent).where(GovernanceAuditEvent.decision_id==d['decision_id']))
  assert event.details_json['context']['api_token']=='[REDACTED]'; assert event.details_json['context']['nested']['password']=='[REDACTED]'; assert 'topsecret' not in str(event.details_json)

def test_audit_chain_detects_tampering(tmp_path):
 s,db=setup(tmp_path)
 with db.session_factory() as session:
  evaluate_access(session,s,principal_type='user',principal_id='u',resource_type='evidence',action='read',requested_visibility='public')
  evaluate_access(session,s,principal_type='user',principal_id='u',resource_type='facility',action='read',requested_visibility='public')
  assert verify_audit_chain(session)['valid']
  row=session.scalar(select(GovernanceAuditEvent).order_by(GovernanceAuditEvent.sequence).limit(1)); row.details_json={'tampered':True}; session.commit()
  assert not verify_audit_chain(session)['valid']

def test_audit_retention_cannot_be_deleted_or_shortened_below_one_year(tmp_path):
 s,db=setup(tmp_path)
 with db.session_factory() as session:
  import pytest
  with pytest.raises(ValueError): create_retention_policy(session,resource_type='governance-audit',retention_hours=100,disposition='compact')
  with pytest.raises(ValueError): create_retention_policy(session,resource_type='governance-audit',retention_hours=8760,disposition='delete')
  row=create_retention_policy(session,resource_type='governance-audit',retention_hours=8760,disposition='retain'); assert row.disposition=='retain'

def test_decision_is_persisted_and_audit_is_append_only_api(tmp_path):
 s,db=setup(tmp_path)
 with db.session_factory() as session:
  d=evaluate_access(session,s,principal_type='service',principal_id='core',resource_type='scale-job',action='execute',requested_visibility='internal')
  assert session.get(GovernanceDecision,d['decision_id']) is not None; assert verify_audit_chain(session)['events_checked']==1

def test_governance_readiness_endpoint(client):
 r=client.get('/v1/governance/readiness'); assert r.status_code==200; body=r.json(); assert body['release']=='2.18.0'; assert body['migration_0019_applied'] is True; assert body['audit_chain']=='sha256-linked'

def test_governance_api_policy_decision_and_audit_verify(client,write_headers):
 p=client.post('/v1/governance/policies',headers=write_headers,json={'name':'api-allow','effect':'allow','principal_type':'service','principal_id':'site-intelligence','product_scope':'site-intelligence','resource_type':'evidence','action':'read','visibility_ceiling':'internal','priority':5}); assert p.status_code==200,p.text
 d=client.post('/v1/governance/decisions/evaluate',headers=write_headers,json={'principal_type':'service','principal_id':'site-intelligence','product':'site-intelligence','resource_type':'evidence','resource_id':'e1','action':'read','requested_visibility':'internal','context':{'token':'must-redact'}}); assert d.status_code==200,d.text; assert d.json()['allowed'] is True
 v=client.get('/v1/governance/audit/verify',headers=write_headers); assert v.status_code==200 and v.json()['valid'] is True
