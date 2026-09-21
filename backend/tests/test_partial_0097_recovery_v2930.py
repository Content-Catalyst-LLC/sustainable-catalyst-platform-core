from sqlalchemy import text,inspect
from app.database import Database
from app.migrations import run_migrations,migration_status

def test_partial_0097_recovery(tmp_path):
 db=Database("sqlite:///"+str(tmp_path/"partial.db")); run_migrations(db)
 with db.engine.begin() as c: c.execute(text("DELETE FROM schema_migrations WHERE version='0097'"))
 st=migration_status(db); assert "0097" not in st["applied"] and "0097" in st["pending"]
 applied=run_migrations(db); assert "0097" in applied and migration_status(db)["pending"]==[]
 names=set(inspect(db.engine).get_table_names()); assert "research_contributors_v293" in names and "research_contributor_snapshots_v293" in names
