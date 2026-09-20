#!/usr/bin/env python3
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from sqlalchemy import inspect
app=create_app(Settings(database_url='sqlite:////tmp/sc-core-v2760-validator.db'))
db=app.state.database
tables={'research_notebooks','research_notebook_sections','research_notebook_entries','research_notebook_bindings','research_notebook_citations','research_analytical_narratives','research_analytical_narrative_blocks','research_notebook_revisions','research_notebook_snapshots'}
assert tables.issubset(set(inspect(db.engine).get_table_names()))
s=migration_status(db);assert '0080' in s['applied'] and s['pending']==[],s
print('PASS - Platform Core v2.76.0 Research Notebook & Analytical Narrative invariants')
