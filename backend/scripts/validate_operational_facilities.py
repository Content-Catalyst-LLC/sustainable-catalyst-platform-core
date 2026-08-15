from __future__ import annotations

import sys
from pathlib import Path
BACKEND=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BACKEND))

from app.config import Settings
from app.database import Database
from app.migrations import run_migrations, migration_status
from app.services.facilities import FACILITY_TYPES, OBSERVATION_KINDS

def main():
    settings=Settings.from_env(); db=Database(settings.database_url); applied=run_migrations(db); status=migration_status(db)
    assert settings.version=='2.12.0'; assert '0013' in status['applied']; assert not status['pending']
    assert {'hospital','school','water-facility','power-facility','crossing','food-distribution'} <= FACILITY_TYPES
    assert {'operational-status','damage-status','access-status','service-status'} <= OBSERVATION_KINDS
    print('PASS - Core v2.12.0 operational facility registry validation')
    print('applied_now=', ','.join(applied) or 'none')
if __name__=='__main__': main()
