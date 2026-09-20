from app.config import Settings
from app.main import create_app
from sqlalchemy import inspect,text
def test_partial_0080_recovery(tmp_path):
 app=create_app(Settings(database_url='sqlite:///'+str(tmp_path/'p.db')));db=app.state.database
 tables={'research_notebooks','research_notebook_sections','research_notebook_entries','research_notebook_bindings','research_notebook_citations','research_analytical_narratives','research_analytical_narrative_blocks','research_notebook_revisions','research_notebook_snapshots'}
 assert tables.issubset(set(inspect(db.engine).get_table_names()))
 with db.engine.begin() as c:c.execute(text("DELETE FROM schema_migrations WHERE version='0080'"))
 from app.migrations import run_migrations,migration_status
 run_migrations(db);assert '0080' in migration_status(db)['applied'];assert migration_status(db)['pending']==[]
