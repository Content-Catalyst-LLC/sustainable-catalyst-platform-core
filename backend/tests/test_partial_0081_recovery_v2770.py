from app.config import Settings
from app.main import create_app
from sqlalchemy import inspect,text

def test_partial_0081_recovery(tmp_path):
 app=create_app(Settings(database_url='sqlite:///'+str(tmp_path/'p.db')));db=app.state.database
 tables={'research_findings','research_finding_revisions','research_interpretations','research_claims_v277','research_claim_revisions_v277','research_evidence_links_v277','research_derivation_links_v277','research_contradictions_v277','research_intelligence_snapshots_v277'}
 assert tables.issubset(set(inspect(db.engine).get_table_names()))
 with db.engine.begin() as c:c.execute(text("DELETE FROM schema_migrations WHERE version='0081'"))
 from app.migrations import run_migrations,migration_status
 run_migrations(db);assert '0081' in migration_status(db)['applied'];assert migration_status(db)['pending']==[]
