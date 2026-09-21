#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_protocols as svc
db=Database("sqlite:///:memory:"); run_migrations(db); m=migration_status(db); assert "0090" in m["applied"] and m["pending"]==[],m
with db.session_factory() as session:
 r=svc.readiness(session); assert r["release"]=="2.86.0"; assert r["universal_protocol_registry_by_core"] is True; assert r["protocol_lineage_by_core"] is True
 for k in ("execute_protocol_by_core","recruit_participants_by_core","randomize_by_core","collect_data_by_core","acquire_evidence_by_core","run_analysis_by_core","compute_results_by_core","infer_results_by_core","infer_causality_by_core","judge_method_quality_by_core","certify_ethics_by_core","approve_protocol_by_core","infer_truth_by_core"): assert r[k] is False,(k,r)
print("PASS - v2.86.0 Scientific Study & Investigation Protocol Model invariants")
