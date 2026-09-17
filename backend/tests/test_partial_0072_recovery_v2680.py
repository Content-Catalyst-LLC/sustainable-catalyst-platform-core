import sqlite3
from sqlalchemy import inspect
from app.database import Database
from app.migrations import run_migrations,migration_status
TABLES={'visual_forensic_workspaces','visual_forensic_evidence_bindings','visual_forensic_claim_overlays','visual_forensic_timeline_layers','visual_forensic_spatial_temporal_layers','visual_forensic_media_layers','visual_forensic_reconstruction_bindings','visual_forensic_documentary_bindings','visual_forensic_graph_bindings','visual_forensic_snapshots'}
def tables(db):return set(inspect(db.engine).get_table_names())
def test_pristine_0072(tmp_path):
 db=Database(f"sqlite:///{tmp_path/'p.db'}");assert '0072' in run_migrations(db);assert TABLES.issubset(tables(db));assert migration_status(db)['pending']==[]
def test_partial_0072(tmp_path):
 p=tmp_path/'q.db';db=Database(f'sqlite:///{p}');run_migrations(db);con=sqlite3.connect(p);con.execute("delete from schema_migrations where version='0072'");con.commit();con.close();assert run_migrations(db)==['0072'];assert migration_status(db)['pending']==[]
