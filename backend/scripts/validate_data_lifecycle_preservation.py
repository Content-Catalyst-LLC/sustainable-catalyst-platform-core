
import os,tempfile
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import lifecycle

def main():
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
    try:
      s=Settings(database_url='sqlite:///'+p); d=Database(s.database_url); run_migrations(d); m=migration_status(d)
      with d.session_factory() as db:
        policy=lifecycle.create_policy(db,s,policy_key='validator',subject_type='evidence-record'); archive=lifecycle.create_archive(db,archive_key='validator-a',subject_type='evidence-record',subject_id='e1',snapshot={'value':1}); check=lifecycle.verify_archive(db,archive); status=lifecycle.readiness(db,s)
        assert tuple(map(int,s.version.split('.')[:3])) >= (2,22,0) and '0025' in m['applied'] and not m['pending']; assert check['valid'] and policy.preserve_provenance and not policy.hard_delete_allowed; assert status['hard_delete_enabled'] is False and status['provenance_preservation_required'] is True
      print({'version':s.version,'migration_0025_applied':True,'pending_migrations':[],'hard_delete_enabled':False,'archive_integrity':'sha256','provenance_preservation_required':True}); print('PASS - Core 2.22.0 data lifecycle archival integrity and preservation validation'); return 0
    finally:
      try: os.unlink(p)
      except FileNotFoundError: pass
if __name__=='__main__': raise SystemExit(main())
