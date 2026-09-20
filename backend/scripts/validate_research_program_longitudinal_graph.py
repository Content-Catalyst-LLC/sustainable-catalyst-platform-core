#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_programs as svc

db=Database("sqlite:///:memory:"); run_migrations(db); m=migration_status(db); assert "0088" in m["applied"] and m["pending"]==[],m
with db.session_factory() as session:
    r=svc.readiness(session); assert r["release"]=="2.84.0"; assert r["research_program_registry_by_core"] is True; assert r["longitudinal_knowledge_node_registry_by_core"] is True
    for k in ("prioritize_research_by_core","allocate_funding_by_core","rank_projects_by_core","auto_link_knowledge_graph_by_core","infer_research_direction_by_core","infer_causality_by_core","forecast_program_success_by_core","resolve_evidence_gaps_by_core","infer_knowledge_truth_by_core","infer_truth_by_core"): assert r[k] is False,(k,r)
print("PASS - v2.84.0 research program & longitudinal knowledge graph invariants")
