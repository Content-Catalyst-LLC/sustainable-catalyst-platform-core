#!/usr/bin/env python3
from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.services.spatial_temporal import readiness

def main():
    settings=Settings.from_env(); db=Database(settings.database_url); run_migrations(db); status=migration_status(db)
    with db.session_factory() as s: r=readiness(s)
    assert '0042' in status['applied'] and status['pending']==[]
    assert r['spatial_temporal_scenes'] and r['renderer_neutral']
    assert not r['spatial_analysis_by_core'] and not r['remote_sensing_by_core'] and not r['automatic_truth_promotion']
    print({'version':settings.version,'migration_0042_applied':True,'renderer_neutral':True,'spatial_analysis_by_core':False,'remote_sensing_by_core':False,'automatic_truth_promotion':False})
    print('PASS - Core 2.38.0 Spatial & Temporal Visual Reasoning validation')
if __name__=='__main__':main()
