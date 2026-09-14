from sqlalchemy import inspect

from app.database import Base, Database
from app.migrations import MIGRATIONS, migration_status, run_migrations
from app.models import SchemaMigration

CAUSAL_TABLES = {
    "causal_graphs", "causal_variables", "causal_edges", "causal_interventions",
    "causal_identifications", "causal_estimates", "causal_diagnostics",
}

def test_partial_0041_table_state_recovers_by_recording_short_metadata(tmp_path):
    db = Database(f"sqlite:///{tmp_path/'partial0041.db'}")
    # Reproduce production ordering: create_all succeeds, ledger insert fails.
    Base.metadata.create_all(db.engine)
    tables = set(inspect(db.engine).get_table_names())
    assert CAUSAL_TABLES <= tables
    with db.session_factory() as session:
        for version, description in MIGRATIONS:
            if version == "0041":
                break
            session.add(SchemaMigration(version=version, description=description))
        session.commit()
        assert session.get(SchemaMigration, "0041") is None

    newly_applied = run_migrations(db)
    assert "0041" in newly_applied
    assert "0042" in newly_applied
    with db.session_factory() as session:
        row = session.get(SchemaMigration, "0041")
        assert row is not None
        assert len(row.description) <= 300

    status = migration_status(db)
    assert status["pending"] == []
    assert status["applied"][-1] == "0052"
    assert CAUSAL_TABLES <= set(inspect(db.engine).get_table_names())
