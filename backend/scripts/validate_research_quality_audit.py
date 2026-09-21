#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_quality_audit as svc
db=Database("sqlite:///:memory:"); run_migrations(db); m=migration_status(db); assert "0093" in m["applied"] and m["pending"]==[],m
with db.session_factory() as session:
 r=svc.readiness(session); assert r["release"]=="2.89.0"; assert r["quality_audit_registry_by_core"] is True; assert r["audit_lineage_by_core"] is True
 for k in ("infer_bias_by_core","score_research_quality_by_core","rank_studies_by_core","determine_method_validity_by_core","infer_confounding_by_core","determine_causal_validity_by_core","resolve_contradictions_by_core","verify_citation_support_by_core","certify_reproducibility_by_core","certify_ethics_by_core","reject_research_by_core","determine_truth_by_core"): assert r[k] is False,(k,r)
print("PASS - v2.89.0 Research Quality, Bias & Methodological Audit Engine invariants")
