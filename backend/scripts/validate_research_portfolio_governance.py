#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_portfolios as svc
db=Database("sqlite:///:memory:"); run_migrations(db); m=migration_status(db); assert "0089" in m["applied"] and m["pending"]==[],m
with db.session_factory() as session:
 r=svc.readiness(session); assert r["release"]=="2.85.0"; assert r["research_portfolio_registry_by_core"] is True; assert r["descriptive_portfolio_map_by_core"] is True
 for k in ("prioritize_programs_by_core","allocate_resources_by_core","allocate_funding_by_core","rank_programs_by_core","score_programs_by_core","optimize_portfolio_by_core","decide_governance_by_core","infer_strategic_value_by_core","forecast_program_success_by_core","close_risks_by_core","infer_truth_by_core"): assert r[k] is False,(k,r)
print("PASS - v2.85.0 research portfolio & institutional knowledge governance invariants")
