import sqlite3
from app.database import Database
from app.migrations import run_migrations,migration_status
TABLES={'predictive_monitoring_studies','predictive_detection_rules','predictive_anomaly_observations','predictive_change_points','predictive_early_warning_signals','predictive_monitoring_episodes','predictive_monitoring_packages'}
def tables(path):
    con=sqlite3.connect(path)
    try:return {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    finally:con.close()
def test_pristine_upgrade_to_0060(tmp_path):
    p=tmp_path/'pristine.db'; db=Database(f'sqlite:///{p}'); applied=run_migrations(db); assert '0060' in applied and migration_status(db)['pending']==[] and TABLES.issubset(tables(p))
def test_safe_partial_0060_tables_then_ledger_repair(tmp_path):
    p=tmp_path/'partial.db'; db=Database(f'sqlite:///{p}'); run_migrations(db); con=sqlite3.connect(p)
    try: con.execute("delete from schema_migrations where version='0060'"); con.commit()
    finally: con.close()
    assert TABLES.issubset(tables(p)); assert run_migrations(db)==['0060']; assert migration_status(db)['pending']==[]
