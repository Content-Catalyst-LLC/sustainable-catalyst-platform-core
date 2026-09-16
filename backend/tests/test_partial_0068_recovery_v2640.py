import sqlite3
from app.database import Database
from app.migrations import run_migrations,migration_status
TABLES={'visual_link_policies','visual_selection_sets','visual_cross_filters','visual_brush_ranges','visual_focus_highlights','visual_propagation_records','visual_linked_view_snapshots'}
def tables(db):
    with db.engine.connect() as c:return set(c.exec_driver_sql("select name from sqlite_master where type='table'").scalars().all())
def test_pristine_0068_migration(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'pristine.db'}");applied=run_migrations(db);assert '0068' in applied and migration_status(db)['pending']==[] and TABLES.issubset(tables(db))
def test_partial_0068_recovers_by_recording_metadata(tmp_path):
    p=tmp_path/'partial.db';db=Database(f'sqlite:///{p}');run_migrations(db);con=sqlite3.connect(p);con.execute("delete from schema_migrations where version='0068'");con.commit();con.close();assert TABLES.issubset(tables(db));assert run_migrations(db)==['0068'];assert migration_status(db)['pending']==[]
