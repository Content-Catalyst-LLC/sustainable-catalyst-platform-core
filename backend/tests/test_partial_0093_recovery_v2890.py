from sqlalchemy import text
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.models import ResearchQualityAuditRecord,ResearchQualityAuditSnapshotRecord

def test_partial_0093_recovery(tmp_path):
 db=Database("sqlite:///"+str(tmp_path/"partial.db")); run_migrations(db)
 with db.engine.begin() as con: con.execute(text("DELETE FROM schema_migrations WHERE version='0093'"))
 assert "0093" not in migration_status(db)["applied"]; run_migrations(db); assert "0093" in migration_status(db)["applied"] and migration_status(db)["pending"]==[]; assert ResearchQualityAuditRecord.__table__.name=="research_quality_audits_v289"; assert ResearchQualityAuditSnapshotRecord.__table__.name=="research_quality_audit_snapshots_v289"
