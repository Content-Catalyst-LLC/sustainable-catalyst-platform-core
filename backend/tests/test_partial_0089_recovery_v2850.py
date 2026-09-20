from sqlalchemy import text
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.models import ResearchPortfolioRecord,ResearchPortfolioSnapshotRecord
def test_partial_0089_recovery(tmp_path):
    db=Database("sqlite:///"+str(tmp_path/"partial.db")); run_migrations(db)
    with db.engine.begin() as con: con.execute(text("DELETE FROM schema_migrations WHERE version='0089'"))
    assert "0089" not in migration_status(db)["applied"]; run_migrations(db); assert "0089" in migration_status(db)["applied"]; assert migration_status(db)["pending"]==[]; assert ResearchPortfolioRecord.__table__.name=="research_portfolios_v285"; assert ResearchPortfolioSnapshotRecord.__table__.name=="research_portfolio_snapshots_v285"
