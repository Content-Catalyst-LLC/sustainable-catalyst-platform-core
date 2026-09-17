import sqlite3
from sqlalchemy import inspect
from app.database import Database
from app.migrations import run_migrations,migration_status
TABLES={"unified_visual_reasoning_workspaces","unified_visual_layer_bindings","unified_visual_reasoning_paths","unified_visual_state_bridges","unified_visual_evidence_chains","unified_visual_runtime_handoffs","unified_visual_package_bindings","unified_visual_replay_states","unified_visual_reasoning_snapshots"}
def tables(db):return set(inspect(db.engine).get_table_names())
def test_pristine_0074(tmp_path):
 db=Database(f"sqlite:///{tmp_path/'p.db'}");assert "0074" in run_migrations(db);assert TABLES.issubset(tables(db));assert migration_status(db)["pending"]==[]
def test_partial_0074(tmp_path):
 p=tmp_path/"q.db";db=Database(f"sqlite:///{p}");run_migrations(db);con=sqlite3.connect(p);con.execute("delete from schema_migrations where version='0074'");con.commit();con.close();assert run_migrations(db)==["0074"];assert migration_status(db)["pending"]==[]
