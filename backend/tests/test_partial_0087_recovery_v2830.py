from sqlalchemy import text
from app.database import Database
from app.migrations import run_migrations, migration_status
from app.models import ResearchEvidenceSynthesisRecord

def test_partial_0087_recovery(tmp_path):
    db=Database("sqlite:///"+str(tmp_path/"partial.db")); run_migrations(db)
    with db.engine.begin() as con: con.execute(text("DELETE FROM schema_migrations WHERE version='0087'"))
    assert "0087" not in migration_status(db)["applied"]
    run_migrations(db); assert "0087" in migration_status(db)["applied"]; assert migration_status(db)["pending"]==[]
    assert ResearchEvidenceSynthesisRecord.__table__.name=="research_evidence_syntheses_v283"
