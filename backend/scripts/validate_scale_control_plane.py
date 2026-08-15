import tempfile, os
from pathlib import Path
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services.scale import readiness
fd,path=tempfile.mkstemp(prefix='sc-core-v2150-',suffix='.db'); os.close(fd)
try:
 s=Settings(database_url='sqlite:///'+path); db=Database(s.database_url); run_migrations(db); st=migration_status(db)
 assert '0018' in st['applied'] and not st['pending']; 
 with db.session_factory() as session: r=readiness(session,s); assert r['enabled'] and not r['external_blob_provider_required']; print({'version':s.version,'migration_0018_applied':True,'pending_migrations':st['pending'],'max_active_jobs':r['max_active_jobs'],'external_blob_provider_required':False}); print('PASS - Core v2.15.0 distributed processing storage and scale validation')
finally:
 try: os.unlink(path)
 except: pass
