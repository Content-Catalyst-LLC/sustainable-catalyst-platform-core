import sqlite3
from sqlalchemy import inspect
from app.database import Database
from app.migrations import run_migrations,migration_status
TABLES={'visual_grammar_specifications','visual_grammar_data_bindings','visual_grammar_marks','visual_grammar_scales','visual_grammar_encodings','visual_grammar_transforms','visual_grammar_guides','visual_grammar_snapshots'}
def tables(db):return set(inspect(db.engine).get_table_names())
def test_pristine_0067_migration(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'pristine.db'}");applied=run_migrations(db);assert '0067' in applied and migration_status(db)['pending']==[] and TABLES.issubset(tables(db))
def test_partial_0067_recovers_by_recording_metadata(tmp_path):
    p=tmp_path/'partial.db';db=Database(f'sqlite:///{p}');run_migrations(db);con=sqlite3.connect(p);con.execute("delete from schema_migrations where version='0067'");con.commit();con.close();assert TABLES.issubset(tables(db));assert run_migrations(db)==['0067'];assert migration_status(db)['pending']==[]
