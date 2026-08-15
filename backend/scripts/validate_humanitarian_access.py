from __future__ import annotations
import os, sys
from pathlib import Path
BACKEND=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BACKEND))
from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.services.humanitarian import SERVICE_DOMAINS, CONDITION_KINDS, HDX_HAPI_METRIC_MAP

def main():
    settings=Settings.from_env(); db=Database(settings.database_url); run_migrations(db); status=migration_status(db)
    assert '0014' in status['applied']; assert not status['pending']
    assert {'health','education','food','water','electricity','fuel','displacement','communications','shelter'} <= SERVICE_DOMAINS
    assert {'access-status','food-security','interruption','displacement'} <= CONDITION_KINDS
    assert 'food_security_nutrition_poverty_food_security' in HDX_HAPI_METRIC_MAP
    print({'version':settings.version,'migration_0014_applied':True,'pending_migrations':status['pending'],'humanitarian_domains':len(SERVICE_DOMAINS),'structured_hdx_mappings':len(HDX_HAPI_METRIC_MAP),'external_provider_health_release_blocking':False})
    print('PASS - Core v2.11.0 humanitarian access and essential services validation')
if __name__=='__main__': main()
