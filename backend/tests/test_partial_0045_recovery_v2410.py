from sqlalchemy import inspect
from app.database import Base, Database
from app.migrations import MIGRATIONS, migration_status, run_migrations
from app.models import SchemaMigration

TABLES={
"reproducible_visual_knowledge_packages","reproducible_visual_knowledge_inputs","reproducible_visual_knowledge_environments",
"reproducible_visual_knowledge_replay_plans","reproducible_visual_knowledge_verifications","reproducible_visual_knowledge_snapshots"}


def test_partial_0045_table_state_recovers_by_recording_metadata(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'partial0045.db'}"); Base.metadata.create_all(db.engine); assert TABLES <= set(inspect(db.engine).get_table_names())
    with db.session_factory() as session:
        for version,description in MIGRATIONS:
            if version=='0045': break
            session.add(SchemaMigration(version=version,description=description))
        session.commit(); assert session.get(SchemaMigration,'0045') is None
    assert run_migrations(db)==['0045','0046','0047']
    with db.session_factory() as session:
        row=session.get(SchemaMigration,'0045'); assert row and len(row.description)<=300
    status=migration_status(db); assert status['pending']==[] and status['applied'][-1]=='0047'


def test_pristine_pre_0045_schema_upgrades_additively(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'pre0045.db'}"); Base.metadata.create_all(db.engine)
    for name in sorted(TABLES, reverse=True): Base.metadata.tables[name].drop(db.engine,checkfirst=True)
    assert TABLES.isdisjoint(set(inspect(db.engine).get_table_names()))
    with db.session_factory() as session:
        for version,description in MIGRATIONS:
            if version=='0045': break
            session.add(SchemaMigration(version=version,description=description))
        session.commit()
    assert run_migrations(db)==['0045','0046','0047']; status=migration_status(db); assert status['pending']==[] and status['applied'][-1]=='0047'; assert TABLES <= set(inspect(db.engine).get_table_names())
