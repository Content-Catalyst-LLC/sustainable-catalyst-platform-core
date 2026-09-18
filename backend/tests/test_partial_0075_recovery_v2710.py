import sqlite3
from sqlalchemy import inspect
from app.database import Database
from app.migrations import run_migrations,migration_status
TABLES={"cross_product_visual_runtime_integrations","cross_product_visual_object_bindings","cross_product_visual_context_bindings","cross_product_visual_capability_bindings","cross_product_visual_view_bindings","cross_product_visual_handoff_routes","cross_product_visual_sync_records","cross_product_visual_integration_snapshots"}
def tables(db): return set(inspect(db.engine).get_table_names())
def test_pristine_0075(tmp_path):
 db=Database(f"sqlite:///{tmp_path/'p.db'}"); assert "0075" in run_migrations(db); assert TABLES.issubset(tables(db)); assert migration_status(db)["pending"]==[]
def test_partial_0075(tmp_path):
 p=tmp_path/"q.db"; db=Database(f"sqlite:///{p}"); run_migrations(db); con=sqlite3.connect(p); con.execute("delete from schema_migrations where version='0075'"); con.commit(); con.close(); assert run_migrations(db)==["0075"]; assert migration_status(db)["pending"]==[]
