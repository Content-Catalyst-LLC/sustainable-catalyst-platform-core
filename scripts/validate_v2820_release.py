#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.82.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.82.0' in cfg; assert 'peer_review_replication_rebuttal_enabled: bool = True' in cfg; assert 'SC_CORE_PEER_REVIEW_REPLICATION_REBUTTAL_ENABLED' in cfg
mod=ast.parse((R/"backend/app/migrations.py").read_text()); migrations=[]
for node in mod.body:
    if isinstance(node,ast.Assign) and any(getattr(t,"id",None)=="MIGRATIONS" for t in node.targets): migrations=ast.literal_eval(node.value)
assert migrations[-1][0]=="0086"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/peer_review_intelligence.py","backend/app/services/peer_review_intelligence.py","backend/tests/test_peer_review_replication_rebuttal_v2820.py","backend/tests/test_partial_0086_recovery_v2820.py","schemas/research-peer-review-replication-rebuttal-v1.schema.json","DEPLOY_PLATFORM_CORE_V2820_CONTABO.sh","PUSH_PLATFORM_CORE_V2820_FINAL.sh","PLATFORM_CORE_V2820_TERMINAL_COMMANDS.txt")
for item in required: assert (R/item).exists(),item
models=(R/"backend/app/models.py").read_text()
for table in ("research_peer_reviews_v282","research_peer_review_comments_v282","research_peer_review_responses_v282","research_replication_studies_v282","research_replication_attempts_v282","research_replication_comparisons_v282","research_rebuttals_v282","research_rebuttal_points_v282","research_peer_review_revisions_v282","research_peer_review_snapshots_v282"): assert table in models,table
main=(R/"backend/app/main.py").read_text(); assert "peer_review_intelligence" in main
service=(R/"backend/app/services/peer_review_intelligence.py").read_text()
for invariant in ('"generate_peer_review_by_core": False','"score_manuscript_quality_by_core": False','"infer_replication_success_by_core": False','"resolve_rebuttal_by_core": False','"decide_publication_by_core": False','"infer_truth_by_core": False','"summary_is_descriptive_only": True'): assert invariant in service,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.82.0" in wp; assert "SCPC_VERSION', '2.82.0'" in wp; assert "sc_platform_core_peer_review_status" in wp; assert "Stable tag: 2.82.0" in readme
assert 'version = "2.82.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.82.0"' in (R/"backend/public_sdk/javascript/package.json").read_text()
print(f"PASS - dependency-free release contract; migration 0086 chars={len(migrations[-1][1])}")
print("PASS - v2.82.0 Peer Review, Replication & Rebuttal release contract")
