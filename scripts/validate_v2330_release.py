#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def req(x):
 p=ROOT/x; assert p.is_file(),f"missing required file: {x}"; return p
def has(x,t): assert t in req(x).read_text(errors="replace"),f"{x} missing: {t}"
for x in [
"RELEASE_NOTES_V2330.md","PLATFORM_CORE_V2330_INSTALL_AND_TEST.md","PLATFORM_CORE_V2330_SCENARIO_LANDSCAPES_AUDIT.md","PLATFORM_CORE_V2330_TERMINAL_COMMANDS.txt",
"docs/SCENARIO_LANDSCAPES_V2330.md","backend/app/services/scenario_landscapes.py","backend/app/routers/scenario_landscapes.py","backend/tests/test_scenario_landscapes_v2330.py","backend/scripts/validate_scenario_landscapes.py",
"deploy_and_validate_platform_core_v2_33_0_macos.sh","PUSH_PLATFORM_CORE_V2330_FINAL.sh","DEPLOY_PLATFORM_CORE_V2330_CONTABO.sh","platform-core-v2330.env.example",
"backend/public_sdk/downloads/sc-platform-core-public-python-v2.33.0.zip","backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.33.0.zip"]: req(x)
has("backend/app/config.py",'version: str = "2.33.0"')
has("backend/app/migrations.py",'("0036", "Governed Scenario Landscapes')
has("backend/app/main.py","scenario_landscapes.router")
has("backend/app/routers/meta.py",'"scenario_landscapes"')
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php","Version: 2.33.0")
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php","sc_platform_core_scenario_landscapes_status")
has("wordpress-plugin/sustainable-catalyst-platform-core/readme.txt","Stable tag: 2.33.0")
has("backend/public_sdk/javascript/package.json",'"version": "2.33.0"')
has("backend/public_sdk/python/pyproject.toml",'version = "2.33.0"')
models=req("backend/app/models.py").read_text()
for cls in ["ScenarioLandscapeRecord","ScenarioLandscapeScenarioRecord","ScenarioLandscapeDimensionRecord","ScenarioLandscapeValueRecord","ScenarioLandscapeViewRecord"]: assert f"class {cls}(Base):" in models
for name in ["scenario-landscape-v1.schema.json","scenario-landscape-scenario-v1.schema.json","scenario-landscape-dimension-v1.schema.json","scenario-landscape-value-v1.schema.json","scenario-landscape-view-v1.schema.json"]:
 d=json.loads(req("schemas/"+name).read_text()); assert d["type"]=="object"
has("README.md","Next planned: **v2.34.0 — Interactive Model Canvas**")
print("PASS - v2.33.0 Scenario Landscapes release contract")
