import sqlite3
from sqlalchemy import inspect
from app.database import Database
from app.migrations import run_migrations,migration_status

TABLES={'visual_runtime_scenes','visual_runtime_layers','visual_runtime_nodes','visual_runtime_edges','visual_runtime_annotations','visual_runtime_views','visual_runtime_bindings','visual_runtime_snapshots'}

def tables(db): return set(inspect(db.engine).get_table_names())

def test_pristine_0065_migration(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'pristine.db'}"); applied=run_migrations(db)
    assert '0065' in applied and migration_status(db)['pending']==[] and TABLES.issubset(tables(db))

def test_partial_0065_recovers_by_recording_metadata(tmp_path):
    p=tmp_path/'partial.db'; db=Database(f'sqlite:///{p}'); run_migrations(db)
    con=sqlite3.connect(p); con.execute("delete from schema_migrations where version='0065'"); con.commit(); con.close()
    assert TABLES.issubset(tables(db)); assert run_migrations(db)==['0065']; assert migration_status(db)['pending']==[]
