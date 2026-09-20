from sqlalchemy import inspect, text
from app.config import Settings
from app.main import create_app

def test_partial_0084_recovery(tmp_path):
    app=create_app(Settings(database_url="sqlite:///" + str(tmp_path / "partial.db"))); db=app.state.database
    tables={"research_conclusions_v280","research_conclusion_evidence_bindings_v280","research_conclusion_caveats_v280","research_conclusion_dissent_v280","research_decision_traces_v280","research_conclusion_reviews_v280","research_conclusion_revisions_v280","research_conclusion_snapshots_v280"}
    assert tables.issubset(set(inspect(db.engine).get_table_names()))
    with db.engine.begin() as con: con.execute(text("DELETE FROM schema_migrations WHERE version='0084'"))
    from app.migrations import migration_status, run_migrations
    run_migrations(db); assert "0084" in migration_status(db)["applied"]; assert migration_status(db)["pending"]==[]
