from sqlalchemy import inspect
from app.database import Base, Database
from app.migrations import MIGRATIONS, migration_status, run_migrations
from app.models import SchemaMigration

TABLES={'forensic_custodians','forensic_custody_events','forensic_evidence_seals','forensic_integrity_checks','forensic_custody_continuity_assessments','forensic_custody_snapshots'}


def _ledger_to(db, stop):
    with db.session_factory() as session:
        for version,description in MIGRATIONS:
            if version==stop: break
            session.add(SchemaMigration(version=version,description=description))
        session.commit()


def test_partial_0047_table_state_recovers_by_recording_metadata(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'partial0047.db'}"); Base.metadata.create_all(db.engine); assert TABLES <= set(inspect(db.engine).get_table_names()); _ledger_to(db,'0047')
    assert run_migrations(db)==['0047','0048','0049','0050','0051','0052','0053','0054','0055','0056','0057']; status=migration_status(db); assert status['pending']==[] and status['applied'][-1]=='0057'


def test_pristine_pre_0047_schema_upgrades_additively(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'pre0047.db'}"); Base.metadata.create_all(db.engine)
    for name in sorted(TABLES,reverse=True): Base.metadata.tables[name].drop(db.engine,checkfirst=True)
    _ledger_to(db,'0047'); assert run_migrations(db)==['0047','0048','0049','0050','0051','0052','0053','0054','0055','0056','0057']; status=migration_status(db); assert status['pending']==[] and status['applied'][-1]=='0057'; assert TABLES <= set(inspect(db.engine).get_table_names())
