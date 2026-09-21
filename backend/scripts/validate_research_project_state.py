#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_project_state as svc
from sqlalchemy import inspect
db=Database("sqlite:///:memory:"); run_migrations(db); st=migration_status(db); assert "0096" in st["applied"] and st["pending"]==[]
names=set(inspect(db.engine).get_table_names()); expected={"research_project_states_v292","research_project_state_versions_v292","research_project_state_bindings_v292","research_project_state_dependencies_v292","research_project_state_environments_v292","research_project_state_checkpoints_v292","research_project_reconstruction_plans_v292","research_project_reconstruction_verifications_v292","research_project_state_revisions_v292","research_project_state_snapshots_v292"}; assert expected<=names
with db.session_factory() as s:
 d=svc.readiness(s); assert d["release"]=="2.92.0" and d["historical_state_reconstruction_manifest_by_core"] is True and d["replay_executions_by_core"] is False and d["determine_truth_by_core"] is False
print("PASS - Platform Core v2.92.0 Research Project State, Versioning & Reproducibility invariants")
