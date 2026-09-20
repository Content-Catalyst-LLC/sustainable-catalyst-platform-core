#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import cross_study_synthesis as svc

db=Database("sqlite:///:memory:"); run_migrations(db); m=migration_status(db); assert "0087" in m["applied"] and m["pending"]==[],m
with db.session_factory() as session:
    r=svc.readiness(session); assert r["release"]=="2.83.0"; assert r["evidence_synthesis_registry_by_core"] is True; assert r["externally_computed_meta_analysis_registry_by_core"] is True
    for k in ("search_literature_by_core","decide_study_inclusion_by_core","compute_effect_size_by_core","pool_estimates_by_core","score_study_quality_by_core","infer_bias_by_core","rank_evidence_by_core","infer_causality_by_core","generate_synthesis_conclusion_by_core","infer_truth_by_core"): assert r[k] is False,(k,r)
print("PASS - v2.83.0 cross-study evidence synthesis invariants")
