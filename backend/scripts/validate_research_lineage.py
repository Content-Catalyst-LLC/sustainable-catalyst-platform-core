from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_lineage as svc
import os
db=Database(os.environ.get('SC_CORE_DATABASE_URL','sqlite:///./platform_core.db')); run_migrations(db)
with db.session_factory() as s:
 r=svc.readiness(s)
 assert r['release']=='2.73.0' and r['contract']=='sc.research.lineage-graph.v1'
 for k in ('lineage_graph_registry_by_core','lineage_node_registry_by_core','explicit_lineage_edge_registry_by_core','provenance_activity_registry_by_core','transformation_registry_by_core','source_binding_registry_by_core','deterministic_declared_trace_by_core','immutable_lineage_snapshots_by_core'): assert r[k] is True,k
 for k in ('infer_missing_edges_by_core','infer_causality_by_core','generate_findings_by_core','promote_truth_by_core','infer_originality_by_core','execute_analysis_by_core','alter_source_evidence_by_core'): assert r[k] is False,k
assert migration_status(db)['pending']==[]
print('PASS - Platform Core v2.73.0 Research Lineage & Provenance Graph invariants')
