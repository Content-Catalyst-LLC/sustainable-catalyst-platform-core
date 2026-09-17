import sqlite3
from sqlalchemy import inspect
from app.database import Database
from app.migrations import run_migrations,migration_status
TABLES={'visual_exploration_sessions','visual_query_targets','visual_query_requests','visual_query_predicates','visual_traversal_requests','visual_query_result_bindings','visual_exploration_states','visual_query_snapshots'}
def tables(db):return set(inspect(db.engine).get_table_names())
def test_pristine_0069_migration(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'pristine.db'}");applied=run_migrations(db);assert '0069' in applied and migration_status(db)['pending']==[] and TABLES.issubset(tables(db))
def test_partial_0069_recovers_by_recording_metadata(tmp_path):
    p=tmp_path/'partial.db';db=Database(f'sqlite:///{p}');run_migrations(db);con=sqlite3.connect(p);con.execute("delete from schema_migrations where version='0069'");con.commit();con.close();assert TABLES.issubset(tables(db));assert run_migrations(db)==['0069'];assert migration_status(db)['pending']==[]
