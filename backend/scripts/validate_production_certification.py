from __future__ import annotations
import os,tempfile
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import certification
fd,path=tempfile.mkstemp(prefix='sc-core-v2170-',suffix='.db'); os.close(fd)
try:
 s=Settings(database_url='sqlite:///'+path); d=Database(s.database_url); run_migrations(d); st=migration_status(d)
 assert '0020' in st['applied'] and not st['pending']
 with d.session_factory() as session:
  cp=certification.create_recovery_checkpoint(session,d,s); assert certification.verify_recovery_checkpoint(cp)['valid']
  row,detail=certification.run_certification(session,d,s,{'release_ready':True,'required_blockers':[]})
  assert row.state=='certified' and detail['migration_head']=='0020' and not detail['pending_migrations']
  assert detail['recovery']['database_backup_embedded'] is False and detail['recovery']['external_backup_required_for_full_restore'] is True
 print({'version':s.version,'migration_0020_applied':True,'pending_migrations':st['pending'],'certification_state':'certified','recovery_checkpoint_integrity':'sha256','database_backup_embedded':False,'external_provider_health_release_blocking':False})
 print(f'PASS - Core {s.version} production certification migration assurance and recovery readiness validation')
finally:
 try: os.unlink(path)
 except FileNotFoundError: pass
