from sqlalchemy import inspect
from app.database import Base, Database
from app.migrations import MIGRATIONS, migration_status, run_migrations
from app.models import SchemaMigration

TABLES = {
    "research_visual_explanations", "research_explanation_nodes", "research_explanation_relations",
    "research_explanation_citations", "research_explanation_views", "research_explanation_snapshots",
}


def test_partial_0043_table_state_recovers_by_recording_short_metadata(tmp_path):
    db = Database(f"sqlite:///{tmp_path/'partial0043.db'}")
    Base.metadata.create_all(db.engine)
    assert TABLES <= set(inspect(db.engine).get_table_names())
    with db.session_factory() as session:
        for version, description in MIGRATIONS:
            if version == "0043": break
            session.add(SchemaMigration(version=version, description=description))
        session.commit(); assert session.get(SchemaMigration, "0043") is None
    assert run_migrations(db) == ["0043", "0044", "0045", "0046", "0047", "0048", "0049", "0050", "0051", "0052", "0053"]
    with db.session_factory() as session:
        row = session.get(SchemaMigration, "0043"); assert row and len(row.description) <= 300
    status = migration_status(db); assert status["pending"] == [] and status["applied"][-1] == "0053"
    assert TABLES <= set(inspect(db.engine).get_table_names())


def test_pristine_pre_0043_schema_upgrades_additively(tmp_path):
    db = Database(f"sqlite:///{tmp_path/'pre0043.db'}")
    Base.metadata.create_all(db.engine)
    # Model a production v2.38 database: migration ledger ends at 0042 and
    # none of the six v2.39 tables exist yet.
    for table_name in (
        "research_explanation_snapshots", "research_explanation_views",
        "research_explanation_citations", "research_explanation_relations",
        "research_explanation_nodes", "research_visual_explanations",
    ):
        Base.metadata.tables[table_name].drop(db.engine, checkfirst=True)
    assert TABLES.isdisjoint(set(inspect(db.engine).get_table_names()))
    with db.session_factory() as session:
        for version, description in MIGRATIONS:
            if version == "0043":
                break
            session.add(SchemaMigration(version=version, description=description))
        session.commit()
    assert run_migrations(db) == ["0043", "0044", "0045", "0046", "0047", "0048", "0049", "0050", "0051", "0052", "0053"]
    status = migration_status(db)
    assert status["pending"] == [] and status["applied"][-1] == "0053"
    assert TABLES <= set(inspect(db.engine).get_table_names())
