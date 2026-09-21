#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import computation_lineage as svc
db=Database("sqlite:///:memory:"); run_migrations(db); m=migration_status(db); assert "0091" in m["applied"] and m["pending"]==[],m
with db.session_factory() as session:
 r=svc.readiness(session); assert r["release"]=="2.87.0"; assert r["execution_registry_by_core"] is True; assert r["execution_lineage_by_core"] is True
 for k in ("execute_code_by_core","run_python_by_core","run_r_by_core","run_julia_by_core","run_workbench_by_core","train_ml_by_core","transform_data_by_core","compute_statistics_by_core","fit_models_by_core","generate_outputs_by_core","infer_findings_by_core","infer_claims_by_core","validate_results_by_core","infer_reproducibility_by_core","infer_truth_by_core"): assert r[k] is False,(k,r)
print("PASS - v2.87.0 Computation, Analysis & Execution Lineage invariants")
