import sqlite3
from app.database import Database
from app.migrations import run_migrations, migration_status

V250_TABLES={
 'forensic_research_graphs','forensic_research_graph_nodes','forensic_research_graph_edges','forensic_research_graph_views',
 'forensic_research_graph_handoffs','forensic_research_graph_snapshots','forensic_research_graph_packages'
}
def tables(path):
    con=sqlite3.connect(path)
    try: return {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    finally: con.close()

def test_pristine_upgrade_to_0054(tmp_path):
    db_path=tmp_path/'pristine.db'; db=Database(f'sqlite:///{db_path}'); applied=run_migrations(db)
    assert '0054' in applied and '0055' in applied and migration_status(db)['pending']==[] and V250_TABLES.issubset(tables(db_path))

def test_safe_partial_0054_tables_then_ledger_repair(tmp_path):
    db_path=tmp_path/'partial.db'; db=Database(f'sqlite:///{db_path}'); run_migrations(db)
    con=sqlite3.connect(db_path)
    try: con.execute("delete from schema_migrations where version='0054'"); con.commit()
    finally: con.close()
    assert V250_TABLES.issubset(tables(db_path)); applied=run_migrations(db); assert applied==['0054'] and migration_status(db)['pending']==[]
