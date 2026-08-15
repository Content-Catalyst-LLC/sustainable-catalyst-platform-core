from dataclasses import replace
from tempfile import TemporaryDirectory
from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.services import operations

def main():
    with TemporaryDirectory() as td:
        settings=replace(Settings(),database_url=f"sqlite:///{td}/core.db")
        db=Database(settings.database_url); run_migrations(db); status=migration_status(db)
        with db.session_factory() as session:
            inc=operations.create_incident(session,title='validator',severity='sev2',idempotency_key='v2190')
            change=operations.create_change(session,settings,change_key='v2190-change',risk='high',release=settings.version)
            assert change.approval_required
            assert operations.verify_event_chain(session,inc.id)['valid']
            ready=operations.readiness(session,settings)
        assert tuple(map(int,settings.version.split('.')[:2])) >= (2,19) and '0022' in status['applied'] and not status['pending'] and ready['automatic_rollback_enabled'] is False and ready['causal_attribution_from_correlation'] is False
        print({'version':settings.version,'migration_0022_applied':True,'pending_migrations':status['pending'],'automatic_rollback_enabled':False,'rollback_execution_mode':'operator-confirmed','causal_attribution_from_correlation':False})
        print('PASS - Core incident response change control and rollback coordination validation')
if __name__=='__main__': main()
