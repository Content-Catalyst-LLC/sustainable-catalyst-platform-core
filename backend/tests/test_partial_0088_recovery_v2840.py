from sqlalchemy import text
from app.database import Database
from app.migrations import run_migrations, migration_status
from app.models import ResearchProgramRecord, ResearchProgramSnapshotRecord

def test_partial_0088_recovery(tmp_path):
    db=Database("sqlite:///"+str(tmp_path/"partial.db")); run_migrations(db)
    with db.engine.begin() as con: con.execute(text("DELETE FROM schema_migrations WHERE version='0088'"))
    assert "0088" not in migration_status(db)["applied"]
    run_migrations(db)
    assert "0088" in migration_status(db)["applied"]; assert migration_status(db)["pending"]==[]
    assert ResearchProgramRecord.__table__.name=="research_programs_v284"
    assert ResearchProgramSnapshotRecord.__table__.name=="research_program_snapshots_v284"
