import sqlite3
from sqlalchemy import inspect
from app.database import Database
from app.migrations import run_migrations,migration_status
TABLES={"unified_research_project_profiles","unified_research_questions","unified_research_objectives","unified_research_components","unified_research_relationships","unified_research_provenance_records","unified_research_runtime_handoffs","unified_research_project_snapshots"}
def tables(db): return set(inspect(db.engine).get_table_names())
def test_pristine_0076(tmp_path):
 db=Database(f"sqlite:///{tmp_path/'p.db'}"); assert "0076" in run_migrations(db); assert TABLES.issubset(tables(db)); assert migration_status(db)["pending"]==[]
def test_partial_0076(tmp_path):
 p=tmp_path/'q.db'; db=Database(f"sqlite:///{p}"); run_migrations(db); con=sqlite3.connect(p); con.execute("delete from schema_migrations where version='0076'"); con.commit(); con.close(); assert run_migrations(db)==["0076"]; assert migration_status(db)["pending"]==[]
