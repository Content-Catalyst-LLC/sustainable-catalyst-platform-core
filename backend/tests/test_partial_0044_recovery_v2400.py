from sqlalchemy import inspect
from app.database import Base, Database
from app.migrations import MIGRATIONS, migration_status, run_migrations
from app.models import SchemaMigration

TABLES = {
    "cross_product_visual_research_objects", "cross_product_visual_research_members",
    "cross_product_visual_research_relations", "cross_product_visual_research_views",
    "cross_product_visual_research_snapshots",
}


def test_partial_0044_table_state_recovers_by_recording_short_metadata(tmp_path):
    db = Database(f"sqlite:///{tmp_path/'partial0044.db'}")
    Base.metadata.create_all(db.engine)
    assert TABLES <= set(inspect(db.engine).get_table_names())
    with db.session_factory() as session:
        for version, description in MIGRATIONS:
            if version == "0044": break
            session.add(SchemaMigration(version=version, description=description))
        session.commit(); assert session.get(SchemaMigration, "0044") is None
    assert run_migrations(db) == ["0044", "0045", "0046"]
    with db.session_factory() as session:
        row = session.get(SchemaMigration, "0044"); assert row and len(row.description) <= 300
    status = migration_status(db); assert status["pending"] == [] and status["applied"][-1] == "0046"
    assert TABLES <= set(inspect(db.engine).get_table_names())


def test_pristine_pre_0044_schema_upgrades_additively(tmp_path):
    db = Database(f"sqlite:///{tmp_path/'pre0044.db'}")
    Base.metadata.create_all(db.engine)
    for table_name in (
        "cross_product_visual_research_snapshots", "cross_product_visual_research_views",
        "cross_product_visual_research_relations", "cross_product_visual_research_members",
        "cross_product_visual_research_objects",
    ):
        Base.metadata.tables[table_name].drop(db.engine, checkfirst=True)
    assert TABLES.isdisjoint(set(inspect(db.engine).get_table_names()))
    with db.session_factory() as session:
        for version, description in MIGRATIONS:
            if version == "0044": break
            session.add(SchemaMigration(version=version, description=description))
        session.commit()
    assert run_migrations(db) == ["0044", "0045", "0046"]
    status = migration_status(db)
    assert status["pending"] == [] and status["applied"][-1] == "0046"
    assert TABLES <= set(inspect(db.engine).get_table_names())
