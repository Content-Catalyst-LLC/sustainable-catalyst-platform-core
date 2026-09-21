#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_workflows as svc
db=Database("sqlite:///:memory:"); run_migrations(db); m=migration_status(db); assert "0094" in m["applied"] and m["pending"]==[],m
with db.session_factory() as session:
 r=svc.readiness(session); assert r["release"]=="2.90.0"; assert r["workflow_registry_by_core"] is True; assert r["apply_declared_transition_by_core"] is True
 for k in ("choose_research_path_by_core","autonomously_advance_workflow_by_core","execute_specialist_work_by_core","dispatch_external_handoff_by_core","infer_stage_completion_by_core","generate_findings_by_core","generate_claims_by_core","approve_scientific_validity_by_core","resolve_challenges_by_core","rank_research_paths_by_core","determine_truth_by_core"): assert r[k] is False,(k,r)
print("PASS - v2.90.0 Research Workflow & Orchestration Engine invariants")
