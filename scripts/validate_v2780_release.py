#!/usr/bin/env python3
from pathlib import Path
import ast

R = Path(__file__).resolve().parents[1]

cfg = (R / "backend/app/config.py").read_text()
assert 'version: str = "2.78.0"' in cfg
assert 'SustainableCatalystPlatformCore/2.78.0' in cfg
assert 'hypothesis_competing_explanation_engine_enabled: bool = True' in cfg
assert 'SC_CORE_HYPOTHESIS_COMPETING_EXPLANATION_ENGINE_ENABLED' in cfg

mod = ast.parse((R / "backend/app/migrations.py").read_text())
migrations = []
for node in mod.body:
    if isinstance(node, ast.Assign) and any(getattr(target, "id", None) == "MIGRATIONS" for target in node.targets):
        migrations = ast.literal_eval(node.value)
assert migrations[-1][0] == "0082"
assert len(migrations[-1][1]) <= 300

required = (
    "backend/app/routers/hypothesis_intelligence.py",
    "backend/app/services/hypothesis_intelligence.py",
    "backend/tests/test_hypothesis_competing_explanation_v2780.py",
    "backend/tests/test_partial_0082_recovery_v2780.py",
    "schemas/research-hypothesis-competing-explanation-v1.schema.json",
    "DEPLOY_PLATFORM_CORE_V2780_CONTABO.sh",
    "PUSH_PLATFORM_CORE_V2780_FINAL.sh",
    "PLATFORM_CORE_V2780_TERMINAL_COMMANDS.txt",
)
for item in required:
    assert (R / item).exists(), item

models = (R / "backend/app/models.py").read_text()
for table in (
    "research_hypothesis_sets_v278",
    "research_hypotheses_v278",
    "research_hypothesis_revisions_v278",
    "research_hypothesis_evidence_assessments_v278",
    "research_hypothesis_predictions_v278",
    "research_hypothesis_assumptions_v278",
    "research_hypothesis_relations_v278",
    "research_hypothesis_discrimination_gaps_v278",
    "research_hypothesis_snapshots_v278",
):
    assert table in models, table

main = (R / "backend/app/main.py").read_text()
assert "hypothesis_intelligence" in main
service = (R / "backend/app/services/hypothesis_intelligence.py").read_text()
for invariant in (
    '"rank_hypotheses_by_core": False',
    '"select_best_hypothesis_by_core": False',
    '"infer_truth_by_core": False',
    '"comparison_is_descriptive_only": True',
):
    assert invariant in service, invariant

wp = (R / "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text()
readme = (R / "wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text()
assert "Version: 2.78.0" in wp
assert "SCPC_VERSION', '2.78.0'" in wp
assert "sc_platform_core_hypothesis_engine_status" in wp
assert "Stable tag: 2.78.0" in readme

pyproject = (R / "backend/public_sdk/python/pyproject.toml").read_text()
package = (R / "backend/public_sdk/javascript/package.json").read_text()
assert 'version = "2.78.0"' in pyproject
assert '"version": "2.78.0"' in package

print(f"PASS - dependency-free release contract; migration ledger max=300, 0082 chars={len(migrations[-1][1])}")
print("PASS - v2.78.0 Hypothesis & Competing Explanation Engine release contract")
