import sqlite3
from app.database import Database
from app.migrations import run_migrations,migration_status
TABLES={'predictive_spatial_temporal_studies','predictive_spatial_units','predictive_spatial_temporal_forecasts','predictive_spatial_temporal_observations','predictive_spatial_propagation_evidence','predictive_spatial_hotspot_evidence','predictive_spatial_temporal_evaluations','predictive_spatial_temporal_packages'}
def tables(path):
    con=sqlite3.connect(path)
    try:return {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    finally:con.close()
def test_pristine_upgrade_to_0061(tmp_path):
    p=tmp_path/'pristine.db'; db=Database(f'sqlite:///{p}'); applied=run_migrations(db); assert '0061' in applied and migration_status(db)['pending']==[] and TABLES.issubset(tables(p))
def test_safe_partial_0061_tables_then_ledger_repair(tmp_path):
    p=tmp_path/'partial.db'; db=Database(f'sqlite:///{p}'); run_migrations(db); con=sqlite3.connect(p)
    try: con.execute("delete from schema_migrations where version='0061'"); con.commit()
    finally: con.close()
    assert TABLES.issubset(tables(p)); assert run_migrations(db)==['0061']; assert migration_status(db)['pending']==[]
