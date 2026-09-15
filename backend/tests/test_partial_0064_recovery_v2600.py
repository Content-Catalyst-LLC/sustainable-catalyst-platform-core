import sqlite3
from sqlalchemy import inspect
from app.database import Database
from app.migrations import run_migrations,migration_status

TABLES={'predictive_intelligence_packages','predictive_intelligence_package_components','predictive_intelligence_package_artifacts','predictive_intelligence_package_environments','predictive_intelligence_package_verifications','predictive_intelligence_package_reviews','predictive_intelligence_package_snapshots'}

def tables(db): return set(inspect(db.engine).get_table_names())

def test_pristine_0064_migration(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'pristine.db'}"); applied=run_migrations(db)
    assert '0064' in applied and migration_status(db)['pending']==[] and TABLES.issubset(tables(db))

def test_partial_0064_recovers_by_recording_metadata(tmp_path):
    p=tmp_path/'partial.db'; db=Database(f'sqlite:///{p}'); run_migrations(db)
    con=sqlite3.connect(p); con.execute("delete from schema_migrations where version='0064'"); con.commit(); con.close()
    assert TABLES.issubset(tables(db)); assert run_migrations(db)==['0064']; assert migration_status(db)['pending']==[]
