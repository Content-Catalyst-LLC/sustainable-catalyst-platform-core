#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import unified_research_scientific_runtime as svc
db=Database("sqlite:///:memory:"); run_migrations(db); s=db.session_factory(); r=svc.readiness(s); st=migration_status(db)
assert r["release"]=="3.0.0" and "0102" in st["applied"] and st["pending"]==[]
for k in ("reference_first_runtime_by_core","unified_session_registry_by_core","research_object_binding_by_core","product_context_binding_by_core","computation_execution_binding_by_core","investigation_binding_by_core","visual_reasoning_binding_by_core","validation_challenge_binding_by_core","research_package_binding_by_core","cross_product_handoff_binding_by_core","milestone_registry_by_core","revision_history_by_core","immutable_runtime_snapshots_by_core","underlying_objects_remain_authoritative_in_specialist_layers"): assert r[k] is True,k
for k in svc.FORBIDDEN: assert r[k] is False,k
print("PASS - Platform Core v3.0.0 Unified Research, Scientific Computing & Investigation Runtime invariants")
