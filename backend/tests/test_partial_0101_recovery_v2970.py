from sqlalchemy import text
from app.database import Database,Base
from app.migrations import run_migrations,migration_status

def test_partial_0101_recovery(tmp_path):
    db=Database("sqlite:///"+str(tmp_path/"partial.db")); Base.metadata.create_all(db.engine)
    with db.engine.begin() as c: c.execute(text("DELETE FROM schema_migrations WHERE version='0101'"))
    run_migrations(db); s=migration_status(db); assert "0101" in s["applied"] and s["pending"]==[]
