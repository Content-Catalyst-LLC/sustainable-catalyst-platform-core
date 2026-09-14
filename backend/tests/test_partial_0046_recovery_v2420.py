from sqlalchemy import inspect
from app.database import Base, Database
from app.migrations import MIGRATIONS, migration_status, run_migrations
from app.models import SchemaMigration

TABLES={
'forensic_investigations','forensic_objects','forensic_evidence_items','forensic_evidence_source_bindings',
'forensic_provenance_activities','forensic_object_relations','forensic_snapshots'}


def test_partial_0046_table_state_recovers_by_recording_metadata(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'partial0046.db'}"); Base.metadata.create_all(db.engine); assert TABLES <= set(inspect(db.engine).get_table_names())
    with db.session_factory() as session:
        for version,description in MIGRATIONS:
            if version=='0046': break
            session.add(SchemaMigration(version=version,description=description))
        session.commit(); assert session.get(SchemaMigration,'0046') is None
    assert run_migrations(db)==['0046','0047','0048','0049','0050','0051','0052','0053','0054','0055']
    status=migration_status(db); assert status['pending']==[] and status['applied'][-1]=='0055'


def test_pristine_pre_0046_schema_upgrades_additively(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'pre0046.db'}"); Base.metadata.create_all(db.engine)
    for name in sorted(TABLES,reverse=True): Base.metadata.tables[name].drop(db.engine,checkfirst=True)
    with db.session_factory() as session:
        for version,description in MIGRATIONS:
            if version=='0046': break
            session.add(SchemaMigration(version=version,description=description))
        session.commit()
    assert run_migrations(db)==['0046','0047','0048','0049','0050','0051','0052','0053','0054','0055']; status=migration_status(db); assert status['pending']==[] and status['applied'][-1]=='0055'; assert TABLES <= set(inspect(db.engine).get_table_names())
