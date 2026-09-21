from app.database import Database
from app.migrations import run_migrations,migration_status
from app.models import ResearchProjectStateRecord,ResearchProjectStateVersionRecord

def test_partial_0096_recovery(tmp_path):
 db=Database("sqlite:///"+str(tmp_path/"partial.db")); ResearchProjectStateRecord.__table__.create(db.engine,checkfirst=True); ResearchProjectStateVersionRecord.__table__.create(db.engine,checkfirst=True); run_migrations(db); st=migration_status(db); assert "0096" in st["applied"] and st["pending"]==[]; names=set(__import__("sqlalchemy").inspect(db.engine).get_table_names()); expected={"research_project_states_v292","research_project_state_versions_v292","research_project_state_bindings_v292","research_project_state_dependencies_v292","research_project_state_environments_v292","research_project_state_checkpoints_v292","research_project_reconstruction_plans_v292","research_project_reconstruction_verifications_v292","research_project_state_revisions_v292","research_project_state_snapshots_v292"}; assert expected<=names
