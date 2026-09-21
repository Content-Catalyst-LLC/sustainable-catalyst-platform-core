#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import unified_inference as svc
db=Database("sqlite:///:memory:"); run_migrations(db); m=migration_status(db); assert "0092" in m["applied"] and m["pending"]==[],m
with db.session_factory() as session:
 r=svc.readiness(session); assert r["release"]=="2.88.0"; assert r["inference_registry_by_core"] is True; assert r["inference_lineage_by_core"] is True
 for k in ("classify_automatically_by_core","generate_inferences_by_core","infer_findings_by_core","infer_claims_by_core","infer_causality_by_core","compute_statistics_by_core","score_confidence_by_core","rank_evidence_by_core","resolve_contradictions_by_core","validate_inference_by_core","promote_speculation_by_core","determine_truth_by_core"): assert r[k] is False,(k,r)
print("PASS - v2.88.0 Unified Findings, Claims & Inference Engine invariants")
