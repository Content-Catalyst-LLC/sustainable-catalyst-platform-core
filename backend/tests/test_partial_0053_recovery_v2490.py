import sqlite3
from app.database import Database
from app.migrations import run_migrations, migration_status

V249_TABLES={
 'forensic_statements','forensic_statement_source_contexts','forensic_documents','forensic_document_assertions',
 'forensic_statement_claim_bindings','forensic_statement_relations','forensic_temporal_consistency_assessments','forensic_documentary_snapshots'
}
def tables(path):
    con=sqlite3.connect(path)
    try: return {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    finally: con.close()

def test_pristine_upgrade_to_0053(tmp_path):
    db_path=tmp_path/'pristine.db'; db=Database(f'sqlite:///{db_path}'); applied=run_migrations(db)
    assert '0053' in applied and '0054' in applied and '0055' in applied and '0056' in applied and migration_status(db)['pending']==[] and V249_TABLES.issubset(tables(db_path))

def test_safe_partial_0053_tables_then_ledger_repair(tmp_path):
    db_path=tmp_path/'partial.db'; db=Database(f'sqlite:///{db_path}'); run_migrations(db)
    con=sqlite3.connect(db_path)
    try: con.execute("delete from schema_migrations where version='0053'"); con.commit()
    finally: con.close()
    assert V249_TABLES.issubset(tables(db_path)); applied=run_migrations(db); assert applied==['0053'] and migration_status(db)['pending']==[]
