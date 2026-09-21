#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import unified_research_runtime as svc

db=Database("sqlite:///:memory:"); run_migrations(db); s=db.session_factory()
r=svc.readiness(s)
assert r["release"]=="2.96.0" and "0100" in migration_status(db)["applied"] and migration_status(db)["pending"]==[]
for k in ("runtime_contract_registry_by_core","runtime_object_type_registry_by_core","runtime_operation_registry_by_core","runtime_capability_registry_by_core","product_binding_registry_by_core","exchange_envelope_registry_by_core","invocation_lineage_registry_by_core","result_binding_registry_by_core","compatibility_assertion_registry_by_core","revision_history_by_core","immutable_runtime_snapshots_by_core"): assert r[k] is True,k
for k in svc.FORBIDDEN: assert r[k] is False,k
print("PASS - Platform Core v2.96.0 Unified Research Runtime Contract invariants")
