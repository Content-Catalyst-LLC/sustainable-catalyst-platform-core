from sqlalchemy import text
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.models import ResearchInferenceRecord,ResearchInferenceSnapshotRecord

def test_partial_0092_recovery(tmp_path):
 db=Database("sqlite:///"+str(tmp_path/"partial.db")); run_migrations(db)
 with db.engine.begin() as con: con.execute(text("DELETE FROM schema_migrations WHERE version='0092'"))
 assert "0092" not in migration_status(db)["applied"]; run_migrations(db); assert "0092" in migration_status(db)["applied"] and migration_status(db)["pending"]==[]; assert ResearchInferenceRecord.__table__.name=="research_inferences_v288"; assert ResearchInferenceSnapshotRecord.__table__.name=="research_inference_snapshots_v288"
