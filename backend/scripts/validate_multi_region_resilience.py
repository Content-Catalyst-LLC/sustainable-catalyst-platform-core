from __future__ import annotations
import os,tempfile
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import resilience
def main():
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
    try:
        d=Database('sqlite:///'+p); run_migrations(d); s=Settings(database_url='sqlite:///'+p)
        with d.session_factory() as db:
            resilience.upsert_region_status(db,region_key='primary',role='primary',health_state='unavailable',readiness_state='blocked',replication_state='current',read_eligible=True,write_eligible=True)
            resilience.upsert_region_status(db,region_key='standby',role='standby',health_state='healthy',readiness_state='ready',replication_state='current',replication_lag_seconds=1,read_eligible=True,write_eligible=True)
            g=resilience.create_group(db,s,group_key='validator',active_region='primary',candidate_regions=['standby']); a=resilience.assess_failover(db,g); st=resilience.readiness(db,s)
            m=migration_status(d); assert tuple(map(int,s.version.split('.')[:3])) >= (2,21,0) and '0024' in m['applied'] and not m['pending']; assert a.recommendation=='failover' and a.automatic_execution is False and a.infrastructure_actuation_by_core is False; assert st['write_failover_requires_replication_safety'] is True
        print({'version':s.version,'migration_0024_applied':True,'pending_migrations':m['pending'],'automatic_failover_enabled':False,'write_failover_requires_replication_safety':True,'degraded_read_only_supported':s.multi_region_degraded_read_only_enabled,'provider_specific_failover_required':False})
        print(f'PASS - Core {s.version} multi-region resilience and failover coordination validation')
    finally:
        try: os.remove(p)
        except OSError: pass
if __name__=='__main__': main()
