import sqlite3
from sqlalchemy import inspect
from app.database import Database
from app.migrations import run_migrations,migration_status

TABLES={'predictive_decision_studies','predictive_decision_options','predictive_decision_criteria','predictive_decision_evidence_bindings','predictive_decision_scenario_assessments','predictive_decision_evaluations','predictive_decision_handoffs','predictive_decision_packages'}

def tables(db): return set(inspect(db.engine).get_table_names())

def test_pristine_0063_migration(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'pristine.db'}"); applied=run_migrations(db)
    assert '0063' in applied and migration_status(db)['pending']==[] and TABLES.issubset(tables(db))

def test_partial_0063_recovers_by_recording_metadata(tmp_path):
    p=tmp_path/'partial.db'; db=Database(f'sqlite:///{p}'); run_migrations(db)
    con=sqlite3.connect(p); con.execute("delete from schema_migrations where version='0063'"); con.commit(); con.close()
    assert TABLES.issubset(tables(db)); assert run_migrations(db)==['0063']; assert migration_status(db)['pending']==[]
