from sqlalchemy import text
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations, migration_status
from app.models import ResearchPeerReviewRecord

def test_partial_0086_recovery(tmp_path):
    db=Database("sqlite:///"+str(tmp_path/"partial.db")); run_migrations(db)
    with db.engine.begin() as con: con.execute(text("DELETE FROM schema_migrations WHERE version='0086'"))
    assert "0086" not in migration_status(db)["applied"]
    run_migrations(db); assert "0086" in migration_status(db)["applied"]; assert migration_status(db)["pending"]==[]
    assert ResearchPeerReviewRecord.__table__.name=="research_peer_reviews_v282"
