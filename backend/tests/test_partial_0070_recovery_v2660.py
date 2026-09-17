import sqlite3
from app.database import Database
from app.migrations import run_migrations,migration_status
TABLES={'visual_model_constructions','visual_model_components','visual_model_relationships','visual_model_assumptions','visual_model_constraints','visual_model_interventions','visual_model_handoffs','visual_model_snapshots'}
def tables(db):
    with db.engine.connect() as c:return {r[0] for r in c.exec_driver_sql("select name from sqlite_master where type='table'")}
def test_pristine_0070(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'p.db'}");assert '0070' in run_migrations(db);assert TABLES.issubset(tables(db));assert migration_status(db)['pending']==[]
def test_partial_0070(tmp_path):
    p=tmp_path/'q.db';db=Database(f'sqlite:///{p}');run_migrations(db);con=sqlite3.connect(p);con.execute("delete from schema_migrations where version='0070'");con.commit();con.close();assert run_migrations(db)==['0070'];assert migration_status(db)['pending']==[]
