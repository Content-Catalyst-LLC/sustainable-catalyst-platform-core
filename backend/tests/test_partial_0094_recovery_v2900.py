from sqlalchemy import text
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.models import ResearchWorkflowRecord,ResearchWorkflowSnapshotRecord

def test_partial_0094_recovery(tmp_path):
 db=Database("sqlite:///"+str(tmp_path/"partial.db")); run_migrations(db)
 with db.engine.begin() as con: con.execute(text("DELETE FROM schema_migrations WHERE version='0094'"))
 assert "0094" not in migration_status(db)["applied"]; run_migrations(db); assert "0094" in migration_status(db)["applied"] and migration_status(db)["pending"]==[]; assert ResearchWorkflowRecord.__table__.name=="research_workflows_v290"; assert ResearchWorkflowSnapshotRecord.__table__.name=="research_workflow_snapshots_v290"
