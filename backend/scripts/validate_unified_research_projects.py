from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import unified_research_projects as svc
import os
db=Database(os.environ.get('SC_CORE_DATABASE_URL','sqlite:///./platform_core.db')); run_migrations(db)
with db.session_factory() as s:
 r=svc.readiness(s)
 assert r['release']=='2.72.0' and r['contract']=='sc.research.unified-project.v1'
 for k in ('research_project_registry_by_core','question_registry_by_core','objective_registry_by_core','typed_component_registry_by_core','research_relationship_registry_by_core','research_provenance_registry_by_core','runtime_handoff_registry_by_core','immutable_project_snapshots_by_core'): assert r[k] is True,k
 for k in ('execute_analysis_by_core','generate_findings_by_core','promote_conclusion_by_core','infer_originality_by_core','automatic_truth_promotion','execute_handoff_by_core'): assert r[k] is False,k
assert migration_status(db)['pending']==[]
print('PASS - Platform Core v2.72.0 Unified Research Project Object Model invariants')
