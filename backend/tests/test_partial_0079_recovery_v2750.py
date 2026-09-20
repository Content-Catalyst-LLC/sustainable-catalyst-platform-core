from app.config import Settings
from app.main import create_app
from sqlalchemy import inspect,text
def test_partial_0079_recovery(tmp_path):
 app=create_app(Settings(database_url='sqlite:///'+str(tmp_path/'p.db')));db=app.state.database
 tables={'reproducible_research_packages','reproducible_research_package_components','reproducible_research_package_artifacts','reproducible_research_package_environments','reproducible_research_replay_plans','reproducible_research_verifications','reproducible_research_reviews','reproducible_research_snapshots'}
 assert tables.issubset(set(inspect(db.engine).get_table_names()))
 with db.engine.begin() as c:c.execute(text("DELETE FROM schema_migrations WHERE version='0079'"))
 from app.migrations import run_migrations,migration_status
 run_migrations(db);assert '0079' in migration_status(db)['applied'];assert migration_status(db)['pending']==[]
