from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.services import observability

def main():
    settings=Settings.from_env(); db=Database(settings.database_url); run_migrations(db); m=migration_status(db)
    assert '0021' in m['applied'] and not m['pending']
    with db.session_factory() as s:
        r=observability.readiness(s,settings); assert r['enabled']; assert r['paid_monitoring_provider_required'] is False
        names={x.name for x in observability.list_slos(s,'platform-core')}; assert {'Core availability','Core p95 latency'} <= names
    print({'version':settings.version,'migration_0021_applied':True,'pending_migrations':m['pending'],'external_monitoring_provider_required':False,'default_slos':2})
    print('PASS - Core v2.18.0 observability SLO and production operations validation')
if __name__=='__main__': main()
