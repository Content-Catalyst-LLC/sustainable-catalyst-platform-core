from sqlalchemy import text
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status

def test_partial_0078_recovery(tmp_path):
 db=Database('sqlite:///'+str(tmp_path/'p.db')); run_migrations(db)
 names=['research_methodologies','research_methodology_versions','research_method_variables','research_method_assumptions','research_method_parameters','research_execution_environments','research_analysis_runs','research_analysis_run_inputs','research_analysis_run_outputs','research_methodology_snapshots']
 with db.engine.begin() as c:
  c.execute(text("DELETE FROM schema_migrations WHERE version='0078'")); c.execute(text('DROP TABLE research_analysis_run_outputs')); c.execute(text('DROP TABLE research_methodology_snapshots'))
 run_migrations(db); st=migration_status(db); assert '0078' in st['applied'] and st['pending']==[]
 with db.engine.connect() as c:
  for n in names: assert c.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),{'n':n}).scalar()==n
