from sqlalchemy import text
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.models import ComputationExecutionRecord,ComputationExecutionSnapshotRecord
def test_partial_0091_recovery(tmp_path):
 db=Database("sqlite:///"+str(tmp_path/"partial.db")); run_migrations(db)
 with db.engine.begin() as con: con.execute(text("DELETE FROM schema_migrations WHERE version='0091'"))
 assert "0091" not in migration_status(db)["applied"]; run_migrations(db); assert "0091" in migration_status(db)["applied"]; assert migration_status(db)["pending"]==[]; assert ComputationExecutionRecord.__table__.name=="computation_executions_v287"; assert ComputationExecutionSnapshotRecord.__table__.name=="computation_execution_snapshots_v287"
