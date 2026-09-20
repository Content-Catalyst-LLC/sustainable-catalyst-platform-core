from app.config import Settings
from app.database import Database
from app.migrations import run_migrations, migration_status
from app.services import research_conclusions as svc

db=Database(Settings.from_env().database_url); run_migrations(db)
with db.session_factory() as s:
    r=svc.readiness(s)
    assert r["release"]=="2.80.0" and r["contract"]=="sc.research.decision-trace-conclusion-governance.v1"
    assert r["researcher_authored_conclusion_registry_by_core"] is True
    assert r["descriptive_governance_summary_by_core"] is True
    assert r["generate_conclusion_by_core"] is False and r["choose_conclusion_by_core"] is False
    assert r["certify_conclusion_by_core"] is False and r["infer_truth_by_core"] is False
assert "0084" in migration_status(db)["applied"]
print("PASS - Platform Core v2.80.0 Research Decision Trace & Conclusion Governance invariants")
