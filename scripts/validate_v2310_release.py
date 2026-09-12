#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def req(x):
 p=ROOT/x; assert p.is_file(),f"missing required file: {x}"; return p
def has(x,t): assert t in req(x).read_text(errors="replace"),f"{x} missing: {t}"
for x in [
"RELEASE_NOTES_V2310.md","PLATFORM_CORE_V2310_INSTALL_AND_TEST.md","PLATFORM_CORE_V2310_SYSTEM_MAPS_AUDIT.md","PLATFORM_CORE_V2310_TERMINAL_COMMANDS.txt",
"docs/SYSTEM_MAPS_V2310.md","backend/app/services/system_maps.py","backend/app/routers/system_maps.py","backend/tests/test_system_maps_v2310.py","backend/scripts/validate_system_maps.py",
"deploy_and_validate_platform_core_v2_31_0_macos.sh","PUSH_PLATFORM_CORE_V2310_FINAL.sh","DEPLOY_PLATFORM_CORE_V2310_CONTABO.sh","platform-core-v2310.env.example",
"backend/public_sdk/downloads/sc-platform-core-public-python-v2.31.0.zip","backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.31.0.zip"]: req(x)
has("backend/app/config.py",'version: str = "2.31.0"')
has("backend/app/migrations.py",'("0034", "Governed System Maps')
has("backend/app/main.py","system_maps.router")
has("backend/app/routers/meta.py",'"system_maps"')
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php","Version: 2.31.0")
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php","sc_platform_core_system_maps_status")
has("wordpress-plugin/sustainable-catalyst-platform-core/readme.txt","Stable tag: 2.31.0")
has("backend/public_sdk/javascript/package.json",'"version": "2.31.0"')
has("backend/public_sdk/python/pyproject.toml",'version = "2.31.0"')
models=req("backend/app/models.py").read_text()
for cls in ["SystemMapRecord","SystemMapBoundaryRecord","SystemMapDomainRecord","SystemMapMembershipRecord","SystemMapViewRecord"]: assert f"class {cls}(Base):" in models
for name in ["system-map-v1.schema.json","system-map-boundary-v1.schema.json","system-map-domain-v1.schema.json","system-map-view-v1.schema.json"]:
 d=json.loads(req("schemas/"+name).read_text()); assert d["type"]=="object"
print("PASS - v2.31.0 System Maps release contract")
