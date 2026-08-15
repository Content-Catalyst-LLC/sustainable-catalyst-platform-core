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
    version=tuple(int(part) for part in settings.version.split('.')[:3]); assert version >= (2,10,0); assert '0013' in status['applied']; assert not status['pending']
    assert {'hospital','school','water-facility','power-facility','crossing','food-distribution'} <= FACILITY_TYPES
    assert {'operational-status','damage-status','access-status','service-status'} <= OBSERVATION_KINDS
    print(f'PASS - Core {settings.version} operational facility registry validation')
    print('applied_now=', ','.join(applied) or 'none')
if __name__=='__main__': main()
