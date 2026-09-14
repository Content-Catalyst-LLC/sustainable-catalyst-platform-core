import sqlite3
from app.database import Database
from app.migrations import run_migrations, migration_status

V248_TABLES={
 'forensic_quantitative_reconstructions','forensic_quantitative_measurements','forensic_quantitative_assumptions','forensic_quantitative_parameters',
 'forensic_quantitative_scenarios','forensic_quantitative_handoffs','forensic_quantitative_result_bindings','forensic_quantitative_reproduction_packages'
}
def tables(path):
    con=sqlite3.connect(path)
    try: return {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    finally: con.close()

def test_pristine_upgrade_to_0052(tmp_path):
    db_path=tmp_path/'pristine.db'; db=Database(f'sqlite:///{db_path}'); applied=run_migrations(db)
    assert '0052' in applied and migration_status(db)['pending']==[] and V248_TABLES.issubset(tables(db_path))

def test_safe_partial_0052_tables_then_ledger_repair(tmp_path):
    db_path=tmp_path/'partial.db'; db=Database(f'sqlite:///{db_path}'); run_migrations(db)
    con=sqlite3.connect(db_path)
    try: con.execute("delete from schema_migrations where version='0052'"); con.commit()
    finally: con.close()
    assert V248_TABLES.issubset(tables(db_path)); applied=run_migrations(db); assert applied==['0052'] and migration_status(db)['pending']==[]
