from sqlalchemy import text
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.models import ScientificResearchProtocolRecord,ScientificProtocolSnapshotRecord
def test_partial_0090_recovery(tmp_path):
 db=Database("sqlite:///"+str(tmp_path/"partial.db")); run_migrations(db)
 with db.engine.begin() as con: con.execute(text("DELETE FROM schema_migrations WHERE version='0090'"))
 assert "0090" not in migration_status(db)["applied"]; run_migrations(db); assert "0090" in migration_status(db)["applied"]; assert migration_status(db)["pending"]==[]; assert ScientificResearchProtocolRecord.__table__.name=="scientific_research_protocols_v286"; assert ScientificProtocolSnapshotRecord.__table__.name=="scientific_protocol_snapshots_v286"
