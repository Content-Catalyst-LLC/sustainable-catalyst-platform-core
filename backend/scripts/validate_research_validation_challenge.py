#!/usr/bin/env python3
from sqlalchemy import inspect
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_validation_challenge as svc
db=Database("sqlite:///:memory:"); run_migrations(db); st=migration_status(db); assert "0098" in st["applied"] and st["pending"]==[]
expected={"research_validation_challenges_v294","research_validation_targets_v294","research_alternative_hypotheses_v294","research_contradiction_tests_v294","research_counterevidence_v294","research_sensitivity_checks_v294","research_robustness_checks_v294","research_replication_attempts_v294","research_reviewer_challenges_v294","research_challenge_responses_v294","research_validation_revisions_v294","research_validation_snapshots_v294"}; assert expected<=set(inspect(db.engine).get_table_names())
with db.session_factory() as s:
 d=svc.readiness(s); assert d["release"]=="2.94.0" and d["validation_challenge_registry_by_core"] is True and d["resolve_hypotheses_by_core"] is False and d["certify_validity_by_core"] is False and d["determine_truth_by_core"] is False
print("PASS - Platform Core v2.94.0 Research Validation & Challenge Engine invariants")
