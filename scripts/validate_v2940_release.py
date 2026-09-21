#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.94.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.94.0' in cfg; assert 'research_validation_challenge_engine_enabled: bool = True' in cfg; assert 'SC_CORE_RESEARCH_VALIDATION_CHALLENGE_ENGINE_ENABLED' in cfg
mtext=(R/"backend/app/migrations.py").read_text(); tree=ast.parse(mtext); migrations=None
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value); break
assert migrations and migrations[-1][0]=="0098"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/research_validation_challenge.py","backend/app/services/research_validation_challenge.py","backend/tests/test_research_validation_challenge_v2940.py","backend/tests/test_partial_0098_recovery_v2940.py","backend/scripts/validate_research_validation_challenge.py","schemas/research-validation-challenge-v1.schema.json","DEPLOY_PLATFORM_CORE_V2940_CONTABO.sh","PUSH_PLATFORM_CORE_V2940_FINAL.sh","PLATFORM_CORE_V2940_TERMINAL_COMMANDS.txt")
for f in required: assert (R/f).exists(),f
models=(R/"backend/app/models.py").read_text()
for table in ("research_validation_challenges_v294","research_validation_targets_v294","research_alternative_hypotheses_v294","research_contradiction_tests_v294","research_counterevidence_v294","research_sensitivity_checks_v294","research_robustness_checks_v294","research_replication_attempts_v294","research_reviewer_challenges_v294","research_challenge_responses_v294","research_validation_revisions_v294","research_validation_snapshots_v294"): assert table in models,table
svc=(R/"backend/app/services/research_validation_challenge.py").read_text()
for invariant in ('resolve_hypotheses_by_core','rank_hypotheses_by_core','declare_winner_by_core','certify_validity_by_core','certify_replication_by_core','infer_contradiction_by_core','infer_counterevidence_by_core','execute_sensitivity_by_core','execute_robustness_by_core','execute_replication_by_core','dismiss_challenges_by_core','determine_truth_by_core','challenge_state_is_declared_not_core_decided'): assert invariant in svc,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.94.0" in wp; assert "SCPC_VERSION', '2.94.0'" in wp; assert "sc_platform_core_research_validation_challenge_status" in wp; assert "Stable tag: 2.94.0" in readme
assert 'version = "2.94.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.94.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "researchValidationChallengeBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "research_validation_challenge_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0098 chars={len(migrations[-1][1])}")
print("PASS - v2.94.0 Research Validation & Challenge Engine release contract")
