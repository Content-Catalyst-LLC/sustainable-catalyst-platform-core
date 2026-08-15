from __future__ import annotations
import os,tempfile
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import continuity

def main():
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
    try:
        d=Database('sqlite:///'+p); run_migrations(d); s=Settings(database_url='sqlite:///'+p)
        with d.session_factory() as db:
            ready=continuity.continuity_status(db,s)
            assert s.version=='2.20.0' and '0023' in migration_status(d)['applied'] and not migration_status(d)['pending']
            assert ready['database_backup_embedded'] is False and ready['automatic_database_restore_enabled'] is False and ready['arbitrary_restore_commands_enabled'] is False and ready['evidence_semantics_unchanged'] is True
        print('PASS - Core v2.20.0 continuity backup verification and disaster recovery validation')
    finally:
        try: os.remove(p)
        except OSError: pass
if __name__=='__main__': main()
