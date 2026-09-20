from sqlalchemy import inspect, text

from app.config import Settings
from app.main import create_app


def test_partial_0082_recovery(tmp_path):
    app = create_app(Settings(database_url="sqlite:///" + str(tmp_path / "p.db")))
    db = app.state.database
    tables = {
        "research_hypothesis_sets_v278",
        "research_hypotheses_v278",
        "research_hypothesis_revisions_v278",
        "research_hypothesis_evidence_assessments_v278",
        "research_hypothesis_predictions_v278",
        "research_hypothesis_assumptions_v278",
        "research_hypothesis_relations_v278",
        "research_hypothesis_discrimination_gaps_v278",
        "research_hypothesis_snapshots_v278",
    }
    assert tables.issubset(set(inspect(db.engine).get_table_names()))
    with db.engine.begin() as connection:
        connection.execute(text("DELETE FROM schema_migrations WHERE version='0082'"))
    from app.migrations import migration_status, run_migrations
    run_migrations(db)
    assert "0082" in migration_status(db)["applied"]
    assert migration_status(db)["pending"] == []
