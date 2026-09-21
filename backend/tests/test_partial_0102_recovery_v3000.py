from sqlalchemy import text
from app.database import Database,Base
from app.migrations import run_migrations,migration_status
def test_partial_0102_recovery(tmp_path):
 db=Database("sqlite:///"+str(tmp_path/"partial.db")); Base.metadata.create_all(db.engine)
 with db.engine.begin() as c:c.execute(text("DELETE FROM schema_migrations WHERE version='0102'"))
 run_migrations(db); s=migration_status(db); assert "0102" in s["applied"] and s["pending"]==[]
