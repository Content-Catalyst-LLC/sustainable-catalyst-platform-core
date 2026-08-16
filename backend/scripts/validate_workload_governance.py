from pathlib import Path
import os,tempfile
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import workload_governance as wg
with tempfile.TemporaryDirectory() as td:
 p=os.path.join(td,'core.db'); s=Settings(database_url='sqlite:///'+p,observability_request_metrics_enabled=False); d=Database(s.database_url); run_migrations(d)
 with d.session_factory() as db:
  wg.bootstrap_defaults(db,s)
  a,l=wg.admit(db,s,request_key='validate-allow',subject_scope='product',subject_key='validator',workload_class_key='standard',requested_units=1)
  b=wg.certification_snapshot(db,s)
  assert a.decision=='allow' and l is not None and b['workload_governance_ready'] and b['hard_admission_control'] and b['shared_state']
 m=migration_status(d); assert '0029' in m['applied'] and not m['pending']
 print({'version':'2.26.0','migration_0029_applied':True,'pending_migrations':m['pending'],'distributed_quota_backend':'database-shared','decision':a.decision,'hard_admission_control':True,'automatic_scaling':False})
 print('PASS - Core 2.26.0 distributed quotas admission control and workload governance validation')
