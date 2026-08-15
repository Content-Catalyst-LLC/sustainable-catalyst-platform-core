from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def req(path):
    p=ROOT/path
    if not p.is_file(): raise SystemExit(f"ERROR - required file missing: {path}")
    return p
def contains(path,needle):
    if needle not in req(path).read_text(errors="replace"): raise SystemExit(f"ERROR - {path} missing marker: {needle}")
def main():
    required=[
      "backend/app/config.py","backend/app/models.py","backend/app/services/humanitarian.py","backend/app/routers/humanitarian.py","backend/app/services/live_data.py","backend/app/routers/meta.py","backend/app/migrations.py","backend/tests/test_humanitarian_access_v2110.py","backend/scripts/validate_humanitarian_access.py",
      "deployment/platform-core-v2110.env.example","docs/HUMANITARIAN_ACCESS_ESSENTIAL_SERVICES_V2110.md","RELEASE_NOTES_V2110.md","PLATFORM_CORE_V2110_INSTALL_AND_TEST.md","PLATFORM_CORE_V2110_HUMANITARIAN_ACCESS_AUDIT.md","render.yaml","wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php",
      "backend/public_sdk/downloads/sc-platform-core-public-python-v2.11.0.zip","backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.11.0.zip","schemas/humanitarian-condition-v1.schema.json"]
    for x in required:req(x)
    contains("backend/app/config.py",'version: str = "2.11.0"')
    contains("backend/app/migrations.py",'("0014", "Humanitarian access and essential-services condition fabric')
    contains("backend/app/models.py","class HumanitarianCondition(Base):")
    contains("backend/app/services/humanitarian.py","report-metadata-not-operational-condition")
    contains("backend/app/services/humanitarian.py","CURRENT_CONDITION_ROLES")
    contains("backend/app/services/live_data.py","humanitarian_conditions_materialized")
    contains("backend/app/routers/humanitarian.py","synthetic_severity_scoring")
    contains("backend/app/routers/humanitarian.py","zero_records_mean_normal_conditions")
    contains("backend/app/routers/meta.py",'"humanitarian_access_essential_services_fabric"')
    contains("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php","Version: 2.11.0")
    contains("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php","sc_platform_core_humanitarian_status")
    assert json.loads(req("backend/public_sdk/javascript/package.json").read_text()).get("version")=="2.11.0"
    assert re.search(r'^version\s*=\s*"2\.11\.0"\s*$',req("backend/public_sdk/python/pyproject.toml").read_text(),re.M)
    json.loads(req("schemas/humanitarian-condition-v1.schema.json").read_text())
    print("PASS - v2.11.0 release contract")
if __name__=="__main__":main()
