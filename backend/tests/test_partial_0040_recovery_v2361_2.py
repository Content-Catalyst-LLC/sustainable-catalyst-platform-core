from sqlalchemy import inspect, select

from app.database import Base, Database
from app.migrations import MIGRATIONS, migration_status, run_migrations
from app.models import SchemaMigration


def test_partial_0040_table_state_recovers_by_recording_short_metadata(tmp_path):
    db = Database(f"sqlite:///{tmp_path/'partial0040.db'}")
    # Reproduce the production failure ordering: create_all succeeds, then the
    # migration-ledger insert fails. The compute table therefore exists while
    # migration 0040 is not yet recorded.
    Base.metadata.create_all(db.engine)
    assert "uncertainty_compute_runs" in inspect(db.engine).get_table_names()
    with db.session_factory() as session:
        for version, description in MIGRATIONS:
            if version == "0040":
                break
            session.add(SchemaMigration(version=version, description=description))
        session.commit()
        assert session.get(SchemaMigration, "0040") is None

    newly_applied = run_migrations(db)
    assert "0040" in newly_applied
    assert newly_applied[-1] == "0050"
    with db.session_factory() as session:
        row = session.get(SchemaMigration, "0040")
        assert row is not None
        assert len(row.description) <= 300

    status = migration_status(db)
    assert status["pending"] == []
    assert "0040" in status["applied"]
