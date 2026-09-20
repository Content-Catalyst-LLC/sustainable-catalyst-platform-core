from sqlalchemy import text
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.models import ResearchPublicationRecord

def test_partial_0085_recovery(tmp_path):
    db=Database("sqlite:///"+str(tmp_path/"partial.db"))
    run_migrations(db)
    with db.engine.begin() as con: con.execute(text("DELETE FROM schema_migrations WHERE version='0085'"))
    assert "0085" not in migration_status(db)["applied"]
    run_migrations(db); assert "0085" in migration_status(db)["applied"]; assert migration_status(db)["pending"]==[]
    assert ResearchPublicationRecord.__table__.name=="research_publications_v281"
