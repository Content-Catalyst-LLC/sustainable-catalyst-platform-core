import sqlite3
from sqlalchemy import inspect
from app.database import Database
from app.migrations import run_migrations,migration_status
TABLES={"visual_decision_workspaces","visual_decision_alternatives","visual_decision_criteria","visual_decision_evidence_bindings","visual_decision_scenario_bindings","visual_decision_risk_overlays","visual_decision_tradeoffs","visual_decision_rationales","visual_decision_handoffs","visual_decision_snapshots"}
def tables(db):return set(inspect(db.engine).get_table_names())
def test_pristine_0073(tmp_path):
 db=Database(f"sqlite:///{tmp_path/'p.db'}");assert "0073" in run_migrations(db);assert TABLES.issubset(tables(db));assert migration_status(db)["pending"]==[]
def test_partial_0073(tmp_path):
 p=tmp_path/"q.db";db=Database(f"sqlite:///{p}");run_migrations(db);con=sqlite3.connect(p);con.execute("delete from schema_migrations where version='0073'");con.commit();con.close();assert run_migrations(db)==["0073"];assert migration_status(db)["pending"]==[]
