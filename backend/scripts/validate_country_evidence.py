from __future__ import annotations
import sys
from pathlib import Path
BACKEND=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BACKEND))
from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.services.country_evidence import AUTHORITY_PRECEDENCE, reconcile_candidates

def main():
    settings=Settings.from_env(); db=Database(settings.database_url); run_migrations(db); status=migration_status(db)
    version=tuple(int(part) for part in settings.version.split('.')[:3]); assert version >= (2,12,0); assert '0015' in status['applied']; assert not status['pending']
    assert AUTHORITY_PRECEDENCE['primary-official'] < AUTHORITY_PRECEDENCE['harmonized-benchmark']
    result=reconcile_candidates('PSE','electricity',[
        {'record_family':'economic-statistic','record_id':'wb','concept':'electricity','source_id':'world-bank','publisher':'World Bank','evidence_class':'harmonized-benchmark','semantic_role':'structural-baseline','geographic_scope':'PSE','reference_period':'2024','value_number':100,'unit':'percent'},
        {'record_family':'humanitarian-condition','record_id':'ops','concept':'electricity','source_id':'ocha-hdx-hapi','publisher':'OCHA','semantic_role':'operational-condition','evidence_class':'operational-reporting','geographic_scope':'PSE-GZA','reference_period':'2026-08-14','status_value':'service-unavailable'},
    ])
    assert result['do_not_blend'] is True; assert result['automatic_averaging'] is False
    assert result['rationale']['structural_baselines_never_substitute_for_operational_conditions'] is True
    assert result['rationale']['subnational_scope_never_substitutes_for_national_scope'] is True
    print({'version':settings.version,'migration_0015_applied':True,'pending_migrations':status['pending'],'authority_roles':len(AUTHORITY_PRECEDENCE),'automatic_averaging':False,'external_provider_health_release_blocking':False})
    print(f'PASS - Core {settings.version} country evidence federation and reconciliation validation')
if __name__=='__main__': main()
