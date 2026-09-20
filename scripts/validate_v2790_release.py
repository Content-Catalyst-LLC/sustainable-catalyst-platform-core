#!/usr/bin/env python3
from pathlib import Path
import ast

R = Path(__file__).resolve().parents[1]

cfg = (R / "backend/app/config.py").read_text()
assert 'version: str = "2.79.0"' in cfg
assert 'SustainableCatalystPlatformCore/2.79.0' in cfg
assert 'research_argument_evidentiary_synthesis_enabled: bool = True' in cfg
assert 'SC_CORE_RESEARCH_ARGUMENT_EVIDENTIARY_SYNTHESIS_ENABLED' in cfg

mod = ast.parse((R / "backend/app/migrations.py").read_text())
migrations = []
for node in mod.body:
    if isinstance(node, ast.Assign) and any(getattr(target, "id", None) == "MIGRATIONS" for target in node.targets):
        migrations = ast.literal_eval(node.value)
assert migrations[-1][0] == "0083"
assert len(migrations[-1][1]) <= 300

required = (
    "backend/app/routers/research_arguments.py",
    "backend/app/services/research_arguments.py",
    "backend/tests/test_research_argument_evidentiary_synthesis_v2790.py",
    "backend/tests/test_partial_0083_recovery_v2790.py",
    "schemas/research-argument-evidentiary-synthesis-v1.schema.json",
    "DEPLOY_PLATFORM_CORE_V2790_CONTABO.sh",
    "PUSH_PLATFORM_CORE_V2790_FINAL.sh",
    "PLATFORM_CORE_V2790_TERMINAL_COMMANDS.txt",
)
for item in required:
    assert (R / item).exists(), item

models = (R / "backend/app/models.py").read_text()
for table in (
    "research_arguments_v279",
    "research_argument_nodes_v279",
    "research_argument_edges_v279",
    "research_evidentiary_syntheses_v279",
    "research_synthesis_components_v279",
    "research_counterarguments_v279",
    "research_argument_tensions_v279",
    "research_argument_revisions_v279",
    "research_argument_snapshots_v279",
):
    assert table in models, table

main = (R / "backend/app/main.py").read_text()
assert "research_arguments" in main
service = (R / "backend/app/services/research_arguments.py").read_text()
for invariant in (
    '"generate_argument_by_core": False',
    '"generate_synthesis_by_core": False',
    '"score_evidence_by_core": False',
    '"rank_arguments_by_core": False',
    '"infer_truth_by_core": False',
    '"coverage_is_descriptive_only": True',
):
    assert invariant in service, invariant

wp = (R / "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text()
readme = (R / "wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text()
assert "Version: 2.79.0" in wp
assert "SCPC_VERSION', '2.79.0'" in wp
assert "sc_platform_core_research_argument_status" in wp
assert "Stable tag: 2.79.0" in readme

pyproject = (R / "backend/public_sdk/python/pyproject.toml").read_text()
package = (R / "backend/public_sdk/javascript/package.json").read_text()
assert 'version = "2.79.0"' in pyproject
assert '"version": "2.79.0"' in package

print(f"PASS - dependency-free release contract; migration ledger max=300, 0083 chars={len(migrations[-1][1])}")
print("PASS - v2.79.0 Research Argument & Evidentiary Synthesis Engine release contract")
