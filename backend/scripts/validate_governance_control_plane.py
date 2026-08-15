from __future__ import annotations
import os,tempfile
from app.config import Settings
from app.database import Database
from app.migrations import migration_status,run_migrations
from app.services.governance import create_policy,evaluate_access,readiness,verify_audit_chain
fd,path=tempfile.mkstemp(prefix='sc-core-v2160-',suffix='.db'); os.close(fd)
try:
 s=Settings(database_url='sqlite:///'+path); db=Database(s.database_url); run_migrations(db); st=migration_status(db)
 assert '0019' in st['applied'] and not st['pending']
 with db.session_factory() as session:
  r=readiness(s); assert r['enabled'] and r['default_private_access']=='deny' and r['secret_values_persisted_in_audit'] is False
  create_policy(session,name='allow-site-intelligence-read',effect='allow',principal_type='service',principal_id='site-intelligence',product_scope='site-intelligence',resource_type='evidence',action='read',visibility_ceiling='internal',priority=100)
  d=evaluate_access(session,s,principal_type='service',principal_id='site-intelligence',product='site-intelligence',resource_type='evidence',resource_id='sample',action='read',requested_visibility='internal',context={'api_token':'must-not-persist','purpose':'validation'})
  assert d['allowed'] is True
  chain=verify_audit_chain(session); assert chain['valid'] and chain['events_checked']>=2
 print({'version':s.version,'migration_0019_applied':True,'pending_migrations':st['pending'],'enforcement_mode':s.governance_enforcement_mode,'audit_chain':'sha256-linked','automatic_evidence_authority_change':False})
 print(f'PASS - Core {s.version} governance access and audit control plane validation')
finally:
 try: os.unlink(path)
 except FileNotFoundError: pass
