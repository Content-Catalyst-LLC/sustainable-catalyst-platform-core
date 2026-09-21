from sqlalchemy import text,inspect
from app.database import Database
from app.migrations import run_migrations,migration_status
def test_partial_0098_recovery(tmp_path):
 db=Database("sqlite:///"+str(tmp_path/"partial.db")); run_migrations(db)
 with db.engine.begin() as c: c.execute(text("DELETE FROM schema_migrations WHERE version='0098'"))
 st=migration_status(db); assert "0098" not in st["applied"] and "0098" in st["pending"]
 applied=run_migrations(db); assert "0098" in applied and migration_status(db)["pending"]==[]
 names=set(inspect(db.engine).get_table_names()); assert "research_validation_challenges_v294" in names and "research_validation_snapshots_v294" in names
