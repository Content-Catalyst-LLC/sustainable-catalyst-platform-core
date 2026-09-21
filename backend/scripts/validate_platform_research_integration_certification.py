#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import platform_research_certification as svc
db=Database("sqlite:///:memory:"); run_migrations(db); s=db.session_factory(); r=svc.readiness(s); st=migration_status(db)
assert r["release"]=="2.97.0" and "0101" in st["applied"] and st["pending"]==[]
for k in ("certification_suite_registry_by_core","certification_product_registry_by_core","conformance_case_registry_by_core","conformance_run_registry_by_core","conformance_result_registry_by_core","exchange_check_registry_by_core","trace_check_registry_by_core","reproduction_check_registry_by_core","certification_evidence_registry_by_core","certification_finding_registry_by_core","revision_history_by_core","immutable_certification_snapshots_by_core"): assert r[k] is True,k
for k in svc.FORBIDDEN: assert r[k] is False,k
print("PASS - Platform Core v2.97.0 Platform Research Integration Certification invariants")
