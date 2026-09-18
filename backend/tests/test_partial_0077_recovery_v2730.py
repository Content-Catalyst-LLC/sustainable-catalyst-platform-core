from sqlalchemy import create_engine,text
from app.database import Database
from app.migrations import run_migrations,migration_status

def test_partial_0077_recovery(tmp_path):
    url=f"sqlite:///{tmp_path/'partial.db'}"; db=Database(url); run_migrations(db)
    names=['research_lineage_graphs','research_lineage_nodes','research_lineage_edges','research_lineage_activities','research_lineage_transformations','research_lineage_source_bindings','research_lineage_traces','research_lineage_snapshots']
    with db.engine.begin() as c:
        c.execute(text("DELETE FROM schema_migrations WHERE version='0077'"))
        c.execute(text('DROP TABLE research_lineage_traces'))
        c.execute(text('DROP TABLE research_lineage_snapshots'))
    applied=run_migrations(db); st=migration_status(db)
    assert '0077' in applied and '0077' in st['applied'] and st['pending']==[]
    with db.engine.begin() as c:
        for n in names:
            assert c.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),{'n':n}).scalar()==n
