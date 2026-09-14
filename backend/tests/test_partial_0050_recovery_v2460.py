import sqlite3
from pathlib import Path
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations, migration_status

V246_TABLES={
 'forensic_places','forensic_evidence_spatial_bindings','forensic_event_place_bindings','forensic_spatial_uncertainty_envelopes',
 'forensic_trajectory_evidence','forensic_spatial_temporal_intersections','forensic_spatial_temporal_views','forensic_spatial_temporal_snapshots'
}

def tables(path):
    con=sqlite3.connect(path)
    try: return {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    finally: con.close()

def test_pristine_upgrade_to_0050(tmp_path):
    db_path=tmp_path/'pristine.db'; db=Database(f'sqlite:///{db_path}')
    applied=run_migrations(db)
    assert '0050' in applied and migration_status(db)['pending']==[]
    assert V246_TABLES.issubset(tables(db_path))

def test_safe_partial_0050_tables_then_ledger_repair(tmp_path):
    db_path=tmp_path/'partial.db'; db=Database(f'sqlite:///{db_path}')
    run_migrations(db)
    con=sqlite3.connect(db_path)
    try:
        con.execute("delete from schema_migrations where version='0050'"); con.commit()
    finally: con.close()
    assert V246_TABLES.issubset(tables(db_path))
    applied=run_migrations(db)
    assert applied==['0050'] and migration_status(db)['pending']==[]
