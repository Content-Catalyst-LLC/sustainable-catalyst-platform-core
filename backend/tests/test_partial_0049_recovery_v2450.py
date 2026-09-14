from sqlalchemy import inspect
from app.database import Base, Database
from app.migrations import MIGRATIONS, migration_status, run_migrations
from app.models import SchemaMigration

TABLES={'forensic_events','forensic_event_evidence_bindings','forensic_event_participants','forensic_event_relations','forensic_event_reconstructions','forensic_timeline_views','forensic_timeline_snapshots'}

def _ledger_to(db, stop):
    with db.session_factory() as session:
        for version,description in MIGRATIONS:
            if version==stop: break
            session.add(SchemaMigration(version=version,description=description))
        session.commit()

def test_partial_0049_table_state_recovers_by_recording_metadata(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'partial0049.db'}"); Base.metadata.create_all(db.engine); assert TABLES <= set(inspect(db.engine).get_table_names()); _ledger_to(db,'0049')
    assert run_migrations(db)==['0049','0050']; status=migration_status(db); assert status['pending']==[] and status['applied'][-1]=='0050'

def test_pristine_pre_0049_schema_upgrades_additively(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'pre0049.db'}"); Base.metadata.create_all(db.engine)
    for name in sorted(TABLES,reverse=True): Base.metadata.tables[name].drop(db.engine,checkfirst=True)
    _ledger_to(db,'0049'); assert run_migrations(db)==['0049','0050']; status=migration_status(db); assert status['pending']==[] and status['applied'][-1]=='0050'; assert TABLES <= set(inspect(db.engine).get_table_names())
