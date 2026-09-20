from sqlalchemy import inspect, text

from app.config import Settings
from app.main import create_app


def test_partial_0083_recovery(tmp_path):
    app = create_app(Settings(database_url="sqlite:///" + str(tmp_path / "partial.db")))
    db = app.state.database
    tables = {
        "research_arguments_v279",
        "research_argument_nodes_v279",
        "research_argument_edges_v279",
        "research_evidentiary_syntheses_v279",
        "research_synthesis_components_v279",
        "research_counterarguments_v279",
        "research_argument_tensions_v279",
        "research_argument_revisions_v279",
        "research_argument_snapshots_v279",
    }
    assert tables.issubset(set(inspect(db.engine).get_table_names()))
    with db.engine.begin() as connection:
        connection.execute(text("DELETE FROM schema_migrations WHERE version='0083'"))
    from app.migrations import migration_status, run_migrations
    run_migrations(db)
    assert "0083" in migration_status(db)["applied"]
    assert migration_status(db)["pending"] == []
